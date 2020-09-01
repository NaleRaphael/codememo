import pytest

from codememo.objects import (
    Snippet, Node, NodeLink, NodeCollection
)


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


class TestNode:
    def test_node__add_leaf__self_reference(self, dummy_nodes):
        A = dummy_nodes[0]
        with pytest.raises(ValueError, match='Self reference'):
            A.add_leaf(A)

    def test_node__add_leaf__circular_reference(self, dummy_nodes):
        A, B = dummy_nodes[0], dummy_nodes[1]
        A.add_leaf(B)
        with pytest.raises(ValueError, match='Circular reference'):
            B.add_leaf(A)

    def test_node__add_leaf__multiple_root(self, dummy_nodes):
        A, B, C = dummy_nodes[0], dummy_nodes[1], dummy_nodes[2]
        A.add_leaf(B)
        with pytest.raises(ValueError, match='Multiple root'):
            C.add_leaf(B)

    def test_node__add_leaf__exceed_range(self, dummy_nodes):
        A, B = dummy_nodes[0], dummy_nodes[1]
        n_lines = A.snippet.n_lines
        with pytest.raises(ValueError, match='should be in the range'):
            A.add_leaf(B, 0)
        with pytest.raises(ValueError, match='should be in the range'):
            A.add_leaf(B, n_lines + 1)
