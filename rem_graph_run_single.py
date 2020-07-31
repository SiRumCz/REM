import networkx as nx # DiGraph
import sqlite3 # database connection
import json # dump()
import sys # exit, argv
import os # path.join, isfile
import requests # get
import plotly.graph_objects as go # create figure
import plotly.express as px # colorscale
import math # ceil


def dict_to_text(node: tuple, key: str) -> str:
    name, d = node
    s = '<b>'+name+'</b>'
    for k,v in sorted(d.items()):
        if k == key:
            s += '<br><b><i>{}</i></b>: {}'.format(k, v)
        else:
            s += '<br><b>{}</b>: {}'.format(k, v)
    return s


def set_node_color(node: tuple) -> str:
    '''
    #6959CD - software
    green   - active     :)
    red     - deprecared :(
    '''
    name, meta = node
    if is_valid_key(data=meta, key='type') and meta['type'] == 'GITHUB':
        return '#6959CD'
    return 'red' if is_valid_key(data=meta, key='deprecated') and meta['deprecated'] else 'green'


def set_node_color_by_scores(node: tuple, key: str) -> str:
    '''
    node: full node information
    key: final, popularity, quality, maintenance
    '''
    name, meta = node
    if is_valid_key(data=meta, key='type') and meta['type'] == 'GITHUB':
        return '#6959CD'
    scale = px.colors.diverging.RdYlGn
    return scale[math.ceil(meta[key]*10)] if (meta and key in meta and meta[key] is not None) else 'black'


def set_node_marker_size(node: tuple) -> int:
    '''
    regular size: 8
    deprecated size: 15
    '''
    name, meta = node
    return 15 if is_valid_key(meta, 'deprecated') and meta['deprecated'] else 10


def set_node_line_width(node: tuple) -> int:
    '''
    regular size: 1
    deprecated size: 3
    '''
    name, meta = node
    return 3 if is_valid_key(meta, 'deprecated') and meta['deprecated'] else 1


def plotly_graph_to_html(G: nx.Graph, pos: dict, title: str = '', key: str = 'final', outfile: str = 'temp.html'):
    ''' 
    G         : networkx graph
    pos       : positions of graph node
    title     : graph title 
    key       : display of nodes based on scores (final(default)|popularity|quality|maintenance)
    outfile   : output path for html file
    '''
    # separating runtime and development dependency networks
    # github software subgraph
    # RUNTIME
    rt_sub_G = nx.DiGraph()
    # DEVELOPMENT
    dev_sub_G = nx.DiGraph()
    for u,v,m in G.edges(data=True):
        if 'runtime' in m and m['runtime'] is True:
            rt_sub_G.add_node(u, **G.nodes()[u])
            rt_sub_G.add_node(v, **G.nodes()[v])
            rt_sub_G.add_edge(u,v, **m)
        if 'development' in m and m['development'] is True:
            dev_sub_G.add_node(u, **G.nodes()[u])
            dev_sub_G.add_node(v, **G.nodes()[v])
            dev_sub_G.add_edge(u,v, **m)
    
    Xv_gh_rt=[pos[n][0] for n in list(rt_sub_G.nodes())]
    Yv_gh_rt=[pos[n][1] for n in list(rt_sub_G.nodes())]
    Xv_gh_dev=[pos[n][0] for n in list(dev_sub_G.nodes())]
    Yv_gh_dev=[pos[n][1] for n in list(dev_sub_G.nodes())]
    # vertice color lists (fill or line)
    v_color_gh_rt=[set_node_color(n) for n in list(rt_sub_G.nodes(data=True))]
    v_color_gh_dev=[set_node_color(n) for n in list(dev_sub_G.nodes(data=True))]
    # vertice node color based on scores system (fill or line)
    v_scores_gh_rt=[set_node_color_by_scores(n, key) for n in list(rt_sub_G.nodes(data=True))]
    v_scores_gh_dev=[set_node_color_by_scores(n, key) for n in list(dev_sub_G.nodes(data=True))]
    # vertice size
    v_size_gh_rt=[set_node_marker_size(n) for n in list(rt_sub_G.nodes(data=True))]
    v_size_gh_dev=[set_node_marker_size(n) for n in list(dev_sub_G.nodes(data=True))]
    # vertice line width
    v_width_gh_rt=[set_node_line_width(n) for n in list(rt_sub_G.nodes(data=True))]
    v_width_gh_dev=[set_node_line_width(n) for n in list(dev_sub_G.nodes(data=True))]
    # vertice text lists
    v_text_gh_rt=[dict_to_text(n, key) for n in list(rt_sub_G.nodes(data=True))]
    v_text_gh_dev=[dict_to_text(n, key) for n in list(dev_sub_G.nodes(data=True))]
    
    # edges
    Xed_github_rt=[] # RUNTIME
    Yed_github_rt=[]
    Xed_github_dev=[] # DEVELOPMENT
    Yed_github_dev=[]
    # edge color lists
    ed_color_github_rt=[]
    ed_color_github_dev=[]

    tmp_gh_rt_nodes=[]
    tmp_gh_dev_nodes=[]
    
    # GITHUB RUNTIME
    for u, v, m in list(rt_sub_G.edges(data=True)):
        Xed_github_rt+=[pos[u][0],pos[v][0]]
        Yed_github_rt+=[pos[u][1],pos[v][1]]
        ed_color_github_rt+=[m['color']]*2
        
    # GITHUB DEVELOPMENT
    for u, v, m in list(dev_sub_G.edges(data=True)):
        Xed_github_dev+=[pos[u][0],pos[v][0]]
        Yed_github_dev+=[pos[u][1],pos[v][1]]
        ed_color_github_dev+=[m['color']]*2
        
    # edge traces
    data=[]
    for i in range(0, len(Xed_github_rt)-2, 2):
        data+=[go.Scatter(
                x=Xed_github_rt[i:i+2],
                y=Yed_github_rt[i:i+2],
                mode='lines',
                legendgroup="gh_rt",
                showlegend=False,
                line=dict(color=ed_color_github_rt[i], width=0.8)
        )]
        
    if len(Xed_github_rt) > 0:
        data+=[go.Scatter(
                x=Xed_github_rt[len(Xed_github_rt)-2:],
                y=Yed_github_rt[len(Yed_github_rt)-2:],
                mode='lines',
                legendgroup="gh_rt",
                name="runtime dependency relationships (dark-red means is affected by package deprecation)",
                line=dict(color=ed_color_github_rt[len(ed_color_github_rt)-1], width=0.8)
        )]
    
    for i in range(0, len(Xed_github_dev)-2, 2):
        data+=[go.Scatter(
            x=Xed_github_dev[i:i+2],
            y=Yed_github_dev[i:i+2],
            mode='lines',
            legendgroup="gh_dev",
            showlegend=False,
            line=dict(color=ed_color_github_dev[i], width=3.2)
        )]
        
    if len(Xed_github_dev) > 0:
        data+=[go.Scatter(
                x=Xed_github_dev[len(Xed_github_dev)-2:],
                y=Yed_github_dev[len(Yed_github_dev)-2:],
                mode='lines',
                legendgroup="gh_dev",
                name="development dependency relationships (dark-red means is affected by package deprecation)",
                line=dict(color=ed_color_github_dev[len(ed_color_github_dev)-1], width=3.2)
        )]
    
    # node traces
    if len(Xv_gh_rt) > 0:
        data+=[go.Scatter(x=Xv_gh_rt,
               y=Yv_gh_rt,
               mode='markers',
               legendgroup="gh_rt",               
               name='runtime dependencies (red outline means deprecation)',
               marker=dict(symbol=[m['symbol'] for x,m in rt_sub_G.nodes(data=True)],
                             size=v_size_gh_rt,
                             opacity=1,
                             color=v_scores_gh_rt,
                             line=dict(color=v_color_gh_rt, width=v_width_gh_rt),
                             colorscale="RdYlGn",
                             showscale=True,
                             cmin=0.0,
                             cmid=0.5,
                             cmax=1.0,
                             colorbar=dict(
                                title=dict(text='metric of health: '+key, side='right'),
                                thickness=10
                             )),
               text=v_text_gh_rt,
               hovertemplate = '%{text}'
               )]
    if len(Xv_gh_dev) > 0:
        data+=[go.Scatter(x=Xv_gh_dev,
               y=Yv_gh_dev,
               mode='markers',
               legendgroup="gh_dev",               
               name='development dependencies (red outline means deprecation)',
               marker=dict(symbol=[m['symbol'] for x,m in dev_sub_G.nodes(data=True)],
                             size=v_size_gh_dev,
                             opacity=1,
                             color=v_scores_gh_dev,
                             line=dict(color=v_color_gh_dev, width=v_width_gh_dev),
                             colorscale="RdYlGn",
                             showscale=True,
                             cmin=0.0,
                             cmid=0.5,
                             cmax=1.0,
                             colorbar=dict(
                                title=dict(text='metric of health: '+key, side='right'),
                                thickness=10
                             )),
               text=v_text_gh_dev,
               hovertemplate = '%{text}'
               )]

    fig=go.Figure(data=data)
    
    fig.update_layout(
        title=title,
        title_x=0.5,
        legend=dict(orientation="h", 
                    font=dict(size=12)),
        xaxis=go.layout.XAxis(showticklabels=False),
        yaxis=go.layout.YAxis(showticklabels=False),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    x_pos_list = [v[0] for v in pos.values()]
    y_pos_list = [v[1] for v in pos.values()]
    xoffset = (max(x_pos_list) - min(x_pos_list)) * 0.05
    yoffset = (max(y_pos_list) - min(y_pos_list)) * 0.05
    fig.update_xaxes(range=[min(x_pos_list)-xoffset, max(x_pos_list)+xoffset])
    fig.update_yaxes(range=[min(y_pos_list)-yoffset, max(y_pos_list)+yoffset])
    
    return fig.write_html(outfile)


def is_valid_key(data: dict, key) -> bool:
    '''
    check if key is valid
    '''
    return data and key and (key in data) and (data[key])


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


def filter_by_score(G: nx.Graph, ripples: set, root: str, keyword: str):
    '''
    minimize graph size
    if the successor node has higher or equal <keyword> score 
    -> 
    filter by removing edge
    '''
    temp_G = G.copy() # copy of original graph
    visited = {n: False for n in list(temp_G.nodes())}
    queue = [root]

    while len(queue) > 0:
        name = queue.pop(0)
        if visited[name]:
            continue
        visited[name] = True
        meta = temp_G.nodes()[name]
        if is_valid_key(meta, 'type') \
        and meta['type'] == 'GITHUB':
            queue += list(temp_G.neighbors(name))
            continue
        score = meta[keyword] if keyword in meta else None
        for dep_name in list(temp_G.neighbors(name)):
            dep_meta = temp_G.nodes()[dep_name]
            dep_score = dep_meta[keyword] if keyword in dep_meta else None
            if score and dep_score:
                if dep_score >= score:
                    if (name, dep_name) not in ripples:
                        temp_G.remove_edge(name, dep_name)
                    else:
                        queue.append(dep_name)
                else:
                    queue.append(dep_name)
            elif dep_score is None:
                if (name, dep_name) not in ripples:
                    temp_G.remove_edge(name, dep_name)
                else:
                    queue.append(dep_name)
            elif score is None:
                queue.append(dep_name)

    return G.subgraph(list(temp_G.subgraph(list(nx.descendants(temp_G, root))+[root]).nodes())).copy()


def assign_graph_node_symbol(full_G: nx.Graph, filtered_G: nx.Graph):
    for node in full_G:
        full_G.nodes()[node]['symbol'] = 'circle'
        if node in filtered_G:
            full_size = len(list(full_G.neighbors(node)))
            filtered_size = len(list(filtered_G.neighbors(node)))
            # if a node in a filtered graph hasless children, then mark it 'circle-cross'
            filtered_G.nodes()[node]['symbol'] = 'circle-cross' if filtered_size < full_size else 'circle'
    return


def project_graph_analysis(G: nx.Graph, pname: str, outfile: str, keyword: str, filter_flag: bool):
    print('NPM software:', pname)
    
    ''' pre. check if exists '''
    if pname not in list(G.nodes()):
        sys.exit('\nsoftware not found.')
    
    ''' pre. check if keyword is valid '''
    if keyword not in ['final', 'quality', 'popularity', 'maintenance']:
        sys.exit('\ninvalid keyword.')
    
    ''' 1. direct dependencies '''
    dependency_list = list(G.edges(pname, data=True))
    
    # RUNTIME
    runtime_dep_list = [t for t in dependency_list if 'runtime_constraint' in t[2]]
    print('\nDirect Runtime Dependency View ({:,})'.format(len(runtime_dep_list)))
    for u,v,m in runtime_dep_list:
        print('{} : {}'.format(v,m['runtime_constraint']))
        
    # DEVELOPMENT
    development_dep_list = [t for t in dependency_list if 'dev_constraint' in t[2]]
    print('\nDirect Dev Dependency View ({:,})'.format(len(development_dep_list)))
    for u,v,m in development_dep_list:
        print('{} : {}'.format(v,m['dev_constraint']))
        
    ''' 2. transitive dependnecies '''
    # github software subgraph
    # RUNTIME
    project_rt_sub_G = nx.DiGraph()
    # DEVELOPMENT
    project_dev_sub_G = nx.DiGraph()
    for u,v,m in G.edges(data=True):
        if 'runtime' in m and m['runtime'] is True:
            project_rt_sub_G.add_node(u, **G.nodes()[u])
            project_rt_sub_G.add_node(v, **G.nodes()[v])
            project_rt_sub_G.add_edge(u,v, **m)
        if 'development' in m and m['development'] is True:
            project_dev_sub_G.add_node(u, **G.nodes()[u])
            project_dev_sub_G.add_node(v, **G.nodes()[v])
            project_dev_sub_G.add_edge(u,v, **m)
    
    # print graph shape
    print()
    print('NPM package RUNTIME dependency network for top starred github project ({}) shape:'
    .format(pname))
    print('nodes:', project_rt_sub_G.number_of_nodes())
    print('edges:', project_rt_sub_G.number_of_edges())
    print('NPM package DEVELOPMENT dependency network for top starred github project ({}) shape:'
    .format(pname))
    print('nodes:', project_dev_sub_G.number_of_nodes())
    print('edges:', project_dev_sub_G.number_of_edges())
    
    ''' 3. deprecated packages '''
    print()
    rt_sub_g_deprecated_list = []
    for x,y in project_rt_sub_G.nodes(data=True):
        if y and y['type'] == 'NPM' and y['deprecated']:
            rt_sub_g_deprecated_list.append((x, y))
            
    dev_sub_g_deprecated_list = []
    for x,y in project_dev_sub_G.nodes(data=True):
        if y and y['type'] == 'NPM' and y['deprecated']:
            dev_sub_g_deprecated_list.append((x, y))
            
    if (len(rt_sub_g_deprecated_list) == 0 and len(dev_sub_g_deprecated_list) == 0):
        print('Congratulations! There is no deprecated packages in the software.')
        ''' 4. node link diagram of the dependency network '''
        project_sub_G = nx.compose(project_rt_sub_G, project_dev_sub_G)
        assign_graph_node_symbol(project_sub_G, project_sub_G)
        for pair in list(project_sub_G.edges()):
            project_sub_G.edges()[pair]['color'] = 'grey'
        
        # using dot diagram which shows the hierarchy of the network
        dot_pos = nx.nx_pydot.pydot_layout(project_sub_G, prog='dot')
        plotly_graph_to_html(G=project_sub_G, pos=dot_pos, 
        title='REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'.html')
    else:
        ''' 3.a number of deprecated packages '''
        if len(rt_sub_g_deprecated_list) > 0:
            print('There is(are) **{:,}** deprecated package(s) in the RUNTIME network:'
              .format(len(rt_sub_g_deprecated_list)))
        if len(dev_sub_g_deprecated_list) > 0:
            print('There is(are) **{:,}** deprecated package(s) in the DEVELOPMENT network:'
              .format(len(dev_sub_g_deprecated_list)))
        
        # RUNTIME
        if len(rt_sub_g_deprecated_list) > 0:
            print('\nRUNTIME:')
            for name, meta in rt_sub_g_deprecated_list:
                print('{} : {}'.format(name, json.dumps(meta, indent=2)))
        
        # DEVELOPMENT
        if len(dev_sub_g_deprecated_list) > 0:
            print('\nDEVELOPMENT:')
            for name, meta in dev_sub_g_deprecated_list:
                print('{} : {}'.format(name, json.dumps(meta, indent=2)))
            
        ''' 3.b number of affect edges '''
        # RUNTIME
        rt_ripple_effect_edges = set()
        rt_ripple_effect_nodes = set()
        if len(rt_sub_g_deprecated_list) > 0:
            print('\nRUNTIME:')
            for deprecated_name, meta in rt_sub_g_deprecated_list:  
                path_list = list(nx.all_simple_paths(project_rt_sub_G, source=pname, target=deprecated_name))
                for path in path_list:
                    for i in range(len(path)-1):
                        rt_ripple_effect_nodes.add(path[i])
                        rt_ripple_effect_nodes.add(path[i + 1])
                        rt_ripple_effect_edges.add((path[i], path[i + 1]))
        
            print(\
        '**{:,}** nodes ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the network.'
              .format(len(rt_ripple_effect_nodes),
                      100 * len(rt_ripple_effect_nodes) / project_rt_sub_G.number_of_nodes(),
                      len(rt_sub_g_deprecated_list)))
            print(\
        '**{:,}** edges ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the network.'
              .format(len(rt_ripple_effect_edges),
                      100 * len(rt_ripple_effect_edges) / project_rt_sub_G.number_of_edges(),
                      len(rt_sub_g_deprecated_list)))
        
        # DEVELOPMENT
        dev_ripple_effect_edges = set()
        dev_ripple_effect_nodes = set()
        if len(dev_sub_g_deprecated_list) > 0: 
            print('\nDEVELOPMENT:')
            for deprecated_name, meta in dev_sub_g_deprecated_list:  
                path_list = list(nx.all_simple_paths(project_dev_sub_G, source=pname, target=deprecated_name))
                for path in path_list:
                    for i in range(len(path)-1):
                        dev_ripple_effect_nodes.add(path[i])
                        dev_ripple_effect_nodes.add(path[i + 1])
                        dev_ripple_effect_edges.add((path[i], path[i + 1]))
        
            print(\
        '**{:,}** nodes ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the network.'
              .format(len(dev_ripple_effect_nodes),
                      100 * len(dev_ripple_effect_nodes) / project_dev_sub_G.number_of_nodes(),
                      len(dev_sub_g_deprecated_list)))
            print(\
        '**{:,}** edges ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the network.'
              .format(len(dev_ripple_effect_edges),
                      100 * len(dev_ripple_effect_edges) / project_dev_sub_G.number_of_edges(),
                      len(dev_sub_g_deprecated_list)))

        ''' 3.c(pre-4.a) adding color attributes on the edges for network '''
        for pair in list(project_rt_sub_G.edges()):
            project_rt_sub_G.edges()[pair]['color'] = 'lightgrey'\
            if pair not in rt_ripple_effect_edges else '#8b0000'

        for pair in list(project_dev_sub_G.edges()):
            project_dev_sub_G.edges()[pair]['color'] = 'lightgrey'\
            if pair not in dev_ripple_effect_edges else '#8b0000'

        ''' 3.d(pre-4.b) graph filter that reduces node number '''
        project_sub_G = nx.compose(project_rt_sub_G, project_dev_sub_G)
        # using dot diagram which shows the hierarchy of the network
        pos = nx.nx_pydot.graphviz_layout(project_sub_G, prog='dot', root=pname)
        # pos = nx.nx_agraph.graphviz_layout(project_sub_G,prog="twopi", root=pname)
        if filter_flag:
            print('\nbefore filter: {:,} nodes, {:,} edges'
                    .format(project_sub_G.number_of_nodes(), project_sub_G.number_of_edges()))
            # version 2 filter
            # RUNTIME
            temp_rt_G = filter_by_score(G=project_rt_sub_G, 
            ripples=rt_ripple_effect_edges, root=pname, keyword=keyword)
            for u,v,m in temp_rt_G.edges(data=True):
                if 'development' in m:
                    del m['development']
            # DEVELOPMENT
            temp_dev_G = filter_by_score(G=project_dev_sub_G, 
            ripples=dev_ripple_effect_edges, root=pname, keyword=keyword)
            for u,v,m in temp_dev_G.edges(data=True):
                if 'runtime' in m:
                    del m['runtime']
            # COMBINED
            filtered_project_sub_G = nx.compose(temp_rt_G, temp_dev_G)
            print('after filter: {:,} nodes, {:,} edges'
                    .format(filtered_project_sub_G.number_of_nodes(), filtered_project_sub_G.number_of_edges()))        
        
        ''' 4. node link diagram of the dependency network '''
        assign_graph_node_symbol(project_sub_G, filtered_project_sub_G)
        if filter_flag:
            plotly_graph_to_html(G=filtered_project_sub_G, pos=pos, 
                    title='filtered REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'_min.html')
        plotly_graph_to_html(G=project_sub_G, pos=pos, 
                     title='full REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'_full.html')
    return

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
        sys.exit('dependency network database not found, please run preprocess fisrt')
    
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
    print('creating NPM dependency network..', end='')
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

    # export dependency network to HTML file
    outfile = os.path.join(out_folder, '{}-{}-{}_{}'.format(owner, repo, branch, keyword))
    project_graph_analysis(G=application_sub_G, pname=application_name, outfile=outfile, keyword=keyword, filter_flag=filter)
    print('exported REM dependency graph to {}.'.format(out_folder))

    conn.close()


if __name__ == '__main__':
    main()