"""Generate a labeled graph and save it as JSON."""

import json
import random
import sys
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph


LABELS = ("dentist", "optometrist", "primary", "high_school")


def parse_args(arguments):
    values = {}
    for argument in arguments:
        if "=" not in argument:
            print("Error: arguments must use key=value.")
            return None
        key, value = argument.split("=", 1)
        if not key or not value:
            print("Error: arguments must use key=value.")
            return None
        if key in values:
            print(f"Error: duplicate argument: {key}.")
            return None
        values[key] = value
    return values


def read_int(values, key, default=None):
    if key not in values:
        if default is None:
            print(f"Error: {key} is required.")
        return default
    try:
        return int(values[key])
    except ValueError:
        print(f"Error: {key} must be an integer.")
        return None


def make_labels(n, seed):
    counts = {
        "dentist": round(0.30 * n),
        "optometrist": round(0.20 * n),
        "primary": round(0.25 * n),
    }
    counts["high_school"] = n - sum(counts.values())

    labels = []
    for label in LABELS:
        labels.extend([label] * counts[label])
    random.Random(seed + 1).shuffle(labels)
    return {node: labels[node] for node in range(n)}


def add_labels(graph, seed):
    labels = make_labels(graph.number_of_nodes(), seed)
    nx.set_node_attributes(graph, labels, "label")


def validate_keys(values, allowed):
    unknown = sorted(set(values) - set(allowed))
    if unknown:
        print(f"Error: unexpected argument: {unknown[0]}.")
        return False
    return True


def generate_graph(values):
    if "t" not in values:
        print("Error: t is required.")
        return False

    graph_type = values["t"]
    if graph_type not in ("gnm", "ba"):
        print("Error: t must be 'gnm' or 'ba'.")
        return False

    n = read_int(values, "n")
    if n is None:
        return False
    seed = read_int(values, "seed", default=0)
    if seed is None:
        return False
    output_path = Path(values.get("o", "graph.json"))
    if n <= 0:
        print("Error: n must be positive.")
        return False

    if graph_type == "gnm":
        if not validate_keys(values, ("n", "e", "t", "seed", "o")):
            return False
        edge_count = read_int(values, "e")
        if edge_count is None:
            return False
        if edge_count < 0:
            print("Error: e must not be negative.")
            return False
        if edge_count > n * (n - 1) // 2:
            print("Error: e is too large for this number of nodes.")
            return False
        graph = nx.gnm_random_graph(n, edge_count, seed=seed)
        saved_graph_type = "gnm"
        display_type = "G(n,m)"
        model_data = {"requested_edges": edge_count}
        m = None
    else:
        if not validate_keys(values, ("n", "m", "t", "seed", "o")):
            return False
        m = read_int(values, "m")
        if m is None:
            return False
        if m <= 0:
            print("Error: m must be positive.")
            return False
        if m >= n:
            print("Error: m must be smaller than n.")
            return False
        graph = nx.barabasi_albert_graph(n, m, seed=seed)
        saved_graph_type = "barabasi_albert"
        display_type = "Barabasi-Albert"
        model_data = {"m": m}

    add_labels(graph, seed)
    graph_data = {
        "graph_type": saved_graph_type,
        "seed": seed,
        "graph": json_graph.node_link_data(graph, edges="edges"),
    }
    graph_data.update(model_data)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(graph_data, file, indent=2)
        file.write("\n")

    edge_count = graph.number_of_edges()
    avg_degree = 2 * edge_count / n
    print("Graph generated")
    print(f"Type: {display_type}")
    print(f"Nodes: {n}")
    print(f"Edges: {edge_count}")
    print(f"Average degree: {avg_degree:.3f}")
    if m is not None:
        print(f"m: {m}")
    print(f"Seed: {seed}")
    print(f"Output: {output_path}")
    return True


def main():
    values = parse_args(sys.argv[1:])
    if values is None:
        return 1
    try:
        success = generate_graph(values)
    except OSError as error:
        print(f"Error: {error}")
        return 1
    if success:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
