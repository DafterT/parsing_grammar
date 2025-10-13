import argparse
import os
import platform
import subprocess
from ctypes import CDLL, PYFUNCTYPE, pythonapi, c_void_p, c_char_p, py_object

from tree_sitter import Language, Parser
import tree_sitter


def parse_cli():
    p = argparse.ArgumentParser(description="Сборка и запуск tree-sitter парсера")
    p.add_argument("grammar_dir", help="Путь к папке с грамматикой (library)")
    p.add_argument("lang_name", help="Имя парсера, напр. 'foo' для tree_sitter_foo")
    p.add_argument("file_path", help="Путь к файлу для парсинга")
    a = p.parse_args()
    return a.grammar_dir, a.lang_name, a.file_path


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


def main():
    grammar_dir, lang_name, file_path = parse_cli()
    lib_path = build_parser(grammar_dir, lang_name)
    root = load_and_parse(lib_path, lang_name, file_path)

    def walk(node, indent=0):
        fname = field_name_of(node)
        is_token = node.type in (
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

        replace_names = {
            "list_argDef": "list<argDef>",
            "list_identifier": "list<identifier>",
            "statment_block": "statment.block",
            "listExpr": "list<expr>",
        }

        if fname in replace_names:
            fname = replace_names[fname]

        indent_str = "  " * indent
        indent_next = indent + 1 if is_token else indent
        indent_next_str = "  " * indent_next

        if is_token:
            print(f"{indent_str}{fname}")

        if len(node.children) == 0:
            text = node.text.decode("utf-8")
            print(f'{indent_next_str}"{text}"')
        else:
            print(f"{indent_str}{fname}")

        for ch in node.children:
            walk(ch, indent + 1)

    walk(root)
    # дальнейшая логика — на вашей стороне


if __name__ == "__main__":
    main()
