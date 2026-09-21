from functools import cmp_to_key

import networkx as nx


def _compare_values(a, b):
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def _compare_positions(a, b):
    i1, j1 = a
    i2, j2 = b
    forward1 = i1 < j1
    forward2 = i2 < j2

    if forward1 and forward2:
        if j1 != j2:
            return _compare_values(j1, j2)
        return _compare_values(i2, i1)

    if not forward1 and not forward2:
        if i1 != i2:
            return _compare_values(i1, i2)
        return _compare_values(j1, j2)

    if forward1:
        if j1 <= i2:
            return -1
        return 1

    if i1 < j2:
        return -1
    return 1


def _compare_edges(a, b):
    position = _compare_positions(a[:2], b[:2])
    if position != 0:
        return position
    return _compare_values(a[2:], b[2:])


def compare_codes(a, b):
    """Compare two DFS codes with the Zhou-Pei order."""
    labels_a, edges_a = a
    labels_b, edges_b = b

    for edge_a, edge_b in zip(edges_a, edges_b):
        result = _compare_edges(edge_a, edge_b)
        if result != 0:
            return result

    if len(edges_a) != len(edges_b):
        return _compare_values(len(edges_a), len(edges_b))

    return _compare_values(labels_a, labels_b)


def _explore(graph, node, seen, order, parent):
    children = []

    for neighbor in sorted(graph.neighbors(node)):
        if neighbor not in seen:
            children.append(neighbor)

    if not children:
        yield seen, order, parent
        return

    for child in children:
        child_seen = seen | {child}
        child_order = order + (child,)
        child_parent = dict(parent)
        child_parent[child] = node

        states = _explore(
            graph,
            child,
            child_seen,
            child_order,
            child_parent,
        )

        for state in states:
            yield from _explore(graph, node, *state)


def _build_code(graph, order, parent):
    index = {}
    for position, node in enumerate(order):
        index[node] = position

    labels = []
    for node in order:
        labels.append(graph.nodes[node]["label"])
    labels = tuple(labels)

    edges = []

    for u, v in graph.edges:
        if parent.get(v) == u:
            i = index[u]
            j = index[v]
        elif parent.get(u) == v:
            i = index[v]
            j = index[u]
        else:
            i = max(index[u], index[v])
            j = min(index[u], index[v])

        edges.append((i, j, labels[i], labels[j]))

    edges.sort(key=cmp_to_key(_compare_edges))
    return labels, tuple(edges)


def min_dfs_code(graph):
    """Return the minimum DFS code of a connected graph."""
    if graph.number_of_nodes() == 0:
        raise ValueError("graph must not be empty")

    if not nx.is_connected(graph):
        raise ValueError("graph must be connected")

    if graph.number_of_nodes() == 1:
        node = min(graph.nodes)
        return ((graph.nodes[node]["label"],), ())

    best = None
    candidates = set()

    for start in sorted(graph.nodes):
        states = _explore(graph, start, {start}, (start,), {})

        for _, order, parent in states:
            code = _build_code(graph, order, parent)

            if code in candidates:
                continue

            candidates.add(code)

            if best is None or compare_codes(code, best) < 0:
                best = code

    return best
