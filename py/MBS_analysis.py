import graph_tool.all as gt
import pickle
import numpy as np
import pandas as pd


def make_df(csv_path = "../rawdata/MBS_SAMPLE_10PCT_2014.csv", 
            nrows=None, 
            append_SPRPRAC=True):
    """Reads in the csv file at `csv_path` and returns a pandas dataframe
    that will be used to construct the graph."""
    df = pd.read_csv(csv_path,
                     usecols=['PIN','DOS','SPR','SPRPRAC', 'SPRSTATE',
                              'ITEM','BILLTYPECD','INHOSPITAL'],
                              nrows=nrows)
    keep = (df['INHOSPITAL'] == 'N') & list(
            map(lambda x: [23,3,36,44,52,53,54,57].count(x) > 0, df['ITEM']))
    df = df[keep].drop('INHOSPITAL',1)
    df[['PIN']] = list(map(lambda x: 'p' + str(int(x)), df['PIN']))
    df[['SPR']] = list(map(lambda x: 'd' + str(x), df['SPR']))
    if append_SPRPRAC:
        df['SPR'] = df['SPR'] + '-' + df['SPRPRAC']
    return(df)
    
def patient_doctor_graph(df):
    """
    Creates a `gt.Graph()` from the edge list `el`
    """
    def edge_list(df):
        def Dcount(x): 
            return(sum(x == 'D'))
        def Pcount(x):
            return(sum(x == 'P'))
        def common_state(x):
            return(np.argmax(np.bincount(x)))
        grouped = df.groupby(['PIN', 'SPR'])
        agg_df = grouped.agg({'BILLTYPECD': [Dcount, Pcount], 'SPRSTATE': common_state})
        out = (row[0] + tuple(row[1]) for row in agg_df.iterrows())
        return(out)
        
    g = gt.Graph(directed=False)
    g.ep['bulkD']   = g.new_edge_property('int')
    g.ep['bulkP']   = g.new_edge_property('int')
    g.ep['sprstate']= g.new_edge_property('int')
    el = edge_list(df)
    label = g.add_edge_list(el, 
                            hashed=True, 
                            string_vals=True, 
                            eprops=[g.ep.bulkD, g.ep.bulkP, g.ep.sprstate])
    g.vertex_properties['label'] = label
    g.vertex_properties['doctor'] = g.new_vertex_property('bool')
    g.vp.doctor.a = list(map(lambda x: x[0]=='d', label))
    return(g)

def blockmodel(g, regions, deg_corr=True, bipartite=True, verbose=False):
    if verbose:
        print("Graph has", g.num_vertices(), "vertices and", g.num_edges(), "edges.")
    gt.remove_parallel_edges(g)
    if verbose: 
        print("After removal of parallel edges:", g.num_vertices(), "vertices", 
          g.num_edges(), "edges.")

    efilt = g.new_edge_property('bool', val=False)
    for k in regions:
        efilt.a = np.logical_or(efilt.a, g.ep.sprstate.a==int(k))
    g.set_edge_filter(efilt)
    vfilt = g.new_vertex_property('bool', val=False)
    vfilt.a = (g.degree_property_map('total').a > 0)
    g.set_vertex_filter(vfilt)

    g.purge_edges()
    g.purge_vertices()

    if verbose:
        print("After removing vertices and edges not from regions", regions)
        print("Vertices:", g.num_vertices(), "Edges:", g.num_edges())
    state_args = dict()
    if bipartite:
        state_args['pclabel'] = g.vp.doctor

    if verbose:
        print("state_args=", state_args)
    
    state = gt.minimize_nested_blockmodel_dl(g, deg_corr=deg_corr,
            state_args=state_args, verbose=verbose)
    
    return(state)

def extract_PPCs(state):
    """
    Subdivides the bottom blockstate further, according to the connected
    components. 
    
    Parameters
    ----------
    state : a hierarchical blockstate, with standard blockstate at the bottom 
            layer (not overlapping or layered).

    Returns
    -------
    A NestedBlockState with an additional layer at the bottom, 
    representing the PPCs. 
    """
    
    g = state.g
    bs = state.get_bs()
    component = g.new_vertex_property('python::object')
    # set component property for patients
    foo_property = g.new_vertex_property('int')
    foo_property.a = bs[0]
    for v in g.vertices():
        if not g.vp.doctor[v]:
            component[v] = foo_property[v],

    doctor_bidx  = np.unique(bs[0][g.vp.doctor.a == 1])
    active = g.new_vertex_property('bool')    
    for k in doctor_bidx:
        active.a = (bs[0] == k)
        gt.infect_vertex_property(g, active, [True])
        try:
            g.set_vertex_filter(active)
            active_comp = gt.label_components(g)[0]
            active.a = active.a & g.vp.doctor.a
            for v in g.vertices():
                component[v] = (k, active_comp[v])            
        finally:
            g.clear_filters()

    comp_dict = dict()
    block_tuples = list(set([component[v] for v in g.vertices()]))
    for k,v in enumerate(block_tuples):
        comp_dict[v] = k
    
    new_b0 = np.zeros(bs[0].shape, dtype = 'int')
    for v in g.vertices():
        new_b0[g.vertex_index[v]] = comp_dict[component[v]]
        
    new_b1 = np.zeros(np.unique(new_b0).shape, dtype = 'int')
    for k in range(len(new_b1)):
        new_b1[k] = block_tuples[k][0]
        
    new_bs = [new_b0] + [new_b1] + bs[1:]
    
    return(gt.NestedBlockState(g, new_bs))


def PPCids(state):
    g = state.g
    bs = state.get_bs()
    return(np.unique(bs[0][g.vp.doctor.a == 1]))
    
def PPCgraph(state,k):
    if k >= len(PPCids(state)):
        raise Exception("k too big.")
    g = state.g
    bs = state.get_bs()
    active = g.new_vertex_property("bool")
    active.a = (bs[0] == PPCids(state)[k])
    gt.infect_vertex_property(g, active, vals=[True])
    try:
        g.set_vertex_filter(active)
        h = g.copy()
    finally:
        g.clear_filters()
    h.purge_vertices()
    return(h)

def plot_PPCgraph(g, output=None):
    size    = g.new_vertex_property("float")
    size.a  = 5 + g.vp.doctor.a * 17
    gt.graph_draw(g, vertex_size=size, vertex_fill_color=g.vp.doctor,
                vorder=g.vp.doctor, 
                output=output)


def add_props(s):
    """
    Adds useful vertex and edge properties to the graph g.
    """
    g = s.g
    g.ep['visits'] = g.new_edge_property('int')
    g.ep['pnv'] = g.new_edge_property('float')
    g.vp['upc'] = g.new_vertex_property('float')
    g.vp['apt'] = g.new_vertex_property('float')
    g.vp['uppcc'] = g.new_vertex_property('float')

    # EDGE properties
    g.ep.visits.a = g.ep.bulkD.a + g.ep.bulkP.a
    weighted_deg = g.degree_property_map('total', g.ep.visits)

    def pat_normalized_visits(e):
        pat = e.source()
        assert(g.vp.doctor[pat] == 0)
        return(g.ep.visits[e] / weighted_deg[pat])

    g.ep.pnv.a = [pat_normalized_visits(e) for e in g.edges()]
    print("Patient normalized visits done.")
    
    # PATIENT PROPERTIES
    # Usual Provider Continuity
    def patient_upc(v):
        if g.vp.doctor[v]:
            return(0)
        else: 
            visit_list = [g.ep.visits[e] for e in v.all_edges()]
            return(max(visit_list) / sum(visit_list))

    # Usual PPC Continuity
    def uppcc(v):
        from collections import Counter
        if g.vp.doctor[v]:
            return(0)
        else:
            es = list(v.all_edges())
            num_visits = [g.ep.visits[e] for e in es]
            neigh_idx = [g.vertex_index[e.target()] for e in es]
            for i in neigh_idx:
                assert(g.vp.doctor[g.vertex(i)])
            PPC_idx    = s.get_bs()[0][neigh_idx]
            c = Counter()
            for k in range(len(PPC_idx)): 
                c[PPC_idx[k]] += num_visits[k]
            return(c.most_common()[0][1] / sum(num_visits))
        
    # DOCTOR PROPERTIES
    def avg_pat_time(v):
        if not g.vp.doctor[v]:
            return(0)
        else:
            visit_list = [g.ep.visits[e] for e in v.all_edges()]
            pat_degs   = [weighted_deg[n] for n in v.all_neighbours()]
            return(sum(visit_list) / sum(pat_degs))            

    for v in g.vertices():
        g.vp.upc[v] = patient_upc(v)
        g.vp.uppcc[v] = uppcc(v)
        g.vp.apt[v] = avg_pat_time(v)
    print("Usual provider continuity, Usual PPC continuity and Average Patient Time done.")

    # PPC PROPERTIES
    # shared patient fraction, averaged over GPs in PPC
    def PPC_shared_patient_fraction(PPCg):        
        def shared_patient_fraction(v):
            if PPCg.vp.doctor[v] == 0:
                return(-1)
            else:
                pat_deg_list = [dpm[pat] for pat in v.all_neighbors()]
                shared_patients = len([True for deg in pat_deg_list if deg > 1])
                total_patients  = len(pat_deg_list)
                return(shared_patients/total_patients)
                
        return(np.mean([shared_patient_fraction(v) for v in PPCg.vertices() if PPCg.vp.doctor[v]]))    
    
    # patient degree, masked to within PPC, averaged over PPC
    def PPC_patient_degree(PPCg):
        def patient_degree(v):
            if PPCg.vp.doctor[v] == 1:
                return(-1)
            else:
                return(dpm[v])
        return(np.mean([patient_degree(v) for v in PPCg.vertices() if not PPCg.vp.doctor[v]]))
    

    # Level 1 graph
    l1g = s.get_bstack()[1]
    spf = l1g.new_vertex_property('float', -1)
    l1g.vp['spf'] = spf
    ppd = l1g.new_vertex_property('float', -1)
    l1g.vp['ppd'] = ppd
    for k in range(len(PPCids(s))):
        i = PPCids(s)[k]
        PPCg = PPCgraph(s, k)
        dpm = PPCg.degree_property_map("total")
        spf[l1g.vertex(i)] = PPC_shared_patient_fraction(PPCg)
        ppd[l1g.vertex(i)] = PPC_patient_degree(PPCg)
    print("Shared patient fraction and PPC patient degree done.")
        
    return(s, l1g) # need to return the state, for Pool().map to work; 
                   # also, l1g won't pickle as an attribute of s

def get_ppc_stats(s_l1g):
    s = s_l1g[0]
    l1g = s_l1g[1]
    PPC_idx = PPCids(s)
    def ppc_stats(k):
        g = PPCgraph(s, k)
        i = PPC_idx[k]
        mean_spf = l1g.vp.spf[l1g.vertex(i)]
        mean_ppd = l1g.vp.ppd[l1g.vertex(i)]
        mean_upcs = np.mean([g.vp.upc[v] for v in g.vertices() if not g.vp.doctor[v]])
        mean_uppccs = np.mean([g.vp.uppcc[v] for v in g.vertices() if not g.vp.doctor[v]])
        mean_apt  = np.mean([g.vp.apt[v] for v in g.vertices() if g.vp.doctor[v]])
        mean_deg = np.mean([g.degree_property_map('total')[v] for v in g.vertices() if g.vp.doctor[v]])
        row = (i, mean_spf, mean_ppd, mean_upcs, mean_uppccs, mean_apt, mean_deg)
        row = list(map(lambda x: round(x,2), row))
        return(row)
    unfmt = list(map(ppc_stats, range(len(PPCids(s)))))
    return(pd.DataFrame(data=unfmt, columns=['idx', 'spf', 'ppd', 'upc', 'uppcc', 'apt', 'deg']))
