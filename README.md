# Supplemental material

This repository documents our computational work for the article

> The network structure of general practice in Australia: analysis of national 
> claims data.

Workflow: 

1. [Preprocessing of MBS claims data] 
2. Generation of patient -- GP graphs
3. Fitting hierarchical blockmodels
4. Analysis of the block structure

Files: 

* The Python module [`MBS_analysis.py`](/py/MBS_analysis.py) (imported as `mbs`) 
  contains our most important methods. 
* The Jupyter Notebook [`supplemental.ipynb`](/py/supplemental.ipynb) shows a 
  minimal example.
* The folder `pbs` contains Unix scripts which were run on the high-performance 
  computing cluster at UNSW Science. 


## Preprocessing of MBS claims data 

* [`mbs.make_df()`](/py/MBS_analysis.py#L7) turns the `csv` data into a pandas
  dataframe. 
* [`mbs.patient_doctor_graph`](/py/MBS_analysis.py#L25) turns the dataframe into 
  a `graph_tool.Graph`

## Generation of patient -- GP graphs

## Fitting hierarchical blockmodels

## Analysis of the block structure


The network we consider is bipartite: there are two types of nodes (GPs
and patients), and there are only edges connecting GPs with patients.
Most previous studies have used unipartite network (or one-mode network)
which is a projection from the bipartite, containing only one type of
node (i.e. GPs only) and the edges indicating number of shared patients.
As a result, the projected network contains less information, and this
is challenging in particular with solo GPs who have few shared patients
and often being merged with a big network. Identifying GP communities
(or Provider Practice Communities -PPCs) is a process of graph
partitioning, communities detection or finding clusters in the networks.
The common used approach, utilising the modularity maximation, has been
shown to be non-robust with the problem of resolution limit, the
phenomenon that small communities cannot be identified. In this
analysis, we utilised an approach proposed by Peixoto which is based on
a hierarchical stochastic blockmodel: GPs and patients are clustered
into blocks, and two connections, e.g. (GP 1, patient 1) and (GP 2,
patient 2), are equally likely if GP1 and GP2 are from the same block of
GPs and patient 1 and patient 2 are from the same block of patients. A
partition which maximizes the likelihood is deemed optimal; such a
partition consists of blocks of GPs which tend to be connected to the
same group(s) of patients. By hierarchically fitting blockmodels at
different resolution levels, the resolution limit problem is avoided.
The hierarchical stochastic blockmodelling approach is also designed to
avoid overfitting (i.e. identifying too many blocks) via Occam’s Razor
theory (ref): the chosen model is the one that best compresses the data.
Because almost 2000 GPs in this data have seen fewer than 5 patients,
some indications showed that some communities with single GP were
grouped into one block. Therefore, the next step after fitting the model
was to identify GP communities as the connected components within each
block; that is, communities are distinct groups of GPs within a block
that do not share patients with any other groups.
