#
# Copyright (c) 2020-2024 Key4hep-Project.
#
# This file is part of Key4hep.
# See https://key4hep.github.io/key4hep-doc/ for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from Gaudi.Configuration import INFO

from k4FWCore import ApplicationMgr
from k4FWCore import IOSvc
from Configurables import EventDataSvc
from Configurables import OverlayTiming
from Configurables import UniqueIDGenSvc
from Configurables import k4DataSvc, MarlinProcessorWrapper


list_overlay = []
for i in range(1,501):
    list_overlay.append("/eos/experiment/fcc/ee/datasets/CLD_tracking/Pythia/CLD_background_only/out_sim_edm4hep_background_"+str(i)+".root")


id_service = UniqueIDGenSvc("UniqueIDGenSvc")

eds = EventDataSvc("EventDataSvc")

iosvc = IOSvc()
# iosvc.input = "input.root"
iosvc.Input = "out_sim_edm4hep.root"
iosvc.Output = "output_overlay_new1.root"

# inp.collections = [
#     "EventHeader",
#     "MCParticle",
#     "VertexBarrelCollection",
#     "VertexEndcapCollection",
#     "HCalRingCollection",
# ]

overlay = OverlayTiming()
overlay.MCParticles = ["MCParticles"]
overlay.BackgroundMCParticleCollectionName = "MCParticles"
overlay.SimTrackerHits = ["VertexBarrelCollection", "VertexEndcapCollection", "InnerTrackerBarrelCollection", "OuterTrackerBarrelCollection","InnerTrackerEndcapCollection","OuterTrackerEndcapCollection"]
overlay.SimCalorimeterHits = ["HCalBarrelCollection"]
overlay.OutputSimTrackerHits = ["NewVertexBarrelCollection", "NewVertexEndcapCollection","NewInnerTrackerBarrelCollection", "NewOuterTrackerBarrelCollection","NewInnerTrackerEndcapCollection","NewOuterTrackerEndcapCollection"]
overlay.OutputSimCalorimeterHits = ["NewHCalBarrelCollection"]
overlay.OutputCaloHitContributions = ["NewCaloHitCollection"]
# overlay.StartBackgroundEventIndex = 0
overlay.AllowReusingBackgroundFiles = True
overlay.CopyCellIDMetadata = True
overlay.NumberBackground = [1]
overlay.Poisson_random_NOverlay = [False]
overlay.BackgroundFileNames = [
      list_overlay
]
overlay.TimeWindows = {"MCParticles": [-10, 1000], "VertexBarrelCollection": [-10, 1000], "VertexEndcapCollection": [-10, 1000], "HCalBarrelCollection": [-10, 1000],"InnerTrackerBarrelCollection": [-10, 1000], "OuterTrackerBarrelCollection": [-10, 1000],"InnerTrackerEndcapCollection": [-10,1000],"OuterTrackerEndcapCollection": [-10,1000] }


ApplicationMgr(TopAlg=[overlay],
               EvtSel="NONE",
               EvtMax=200,
               ExtSvc=[eds],
               OutputLevel=INFO,
               )
