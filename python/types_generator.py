def get_type_from_typeRef(type_ref_node):
    """
    type_ref_node — узел TreeViewNode(label='typeRef', ...)

    Возвращает кортеж:
      (type_str, error_msg)

    type_str:
      - строка вида "int", "MyType", "array[] of int" и т.п.
      - None, если тип не удалось корректно определить

    error_msg:
      - None, если ошибок нет
      - строка с описанием ошибки (например, про многомерный массив или custom)
    """
    kind = type_ref_node.children[0]

    # builtin: 'int', 'bool', 'string', ...
    if kind.label == 'builtin':
        token = kind.children[0]
        return token.label.strip('"'), None

    # custom: identifier — считаем ошибкой (классы не поддерживаются)
    if kind.label == 'custom':
        ident = next(c for c in kind.children if c.label == 'identifier')
        token = ident.children[0]
        type_name = token.label.strip('"')
        return type_name, "классы не поддерживаются"

    # иногда грамматика может давать сразу identifier
    if kind.label == 'identifier':
        token = kind.children[0]
        # это тоже пользовательский тип
        type_name = token.label.strip('"')
        return type_name, "классы не поддерживаются"

    # array: 'array' '[' (',')* ']' 'of' typeRef
    if kind.label == 'array':
        # проверяем количество запятых в квадратных скобках
        comma_count = sum(1 for c in kind.children if c.label == '\",\"')
        if comma_count > 0:
            return None, "многомерные массивы не поддерживаются"

        # находим вложенный typeRef (тип элементов массива)
        inner_type_ref = next(c for c in kind.children if c.label == 'typeRef')
        inner_str, inner_err = get_type_from_typeRef(inner_type_ref)
        if inner_err is not None:
            return None, inner_err

        return f"array[] of {inner_str}", None

    return None, f"неподдерживаемый вид typeRef: {kind.label}"


def get_dict_var(nodes):
    """
    nodes — это последовательность узлов:
    list<identifier> ':' typeRef? ';' list<identifier> ':' typeRef? ';' ...

    Возвращает:
      types_dict: { var_name: (type_str | None, type_ref_node | None) }
      errors:     список строк с описанием ошибок
    """
    nodes = list(nodes)
    i = 0
    types_dict: dict[str, tuple[str | None, object | None]] = {}
    errors: list[str] = []

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
        error_for_this_decl = None

        # смотрим, есть ли дальше ':' typeRef
        j = i + 1
        if j < len(nodes) and nodes[j].label == '":"':
            j += 1
            if j < len(nodes) and nodes[j].label == 'typeRef':
                type_node = nodes[j]
                type_str, type_err = get_type_from_typeRef(type_node)
                if type_err is not None:
                    error_for_this_decl = type_err
            else:
                error_for_this_decl = "ожидался typeRef после ':'"
        else:
            error_for_this_decl = "тип не задан"

        # записываем результат для всех имён
        for name in names:
            if name in types_dict:
                errors.append(f"повторное объявление переменной '{name}'")
                continue
            types_dict[name] = (type_str, type_node)

        if error_for_this_decl is not None:
            errors.append(
                f"{error_for_this_decl} (переменные: {', '.join(names)})"
            )

        # сдвигаем i к следующему объявлению: проматываем до ';'
        i = j
        while i < len(nodes) and nodes[i].label != '";"':
            i += 1
        if i < len(nodes) and nodes[i].label == '";"':
            i += 1

    return types_dict, errors


def get_func_returns_type(tree):
    """
    tree — узел функции.
    Возвращает:
      (type_str | None, type_ref_node | None, error_msg | None)
    """
    type_ref_node = tree.children[0].children[1].children[-1]

    # тип не задан (процедура)
    if type_ref_node.label != 'typeRef':
        return (None, None), None

    type_str, error = get_type_from_typeRef(type_ref_node)

    # если тип разобрать не удалось или он некорректен
    if error:
        # узел typeRef всё равно возвращаем, чтобы можно было повесить диагностику
        return (None, type_ref_node), error

    # всё ок: строка типа + сам узел typeRef
    return (type_str, type_ref_node), None


def get_args_dict(arg_nodes):
    """
    arg_nodes — список вида:
      [argDef, ",", argDef, ",", argDef, ...]
    Каждый argDef: identifier (':' typeRef)?

    Возвращает:
      args_dict: { arg_name: (type_str | None, type_ref_node | None) }
      errors:    список строк с ошибками
    """
    args_dict: dict[str, tuple[str | None, object | None]] = {}
    errors: list[str] = []

    # Берём только узлы argDef, запятые игнорируем
    for arg in arg_nodes:
        if arg.label != 'argDef':
            continue

        # 1. имя аргумента
        ident_node = next(c for c in arg.children if c.label == 'identifier')
        name = ident_node.children[0].label.strip('"')

        type_node = None
        type_str = None
        error_msg = None

        # 2. ищем ':' и typeRef внутри argDef
        has_colon = any(c.label == '":"'
                        for c in arg.children)
        if has_colon:
            type_child = [c for c in arg.children if c.label == 'typeRef']
            if type_child:
                type_node = type_child[0]
                type_str, type_err = get_type_from_typeRef(type_node)
                if type_err is not None:
                    error_msg = type_err
            else:
                error_msg = "ожидался typeRef после ':'"
        else:
            error_msg = "тип не задан"

        # 3. проверка на дубликат аргумента
        if name in args_dict:
            errors.append(f"повторное объявление аргумента '{name}'")
        else:
            args_dict[name] = (type_str, type_node)

        if error_msg is not None:
            errors.append(f"{error_msg} (аргумент: {name})")

    return args_dict, errors


def process_type(not_typed_data: dict):
    global_errors = {}
    funcs_returns = {}
    funcs_calls = {}
    funcs_vars = {}
    # Типы данных функций
    for func_name, (references, _, cfg, tree) in not_typed_data.items():
        # Тип данных, возвращаемый функцией
        func_type, error = get_func_returns_type(tree)
        if error:
            global_errors[func_name] = [error]
        funcs_returns[func_name] = func_type
        # Типы данных, в самих функциях
        types = tree.children[0].children[2].children[1:-1]
        dict_var, error = get_dict_var(types)
        if error:
            global_errors[func_name] = global_errors.get(func_name, []) + error
        funcs_vars[func_name] = dict_var
        # Типы данных, передаваемые в функции
        arg_nodes = tree.children[0].children[1].children[2].children
        func_call, error = get_args_dict(arg_nodes)
        if error:
            global_errors[func_name] = global_errors.get(func_name, []) + error
        funcs_calls[func_name] = func_call
        
    # Если есть ошибки, вернем
    if global_errors:
        return None, global_errors
    
    # Типы данных в листьях
    for func_name, (references, _, cfg, tree) in not_typed_data.items():
        for block in cfg.blocks.values():
            pass
            
        
    return None, global_errors # TODO