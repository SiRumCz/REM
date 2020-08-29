'''
filters for REM graph

Zhe Chen (zkchen@uvic.ca)
'''

import networkx as nx
from utils import is_valid_key


def filter_pre_order(G: nx.Graph, ripples: set, root: str, keyword: str):
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


def clean_cycles(G: nx.DiGraph, source: str):
    contains_cycle = True
    while (contains_cycle):
        try:
            cycle = nx.find_cycle(G, source)
            G.remove_edge(cycle[-1][0], cycle[-1][1])
        except:
            contains_cycle = False


def minimum_in_tree_rec(minimum: dict, G: nx.DiGraph, node: str, keyword: str):
    meta = G.nodes()[node]
    score = meta[keyword] if keyword in meta and meta[keyword] else None
    for n in nx.descendants(G, node):
        clean_cycles(G, n)
        if n in minimum:
            min_n = minimum[n]
        else:
            min_n = minimum_in_tree_rec(minimum, G, n, keyword)
        if min_n and score:
            score = min(score, min_n)
    minimum[node] = score
    return score


def is_collapsed(a, b) -> bool:
    return a >= (0.9 * b) # difference threshold of 90%


def filter_post_order_minimum(G: nx.Graph, ripples: set, root: str, keyword: str):
    '''
    minimize graph size
    a bottom-up approach
    if an successor node has higher or equal <keyword> score than its parent
    -> 
    filter by removing edge with minimum
    '''
    temp_G = G.copy() # copy of original graph
    minimum = {}
    minimum_in_tree_rec(minimum, G.copy(), root, keyword) # minumum metric in each subgraph
    visited = {n: False for n in list(temp_G.nodes())}
    queue = [x for x in temp_G.nodes() if temp_G.out_degree(x)==0]

    while len(queue) > 0:
        name = queue.pop(0)
        if visited[name]:
            continue
        visited[name] = True
        meta = temp_G.nodes()[name]
        if is_valid_key(meta, 'type') \
        and meta['type'] == 'GITHUB':
            continue
        # score = meta[keyword] if keyword in meta else None
        score = minimum[name]
        for p_name in list(temp_G.predecessors(name)):
            p_meta = temp_G.nodes()[p_name]
            p_score = p_meta[keyword] if keyword in p_meta else None
            if score and p_score:
                if (p_name, name) not in ripples and is_collapsed(score, p_score):
                    if temp_G.out_degree(name) == 0:
                        temp_G.remove_edge(p_name, name)
            queue.append(p_name)

    return G.subgraph(list(temp_G.subgraph(list(nx.descendants(temp_G, root))+[root]).nodes())).copy()


def filter_pre_order_minimum(G: nx.Graph, ripples: set, root: str, keyword: str):
    '''
    minimize graph size
    a top-down(BFS) approach
    if a successor node has higher or equal <keyword> score than its parent
    -> 
    filter by removing edge with minimum
    '''
    temp_G = G.copy() # copy of original graph
    minimum = {}
    minimum_in_tree_rec(minimum, G.copy(), root, keyword)
    
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
            dep_score = minimum[dep_name]
            if score and dep_score and dep_score >= score and (name, dep_name) not in ripples:
                        temp_G.remove_edge(name, dep_name)
            else:
                queue.append(dep_name)

    return G.subgraph(list(temp_G.subgraph(list(nx.descendants(temp_G, root))+[root]).nodes())).copy()


def gray_out_non_problematics(G: nx.Graph, root: str, keyword: str):
    '''
    in a filtered REM, non-problematic nodes will be grayed-out to highlight problematic transitive
    dependencies
    '''
    dir_dependencies = list(G.neighbors(root))
    for node in G.nodes():
        if (node in dir_dependencies+[root]):
            continue
        if not is_valid_key(G.nodes()[node], keyword):
            continue
        predecessors_in_dir = [G.nodes()[n][keyword] for n in G.predecessors(node) \
            if n in dir_dependencies and is_valid_key(G.nodes()[n], keyword)]
        if predecessors_in_dir and G.nodes()[node][keyword] > max(predecessors_in_dir):
            G.nodes()[node]['non_problematic'] = True
    return
