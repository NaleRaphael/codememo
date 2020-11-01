from pathlib import Path
import json
import pytest

from codememo.objects import (
    Snippet, Node, NodeLink, NodeIndexLink, NodeCollection
)
from codememo.exceptions import (
    NodeRemovalException, NodeReferenceException,
)


@pytest.fixture
def dummy_snippet_data():
    data = {
        'name': 'foo.py',
        'content': 'def foo():\n    print("foo")',
        'lang': 'python',
        'line_start': 5,
        'path': '~/data/foo.py',
        'url': 'https://foo.bar/snippet/foo.py',
    }
    return data


@pytest.fixture
def dummy_node_data():
    snippet_data = {
        'name': 'foo.py',
        'content': 'def foo():\n    print("foo")',
        'lang': 'python',
        'line_start': 5,
        'path': '~/data/foo.py',
        'url': 'https://foo.bar/snippet/foo.py',
    }
    node_data = {
        'uuid': '554baf0e-b43a-4a52-a384-161e1f196320',
        'snippet': snippet_data,
        'comment': 'just some comment...',
        'roots': [],
        'leaves': [],
        'ref_infos': {},
    }
    return node_data


@pytest.fixture
def dummy_node_collection_data():
    fn_data = Path(Path(__file__).parent, 'node_collection_data.json')
    with open(fn_data, 'r') as f:
        nodes_data = json.load(f)
    return nodes_data


@pytest.fixture
def dummy_nodes():
    data = [
        ('foo.py', 'def foo():\n    print("foo")', 'python'),
        ('bar.py', 'def bar():\n    print("bar")', 'python'),
        ('buzz.py', 'def buzz():\n    print("buzz")', 'python'),
        ('gin.py', 'def gin():\n    print("gin")', 'python'),
        ('fizz.py', 'def fizz():\n    print("fizz")', 'python'),
        ('greet.c', 'int main(void) {\n  printf("Hello world!\n");  \n return 0;\n}', 'c'),
    ]
    snippets = [Snippet(v[0], v[1], lang=v[2]) for v in data]
    return [Node(v) for v in snippets]


@pytest.fixture
def dummy_nodes_multiple_trees():
    data = [
        ('0_0', 'def foo():\n    print("foo")', 'python'),
        ('0_1', 'def bar():\n    print("bar")', 'python'),
        ('0_2', 'def buzz():\n    print("buzz")', 'python'),
        ('0_3', 'def gin():\n    print("gin")', 'python'),
        ('1_0', 'def fizz():\n    print("fizz")', 'python'),
        ('2_0', 'def foo():\n    print("foo")', 'python'),
        ('2_1', 'def bar():\n    print("bar")', 'python'),
        ('2_2', 'def buzz():\n    print("buzz")', 'python'),
        ('2_3', 'def gin():\n    print("gin")', 'python'),
        ('2_4', 'def fizz():\n    print("fizz")', 'python'),
    ]
    snippets = [Snippet(v[0], v[1], lang=v[2]) for v in data]
    nodes = [Node(v) for v in snippets]

    # Set dependencies
    nodes[0].add_leaf(nodes[1])
    nodes[0].add_leaf(nodes[2])
    nodes[2].add_leaf(nodes[3])
    nodes[5].add_leaf(nodes[6])
    nodes[6].add_leaf(nodes[7])
    nodes[6].add_leaf(nodes[8])
    nodes[7].add_leaf(nodes[9])

    desired_links = [
        NodeLink(nodes[0], 0, nodes[1], 0),
        NodeLink(nodes[0], 0, nodes[2], 1),
        NodeLink(nodes[2], 0, nodes[3], 0),
        NodeLink(nodes[5], 0, nodes[6], 0),
        NodeLink(nodes[6], 0, nodes[7], 0),
        NodeLink(nodes[6], 0, nodes[8], 1),
        NodeLink(nodes[7], 0, nodes[9], 0),
    ]

    desired_index_links = [
        NodeIndexLink(0, 0, 1, 0),
        NodeIndexLink(0, 0, 2, 1),
        NodeIndexLink(2, 0, 3, 0),
        NodeIndexLink(5, 0, 6, 0),
        NodeIndexLink(6, 0, 7, 0),
        NodeIndexLink(6, 0, 8, 1),
        NodeIndexLink(7, 0, 9, 0),
    ]
    return nodes, desired_links, desired_index_links


@pytest.fixture
def dummy_nodes_circular_references():
    data = [
        ('0_0', 'def foo():\n    print("foo")', 'python'),
        ('1_0', 'def bar():\n    print("bar")', 'python'),
        ('1_1', 'def buzz():\n    print("buzz")', 'python'),
        ('1_2', 'def gin():\n    print("gin")', 'python'),
        ('2_0', 'def fizz():\n    print("fizz")', 'python'),
        ('2_1', 'def foo():\n    print("foo")', 'python'),
        ('2_2', 'def bar():\n    print("bar")', 'python'),
    ]
    snippets = [Snippet(v[0], v[1], lang=v[2]) for v in data]
    nodes = [Node(v) for v in snippets]

    # Set dependencies
    nodes[1].add_leaf(nodes[2])
    nodes[2].add_leaf(nodes[3])
    nodes[3].add_leaf(nodes[1])
    nodes[4].add_leaf(nodes[5])
    nodes[5].add_leaf(nodes[6])
    nodes[6].add_leaf(nodes[4])

    desired_links = [
        NodeLink(nodes[1], 0, nodes[2], 0),
        NodeLink(nodes[2], 0, nodes[3], 0),
        NodeLink(nodes[3], 0, nodes[1], 0),
        NodeLink(nodes[4], 0, nodes[5], 0),
        NodeLink(nodes[5], 0, nodes[6], 0),
        NodeLink(nodes[6], 0, nodes[4], 0),
    ]

    desired_index_links = [
        NodeIndexLink(1, 0, 2, 0),
        NodeIndexLink(2, 0, 3, 0),
        NodeIndexLink(3, 0, 1, 0),
        NodeIndexLink(4, 0, 5, 0),
        NodeIndexLink(5, 0, 6, 0),
        NodeIndexLink(6, 0, 4, 0),
    ]
    return nodes, desired_links, desired_index_links


class TestSnippet:
    def test__to_dict(self, dummy_snippet_data):
        data = dummy_snippet_data
        snippet = Snippet(
            data['name'], data['content'], line_start=data.get('line_start'),
            lang=data.get('lang'), path=data.get('path'), url=data.get('url'),
        )
        assert snippet.to_dict() == data

    def test__from_dict(self, dummy_snippet_data):
        data = dummy_snippet_data
        snippet = Snippet.from_dict(data)
        assert snippet.to_dict() == data


class TestNode:
    def test__to_dict(self, dummy_node_data):
        data = dummy_node_data
        node = Node(
            Snippet.from_dict(data['snippet']), comment=data.get('comment'),
            uuid=data.get('uuid')
        )
        assert node.to_dict() == data

    def test__from_dict(self, dummy_node_data):
        data = dummy_node_data
        node = Node.from_dict(data)
        assert node.to_dict() == data

    def test__add_leaf__self_reference(self, dummy_nodes):
        A = dummy_nodes[0]
        A.add_leaf(A)
        assert A in A.roots

    def test__add_leaf__self_reference_duplicate(self, dummy_nodes):
        A = dummy_nodes[0]
        A.add_leaf(A)
        with pytest.raises(NodeReferenceException, match='Duplicate reference'):
            A.add_leaf(A)

    def test__add_leaf__multiple_roots(self, dummy_nodes):
        A, B, C = dummy_nodes[:3]
        A.add_leaf(B)
        C.add_leaf(B)
        assert A in B.roots
        assert C in B.roots

    def test__add_leaf__exceed_range(self, dummy_nodes):
        A, B = dummy_nodes[:2]
        n_lines = A.snippet.n_lines
        with pytest.raises(ValueError, match='should be in the range'):
            A.add_leaf(B, 0)
        with pytest.raises(ValueError, match='should be in the range'):
            A.add_leaf(B, n_lines + 1)

    def test__remove_leaf(self, dummy_nodes):
        A, B, C = dummy_nodes[:3]
        A.add_leaf(B)
        A.add_leaf(C)

        assert all([leaf in A.leaves for leaf in [B, C]])
        A.remove_leaf(C)
        assert A.leaves == [B]
        A.remove_leaf(B)
        assert A.leaves == []

        with pytest.raises(NodeRemovalException, match='not a leaf'):
            A.remove_leaf(B)

    def test__remove_all_leaves(self, dummy_nodes):
        A, B, C, D = dummy_nodes[:4]
        A.add_leaf(B)
        A.add_leaf(C)
        B.add_leaf(D)

        # Current graph:
        # A --> B --> D
        #   \-> C
        assert all([leaf in A.leaves for leaf in [B, C]])
        assert D in B.leaves

        A.remove_all_leaves()

        # Current graph:
        # A     B --> D
        #       C
        assert A.leaves == []
        assert B.roots == [] and B.leaves == [D]
        assert C.roots == []

    def test__remove_all_leaves__circular_references(self, dummy_nodes):
        A, B, C, D = dummy_nodes[:4]
        A.add_leaf(B)
        B.add_leaf(C)
        C.add_leaf(D)
        D.add_leaf(A)

        # Current graph:
        # -> A --> B --> C --> D -
        # |----------------------|
        assert A.leaves == [B] and B.roots == [A]
        assert B.leaves == [C] and C.roots == [B]
        assert C.leaves == [D] and D.roots == [C]
        assert D.leaves == [A] and A.roots == [D]

        # Current graph:
        # B --> C --> D --> A
        A.remove_all_leaves()
        assert B.leaves == [C] and C.roots == [B]
        assert C.leaves == [D] and D.roots == [C]
        assert D.leaves == [A] and A.roots == [D]
        assert A.leaves == []

    def test__remove_all_leaves__self_reference(self, dummy_nodes):
        A = dummy_nodes[0]
        A.add_leaf(A)

        # Current graph:
        # -> A -
        # |----|
        assert A.leaves == [A]
        assert A.roots == [A]

        # Current graph:
        #    A
        A.remove_all_leaves()
        assert A.leaves == []
        assert A.roots == []

class TestNodeCollection:
    def test__add_leaf_reference(self, dummy_nodes):
        node_collection = NodeCollection(dummy_nodes)
        root, leaf = node_collection[0], node_collection[1]
        ref_start, ref_stop = 1, 2
        node_collection.add_leaf_reference(root, leaf, ref_start=1, ref_stop=2)
        assert root in leaf.roots
        ref_info = leaf.ref_infos[root.uuid]
        assert (ref_info.start, ref_info.stop) == (ref_start, ref_stop)

    def test__remove_root_reference(self, dummy_nodes_multiple_trees):
        nodes, *_ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        root, leaf_2, leaf_3 = [node_collection[i] for i in [0, 2, 3]]
        orphan = node_collection[4]
        assert leaf_2 in root.leaves
        assert leaf_3 in leaf_2.leaves
        assert [orphan not in node.leaves for node in [root, leaf_2, leaf_3]]

        assert root in leaf_2.roots
        node_collection.remove_root_reference(leaf_2, root)
        assert root not in leaf_2.roots

        with pytest.raises(NodeRemovalException, match='not a root of this node'):
            node_collection.remove_root_reference(leaf_3, root)

        with pytest.raises(NodeRemovalException, match='does not have a root'):
            node_collection.remove_root_reference(orphan, root)

    def test__remove_node(self, dummy_nodes_multiple_trees):
        nodes, *_ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        root, leaf_2, leaf_3 = [node_collection[i] for i in [0, 2, 3]]
        orphan = node_collection[4]
        assert leaf_2 in root.leaves
        assert leaf_3 in leaf_2.leaves
        assert [orphan not in node.leaves for node in [root, leaf_2, leaf_3]]

        node_collection.remove_node(leaf_3)
        assert leaf_3 not in node_collection

        # `leaf_3` has been removed, so this operation should trigger an exception
        with pytest.raises(NodeRemovalException, match='does not exist in this collection'):
            node_collection.remove_node(leaf_3)

        # `root` still has a leaf `leaf_2`
        with pytest.raises(NodeRemovalException, match='there are remaining leaves'):
            node_collection.remove_node(root)

    def test__remove_node_and_its_leaves__multiple_trees(
        self, dummy_nodes_multiple_trees
    ):
        nodes, desired_links, _ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)

        node_0_0_to_0_3 = nodes[:4]
        node_0_0 = nodes[0]
        links_to_be_removed, remaining_links = desired_links[:3], desired_links[3:]
        removed = node_collection.remove_node_and_its_leaves(node_0_0)
        assert set(removed) == set(node_0_0_to_0_3)

        links = node_collection.resolve_links()
        assert all([removed_link not in links for removed_link in links_to_be_removed])
        assert len(links) == len(remaining_links)
        assert all([remaining_link in links for remaining_link in remaining_links])

        node_2_1_to_2_4 = nodes[-4:]
        node_2_1 = nodes[-4]
        links_to_be_removed, remaining_links = desired_links[-3:], []
        removed = node_collection.remove_node_and_its_leaves(node_2_1)
        assert set(removed) == set(node_2_1_to_2_4)

        # `node_2_1` is a leaf node of `node_2_0`, so the link <2_0, 2_1> will
        # also be removed after `node_2_1` is removed. Hence that there is no
        # remaining links now.
        links = node_collection.resolve_links()
        assert links == []

    def test__remove_node_and_its_leaves__circular_references(
        self, dummy_nodes_circular_references
    ):
        nodes, desired_links, _ = dummy_nodes_circular_references
        node_collection = NodeCollection(nodes)

        node_1_0_to_1_2 = nodes[1:4]
        node_1_0 = nodes[1]
        links_to_be_removed, remaining_links = desired_links[:3], desired_links[3:]
        removed = node_collection.remove_node_and_its_leaves(node_1_0)
        assert set(removed) == set(node_1_0_to_1_2)

        links = node_collection.resolve_links()
        assert all([removed_link not in links for removed_link in links_to_be_removed])
        assert len(links) == len(remaining_links)
        assert all([remaining_link in links for remaining_link in remaining_links])

    def test__remove_node_and_its_leaves__self_reference(self, dummy_nodes):
        nodes = dummy_nodes
        A = nodes[0]
        A.add_leaf(A)
        assert A.leaves == [A] and A.roots == [A]

        node_collection = NodeCollection([A])
        links = node_collection.resolve_links()
        assert links == [NodeLink(A, 0, A, 0)]

        node_collection.remove_node_and_its_leaves(A)
        assert len(node_collection) == 0

        links = node_collection.resolve_links()
        assert links == []

    def test__to_dict(self, dummy_node_collection_data):
        data = dummy_node_collection_data
        node_collection = NodeCollection.from_dict(data)
        assert node_collection.to_dict() == data

    def test__resolve_link__multiple_trees(self, dummy_nodes_multiple_trees):
        nodes, desired_links, _ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        links = node_collection.resolve_links()
        assert len(links) == len(desired_links)
        assert all([v in desired_links for v in links])

    def test__resolve_link__circular_references(
        self, dummy_nodes_circular_references
    ):
        nodes, desired_links, _ = dummy_nodes_circular_references
        node_collection = NodeCollection(nodes)
        links = node_collection.resolve_links()
        assert len(links) == len(desired_links)
        assert all([v in desired_links for v in links])

    def test__resolve_link_from_trees__multiple_trees(self, dummy_nodes_multiple_trees):
        nodes, desired_links, _ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        trees, orphans = node_collection.resolve_trees()
        links = node_collection.resolve_links_from_trees(trees)
        assert len(links) == len(desired_links)
        assert all([v in desired_links for v in links])

    def test__resolve_link_from_trees__circular_references(
        self, dummy_nodes_circular_references
    ):
        nodes, desired_links, _ = dummy_nodes_circular_references
        node_collection = NodeCollection(nodes)
        trees, orphans = node_collection.resolve_trees()
        links = node_collection.resolve_links_from_trees(trees)
        assert len(links) == len(desired_links)
        assert all([v in desired_links for v in links])

    def test__resolve_index_link_from_trees__multiple_trees(self, dummy_nodes_multiple_trees):
        nodes, desired_links, _ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        trees, orphans = node_collection.resolve_trees()
        links = node_collection.resolve_index_links_from_trees(trees)

        # Index link is based on element indices in trees rather than indices in
        # `NodeCollection.nodes`, so that we cannot validate these index links
        # with those preset answer from fixture `dummy_nodes_multiple_trees`.
        # Here we use uuid pairs to validate it instead.
        desired_uuid_pairs = [(link.root.uuid, link.leaf.uuid) for link in desired_links]

        uuid_pairs = []
        flatten_trees = [node for tree in trees for layer in tree for node in layer]
        for link in links:
            root, leaf = flatten_trees[link.root_idx], flatten_trees[link.leaf_idx]
            uuid_pairs.append((root.uuid, leaf.uuid))
        assert set(uuid_pairs) == set(desired_uuid_pairs)

    def test__resolve_index_link_from_trees__circular_references(
        self, dummy_nodes_circular_references
    ):
        nodes, desired_links, _ = dummy_nodes_circular_references
        node_collection = NodeCollection(nodes)
        trees, orphans = node_collection.resolve_trees()
        links = node_collection.resolve_index_links_from_trees(trees)

        desired_uuid_pairs = [(link.root.uuid, link.leaf.uuid) for link in desired_links]

        flatten_trees = [node for tree in trees for layer in tree for node in layer]
        uuid_pairs = []
        for link in links:
            root, leaf = flatten_trees[link.root_idx], flatten_trees[link.leaf_idx]
            uuid_pairs.append((root.uuid, leaf.uuid))
        assert set(uuid_pairs) == set(desired_uuid_pairs)

    def test__resolve_index_link__multiple_trees(self, dummy_nodes_multiple_trees):
        nodes, _, desired_index_links = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        links = node_collection.resolve_index_links()
        assert len(links) == len(desired_index_links)
        assert all([v in desired_index_links for v in links])

    def test__resolve_index_link__circular_references(
        self, dummy_nodes_circular_references
    ):
        nodes, _, desired_index_links = dummy_nodes_circular_references
        node_collection = NodeCollection(nodes)
        links = node_collection.resolve_index_links()
        assert len(links) == len(desired_index_links)
        assert all([v in desired_index_links for v in links])

    def test__resolve_trees__multiple_trees(self, dummy_nodes_multiple_trees):
        nodes, *_ = dummy_nodes_multiple_trees
        node_collection = NodeCollection(nodes)
        trees, orphans = node_collection.resolve_trees()
        desired_trees = [
            [[nodes[0]], [nodes[1], nodes[2]], [nodes[3]]],
            [[nodes[5]], [nodes[6]], [nodes[7], nodes[8]], [nodes[9]]],
        ]
        assert len(trees) == len(desired_trees)
        assert orphans == [nodes[4]]
        assert all([tree in desired_trees for tree in trees])

    def test__resolve_trees__circular_references(self, dummy_nodes_circular_references):
        nodes, *_ = dummy_nodes_circular_references
        node_collection = NodeCollection(nodes)
        trees, orphans = node_collection.resolve_trees()
        desired_trees = [
            [[nodes[1]], [nodes[2]], [nodes[3]]],
            [[nodes[4]], [nodes[5]], [nodes[6]]],
        ]
        assert len(trees) == len(desired_trees)
        assert orphans == [nodes[0]]

        # Order of built tree from circular reference loop is not guaranteed
        # to be the same as desired tree.
        for tree in trees:
            assert all([len(layer) == 1 for layer in tree])
