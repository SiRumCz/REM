'''
run single REM on chosen metric of health with ripple effect of highlighted dependencies
prepared for dependabot Pull Request

Zhe Chen (zkchen@uvic.ca)
'''
import networkx as nx # DiGraph, descendants, all_simple_paths, set_node_attributes, set_edge_attributes
from os.path import join, isfile # path.join, isfile
import json
import uuid # uuid1
from PIL import ImageColor # ImageColor.getrgb()

from configs import REM_DEPENDABOT_HTML_OUTDIR, REM_DEPENDABOT_IMG_OUTDIR, REM_DEPENDABOT_HTML_URL, REM_DEPENDABOT_IMG_URL
from utils import *
from rem_filter import *
from rem_graphics import *


from flask import current_app


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


def prepare_ripple_effect_highlights(application_name, G, packages) -> set:
    nx.set_node_attributes(G, False, 'ripple')
    nx.set_edge_attributes(G, 'lightgrey', 'color')

    ripple_effect_edges = set()

    for p in packages:
        if not G.has_node(p):
            continue
        G.nodes()[p]['ripple'] = True
        for path in list(nx.all_simple_paths(G, source=application_name, target=p)):
            for i in range(len(path)-1):
                ripple_effect_edges.add((path[i], path[i + 1]))
                G.edges[(path[i], path[i+1])]['color'] = '#8b0000'
    
    return ripple_effect_edges


def prepare_sub_graphs(npm_G, rt_deps, dev_deps, application_name) -> tuple:
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
        current_app.logger.debug('target application does not contain any runtime and development dependencies')
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

    uname = str(uuid.uuid1())
    html_outfile = f'{uname}.html'
    img_outfile = f'{uname}.png'
    html_out_path = join(REM_DEPENDABOT_HTML_OUTDIR, html_outfile)
    img_out_path = join(REM_DEPENDABOT_IMG_OUTDIR, img_outfile)
    html_out_link = join(REM_DEPENDABOT_HTML_URL, html_outfile)
    img_out_link = join(REM_DEPENDABOT_IMG_URL, img_outfile)

    plotly_graph_to_html(G=filtered_application_sub_G, pos=pos, 
                title=f'filtered Ripple-Effect of Metrics(REM) dependency graph for {application_name}', 
                key=keyword, outfile=html_out_path, out_img=img_out_path, re_metric='ripple')
    
    return (img_out_link, html_out_link)


def encrypt_nodename(*params) -> str:
    key = '!'
    return key.join(params)


def decrypt_nodename(name:str) -> list:
    """
    dependency node will be stored as "<name>!<version>!<breadcrumbs>" (e.g. "lodash!4.17.11!root->@babel/core")
    """
    key = '!'
    if key not in name:
        return [name]
    return name.split(key)


def join_breadcrumbs(*paths) -> str:
    return '->'.join(paths)


def remove_last_level_breadcrumbs(breadcrumbs) -> str:
    if '->' not in breadcrumbs:
        return ''
    plist = breadcrumbs.split('->')
    return '->'.join(plist[:-1])


def split_G_by_dependency_type(G) -> tuple:
    runtime_G = nx.DiGraph()
    development_G = nx.DiGraph()
    for u,v,m in G.edges(data=True):
        if m.get('runtime'):
            runtime_G.add_node(u, **G.nodes()[u])
            runtime_G.add_node(v, **G.nodes()[v])
            runtime_G.add_edge(u,v, **m)
        if m.get('development'):
            development_G.add_node(u, **G.nodes()[u])
            development_G.add_node(v, **G.nodes()[v])
            development_G.add_edge(u,v, **m)
    return (runtime_G, development_G)


def combine_G_by_dependency_type(r_G, d_G):
    return nx.compose(r_G, d_G).copy()


def create_ripple_effect_subgraph(G, packages) -> nx.DiGraph:
    """
    create a graph model that contains only application root and ripples
    G: application graph model
    packages: list of packagesname and version. e.g. ['handlebars!4.1.2', 'dot-prop!4.2.0']
    """
    application_name = [x for x,m in G.nodes(data=True) if m.get('type') and m.get('type') == 'application-root'][0]
    name_table = {}
    for node, meta in G.nodes(data=True):
        if meta.get('type') == 'application-root':
            continue
        decrypted = decrypt_nodename(node)
        # { "lodash!4.17.11" : "lodash!4.17.11!root", }
        name_table[encrypt_nodename(decrypted[0], decrypted[1])] = node
    ripple_effect_nodes = set()
    for p in packages:
        p_nodename = name_table.get(p)
        if not p_nodename or not G.has_node(p_nodename):
            continue
        for path in nx.all_simple_paths(G, source=application_name, target=p_nodename):
           ripple_effect_nodes.update(path)
    sub_G = G.subgraph(list(ripple_effect_nodes)).copy()
    nx.set_node_attributes(sub_G, False, 'ripple')
    nx.set_edge_attributes(sub_G, '#8b0000', 'color')
    for p in packages:
        p_nodename = name_table.get(p)
        if p_nodename:
            sub_G.nodes()[p_nodename]['ripple'] = True
    return sub_G
                

def assign_edge_attrs(G: nx.DiGraph, data:dict):
    for key,val in data.items():
        nx.set_edge_attributes(G, val, key)


def node_meta_to_hover_text(meta: dict, ll: list=['version']) -> str:
    """
    meta must contain name attr
    """
    texts = f"<b>{meta.get('name')}</b>"
    for k in ll:
        texts += f"<br><b>{k}</b>: {meta.get(k)}"
    return texts


def assign_node_attrs(G: nx.DiGraph):
    """
    this part is hardcoded
    adding attributes:
     - text-label
     - text-hover
     - marker-size: node size
     - color: node color
     - marker-symbol: marker symbol
     - line-width: node line width (outter ring)
    """
    nx.set_node_attributes(G, 'grey', 'color')
    nx.set_node_attributes(G, 10, 'marker-size')
    nx.set_node_attributes(G, 'circle', 'marker-symbol')
    nx.set_node_attributes(G, 1, 'line-width')
    for n,m in G.nodes(data=True):
        if m and m.get('type') == 'application-root':
            G.nodes()[n]['color'] = '#6959CD'
            G.nodes()[n]['text-label'] = n
            G.nodes()[n]['text-hover'] = node_meta_to_hover_text({'name': n})
        else:
            node_info = decrypt_nodename(n)
            G.nodes()[n]['text-hover'] = node_meta_to_hover_text(
                {
                    'name': node_info[0], 
                    'version': node_info[1], 
                    'paths': node_info[2]
                })
            if m.get('ripple'):
                # only ripple and application can have label
                G.nodes()[n]['text-label'] = node_info[0]
                G.nodes()[n]['marker-size'] = 15
                G.nodes()[n]['line-width'] = 3
                G.nodes()[n]['color'] = 'red'


def assign_node_attrs_by_data(G:nx.DiGraph, data:dict):
    """
    add items in data as attributes to each node in graph G
    G: graph
    data: in dictionary
    e.g.
    {
        'lodash': {
            'final': 0.65123,
            'popularity': 0.6451231,
            ...
        },
        ...
    }
    """
    if not data:
        return
    # prepare name mapping first
    name_table = {}
    for node, meta in G.nodes(data=True):
        # if meta.get('type') == 'application-root':
        #     continue
        decrypted = decrypt_nodename(node)
        # { "lodash" : ["lodash!4.17.11!root"], }
        name_table[decrypted[0]] = name_table.get(decrypted[0])+[node] if name_table.get(decrypted[0]) else [node]
    for key, val in data.items():
        if not name_table.get(key):
            # this should not happen
            current_app.logger.debug(f'key {key} not found -- line {get_linenumber()}')
            print(key)
            continue
        for node in name_table.get(key):
            for attr_name, attr_val in val.items():
                G.nodes()[node][attr_name] = attr_val


def dependabot_issue_hoverlabel(node: tuple, key: str, re_metric: str=None, out_list:list=['version']) -> str:
    if re_metric:
        out_list.append(re_metric)
    nodename, data = node
    name = decrypt_nodename(nodename)[0]
    s = '<b>'+name+'</b>'
    for k,v in sorted(data.items()):
        if k == key:
            s += '<br><b><i>{}</i></b>: {}'.format(k, v)
        elif k in out_list:
            s += '<br><b>{}</b>: {}'.format(k, v)
    return s


def add_to_installed_dependencies(installed_dependencies, data, breadcrumbs):
    """
    add current data into a dependency list which is used for tracking down the right dependency
    if lodash(4.17.11) installed under root->@babel/core
    it is stored as:
    installed_dependencies = {
        "lodash": [
            {
                "version": "4.17.11",
                "breadcrumbs": "root->@babel/core"
            }
        ]
    }
    """
    if not data:
        return
    for name, metadata in data.items():
        dependency = {
            'version': metadata.get('version'),
            'breadcrumbs': breadcrumbs
        }
        if name in installed_dependencies:
            installed_dependencies[name].insert(0, dependency)
        else:
            installed_dependencies[name] = [dependency]


def find_closest_dependency_node_name(installed_dependencies, dependency_name, breadcrumbs) -> str:
    """
    find the closest dependency in installed_dependencies
    the closest dependency would be :
    1. the one that share same breadcrumbs
    2. the one that share the same breadcrumbs when last level removed
    3. repeat step 2
    4. it should stop until the very root level
    """
    deplist = installed_dependencies.get(dependency_name)
    if not deplist:
        return None
    else:
        while (breadcrumbs != ''):
            for depdata in deplist:
                dep_nodename = encrypt_nodename(dependency_name, depdata.get('version'), depdata.get('breadcrumbs'))
                if breadcrumbs == depdata.get('breadcrumbs'):
                    return dep_nodename
            breadcrumbs = remove_last_level_breadcrumbs(breadcrumbs)
    return None


def build_from_package_json(G: nx.DiGraph, metadata: dict):
    """
    package.json file provides a direct link between the application to the top-level dependencies
    this function creates such link and also updates the dependency relationship type as eiter
    runtime and development dependency.
    """
    # 1. retrieve runtime and development dependencies
    dependencies = metadata.get('dependencies')
    dev_dependencies = metadata.get('devDependencies')
    # check if has any dependency
    if not dependencies and not dev_dependencies:
        return
    # 2. prepare application nodename and breadcrumbs
    # note that application_nodename equals breadcrumbs
    application_nodename = f"{metadata.get('name')}({metadata.get('version')})"
    # cehcking if root application node exists
    if not G.has_node(application_nodename) or G.nodes()[application_nodename].get('type') != 'application-root':
        current_app.logger.debug(f'required dependency root ({application_nodename}) not found')
        return
    # 3. prepare mapping table e.g. from <name>!<breadcrumbs> to <name>!<version>!<breadcrumbs>
    name_table = {}
    for node, meta in G.nodes(data=True):
        if meta.get('type') == 'application-root':
            continue
        decrypted = decrypt_nodename(node)
        # { "lodash!root" : "lodash!4.17.11!root", }
        name_table[encrypt_nodename(decrypted[0], decrypted[2])] = node
    # 4. process runtime dependencies
    if dependencies:
        runtime_dependencies = {application_nodename}
        runtime_dependencies.update({name_table.get(encrypt_nodename(x, application_nodename)) for x in dependencies.keys()})
        for dependency in dependencies.keys():
            # dependency should be on top-level, therefore they are under breadcrumbs of application root
            # because we don't have a version, we will compare name and breadcrumbs to find the right one
            dependency_hashname = encrypt_nodename(dependency, application_nodename)
            if not G.has_node(name_table.get(dependency_hashname)):
                current_app.logger.debug(f'required top-level dependency ({name_table.get(dependency_hashname)}) not found')
            G.add_edge(application_nodename, name_table.get(dependency_hashname))
            # update all runtime dependencies
            runtime_dependencies.update(nx.descendants(G, name_table.get(dependency_hashname)))
        for edge in G.subgraph(runtime_dependencies).edges():
            G.edges()[edge]['runtime'] = True
    # 5. process development dependencies
    if dev_dependencies:
        development_dependencies = {application_nodename}
        development_dependencies.update({name_table.get(encrypt_nodename(x, application_nodename)) for x in dev_dependencies.keys()})
        for dependency in dev_dependencies.keys():
            # dependency should be on top-level, therefore they are under breadcrumbs of application root
            # because we don't have a version, we will compare name and breadcrumbs to find the right one
            dependency_hashname = encrypt_nodename(dependency, application_nodename)
            if not G.has_node(name_table.get(dependency_hashname)):
                current_app.logger.debug(f'required top-level dependency ({name_table.get(dependency_hashname)}) not found')
            G.add_edge(application_nodename, name_table.get(dependency_hashname))
            # update all development dependencies
            development_dependencies.update(nx.descendants(G, name_table.get(dependency_hashname)))
        for edge in G.subgraph(development_dependencies).edges():
            G.edges()[edge]['development'] = True


def build_from_lockfile(G: nx.DiGraph, metadata: dict):
    """
    G: networkx directed graph model
    metadata: lockfile data
    """
    name = metadata.get('name')
    version = metadata.get('version')
    breadcrumbs = f'{name}({version})' # which is also the root directory
    G.add_node(breadcrumbs, type='application-root')
    dependencies = metadata.get('dependencies')
    installed_dependencies = {}
    add_to_installed_dependencies(installed_dependencies, dependencies, breadcrumbs)
    for dep_name, dep_metadata in dependencies.items():
        # add encrypted name to distinguish same dependency from different versions paths
        # e.g. "lodash!4.17.11!root->@babel/core"
        dep_nodename = encrypt_nodename(dep_name, dep_metadata.get('version'), breadcrumbs)
        G.add_node(dep_nodename)
        dep_metadata['name'] = dep_name
        dep_metadata['node_name'] = dep_nodename
        recursive_build_from_lockfile(G, installed_dependencies, dep_metadata, breadcrumbs)


def recursive_build_from_lockfile(G: nx.DiGraph, installed_dependencies: dict, dependent: dict, breadcrumbs: str):
    """
    G: networkx directed graph model
    dependent: lockfile dependencies in dictionary
    dependent will contain:
        'name': name of current dependency
        'version': exact version of current dependency
        'dep': if true, then current dependency is a dev dependency ONLY
        'requires': dependencies of current dependency same as in package.json with <name>: <version_constraint>
        'dependencies': packages that are going to be installed at dependent's node_module
    """
    if not dependent:
        return
    node_name = dependent.get('node_name')
    name = dependent.get('name')
    version = dependent.get('version')
    requires = dependent.get('requires')
    if not requires:
        return
    # prepare current path (breadcrumbs)
    curr_breadcrumbs = join_breadcrumbs(breadcrumbs, name)
    dependencies = dependent.get('dependencies')
    # update installed_dependencies list
    # these dependencies will be added to current path (breadcrumbs)
    add_to_installed_dependencies(installed_dependencies, dependencies, curr_breadcrumbs)
    for req_name, req_vc in requires.items():
        req_node_name = find_closest_dependency_node_name(installed_dependencies, req_name, curr_breadcrumbs)
        if not req_node_name:
            # should not happen, let's log it
            current_app.logger.debug(f'required dependency ({req_name}) not found on the tree')
        else:
            G.add_edge(node_name, req_node_name)
    if not dependencies:
        return
    for dep_name, dep_meta in dependencies.items():
        dep_meta['name'] = dep_name
        # their nodes will be added to graph first
        dep_meta['node_name'] = encrypt_nodename(dep_name, dep_meta.get('version'), curr_breadcrumbs)
        G.add_node(dep_meta['node_name'])
        recursive_build_from_lockfile(G, installed_dependencies, dep_meta, curr_breadcrumbs)
         

def create_from_lockfile_and_package_json(package_json: str, lockfile: str) -> nx.DiGraph:
    """
    create sub REM graph for dependabot to use in Pull Request
    returns:
        a url to be used in PR: http://.../.img,
        a url to be used as live tool: http://.../.html
    show only the ripple-effect(including affected dependencies 
    during the ripple-effect) from the vulnerable dependencies to application root
    """
    depdata = {}
    package_json_data = {}
    try:
        depdata = json.loads(lockfile)
        package_json_data = json.loads(package_json)
    except:
        current_app.logger.debug('invalid input dependency files')
        return (None, None)
    # read runtime and development dependencies from lockfile
    dependencies = depdata.get('dependencies')
    if not dependencies: 
        current_app.logger.debug('target application does not contain any dependency')
        return (None, None)
    application_G = nx.DiGraph()
    # build graph model from lockfile
    build_from_lockfile(application_G, depdata)
    # build graph model from package.json
    build_from_package_json(application_G, package_json_data)
    return application_G


def create_dependabot_issue_rem_graph(package_json: str, lockfile: str, highlight_metric:str='final') -> tuple:
    """
    create a rem graph that contains a complete dependency graph and metrics of health
    """
    # create a full dependency graph
    G = create_from_lockfile_and_package_json(package_json, lockfile)
    # generate graph layout
    root = [x for x,m in G.nodes(data=True) if m.get('type') == 'application-root'][0]
    pos = nx.nx_pydot.graphviz_layout(G=G, prog='dot', root=root)
    # fetch health metrics from database and add to graph
    dependency_list = {decrypt_nodename(n)[0] for n,m in G.nodes(data=True) if m.get('type') != 'application-root'}
    health_metrics = fetch_metric_data_from_list_by_db(plist=dependency_list)
    assign_node_attrs_by_data(G, health_metrics)
    # assign version attr
    data = {decrypt_nodename(n)[0]: {
        'version': decrypt_nodename(n)[1]
        } for n,m in G.nodes(data=True) if m.get('type') != 'application-root'}
    assign_node_attrs_by_data(G, data)
    # assign some basic plotly attrs
    data = {decrypt_nodename(n)[0]: {
        'color': set_node_color_by_scores(node=(n,m), key=highlight_metric),
        'marker-size': 10, 
        'marker-symbol': 'circle', 
        'line-width': 1,
        'text-hover': dependabot_issue_hoverlabel(node=(n,m), key=highlight_metric, out_list=['version', 'final', 'quality', 'popularity', 'maintenance'])
        } for n,m in G.nodes(data=True)}
    assign_node_attrs_by_data(G, data)
    # separate by type
    runtime_G, development_G = split_G_by_dependency_type(G)
    # assign attrs to edges
    assign_edge_attrs(runtime_G, {'line-width':0.8, 'opacity':1, 'color':'grey'})
    assign_edge_attrs(development_G, {'line-width':3.2, 'opacity':0.7, 'color':'lightgrey'})
    # generate out files
    uname = str(uuid.uuid1())
    html_outfile = f'{uname}.html'
    img_outfile = f'{uname}.png'
    html_out_path = join(REM_DEPENDABOT_HTML_OUTDIR, html_outfile)
    img_out_path = join(REM_DEPENDABOT_IMG_OUTDIR, img_outfile)
    html_out_link = join(REM_DEPENDABOT_HTML_URL, html_outfile)
    img_out_link = join(REM_DEPENDABOT_IMG_URL, img_outfile)
    # create graph files
    create_deepndabot_issue_rem_graph(r_G=runtime_G, d_G=development_G, pos=pos, metric=highlight_metric,
        title=f'Ripple-Effect of Health Metric Graph of {root}', html_out=html_out_path, img_out=img_out_path)
    return (img_out_link, html_out_link)


def create_dependabot_pr_rem_subgraph(packages: list, package_json: str, lockfile: str) -> tuple:
    """
    creates a rem subgraph that contains only the application and paths and nodes affected by 
    the highlighted dependencies.
    """
    # create a full dependency graph
    G = create_from_lockfile_and_package_json(package_json, lockfile)
    # create a ripple-effect of metrics subgraph
    rem_sub_G = create_ripple_effect_subgraph(G, packages)
    runtime_rem_sub_G, development_rem_sub_G = split_G_by_dependency_type(rem_sub_G)
    # assign attrs to be sent to plotly
    assign_edge_attrs(runtime_rem_sub_G, {'line-width':0.8, 'opacity':1})
    assign_edge_attrs(development_rem_sub_G, {'line-width':3.2, 'opacity':0.7})
    assign_node_attrs(runtime_rem_sub_G)
    assign_node_attrs(development_rem_sub_G)
    # prepare graph layout
    root = [x for x,m in rem_sub_G.nodes(data=True) if m.get('type') == 'application-root'][0]
    pos = nx.nx_pydot.graphviz_layout(G=rem_sub_G, prog='dot', root=root)
    # prepare output files and links
    uname = str(uuid.uuid1())
    html_outfile = f'{uname}.html'
    img_outfile = f'{uname}.png'
    html_out_path = join(REM_DEPENDABOT_HTML_OUTDIR, html_outfile)
    img_out_path = join(REM_DEPENDABOT_IMG_OUTDIR, img_outfile)
    html_out_link = join(REM_DEPENDABOT_HTML_URL, html_outfile)
    img_out_link = join(REM_DEPENDABOT_IMG_URL, img_outfile)
    # create graph files
    create_deepndabot_pr_rem_subgraph(r_G=runtime_rem_sub_G, d_G=development_rem_sub_G, pos=pos, 
        title=f'Ripple-Effect of Vulnerability Metric Graph of {root}', html_out=html_out_path, img_out=img_out_path)
    return (img_out_link, html_out_link)


def test_subgraph_on_lockfile():
    """
    test on subgraph using lockfile and package.json
    """
    lockfile_one = join('D:\\myGithubRepo\\REM\\test', 'lockfiles', 'package-lock.json')
    package_json_one = join('D:\\myGithubRepo\\REM\\test', 'package_jsons', 'package.json')
    lockfile = open(lockfile_one, 'r').read()
    package_json_file = open(package_json_one, 'r').read()
    print(create_dependabot_pr_rem_subgraph(['handlebars!4.1.2', 'dot-prop!4.2.0'], package_json_file, lockfile))


def test_issue_rem_graph_on_lockfile():
    """
    test on full rem graph using lockfile and package.json
    """
    test_locs = [
        'D:\\myGithubRepo\\rem_testrepos\\agalwood-Motrix',
        'D:\\myGithubRepo\\rem_testrepos\\algorithm-visualizer',
        'D:\\myGithubRepo\\rem_testrepos\\DustinBrett-x'
    ]

    for test in test_locs:
        lockfile_loc = join(test, 'package-lock.json')
        package_json_loc = join(test, 'package.json')
        lockfile = open(lockfile_loc, 'r').read()
        package_json = open(package_json_loc, 'r').read()
        print(create_dependabot_issue_rem_graph(package_json=package_json, 
            lockfile=lockfile, highlight_metric='final'))


if __name__ == '__main__':
    # test_subgraph_on_lockfile()
    test_issue_rem_graph_on_lockfile()