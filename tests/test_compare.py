from visio_class_compare.compare import compare_classes, generate_html_report

def test_compare_classes_changes():
    initial_nodes = {
        "ClassA": {"attr1", "attr2"},
        "ClassB": {"attrX"},
    }
    updated_nodes = {
        "ClassA": {"attr1", "attr2"},  # unchanged
        "ClassC": {"attrY"},           # new
    }

    added_classes, deleted_classes, changed_classes = compare_classes(initial_nodes, updated_nodes)

    assert added_classes == {"ClassC"}
    assert deleted_classes == {"ClassB"}
    assert changed_classes == []

def test_generate_html_report(tmp_path):
    added_classes = {"ClassC"}
    deleted_classes = {"ClassB"}
    changed_classes = []
    added_edges = {("A", "B")}
    deleted_edges = set()

    initial_nodes = {"ClassB": {"attrX"}}
    updated_nodes = {"ClassC": {"attrY"}}

    output_file = tmp_path / "report.html"

    generate_html_report(
        added_classes,
        deleted_classes,
        changed_classes,
        added_edges,
        deleted_edges,
        initial_nodes,
        updated_nodes,
        output_file
    )

    assert output_file.exists()
    content = output_file.read_text()
    assert "ClassC" in content
    assert "ClassB" in content
