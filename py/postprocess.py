import graph_tool.all as gt
import numpy as np

# if called as a main method (s. bottom), with a path to a directory as its
# argument, it post-processes all files in this directory.

def add_vp_PPC(state):
    """Adds a vertex property 'PPC' to the graph g in an object 'state' of 
    class gt.BlockState. A PPC is defined as a connected component found in a 
    block.
    """
    g = state.g
    if 'PPC' in state.g.vp:
        return(state)
    g.vp['block'] = state.get_levels()[0].get_blocks()
    # not sure if I need this g = gt.Graph(g, prune=True)

    blockpair = dict() # maps: vertex_label -> (block, component)
    for k in np.unique(g.vp.block.a[np.where(g.vp.doctor.a)]):
        active = g.new_vertex_property('bool')
        active.a = (g.vp.block.a == k)
        gt.infect_vertex_property(g, active, [True])
        g_v = gt.GraphView(g, vfilt=active)
        comp = gt.label_components(g_v)[0]
        for v in g_v.vertices():
            if not g_v.vp.doctor[v]:
                continue
            blockpair[g_v.vp.label[v]] = (k, comp[v])

    PPC_id = dict() # maps: (block, component) -> PPC_id
    for k, v in enumerate(set(blockpair.values())):
        PPC_id[v] = k

    PPC = g.new_vp('int', val=-1) # -1 because 0 is a valid PPC_id
    for v in g.vertices():
        if not g.vp.doctor[v]:
            continue
        PPC[v] = PPC_id[blockpair[g.vp.label[v]]]
        # closes the circle: maps vertex -> label -> (block, component) -> 
        # new_block
    g.vp['PPC'] = PPC
    return(state)


def write_PPCs(state, path):
    """Creates a csv file at `path` with two columns: GP label and PPC id.
        state:  a hierarchical BlockState
    """
    state = add_vp_PPC(state)
    g = state.g
    import csv
    with open(path, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        for v in g.vertices():
            if g.vp.doctor[v]:
                writer.writerow([g.vp.label[v], g.vp.PPC[v]])


if __name__ == "__main__":
    # reads in a blockstate at path given by first argument
    # outputs a csv file mapping GPs to PPCs at path given by second argument
    import sys
    import pickle
    blockstate_path = sys.argv[1]
    ppc_path        = sys.argv[2]
    print("---------------------------------------------------")
    print("Postprocessing", blockstate_path)
    try:
        with open(blockstate_path, 'rb') as fo:
            state = pickle.load(fo)
        print("Entropy:", state.entropy())
        state = add_vp_PPC(state)
        print("Number of PPCs:", len(np.unique(state.g.vp.PPC.a)))
        write_PPCs(state, ppc_path)
    except EOFError:
        print("Problem with pickled file.")
