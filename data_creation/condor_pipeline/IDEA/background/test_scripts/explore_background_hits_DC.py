from podio import root_io
import edm4hep
import sys
import ROOT
from ROOT import TFile, TTree
import numpy as np 
from array import array
import math

list_overlay = []
for i in range(1,20):
    list_overlay.append("/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/IDEA_background_only/out_sim_edm4hep_background_"+str(i)+".root")

dic = {}
total_time = 0 
rootfile = list_overlay[0]

reader = root_io.Reader(rootfile)
metadata = reader.get("metadata")[0]

list_index = []
for event in reader.get("events"):
    dc_hits = event.get("CDCHHits")
    for num_hit, dc_hit in enumerate(dc_hits):
        mcParticle = dc_hit.getMCParticle()
        index_mc = mcParticle.getObjectID().index
        list_index.append(index_mc)
unique_mcs = np.unique(np.array(list_index))
print("unique_mcs", unique_mcs)
list_R = []
list_p = []
list_px = []
list_py = []
list_pz = []
list_gen_status = []
MCparticles = event.get("MCParticles")
for i in range(0, len(unique_mcs)):
    mc_index = unique_mcs[i]
    mcParticle = MCparticles[int(mc_index)]
    x_vertex = mcParticle.getVertex().x
    y_vertex = mcParticle.getVertex().y
    z_vertex = mcParticle.getVertex().z
    vertex_R = math.sqrt(mcParticle.getVertex().x ** 2 + mcParticle.getVertex().y ** 2)* 1e-03
    list_R.append(vertex_R)
    momentum = mcParticle.getMomentum()
    p = math.sqrt(momentum.x**2 + momentum.y**2 + momentum.z**2)
    list_p.append(p)
    list_px.append(momentum.x)
    list_py.append(momentum.y)
    list_pz.append(momentum.z)
    gen_status = mcParticle.getGeneratorStatus()
    list_gen_status.append(gen_status)

dic["R"]=np.array(list_R)
dic["p"]=np.array(list_p)
dic["px"]=np.array(list_px)
dic["py"]=np.array(list_py)
dic["pz"]=np.array(list_pz)
dic["gens"]=np.array(list_gen_status)

# eos_base_file = "/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/scratch/Zcard_CLD_background/4/out_sim_edm4hep_base.root"

# reader = root_io.Reader(eos_base_file)
# metadata = reader.get("metadata")[0]
# list_times = []
# for event in reader.get("events"):
#     dc_hits = event.get("CDCHHits")
#     for num_hit, dc_hit in enumerate(dc_hits):
#         time = dc_hit.getTime()
#         if time<400:
#             list_times.append(time)

# dic["base"] =  list_times

np.save("background_particles.npy", dic)