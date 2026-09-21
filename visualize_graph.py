import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from anonymize import load_graph


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


def edge_set(graph):
    edges = set()
    for u, v in graph.edges:
        edges.add(frozenset((u, v)))
    return edges


def draw_graphs(original_graph, final_graph, output_path):
    """Draw G and G' with shared node positions."""
    positions = nx.spring_layout(original_graph, seed=0)
    original_edges = list(original_graph.edges)
    added_edges = []
    original_edge_set = edge_set(original_graph)
    for u, v in final_graph.edges:
        if frozenset((u, v)) not in original_edge_set:
            added_edges.append((u, v))

    figure, axes = plt.subplots(1, 2, figsize=(13, 6))
    nx.draw_networkx(
        original_graph,
        positions,
        ax=axes[0],
        node_color="lightblue",
        edge_color="black",
        with_labels=True,
        font_size=8,
    )
    axes[0].set_title("Original G")
    axes[0].axis("off")

    nx.draw_networkx_nodes(
        final_graph,
        positions,
        ax=axes[1],
        node_color="lightblue",
    )
    nx.draw_networkx_labels(
        final_graph,
        positions,
        ax=axes[1],
        font_size=8,
    )
    nx.draw_networkx_edges(
        final_graph,
        positions,
        edgelist=original_edges,
        ax=axes[1],
        edge_color="black",
        style="solid",
        label="Original edges",
    )
    nx.draw_networkx_edges(
        final_graph,
        positions,
        edgelist=added_edges,
        ax=axes[1],
        edge_color="tab:red",
        style="dashed",
        label="Added edges",
    )
    axes[1].set_title("Anonymized G'")
    axes[1].axis("off")
    axes[1].legend()

    figure.tight_layout()
    figure.savefig(output_path, dpi=160, facecolor="white")
    plt.close(figure)


def main():
    values = parse_args(sys.argv[1:])
    if values is None:
        return 1

    original_graph = load_graph(Path(values["g"]))
    final_graph = load_graph(Path(values["a"]))
    if original_graph is None or final_graph is None:
        return 1

    if original_graph.number_of_nodes() > 50:
        print("Warning: graph visualization is limited to 50 nodes.")
        return 0
    if set(original_graph.nodes) != set(final_graph.nodes):
        print("Error: G and G' do not have the same vertices.")
        return 1
    if not edge_set(original_graph).issubset(edge_set(final_graph)):
        print("Error: G' does not preserve every original edge.")
        return 1

    figures_path = Path("results/figures")
    figures_path.mkdir(parents=True, exist_ok=True)
    output_path = figures_path / "graph_before_after.png"
    draw_graphs(original_graph, final_graph, output_path)
    print(f"Figure: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
