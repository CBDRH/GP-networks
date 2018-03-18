import graph_tool.all as gt
import pickle
import time
import argparse
import numpy as np
import MBS_analysis as mbs 
import multiprocessing as mp

    
def work_hard(kw):
    print(kw)
    np.random.seed(kw['seed'])
    time.sleep(5 + np.random.randn(1)[0])
    state = mbs.blockmodel(kw['g'], kw['regions'], kw['deg_corr'], kw['bipartite'], verbose=True)
    return(state)


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

    start_time = time.time()    
    with open(inpath, 'rb') as fo:
        g = pickle.load(fo)

    seeds = [42, 1]
        
    mp.set_start_method('spawn')
    kws = []
    for seed in seeds:
        kws += [dict(g = g, regions = regions, deg_corr = deg_corr, 
                    bipartite = bipartite, seed = seed)]
    with mp.Pool(2) as p: 
        candidate_models = p.map(work_hard, kws)
    
    entropies = list(map(lambda x: x.entropy(), candidate_models))
    print("Entropies:", entropies)
    keep = np.argmin(entropies)
    
    state = candidate_models[keep]
    state = mbs.extract_PPCs(state)
    
    with open(outpath, 'wb') as save_to:
        pickle.dump(state, save_to, -1)
    print("--- %s seconds ---" % (time.time() - start_time))
