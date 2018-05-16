import snafu as snafu
import numpy as np
import os, sys
import networkx as nx

def list_subjects_and_categories(command, root_path):
    subjects=[]
    categories=[]
    groups=["all"]
    
    with open(command['fullpath'],'r') as fh:
        header=fh.readline().strip().decode("utf-8-sig").encode("utf-8").split(',')
        subj_idx = header.index("id")
        cat_idx = header.index("category")
        try:
            group_idx = header.index("group")
        except:
            group_idx = -1
        for line in fh:
            line=line.rstrip().split(',')
            if line[subj_idx] not in subjects:
                subjects.append(line[subj_idx])
            if line[cat_idx] not in categories:
                categories.append(line[cat_idx])
            if group_idx > -1:
                group_label = line[group_idx]
                if group_label == "all":        # "all" is a reserved group label, if user uses
                    group_label = "all.b"       # this label it will be replaced by "all.b", even though it won't compute statistics for that group in snafu
                if group_label not in groups:
                    groups.append(group_label)
    return { "type": "list_subjects_and_categories",
             "subjects": subjects, 
             "categories": categories,
             "groups": groups,
             "subject": subjects[0],
             "category": categories[0],
             "group": groups[0] }

def jsonGraph(g, items):
    from networkx.readwrite import json_graph
    json_data = json_graph.node_link_data(g)
    
    json_data['edges'] = json_data['links']
    json_data.pop('links', None)
    json_data.pop('directed', None)
    json_data.pop('multigraph', None)
    json_data.pop('graph', None)
    
    for i, j in enumerate(json_data['edges']):
        json_data['edges'][i]['id'] = i
    
    for i, j in enumerate(json_data['nodes']):
        json_data['nodes'][i]['label']=items[j['id']]
    
    return json_data

def label_to_filepath(x, root_path, filetype):
    filedict=dict()
    folder = root_path + "/" + filetype + "/"

    # since filenames are populated from directory listing there's no need to build a dict() anymore, but that's the way it's done still
    for filename in os.listdir(folder):
        if "csv" in filename:
            label = filename[0:filename.find('.')].replace('_',' ')
            filedict[label] = folder + filename
    try:
        filename = filedict[x]
    except:
        filename = None
    return filename

def data_properties(command, root_path):
   
    # turns array into string: "Mean (Std) [Min - Max]"
    def format_output(x):
        x_mean = str(round(np.mean(x),2))
        x_std = str(round(np.std(x),2))
        x_min = str(round(np.min(x),2))
        x_max = str(round(np.max(x),2))
        
        return x_mean + " (" + x_std + ") [" + x_min + " -- " + x_max + "]"
    
    command = command['data_parameters']
  
    if command['factor_type'] == "subject":
        ids = str(command['subject'])
        group = False
    elif command['factor_type'] == "group":
        ids = str(command['group'])            # without str() causes unicode issues for "all" :(
        group = True

    filedata = snafu.readX(ids, command['fullpath'], category=command['category'], spellfile=label_to_filepath(command['spellfile'], root_path, "spellfiles"), group=group)
    filedata.hierarchical()
    Xs = filedata.Xs
    items = filedata.items
    irts = filedata.irts
    numnodes = filedata.numnodes

    # initialize
    avg_cluster_size = []
    avg_num_cluster_switches = []
    num_lists = []
    avg_items_listed = []
    avg_unique_items_listed = []
    intrusions = []
    avg_num_intrusions = []
    perseverations = []
    avg_num_perseverations = []

    # kinda messy...
    for subjnum in range(len(Xs)):
        Xs[subjnum] = snafu.numToAnimal(Xs[subjnum], items[subjnum])
        if command['cluster_scheme'] != "None":
            cluster_sizes = snafu.clusterSize(Xs[subjnum], label_to_filepath(command['cluster_scheme'], root_path, "schemes"), clustertype=command['cluster_type'])
            avg_cluster_size.append(snafu.avgClusterSize(cluster_sizes))
            avg_num_cluster_switches.append(snafu.avgNumClusterSwitches(cluster_sizes))
            intrusions.append(snafu.intrusions(Xs[subjnum], label_to_filepath(command['cluster_scheme'], root_path, "schemes")))
            avg_num_intrusions.append(snafu.avgNumIntrusions(intrusions[-1]))
            perseverations.append(snafu.perseverations(Xs[subjnum]))
            avg_num_perseverations.append(snafu.avgNumPerseverations(Xs[subjnum]))
        else:
            avg_cluster_size = ["n/a"]
            avg_num_cluster_switches = ["n/a"]
            avg_num_intrusions = ["n/a"]
            avg_num_perseverations = ["n/a"]
        num_lists.append(len(Xs[subjnum]))
        avg_items_listed.append(np.mean([len(i) for i in Xs[subjnum]]))
        avg_unique_items_listed.append(np.mean([len(set(i)) for i in Xs[subjnum]]))

    # clean up / format data to send back, still messy
    intrusions = snafu.flatten_list(intrusions)
    perseverations = snafu.flatten_list(perseverations)

    if len(Xs) > 1:
        if command['cluster_scheme'] != "None":
            avg_cluster_size = format_output(avg_cluster_size)
            avg_num_cluster_switches = format_output(avg_num_cluster_switches)
            avg_num_intrusions = format_output(avg_num_intrusions)
            avg_num_perseverations = format_output(avg_num_perseverations)
        num_lists = format_output(num_lists)
        avg_items_listed = format_output(avg_items_listed)
        avg_unique_items_listed = format_output(avg_unique_items_listed)

    return { "type": "data_properties", 
             "num_lists": num_lists,
             "avg_items_listed": avg_items_listed,
             "intrusions": intrusions,
             "perseverations": perseverations,
             "avg_num_intrusions": avg_num_intrusions,
             "avg_num_perseverations": avg_num_perseverations,
             "avg_unique_items_listed": avg_unique_items_listed,
             "avg_num_cluster_switches": avg_num_cluster_switches,
             "avg_cluster_size": avg_cluster_size }

def network_properties(command, root_path):
    subj_props = command['data_parameters']
    command = command['network_parameters']

    # U-INVITE won't work with perseverations
    if command['network_method'] == "U-INVITE":
        removePerseverations=True
    else:
        removePerseverations=False
    
    if subj_props['factor_type'] == "subject":
        ids = str(subj_props['subject'])
        group = False
    elif subj_props['factor_type'] == "group":
        ids = str(subj_props['group'])            # without str() causes unicode issues for "all" :(
        group = True

    filedata = snafu.readX(ids, subj_props['fullpath'], category=subj_props['category'], spellfile=label_to_filepath(subj_props['spellfile'], root_path, "spellfiles"), removePerseverations=removePerseverations, group=group)
    filedata.nonhierarchical()
    Xs = filedata.Xs
    items = filedata.items
    irts = filedata.irts
    numnodes = filedata.numnodes
    
    toydata=snafu.DataModel({
            'numx': len(Xs),
            'trim': 1,
            'jump': float(command['jump_probability']),
            'jumptype': command['jump_type'],
            'priming': float(command['priming_probability']),
            'startX': command['first_item']})
    fitinfo=snafu.Fitinfo({
            'prior_method': "zeroinflatedbetabinomial",
            'prior_a': 1,
            'prior_b': 2,
            'zibb_p': 0.5,
            'startGraph': command['starting_graph'],
            'goni_size': int(command['goni_windowsize']),
            'goni_threshold': int(command['goni_threshold']),
            'followtype': "avg", 
            'prune_limit': 100,
            'triangle_limit': 100,
            'other_limit': 100})
   
    if command['prior']=="None":
        prior=None
    elif command['prior']=="USF":
        usf_file_path = "/snet/USF_animal_subset.snet"
        filename = root_path + usf_file_path
        
        usf_graph, usf_items = snafu.read_graph(filename)
        usf_numnodes = len(usf_items)
        priordict = snafu.genGraphPrior([usf_graph], [usf_items], fitinfo=fitinfo)
        prior = (priordict, usf_items)
        
    if command['network_method']=="RW":
        bestgraph = snafu.noHidden(Xs, numnodes)
    elif command['network_method']=="Goni":
        bestgraph = snafu.goni(Xs, numnodes, td=toydata, valid=0, fitinfo=fitinfo)
    elif command['network_method']=="Chan":
        bestgraph = snafu.chan(Xs, numnodes)
    elif command['network_method']=="Kenett":
        bestgraph = snafu.kenett(Xs, numnodes)
    elif command['network_method']=="FirstEdge":
        bestgraph = snafu.firstEdge(Xs, numnodes)
    elif command['network_method']=="U-INVITE":
        bestgraph, ll = snafu.uinvite(Xs, toydata, numnodes, fitinfo=fitinfo, debug=False, prior=prior)
    
    nxg = nx.to_networkx_graph(bestgraph)
    
    node_degree = np.mean(dict(nxg.degree()).values())
    nxg_json = jsonGraph(nxg, items)
    clustering_coefficient = nx.average_clustering(nxg)
    try:
        aspl = nx.average_shortest_path_length(nxg)
    except:
        aspl = "disjointed graph"
    
    return { "type": "network_properties",
             "node_degree": node_degree,
             "clustering_coefficient": clustering_coefficient,
             "aspl": aspl,
             "graph": nxg_json }

def quit(command, root_path): 
    return { "type": "quit",
             "status": "success" }

def error(msg):
    return { "type": "error",
             "msg": msg }
