from get_parse_tree import parse_cli, get_tree_root
from tree_parser import print_tree_view, build_tree_view
from graph_parser import build_graph, render_cfg


def main():
    grammar_dir, lang_name, file_path, out_file_path, lib_path = parse_cli()
    root = get_tree_root(lib_path, lang_name, file_path, grammar_dir)
    view_root = build_tree_view(root)
    print_tree_view(view_root)

    for i in view_root.children:
        cfg = build_graph(i)
        render_cfg(cfg, filename="example_cfg", fmt="svg")


if __name__ == "__main__":
    main()
