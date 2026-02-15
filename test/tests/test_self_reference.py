from api.v1.self_reference_pydantic import TreeNode


def test_tree_node_leaf():
    """A leaf node with no children or parent."""
    leaf = TreeNode(name="leaf", children=[])
    assert leaf.name == "leaf"
    assert leaf.children == []
    assert leaf.parent is None


def test_tree_node_nested():
    """A tree with nested children."""
    tree = TreeNode(
        name="root",
        children=[
            TreeNode(name="child1", children=[]),
            TreeNode(
                name="child2",
                children=[TreeNode(name="grandchild", children=[])],
            ),
        ],
    )
    assert tree.name == "root"
    assert len(tree.children) == 2
    assert tree.children[1].children[0].name == "grandchild"


def test_tree_node_json_roundtrip():
    """Self-referencing model should survive JSON roundtrip."""
    tree = TreeNode(
        name="root",
        children=[TreeNode(name="child", children=[])],
    )
    json_str = tree.model_dump_json()
    restored = TreeNode.model_validate_json(json_str)
    assert restored == tree
