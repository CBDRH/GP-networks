#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 25 19:57:39 2018

@author: poyda
"""

#%% preprocess
import preprocess
csv_path = "../rawdata/oneMill2014.csv"
graph_path = "../pickle/graphs/oneMill2014.p"
preprocess.main(csv_path, graph_path)

#%% fit blockmodel
import graph_to_blockmodel as g2b
bm_path = "../pickle/blockmodels/quick2014.p"
g2b.main(inpath=graph_path, regions=[3,4], outpath=bm_path)

#%% cherry-pick
import plotting
state = plotting.get_state("../pickle/blockmodels/complete2014reg3.p")

ks = [23, 533, 563, 512, 529, 530]

for k in ks:
    g = plotting.PPCgraph(state,k)
    plotting.plotPPCgraph(g, output="../data-out/into-paper/"+'{:04d}'.format(k)+".png")
    deg = g.degree_property_map("total")
    (sum(g.vp.doctor.a == 1), 
     sum(deg.a[g.vp.doctor.a == 1]) / sum(g.vp.doctor.a == 1),
     sum(g.vp.doctor.a == 0),
     sum(deg.a[g.vp.doctor.a == 0]) / sum(g.vp.doctor.a == 0))

