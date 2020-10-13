'''
utility functions

Zhe Chen (zkchen@uvic.ca)
'''

import networkx as nx
from networkx.classes import graph
import requests # get
import json
import sqlite3
import sys
from os.path import join, isfile
from configs import NPMDB, NPMJSON
from networkx.readwrite import json_graph


def is_valid_key(data: dict, key: str) -> bool:
    '''
    check if key is valid
    '''
    return data and key and (key in data) and (data[key])


def retrieve_package_json_deps(owner, repo, branch) -> tuple:
    '''
    extract runtime and development dependencies from 
    github.com/owner/repo/branch/package.json
    returns tuple of dict: (dependencies: dict, devDependencies: dict)
    dependencies: runtime
    devDependencies: development
    '''
    npm_file_path = 'https://raw.github.com/{owner}/{repo}/{branch}/package.json'\
        .format(owner=owner, repo=repo, branch=branch)

    print('retrieving package.json file from [{}]..'.format(npm_file_path), end='')
    try:
        resp = requests.get(npm_file_path)
        if resp.status_code != 200:
            print('failed, please make sure the github repo is not valid and public.')
            return (None, None)
        else:
            data = resp.json()
            runtime_dep = data['dependencies'] if is_valid_key(data, 'dependencies') else None
            dev_dep = data['devDependencies'] if is_valid_key(data, 'devDependencies') else None
            print('done.')
            return (runtime_dep, dev_dep)
    except:
        print('request failed.')
        return (None, None)


def create_graph(node_list: list, dep_rel_list: list) -> nx.DiGraph:
    npm_G = nx.DiGraph()
    # add every package as node in the network
    for pkg in node_list:
        name, latest, deprecated, final, popularity, quality, maintenance = pkg
        deprecated = True if (deprecated == 1) else False
        # round scores to 2 decimal place
        final = round(final, 2) if final else final
        popularity = round(popularity, 2) if popularity else popularity
        maintenance = round(maintenance, 2) if maintenance else maintenance
        quality = round(quality, 2) if quality else quality
        npm_G.add_node(name, version=latest, deprecated=deprecated, final=final, 
                   popularity=popularity, quality=quality, maintenance=maintenance, type='NPM')
    # connect packages according to their dependency relationships
    for deps in dep_rel_list:
        name, ver, dep_name, dep_cons = deps
        npm_G.add_edge(name, dep_name, dep_constraint=dep_cons)
    return npm_G


def prepare_npm_graph(reload_flag: bool = False):
    # skip if reload is false and json file exists
    if (reload_flag is False) and isfile(NPMJSON):
        print(f'use {NPMJSON}')
        return
    
    # check if file exists
    if not isfile(NPMDB):
        sys.exit('NPM dependency database not found, please run preprocess.py fisrt')
    
    # establish database connection
    conn = sqlite3.connect(NPMDB)
    c = conn.cursor()
    
    # npm metadata list
    npm_meta_query = ''' 
        SELECT n.name, n.latest, n.deprecated, 
        s.final, s.popularity, s.quality, s.maintenance
        FROM packages AS n
        LEFT JOIN scores AS s
        USING (name); 
    '''
    print('fetching NPM metadata..', end='')
    c.execute(npm_meta_query)
    npm_with_deprecated_list = c.fetchall()
    print('done. [{:,}]'.format(len(npm_with_deprecated_list)))

    # npm dependency relationships list
    npm_dep_query = ''' SELECT * FROM depend; '''
    print('fetching NPM dependency relationships..', end='')
    c.execute(npm_dep_query)
    npm_dep_list = c.fetchall()
    print('done. [{:,}]'.format(len(npm_dep_list)))

    # create di-graph to store npm package network
    print('creating NPM dependency graph..', end='')
    npm_G = create_graph(npm_with_deprecated_list, npm_dep_list)
    print('done. [{:,}] nodes, [{:,}] edges'
    .format(npm_G.number_of_nodes(), npm_G.number_of_edges()))
    dump_graph_json(npm_G, NPMJSON)
    conn.close()


def read_graph_json(filepath) -> nx.Graph:
    with open(filepath) as json_file:
        data = json.load(json_file)
    print(f'read from {filepath}')
    return json_graph.node_link_graph(data, directed=True)


def dump_graph_json(G, filepath: str = 'temp.json'):
    data = json_graph.node_link_data(G)
    with open(filepath, 'w') as dfile:
        json.dump(data, dfile)
    print(f'json file dumped at {filepath}')
