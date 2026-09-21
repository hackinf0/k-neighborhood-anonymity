from functools import cmp_to_key

import networkx as nx

from kanon.dfs_code import compare_codes, min_dfs_code


def get_components(graph):
    """Return copies of the connected components."""
    node_sets = list(nx.connected_components(graph))
    node_sets.sort(key=min)

    components = []

    for nodes in node_sets:
        components.append(graph.subgraph(nodes).copy())

    return components


def _compare_components(a, b):
    if a[0] != b[0]:
        if a[0] < b[0]:
            return -1
        return 1

    if a[1] != b[1]:
        if a[1] < b[1]:
            return -1
        return 1

    return compare_codes(a[2], b[2])


def get_ncc(graph, node):
    """Return the neighborhood component code of a node."""
    neighbors = list(graph.neighbors(node))
    neighborhood = graph.subgraph(neighbors).copy()
    coded = []

    for component in get_components(neighborhood):
        code = min_dfs_code(component)
        item = (
            component.number_of_nodes(),
            component.number_of_edges(),
            code,
        )
        coded.append(item)

    coded.sort(key=cmp_to_key(_compare_components))

    result = []
    for item in coded:
        result.append(item[2])

    return tuple(result)
