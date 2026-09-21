class LabelHierarchy:
    """Store labels in a tree rooted at '*'."""

    def __init__(self):
        self._parent = {"*": None}
        self._children = {"*": set()}

    def _check_label(self, label):
        if not isinstance(label, str):
            raise ValueError("label must be a string")

    def add(self, label, parent):
        """Add a label under an existing parent."""
        self._check_label(label)
        self._check_label(parent)

        if label in self._parent:
            raise ValueError(f"label already exists: {label}")

        if parent not in self._parent:
            raise ValueError(f"unknown parent: {parent}")

        self._parent[label] = parent
        self._children[label] = set()
        self._children[parent].add(label)

    def parent(self, label):
        """Return the parent of a label."""
        self._check_label(label)

        if label not in self._parent:
            raise ValueError(f"unknown label: {label}")

        return self._parent[label]

    def ancestors(self, label):
        """Return the path from a label to the root."""
        self._check_label(label)

        if label not in self._parent:
            raise ValueError(f"unknown label: {label}")

        result = []
        current = label

        while current is not None:
            result.append(current)
            current = self._parent[current]

        return result

    def is_leaf(self, label):
        """Return True when a label has no children."""
        self._check_label(label)

        if label not in self._children:
            raise ValueError(f"unknown label: {label}")

        return not self._children[label]

    def leaves(self, label):
        """Return all leaf labels below a label."""
        self._check_label(label)

        if label not in self._children:
            raise ValueError(f"unknown label: {label}")

        leaves = set()
        pending = [label]

        while pending:
            current = pending.pop()
            children = self._children[current]

            if children:
                pending.extend(children)
            else:
                leaves.add(current)

        return leaves

    def size(self, label):
        """Return the number of leaf labels below a label."""
        return len(self.leaves(label))

    def common_label(self, a, b):
        """Return the closest common ancestor of two labels."""
        self._check_label(a)
        self._check_label(b)

        ancestors_a = self.ancestors(a)
        ancestors_b = set(self.ancestors(b))

        for label in ancestors_a:
            if label in ancestors_b:
                return label

    def ncp(self, label):
        """Return the normalized certainty penalty of a label."""
        if self.is_leaf(label):
            return 0.0

        return self.size(label) / self.size("*")
