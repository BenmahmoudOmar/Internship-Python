from vsdx import VisioFile
from jinja2 import Environment, FileSystemLoader
import os

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
                    lines = text.splitlines()
                    state_name = lines[0].strip() if lines else "(no label)"
                    attributes = "\n".join(line.strip() for line in lines[1:]) if len(lines) > 1 else ""
                    nodes.add((state_name, attributes))

    return nodes, edges


def generate_html_report(added_nodes, deleted_nodes, added_edges, deleted_edges, output_file):
    env = Environment(loader=FileSystemLoader(searchpath=os.getcwd()))
    template = env.get_template("report_template.html")

    rendered = template.render(
        added_nodes=sorted(added_nodes),
        deleted_nodes=sorted(deleted_nodes),
        added_edges=sorted(added_edges),
        deleted_edges=sorted(deleted_edges)
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"✅ Jinja2 report saved to: {output_file}")


if __name__ == "__main__":
    initial_vsdx = r"C:\Users\benma\Downloads\diagram_act001.vsdx"
    updated_vsdx = r"C:\Users\benma\Downloads\diagram_act002.vsdx"

    initial_nodes, initial_edges = extract_diagram_info(initial_vsdx)
    updated_nodes, updated_edges = extract_diagram_info(updated_vsdx)

    added_nodes = updated_nodes - initial_nodes
    deleted_nodes = initial_nodes - updated_nodes
    added_edges = updated_edges - initial_edges
    deleted_edges = initial_edges - updated_edges

    output_path = "diagram_comparison_report.html"
    generate_html_report(added_nodes, deleted_nodes, added_edges, deleted_edges, output_path)
