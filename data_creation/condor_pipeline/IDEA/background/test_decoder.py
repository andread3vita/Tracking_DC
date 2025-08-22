import ROOT
from podio import root_io
import dd4hep as dd4hepModule
from ROOT import dd4hep

input_file_path = "/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/IDEA_background_only/out_sim_edm4hep_background_186.root"

podio_reader = root_io.Reader(input_file_path)
metadata = podio_reader.get("metadata")[0]
cellid_encoding = metadata.get_parameter("CDCHHits__CellIDEncoding")
decoder = dd4hep.BitFieldCoder(cellid_encoding)
for event in podio_reader.get("events"):
    for dc_hit in event.get("CDCHHits"):
                    cellID = dc_hit.getCellID()
                    superLayer = decoder.get(cellID, "superLayer")
                    layer = decoder.get(cellID, "layer")
                    phi = decoder.get(cellID, "phi")
                    stereo = decoder.get(cellID, "stereo")
                    print("SuperLayer: ", superLayer, " Layer: ", layer, " Phi: ", phi, " Stereo: ", stereo)