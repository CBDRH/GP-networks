import pandas as pd
import collections
import numpy as np
import graph_tool.all as gt
import pickle
import MBS_analysis as mbs


def main(csv_path, graph_path):
    print("Creating dataframe...")
    print(csv_path)
    print(graph_path)
    df = mbs.make_df(csv_path)
    print("Done. Creating bipartite simple graph...")
    g = mbs.patient_doctor_graph(df)
    print("Done. Pickling graph at", graph_path, "...")
    with open(graph_path, 'wb') as fo:
        pickle.dump(g, fo)
        
    print("Done.")
    

if __name__ == "__main__":
    import sys
    csv_path    = sys.argv[1]
    graph_path  = sys.argv[2]
    main(csv_path, graph_path)
