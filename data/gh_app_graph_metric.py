'''
author: Zhe Chen (zkchen@uvic.ca)

This script reports metric about NPM GitHub applications dependency graph sizes

Input:
a directory path that contains package.json files for NPM applications
Stats:
average (median) direct and transitive (run time and development) dependencies for a set of NPM applications

|         | Direct Runtime | Transitive Runtime | Direct Development | Transitive Development |
|---------|----------------|--------------------|--------------------|------------------------|
| Lowest  |                |                    |                    |                        |
| Highest |                |                    |                    |                        |
| Mean    |                |                    |                    |                        |
| Median  |                |                    |                    |                        |
'''

import sys
import json
import networkx as nx
import sqlite3
import statistics
import csv
from os import listdir
from os.path import isfile, isdir, join
from beautifultable import BeautifulTable


def get_package_json(project_path: str):
    if isfile(project_path):
        file_content = open(project_path, 'r')
        try:
            # handle broken package.json file
            return json.load(file_content)
        except:
            return None
    else:
        return None


def create_graph(node_list: list, dep_rel_list: list) -> nx.DiGraph:
    npm_G = nx.DiGraph()
    # add every package as node in the network
    for name in node_list:
        npm_G.add_node(name, type='NPM')
    # connect packages according to their dependency relationships
    for deps in dep_rel_list:
        name, ver, dep_name, dep_cons = deps
        npm_G.add_edge(name, dep_name, dep_constraint=dep_cons)
    return npm_G


def get_npm_lists(db_path: str) -> tuple:
    # establish database connection
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # npm metadata list
    npm_node_query = ''' SELECT DISTINCT name FROM packages; '''
    c.execute(npm_node_query)
    node_list = c.fetchall()
    npm_dep_rel_query = ''' 
        SELECT project_name, project_ver, depend_name, depend_constraints 
        FROM depend; 
    '''
    c.execute(npm_dep_rel_query)
    rel_list = c.fetchall()

    return (node_list, rel_list)


'''
G: nx.DiGraph
dlist: list
root: str

-> tuple: (#direct, #transitive)
'''
def get_dep_stat_by_list(G: nx.DiGraph, dlist: list, root: str) -> tuple:
    if not dlist:
        return (0, 0)
    num_direct = len(dlist)
    G.add_node(root)
    
    for dep in dlist:
        G.add_edge(root, str(dep))
    sub_G = G.subgraph(list(nx.descendants(G, root))+[root])
    num_tran = max(sub_G.number_of_nodes()-num_direct-1, 0)
    G.remove_node(root)
    
    return (num_direct, num_tran)


def test_files(path: str):
    for fi in listdir(path):
        if not fi.endswith('package.json') or not isfile(join(path, fi)):
            continue
        print(fi)


def get_dep_size_lists(path: str) -> tuple:
    file_count = 0
    # tracker = ([0,0], [0,0]) # ([direct runtime, transitive runtime], [direct dev, transitive dev])
    pkg_names = []
    runtime_dep = ([],[]) # ()
    dev_dep = ([],[])
    node_list, rel_list = get_npm_lists(npm_db)
    npm_G = create_graph(node_list, rel_list)

    for fi in listdir(path):
        if not fi.endswith('package.json') or not isfile(join(path, fi)):
            continue
        name = fi[:len(fi)-13] # len('_package.json') = 13
        file_path = join(path, fi)
        mdata = get_package_json(file_path)
        if mdata is None:
            continue
        file_count += 1
        pkg_names.append(name)
        # runtime dependencies
        num_direct_rt = 0
        num_transitive_rt = 0
        if 'dependencies' in mdata and mdata['dependencies'] is not None:
            dep_list = list(mdata['dependencies'])
            num_direct_rt, num_transitive_rt = get_dep_stat_by_list(npm_G, dep_list, 'application_root')
        runtime_dep[0].append(num_direct_rt)
        runtime_dep[1].append(num_transitive_rt)
        # development dependencies
        num_direct_dev = 0
        num_transitive_dev = 0
        if 'devDependencies' in mdata and mdata['devDependencies'] is not None:
            dep_list = list(mdata['devDependencies'])
            num_direct_dev, num_transitive_dev = get_dep_stat_by_list(npm_G, dep_list, 'application_root')
        dev_dep[0].append(num_direct_dev)
        dev_dep[1].append(num_transitive_dev)
        print('[{ind}] name[{name}] #dir_rt[{dr}] #tran_rt[{tr}] #dir_dev[{dd}] #tran_dd[{td}]'
        .format(ind=file_count, name=name, dr=num_direct_rt, tr=num_transitive_rt,
        dd=num_direct_dev, td=num_transitive_dev))

    return (pkg_names, runtime_dep, dev_dep)


def report_stats(rt_dep: tuple, dev_dep: tuple):
    table = BeautifulTable()
    table.rows.append([min(rt_dep[0]), min(rt_dep[1]), min(dev_dep[0]), min(dev_dep[1])])
    table.rows.append([max(rt_dep[0]), max(rt_dep[1]), max(dev_dep[0]), max(dev_dep[1])])
    table.rows.append([statistics.mean(rt_dep[0]), statistics.mean(rt_dep[1]), 
    statistics.mean(dev_dep[0]), statistics.mean(dev_dep[1])])
    table.rows.append([statistics.median(rt_dep[0]), statistics.median(rt_dep[1]), 
    statistics.median(dev_dep[0]), statistics.median(dev_dep[1])])
    table.columns.header = ['Direct Runtime', 'Transitive Runtime', 'Direct Development', 'Transitive Development']
    table.rows.header = ['Lowest', 'Highest', 'Mean', 'Median']
    print(table)

def export_csv(names: list, rt_dep: tuple, dev_dep: tuple):
    if len(names) != len(rt_dep[0]) != len(dev_dep[0]):
        sys.exit('different size of inputs in export_csv().')
    with open('npm_dep_sizes.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['pkg_name', 'num_direct_runtime', 'num_trans_runtime', 'num_direct_development', 'num_trans_development'])
        for i in range(len(names)):
            writer.writerow([names[i], rt_dep[0][i], rt_dep[1][i], dev_dep[0][i], dev_dep[1][i]])
    print('exported to csv!')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('Usage: python3 gh_app_graph_metric.py <repo_path> <npm_db>')
    out_path = sys.argv[1]
    npm_db = sys.argv[2]
    name_list, runtime_dep, dev_dep = get_dep_size_lists(out_path)
    report_stats(runtime_dep, dev_dep)
    export_csv(name_list, runtime_dep, dev_dep)



    
