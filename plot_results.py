import csv
from pathlib import Path

import matplotlib.pyplot as plt


SEED_COLORS = {
    0: "tab:blue",
    1: "tab:orange",
    2: "tab:green",
    3: "tab:red",
    4: "tab:purple",
}


def make_plot(
    rows,
    graph_type,
    value_field,
    title,
    y_label,
    output_path,
):
    figure, axis = plt.subplots(figsize=(8, 5))

    for seed in SEED_COLORS:
        points = []
        for row in rows:
            if row["graph_type"] != graph_type:
                continue
            if int(row["seed"]) != seed:
                continue
            if row[value_field] == "":
                continue

            k = int(row["k"])
            value = float(row[value_field])
            points.append((k, value))

        points.sort()
        k_values = []
        values = []
        for k, value in points:
            k_values.append(k)
            values.append(value)

        axis.plot(
            k_values,
            values,
            color=SEED_COLORS[seed],
            marker="o",
            linewidth=1.8,
            label=f"Seed {seed}",
        )

    axis.set_title(title)
    axis.set_xlabel("k")
    axis.set_ylabel(y_label)
    axis.set_xticks([2, 3, 5])
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=160, facecolor="white")
    plt.close(figure)


def main():
    summary_path = Path("results/utility_summary.csv")
    if not summary_path.exists():
        print("Error: results/utility_summary.csv not found.")
        return 1

    with summary_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        print("Error: utility summary is empty.")
        return 1

    figures_path = Path("results/figures")
    figures_path.mkdir(parents=True, exist_ok=True)

    make_plot(
        rows,
        "gnm",
        "edge_increase_pct",
        "Edge growth — G(n,m)",
        "Edge increase (%)",
        figures_path / "edge_growth_gnm.png",
    )
    make_plot(
        rows,
        "barabasi_albert",
        "edge_increase_pct",
        "Edge growth — Barabasi-Albert",
        "Edge increase (%)",
        figures_path / "edge_growth_ba.png",
    )
    make_plot(
        rows,
        "gnm",
        "avg_ncp",
        "Average NCP — G(n,m)",
        "Average NCP",
        figures_path / "average_ncp_gnm.png",
    )
    make_plot(
        rows,
        "barabasi_albert",
        "avg_ncp",
        "Average NCP — Barabasi-Albert",
        "Average NCP",
        figures_path / "average_ncp_ba.png",
    )
    make_plot(
        rows,
        "gnm",
        "avg_query_error_pct",
        "Query error — G(n,m)",
        "Average query error (%)",
        figures_path / "query_error_gnm.png",
    )
    make_plot(
        rows,
        "barabasi_albert",
        "avg_query_error_pct",
        "Query error — Barabasi-Albert",
        "Average query error (%)",
        figures_path / "query_error_ba.png",
    )

    print("Figures created")
    print(f"Edge growth G(n,m): {figures_path / 'edge_growth_gnm.png'}")
    print(f"Edge growth BA: {figures_path / 'edge_growth_ba.png'}")
    print(f"Average NCP G(n,m): {figures_path / 'average_ncp_gnm.png'}")
    print(f"Average NCP BA: {figures_path / 'average_ncp_ba.png'}")
    print(f"Query error G(n,m): {figures_path / 'query_error_gnm.png'}")
    print(f"Query error BA: {figures_path / 'query_error_ba.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
