import argparse
import os
import subprocess
from ctypes import CDLL, PYFUNCTYPE, pythonapi, c_void_p, c_char_p, py_object
from pathlib import Path

from tree_sitter import Language, Parser

def parse_cli():
    """
    Единственный режим: уже собранная библиотека.

       python main.py --lib path/to/parser.dll [--lang foo] input.txt output.txt

       --lib  : путь к .dll/.so/.dylib (обязательный)
       --lang : имя языка (foo => функция tree_sitter_foo). Если не указано,
                имя берётся из имени файла библиотеки.
    """
    p = argparse.ArgumentParser(description="Запуск tree-sitter парсера по готовой DLL")

    p.add_argument(
        "--lib",
        required=True,
        dest="lib_path",
        help="Путь к готовой tree-sitter библиотеке (.so/.dll/.dylib).",
    )
    p.add_argument(
        "--lang",
        dest="lib_lang_name",
        help=(
            "Имя языка при использовании --lib (например, 'foo' для tree_sitter_foo). "
            "Если не указано, будет выведено из имени файла библиотеки."
        ),
    )

    p.add_argument("file_path", help="Путь к файлу для парсинга")
    p.add_argument("out_file_path", help="Путь к выходному файлу")

    a = p.parse_args()

    lib_path = a.lib_path
    if a.lib_lang_name:
        lang_name = a.lib_lang_name
    else:
        stem = Path(a.lib_path).stem  # e.g. libfoo -> libfoo, foo -> foo
        lang_name = stem[3:] if stem.startswith("lib") else stem

    return None, lang_name, a.file_path, a.out_file_path, lib_path

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

def get_tree_root(lib_path, lang_name, file_path, grammar_dir=None):
    if not lib_path:
        raise ValueError("lib_path is required for parsing")
    return load_and_parse(lib_path, lang_name, file_path)