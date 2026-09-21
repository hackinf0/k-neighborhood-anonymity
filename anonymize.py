import json
import sys
from pathlib import Path
from time import perf_counter

import networkx as nx
from networkx.readwrite import json_graph

from kanon.anonymizer import anonymize_graph
from kanon.automorphism import verify_automorphism
from kanon.label_hierarchy import LabelHierarchy


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
    unknown = sorted(set(values) - {"i", "k", "o"})
    if unknown:
        print(f"Error: unexpected argument: {unknown[0]}.")
        return None
    return values


def make_hierarchy():
    hierarchy = LabelHierarchy()
    hierarchy.add("professional", "*")
    hierarchy.add("medical", "professional")
    hierarchy.add("teacher", "professional")
    hierarchy.add("dentist", "medical")
    hierarchy.add("optometrist", "medical")
    hierarchy.add("primary", "teacher")
    hierarchy.add("high_school", "teacher")
    return hierarchy


def load_graph(input_path):
    """Load a graph from a JSON file."""
    try:
        with input_path.open(encoding="utf-8") as file:
            graph_data = json.load(file)
    except FileNotFoundError:
        print("Error: input file not found.")
        return None
    except json.JSONDecodeError:
        print("Error: input file is not valid JSON.")
        return None

    if not isinstance(graph_data, dict) or "graph" not in graph_data:
        print("Error: input graph data is invalid.")
        return None

    try:
        graph = json_graph.node_link_graph(
            graph_data["graph"],
            edges="edges",
        )
    except (KeyError, TypeError, nx.NetworkXError):
        print("Error: input graph data is invalid.")
        return None

    if type(graph) is not nx.Graph:
        print("Error: input graph must be an undirected simple graph.")
        return None
    if nx.number_of_selfloops(graph) != 0:
        print("Error: input graph must not contain self-loops.")
        return None
    for node in graph.nodes:
        label = graph.nodes[node].get("label")
        if type(node) is not int or not isinstance(label, str):
            print("Error: input graph data is invalid.")
            return None
    return graph


def default_output(input_path, k):
    suffix = input_path.suffix or ".json"
    return input_path.with_name(f"{input_path.stem}_k{k}{suffix}")


def block_sizes_text(blocks):
    counts = {}
    for block in blocks:
        size = len(block)
        counts[size] = counts.get(size, 0) + 1

    parts = []
    for size in sorted(counts):
        parts.append(f"{size}x{counts[size]}")
    return ", ".join(parts)


def save_graph(
    output_path,
    final_graph,
    blocks,
    sigma,
    k,
    original_edges,
    runtime,
):
    saved_blocks = []
    for block in blocks:
        saved_blocks.append(list(block))

    saved_sigma = {}
    for node in sorted(sigma):
        saved_sigma[str(node)] = sigma[node]

    graph_data = {
        "k": k,
        "original_edges": original_edges,
        "runtime_sec": runtime,
        "blocks": saved_blocks,
        "sigma": saved_sigma,
        "graph": json_graph.node_link_data(final_graph, edges="edges"),
    }
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(graph_data, file, indent=2)
        file.write("\n")


def anonymize_file(values):
    if "i" not in values:
        print("Error: i is required.")
        return False
    if "k" not in values:
        print("Error: k is required.")
        return False

    input_path = Path(values["i"])
    try:
        k = int(values["k"])
    except ValueError:
        print("Error: k must be an integer.")
        return False

    graph = load_graph(input_path)
    if graph is None:
        return False
    n = graph.number_of_nodes()
    if k < 2:
        print("Error: k must be at least 2.")
        return False
    if k > n:
        print("Error: k must not exceed the number of nodes.")
        return False
    if n % k:
        print("Warning: n is not divisible by k; block sizes may differ.")

    output_path = Path(values.get("o", default_output(input_path, k)))
    hierarchy = make_hierarchy()
    original_edges = graph.number_of_edges()
    original_labels = {}
    for node in graph.nodes:
        original_labels[node] = graph.nodes[node]["label"]

    started = perf_counter()
    final_graph, blocks, sigma = anonymize_graph(
        graph,
        hierarchy,
        k,
        return_metadata=True,
    )
    runtime = perf_counter() - started
    verified = verify_automorphism(final_graph, sigma, k)

    final_edges = final_graph.number_of_edges()
    added_edges = final_edges - original_edges
    if original_edges == 0:
        edge_increase = 0.0
    else:
        edge_increase = 100 * added_edges / original_edges
    avg_before = 2 * original_edges / n
    avg_after = 2 * final_edges / n
    generalized_labels = 0
    for node in graph.nodes:
        if final_graph.nodes[node]["label"] != original_labels[node]:
            generalized_labels += 1

    print(f"Input: {input_path}")
    print(f"Nodes: {n}")
    print(f"Original edges: {original_edges}")
    print(f"Average degree before: {avg_before:.3f}")
    print(f"k: {k}")
    print()
    print(f"Blocks: {len(blocks)}")
    print(f"Block sizes: {block_sizes_text(blocks)}")
    print()
    print(f"Final edges: {final_edges}")
    print(f"Added edges: {added_edges}")
    print(f"Edge increase: {edge_increase:.3f}%")
    print(f"Average degree after: {avg_after:.3f}")
    print(f"Generalized labels: {generalized_labels}")
    print(f"Runtime: {runtime:.3f} s")
    print(f"Sigma verification: {'PASS' if verified else 'FAIL'}")

    if not verified:
        print("Error: sigma verification failed.")
        return False

    save_graph(
        output_path,
        final_graph,
        blocks,
        sigma,
        k,
        original_edges,
        runtime,
    )
    print(f"Output: {output_path}")
    return True


def main():
    values = parse_args(sys.argv[1:])
    if values is None:
        return 1
    try:
        success = anonymize_file(values)
    except OSError as error:
        print(f"Error: {error}")
        return 1
    if success:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
