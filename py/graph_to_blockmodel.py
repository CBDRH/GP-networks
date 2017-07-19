
import graph_tool.all as gt
import cPickle as pickle
import time
import sys
import os
from logger import Logger
import argparse
import random as rd
import numpy as np

start_time = time.time()

# parse arguments

parser = argparse.ArgumentParser()
parser.add_argument('--infile',
    help="Path to input", required=True)
parser.add_argument('--outfile',
    help="Path to output")
parser.add_argument('--ndc', action='store_false', dest='dc',
    help="""Flag for using non-degree-corrected version. Default is
    degree-corrected""")
parser.add_argument('--bipartite', help="""Name of vertex property which
    names the two types of vertices.""")
parser.add_argument('--remove_parallel', action='store_true',
    dest='rm', help="Should parallel edges be removed?")
parser.add_argument('--regions', nargs='+',
    help="""Which SPRSTATE regions should be combined?""")
parser.add_argument('--layer_variable',
    help="""Name of edge property to be used to split the network into
            discrete layers. Default: None""")
parser.add_argument('--layer_type', choices=['no', 'id', 'ec'],
    default='no',
    help="""'no' (default, ignores --layer_variable),
            'id' for independent layers,
            'ec' for edge covariates""")
parser.add_argument('--weight', help="Edge property containing weights.")
parser.add_argument('--Bmin', help="minimum number of blocks", type=int)
parser.add_argument('--Bmax', help="maximum number of blocks", type=int)
parser.add_argument('--mult', help="multiply edge weight by",  type=int)
parser.add_argument('--cutoff', help="remove edges with weights below cutoff.",
                    type=float)

args = parser.parse_args()

# redirect input graph
args.infile
g = pickle.load(open(args.infile, "rb"))
print "Graph loaded."

# direct logs
logfile = args.outfile + '.log'
logger = Logger(logfile)
saveout = sys.stdout
sys.stdout = logger
sys.stderr = logger

print "Arguments:", args

print "Graph has", g.num_vertices(), "vertices and", g.num_edges(), "edges."

if args.rm:
    gt.remove_parallel_edges(g)
    print "After removal of parallel edges:", g.num_vertices(), "vertices", g.num_edges(), "edges."

print "Saving to", args.outfile
print '---------------------------------------'

vfilt = g.new_vertex_property('bool', val=False)
for k in args.regions:
    vfilt.a = np.logical_or(vfilt.a, g.vp.sprstate.a==int(k))
gt.infect_vertex_property(g, vfilt, vals=[True])
gv = gt.GraphView(g, vfilt=vfilt)
print "Vertices:", gv.num_vertices(), "Edges:", gv.num_edges()

state_args = dict()
if args.bipartite:
    state_args['pclabel'] = eval('g.vp.'+args.bipartite)
    print "Using", args.bipartite, "as pclabel."

# specify edge weights
if args.weight:
    weight = eval('gv.ep.' + args.weight)
    gv.edge_properties['weight'] = weight
    if args.mult:
        print "Multiplying weights by", args.mult
        weight.a = weight.a * args.mult
    if args.cutoff:
        print "Applying cutoff at", args.cutoff
        efilt = g.new_edge_property('bool')
        efilt.a = (weight.a >= args.cutoff)
        gv = gt.Graph(gt.GraphView(g, efilt=efilt), prune=True)

if args.layer_variable:
    state_args['ec'] = eval('gv.ep.' + args.layer_variable)
if args.layer_type == 'id':
    state_args['layers'] = True
if args.layer_type == 'ec':
    state_args['layers'] = False

print "state_args=", state_args

state = gt.minimize_nested_blockmodel_dl(
    gv, B_min=args.Bmin, B_max=args.Bmax,
    deg_corr=args.dc,
	layers=(args.layer_type != 'no'),
    state_args= state_args,
	verbose=True)
state.call_args = args

with open(args.outfile, 'wb') as save_to:
    pickle.dump(state, save_to, -1)

print("--- %s seconds ---" % (time.time() - start_time))

# sys.stdout = saveout
