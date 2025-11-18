from get_parse_tree import parse_cli, get_tree_root
from tree_parser import write_tree_view_to_file, build_tree_view
from graph_parser import build_graph, render_cfg


def main():
    grammar_dir, lang_name, file_path, out_file_path, lib_path = parse_cli()
    root = get_tree_root(lib_path, lang_name, file_path, grammar_dir)
    view_root, errors_tree_build = build_tree_view(root)
    if errors_tree_build:
        print('\r\n'.join(errors_tree_build))
        return
    
    write_tree_view_to_file(view_root, f"{out_file_path}/my_tree")

    for indx, i in enumerate(view_root.children):
        cfg, coll_names, errors_graph = build_graph(i)
        print('\r\n'.join(errors_graph))
        print('\r\n'.join(coll_names))
        render_cfg(cfg, filename=f"{out_file_path}/example_cfg_{indx}", fmt="svg")
        cfg.remove_dangling_blocks()
        render_cfg(cfg, filename=f"{out_file_path}/example_cfg_{indx}_rem", fmt="svg")


if __name__ == "__main__":
    main()
