'''
Plotly graph rendering supports

Zhe Chen (zkchen@uvic.ca)
'''

from utils import is_valid_key
import plotly.graph_objects as go # create figure
import plotly.express as px # colorscale
import math # ceil
import networkx as nx


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
    regular size: 10
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
                name="development dependency relationships (dark-red means is affected by library deprecation)",
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