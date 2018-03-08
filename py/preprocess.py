import pandas as pd
import collections
import numpy as np
import graph_tool.all as gt
import pickle
import MBS_analysis as mbs


def main(csv_path, graph_path):
    print("Creating dataframe...")
    df = mbs.make_df(csv_path)
    print("Done. Creating bipartite simple graph...")
    el = edge_list_bi(df)
    g = make_bipartite_simple_graph(el, SPRtab)
    add_vp_SPRPRAC(g)
    print("Done. Pickling graph at", graph_path, "...")
    pickle.dump(g, open(graph_path, "wb"))
    print("Done.")
    

if __name__ == "__main__":
    import sys
    csv_path    = sys.argv[1]
    graph_path  = sys.argv[2]
    main(csv_path, graph_path)
