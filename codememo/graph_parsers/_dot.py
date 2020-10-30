try:
    import pygraphviz
    from networkx import nx_agraph
    from networkx.readwrite import json_graph
except ImportError as ex_import:
    msg = 'Please install required dependencies before importing this module.'
    raise ImportError(msg) from ex_import

from pathlib import Path

from codememo.objects import Snippet, Node, NodeCollection
from .base import BaseParser


__all__ = ['DotParser']

PARSER_IMPL = 'DotParser'


class DotParser(BaseParser):
    """A parser for parsing DOT file to data structure used by this application."""
    VALID_EXTENSIONS = ['.dot']

    def _convert_to_json_graph(self, fn):
        """Convert `AGraph` (content of a DOT file, usually generated by `graphviz`)
        to a JSON graph."""
        graph_dot = pygraphviz.AGraph(fn)
        graph_netx = nx_agraph.from_agraph(graph_dot)
        graph_json = json_graph.node_link_data(graph_netx)
        return graph_json

    def parse(self, fn):
        """Parse a DOT file to a `NodeCollection` object.

        Note that nodes with multiple parents (roots) will be separated into several
        new nodes since `codememo.object.Node` is a single-root structure.

        Parameters
        ----------
        fn : str
            Path of file.
        """
        if Path(fn).suffix not in self.VALID_EXTENSIONS:
            raise ValueError('it seems given file is not a valid DOT file.')

        graph_json = self._convert_to_json_graph(fn)

        raw_nodes = graph_json['nodes']
        raw_links = graph_json['links']

        nodes = [Node(Snippet(raw_node['id'], '')) for raw_node in raw_nodes]
        node_index_map = {raw_node['id']: i for i, raw_node in enumerate(raw_nodes)}

        multi_root_counter = {}

        for raw_link in raw_links:
            idx_src, idx_tgt = node_index_map[raw_link['source']], node_index_map[raw_link['target']]
            src, tgt = nodes[idx_src], nodes[idx_tgt]
            src.add_leaf(tgt)

        return NodeCollection(nodes)
