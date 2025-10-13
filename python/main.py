import argparse
import os
import sys
import subprocess
from ctypes import CDLL, PYFUNCTYPE, pythonapi, c_void_p, c_char_p, py_object
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter


def parse_cli():
    p = argparse.ArgumentParser(description="Сборка и запуск tree-sitter парсера")
    p.add_argument("grammar_dir", help="Путь к папке с грамматикой (library)")
    p.add_argument("lang_name", help="Имя парсера, напр. 'foo' для tree_sitter_foo")
    p.add_argument("file_path", help="Путь к файлу для парсинга")
    p.add_argument("out_file_path", help="Путь к выходному файлу")
    a = p.parse_args()
    return a.grammar_dir, a.lang_name, a.file_path, a.out_file_path


def build_parser(grammar_dir: str, lang_name: str) -> str:
    """Собрать shared-библиотеку в <grammar_dir>/build/<lang_name>.(dll|so|dylib)."""
    out_dir = os.path.join(grammar_dir, "build")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{lang_name}.dll")

    # Генерация и сборка через официальную CLI
    subprocess.run(
        ["tree-sitter", "generate", "--abi", str(tree_sitter.LANGUAGE_VERSION)],
        cwd=grammar_dir,
        check=True,
    )
    subprocess.run(
        ["tree-sitter", "build", "-o", out_path], cwd=grammar_dir, check=True
    )
    return out_path


def load_and_parse(lib_path: str, lang_name: str, file_path: str):
    """Загрузить язык из DLL, распарсить файл, вернуть корневой узел."""
    cdll = CDLL(os.path.abspath(lib_path))
    func_name = f"tree_sitter_{lang_name}"
    if not hasattr(cdll, func_name) and hasattr(cdll, func_name + "_language"):
        func_name = func_name + "_language"
    func = getattr(cdll, func_name)
    func.restype = c_void_p
    ptr = func()

    PyCapsule_New = PYFUNCTYPE(py_object, c_void_p, c_char_p, c_void_p)(
        ("PyCapsule_New", pythonapi)
    )
    capsule = PyCapsule_New(ptr, b"tree_sitter.Language", None)
    lang = Language(capsule)

    parser = Parser(lang)
    with open(file_path, "rb") as f:
        data = f.read()
    tree = parser.parse(data, encoding="utf8")
    return tree.root_node


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
            "break",
            "builtin",
        )
        if fname in replace_names:
            fname = replace_names[fname]

        if is_token:
            out.write(f"{_prefix(anc_has_next, is_last)}{fname}\n")

        if n.is_missing:
            print(f"Error: missing element \"{n.type}\" in end point {n.end_point}",file=sys.stderr)
        if n.is_error:
            print(f"Error: incorrect in end point {n.end_point}",file=sys.stderr)
        
        if len(n.children) == 0:
            text = n.text.decode("utf-8")
            if is_token:
                child_pref = _prefix(_child_anc(anc_has_next, is_last), True)
                out.write(f'{child_pref}"{text}"\n')
            else:
                out.write(f'{_prefix(anc_has_next, is_last)}"{text}"\n')
        else:
            out.write(f"{_prefix(anc_has_next, is_last)}{fname}\n")

        child_anc = _child_anc(anc_has_next, is_last)
        for i, ch in enumerate(n.children):
            _walk(ch, indent + 1, child_anc, i == len(n.children) - 1, out)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        _walk(node, 0, [], True, f)



def main():
    grammar_dir, lang_name, file_path, out_file_path = parse_cli()
    lib_path = build_parser(grammar_dir, lang_name)
    root = load_and_parse(lib_path, lang_name, file_path)

    write_tree_to_file(root, out_file_path)


if __name__ == "__main__":
    main()
