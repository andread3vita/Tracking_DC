import numpy as np
import torch
import dgl
from torch_scatter import scatter_add, scatter_sum, scatter_min, scatter_max
from sklearn.preprocessing import StandardScaler


# TODO remove the particles with little hits or mark them as noise
def get_number_hits(part_idx):
    number_of_hits = scatter_sum(torch.ones_like(part_idx), part_idx.long(), dim=0)
    return number_of_hits[1:].view(-1)


# def find_cluster_id(hit_particle_link):

#         non_noise_idx = torch.where(hit_particle_link != -1)[0]
#         noise_idx = torch.where(hit_particle_link == -1)[0]
#         non_noise_particles = list(np.array(unique_list_particles[1:]))
#         cluster_id = map(
#             lambda x: non_noise_particles.index(x), hit_particle_link[non_noise_idx]
#         )
#         cluster_id_small = torch.Tensor(list(cluster_id)) + 1
#         cluster_id = hit_particle_link.clone()
#         cluster_id[non_noise_idx] = cluster_id_small
#         cluster_id[noise_idx] = 0


def find_cluster_id(hit_particle_link):
    unique_list_particles = list(np.unique(hit_particle_link))

    if np.sum(np.array(unique_list_particles) == -1) > 0:
        non_noise_idx = torch.where(hit_particle_link != -1)[0]  #
        noise_idx = torch.where(hit_particle_link == -1)[0]  #
        unique_list_particles1 = torch.unique(hit_particle_link)[1:]
        cluster_id_ = torch.searchsorted(
            unique_list_particles1, hit_particle_link[non_noise_idx], right=False
        )
        cluster_id_small = 1.0 * cluster_id_ + 1
        cluster_id = hit_particle_link.clone()
        cluster_id[non_noise_idx] = cluster_id_small
        cluster_id[noise_idx] = 0
    else:
        unique_list_particles1 = torch.unique(hit_particle_link)
        cluster_id = torch.searchsorted(
            unique_list_particles1, hit_particle_link, right=False
        )
        cluster_id = cluster_id + 1
    return cluster_id, unique_list_particles


def scatter_count(input: torch.Tensor):
    return scatter_add(torch.ones_like(input, dtype=torch.long), input.long())


def create_inputs_from_table(output, predict=False, tau=False, overlay=False):
    number_hits = np.int32(np.sum(output["pf_mask"][0]))
    # print("number_hits", number_hits)
    number_part = np.int32(np.sum(output["pf_mask"][1]))
    #! idx of particle does not start at 1
    hit_particle_link = torch.tensor(output["pf_vectoronly"][0, 0:number_hits])
    if tau:
        hit_particle_link_tau = torch.tensor(output["pf_vectoronly"][1, 0:number_hits])
        unique_tau_label = torch.unique(hit_particle_link_tau)
    else:
        hit_particle_link_tau = None
    if predict:
        ct_track = torch.tensor(output["pf_vectoronly"][2, 0:number_hits])
        unique_id = torch.tensor(output["pf_vectoronly"][3, 0:number_hits])
    else:
        ct_track = None
        unique_id = None
    features_hits = torch.permute(
        torch.tensor(output["pf_features"][:, 0:number_hits]), (1, 0)
    )
    hit_type = features_hits[:, 3].clone()
    if overlay:
        overlay_flag =  features_hits[:, -1].clone()
    else:
        overlay_flag = None
    # hit_type_one_hot = torch.nn.functional.one_hot(hit_type.long(), num_classes=2)

    cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)

    # features particles
    unique_list_particles = torch.Tensor(unique_list_particles).to(torch.int64)
    # print("unique_list_particles", unique_list_particles)
    features_particles = torch.permute(
        torch.tensor(output["pf_vectors"][:, list(unique_list_particles)]),
        (1, 0),
    )
    if tau and predict:
        tau_mom = torch.tensor(output["pf_vectors"][6, list(unique_tau_label.long().numpy())])
        # print(tau_mom)
    else:
        tau_mom = None
    
    y_data_graph = features_particles

    assert len(y_data_graph) == len(unique_list_particles)

    
    result = [
        y_data_graph,
        cluster_id,
        hit_particle_link,
        features_hits,
        hit_type,
        ct_track,
        unique_id,
        hit_particle_link_tau,
        tau_mom, 
        overlay_flag
    ]
    return result

def theta_slope():
    def func(edges):
        distance = torch.abs((edges.src["theta"] - edges.dst["theta"])/(edges.src["rho"] - edges.dst["rho"]+1e-6))
        return {"theta_slope": distance}

    return func

def create_graph_tracking_CLD(output, predict, tau, overlay=False):

    (
        y_data_graph,
        cluster_id,
        hit_particle_link,
        features_hits,
        hit_type,
        ct_track_label,
        unique_id,
        hit_particle_link_tau,
        tau_mom, 
        overlay_flag
    ) = create_inputs_from_table(output, predict=predict, tau=tau, overlay=overlay)
    
    mask_loopers, mask_particles = create_noise_label(
        hit_particle_link, y_data_graph, cluster_id, overlay, overlay_flag
    )
    # hit_type_one_hot = hit_type_one_hot[mask_not_loopers]
    # cluster_id[mask_not_loopers] = 0
    hit_particle_link[mask_loopers] = -1
    y_data_graph = y_data_graph[mask_particles]
    cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)
    if hit_particle_link.shape[0] > 0:
        graph_empty = False
        g = dgl.DGLGraph()
        g.add_nodes(hit_particle_link.shape[0])
        # this is for the new baseline
        # i, j = torch.tril_indices(g.number_of_nodes()-1, g.number_of_nodes()-1)
        # g.add_edges(i,j)
        # g = dgl.to_simple(g) 
        # g =dgl.remove_self_loop(g)
        # hit_features_graph = torch.cat(
        #     (features_hits[:, 4:-1], hit_type_one_hot), dim=1
        # )  # dims = 7
        hit_features_graph = features_hits
        # uvz = convert_to_conformal_coordinates(features_hits[:, 0:3])
        # polar = convert_to_polar_coordinates(uvz)
        # hit_features_graph1 = torch.cat(
        #     (uvz, polar), dim=1
        # )  # dim =8 #features_hits[:, 0:3],
        # # ! currently we are not doing the pid or mass regression
        # g.ndata["z"] = uvz[:,2].view(-1,1)
        # g.ndata["rho"]=polar[:,0].view(-1,1)
        # g.ndata["theta"]=polar[:,1].view(-1,1)
        # g.ndata["h_graph_constr"] = hit_features_graph1
        g.ndata["h"] = hit_features_graph
        g.ndata["hit_type"] = hit_type
        g.ndata["particle_number"] = cluster_id.to(torch.float32)
        g.ndata["particle_number_nomap"] = hit_particle_link
        if tau:
            g.ndata["hit_particle_link_tau"] = hit_particle_link_tau
        g.ndata["pos_hits_xyz"] = features_hits[:, 0:3]
        if overlay:
            g.ndata["isoverlay"] =overlay_flag

        if predict:
            if tau:
                cluster_id_tau, _ = find_cluster_id(hit_particle_link_tau)
                tau_mom = tau_mom.view(-1)
                if torch.sum(cluster_id_tau==0)>0:
                    g.ndata["tau_mom"] = tau_mom[cluster_id_tau.long()]
                else:
                    g.ndata["tau_mom"] = tau_mom[cluster_id_tau-1]
            g.ndata["ct_track_label"] = ct_track_label
            g.ndata["unique_id"] = unique_id

        # i = g.edges()[0]
        # j =  g.edges()[1]
       
        # # only if baseline
        # g.apply_edges(theta_slope())
        # g.edata["theta_slope"][g.edata["theta_slope"]==-np.inf]=0
        # mask_weights = g.edata["theta_slope"]<0.3
        # i_updated = i[mask_weights.view(-1)]
        # j_updated = j[mask_weights.view(-1)]
        # g_updated = dgl.graph((i_updated, j_updated), num_nodes=g.number_of_nodes())
        # g_updated.ndata["pos_hits_xyz"]=g.ndata["pos_hits_xyz"]
        # g_updated.ndata["particle_number"] = g.ndata["particle_number"]
        # g_updated.ndata["z"] = g.ndata["z"]
        # g_updated.ndata["rho"] = g.ndata["rho"]
        # g_updated.ndata["theta"] = g.ndata["theta"]
        # g_updated.ndata["h_graph_constr"] = g.ndata["h_graph_constr"]
        # g_updated.ndata["hit_type"] = g.ndata["hit_type"]


        if len(y_data_graph) < 4:
            graph_empty = True

    else:
        graph_empty = True
        g = 0
        y_data_graph = 0
    if features_hits.shape[0] < 10:
        graph_empty = True

    return [g, y_data_graph], graph_empty


def create_noise_label(hit_particle_link, y, cluster_id, overlay=False, overlay_flag=None):
    """
    Created a label to each node in the graph to determine if it is noise 
    Hits are considered as noise if:
    - They belong to an MC that left no more than 4 hits (mask_hits)
    - The particle has p below x, currently it is set to 0 so not condition on this case (mask_p)
    - The hit is overlaid background
    #TODO overlay hits could leave a track (there can be more than a couple hits for a given particle, for now we don't ask to reconstruc these but it might make our alg worse)

    Args:
        hit_particle_link (torch Tensor): particle the nodes belong to
        y (torch Tensor): particle features
        cluster_id (torch Tensor): particle the node belongs to from 1,N (no gaps)
        overlay (bool): is there background overlay in the data
        overlay_flag (torch Tensor): which hits are background
    Returns:
        mask (torch bool Tensor): which hits are noise
        mask_particles: which particles should be removed 
    """
    unique_p_numbers = torch.unique(hit_particle_link)
    mask_p = y[:, 4] < 0.0
    number_of_hits = get_number_hits(cluster_id)
    mask_hits = number_of_hits < 4
    if overlay:
        number_of_overlay = scatter_sum(overlay_flag.view(-1), cluster_id.long(), dim=0)[1:].view(-1)
        mask_overlay = number_of_overlay>0
        mask_all = mask_hits.view(-1) + mask_p.view(-1) + mask_overlay.view(-1)
    else:
        mask_all = mask_hits.view(-1) + mask_p.view(-1)
    list_remove = unique_p_numbers[mask_all.view(-1)]

    if len(list_remove) > 0:
        mask = torch.tensor(np.full((len(hit_particle_link)), False, dtype=bool))
        for p in list_remove:
            mask1 = hit_particle_link == p
            mask = mask1 + mask
    else:
        mask = torch.tensor(np.full((len(hit_particle_link)), False, dtype=bool))
    list_p = unique_p_numbers
    if len(list_remove) > 0:
        mask_particles = np.full((len(list_p)), False, dtype=bool)
        for p in list_remove:
            mask_particles1 = list_p == p
            mask_particles = mask_particles1 + mask_particles
    else:
        mask_particles = torch.tensor(np.full((len(list_p)), False, dtype=bool))
    return mask.to(bool), ~mask_particles.to(bool)


def convert_to_conformal_coordinates(xyz):
    # https://pytorch-geometric.readthedocs.io/en/latest/_modules/torch_geometric/transforms/polar.html
    x = xyz[:, 0]
    y = xyz[:, 1]
    u = x / (torch.square(x) + torch.square(y))
    v = y / (torch.square(x) + torch.square(y))
    uvz = torch.cat((u.view(-1, 1), v.view(-1, 1), xyz[:, 2].view(-1, 1)), dim=1)
    return uvz


def convert_to_polar_coordinates(uvz):
    cart = uvz[:, 0:2]
    rho = torch.norm(cart, p=2, dim=-1).view(-1, 1)
    from math import pi as PI

    theta = torch.atan2(cart[:, 1], cart[:, 0]).view(-1, 1)
    theta = theta + (theta < 0).type_as(theta) * (2 * PI)
    rho = rho / (rho.max())
    # theta = theta / (2 * PI)

    polar = torch.cat([rho, theta], dim=-1)
    return polar
