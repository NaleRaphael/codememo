
__all__ = ['LineInfo', 'Snippet', 'ReferenceInfo', 'Node', 'NodeCollection']


class LineInfo(object):
    """Information of the start and stop line number of a code snippet."""
    __slots__ = ('start', 'stop')

    def __init__(self, start, stop=None):
        """
        Parameters
        ----------
        start : int
            Start line of a code snippet.
        stop : int
            Stop line of a code snippet.
        """
        self.start = start
        self.stop = stop

    def __str__(self):
        return f'<{self.__class__.__name__}; start: {self.start}, stop: {self.stop}>'


class AbsoluteLineInfo(LineInfo):
    pass


class RelativeLineInfo(LineInfo):
    pass


class Snippet(object):
    """Container of a code snippet."""
    __slots__ = ('name', 'content', 'line_start', 'lang', 'path', 'url')

    def __init__(self, name, content, line_start=None, lang=None, path=None, url=None):
        """
        Parameters
        ----------
        name : str
            Name of this code snippet.
        content : str
            Code snippet.
        line_start : int, optional
            Start line of given code snippet. If it's not given, it will be
            set to 1 by default (indicating the first line of a file).
        lang : str, optional
            Language of given code snippet.
        path : str, optional
            Path of file where given code snippet locating.
        url : str, optional
            An URL indicating the source of this code snippet.
        """
        self.name = name
        self.content = content
        self.lang = 'raw' if lang is None else lang
        self.path = path
        self.url = url
        self.line_start = 1 if line_start is None else line_start

    @property
    def n_lines(self):
        return self.content.count('\n') + 1

    @property
    def line_info(self):
        return AbsoluteLineInfo(self.line_start, self.line_start + self.n_lines - 1)


class ReferenceInfo(object):
    """Information of the source which a code snippet should point to."""
    def __init__(self, src, ref_start, ref_stop=None):
        """
        Parameters
        ----------
        src : snippet
            A code snippet as the source.
        ref_start : int
            Start line of the reference.
        ref_stop : int
            Stop line of the reference.
        """
        self.src = src
        self.line_info = RelativeLineInfo(ref_start, stop=ref_stop)


class Node(object):
    def __init__(self, snippet, comment=None, leaves=None):
        """
        Parameters
        ----------
        snippet : Snippet
            An object containing information of code snippet.
        comment : str, optional
            Comment/note of given code snippet.
        leaves : list of Node, optional
            Nodes that related to this code snippet.
        """
        if not isinstance(snippet, Snippet):
            raise TypeError(f'should be an instance of {Snippet}')

        self._ref_info = None
        self.snippet = snippet
        self.comment = comment

        self.root = None
        self.leaves = []

        if leaves is not None:
            if not isinstance(leaves, list):
                raise TypeError(f'should be a list')
            for v in leaves:
                self.add_leaf(v)

    def __repr__(self):
        return f'<Node "{self.snippet.name}">'

    @property
    def ref_info(self):
        return self._ref_info

    @ref_info.setter
    def ref_info(self, value):
        if not isinstance(value, ReferenceInfo):
            raise TypeError(f'should be an instance of {ReferenceInfo}')
        self._ref_info = value

    def set_root(self, node, ref_start, ref_stop=None):
        if node and not isinstance(node, Node):
            raise TypeError(f'should be an instance of {Node}')
        self.root = node
        self.ref_info = ReferenceInfo(
            node.snippet, ref_start, ref_stop=ref_stop
        )

    def reset_root(self):
        self.root = None
        self.ref_info = None

    def add_leaf(self, node, ref_start=1, ref_stop=None):
        if not isinstance(node, Node):
            raise TypeError(f'should be an instance of {Node}')
        n_lines = node.snippet.n_lines
        if ref_start < 1 or ref_start > n_lines:
            msg = f'Reference of start line should be in the range of [1, {n_lines}]'
            raise ValueError(msg)
        if ref_stop and ref_stop > node.snippet.n_lines:
            msg = f'Reference of stop line should be in the range of [1, {n_lines}]'
            raise ValueError(msg)
        if node.root is not None:
            msg = ('Multiple root: Given node is already an leaf of other node.'
            ' You need to reset its root node first.')
            raise ValueError(msg)
        if node is self:
            msg = 'Self reference: given leaf node is this node itself'
            raise ValueError(msg)
        if node is self.root:
            msg = 'Circular reference: given node is already the root of this node'
            raise ValueError(msg)
        node.set_root(self, ref_start, ref_stop=ref_stop)
        self.leaves.append(node)

    def remove_leaf(self, idx):
        node = self.leaves.pop(idx)
        node.reset_root()


class NodeLink(object):
    """A link indicates the relation between root and leaf node."""
    def __init__(self, root, root_slot, leaf, leaf_slot):
        if not isinstance(root, Node):
            raise TypeError(f'expected type: {Node}, got {type(root)}')
        if not isinstance(root_slot, int):
            raise TypeError(f'expected type: {int}, got {type(root_slot)}')
        if not isinstance(leaf, Node):
            raise TypeError(f'expected type: {Node}, got {type(leaf)}')
        if not isinstance(leaf_slot, int):
            raise TypeError(f'expected type: {int}, got {type(leaf_slot)}')

        self.root = root
        self.root_slot = root_slot
        self.leaf = leaf
        self.leaf_slot = leaf_slot

    def __eq__(self, val):
        return all([
            getattr(self, name) == getattr(val, name)
            for name in ['root', 'root_slot', 'leaf', 'leaf_slot']
        ])

    def __repr__(self):
        return f'<NodeLink root: {self.root}; leaf_{self.leaf_slot}: {self.leaf}>'


class NodeIndexLink(object):
    """A link indicates the relation between root and leaf node by their index."""
    def __init__(self, root_idx, root_slot, leaf_idx, leaf_slot):
        if not isinstance(root_idx, int):
            raise TypeError(f'expected type: {int}, got {type(root_idx)}')
        if not isinstance(root_slot, int):
            raise TypeError(f'expected type: {int}, got {type(root_slot)}')
        if not isinstance(leaf_idx, int):
            raise TypeError(f'expected type: {int}, got {type(leaf_idx)}')
        if not isinstance(leaf_slot, int):
            raise TypeError(f'expected type: {int}, got {type(leaf_slot)}')

        self.root_idx = root_idx
        self.root_slot = root_slot
        self.leaf_idx = leaf_idx
        self.leaf_slot = leaf_slot

    def __eq__(self, val):
        return all([
            getattr(self, name) == getattr(val, name)
            for name in ['root_idx', 'root_slot', 'leaf_idx', 'leaf_slot']
        ])

    def __repr__(self):
        return f'<NodeIndexLink root: {self.root_idx}; leaf_{self.leaf_slot}: {self.leaf_idx}>'


class NodeCollection(object):
    def __init__(self, nodes):
        self.nodes = nodes

    def resolve_links(self):
        """Returns list of `NodeLink` objects."""
        links = []
        for node in self.nodes:
            for i, leaf in enumerate(node.leaves):
                links.append(NodeLink(node, 0, leaf, i))
        return links

    def resolve_index_links(self):
        """Returns list of `NodeIndexLink` objects."""
        links = []
        for idx_root, node in enumerate(self.nodes):
            for i, leaf in enumerate(node.leaves):
                idx_leaf = self.nodes.index(leaf)
                links.append(NodeIndexLink(idx_root, 0, idx_leaf, i))
        return links

    def resolve_index_links_from_trees(self, trees):
        """Same as `resolve_index_links()`, but resolve from given trees which are
        generated by `resolve_tree()`."""
        links = []
        prev_tree_size = 0
        for n, tree in enumerate(trees):
            flattened_tree = [v for layer in tree for v in layer]
            for idx_root, node in enumerate(flattened_tree):
                for i, leaf in enumerate(node.leaves):
                    idx_leaf = flattened_tree.index(leaf)
                    links.append(NodeIndexLink(idx_root + prev_tree_size, 0, idx_leaf + prev_tree_size, i))
            prev_tree_size = len(flattened_tree)
        return links

    def resolve_tree(self):
        """Returns possible **trees** relation and orphan nodes."""
        def build_tree(node, tree):
            """Build a tree starting from given node.

            Parameters
            ----------
            node : Node
                Entry node to traverse.
            tree : list
                An container to store traversed nodes.

            Returns
            -------
            tree : list
                Traversed tree. Note that sublayers will be a list.
                (See also the example below)

            Example
            -------
            Given a tree structure (not expressed in list of `Node`):
                A --- B
                  \\- C --- D
                        \\- E

            This method returns:
                [A, [B, C, [D, E]]]
            """
            tree.append(node)
            if len(node.leaves) == 0:
                return tree

            subtrees = []
            for leaf in node.leaves:
                subtrees.append(build_tree(leaf, []))

            # Flatten sub_layers
            flattened = [v for sub in subtrees for v in sub]
            tree.append(flattened)
            return tree

        def build_layers(tree, layers, idx_current_layer):
            """Convert tree to layers. Number of layers is determined by the
            depth of given tree.

            Parameters
            ----------
            tree : list
                Result of `build_tree()`.
            layers : list
                A container to store converted layer from given tree.
            idx_current_layer : int
                An index indicating the current layer, should be initialized to 0.

            Example
            -------
            Given a tree:
                [A, [B, C, [D, E]]]

            This method returns:
                [[A], [B, C], [D, E]]
            """
            if len(layers) < idx_current_layer + 1:
                layers.append([])
            for i, element in enumerate(tree):
                if isinstance(element, list):
                    layers = build_layers(element, layers, idx_current_layer + 1)
                else:
                    layers[idx_current_layer].append(element)
            return layers

        # Find roots and orphans
        roots = []
        orphans = []
        for idx_root, node in enumerate(self.nodes):
            if node.root is None:
                if len(node.leaves) == 0:
                    orphans.append(node)
                else:
                    roots.append(node)
        # Build trees
        trees = []
        for root in roots:
            trees.append(build_tree(root, []))

        # Resolve layers starting from roots
        layer_collection = []
        for tree in trees:
            layer_collection.append(build_layers(tree, [], 0))

        return layer_collection, orphans
