import csv
import json
import statistics
import sys
from pathlib import Path

import networkx as nx

from anonymize import load_graph, make_hierarchy


LEAF_LABELS = ("dentist", "optometrist", "primary", "high_school")
SUMMARY_FIELDS = (
    "graph_type",
    "n",
    "seed",
    "model_parameter",
    "k",
    "original_edges",
    "final_edges",
    "added_edges",
    "edge_increase_pct",
    "avg_degree_before",
    "avg_degree_after",
    "generalized_labels",
    "generalized_labels_pct",
    "total_ncp",
    "avg_ncp",
    "avg_query_error_pct",
    "median_query_error_pct",
    "max_query_error_pct",
    "query_coverage_pct",
    "runtime_sec",
)
QUERY_FIELDS = (
    "graph_type",
    "n",
    "seed",
    "model_parameter",
    "k",
    "source_label",
    "target_label",
    "original_distance",
    "anonymized_distance",
    "error_pct",
    "source_count",
    "reachable_sources",
    "coverage_pct",
)
KEY_FIELDS = ("graph_type", "n", "seed", "model_parameter", "k")


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
        values[key] = value

    if "g" not in values or "a" not in values:
        print("Error: g and a are required.")
        return None
    if set(values) != {"g", "a"}:
        print("Error: only g and a are accepted.")
        return None
    return values


def load_metadata(path):
    """Load the metadata stored beside node-link graph data."""
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: invalid JSON: {path}")
        return None
    return data


def label_matches(hierarchy, node_label, requested_leaf):
    """Return whether a label represents the requested leaf."""
    return requested_leaf in hierarchy.leaves(node_label)


def matching_nodes(graph, hierarchy, requested_leaf):
    nodes = []
    for node in graph.nodes:
        node_label = graph.nodes[node]["label"]
        if label_matches(hierarchy, node_label, requested_leaf):
            nodes.append(node)
    return nodes


def nearest_distance(graph, source, targets):
    """Return the nearest reachable target distance."""
    lengths = nx.single_source_shortest_path_length(graph, source)
    nearest = None

    for target in targets:
        if target == source or target not in lengths:
            continue
        distance = lengths[target]
        if nearest is None or distance < nearest:
            nearest = distance

    return nearest


def average_distance(graph, sources, targets):
    distances = []
    for source in sources:
        distance = nearest_distance(graph, source, targets)
        if distance is not None:
            distances.append(distance)

    if not distances:
        return None, 0
    return statistics.mean(distances), len(distances)


def format_number(value):
    if value is None:
        return ""
    return f"{value:.3f}"


def experiment_key(row):
    key = []
    for field in KEY_FIELDS:
        key.append(str(row[field]))
    return tuple(key)


def replace_rows(path, fields, new_rows, key):
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if experiment_key(row) != key:
                    rows.append(row)

    rows.extend(new_rows)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def model_parameter(metadata, original_edges):
    graph_type = metadata.get("graph_type")
    if graph_type == "gnm":
        edge_count = metadata.get("requested_edges", original_edges)
        return f"e={edge_count}"
    if graph_type == "barabasi_albert":
        return f"m={metadata.get('m', '')}"
    return ""


def query_results(original_graph, final_graph, hierarchy, identity):
    rows = []
    errors = []
    total_sources = 0
    total_reachable = 0

    for source_label in LEAF_LABELS:
        sources = matching_nodes(original_graph, hierarchy, source_label)

        for target_label in LEAF_LABELS:
            if source_label == target_label:
                continue

            original_targets = matching_nodes(
                original_graph, hierarchy, target_label
            )
            final_targets = matching_nodes(final_graph, hierarchy, target_label)
            original_distance, _ = average_distance(
                original_graph, sources, original_targets
            )
            final_distance, reachable = average_distance(
                final_graph, sources, final_targets
            )

            source_count = len(sources)
            if source_count == 0:
                coverage = None
            else:
                coverage = 100 * reachable / source_count

            error = None
            if original_distance not in (None, 0) and final_distance is not None:
                error = (
                    100
                    * (original_distance - final_distance)
                    / original_distance
                )
                errors.append(error)

            row = dict(identity)
            row.update(
                {
                    "source_label": source_label,
                    "target_label": target_label,
                    "original_distance": format_number(original_distance),
                    "anonymized_distance": format_number(final_distance),
                    "error_pct": format_number(error),
                    "source_count": source_count,
                    "reachable_sources": reachable,
                    "coverage_pct": format_number(coverage),
                }
            )
            rows.append(row)
            total_sources += source_count
            total_reachable += reachable

    if errors:
        average_error = statistics.mean(errors)
        median_error = statistics.median(errors)
        maximum_error = max(errors)
    else:
        average_error = None
        median_error = None
        maximum_error = None

    if total_sources == 0:
        query_coverage = None
    else:
        query_coverage = 100 * total_reachable / total_sources

    summary = {
        "avg_query_error_pct": average_error,
        "median_query_error_pct": median_error,
        "max_query_error_pct": maximum_error,
        "query_coverage_pct": query_coverage,
    }
    return rows, summary


def analyze(original_path, final_path):
    original_metadata = load_metadata(original_path)
    final_metadata = load_metadata(final_path)
    if original_metadata is None or final_metadata is None:
        return False

    original_graph = load_graph(original_path)
    final_graph = load_graph(final_path)
    if original_graph is None or final_graph is None:
        return False

    if set(original_graph.nodes) != set(final_graph.nodes):
        print("Error: G and G' do not have the same vertices.")
        return False

    original_edge_set = set()
    for u, v in original_graph.edges:
        original_edge_set.add(frozenset((u, v)))
    final_edge_set = set()
    for u, v in final_graph.edges:
        final_edge_set.add(frozenset((u, v)))
    if not original_edge_set.issubset(final_edge_set):
        print("Error: G' does not preserve every original edge.")
        return False

    if "k" not in final_metadata:
        print("Error: anonymized metadata does not contain k.")
        return False

    hierarchy = make_hierarchy()
    n = original_graph.number_of_nodes()
    original_edges = original_graph.number_of_edges()
    final_edges = final_graph.number_of_edges()
    added_edges = final_edges - original_edges

    if original_edges == 0:
        edge_increase = 0.0
    else:
        edge_increase = 100 * added_edges / original_edges

    if n == 0:
        avg_degree_before = 0.0
        avg_degree_after = 0.0
    else:
        avg_degree_before = 2 * original_edges / n
        avg_degree_after = 2 * final_edges / n

    generalized_labels = 0
    total_ncp = 0.0
    try:
        for node in original_graph.nodes:
            original_label = original_graph.nodes[node]["label"]
            final_label = final_graph.nodes[node]["label"]
            if original_label != final_label:
                generalized_labels += 1
            total_ncp += hierarchy.ncp(final_label) - hierarchy.ncp(
                original_label
            )
    except (KeyError, ValueError):
        print("Error: graph contains a label outside the hierarchy.")
        return False

    if n == 0:
        generalized_pct = 0.0
        avg_ncp = 0.0
    else:
        generalized_pct = 100 * generalized_labels / n
        avg_ncp = total_ncp / n

    graph_type = original_metadata.get("graph_type", "unknown")
    seed = original_metadata.get("seed", "")
    parameter = model_parameter(original_metadata, original_edges)
    k = final_metadata["k"]
    identity = {
        "graph_type": graph_type,
        "n": n,
        "seed": seed,
        "model_parameter": parameter,
        "k": k,
    }

    try:
        queries, query_summary = query_results(
            original_graph, final_graph, hierarchy, identity
        )
    except ValueError:
        print("Error: query labels are outside the hierarchy.")
        return False

    summary = dict(identity)
    runtime = final_metadata.get("runtime_sec")
    summary.update(
        {
            "original_edges": original_edges,
            "final_edges": final_edges,
            "added_edges": added_edges,
            "edge_increase_pct": format_number(edge_increase),
            "avg_degree_before": format_number(avg_degree_before),
            "avg_degree_after": format_number(avg_degree_after),
            "generalized_labels": generalized_labels,
            "generalized_labels_pct": format_number(generalized_pct),
            "total_ncp": format_number(total_ncp),
            "avg_ncp": format_number(avg_ncp),
            "avg_query_error_pct": format_number(
                query_summary["avg_query_error_pct"]
            ),
            "median_query_error_pct": format_number(
                query_summary["median_query_error_pct"]
            ),
            "max_query_error_pct": format_number(
                query_summary["max_query_error_pct"]
            ),
            "query_coverage_pct": format_number(
                query_summary["query_coverage_pct"]
            ),
            "runtime_sec": format_number(runtime),
        }
    )

    results_path = Path("results")
    results_path.mkdir(exist_ok=True)
    summary_path = results_path / "utility_summary.csv"
    queries_path = results_path / "utility_queries.csv"
    key = experiment_key(summary)
    replace_rows(summary_path, SUMMARY_FIELDS, [summary], key)
    replace_rows(queries_path, QUERY_FIELDS, queries, key)

    if graph_type == "gnm":
        display_type = "G(n,m)"
    elif graph_type == "barabasi_albert":
        display_type = "Barabasi-Albert"
    else:
        display_type = graph_type

    print("Utility analysis")
    print()
    print("Graph")
    print(f"Type: {display_type}")
    print(f"Nodes: {n}")
    print(f"k: {k}")
    print()
    print("Structure")
    print(f"Original edges: {original_edges}")
    print(f"Final edges: {final_edges}")
    print(f"Added edges: {added_edges}")
    print(f"Edge increase: {edge_increase:.3f}%")
    print(f"Average degree before: {avg_degree_before:.3f}")
    print(f"Average degree after: {avg_degree_after:.3f}")
    print()
    print("Labels")
    print(f"Generalized labels: {generalized_labels}")
    print(f"Generalized labels: {generalized_pct:.3f}%")
    print(f"Total NCP: {total_ncp:.3f}")
    print(f"Average NCP: {avg_ncp:.3f}")
    print()
    print("Queries")
    print(f"Pairs evaluated: {len(queries)}")

    average_error = query_summary["avg_query_error_pct"]
    median_error = query_summary["median_query_error_pct"]
    maximum_error = query_summary["max_query_error_pct"]
    query_coverage = query_summary["query_coverage_pct"]
    if average_error is None:
        print("Average query error: unavailable")
        print("Median query error: unavailable")
        print("Maximum query error: unavailable")
    else:
        print(f"Average query error: {average_error:.3f}%")
        print(f"Median query error: {median_error:.3f}%")
        print(f"Maximum query error: {maximum_error:.3f}%")
    if query_coverage is None:
        print("Query coverage: unavailable")
    else:
        print(f"Query coverage: {query_coverage:.3f}%")
    print()
    print(f"Summary: {summary_path}")
    print(f"Queries: {queries_path}")
    return True


def main():
    values = parse_args(sys.argv[1:])
    if values is None:
        return 1
    success = analyze(Path(values["g"]), Path(values["a"]))
    if success:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
