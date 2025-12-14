from pathlib import Path

from get_parse_tree import get_tree_root
from tree_parser import write_tree_view_to_file, build_tree_view
from graph_parser import build_graph, render_cfg, get_func_name
from graphviz import Digraph  
from tree_parser import TreeViewNode

import argparse


def parse_cli():
    """
    Запуск с уже собранной библиотекой:
    python main.py path/to/parser.dll input1.txt [input2.txt ...] output_dir

    - Первый аргумент: путь к .dll/.so/.dylib
    - Далее: один или несколько входных файлов
    - Последний аргумент: выходная директория
    
    Имя языка автоматически извлекается из имени файла библиотеки.
    """
    p = argparse.ArgumentParser(description="Запуск tree-sitter парсера")

    p.add_argument(
        "lib_path",
        help="Путь к скомпилированной tree-sitter библиотеке (.so/.dll/.dylib)"
    )
    
    p.add_argument(
        "rest",
        nargs="+",
        help="Входные файлы и выходная директория: file1 [file2 ...] out_dir"
    )

    a = p.parse_args()

    # Проверка минимального количества аргументов
    if len(a.rest) < 2:
        p.error(
            "Необходимо указать хотя бы один входной файл и выходную директорию.\n"
            "Пример: python main.py path/to/lib.dll input1.c [input2.c ...] out_dir"
        )

    lib_path = a.lib_path
    file_paths = a.rest[:-1]
    out_dir = a.rest[-1]

    # Извлекаем имя языка из имени файла библиотеки
    stem = Path(lib_path).stem  # e.g. libfoo -> libfoo, foo -> foo
    lang_name = stem[3:] if stem.startswith("lib") else stem

    # Для совместимости с остальным кодом
    grammar_dir = None

    return grammar_dir, lang_name, file_paths, out_dir, lib_path


BUILTIN_TYPES = {
    'bool', 'byte', 'int', 'uint', 'long', 'ulong', 'char'
}
BUILTIN_FUNCTIONS = {
    'read_byte', 'send_byte', *BUILTIN_TYPES,
    'bool_to_byte', 'byte_to_bool',
    'byte_to_int', 'int_to_byte',
    'int_to_uint', 'uint_to_int',
    'int_to_long', 'long_to_int',
    'long_to_ulong', 'ulong_to_long'
}


def get_args_list_ordered(tree):
    """
    Извлекает аргументы функции в упорядоченном виде из дерева функции.
    
    tree — узел функции (funcDef).
    
    Возвращает:
      list[tuple[str, str | None]]: список кортежей (название_переменной, тип)
      Тип может быть None, если тип не задан или не удалось определить.
    """
    from types_generator import get_type_from_typeRef, normalize_type
    
    # Структура дерева: tree (funcDef) -> children[0] -> children[1] (funcSignature)
    # Это видно из get_func_returns_type: tree.children[0].children[1]
    if not tree.children or len(tree.children) < 1:
        return []
    
    func_def_wrapper = tree.children[0]
    if not func_def_wrapper.children or len(func_def_wrapper.children) < 2:
        return []
    
    func_signature = func_def_wrapper.children[1]
    
    # funcSignature -> [identifier, '(', list_argDef?, ')', (':' typeRef)?]
    arg_list_node = None
    for child in func_signature.children:
        if child.label == 'list<argDef>':
            arg_list_node = child
            break
    
    if not arg_list_node:
        return []
    
    args_list = []
    # arg_list_node.children содержит [argDef, ",", argDef, ",", argDef, ...]
    for node in arg_list_node.children:
        if node.label != 'argDef':
            continue
        
        # argDef: identifier (':' typeRef)?
        ident_node = None
        type_ref_node = None
        
        for child in node.children:
            if child.label == 'identifier':
                ident_node = child
            elif child.label == 'typeRef':
                type_ref_node = child
        
        if not ident_node:
            continue
        
        name = ident_node.children[0].label.strip('"')
        type_str = None
        
        if type_ref_node:
            type_str, _ = get_type_from_typeRef(type_ref_node)
            if type_str:
                type_str = normalize_type(type_str)
        
        args_list.append((name, type_str))
    
    return args_list


def get_vars_list_ordered(tree):
    """
    Извлекает локальные переменные функции в упорядоченном виде из дерева функции.
    
    tree — узел функции (funcDef).
    
    Возвращает:
      list[tuple[str, str | None]]: список кортежей (название_переменной, тип)
      Тип может быть None, если тип не задан или не удалось определить.
    """
    from types_generator import get_type_from_typeRef, normalize_type
    
    # Структура дерева: tree (funcDef) -> children[0] -> children[2] (body)
    if not tree.children or len(tree.children) < 1:
        return []
    
    func_def_wrapper = tree.children[0]
    if not func_def_wrapper.children or len(func_def_wrapper.children) < 3:
        return []
    
    body_node = func_def_wrapper.children[2]
    if not body_node or body_node.label != 'body':
        return []
    
    # body -> [var?, list<var_decl>, block]
    # Переменные находятся между первым элементом и последним (block)
    if len(body_node.children) < 2:
        return []
    
    var_decl_nodes = body_node.children[1:-1]  # Все между первым и последним
    
    vars_list = []
    i = 0
    nodes = list(var_decl_nodes)
    
    while i < len(nodes):
        node = nodes[i]
        
        # ожидаем list<identifier>
        if node.label != 'list<identifier>':
            i += 1
            continue
        
        # собираем имена идентификаторов a,b,c,...
        names = [
            ident.children[0].label.strip('"')
            for ident in node.children
            if ident.label == 'identifier'
        ]
        
        type_node = None
        type_str = None
        
        # смотрим, есть ли дальше ':' typeRef
        j = i + 1
        if j < len(nodes) and nodes[j].label == '":"':
            j += 1
            if j < len(nodes) and nodes[j].label == 'typeRef':
                type_node = nodes[j]
                type_str, _ = get_type_from_typeRef(type_node)
                if type_str:
                    type_str = normalize_type(type_str)
        
        # добавляем все переменные с их типом в порядке объявления
        for name in names:
            vars_list.append((name, type_str))
        
        # сдвигаем i к следующему объявлению: проматываем до ';'
        i = j
        while i < len(nodes) and nodes[i].label != '";"':
            i += 1
        if i < len(nodes) and nodes[i].label == '";"':
            i += 1
    
    return vars_list


def compare_treeviews(previous_subtree: TreeViewNode | None,
                      current_subtree: TreeViewNode | None) -> bool:
    """
    Сравнивает два поддерева TreeViewNode по label и структуре children.
    Поле `node` не учитывается.

    Возвращает True, если деревья эквивалентны, иначе False.
    """
    # Оба отсутствуют
    if previous_subtree is None and current_subtree is None:
        return True

    # Только одно из них отсутствует
    if previous_subtree is None or current_subtree is None:
        return False

    # Сравниваем метки
    if previous_subtree.label != current_subtree.label:
        return False

    # Сравниваем количество потомков
    if len(previous_subtree.children) != len(current_subtree.children):
        return False

    # Рекурсивно сравниваем детей по порядку
    for child_prev, child_curr in zip(previous_subtree.children, current_subtree.children):
        if not compare_treeviews(child_prev, child_curr):
            return False

    return True


def analyze_files(file_paths, lib_path, lang_name, grammar_dir, out_dir=None):
    """
    Обработка набора файлов.
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

        # Ошибки построения дерева
        if errors_tree_build:
            pseudo_name = f"<file:{input_file_name}>"
            data = results_internal.setdefault(
                pseudo_name, {"calls": set(), "errors": [], "cfg": None, "tree": view_root, "params": [], "vars": []}
            )
            for msg in errors_tree_build:
                data["errors"].append(f"{file_path}: {msg}")
            continue

        if tree_dir is not None:
            write_tree_view_to_file(view_root, str(tree_dir / input_file_name))

        # Обходим функции верхнего уровня
        for node in getattr(view_root, "children", []):
            func_name = get_func_name(node).strip().strip('"')
            if not func_name:
                continue

            data = results_internal.setdefault(
                func_name, {"calls": set(), "errors": [], "cfg": None, "tree": node, "params": [], "vars": []}
            )

            # ВАЖНО: сохраняем старое дерево ДО любых изменений
            previous_tree = data["tree"]
            current_tree = node

            # Проверка повторных объявлений / перегрузки
            if func_name in global_func_names:
                # Функция уже встречалась ранее
                if data["cfg"] is None and not data["errors"]:
                    # Функция существует логически, но пока "not defined"
                    # (нет CFG и нет ошибок) — можно попытаться принять
                    # новую реализацию при выполнении условия.

                    # previous_tree — дерево предыдущего объявления
                    # current_tree  — дерево текущего объявления
                    previous_subtree = previous_tree.children[0].children[1]
                    current_subtree = current_tree.children[0].children[1]

                    if not compare_treeviews(previous_subtree, current_subtree):
                        data["errors"].append(
                            f"Ошибка: попытка перегрузки функции '{func_name}' в файле '{file_path}'"
                        )
                        continue

                    # Условие прошло — принимаем новую реализацию:
                    data["tree"] = current_tree
                else:
                    # Уже есть реализация (cfg != None) или были ошибки —
                    # это точно перегрузка
                    data["errors"].append(
                        f"Ошибка: попытка перегрузки функции '{func_name}' в файле '{file_path}'"
                    )
                    continue
            else:
                # Первое появление имени функции
                global_func_names.add(func_name)
                data["tree"] = current_tree

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

            for err in errors_graph:
                data["errors"].append(f"{file_path}: {err}")

            for name in call_names:
                clean_name = name.strip().strip('"')
                if clean_name:
                    data["calls"].add(clean_name)

            cfg.remove_dangling_blocks()
            data["cfg"] = cfg
            
            # Извлекаем параметры функции в упорядоченном виде
            data["params"] = get_args_list_ordered(node)
            # Извлекаем локальные переменные функции в упорядоченном виде
            data["vars"] = get_vars_list_ordered(node)
            
            if graph_dir is not None:
                render_cfg(
                    cfg,
                    filename=str(graph_dir / f"{input_file_name}_{func_name}"),
                    fmt="svg",
                )
        
        # Для функций без CFG тоже извлекаем параметры и переменные
        if data.get("cfg") is None and data.get("tree") is not None:
            data["params"] = get_args_list_ordered(data["tree"])
            data["vars"] = get_vars_list_ordered(data["tree"])

    result = {
        name: (info["calls"], info["errors"], info["cfg"], info["tree"], info.get("params", []), info.get("vars", []))
        for name, info in results_internal.items()
    }
    return result

def write_errors_report(result, filename: str) -> bool:
    """
    Пишет человекочитаемый отчёт об ошибках в файл filename.
    Файл создаётся только если действительно есть какие-то ошибки/проблемы.
    
    Returns:
        bool: True, если ошибки были найдены и записаны в файл. False, если ошибок нет.
    """
    lines: list[str] = []

    # Разделим файл-уровень и функции
    file_entries = {
        name: (calls, errors, cfg, tree, params, vars)
        for name, (calls, errors, cfg, tree, params, vars) in result.items()
        if name.startswith("<file:")
    }
    func_entries = {
        name: (calls, errors, cfg, tree, params, vars)
        for name, (calls, errors, cfg, tree, params, vars) in result.items()
        if not name.startswith("<file:")
    }

    # ==== Ошибки на уровне файлов ====
    file_section_added = False
    for pseudo_name, (_calls, errors, _cfg, _tree, _params, _vars) in sorted(file_entries.items()):
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
    for fname, (calls, errors, cfg, _tree, args, vars) in sorted(func_entries.items()):
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
    for calls, _errors, _cfg, _tree, _, _ in func_entries.values():
        called_funcs |= set(calls)

    missing_funcs = sorted(called_funcs - defined_names - BUILTIN_FUNCTIONS)
    if missing_funcs:
        lines.append("\n=== REFERENCED BUT NOT DEFINED ===")
        for fname in missing_funcs:
            lines.append(f"  - {fname}")

    # Если вообще нечего писать — не создаём файл и возвращаем False
    if not lines:
        return False

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return True


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
    for _name, (calls, _errors, _cfg, tree, _params, _vars) in defined_funcs.items():
        called_funcs |= set(calls)

    # Все имена функций: и объявленные, и только вызываемые
    all_func_names = set(defined_funcs.keys()) | called_funcs

    # Создаём вершины
    for fname in sorted(all_func_names):
        info = defined_funcs.get(fname)
        status = ""

        if info is not None:
            calls, errors, cfg, tree, params, vars = info
            if errors:
                status = "ERROR"
            elif cfg is None:
                # Объявлена, но CFG нет
                status = "NOT DEFINED"
        else:
            # Функция только вызывается, но нигде не объявлена
            if fname in BUILTIN_FUNCTIONS:
                status = "BUILTIN"
            else:
                status = "NOT DEFINED"

        if status:
            label = f"{fname}\n{status}"
        else:
            label = fname

        dot.node(fname, label=label)

    # Добавляем рёбра: кто кого вызывает
    for caller, (calls, _errors, _cfg, tree, _params, _vars) in defined_funcs.items():
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
