#!/usr/bin/env python3
# print_tree.py — формат вывода 1-в-1 как `tree-sitter p`, + текст листьев.
# - только named-узлы (анон токены скрыты)
# - поля: field: (type [r,c] - [r,c])
# - листья: доп. строка text: '...'
# - --all: добавляет text и на "ветвях" (заголовок узла)

import argparse
import sys
from pathlib import Path
import ctypes
import warnings
from tree_sitter import Language, Parser


def read_source(path: str) -> bytes:
    if path == "-" or not path:
        return sys.stdin.buffer.read()
    return Path(path).read_bytes()


def load_language_from_dll(lib_path: str, lang_name: str) -> Language:
    lib = ctypes.CDLL(lib_path)
    sym = f"tree_sitter_{lang_name}"
    try:
        lang_fn = getattr(lib, sym)
    except AttributeError as e:
        raise SystemExit(
            f"Не найден символ {sym} в {lib_path}. "
            f"Проверь name: \"{lang_name}\" в grammar.js и пересборку parser.dll."
        ) from e
    lang_fn.restype = ctypes.c_void_p
    ptr = lang_fn()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return Language(ptr)  # int-адрес
    except TypeError:
        return Language(ctypes.c_void_p(ptr))  # указатель


def pos(n) -> str:
    # нулевые индексы, формат как у `p`: [r, c] - [r, c]
    sr, sc = n.start_point
    er, ec = n.end_point
    return f"[{sr}, {sc}] - [{er}, {ec}]"


def node_text(n, src: bytes) -> str:
    return src[n.start_byte:n.end_byte].decode("utf-8", "replace")


def named_children_with_fields(node):
    """Вернём список (child, fieldname) только для named-детей.
    Если поле повешено на анонимный элемент (например, '(' в seq),
    подтянем его к ближайшему слева анонимному брату, иначе попробуем справа.
    """
    res = []
    # соберём сырых детей и заранее их field-имена
    kids = [(i, node.child(i)) for i in range(node.child_count)]
    fields = {i: node.field_name_for_child(i) for i, _ in kids}

    # индексы только named-детей
    named_idx = [i for i, ch in kids if ch.is_named]

    for i in named_idx:
        ch = node.child(i)
        fname = fields.get(i)
        if not fname:
            # ищем влево по анонимным братьям
            j = i - 1
            while j >= 0 and not node.child(j).is_named:
                f = fields.get(j)
                if f:
                    fname = f
                    break
                j -= 1
        if not fname:
            # попробуем вправо по анонимным братьям (на случай иной разметки)
            j = i + 1
            while j < node.child_count and not node.child(j).is_named:
                f = fields.get(j)
                if f:
                    fname = f
                    break
                j += 1
        res.append((ch, fname))
    return res


def dump_like_p(node, src: bytes, field: str | None, indent: int, show_all: bool, lines: list[int | str]) -> int:
    """Печатаем одну строку заголовка узла в стиле `p` и рекурсивно детей.
    Возвращаем индекс ПОСЛЕДНЕЙ структурной строки, чтобы туда дописать ')'.
    """
    ind = "  " * indent
    prefix = f"{field}: " if field else ""
    header = f"{ind}{prefix}({node.type} {pos(node)}"
    if show_all:
        header += f"  text: {node_text(node, src)!r}"
    # добавляем заголовок (без ')', если есть дети)
    lines.append(header)
    header_idx = len(lines) - 1  # индекс последней структурной строки

    kids = named_children_with_fields(node)
    if not kids:
        # Лист: закрываем тут же и печатаем подстроку текста
        lines[header_idx] += ")"
        lines.append(f"{ind}  text: {node_text(node, src)!r}")
        return header_idx

    # Есть дети — печатаем каждого (как отдельный заголовок со своим field:)
    last_struct_idx = header_idx
    for ch, f in kids:
        last_struct_idx = dump_like_p(ch, src, f, indent + 1, show_all, lines)

    # Закрывающая скобка уходит в конец ПОСЛЕДНЕЙ структурной строки
    lines[last_struct_idx] += ")"
    return last_struct_idx


def main():
    ap = argparse.ArgumentParser(description="Вывод как `tree-sitter p`, но с текстом листьев.")
    ap.add_argument("input", help="Файл исходника или '-' для stdin")
    ap.add_argument("--lib", default="parser.dll", help="Путь к DLL с языком")
    ap.add_argument("--lang", default="var2", help="Имя языка из grammar.js")
    ap.add_argument("--all", action="store_true",
                    help="Добавлять text: '...' к заголовкам (ветвям)")
    args = ap.parse_args()

    src = read_source(args.input)
    lang = load_language_from_dll(args.lib, args.lang)
    parser = Parser(lang)
    tree = parser.parse(src)

    # Собираем строки
    lines: list[str] = []
    dump_like_p(tree.root_node, src, field=None, indent=0, show_all=args.all, lines=lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
