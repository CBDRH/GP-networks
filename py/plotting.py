#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 16:48:29 2018

@author: poyda
"""

import graph_tool.all as gt
import pickle
import numpy as np

def get_state(path="../pickle/blockmodels/complete2014reg3.p"): 
    with open(path, 'rb') as fo: 
        state = pickle.load(fo)
    import conn_comp
    return(conn_comp.divide_by_component(state))

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
    return(h)
    
def plotPPCgraph(g, output=None):
    size    = g.new_vertex_property("float")
    size.a  = 5 + g.vp.doctor.a * 17
    gt.graph_draw(g, vertex_size=size, vertex_fill_color=g.vp.doctor,
                vorder=g.vp.doctor, 
                output=output)
    
def plot_all(state):
    for k in range(len(PPCids(state))):
        plotPPCgraph(PPCgraph(state,k))
        g = PPCgraph(state,k)
        plotPPC(state, k)
