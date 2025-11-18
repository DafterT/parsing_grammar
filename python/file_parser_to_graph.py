from pathlib import Path

from get_parse_tree import get_tree_root
from tree_parser import write_tree_view_to_file, build_tree_view
from graph_parser import build_graph, render_cfg, get_func_name
from graphviz import Digraph  

import argparse


def parse_cli():
    """
    Поддерживаются два режима запуска:

    1) Уже собранная библиотека:
       python main.py --lib path/to/parser.dll [--lang foo] input1.txt [input2.txt ...] output_dir

       --lib  : путь к .dll/.so/.dylib
       --lang : имя языка (foo => функция tree_sitter_foo). Если не указано,
                имя берётся из имени файла библиотеки.

    2) Грамматика-проект (нужно собрать библиотеку):
       python main.py path/to/grammar foo input1.txt [input2.txt ...] output_dir

       grammar_dir : путь к папке с grammar.js
       lang_name   : имя языка (foo => функция tree_sitter_foo)
    """
    p = argparse.ArgumentParser(description="Сборка и запуск tree-sitter парсера")

    # Общие опции
    p.add_argument(
        "--lib",
        dest="lib_path",
        help=(
            "Путь к уже скомпилированной tree-sitter библиотеке (.so/.dll/.dylib). "
            "В этом режиме grammar_dir и lang_name позиционно не задаются."
        ),
    )
    p.add_argument(
        "--lang",
        dest="lib_lang_name",
        help=(
            "Имя языка при использовании --lib (например, 'foo' для tree_sitter_foo). "
            "Если не указано, будет выведено из имени файла библиотеки."
        ),
    )

    # Остаток позиционных аргументов.
    # В lib-режиме:      file1 [file2 ...] out_dir
    # В grammar-режиме:  grammar_dir lang_name file1 [file2 ...] out_dir
    p.add_argument(
        "rest",
        nargs="+",
        help=(
            "Режим 1 (--lib): file1 [file2 ...] out_dir\n"
            "Режим 2 (grammar): grammar_dir lang_name file1 [file2 ...] out_dir"
        ),
    )

    a = p.parse_args()

    # Режим 1: уже собранная библиотека
    if a.lib_path is not None:
        if len(a.rest) < 2:
            p.error(
                "В режиме --lib нужно указать хотя бы один входной файл и путь к выходной папке.\n"
                "Пример: python main.py --lib path/to/lib.so input1.c [input2.c ...] out_dir"
            )

        file_paths = a.rest[:-1]
        out_dir = a.rest[-1]

        grammar_dir = None
        lib_path = a.lib_path

        # Имя языка: сначала берём из --lang, иначе вытаскиваем из имени файла
        if a.lib_lang_name:
            lang_name = a.lib_lang_name
        else:
            stem = Path(a.lib_path).stem  # e.g. libfoo -> libfoo, foo -> foo
            lang_name = stem[3:] if stem.startswith("lib") else stem

    # Режим 2: проект с грамматикой (сборка)
    else:
        # Нужны минимум: grammar_dir, lang_name, один файл и out_dir
        if len(a.rest) < 4:
            p.error(
                "В режиме сборки из грамматики нужно указать "
                "grammar_dir lang_name хотя бы один входной файл и выходную папку.\n"
                "Пример: python main.py path/to/grammar foo input1.txt [input2.txt ...] out_dir"
            )

        grammar_dir = a.rest[0]
        lang_name = a.rest[1]
        file_paths = a.rest[2:-1]
        out_dir = a.rest[-1]
        lib_path = None

    return grammar_dir, lang_name, file_paths, out_dir, lib_path


def analyze_files(file_paths, lib_path, lang_name, grammar_dir, out_dir=None):
    """
    Обработка набора файлов.

    :param file_paths: iterable путей к входным файлам.
    :param lib_path: путь к уже собранной библиотеке tree-sitter (или None, если используем grammar_dir).
    :param lang_name: имя языка (foo => tree_sitter_foo).
    :param grammar_dir: путь к папке с грамматикой (или None, если используем lib_path).
    :param out_dir: базовая папка для вывода (`tree/` и `graph/`). Если None — файлы не пишем.

    :return: словарь вида:
             {
                 "func_name": (set(call_names), [errors...]),
                 "<file:имя_файла>": (set(), [file_level_errors...]),
                 ...
             }
             Для каждой функции — множество вызываемых функций и список всех ошибок/предупреждений.
    """
    results_internal = {}  # func_name -> {"calls": set(), "errors": [], "cfg": None, "tree": None}
    global_func_names = set()  # множество всех имён функций (для проверки дубликатов)

    tree_dir = graph_dir = None
    if out_dir is not None:
        out_dir = Path(out_dir)
        tree_dir = out_dir / "tree"
        graph_dir = out_dir / "graph"
        tree_dir.mkdir(parents=True, exist_ok=True)
        graph_dir.mkdir(parents=True, exist_ok=True)

    for file_path in file_paths:
        file_path = str(file_path)
        input_file_name = Path(file_path).stem

        root = get_tree_root(lib_path, lang_name, file_path, grammar_dir)
        view_root, errors_tree_build = build_tree_view(root)

        # Ошибки построения дерева: не прерываем всю обработку, а завязываем на "псевдо-функцию" файла
        if errors_tree_build:
            pseudo_name = f"<file:{input_file_name}>"
            data = results_internal.setdefault(
                pseudo_name, {"calls": set(), "errors": [], "cfg": None, "tree": view_root}
            )
            for msg in errors_tree_build:
                data["errors"].append(f"{file_path}: {msg}")
            # По аналогии с исходным кодом — функции для этого файла не разбираем
            continue

        # Сохраняем дерево в файл (если задан out_dir)
        if tree_dir is not None:
            write_tree_view_to_file(view_root, str(tree_dir / input_file_name))

        # Обходим функции верхнего уровня
        for node in getattr(view_root, "children", []):
            func_name = get_func_name(node).strip().strip('"')
            if not func_name:
                # На всякий случай пропускаем "безымянные" узлы
                continue

            data = results_internal.setdefault(
                func_name, {"calls": set(), "errors": [], "cfg": None, "tree": node}
            )
            # Всегда обновляем tree на последний узел (объявление/реализацию)
            data["tree"] = node

            # Проверка повторных объявлений / перегрузки
            if func_name in global_func_names:
                # Функция уже встречалась ранее
                if data["cfg"] is None and not data["errors"]:
                    # Функция существует логически, но пока "not defined"
                    # (нет CFG и нет ошибок) — можно попытаться принять
                    # новую реализацию при выполнении пользовательского условия.
                    
                    # Дерево "старого" объявления/описания (если оно уже было)
                    previous_tree = results_internal[func_name]['tree'].children[0].children[1]
                    # Дерево текущего узла
                    current_tree = node.children[0].children[1]
                    if previous_tree != current_tree:
                        data["errors"].append(
                            f"Ошибка: попытка перегрузки функции '{func_name}' в файле '{file_path}'"
                        )
                        continue
                    # если условие выполняется — не прерываем, даём пройти дальше
                    # и построить CFG для новой реализации
                else:
                    # Уже есть реализация (cfg != None) или были ошибки —
                    # это точно попытка перегрузки
                    data["errors"].append(
                        f"Ошибка: попытка перегрузки функции '{func_name}' в файле '{file_path}'"
                    )
                    continue

            # Первое появление имени или допустимая "дореализация" сверху
            global_func_names.add(func_name)

            # Построение графа
            try:
                cfg, call_names, errors_graph = build_graph(node)
            except SyntaxError as e:
                data["errors"].append(
                    f"SyntaxError while building graph for '{func_name}' "
                    f"in file '{file_path}': {e}"
                )
                continue
            if cfg is None:
                continue
            # Ошибки парсинга графа
            for err in errors_graph:
                data["errors"].append(f"{file_path}: {err}")

            # Множество вызываемых функций
            for name in call_names:
                clean_name = name.strip().strip('"')
                if clean_name:
                    data["calls"].add(clean_name)

            # Финальная обработка CFG и сохранение графа, если нужно
            cfg.remove_dangling_blocks()

            data["cfg"] = cfg
            if graph_dir is not None:
                render_cfg(
                    cfg,
                    filename=str(graph_dir / f"{input_file_name}_{func_name}"),
                    fmt="svg",
                )

    result = {
        name: (info["calls"], info["errors"], info["cfg"], info["tree"])
        for name, info in results_internal.items()
    }
    return result

def write_errors_report(result, filename: str) -> None:
    """
    Пишет человекочитаемый отчёт об ошибках в файл filename.
    Файл создаётся только если действительно есть какие-то ошибки/проблемы.
    """
    lines: list[str] = []

    # Разделим файл-уровень и функции
    file_entries = {
        name: (calls, errors, cfg, tree)
        for name, (calls, errors, cfg, tree) in result.items()
        if name.startswith("<file:")
    }
    func_entries = {
        name: (calls, errors, cfg, tree)
        for name, (calls, errors, cfg, tree) in result.items()
        if not name.startswith("<file:")
    }

    # ==== Ошибки на уровне файлов ====
    file_section_added = False
    for pseudo_name, (_calls, errors, _cfg, _tree) in sorted(file_entries.items()):
        if not errors:
            continue
        if not file_section_added:
            lines.append("=== FILE-LEVEL ERRORS ===")
            file_section_added = True

        # pseudo_name = "<file:basename>"
        if pseudo_name.startswith("<file:") and pseudo_name.endswith(">"):
            fname = pseudo_name[len("<file:"):-1]
        else:
            fname = pseudo_name

        lines.append(f"\n[File: {fname}]")
        for err in errors:
            lines.append(f"  - {err}")

    # ==== Ошибки на уровне функций ====
    func_section_added = False
    for fname, (calls, errors, cfg, _tree) in sorted(func_entries.items()):
        status_parts = []
        if errors:
            status_parts.append("ERROR")
        if cfg is None:
            status_parts.append("NOT DEFINED")

        # Если вообще нет проблем — пропускаем
        if not status_parts and not errors:
            continue

        if not func_section_added:
            lines.append("\n=== FUNCTION ERRORS ===")
            func_section_added = True

        status_str = " / ".join(status_parts) if status_parts else "OK"
        lines.append(f"\nFunction: {fname}")
        lines.append(f"Status: {status_str}")
        if errors:
            lines.append("Errors:")
            for err in errors:
                lines.append(f"  - {err}")

    # ==== Функции, которые вызываются, но не объявлены ====
    defined_names = set(func_entries.keys())
    called_funcs = set()
    for calls, _errors, _cfg, _tree in func_entries.values():
        called_funcs |= set(calls)

    missing_funcs = sorted(called_funcs - defined_names)
    if missing_funcs:
        lines.append("\n=== REFERENCED BUT NOT DEFINED ===")
        for fname in missing_funcs:
            lines.append(f"  - {fname}")

    # Если вообще нечего писать — не создаём файл
    if not lines:
        return

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def calls_to_graphviz(result,
                      graph_name: str = "CallGraph",
                      node_shape: str = "box") -> Digraph:
    """
    result — это словарь, который возвращает analyze_files:
        { name: (calls: set[str], errors: list[str], cfg_or_none) }
    Строит граф вызовов между функциями.
    """
    dot = Digraph(name=graph_name)
    dot.attr("node", shape=node_shape)

    # Отфильтруем псевдо-узлы вида <file:...>
    defined_funcs = {
        name: data
        for name, data in result.items()
        if not name.startswith("<file:")
    }

    # Все вызываемые функции
    called_funcs = set()
    for _name, (calls, _errors, _cfg, tree) in defined_funcs.items():
        called_funcs |= set(calls)

    # Все имена функций: и объявленные, и только вызываемые
    all_func_names = set(defined_funcs.keys()) | called_funcs

    # Создаём вершины
    for fname in sorted(all_func_names):
        info = defined_funcs.get(fname)
        status = ""

        if info is not None:
            calls, errors, cfg, tree = info
            if errors:
                status = "ERROR"
            elif cfg is None:
                # Объявлена, но CFG нет
                status = "NOT DEFINED"
        else:
            # Функция только вызывается, но нигде не объявлена
            status = "NOT DEFINED"

        if status:
            label = f"{fname}\n{status}"
        else:
            label = fname

        dot.node(fname, label=label)

    # Добавляем рёбра: кто кого вызывает
    for caller, (calls, _errors, _cfg, tree) in defined_funcs.items():
        for callee in calls:
            # Узел для callee уже добавлен выше
            dot.edge(caller, callee)

    return dot


def render_call_graph(result,
                      filename: str = "call_graph",
                      fmt: str = "svg") -> None:
    """
    Рисует граф вызовов в файл (по умолчанию call_graph.svg).
    """
    dot = calls_to_graphviz(result)
    dot.render(filename, format=fmt, cleanup=True)
