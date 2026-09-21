from math import lcm

from kanon.partition import build_blocks


def _common_label(graph, hierarchy, block):
    common = graph.nodes[block[0]]["label"]
    for node in block[1:]:
        common = hierarchy.common_label(common, graph.nodes[node]["label"])
    return common


def _build_permutation(blocks):
    sigma = {}
    sizes = {}

    for block in blocks:
        size = len(block)
        for index, node in enumerate(block):
            sigma[node] = block[(index + 1) % size]
            sizes[node] = size

    return sigma, sizes


def anonymize_graph(graph, hierarchy, k, return_metadata=False):
    """Return an anonymized copy of the graph."""
    blocks = build_blocks(graph, hierarchy, k)
    sigma, sizes = _build_permutation(blocks)

    common_labels = []
    for block in blocks:
        common_labels.append(_common_label(graph, hierarchy, block))

    final_graph = graph.copy()

    for block, common in zip(blocks, common_labels):
        for node in block:
            final_graph.nodes[node]["label"] = common

    original_edges = list(graph.edges)

    for u, v in original_edges:
        orbit_length = lcm(sizes[u], sizes[v])
        a = u
        b = v

        for _ in range(orbit_length):
            final_graph.add_edge(a, b)
            a = sigma[a]
            b = sigma[b]

    if return_metadata:
        return final_graph, blocks, sigma

    return final_graph
