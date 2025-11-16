import sys
from pathlib import Path
from get_parse_tree import parse_cli, get_tree_root
from tree_parser import print_tree_view, build_tree_view, dfs_tree


def main():
    grammar_dir, lang_name, file_path, out_file_path, lib_path = parse_cli()
    root = get_tree_root(lib_path, lang_name, file_path, grammar_dir)
    view_root = build_tree_view(root)
    print_tree_view(view_root)
    dfs_tree(view_root)


if __name__ == "__main__":
    main()
