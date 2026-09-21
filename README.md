# Neighborhood k-Anonymity

This project is a student-scale implementation of neighborhood
`k`-anonymity for labeled social graphs. It uses NetworkX and provides tools
to generate graphs, anonymize them, measure utility, and create report plots.

The anonymizer groups vertices into blocks, generalizes their labels, and
closes the graph edges under a cyclic permutation. The original graph is not
modified.

## Basic usage

Generate a graph:

```bash
python generate_graph.py n=300 e=450 t=gnm seed=0 o=graph.json
```

Anonymize it:

```bash
python anonymize.py i=graph.json k=2 o=graph_k2.json
```

Measure utility and create plots:

```bash
python utility.py g=graph.json a=graph_k2.json
python plot_results.py
```

## Reference

Bin Zhou and Jian Pei, “Preserving Privacy in Social Networks Against
Neighborhood Attacks,” *Proceedings of the 24th IEEE International Conference
on Data Engineering (ICDE)*, pp. 506–515, 2008.
[https://doi.org/10.1109/ICDE.2008.4497459](https://doi.org/10.1109/ICDE.2008.4497459)
