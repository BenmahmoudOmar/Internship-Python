from vsdx import VisioFile

def extract_diagram_info(vsdx_path):
    nodes = set()
    edges = set()

    with VisioFile(vsdx_path) as vis:
        for page in vis.pages:
            shapes_by_id = {}
            connector_masters = {'connector', 'dynamic connector', 'arced line arrow', 'line'}

            def index_shapes_recursively(shape):
                if shape.ID not in shapes_by_id:
                    shapes_by_id[shape.ID] = shape
                    for sub_shape in shape.child_shapes:
                        index_shapes_recursively(sub_shape)

            for shape in page.child_shapes:
                index_shapes_recursively(shape)

            for shape_id, shape in shapes_by_id.items():
                master = shape.master_page.name.lower() if shape.master_page else ""
                text = shape.text.strip() if shape.text else "(no text)"

                if any(conn in master for conn in connector_masters):
                    connects = list(getattr(shape, "connects", []))
                    conn_ids = [c.to_id for c in connects if c.to_id != shape.ID]

                    if len(conn_ids) >= 2:
                        from_id, to_id = conn_ids[0], conn_ids[1]
                        from_shape = shapes_by_id.get(from_id)
                        to_shape = shapes_by_id.get(to_id)
                        if from_shape and to_shape:
                            from_text = from_shape.text.strip() if from_shape.text else "(no text)"
                            to_text = to_shape.text.strip() if to_shape.text else "(no text)"
                            edges.add((from_text, to_text, text))
                else:
                    nodes.add(text)
    return nodes, edges

def generate_html_report(added_nodes, deleted_nodes, added_edges, deleted_edges, output_file):
    html_template = """
    <html><head><style>
    body {{ font-family: Arial; }}
    h2 {{ color: #2F4F4F; }}
    table {{ border-collapse: collapse; width: 80%; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; }}
    th {{ background-color: #f2f2f2; }}
    .added {{ background-color: #d4fcdc; }}
    .deleted {{ background-color: #fcdcdc; }}
    </style></head><body>
    <h2>Visio Diagram Comparison Report</h2>

    <h3>🟢 Added Nodes</h3>
    <table><tr><th>Label</th></tr>{0}</table>

    <h3>🔴 Deleted Nodes</h3>
    <table><tr><th>Label</th></tr>{1}</table>

    <h3>🟢 Added Edges</h3>
    <table><tr><th>From</th><th>To</th><th>Label</th></tr>{2}</table>

    <h3>🔴 Deleted Edges</h3>
    <table><tr><th>From</th><th>To</th><th>Label</th></tr>{3}</table>

    </body></html>
    """

    added_node_rows = ''.join(f'<tr class="added"><td>{n}</td></tr>' for n in added_nodes)
    deleted_node_rows = ''.join(f'<tr class="deleted"><td>{n}</td></tr>' for n in deleted_nodes)
    added_edge_rows = ''.join(f'<tr class="added"><td>{f}</td><td>{t}</td><td>{l}</td></tr>' for f, t, l in added_edges)
    deleted_edge_rows = ''.join(f'<tr class="deleted"><td>{f}</td><td>{t}</td><td>{l}</td></tr>' for f, t, l in deleted_edges)

    html = html_template.format(added_node_rows, deleted_node_rows, added_edge_rows, deleted_edge_rows)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report saved as: {output_file}")

if __name__ == "__main__":
    # paths
    initial_vsdx = r"C:\Users\benma\Downloads\diagram_act.vsdx"
    updated_vsdx = r"C:\Users\benma\Downloads\diag_act2.vsdx"

    # Extract
    initial_nodes, initial_edges = extract_diagram_info(initial_vsdx)
    updated_nodes, updated_edges = extract_diagram_info(updated_vsdx)

    # Compare
    added_nodes = updated_nodes - initial_nodes
    deleted_nodes = initial_nodes - updated_nodes
    added_edges = updated_edges - initial_edges
    deleted_edges = initial_edges - updated_edges

    # Generate HTML
    output_path = "diagram_comparison_report.html"
    generate_html_report(added_nodes, deleted_nodes, added_edges, deleted_edges, output_path)
