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
for number_file, rootfile in enumerate(list_overlay):
    reader = root_io.Reader(rootfile)
    metadata = reader.get("metadata")[0]
    list_times = []
    for event in reader.get("events"):
        dc_hits = event.get("CDCHHits")
        for num_hit, dc_hit in enumerate(dc_hits):
            time = dc_hit.getTime()
            list_times.append(time+total_time)
    total_time = total_time + 20
    dic[str(number_file)] = list_times

eos_base_file = "/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/scratch/Zcard_CLD_background/4/out_sim_edm4hep_base.root"

reader = root_io.Reader(eos_base_file)
metadata = reader.get("metadata")[0]
list_times = []
for event in reader.get("events"):
    dc_hits = event.get("CDCHHits")
    for num_hit, dc_hit in enumerate(dc_hits):
        time = dc_hit.getTime()
        if time<400:
            list_times.append(time)

dic["base"] =  list_times

np.save("d1.npy", dic)