
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
    def __init__(self, src, src_slot, tgt, tgt_slot):
        self.src = src
        self.src_slot = src_slot
        self.tgt = tgt
        self.tgt_slot = tgt_slot

    def __repr__(self):
        return f'<NodeLink source: {self.src}; target_{self.tgt_slot}: {self.tgt}>'


class NodeCollection(object):
    def __init__(self, nodes):
        self.nodes = nodes

    def resolve_links(self):
        links = []
        for node in self.nodes:
            for i, leaf in enumerate(node.leaves):
                links.append(NodeLink(node, 0, leaf, i))
        return links
