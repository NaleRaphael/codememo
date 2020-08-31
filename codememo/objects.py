
__all__ = ['LineInfo', 'Code', 'ReferenceInfo', 'Node']


class LineInfo(object):
    """Information of the start and stop line number of code."""
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


class Code(object):
    """Container of code, including lines """
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
    def __init__(self, src_code, rel_start, rel_stop=None):
        """
        Parameters
        ----------
        src_code : Code
            A code snippet as the source.
        start : int
            Start line of the source code
        """
        self.code = src_code
        self.line_info = RelativeLineInfo(rel_start, stop=rel_stop)


class Node(object):
    def __init__(self, code, comment=None, root=None, leaves=None):
        """
        Parameters
        ----------
        code : Code
            An object containing information of code snippet.
        comment : str, optional
            Comment/note of given code snippet.
        root : RootNode, optional
            Source of code snippet in this node should point to.
        leaves : list of Node, optional
            Nodes that related to this code snippet.
        """
        if not isinstance(code, Code):
            raise TypeError(f'should be an instance of {Code}')
        if not isinstance(ref_info, ReferenceInfo):
            raise TypeError(f'should be an instance of {LineInfo}')

        self._ref_info = None
        self.code = code
        self.comment = comment

        self.root = None
        self.leaves = []

        if root is not None:
            self.set_root(root)
        if leaves is not None:
            if not isinstance(leaves, list):
                raise TypeError(f'should be a list')
            for v in leaves:
                self.add_leaf(v)

    @property
    def ref_info(self):
        return self._ref_info

    @ref_info.setter
    def ref_info(self, value):
        if not isinstance(value, ReferenceInfo):
            raise TypeError(f'should be an instance of {ReferenceInfo}')
        self._ref_info = value

    def set_root(self, node, rel_start, rel_stop=None):
        if node and not isinstance(node, RootNode):
            raise TypeError(f'should be an instance of {RootNode}')
        self.root = node
        self.ref_info = ReferenceInfo(
            node.code, rel_start, rel_stop=rel_stop
        )

    def reset_root(self):
        self.root = None
        self.ref_info = None

    def add_leaf(self, node, line_start, line_stop=None):
        if not isinstance(node, Node):
            raise TypeError(f'should be an instance of {Node}')
        if node.root is not None:
            msg = ('Given node is already an leaf of other node. You need '
            'to reset its root node first.')
            raise ValueError(msg)
        node.set_root(self, line_start, line_stop=line_stop)
        self.leaves.append(node)

    def remove_leaf(self, idx):
        node = self.leaves.pop(idx)
        node.reset_root()
