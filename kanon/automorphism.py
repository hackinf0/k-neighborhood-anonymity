def verify_automorphism(graph, sigma, k):
    """Return True when sigma is a valid automorphism for k."""
    if k < 2:
        raise ValueError("k must be at least 2")

    nodes = set(graph.nodes)

    if set(sigma.keys()) != nodes:
        return False

    if set(sigma.values()) != nodes:
        return False

    for u, v in graph.edges:
        if not graph.has_edge(sigma[u], sigma[v]):
            return False

    for node in graph.nodes:
        label = graph.nodes[node]["label"]
        mapped_label = graph.nodes[sigma[node]]["label"]
        if label != mapped_label:
            return False

    seen = set()

    for start in sorted(graph.nodes):
        if start in seen:
            continue

        current = start
        size = 0

        while current not in seen:
            seen.add(current)
            size += 1
            current = sigma[current]

        if current != start or size < k:
            return False

    return True
