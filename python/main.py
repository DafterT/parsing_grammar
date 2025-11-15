import sys
from pathlib import Path
from get_parse_tree import parse_cli, get_tree_root


def field_name_of(node):
    p = node.parent
    if p is None:
        return node.type
    for i in range(p.child_count):
        if p.child(i) == node and p.field_name_for_child(i):
            return p.field_name_for_child(i)
    return node.type


def write_tree_to_file(node, out_path: str | Path, *, ascii: bool = False) -> None:
    """
    Пишет вывод дерева в файл out_path.
    Ветвление оформлено как в `tree`. Логика печати полностью соответствует исходной.
    """
    VBAR, SPACE, TEE, ELBOW = ("|   ", "    ", "|-- ", "`-- ") if ascii else ("│   ", "    ", "├── ", "└── ")

    replace_names = {
        "list_argDef": "list<argDef>",
        "list_identifier": "list<identifier>",
        "statment_block": "statment.block",
        "listExpr": "list<expr>",
    }

    def _prefix(anc_has_next: list[bool], is_last: bool) -> str:
        if not anc_has_next:
            return ""
        
        base = "".join(VBAR if has_next else SPACE for has_next in anc_has_next)
        return base + (ELBOW if is_last else TEE)

    def _child_anc(anc_has_next: list[bool], is_last: bool) -> list[bool]:
        return [*anc_has_next, not is_last]

    def _walk(n, indent: int, anc_has_next: list[bool], is_last: bool, out):
        fname = field_name_of(n)
        is_token = n.type in (
            "identifier",
            "bin_op",
            "str",
            "char",
            "hex",
            "bits",
            "dec",
            "un_op",
            "builtin",
        )
        if fname in replace_names:
            fname = replace_names[fname]

        if is_token:
            out.write(f"{_prefix(anc_has_next, is_last)}{fname}\n")

        if n.is_missing:
            print(f"Error: missing element \"{n.type}\" in end point {n.end_point}", file=sys.stderr)
        if n.is_error:
            print(f"Error: incorrect in end point {n.end_point}", file=sys.stderr)
        
        if len(n.children) == 0:
            text = n.text.decode("utf-8")
            if is_token:
                child_pref = _prefix(_child_anc(anc_has_next, is_last), True)
                out.write(f'{child_pref}"{text}"\n')
            else:
                if not anc_has_next:
                    out.write(f"{_prefix(anc_has_next, is_last)}{fname}\n")
                else:
                    out.write(f'{_prefix(anc_has_next, is_last)}"{text}"\n')
        else:
            out.write(f"{_prefix(anc_has_next, is_last)}{fname}\n")

        child_anc = _child_anc(anc_has_next, is_last)

        inject_cfg = {
            "funcSignature": ("list_argDef", "("),
            "call_expression": ("listExpr", "("),
            "indexer": ("listExpr", "["),
        }
        need_field, left_token = inject_cfg.get(n.type, (None, None))
        present_fields = {n.field_name_for_child(i) for i in range(n.child_count)} - {None}
        should_inject = bool(need_field) and (need_field not in present_fields)
        injected = False

        for i, ch in enumerate(n.children):
            _walk(ch, indent + 1, child_anc, i == len(n.children) - 1, out)

            if (should_inject and not injected and ch.type == left_token):
                display = replace_names.get(need_field, need_field)
                out.write(f"{_prefix(child_anc, False)}{display} (empty)\n")
                injected = True
            
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        _walk(node, 0, [], True, f)



def main():
    grammar_dir, lang_name, file_path, out_file_path, lib_path = parse_cli()
    root = get_tree_root(lib_path, lang_name, file_path, grammar_dir)
    write_tree_to_file(root, out_file_path)


if __name__ == "__main__":
    main()
