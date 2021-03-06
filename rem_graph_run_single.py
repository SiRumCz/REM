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
from configs import NPMJSON, FILTER_ENABLE


def main():
    if len(sys.argv) < 3:
        sys.exit('Usage: python3 rem_graph_run_single.py <keyword> <github_url> [<out_folder>(htmls/)]')
    
    keyword = sys.argv[1]

    if len(sys.argv) == 5:
        out_folder = sys.argv[3]
    else:
        out_folder = 'htmls'

    # parse github repo and split into owner, repo, and branch 
    repo_url = sys.argv[2]
    # naive check if input is github address
    if 'github' not in repo_url:
        sys.exit('input must be a github url, example: github.com/<owner>/<repo>')
    url_tokens = repo_url.split('/')
    # if input url has specified branch, otherwise will be master
    if 'tree' in url_tokens:
        owner, repo, tree, branch = url_tokens[-4:]
        del tree
    else:
        owner, repo, branch = url_tokens[-2:]+['master']
    
    prepare_npm_graph()
    npm_G = read_graph_json(NPMJSON)

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
    outfile = f'{owner}-{repo}-{branch}_{keyword}'
    project_graph_analysis(G=application_sub_G, pname=application_name, outfile=outfile, outfolder=out_folder, keyword=keyword, filter_flag=FILTER_ENABLE)


if __name__ == '__main__':
    main()