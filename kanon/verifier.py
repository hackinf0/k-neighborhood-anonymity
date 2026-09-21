from kanon.ncc import get_ncc


class AnonymityReport:
    """Store the result of an anonymity check."""

    def __init__(self, k, valid, classes, class_sizes, minimum_class_size):
        self.k = k
        self.valid = valid
        self.classes = classes
        self.class_sizes = class_sizes
        self.minimum_class_size = minimum_class_size


def anonymity_classes(graph):
    """Group nodes that have the same NCC."""
    classes_by_ncc = {}

    for node in sorted(graph.nodes):
        ncc = get_ncc(graph, node)

        if ncc not in classes_by_ncc:
            classes_by_ncc[ncc] = []

        classes_by_ncc[ncc].append(node)

    classes = []

    for nodes in classes_by_ncc.values():
        classes.append(tuple(sorted(nodes)))

    classes.sort(key=lambda group: group[0])
    return tuple(classes)


def verify_k_anonymity(graph, k):
    """Return True when every NCC class has at least k nodes."""
    if k < 2:
        raise ValueError("k must be at least 2")

    classes = anonymity_classes(graph)

    for group in classes:
        if len(group) < k:
            return False

    return True


def anonymity_report(graph, k):
    """Return a summary of the NCC anonymity classes."""
    if k < 2:
        raise ValueError("k must be at least 2")

    classes = anonymity_classes(graph)
    class_sizes = []

    for group in classes:
        class_sizes.append(len(group))

    class_sizes = tuple(class_sizes)

    if class_sizes:
        minimum_class_size = min(class_sizes)
    else:
        minimum_class_size = 0

    valid = True
    for size in class_sizes:
        if size < k:
            valid = False
            break

    return AnonymityReport(
        k,
        valid,
        classes,
        class_sizes,
        minimum_class_size,
    )
