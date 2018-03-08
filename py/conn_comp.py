#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 15:19:56 2018

@author: poyda
"""

import graph_tool.all as gt
import numpy as np

def divide_by_component(state):
    """
    Subdivides the bottom blockstate further, according to the connected
    components. 
    
    Parameters
    ----------
    state : a hierarchical blockstate, with standard blockstate at the bottom 
            layer (not overlapping or layered).

    Returns
    -------
    None
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
        g.set_vertex_filter(active)
        active_comp = gt.label_components(g)[0]
        active.a = active.a & g.vp.doctor.a
        for v in g.vertices():
            component[v] = (k, active_comp[v])            
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
