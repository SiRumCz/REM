'''
Plotly graph rendering supports

Zhe Chen (zkchen@uvic.ca)
'''
from kaleido.scopes.plotly import PlotlyScope
from utils import is_valid_key
import plotly.graph_objects as go # create figure
import plotly.express as px # colorscale
import math # ceil
import networkx as nx

scope = PlotlyScope()


def dict_to_text(node: tuple, key: str, re_metric: str, out_list:list=['final', 'quality', 'popularity', 'maintenance', 'type', 'version']) -> str:
    re_metric = 'deprecated' if not re_metric else re_metric
    if re_metric:
        out_list.append(re_metric)
    name, d = node
    s = '<b>'+name+'</b>'
    for k,v in sorted(d.items()):
        if k == key:
            s += '<br><b><i>{}</i></b>: {}'.format(k, v)
        elif k in out_list:
            s += '<br><b>{}</b>: {}'.format(k, v)
    return s


def set_scalecolor(val) -> str:
    scale = px.colors.diverging.RdYlGn
    return scale[val]


def set_node_color(node: tuple, key: str, re_metric: str) -> str:
    '''
    #6959CD - software
    green   - active     :)
    red     - deprecared :(
    '''
    re_metric = 'deprecated' if not re_metric else re_metric
    name, meta = node
    if is_valid_key(data=meta, key='type') and meta['type'] == 'GITHUB':
        return '#6959CD'
    elif is_valid_key(data=meta, key='non_problematic') and meta['non_problematic'] == True:
        # return set_scalecolor(math.ceil(meta[key]*10)) if (meta and key in meta and meta[key] is not None) else 'black'
        return set_scalecolor(math.ceil(meta[key]*10)) # node with None metric will be marked problematic and should not enter here
    else:
        return 'red' if is_valid_key(data=meta, key=re_metric) and meta[re_metric] else set_node_color_by_scores(node, key)


def set_node_color_by_scores(node: tuple, key: str) -> str:
    '''
    node: full node information
    key: final, popularity, quality, maintenance
    '''
    name, meta = node
    if is_valid_key(data=meta, key='type') and (meta['type'] == 'GITHUB' or meta['type'] == 'application-root'):
        return '#6959CD'
    elif is_valid_key(data=meta, key='non_problematic') and meta['non_problematic'] == True:
        return 'white'
    else:
        return set_scalecolor(math.ceil(meta[key]*10)) if (meta and key in meta and meta[key] is not None) else 'black'


def set_plain_node_color(node: tuple, dir_list: list) -> str:
    name, meta = node
    if is_valid_key(data=meta, key='type') and meta['type'] == 'GITHUB':
        return '#6959CD'
    elif name in dir_list:
        return '#6495ED'
    else:
        return 'grey'


def set_node_marker_size(node: tuple, re_metric: str) -> int:
    '''
    regular size: 10
    deprecated size: 15
    '''
    re_metric = 'deprecated' if not re_metric else re_metric
    name, meta = node
    return 15 if is_valid_key(meta, re_metric) and meta[re_metric] else 10


def set_node_line_width(node: tuple, re_metric: str) -> int:
    '''
    regular size: 1
    deprecated size: 3
    '''
    re_metric = 'deprecated' if not re_metric else re_metric
    name, meta = node
    return 3 if is_valid_key(meta, re_metric) and meta[re_metric] else 1


def plain_plotly_graph_to_html(G: nx.Graph, pname: str, pos: dict, title: str = '', outfile: str = 'plain_temp.html'):
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

    # edges
    Xed_github_rt=[] # RUNTIME
    Yed_github_rt=[]
    Xed_github_dev=[] # DEVELOPMENT
    Yed_github_dev=[]

    # GITHUB RUNTIME
    for u, v, m in list(rt_sub_G.edges(data=True)):
        Xed_github_rt+=[pos[u][0],pos[v][0]]
        Yed_github_rt+=[pos[u][1],pos[v][1]]
        
    # GITHUB DEVELOPMENT
    for u, v, m in list(dev_sub_G.edges(data=True)):
        Xed_github_dev+=[pos[u][0],pos[v][0]]
        Yed_github_dev+=[pos[u][1],pos[v][1]]

    # vertice node color based on dependency type (filling)
    dir_list = list(G.neighbors(pname))
    v_scores_gh_rt=[set_plain_node_color(n, dir_list) for n in list(rt_sub_G.nodes(data=True))]
    v_scores_gh_dev=[set_plain_node_color(n, dir_list) for n in list(dev_sub_G.nodes(data=True))]

    # edge traces
    data=[]
    for i in range(0, len(Xed_github_rt)-2, 2):
        data+=[go.Scatter(
                x=Xed_github_rt[i:i+2],
                y=Yed_github_rt[i:i+2],
                mode='lines',
                legendgroup="gh_rt",
                showlegend=False,
                line=dict(color='lightgrey', width=0.8)
        )]

    if len(Xed_github_rt) > 0:
        data+=[go.Scatter(
                x=Xed_github_rt[len(Xed_github_rt)-2:],
                y=Yed_github_rt[len(Yed_github_rt)-2:],
                mode='lines',
                legendgroup="gh_rt",
                name="runtime dependency relationships",
                line=dict(color='lightgrey', width=0.8)
        )]
    for i in range(0, len(Xed_github_dev)-2, 2):
        data+=[go.Scatter(
            x=Xed_github_dev[i:i+2],
            y=Yed_github_dev[i:i+2],
            mode='lines',
            legendgroup="gh_dev",
            showlegend=False,
            line=dict(color='lightgrey', width=3.2)
        )]
        
    if len(Xed_github_dev) > 0:
        data+=[go.Scatter(
                x=Xed_github_dev[len(Xed_github_dev)-2:],
                y=Yed_github_dev[len(Yed_github_dev)-2:],
                mode='lines',
                legendgroup="gh_dev",
                name="development dependency relationships",
                line=dict(color='lightgrey', width=3.2)
        )]

    # node traces
    if len(Xv_gh_rt) > 0:
        data+=[go.Scatter(x=Xv_gh_rt,
               y=Yv_gh_rt,
               mode='markers',
               legendgroup="gh_rt",               
               name='runtime dependencies',
               marker=dict(symbol='circle',
                             size=10,
                             opacity=1,
                             color=v_scores_gh_rt,
                             line=dict(color='black', width=1),
                             ),
               )]
    if len(Xv_gh_dev) > 0:
        data+=[go.Scatter(x=Xv_gh_dev,
               y=Yv_gh_dev,
               mode='markers',
               legendgroup="gh_dev",               
               name='development dependencies (red outline means deprecation)',
               marker=dict(symbol='circle',
                             size=10,
                             opacity=1,
                             color=v_scores_gh_dev,
                             line=dict(color='black', width=1),
                             ),
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


def plotly_save_to_local_img(fig, path):
    with open(path, "wb") as f:
        f.write(scope.transform(fig, format="png", width=1500, height=750, scale=0.7))


def plotly_graph_to_html(G: nx.Graph, pos: dict, title: str = '', key: str = 'final', outfile: str = 'temp.html', out_img: str = None, re_metric: str = None):
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
    # vertice color lists (line)
    v_color_gh_rt=[set_node_color(n, key, re_metric) for n in list(rt_sub_G.nodes(data=True))]
    v_color_gh_dev=[set_node_color(n, key, re_metric) for n in list(dev_sub_G.nodes(data=True))]
    # vertice node color based on scores system (fill)
    v_scores_gh_rt=[set_node_color_by_scores(n, key) for n in list(rt_sub_G.nodes(data=True))]
    v_scores_gh_dev=[set_node_color_by_scores(n, key) for n in list(dev_sub_G.nodes(data=True))]
    # vertice size
    v_size_gh_rt=[set_node_marker_size(n, re_metric) for n in list(rt_sub_G.nodes(data=True))]
    v_size_gh_dev=[set_node_marker_size(n, re_metric) for n in list(dev_sub_G.nodes(data=True))]
    # vertice line width
    v_width_gh_rt=[set_node_line_width(n, re_metric) for n in list(rt_sub_G.nodes(data=True))]
    v_width_gh_dev=[set_node_line_width(n, re_metric) for n in list(dev_sub_G.nodes(data=True))]
    # vertice text lists
    v_text_gh_rt=[dict_to_text(n, key, re_metric) for n in list(rt_sub_G.nodes(data=True))]
    v_text_gh_dev=[dict_to_text(n, key, re_metric) for n in list(dev_sub_G.nodes(data=True))]
    
    # edges
    Xed_github_rt=[] # RUNTIME
    Yed_github_rt=[]
    Xed_github_dev=[] # DEVELOPMENT
    Yed_github_dev=[]
    # edge color lists
    ed_color_github_rt=[]
    ed_color_github_dev=[]
    
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
                name="runtime dependency relationships (dark-red means ripple-effect of problematic dependency)",
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
                name="development dependency relationships (dark-red means ripple-effect of problematic dependency)",
                line=dict(color=ed_color_github_dev[len(ed_color_github_dev)-1], width=3.2)
        )]
    
    # node traces
    if len(Xv_gh_rt) > 0:
        data+=[go.Scatter(x=Xv_gh_rt,
               y=Yv_gh_rt,
               mode='markers',
               legendgroup="gh_rt",               
               name='runtime dependencies (red outline means rippling one)',
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
               name='development dependencies (red outline means rippling one)',
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
    
    if out_img:
        print(f'exporting REM dependency graph to {out_img}.')
        plotly_save_to_local_img(fig, out_img)
    print(f'exporting REM dependency graph to {outfile}.')
    return fig.write_html(outfile)


def assign_graph_node_symbol(full_G: nx.Graph, filtered_G: nx.Graph):
    for node in full_G:
        full_G.nodes()[node]['symbol'] = 'circle'
        if node in filtered_G:
            full_size = len(list(full_G.neighbors(node)))
            filtered_size = len(list(filtered_G.neighbors(node)))
            # if a node in a filtered graph hasless children, then mark it 'circle-cross'
            filtered_G.nodes()[node]['symbol'] = 'circle-cross' if filtered_size < full_size else 'circle'
    return


def create_deepndabot_issue_rem_graph(r_G: nx.DiGraph, d_G: nx.DiGraph, pos: dict, metric: str='final', title: str='', html_out: str=None, img_out: str=None):
    """
    draw REM graph to show on Dependabot Issue creator
    
    r_G: runtime graph
    d_G: development graph
    pos: graph layout
    title: graph title
    html_out: html output path
    img_out: image output path
    """
    # node pos
    # make sure application is at the last index of the list
    Xv_r = [pos[n][0] for n,m in r_G.nodes(data=True) if m.get('type') != 'application-root'] + [pos[n][0] for n,m in r_G.nodes(data=True) if m.get('type') == 'application-root']
    Yv_r = [pos[n][1] for n,m in r_G.nodes(data=True) if m.get('type') != 'application-root'] + [pos[n][1] for n,m in r_G.nodes(data=True) if m.get('type') == 'application-root']
    Xv_d = [pos[n][0] for n,m in d_G.nodes(data=True) if m.get('type') != 'application-root'] + [pos[n][0] for n,m in d_G.nodes(data=True) if m.get('type') == 'application-root']
    Yv_d = [pos[n][1] for n,m in d_G.nodes(data=True) if m.get('type') != 'application-root'] + [pos[n][1] for n,m in d_G.nodes(data=True) if m.get('type') == 'application-root']
    # edge pos
    Xed_r = []
    Yed_r = []
    Xed_d = []
    Yed_d = []
    # edge colors
    ed_color_r = []
    ed_color_d = []
    # edge line-width
    ed_linewidth_r = []
    ed_linewidth_d = []
    # edge opacity
    ed_opacity_r = []
    ed_opacity_d = []
    # RUNTIME
    for u,v,m in r_G.edges(data=True):
        Xed_r += [pos[u][0],pos[v][0]]
        Yed_r += [pos[u][1],pos[v][1]]
        ed_color_r += [m.get('color')]*2
        ed_linewidth_r += [m.get('line-width')]*2
        ed_opacity_r += [m.get('opacity')]*2
    # DEVELOPMENT
    for u,v,m in d_G.edges(data=True):
        Xed_d += [pos[u][0],pos[v][0]]
        Yed_d += [pos[u][1],pos[v][1]]
        ed_color_d += [m.get('color')]*2
        ed_linewidth_d += [m.get('line-width')]*2
        ed_opacity_d += [m.get('opacity')]*2
    # data to be added to graph
    data = []
    # add edge traces to data
    # development
    for i in range(0, len(Xed_d)-2, 2):
        data+=[go.Scatter(
            x=Xed_d[i:i+2],
            y=Yed_d[i:i+2],
            mode='lines',
            opacity=ed_opacity_d[i],
            legendgroup="dev",
            showlegend=False,
            line=dict(color=ed_color_d[i], width=ed_linewidth_d[i])
        )]
    if len(Xed_d) > 0:
        data+=[go.Scatter(
                x=Xed_d[len(Xed_d)-2:],
                y=Yed_d[len(Yed_d)-2:],
                mode='lines',
                opacity=ed_opacity_d[-1],
                legendgroup="dev",
                name="development dependency relationships",
                line=dict(color=ed_color_d[-1], width=ed_linewidth_d[-1])
        )]
    # runtime
    for i in range(0, len(Xed_r)-2, 2):
        data += [go.Scatter(
                x=Xed_r[i:i+2],
                y=Yed_r[i:i+2],
                mode='lines',
                opacity=ed_opacity_r[i],
                legendgroup="rt",
                showlegend=False,
                line=dict(color=ed_color_r[i], width=ed_linewidth_r[i])
        )]
    if len(Xed_r) > 0:
        data+=[go.Scatter(
                x=Xed_r[len(Xed_r)-2:],
                y=Yed_r[len(Yed_r)-2:],
                mode='lines',
                opacity=ed_opacity_r[-1],
                legendgroup="rt",
                name="runtime dependency relationships",
                line=dict(color=ed_color_r[-1], width=ed_linewidth_r[-1])
        )]
    # add node traces to data
    Xv_d_symbols = [m.get('marker-symbol') for x,m in d_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('marker-symbol') for x,m in d_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_d_sizes = [m.get('marker-size') for x,m in d_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('marker-size') for x,m in d_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_d_colors = [m.get('color') for x,m in d_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('color') for x,m in d_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_d_linecolors = [m.get('line-color') for x,m in d_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('line-color') for x,m in d_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_d_linewidth = [m.get('line-width') for x,m in d_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('line-width') for x,m in d_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_d_texthover = [m['text-hover'] for x,m in d_G.nodes(data=True) if m.get('type')!='application-root']+[m['text-hover'] for x,m in d_G.nodes(data=True) if m.get('type')=='application-root']
    if len(Xv_d) > 1:
        data+=[go.Scatter(x=Xv_d[:-1],
               y=Yv_d[:-1],
               mode='markers',
               legendgroup="dev",
               name='dependencies required during build (blue ring means direct dependencies)',
               marker=dict(symbol=Xv_d_symbols[:-1],
                             size=Xv_d_sizes[:-1],
                             opacity=1,
                             color=Xv_d_colors[:-1],
                             line=dict(color=Xv_d_linecolors[:-1], width=Xv_d_linewidth[:-1]),
                             colorscale="RdYlGn",
                             showscale=True,
                             cmin=0.0,
                             cmid=0.5,
                             cmax=1.0,
                             colorbar=dict(
                                title=dict(text=f'Metric of Health: {metric}', side='right'),
                                thickness=10
                             )),
               text=Xv_d_texthover[:-1],
               hovertemplate='%{text}')]
    if len(Xv_d) > 0:
        data += [go.Scatter(
               x=Xv_d[-1:],
               y=Yv_d[-1:],
               mode='markers',
               legendgroup="dev",
               name='application in name(version)',
               marker=dict(symbol=Xv_d_symbols[-1:],
                             size=Xv_d_sizes[-1:],
                             opacity=1,
                             color=Xv_d_colors[-1:],
                             line=dict(color=Xv_d_linecolors[-1:], width=Xv_d_linewidth[-1:])
                             ),
               text=Xv_d_texthover[-1:],
               hovertemplate='%{text}'
        )]
    Xv_r_symbols = [m.get('marker-symbol') for x,m in r_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('marker-symbol') for x,m in r_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_r_sizes = [m.get('marker-size') for x,m in r_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('marker-size') for x,m in r_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_r_colors = [m.get('color') for x,m in r_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('color') for x,m in r_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_r_linecolors = [m.get('line-color') for x,m in r_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('line-color') for x,m in r_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_r_linewidth = [m.get('line-width') for x,m in r_G.nodes(data=True) if m.get('type')!='application-root']+[m.get('line-width') for x,m in r_G.nodes(data=True) if m.get('type')=='application-root']
    Xv_r_texthover = [m['text-hover'] for x,m in r_G.nodes(data=True) if m.get('type')!='application-root']+[m['text-hover'] for x,m in r_G.nodes(data=True) if m.get('type')=='application-root']
    if len(Xv_r) > 1:
        data += [go.Scatter(x=Xv_r[:-1],
               y=Yv_r[:-1],
               mode='markers',
               legendgroup="rt",        
               name='dependencies required during use (blue ring means direct dependencies)',       
               marker=dict(symbol=Xv_r_symbols[:-1],
                             size=Xv_r_sizes[:-1],
                             opacity=1,
                             color=Xv_r_colors[:-1],
                             line=dict(color=Xv_r_linecolors[:-1], width=Xv_r_linewidth[:-1]),
                             colorscale="RdYlGn",
                             showscale=True,
                             cmin=0.0,
                             cmid=0.5,
                             cmax=1.0,
                             colorbar=dict(
                                title=dict(text=f'Metric of Health: {metric}', side='right'),
                                thickness=10
                             )),
               text=Xv_r_texthover[:-1],
               hovertemplate='%{text}')]
    # add application node
    if len(Xv_r) > 0:
        data += [go.Scatter(
               x=Xv_r[-1:],
               y=Yv_r[-1:],
               mode='markers',
               legendgroup="rt",               
               name='application in name(version)',
               marker=dict(symbol=Xv_r_symbols[-1:],
                             size=Xv_r_sizes[-1:],
                             opacity=1,
                             color=Xv_r_colors[-1:],
                             line=dict(color=Xv_r_linecolors[-1:], width=Xv_r_linewidth[-1:])
                             ),
               text=Xv_r_texthover[-1:],
               hovertemplate='%{text}'
        )]
    # create
    fig=go.Figure(data=data)
    # update layout
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
    # update graph scale
    x_pos_list = [v[0] for v in pos.values()]
    y_pos_list = [v[1] for v in pos.values()]
    xoffset = (max(x_pos_list) - min(x_pos_list)) * 0.05
    yoffset = (max(y_pos_list) - min(y_pos_list)) * 0.05
    fig.update_xaxes(range=[min(x_pos_list)-xoffset, max(x_pos_list)+xoffset])
    fig.update_yaxes(range=[min(y_pos_list)-yoffset, max(y_pos_list)+yoffset])
    
    if img_out:
        print(f'exporting REM dependency graph to {img_out}.')
        plotly_save_to_local_img(fig, img_out)
    if html_out:
        print(f'exporting REM dependency graph to {html_out}.')
        fig.write_html(html_out)


def create_dependabot_pr_rem_subgraph(r_G: nx.DiGraph, d_G: nx.DiGraph, pos: dict, title: str='', html_out: str=None, img_out: str=None):
    """
    draw REM subgraph to show on Dependabot Pull Request
    
    r_G: runtime graph
    d_G: development graph
    pos: graph layout
    title: graph title
    html_out: html output path
    img_out: image output path
    """
    # node pos
    Xv_r = [pos[n][0] for n in list(r_G.nodes())]
    Yv_r = [pos[n][1] for n in list(r_G.nodes())]
    Xv_d = [pos[n][0] for n in list(d_G.nodes())]
    Yv_d = [pos[n][1] for n in list(d_G.nodes())]
    # edge pos
    Xed_r = []
    Yed_r = []
    Xed_d = []
    Yed_d = []
    # edge colors
    ed_color_r = []
    ed_color_d = []
    # edge line-width
    ed_linewidth_r = []
    ed_linewidth_d = []
    # edge opacity
    ed_opacity_r = []
    ed_opacity_d = []
    # RUNTIME
    for u,v,m in r_G.edges(data=True):
        Xed_r += [pos[u][0],pos[v][0]]
        Yed_r += [pos[u][1],pos[v][1]]
        ed_color_r += [m.get('color')]*2
        ed_linewidth_r += [m.get('line-width')]*2
        ed_opacity_r += [m.get('opacity')]*2
    # DEVELOPMENT
    for u,v,m in d_G.edges(data=True):
        Xed_d += [pos[u][0],pos[v][0]]
        Yed_d += [pos[u][1],pos[v][1]]
        ed_color_d += [m.get('color')]*2
        ed_linewidth_d += [m.get('line-width')]*2
        ed_opacity_d += [m.get('opacity')]*2
    # data to be added to graph
    data = []
    # add edge traces to data
    # runtime
    for i in range(0, len(Xed_r)-2, 2):
        data += [go.Scatter(
                x=Xed_r[i:i+2],
                y=Yed_r[i:i+2],
                mode='lines',
                opacity=ed_opacity_r[i],
                legendgroup="rt",
                showlegend=False,
                line=dict(color=ed_color_r[i], width=ed_linewidth_r[i])
        )]
    if len(Xed_r) > 0:
        data+=[go.Scatter(
                x=Xed_r[len(Xed_r)-2:],
                y=Yed_r[len(Yed_r)-2:],
                mode='lines',
                opacity=ed_opacity_r[-1],
                legendgroup="rt",
                name="rippe-effect runtime dependency relationships",
                line=dict(color=ed_color_r[-1], width=ed_linewidth_r[-1])
        )]
    # development
    for i in range(0, len(Xed_d)-2, 2):
        data+=[go.Scatter(
            x=Xed_d[i:i+2],
            y=Yed_d[i:i+2],
            mode='lines',
            opacity=ed_opacity_d[i],
            legendgroup="dev",
            showlegend=False,
            line=dict(color=ed_color_d[i], width=ed_linewidth_d[i])
        )]
    if len(Xed_d) > 0:
        data+=[go.Scatter(
                x=Xed_d[len(Xed_d)-2:],
                y=Yed_d[len(Yed_d)-2:],
                mode='lines',
                opacity=ed_opacity_d[-1],
                legendgroup="dev",
                name="rippe-effect development dependency relationships",
                line=dict(color=ed_color_d[-1], width=ed_linewidth_d[-1])
        )]
    # add node traces to data
    if len(Xv_r) > 0:
        data += [go.Scatter(x=Xv_r,
               y=Yv_r,
               mode='markers',
               legendgroup="rt",               
               name='dependencies required during use (red means vulnerable)',
               marker=dict(symbol=[m['marker-symbol'] for x,m in r_G.nodes(data=True)],
                             size=[m['marker-size'] for x,m in r_G.nodes(data=True)],
                             opacity=1,
                             color=[m['color'] for x,m in r_G.nodes(data=True)],
                             line=dict(color=[m['color'] for x,m in r_G.nodes(data=True)], width=[m['line-width'] for x,m in r_G.nodes(data=True)])
                             ),
               text=[m['text-hover'] for x,m in r_G.nodes(data=True)],
               hovertemplate='%{text}',
               hoverlabel=dict(bgcolor='#3c3c3c', 
                                font=dict(color='white'))
               )]
    if len(Xv_d) > 0:
        data+=[go.Scatter(x=Xv_d,
               y=Yv_d,
               mode='markers',
               legendgroup="dev",               
               name='dependencies required during build (red means vulnerable)',
               marker=dict(symbol=[m['marker-symbol'] for x,m in d_G.nodes(data=True)],
                             size=[m['marker-size'] for x,m in d_G.nodes(data=True)],
                             opacity=1,
                             color=[m['color'] for x,m in d_G.nodes(data=True)],
                             line=dict(color=[m['color'] for x,m in d_G.nodes(data=True)], width=[m['line-width'] for x,m in d_G.nodes(data=True)])
                             ),
               text=[m['text-hover'] for x,m in d_G.nodes(data=True)],
               hovertemplate='%{text}',
               hoverlabel=dict(bgcolor='#3c3c3c', 
                                font=dict(color='white'))
               )]
    # create
    fig=go.Figure(data=data)
    # update layout
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
    # add annotations
    for n,m in r_G.nodes(data=True):
        if m.get('text-label'):
            fig.add_annotation(
                x=pos[n][0],
                y=pos[n][1],
                text=m.get('text-label'),
                showarrow=True,
                arrowcolor="#3c3c3c",
                arrowhead=1,
                arrowwidth=2,
                startarrowsize=1.5,
                yshift=10,
                font=dict(
                    size=20,
                    color="#3c3c3c"))
    for n,m in d_G.nodes(data=True):
        if m.get('text-label'):
            fig.add_annotation(
                x=pos[n][0],
                y=pos[n][1],
                text=m.get('text-label'),
                showarrow=True,
                arrowcolor="#3c3c3c",
                arrowhead=1,
                arrowwidth=2,
                startarrowsize=1.5,
                yshift=10,
                font=dict(
                    size=20,
                    color="#3c3c3c"))
    # update graph scale
    x_pos_list = [v[0] for v in pos.values()]
    y_pos_list = [v[1] for v in pos.values()]
    xoffset = (max(x_pos_list) - min(x_pos_list)) * 0.05
    yoffset = (max(y_pos_list) - min(y_pos_list)) * 0.05
    fig.update_xaxes(range=[min(x_pos_list)-xoffset, max(x_pos_list)+xoffset])
    fig.update_yaxes(range=[min(y_pos_list)-yoffset, max(y_pos_list)+yoffset])
    
    if img_out:
        print(f'exporting REM dependency graph to {img_out}.')
        plotly_save_to_local_img(fig, img_out)
    if html_out:
        print(f'exporting REM dependency graph to {html_out}.')
        fig.write_html(html_out)
