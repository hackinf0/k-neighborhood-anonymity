def _common_label(graph, hierarchy, nodes):
    common = graph.nodes[nodes[0]]["label"]

    for node in nodes[1:]:
        common = hierarchy.common_label(common, graph.nodes[node]["label"])

    return common


def _label_cost(graph, hierarchy, nodes):
    common = _common_label(graph, hierarchy, nodes)
    cost = 0.0

    for node in nodes:
        original = graph.nodes[node]["label"]
        cost += hierarchy.ncp(common) - hierarchy.ncp(original)

    return cost


def build_blocks(graph, hierarchy, k):
    """Build greedy blocks with at least k nodes."""
    if k < 2:
        raise ValueError("k must be at least 2")

    if graph.number_of_nodes() < k:
        raise ValueError("graph must contain at least k vertices")

    degrees = {}
    neighborhood_edges = {}

    for node in graph.nodes:
        degrees[node] = graph.degree[node]
        neighbors = list(graph.neighbors(node))
        neighborhood_edges[node] = graph.subgraph(neighbors).number_of_edges()

    def structural_cost(node, block):
        cost = 0

        for member in block:
            degree_difference = abs(degrees[node] - degrees[member])
            edge_difference = abs(
                neighborhood_edges[node] - neighborhood_edges[member]
            )
            cost += degree_difference + edge_difference

        return cost

    def candidate_cost(node, block):
        structure = structural_cost(node, block)
        label = _label_cost(graph, hierarchy, block + [node])
        return structure + label, structure, label, node

    remaining = set(graph.nodes)
    blocks = []

    while len(remaining) >= k:
        seed = min(remaining)
        remaining.remove(seed)
        block = [seed]

        while len(block) < k:
            best_node = None
            best_cost = None

            for node in sorted(remaining):
                cost = candidate_cost(node, block)

                if best_cost is None or cost < best_cost:
                    best_node = node
                    best_cost = cost

            block.append(best_node)
            remaining.remove(best_node)

        blocks.append(block)

    for node in sorted(remaining):
        best_index = None
        best_cost = None

        for index in range(len(blocks)):
            cost = candidate_cost(node, blocks[index])[:3] + (index,)

            if best_cost is None or cost < best_cost:
                best_index = index
                best_cost = cost

        blocks[best_index].append(node)

    result = []
    for block in blocks:
        result.append(tuple(block))

    result = tuple(result)

    assert all(len(block) >= k for block in result)

    assigned = []
    for block in result:
        assigned.extend(block)

    assert sorted(assigned) == sorted(graph.nodes)

    return result