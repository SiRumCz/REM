'''
run single REM on chosen metric of health 
with ripple effect of deprecation

Zhe Chen (zkchen@uvic.ca)
'''
import networkx as nx # DiGraph
import sqlite3 # database connection
import sys # exit, argv
import os # path.join, isfile
from rem_graph_analysis import project_graph_analysis
from plain_graph_run import draw_plain_dependency_graph
from utils import *


def main():
    if len(sys.argv) < 3:
        sys.exit('Usage: python3 rem_graph_run_single.py <keyword> filter=True|False <github_url> [<out_folder>(htmls/)]')
    
    keyword = sys.argv[1]
    filter_flag = False
    if sys.argv[2] in ['filter=True','filter=true','filter=TRUE']:
        filter_flag = True

    if len(sys.argv) == 5:
        out_folder = sys.argv[4]
    else:
        out_folder = 'htmls'

    dbfile = os.path.join('data', 'dep_network_npm_search.db') # sqlite3 dependency network database

    # check if file exists
    if not os.path.isfile(dbfile):
        sys.exit('dependency database not found, please run preprocess fisrt')
    
    # parse github repo and split into owner, repo, and branch 
    repo_url = sys.argv[3]
    # naive check if input is github address
    if 'github' not in repo_url:
        sys.exit('input must be a github url, example: github.com/<owner>/<repo>')
    url_tokens = repo_url.split('/')
    # if input url has specified branch, otherwise will be master
    if 'tree' in url_tokens:
        owner, repo, tree, branch = url_tokens[-4:]
    else:
        owner, repo, branch = url_tokens[-2:]+['master']

    # establish database connection
    conn = sqlite3.connect(dbfile)
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

    # fetch github application package.json
    # runtime and development dependencies
    rt_deps, dev_deps = retrieve_package_json_deps(owner, repo, branch)
    if not rt_deps and not dev_deps: 
        sys.exit('application does not have any runtime and development dependencies')

    # add github application to the NPM network
    application_name = '{owner}:{repo}({branch})'.format(owner=owner, repo=repo, branch=branch)
    npm_G.add_node(application_name, type='GITHUB')
    temp_G = npm_G.copy()
    if rt_deps is not None:
        for k, v in rt_deps.items():
            temp_G.add_edge(application_name, str(k), runtime_constraint=str(v))
    application_rt_sub_G = temp_G.subgraph(list(nx.descendants(temp_G, application_name))+[application_name]).copy()
    for ed in application_rt_sub_G.edges():
        application_rt_sub_G.edges()[ed]['runtime'] = True
    temp_G = npm_G.copy()
    if dev_deps is not None:
        for k, v in dev_deps.items():
            temp_G.add_edge(application_name, str(k), dev_constraint=str(v))
    application_dev_sub_G = temp_G.subgraph(list(nx.descendants(temp_G, application_name))+[application_name]).copy()
    for ed in application_dev_sub_G.edges():
        application_dev_sub_G.edges()[ed]['development'] = True
    npm_G.clear()
    temp_G.clear()

    # create github application sub graph
    application_sub_G = nx.compose(application_rt_sub_G, application_dev_sub_G).copy()
    application_rt_sub_G.clear()
    application_dev_sub_G.clear()
    print('created sub-graph for {}. [{:,}] nodes, [{:,}] edges'
    .format(application_name, application_sub_G.number_of_nodes(), application_sub_G.number_of_edges()))

    # export dependency graph to HTML file
    # draw_plain_dependency_graph(G=application_sub_G, pname=application_name, outfile=os.path.join(out_folder, f'{application_name}_plain_graph.html'))
    outfile = os.path.join(out_folder, '{}-{}-{}_{}'.format(owner, repo, branch, keyword))
    project_graph_analysis(G=application_sub_G, pname=application_name, outfile=outfile, keyword=keyword, filter_flag=filter_flag)
    print('exported REM dependency graph to {}.'.format(out_folder))

    conn.close()


if __name__ == '__main__':
    main()