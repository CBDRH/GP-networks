import graph_tool.all as gt
import pickle
import time
import argparse
import numpy as np
import MBS_analysis as mbs 
from multiprocessing import Pool 


def thread(g_rseed):
    np.random.seed(g_rseed[1])
    state = mbs.blockmodel(g_rseed[0].copy(), regions, deg_corr, bipartite, verbose=True)
    return(state)

def main(inpath, regions, outpath, deg_corr=True, bipartite=True):
    start_time = time.time()    
    with open(inpath, 'rb') as fo:
        g = pickle.load(fo)
    
    seeds = [42, 1,3,5]
    with Pool(4) as p: 
        candidate_models = p.map(thread, zip([g]*4, seeds))
    
    entropies = list(map(lambda x: x.entropy(), candidate_models))
    print("Entropies:", entropies)
    keep = np.argmax(entropies)
    
    state = candidate_models[keep]
    state = mbs.extract_PPCs(state)
    
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
