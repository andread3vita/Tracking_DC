import numpy as np
import torch
import dgl
from torch_scatter import scatter_add, scatter_sum, scatter_min, scatter_max
from sklearn.preprocessing import StandardScaler
import time


# TODO remove the particles with little hits or mark them as noise
def get_number_hits(part_idx):
    number_of_hits = scatter_sum(torch.ones_like(part_idx), part_idx.long(), dim=0)
    return number_of_hits[1:].view(-1)

def find_cluster_id(hit_particle_link):
    unique_list_particles = list(np.unique(hit_particle_link))
    # print("unique_list_particles", unique_list_particles)
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
        # cluster_id = map(lambda x: unique_list_particles.index(x), hit_particle_link)
        # print(torch.Tensor(list(cluster_id)))
        cluster_id = cluster_id + 1  # torch.Tensor(list(cluster_id)) + 1
    return cluster_id, unique_list_particles


def scatter_count(input: torch.Tensor):
    return scatter_add(torch.ones_like(input, dtype=torch.long), input.long())


def fix_splitted_tracks(hit_particle_link, y):
    parents = y[:, -1]
    particle_ids = y[:, 4]
    change_pairs = []
    for indx, i in enumerate(parents):
        if (torch.sum(particle_ids == i) > 0) and y[indx, 5] > 0.01:
            change_pairs.append([parents[indx], particle_ids[indx]])
    # print("change_pairs", change_pairs)
    for pair in change_pairs:
        mask_change = hit_particle_link == pair[1]
        hit_particle_link[mask_change] = pair[0]

    return hit_particle_link


def create_inputs_from_table(output, get_vtx, cld=False, tau=False):
    graph_empty = False
    number_hits = np.int32(np.sum(output["pf_mask"][0]))

    number_part = np.int32(np.sum(output["pf_mask"][1]))
    #! idx of particle does not start at
    if tau:
        hit_particle_link = torch.tensor(output["pf_vectoronly"][0, 0:number_hits])
        hit_particle_link_tau = torch.tensor(output["pf_vectoronly"][1, 0:number_hits])
    else:
        hit_particle_link = torch.tensor(output["pf_vectoronly"][0, 0:number_hits])
        hit_particle_link_tau = None
    # print(output["pf_vectoronly"].shape[1], hit_particle_link.shape[0])
    # if output["pf_vectoronly"].shape[1] > hit_particle_link.shape[0]:
    # print("hit_particle_link", torch.unique(hit_particle_link))
    features_hits = torch.permute(
        torch.tensor(output["pf_features"][:, 0:number_hits]), (1, 0)
    )
    
    hit_type = features_hits[:, 9].clone()
    hit_type_one_hot = torch.nn.functional.one_hot(hit_type.long(), num_classes=2)
    if get_vtx:
        hit_type_one_hot = hit_type_one_hot
        features_hits = features_hits
        hit_particle_link = hit_particle_link
    else:
        mask_DC = hit_type == 0
        hit_type_one_hot = hit_type_one_hot[mask_DC]
        features_hits = features_hits[mask_DC]
        hit_particle_link = hit_particle_link[mask_DC]
        hit_type = hit_type[mask_DC]

    unique_list_particles = list(np.unique(hit_particle_link))
    # print("unique_list_particles", unique_list_particles)
    unique_list_particles = torch.Tensor(unique_list_particles).to(torch.int64)
    features_particles = torch.permute(
        torch.tensor(output["pf_vectors"][:, 0:number_part]),
        (1, 0),
    )

    y_data_graph = features_particles
    y_id = features_particles[:, 4]
    
    mask_particles = check_unique_particles(unique_list_particles, y_id)

    y_data_graph = features_particles[mask_particles]
    if tau:
        print("y_id", y_id)
        print("hit_particle_link_tau",torch.unique(hit_particle_link_tau))
        mask_taus = check_unique_particles(torch.unique(hit_particle_link_tau), y_id)
        pt_taus = features_particles[mask_taus][:,6]
        print("pt_taus", pt_taus)
    else:
        pt_taus = None
    # print("features_particles", features_particles.shape, torch.sum(mask_particles).item())
    if features_particles.shape[0] >= torch.sum(mask_particles).item():
        hit_particle_link = fix_splitted_tracks(hit_particle_link, y_data_graph)

        cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)
        unique_list_particles = torch.Tensor(unique_list_particles).to(torch.int64)

        features_particles = torch.permute(
            torch.tensor(output["pf_vectors"][:, 0:number_part]),
            (1, 0),
        )

        y_id = features_particles[:, 4]
        mask_particles = check_unique_particles(unique_list_particles, y_id)
        
        y_data_graph = features_particles[mask_particles]
        # print(y_data_graph.shape, unique_list_particles.shape)
        assert len(y_data_graph) == len(unique_list_particles)
    else:
        graph_empty = True
    # else:
    #     graph_empty = True
    if graph_empty:
        return [None]
    else:
        result = [
            y_data_graph,
            hit_type_one_hot,  # [no_tracks],
            cluster_id,
            hit_particle_link,
            features_hits,
            hit_type,
            hit_particle_link_tau,
            pt_taus
        ]
        return result


def check_unique_particles(unique_list_particles, y_id):
    mask = torch.zeros_like(y_id)
    for i in range(0, len(unique_list_particles)):
        id_u = unique_list_particles[i]
        if torch.sum(y_id == id_u) > 0:
            mask = mask + (y_id == id_u)
    return mask.to(bool)


def create_graph_tracking(
    output,
):
    # REMOVE DEPRECATED
    print("creating graph")
    (
        y_data_graph,
        hit_type_one_hot,  # [no_tracks],
        cluster_id,
        hit_particle_link,
        features_hits,
        hit_type,
    ) = create_inputs_from_table(output)

    #! REMOVING LOOPERS TO CHECK IF THE OUTPUTS ARE THE SAME
    # mask_not_loopers, mask_particles = remove_loopers(hit_particle_link, y_data_graph)
    # hit_type_one_hot = hit_type_one_hot[mask_not_loopers]
    # cluster_id = cluster_id[mask_not_loopers]
    # hit_particle_link = hit_particle_link[mask_not_loopers]
    # features_hits = features_hits[mask_not_loopers]
    # y_data_graph = y_data_graph[mask_particles]
    # cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)
    unique_list_particles = torch.unique(hit_particle_link)
    cluster_id = torch.searchsorted(
        unique_list_particles, hit_particle_link, right=False
    )
    if hit_type_one_hot.shape[0] > 0:
        graph_empty = False
        g = dgl.DGLGraph()
        g.add_nodes(hit_type_one_hot.shape[0])

        hit_features_graph = features_hits[:, 4:-2]
        # uvz = convert_to_conformal_coordinates(features_hits[:, 0:3])
        # polar = convert_to_polar_coordinates(uvz)
        # hit_features_graph = torch.cat(
        #     (uvz, polar), dim=1
        # )  # dim =8 #features_hits[:, 0:3],
        # ! currently we are not doing the pid or mass regression
        g.ndata["h"] = hit_features_graph
        g.ndata["hit_type"] = hit_type_one_hot
        g.ndata["particle_number"] = cluster_id
        g.ndata["particle_number_nomap"] = hit_particle_link
        g.ndata["pos_hits_xyz"] = features_hits[:, 0:3]
        g.ndata["e_dep"] = features_hits[:, 3]
        g.ndata["is_overlay"] = features_hits[:, -1]
        if len(y_data_graph) < 4:
            graph_empty = True
    else:
        graph_empty = True
        g = 0
        y_data_graph = 0
    if features_hits.shape[0] < 10:
        graph_empty = True
    # print("graph_empty", graph_empty, features_hits.shape[0])
    return [g, y_data_graph], graph_empty


def create_weights_for_shower_hits(g):
    weights = torch.ones_like(g.ndata["particle_number"])
    for i in torch.unique(g.ndata["particle_number"]):
        mask = g.ndata["particle_number"] == i
        mask2 = mask * (g.ndata["hit_type"] == 1)
        mask3 = mask * (g.ndata["hit_type"] == 0)
        a = g.ndata["hit_type"][mask]
        total_hits = len(a)
        n_vtx_hits = torch.sum(a)
        n_dch = total_hits - torch.sum(a)
        if n_dch > 0 and n_vtx_hits > 0:
            weights[mask3] = total_hits / (2 * n_dch)
            weights[mask2] = total_hits / (2 * n_vtx_hits)
    g.ndata["weights"] = weights
    return g


def create_graph_tracking_global(output, get_vtx=False, vector=False, tau=False, overlay=False):
    graph_empty = False
    result = create_inputs_from_table(output, get_vtx, tau=tau)
    if len(result) == 1:
        graph_empty = True
    else:
        (
            y_data_graph,
            hit_type_one_hot,
            cluster_id,
            hit_particle_link,
            features_hits,
            hit_type,
            hit_particle_link_tau,
            pt_taus
        ) = result
        # print("hit_type_one_hot previous to removing loopers", hit_type_one_hot.shape, hit_particle_link.shape)
        if not overlay:
            
            # Remove loopers from the list of hits and the list of particles
            mask_not_loopers, mask_particles = remove_loopers(
                hit_particle_link, y_data_graph, features_hits[:, 3:6], cluster_id
            )

            hit_type_one_hot = hit_type_one_hot[mask_not_loopers]
            cluster_id = cluster_id[mask_not_loopers]
            hit_particle_link = hit_particle_link[mask_not_loopers]
            if tau:
                hit_particle_link_tau = hit_particle_link_tau[mask_not_loopers]
            features_hits = features_hits[mask_not_loopers]
            hit_type = hit_type[mask_not_loopers]
            y_data_graph = y_data_graph[mask_particles]
            
            # Compute the cluster id after removing loopers
            cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)
            
        else:
            mask_not_loopers, mask_particles = remove_loopers_overlay(
                hit_particle_link, y_data_graph, features_hits[:, 3:6], cluster_id
            )

            hit_type_one_hot = hit_type_one_hot[mask_not_loopers]
            cluster_id = cluster_id[mask_not_loopers]
            hit_particle_link = hit_particle_link[mask_not_loopers]
            features_hits = features_hits[mask_not_loopers]
            hit_type = hit_type[mask_not_loopers]
            y_data_graph = y_data_graph[mask_particles]

            cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)
            
            mask_loopers, mask_particles = create_noise_label(
            hit_particle_link, y_data_graph, cluster_id, True, features_hits[:,-1]
            )
            hit_particle_link[mask_loopers] = -1
            y_data_graph = y_data_graph[mask_particles]
            cluster_id, unique_list_particles = find_cluster_id(hit_particle_link)

        if hit_type_one_hot.shape[0] > 0:
            mask_dc = hit_type == 0
            mask_vtx = hit_type == 1
            number_of_vtx = torch.sum(mask_vtx)
            number_of_dc = torch.sum(mask_dc)
            g = dgl.DGLGraph()
            if vector:
                g.add_nodes(number_of_vtx + number_of_dc)
            else:
                g.add_nodes(number_of_vtx + number_of_dc * 2)

            left_right_pos = features_hits[:, 3:9][mask_dc]
            left_post = left_right_pos[:, 0:3]
            right_post = left_right_pos[:, 3:]
            vector_like_data = vector
            if get_vtx:
                if vector_like_data:
                    particle_number = torch.cat(
                        (cluster_id[mask_vtx], cluster_id[mask_dc]), dim=0
                    )
                    particle_number_nomap = torch.cat(
                        (
                            hit_particle_link[mask_vtx],
                            hit_particle_link[mask_dc],
                        ),
                        dim=0,
                    )
                    if tau:
                        hit_link_tau = torch.cat(
                            (
                                hit_particle_link_tau[mask_vtx],
                                hit_particle_link_tau[mask_dc],
                            ),
                            dim=0,
                        )
                
                        cluster_id_tau, _ = find_cluster_id(hit_particle_link_tau)
                        pt_taus = pt_taus.view(-1)
                        if torch.sum(cluster_id_tau==0)>0:
                            pt_taus = torch.cat((torch.Tensor([0]), pt_taus),dim=0)
                            tau_mom = pt_taus[cluster_id_tau.long()]
                        else:
                            tau_mom = pt_taus[cluster_id_tau-1]
                        tau_mom_all = torch.cat((tau_mom[mask_vtx],tau_mom[mask_dc]), dim=0)

                    pos_xyz = torch.cat(
                        (features_hits[:, 0:3][mask_vtx], left_post), dim=0
                    )
                    is_overlay = torch.cat(
                        (features_hits[:,-1][mask_vtx].view(-1), features_hits[:,-1][mask_dc].view(-1)), dim=0
                    )
                    vector_data = torch.cat(
                        (0 * features_hits[:, 0:3][mask_vtx], right_post - left_post),
                        dim=0,
                    )
                    hit_type_all = torch.cat(
                        (hit_type[mask_vtx], hit_type[mask_dc]), dim=0
                    )
                    cellid = torch.cat(
                        (
                            features_hits[:, -1][mask_vtx].view(-1, 1),
                            features_hits[:, -1][mask_dc].view(-1, 1),
                        ),
                        dim=0,
                    )
                    # produced_from_secondary_ = torch.cat(
                    #     (
                    #         produced_from_secondary[mask_vtx].view(-1, 1),
                    #         produced_from_secondary[mask_dc].view(-1, 1),
                    #     ),
                    #     dim=0,
                    # )
                    # print(
                    #     features_hits[:, -1][mask_vtx].view(-1, 1).shape,
                    #     features_hits[:, -1][mask_dc].view(-1, 1).shape,
                    # )
                else:
                    particle_number = torch.cat(
                        (
                            cluster_id[mask_vtx],
                            cluster_id[mask_dc],
                            cluster_id[mask_dc],
                        ),
                        dim=0,
                    )
                    particle_number_nomap = torch.cat(
                        (
                            hit_particle_link[mask_vtx],
                            hit_particle_link[mask_dc],
                            hit_particle_link[mask_dc],
                        ),
                        dim=0,
                    )
                    if tau:
                        hit_link_tau = torch.cat(
                            (
                                hit_particle_link_tau[mask_vtx],
                                hit_particle_link_tau[mask_dc],
                                hit_particle_link_tau[mask_dc],
                            ),
                            dim=0,
                        )
                    pos_xyz = torch.cat(
                        (features_hits[:, 0:3][mask_vtx], left_post, right_post), dim=0
                    )
                    hit_type_all = torch.cat(
                        (hit_type[mask_vtx], hit_type[mask_dc], hit_type[mask_dc]),
                        dim=0,
                    )
                    cellid = torch.cat(
                        (
                            features_hits[:, -1][mask_vtx].view(-1, 1),
                            features_hits[:, -1][mask_dc].view(-1, 1),
                            features_hits[:, -1][mask_dc].view(-1, 1),
                        ),
                        dim=0,
                    )
                    # print(
                    #     features_hits[:, -1][mask_vtx].view(-1, 1).shape,
                    #     features_hits[:, -1][mask_dc].view(-1, 1).shape,
                    # )
            else:
                particle_number = torch.cat((cluster_id, cluster_id), dim=0)
                particle_number_nomap = torch.cat(
                    (hit_particle_link, hit_particle_link), dim=0
                )
                pos_xyz = torch.cat((left_post, right_post), dim=0)
                hit_type_all = torch.cat((hit_type, hit_type), dim=0)
            if vector_like_data:
                g.ndata["vector"] = vector_data
            g.ndata["hit_type"] = hit_type_all
            g.ndata["particle_number"] = particle_number
            g.ndata["particle_number_nomap"] = particle_number_nomap
            if tau:
                g.ndata["hit_link_tau"] = hit_link_tau
                g.ndata["tau_mom"] = tau_mom_all
            g.ndata["pos_hits_xyz"] = pos_xyz
            g.ndata["cellid"] = cellid
            g.ndata["unique_id"] = cellid.view(-1)
            g.ndata["is_overlay"] = is_overlay
            # g.ndata["weights"] = hit_type_all

            # g.ndata["produced_from_secondary_"] = produced_from_secondary_.view(-1)
            # g = create_weights_for_shower_hits(g)
            # uvz = convert_to_conformal_coordinates(pos_xyz)
            # g.ndata["conformal"] = uvz
            if len(y_data_graph) < 1:
                # print("problem here")
                graph_empty = True
            if features_hits.shape[0] < 10:
                graph_empty = True
        else:
            # print("hit_type_one_hot", hit_type_one_hot.shape, hit_particle_link.shape)
            graph_empty = True
    if graph_empty:
        g = 0
        y_data_graph = 0
    # print("graph_empty", graph_empty)
    return [g, y_data_graph], graph_empty

def remove_loopers_overlay(hit_particle_link, y, coord, cluster_id):
    unique_p_numbers = torch.unique(hit_particle_link)
    cluster_id_unique = torch.unique(cluster_id)
    # mask_p = y[:, 5] < 0.1
    # remove particles with a couple hits
    number_of_hits = get_number_hits(cluster_id)
    mask_hits = number_of_hits < 5

    mask_all = mask_hits.view(-1)
    list_remove = unique_p_numbers[mask_all.view(-1)]
    # print("number_of_hits", number_of_hits)
    # print("list_remove", cluster_id_unique[mask_all.view(-1)])
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
    return ~mask.to(bool), ~mask_particles.to(bool)




def remove_loopers(hit_particle_link, y, coord, cluster_id):
    unique_p_numbers = torch.unique(hit_particle_link)
    cluster_id_unique = torch.unique(cluster_id)
    # mask_p = y[:, 5] < 0.1

    min_x = scatter_min(coord[:, 0], cluster_id.long() - 1)[0]
    min_z = scatter_min(coord[:, 2], cluster_id.long() - 1)[0]
    min_y = scatter_min(coord[:, 1], cluster_id.long() - 1)[0]
    max_x = scatter_max(coord[:, 0], cluster_id.long() - 1)[0]
    max_z = scatter_max(coord[:, 2], cluster_id.long() - 1)[0]
    max_y = scatter_max(coord[:, 1], cluster_id.long() - 1)[0]
    diff_x = torch.abs(max_x - min_x)
    diff_z = torch.abs(max_z - min_z)
    diff_y = torch.abs(max_y - min_y)
    
    mask_x = diff_x > 1600
    mask_z = diff_z > 2800
    mask_y = diff_y > 1600 ####### 1600?
    
    mask_p = mask_x + mask_z + mask_y
    # remove particles with a couple hits
    number_of_hits = get_number_hits(cluster_id)
    mask_hits = number_of_hits < 5

    mask_all = mask_hits.view(-1) + mask_p.view(-1)
    list_remove = unique_p_numbers[mask_all.view(-1)]
    # print("number_of_hits", number_of_hits)
    # print("list_remove", cluster_id_unique[mask_all.view(-1)])
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
    return ~mask.to(bool), ~mask_particles.to(bool)


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



def create_noise_label(hit_particle_link, y, cluster_id, overlay=False,overlay_flag=None):
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

    number_of_overlay = scatter_sum(overlay_flag.view(-1), cluster_id.long(), dim=0)[1:].view(-1)
    mask_overlay = number_of_overlay>0
    mask_all =  mask_overlay.view(-1)

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
