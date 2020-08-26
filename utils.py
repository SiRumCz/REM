'''
utility functions

Zhe Chen (zkchen@uvic.ca)
'''

import networkx as nx
import requests # get


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
        npm_G.add_node(name, version=latest, deprecated=deprecated, final=final, 
                   popularity=popularity, quality=quality, maintenance=maintenance, type='NPM')
    # connect packages according to their dependency relationships
    for deps in dep_rel_list:
        name, ver, dep_name, dep_cons = deps
        npm_G.add_edge(name, dep_name, dep_constraint=dep_cons)
    return npm_G