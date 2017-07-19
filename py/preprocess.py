import pandas as pd
import collections
import numpy as np
import graph_tool.all as gt
import cPickle as pickle


def make_df(path):
    """Reads in the csv file at `path` and returns a pandas dataframe
    that will be used to construct the graph."""
    df = pd.read_csv(path, usecols=['PIN','DOS','SPR','SPRPRAC',
                    'SPRSTATE','ITEM','BILLTYPECD','INHOSPITAL'])
    keep = (df['INHOSPITAL'] == 'N') & (map(lambda x: [23,3,36,44,52,53,54,57].count(x) > 0, df['ITEM']))
    df = df[keep].drop('INHOSPITAL',1)
    df[['PIN']] = list(map(lambda x: 'p' + str(int(x)), df['PIN']))
    df[['SPR']] = list(map(lambda x: 'd' + str(x), df['SPR']))
    return(df)


def SPRrec(state = None, pats=0, bulk=None):
    """A function for the defaultdict, returning the default
    (the named triple (None, 0, None))
    """
    return (state, pats, bulk)


def make_SPRtable(df):
    """Takes the dataframe created above and creates a lookup table, i.e.
    a dictionary with doctor labels as keys and a triple
    (state, num_patients, frac_bulk_bill) as the values."""
    grouped = df.groupby('SPR')
    SPRtab = collections.defaultdict(SPRrec)
    processed = 0
    for doc in grouped.groups:
        rec = grouped.get_group(doc)
        state = np.argmax(np.bincount(rec['SPRSTATE']))
        bulk = float((rec['BILLTYPECD']=='D').sum()) / rec['BILLTYPECD'].count()
        pats = np.unique(rec['PIN'])
        SPRtab[doc] = SPRrec(state, pats, bulk)
        processed += 1
        if processed % 1000 == 0:
            print "Processed", processed, "out of", grouped.ngroups, "doctors."
    print "Finished."
    return(SPRtab)


def make_bipartite_simple_graph(df, SPRtab):
    """Creates a `gt.Graph()` from the data frame `df` and the lookup
    table `SPRtab`
    """

    def edge_list_bi(df):
        processed = 0
        grouped = df.groupby(['PIN', 'SPR'])
        print "Grouping data by PIN and SPR."
        pat_doc_groups = grouped.groups
        print "Finished grouping. Processing", len(grouped.groups), "edges."
        for pat_doc in pat_doc_groups:
            rec = grouped.get_group(pat_doc)
            bulk = (rec['BILLTYPECD'].value_counts().index[0] == 'D')
            yield (pat_doc[0], pat_doc[1], bulk)
            processed += 1
            if processed % 100000 == 0:
                print "Processed", processed, "edges."
        print "Finished."

    g = gt.Graph(directed=False)
    bulk = g.new_edge_property('bool')
    label = g.add_edge_list(edge_list_bi(df), hashed=True, string_vals=True,
                            eprops=[bulk])
    g.vertex_properties['label'] = label
    g.edge_properties['bulk']    = bulk
    doctor = gt.is_bipartite(g, partition=True)[1]
    if sum(doctor.a) > sum(1-doctor.a): #the smaller of the two groups must be
                                        #doctors; relabel
        doctor.a = 1-doctor.a
    g.vertex_properties['doctor'] = doctor
    # assign to each vertex the state which corresponds to the majority of its edges. This is stored in SPRtab.p.
    sprstate = g.new_vertex_property('int')
    for v in g.vertices():
        if not doctor[v]:
            continue
        sprstate[v] = SPRtab[label[v]][0]
    g.vertex_properties['sprstate'] = sprstate
    return(g)


if __name__ == "__main__":
    import sys

    csv_path    = sys.argv[1]
    graph_path  = sys.argv[2]

    print("Creating dataframe...")
    df = make_df(csv_path)
    print("Done. Creating lookup table for SPRs...")
    SPRtab = make_SPRtable(df)
    print("Done. Creating bipartite simple graph...")
    g = make_bipartite_simple_graph(df, SPRtab)
    print "Done. Pickling graph at", graph_path, "..."
    pickle.dump(g, open(graph_path, "wb"))
    print("Done.")
