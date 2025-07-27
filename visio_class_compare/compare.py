import argparse
import os
from vsdx import VisioFile
from jinja2 import Environment, FileSystemLoader
#deee
def extract_class_diagram_info(vsdx_path):
    classes = dict()
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

            for shape in shapes_by_id.values():
                if not shape.child_shapes:
                    continue

                title = None
                attributes = set()

                for sub in shape.child_shapes:
                    if not sub.text:
                        continue
                    text = sub.text.strip()
                    if '=' in text:
                        attributes.add(text)
                    else:
                        title = text

                if title:
                    classes[title] = attributes

            for shape_id, shape in shapes_by_id.items():
                master = shape.master_page.name.lower() if shape.master_page else ""
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
                            edges.add((from_text, to_text))

    return classes, edges

def compare_classes(initial_nodes, updated_nodes):
    added_classes = set(updated_nodes.keys()) - set(initial_nodes.keys())
    deleted_classes = set(initial_nodes.keys()) - set(updated_nodes.keys())

    changed_classes = []
    common_classes = set(initial_nodes.keys()) & set(updated_nodes.keys())

    for class_title in common_classes:
        old_attrs = initial_nodes[class_title]
        new_attrs = updated_nodes[class_title]

        if old_attrs != new_attrs:
            if not old_attrs and not new_attrs:
                continue
            changed_classes.append((
                class_title,
                sorted(old_attrs),
                sorted(new_attrs)
            ))

    return added_classes, deleted_classes, changed_classes

def generate_html_report(added_classes, deleted_classes, changed_classes, added_edges, deleted_edges,
                         initial_nodes, updated_nodes, output_file):
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    added_nodes = [(name, sorted(updated_nodes[name])) for name in added_classes]
    deleted_nodes = [(name, sorted(initial_nodes[name])) for name in deleted_classes]

    changed_nodes = [
        (name, old_attrs, new_attrs)
        for name, old_attrs, new_attrs in changed_classes
    ]

    rendered = template.render(
        added_nodes=added_nodes,
        deleted_nodes=deleted_nodes,
        changed_nodes=changed_nodes,
        added_edges=sorted(added_edges),
        deleted_edges=sorted(deleted_edges)
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Jinja2 report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Compare Visio class diagrams and generate HTML report")
    parser.add_argument("initial_vsdx", help="Path to the initial Visio file (.vsdx)")
    parser.add_argument("updated_vsdx", help="Path to the updated Visio file (.vsdx)")
    parser.add_argument("-o", "--output-dir", default="output", help="Output directory for the HTML report")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    initial_nodes, initial_edges = extract_class_diagram_info(args.initial_vsdx)
    updated_nodes, updated_edges = extract_class_diagram_info(args.updated_vsdx)

    added_classes, deleted_classes, changed_classes = compare_classes(initial_nodes, updated_nodes)
    added_edges = updated_edges - initial_edges
    deleted_edges = initial_edges - updated_edges

    output_path = os.path.join(args.output_dir, "diagram_comparison_report.html")
    generate_html_report(
        added_classes, deleted_classes, changed_classes,
        added_edges, deleted_edges,
        initial_nodes, updated_nodes,
        output_path
    )

if __name__ == "__main__":
    main()
