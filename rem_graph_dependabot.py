'''
run single REM on chosen metric of health with ripple effect of highlighted dependencies
prepared for dependabot Pull Request

Zhe Chen (zkchen@uvic.ca)
'''
import networkx as nx # DiGraph, descendants, all_simple_paths, set_node_attributes, set_edge_attributes
import os # path.join, isfile
import json

from configs import REM_DEPENDABOT_HTML_OUTDIR, REM_DEPENDABOT_IMG_OUTDIR, REM_DEPENDABOT_HTML_URL, REM_DEPENDABOT_IMG_URL
from utils import *
from rem_filter import *
from rem_graphics import *


def prepare_filtered_graph(project_rt_sub_G, project_dev_sub_G, rt_ripple_effect_edges, dev_ripple_effect_edges, pname, keyword) -> nx.DiGraph:
    # RUNTIME
    temp_rt_G = filter_post_order_minimum(G=project_rt_sub_G, 
    ripples=rt_ripple_effect_edges, root=pname, keyword=keyword)
    for u,v,m in temp_rt_G.edges(data=True):
        if 'development' in m:
            del m['development']
    # DEVELOPMENT
    temp_dev_G = filter_post_order_minimum(G=project_dev_sub_G, 
    ripples=dev_ripple_effect_edges, root=pname, keyword=keyword)
    for u,v,m in temp_dev_G.edges(data=True):
        if 'runtime' in m:
            del m['runtime']

    return nx.compose(temp_rt_G, temp_dev_G).copy()


def prepare_ripple_effect_highlights(application_name, G, packages) -> tuple:
    nx.set_node_attributes(G, False, 'ripple')
    nx.set_edge_attributes(G, 'lightgrey', 'color')

    ripple_effect_edges = set()

    for p in packages:
        G.nodes()[p]['ripple'] = True
        for path in list(nx.all_simple_paths(G, source=application_name, target=p)):
            for i in range(len(path)-1):
                ripple_effect_edges.add((path[i], path[i + 1]))
                G.edges[(path[i], path[i+1])]['color'] = '#8b0000'
    
    return ripple_effect_edges


def prepare_sub_graphs(npm_G, rt_deps, dev_deps, application_name):
    """
    create target application (ROOT-APPLICATION) sub-graphs
    """
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

    return (application_rt_sub_G.copy(), application_dev_sub_G.copy())


def create(packages, depfile) -> tuple:
    """
    create REM graphs for dependabot to use in Pull Request
    returns:
        a url to be used in PR: http://.../.img,
        a url to be used as live tool: http://.../.html
    """
    keyword = 'final'

    # runtime and development dependencies
    depdata = {}
    try:
        depdata = json.loads(depfile)
    except:
        print('invalid input dependency file')
        return (None, None)

    rt_deps = depdata['dependencies'] if is_valid_key(depdata, 'dependencies') else None
    dev_deps = depdata['devDependencies'] if is_valid_key(depdata, 'devDependencies') else None
            
    if not rt_deps and not dev_deps: 
        print('target application does not have any runtime and development dependencies')
        return (None, None)

    # prepare npm packages graph
    prepare_npm_graph()
    npm_G = read_graph_json(NPMJSON)

    # add github application to the NPM network
    application_name = f'{depdata.get("name")}({depdata.get("version")})'
    # prepare sub-graph
    application_rt_sub_G, application_dev_sub_G = prepare_sub_graphs(npm_G, rt_deps, dev_deps, application_name)
    npm_G.clear()
    # prepare ripple-effects
    rt_ripple_effect_edges = prepare_ripple_effect_highlights(application_name=application_name, 
        G=application_rt_sub_G, packages=packages)
    dev_ripple_effect_edges = prepare_ripple_effect_highlights(application_name=application_name, 
        G=application_dev_sub_G, packages=packages)
    application_sub_G = nx.compose(application_rt_sub_G, application_dev_sub_G)
    # prepare graph layout
    pos = nx.nx_pydot.graphviz_layout(G=application_sub_G, prog='dot', root=application_name)
    # run filter
    filtered_application_sub_G = prepare_filtered_graph(project_rt_sub_G=application_rt_sub_G, project_dev_sub_G=application_dev_sub_G, 
        rt_ripple_effect_edges=rt_ripple_effect_edges, dev_ripple_effect_edges=dev_ripple_effect_edges, 
        pname=application_name, keyword=keyword)
    # run greyout
    gray_out_non_problematics(G=filtered_application_sub_G, root=application_name, keyword=keyword, re_metric='ripple')
    # assign node symbol
    assign_graph_node_symbol(application_sub_G, filtered_application_sub_G)

    html_outfile = f'{application_name}_{keyword}_min.html'
    img_outfile = f'{application_name}_{keyword}_min.png'
    html_out_path = join(REM_DEPENDABOT_HTML_OUTDIR, html_outfile)
    img_out_path = join(REM_DEPENDABOT_IMG_OUTDIR, img_outfile)
    html_out_link = join(REM_DEPENDABOT_HTML_URL, html_outfile)
    img_out_link = join(REM_DEPENDABOT_IMG_URL, img_outfile)

    plotly_graph_to_html(G=filtered_application_sub_G, pos=pos, 
                title=f'filtered Ripple-Effect of Metrics(REM) dependency graph for {application_name}', 
                key=keyword, outfile=html_out_path, out_img=img_out_path, re_metric='ripple')
    
    return (img_out_link, html_out_link)
            


'''
save for testing purpose
'''
if __name__ == '__main__':
    ff = '''
    {
        "name": "Brackets",
        "version": "1.15.0-0",
        "apiVersion": "1.15.0",
        "homepage": "http://brackets.io",
        "issues": {
            "url": "http://github.com/adobe/brackets/issues"
        },
        "repository": {
            "type": "git",
            "url": "https://github.com/adobe/brackets.git",
            "branch": "",
            "SHA": ""
        },
        "defaultExtensions": {
            "brackets-eslint": "3.2.0"
        },
        "dependencies": {
            "anymatch": "1.3.0",
            "async": "2.1.4",
            "chokidar": "1.6.1",
            "decompress-zip": "0.3.0",
            "fs-extra": "2.0.0",
            "lodash": "4.17.15",
            "npm": "3.10.10",
            "opn": "4.0.2",
            "request": "2.79.0",
            "semver": "5.3.0",
            "temp": "0.8.3",
            "ws": "~0.4.31"
        },
        "devDependencies": {
            "glob": "7.1.1",
            "grunt": "0.4.5",
            "husky": "0.13.2",
            "jasmine-node": "1.11.0",
            "grunt-jasmine-node": "0.1.0",
            "grunt-cli": "0.1.9",
            "phantomjs": "1.9.18",
            "grunt-lib-phantomjs": "0.3.0",
            "grunt-eslint": "19.0.0",
            "grunt-contrib-watch": "1.0.0",
            "grunt-contrib-jasmine": "0.4.2",
            "grunt-template-jasmine-requirejs": "0.1.0",
            "grunt-contrib-cssmin": "0.6.0",
            "grunt-contrib-clean": "0.4.1",
            "grunt-contrib-copy": "0.4.1",
            "grunt-contrib-htmlmin": "0.1.3",
            "grunt-contrib-less": "1.4.0",
            "grunt-contrib-requirejs": "0.4.1",
            "grunt-contrib-uglify": "0.2.0",
            "grunt-contrib-concat": "0.3.0",
            "grunt-targethtml": "0.2.6",
            "grunt-usemin": "0.1.11",
            "grunt-cleanempty": "1.0.3",
            "load-grunt-tasks": "3.5.0",
            "q": "1.4.1",
            "rewire": "1.1.2",
            "tar": "2.2.1",
            "webpack": "2.2.1",
            "xmldoc": "0.1.2",
            "zlib": "1.0.5"
        },
        "scripts": {
            "prepush": "npm run eslint",
            "postinstall": "grunt install",
            "test": "grunt test",
            "eslint": "grunt eslint"
        },
        "licenses": [
            {
                "type": "MIT",
                "url": "https://github.com/adobe/brackets/blob/master/LICENSE"
            }
        ]
    }
    '''
    print(create(['lodash'], ff))