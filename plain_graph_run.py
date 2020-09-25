from rem_graphics import plain_plotly_graph_to_html
import networkx as nx # DiGraph
import sys


def draw_plain_dependency_graph(G: nx.Graph, pname: str, outfile: str):
    # RUNTIME
    project_rt_sub_G = nx.DiGraph()
    # DEVELOPMENT
    project_dev_sub_G = nx.DiGraph()
    project_rt_sub_G.add_node(pname, **G.nodes()[pname])
    project_dev_sub_G.add_node(pname, **G.nodes()[pname])
    for u,v,m in G.edges(data=True):
        if 'runtime' in m and m['runtime'] is True:
            project_rt_sub_G.add_node(u, **G.nodes()[u])
            project_rt_sub_G.add_node(v, **G.nodes()[v])
            project_rt_sub_G.add_edge(u,v, **m)
        if 'development' in m and m['development'] is True:
            project_dev_sub_G.add_node(u, **G.nodes()[u])
            project_dev_sub_G.add_node(v, **G.nodes()[v])
            project_dev_sub_G.add_edge(u,v, **m)
    project_sub_G = nx.compose(project_rt_sub_G, project_dev_sub_G)
    pos = nx.nx_pydot.graphviz_layout(project_sub_G, prog='dot', root=pname)
    plain_plotly_graph_to_html(G=G, pname=pname, pos=pos, title=f'{pname} dependency graph', outfile=outfile)