import graph_tool.all as gt
import pickle
import time
import argparse
import numpy as np

def main(inpath, regions, outpath, deg_corr=True, bipartite=True):
    start_time = time.time()    
    with open(inpath, 'rb') as fo:
        g = pickle.load(fo)    
    print("Graph loaded with", g.num_vertices(), "vertices and", g.num_edges(),
          "edges.")
    gt.remove_parallel_edges(g)
    print("After removal of parallel edges:", g.num_vertices(), "vertices", 
          g.num_edges(), "edges.")
    
    # Drop all vertices not from regions of interest
    vfilt = g.new_vertex_property('bool', val=False)
    for k in regions:
        vfilt.a = np.logical_or(vfilt.a, g.vp.sprstate.a==int(k))
    gt.infect_vertex_property(g, vfilt, vals=[True])
    g.set_vertex_filter(vfilt)
    g.purge_vertices()
    g.clear_filters()
    print("After removing vertices not from regions", regions)
    print("Vertices:", g.num_vertices(), "Edges:", g.num_edges())

    state_args = dict()
    if bipartite:
        (check, vp) = gt.is_bipartite(g, partition=True)
        state_args['pclabel'] = vp

    print("state_args=", state_args)
    
    state = gt.minimize_nested_blockmodel_dl(g, deg_corr=deg_corr,
            state_args=state_args, verbose=True)
    
    with open(outpath, 'wb') as save_to:
        pickle.dump(state, save_to, -1)
    print("--- %s seconds ---" % (time.time() - start_time))

    
if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--infile',
        help="Path to input", required=True)
    parser.add_argument('--outfile',
        help="Path to output")
    parser.add_argument('--ndc', action='store_false', dest='dc',
        help="""Flag for using non-degree-corrected version. Default is
        degree-corrected""")
    parser.add_argument('--regions', nargs='+',
        help="""Which SPRSTATE regions should be combined?""")
    parser.add_argument('--unipartite', action='store_false', dest='bipartite',
        help="Flag for assuming unipartite structure. Default is bipartite.")
    
    args = parser.parse_args()
    inpath = args.infile
    regions = args.regions
    outpath = args.outfile
    deg_corr = args.dc
    bipartite = args.bipartite

    main(inpath, regions, outpath, deg_corr, bipartite)