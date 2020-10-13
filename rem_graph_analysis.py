'''
analyze dependencies on an NPM application and generate a set of 
Ripple Effect of Metrics (REM) graph with metrics of health

Zhe Chen (zkchen@uvic.ca)
'''

from rem_filter import *
from rem_graphics import *
import networkx as nx # DiGraph
import sys
import json # dump()


def project_graph_analysis(G: nx.Graph, pname: str, outfile: str, keyword: str, filter_flag: bool):
    print('NPM software:', pname)
    
    ''' pre. check if exists '''
    if pname not in list(G.nodes()):
        sys.exit('\nsoftware not found.')
    
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
        
    ''' 2. transitive dependencies '''
    # github software subgraph
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
    
    # print graph shape
    print()
    print('NPM package RUNTIME dependency graph for top starred github project ({}) shape:'
    .format(pname))
    print('nodes:', project_rt_sub_G.number_of_nodes())
    print('edges:', project_rt_sub_G.number_of_edges())
    print('NPM package DEVELOPMENT dependency graph for top starred github project ({}) shape:'
    .format(pname))
    print('nodes:', project_dev_sub_G.number_of_nodes())
    print('edges:', project_dev_sub_G.number_of_edges())

    # DEVELOPMENT and RUNTIME ripple effect edges and nodes set
    rt_ripple_effect_edges = set()
    rt_ripple_effect_nodes = set()
    dev_ripple_effect_edges = set()
    dev_ripple_effect_nodes = set()
    
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
        ''' 4. node link diagram of the dependency graph '''
        for pair in list(project_rt_sub_G.edges()):
            project_rt_sub_G.edges()[pair]['color'] = 'lightgrey'

        for pair in list(project_dev_sub_G.edges()):
            project_dev_sub_G.edges()[pair]['color'] = 'lightgrey'
        
        project_sub_G = nx.compose(project_rt_sub_G, project_dev_sub_G)
        
        # using dot diagram which shows the hierarchy of the graph
        pos = nx.nx_pydot.pydot_layout(project_sub_G, prog='dot', root=pname)
        filtered_project_sub_G = nx.DiGraph()
        if filter_flag:
            print('\nbefore filter: {:,} nodes, {:,} edges'
                    .format(project_sub_G.number_of_nodes(), project_sub_G.number_of_edges()))
            # version 2 filter
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
            # COMBINED
            filtered_project_sub_G = nx.compose(temp_rt_G, temp_dev_G)
            print('after filter: {:,} nodes, {:,} edges'
                    .format(filtered_project_sub_G.number_of_nodes(), filtered_project_sub_G.number_of_edges()))        
        
        ''' 4. node link diagram of the dependency graph '''
        assign_graph_node_symbol(project_sub_G, filtered_project_sub_G)
        if filter_flag:
            plotly_graph_to_html(G=filtered_project_sub_G, pos=pos, 
                    title='filtered REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'_min.html')
        plotly_graph_to_html(G=project_sub_G, pos=pos, 
        title='REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'.html')
    else:
        ''' 3.a number of deprecated packages '''
        if len(rt_sub_g_deprecated_list) > 0:
            print('There is(are) **{:,}** deprecated package(s) in the RUNTIME:'
              .format(len(rt_sub_g_deprecated_list)))
        if len(dev_sub_g_deprecated_list) > 0:
            print('There is(are) **{:,}** deprecated package(s) in the DEVELOPMENT:'
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
        '**{:,}** nodes ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the graph.'
              .format(len(rt_ripple_effect_nodes),
                      100 * len(rt_ripple_effect_nodes) / project_rt_sub_G.number_of_nodes(),
                      len(rt_sub_g_deprecated_list)))
            print(\
        '**{:,}** edges ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the graph.'
              .format(len(rt_ripple_effect_edges),
                      100 * len(rt_ripple_effect_edges) / project_rt_sub_G.number_of_edges(),
                      len(rt_sub_g_deprecated_list)))
        
        # DEVELOPMENT
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
        '**{:,}** nodes ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the graph.'
              .format(len(dev_ripple_effect_nodes),
                      100 * len(dev_ripple_effect_nodes) / project_dev_sub_G.number_of_nodes(),
                      len(dev_sub_g_deprecated_list)))
            print(\
        '**{:,}** edges ({:.2f}%) affected by ripple effect by the deprecation of {:,} packages in the graph.'
              .format(len(dev_ripple_effect_edges),
                      100 * len(dev_ripple_effect_edges) / project_dev_sub_G.number_of_edges(),
                      len(dev_sub_g_deprecated_list)))

        ''' 3.c(pre-4.a) adding color attributes on the edges for graph '''
        for pair in list(project_rt_sub_G.edges()):
            project_rt_sub_G.edges()[pair]['color'] = 'lightgrey'\
            if pair not in rt_ripple_effect_edges else '#8b0000'

        for pair in list(project_dev_sub_G.edges()):
            project_dev_sub_G.edges()[pair]['color'] = 'lightgrey'\
            if pair not in dev_ripple_effect_edges else '#8b0000'

        ''' 3.d(pre-4.b) graph filter that reduces node number '''
        project_sub_G = nx.compose(project_rt_sub_G, project_dev_sub_G)
        # using dot diagram which shows the hierarchy of the graph
        pos = nx.nx_pydot.graphviz_layout(project_sub_G, prog='dot', root=pname)
        # pos = nx.nx_agraph.graphviz_layout(project_sub_G,prog="twopi", root=pname)
        filtered_project_sub_G = nx.DiGraph()
        if filter_flag:
            print('\nbefore filter: {:,} nodes, {:,} edges'
                    .format(project_sub_G.number_of_nodes(), project_sub_G.number_of_edges()))
            # version 2 filter
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
            # COMBINED
            filtered_project_sub_G = nx.compose(temp_rt_G, temp_dev_G)
            gray_out_non_problematics(G=filtered_project_sub_G, root=pname, keyword=keyword)
            print('after filter: {:,} nodes, {:,} edges'
                    .format(filtered_project_sub_G.number_of_nodes(), filtered_project_sub_G.number_of_edges()))        

        ''' 4. node link diagram of the dependency graph '''
        assign_graph_node_symbol(project_sub_G, filtered_project_sub_G)
        if filter_flag:
            plotly_graph_to_html(G=filtered_project_sub_G, pos=pos, 
                    title='filtered REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'_min.html')
        plotly_graph_to_html(G=project_sub_G, pos=pos, 
                     title='full REM dependency graph for {}'.format(pname), key=keyword, outfile=outfile+'_full.html')
    return