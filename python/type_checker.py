"""
Модуль для строгой проверки типов (как в Go).

Операции можно выполнять только над строго одинаковыми типами данных.
При конфликте типов сохраняется дерево и описание ошибки.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from tree_parser import TreeViewNode, tree_view_to_str
import re


# Числовые типы (целочисленные)
INTEGER_TYPES = {'byte', 'int', 'uint', 'long', 'ulong'}

# Все числовые типы
NUMERIC_TYPES = INTEGER_TYPES

# Специальный тип для нетипизированных числовых констант (как в Go)
# Автоматически приводится к нужному числовому типу
UNTYPED_INT = '_untyped_int'

# Типы, над которыми можно выполнять арифметические операции
ARITHMETIC_TYPES = NUMERIC_TYPES | {UNTYPED_INT}

# Типы, над которыми можно выполнять битовые операции
BITWISE_TYPES = INTEGER_TYPES | {UNTYPED_INT}

# Типы, которые можно сравнивать
COMPARABLE_TYPES = NUMERIC_TYPES | {'char', 'bool', 'string', UNTYPED_INT}

# Операторы по категориям
ARITHMETIC_OPS = {'+', '-', '*', '/', '%'}
BITWISE_OPS = {'|', '&', '^', '<<', '>>'}
LOGICAL_OPS = {'||', '&&'}
COMPARISON_OPS = {'=', '!=', '>', '>=', '<', '<='}
UNARY_LOGICAL_OPS = {'!'}
UNARY_BITWISE_OPS = {'~'}


@dataclass
class TypeCheckError:
    """Ошибка проверки типов."""
    message: str
    tree: TreeViewNode  # Узел, где произошла ошибка
    tree_str: str  # Строковое представление дерева


@dataclass
class TypeCheckResult:
    """Результат проверки типов для одной функции."""
    func_name: str
    errors: List[TypeCheckError] = field(default_factory=list)
    # Типизированные блоки: block_id -> список (tree, type_str | None)
    typed_blocks: Dict[int, List[Tuple[TreeViewNode, Optional[str]]]] = field(default_factory=dict)


def get_literal_type(lit_type: str) -> str:
    """
    Определяет тип литерала по его виду.
    
    Числовые литералы (dec, hex, bits) возвращают UNTYPED_INT -
    специальный тип, который автоматически приводится к нужному
    числовому типу при использовании в операциях.
    
    dec -> _untyped_int (автоматически приводится к int/uint/long/etc)
    hex -> _untyped_int
    bits -> _untyped_int
    bool -> bool
    str -> string
    char -> char
    """
    mapping = {
        'dec': UNTYPED_INT,
        'bool': 'bool',
        'str': 'string',
        'char': 'char',
        'hex': UNTYPED_INT,
        'bits': UNTYPED_INT,
    }
    return mapping.get(lit_type, 'unknown')


def parse_const_literal(label: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Парсит const(type(value)) и возвращает (lit_type, value).
    
    Пример: const(dec(123)) -> ('dec', '123')
    """
    match = re.match(r'const\((\w+)\((.+)\)\)', label)
    if match:
        return match.group(1), match.group(2)
    return None, None


def parse_load_name(label: str) -> Optional[str]:
    """
    Парсит load(name) или load(name[]) и возвращает имя переменной.
    
    load(x) -> 'x'
    load(arr[]) -> 'arr[]'
    """
    match = re.match(r'load\((.+)\)', label)
    if match:
        return match.group(1)
    return None


def parse_store_name(label: str) -> Optional[str]:
    """
    Парсит store(name) и возвращает имя переменной.
    
    store(x) -> 'x'
    """
    match = re.match(r'store\((.+)\)', label)
    if match:
        return match.group(1)
    return None


def parse_store_at_name(label: str) -> Optional[str]:
    """
    Парсит store_at(name) и возвращает имя массива.
    
    store_at(arr) -> 'arr'
    """
    match = re.match(r'store_at\((.+)\)', label)
    if match:
        return match.group(1)
    return None


def parse_call_name(label: str) -> Optional[str]:
    """
    Парсит call(func_name) и возвращает имя функции.
    
    call(foo) -> 'foo'
    """
    match = re.match(r'call\((.+)\)', label)
    if match:
        return match.group(1)
    return None


def get_array_element_type(array_type: str) -> Optional[str]:
    """
    Извлекает тип элемента массива.
    
    array[] of int -> int
    array[] of char -> char
    """
    match = re.match(r'array\[\]\s+of\s+(.+)', array_type)
    if match:
        return match.group(1)
    return None


def is_array_type(type_str: str) -> bool:
    """Проверяет, является ли тип массивом."""
    return type_str is not None and type_str.startswith('array[]')


def is_untyped_int(type_str: Optional[str]) -> bool:
    """Проверяет, является ли тип нетипизированной числовой константой."""
    return type_str == UNTYPED_INT


def unify_types(left_type: Optional[str], right_type: Optional[str]) -> Optional[str]:
    """
    Унифицирует два типа для бинарной операции.
    
    Если один из типов - UNTYPED_INT, а другой - конкретный числовой тип,
    возвращает конкретный тип (литерал приводится к типу переменной).
    
    Если оба - UNTYPED_INT, возвращает 'int' по умолчанию.
    
    Если типы одинаковые, возвращает этот тип.
    
    Иначе возвращает None (типы несовместимы).
    """
    if left_type is None or right_type is None:
        return left_type or right_type
    
    # Оба untyped -> int по умолчанию
    if is_untyped_int(left_type) and is_untyped_int(right_type):
        return 'int'
    
    # Левый untyped, правый конкретный числовой -> правый
    if is_untyped_int(left_type) and right_type in NUMERIC_TYPES:
        return right_type
    
    # Правый untyped, левый конкретный числовой -> левый
    if is_untyped_int(right_type) and left_type in NUMERIC_TYPES:
        return left_type
    
    # Оба конкретные и одинаковые
    if left_type == right_type:
        return left_type
    
    # Типы несовместимы
    return None


def resolve_type(type_str: Optional[str]) -> Optional[str]:
    """
    Разрешает тип для отображения.
    Если тип - UNTYPED_INT, возвращает 'int'.
    """
    if type_str == UNTYPED_INT:
        return 'int'
    return type_str


class TypeChecker:
    """
    Класс для проверки типов в AST.

    Реализует строгую типизацию как в Go:
    - uint + int -> ОШИБКА
    - операции только над одинаковыми типами
    """

    def __init__(
        self,
        funcs_vars: Dict[str, Dict[str, Tuple[Optional[str], object]]],
        funcs_calls: Dict[str, Dict[str, Tuple[Optional[str], object]]],
        funcs_returns: Dict[str, Tuple[Optional[str], object]],
    ):
        """
        funcs_vars: { func_name: { var_name: (type_str, type_ref_node) } }
        funcs_calls: { func_name: { arg_name: (type_str, type_ref_node) } }
        funcs_returns: { func_name: (return_type_str, type_ref_node) }
        """
        self.funcs_vars = funcs_vars
        self.funcs_calls = funcs_calls
        self.funcs_returns = funcs_returns

        # Текущий контекст функции
        self.current_func: Optional[str] = None
        self.current_vars: Dict[str, Tuple[Optional[str], object]] = {}
        self.current_args: Dict[str, Tuple[Optional[str], object]] = {}
        
        # Кэш разрешённых типов узлов (id(node) -> resolved_type)
        # Используется для отображения конкретных типов вместо UNTYPED_INT
        self.resolved_types: Dict[int, str] = {}

    def set_context(self, func_name: str):
        """Устанавливает контекст текущей функции."""
        self.current_func = func_name
        self.current_vars = self.funcs_vars.get(func_name, {})
        self.current_args = self.funcs_calls.get(func_name, {})
        # Очищаем кэш при смене контекста
        self.resolved_types.clear()
    
    def set_resolved_type(self, node: TreeViewNode, type_str: str):
        """Сохраняет разрешённый тип для узла и записывает в node.type."""
        if type_str is not None:
            self.resolved_types[id(node)] = type_str
            # Также записываем в сам узел
            node.type = type_str
    
    def get_resolved_type(self, node: TreeViewNode) -> Optional[str]:
        """Получает разрешённый тип для узла."""
        return self.resolved_types.get(id(node))
    
    def assign_types(self, node: TreeViewNode) -> Tuple[Optional[str], List[TypeCheckError]]:
        """
        Выводит тип для узла и записывает его в node.type.
        Рекурсивно обрабатывает всех потомков.
        
        Возвращает (type_str, errors).
        """
        # Выводим тип (это рекурсивно обработает всех потомков)
        inferred_type, errors = self.infer_type(node)
        
        # Проверяем, был ли разрешённый тип (из контекста)
        resolved = self.get_resolved_type(node)
        if resolved is not None:
            node.type = resolved
        elif inferred_type is not None:
            # Разрешаем UNTYPED_INT в int для отображения
            node.type = resolve_type(inferred_type)
        
        # Рекурсивно присваиваем типы потомкам (если они ещё не обработаны)
        for child in node.children:
            if child.type is None:
                self._assign_type_to_child(child)
        
        return node.type, errors
    
    def _assign_type_to_child(self, node: TreeViewNode):
        """Присваивает тип дочернему узлу, если он ещё не присвоен."""
        # Проверяем кэш разрешённых типов
        resolved = self.get_resolved_type(node)
        if resolved is not None:
            node.type = resolved
            return
        
        # Выводим тип
        inferred_type, _ = self.infer_type(node)
        if inferred_type is not None:
            node.type = resolve_type(inferred_type)
        
        # Рекурсивно для потомков
        for child in node.children:
            if child.type is None:
                self._assign_type_to_child(child)
    
    def get_variable_type(self, var_name: str) -> Optional[str]:
        """
        Получает тип переменной из локальных переменных или аргументов.
        """
        # Проверяем массив (var_name[])
        if var_name.endswith('[]'):
            base_name = var_name[:-2]
            type_info = self.current_vars.get(base_name) or self.current_args.get(base_name)
            if type_info:
                return type_info[0]
            return None
        
        # Обычная переменная
        type_info = self.current_vars.get(var_name) or self.current_args.get(var_name)
        if type_info:
            return type_info[0]
        return None
    
    def get_function_return_type(self, func_name: str) -> Optional[str]:
        """Получает тип возвращаемого значения функции."""
        type_info = self.funcs_returns.get(func_name)
        if type_info:
            return type_info[0]
        return None
    
    def get_function_args(self, func_name: str) -> Dict[str, Tuple[Optional[str], object]]:
        """Получает словарь аргументов функции."""
        return self.funcs_calls.get(func_name, {})
    
    def infer_type(self, node: TreeViewNode) -> Tuple[Optional[str], List[TypeCheckError]]:
        """
        Выводит тип для узла AST.
        
        Возвращает (type_str, errors).
        """
        errors: List[TypeCheckError] = []
        label = node.label
        
        # 1. Константа: const(type(value))
        if label.startswith('const('):
            lit_type, value = parse_const_literal(label)
            if lit_type:
                return get_literal_type(lit_type), errors
            errors.append(TypeCheckError(
                message=f"Не удалось распознать константу: {label}",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            return None, errors
        
        # 2. Загрузка переменной: load(name) или load(name[])
        if label.startswith('load('):
            var_name = parse_load_name(label)
            if var_name:
                var_type = self.get_variable_type(var_name)
                if var_type is None:
                    errors.append(TypeCheckError(
                        message=f"Неизвестная переменная: {var_name}",
                        tree=node,
                        tree_str=tree_view_to_str(node)
                    ))
                return var_type, errors
            errors.append(TypeCheckError(
                message=f"Не удалось распознать load: {label}",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            return None, errors
        
        # 3. Вызов функции: call(func_name)
        if label.startswith('call('):
            func_name = parse_call_name(label)
            if func_name:
                call_errors = self._check_call(node, func_name)
                errors.extend(call_errors)
                return_type = self.get_function_return_type(func_name)
                return return_type, errors
            errors.append(TypeCheckError(
                message=f"Не удалось распознать вызов функции: {label}",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            return None, errors
        
        # 4. Сохранение: store(name)
        if label.startswith('store(') and not label.startswith('store_at('):
            var_name = parse_store_name(label)
            if var_name and node.children:
                var_type = self.get_variable_type(var_name)
                if var_type is None:
                    errors.append(TypeCheckError(
                        message=f"Неизвестная переменная для записи: {var_name}",
                        tree=node,
                        tree_str=tree_view_to_str(node)
                    ))
                    return None, errors

                # Проверяем тип правой части
                rhs_type, rhs_errors = self.infer_type(node.children[0])
                errors.extend(rhs_errors)

                # UNTYPED_INT автоматически приводится к числовому типу переменной
                if rhs_type is not None:
                    if is_untyped_int(rhs_type) and var_type in NUMERIC_TYPES:
                        # Литерал приводится к типу переменной - сохраняем разрешённый тип
                        self.set_resolved_type(node.children[0], var_type)
                    elif var_type != rhs_type:
                        errors.append(TypeCheckError(
                            message=f"Несоответствие типов при присваивании: "
                                    f"переменная '{var_name}' имеет тип '{var_type}', "
                                    f"а выражение имеет тип '{resolve_type(rhs_type)}'",
                            tree=node,
                            tree_str=tree_view_to_str(node)
                        ))

                # store возвращает тип переменной (для цепочек)
                return var_type, errors
            return None, errors
        
        # 4.1. Сохранение в массив: store_at(name) [idx1, idx2, ..., value]
        if label.startswith('store_at('):
            arr_name = parse_store_at_name(label)
            if arr_name and node.children:
                # Получаем тип массива
                arr_type = self.get_variable_type(arr_name)
                if arr_type is None:
                    errors.append(TypeCheckError(
                        message=f"Неизвестный массив для записи: {arr_name}",
                        tree=node,
                        tree_str=tree_view_to_str(node)
                    ))
                    return None, errors
                
                if not is_array_type(arr_type):
                    errors.append(TypeCheckError(
                        message=f"Переменная '{arr_name}' не является массивом: '{arr_type}'",
                        tree=node,
                        tree_str=tree_view_to_str(node)
                    ))
                    return None, errors
                
                element_type = get_array_element_type(arr_type)
                
                # Дети: [idx1, idx2, ..., value]
                # Последний ребёнок - значение, остальные - индексы
                if len(node.children) < 2:
                    errors.append(TypeCheckError(
                        message=f"store_at требует минимум индекс и значение",
                        tree=node,
                        tree_str=tree_view_to_str(node)
                    ))
                    return None, errors
                
                indices = node.children[:-1]
                value_node = node.children[-1]
                
                # Проверяем типы индексов (UNTYPED_INT приводится к int)
                for idx_node in indices:
                    idx_type, idx_errors = self.infer_type(idx_node)
                    errors.extend(idx_errors)

                    if idx_type is not None and idx_type != 'int' and not is_untyped_int(idx_type):
                        errors.append(TypeCheckError(
                            message=f"Индекс массива должен иметь тип 'int', а не '{resolve_type(idx_type)}'",
                            tree=idx_node,
                            tree_str=tree_view_to_str(idx_node)
                        ))

                # Проверяем тип значения
                value_type, value_errors = self.infer_type(value_node)
                errors.extend(value_errors)

                if value_type is not None and element_type is not None:
                    # UNTYPED_INT автоматически приводится к числовому типу элемента
                    if is_untyped_int(value_type) and element_type in NUMERIC_TYPES:
                        # Литерал приводится к типу элемента - сохраняем разрешённый тип
                        self.set_resolved_type(value_node, element_type)
                    elif value_type != element_type:
                        errors.append(TypeCheckError(
                            message=f"Несоответствие типов при присваивании в массив: "
                                    f"элемент массива '{arr_name}' имеет тип '{element_type}', "
                                    f"а выражение имеет тип '{resolve_type(value_type)}'",
                            tree=node,
                            tree_str=tree_view_to_str(node)
                        ))

                # store_at возвращает тип элемента массива
                return element_type, errors
            return None, errors
        
        # 5. Индексация: index
        if label == 'index':
            if len(node.children) != 2:
                errors.append(TypeCheckError(
                    message=f"Некорректная индексация: ожидается 2 потомка",
                    tree=node,
                    tree_str=tree_view_to_str(node)
                ))
                return None, errors

            base_node, index_node = node.children
            base_type, base_errors = self.infer_type(base_node)
            errors.extend(base_errors)

            index_type, index_errors = self.infer_type(index_node)
            errors.extend(index_errors)

            # Индекс должен быть int (UNTYPED_INT автоматически приводится к int)
            if index_type is not None and index_type != 'int' and not is_untyped_int(index_type):
                errors.append(TypeCheckError(
                    message=f"Индекс массива должен иметь тип 'int', а не '{resolve_type(index_type)}'",
                    tree=index_node,
                    tree_str=tree_view_to_str(index_node)
                ))
            
            # База должна быть массивом
            if base_type is not None:
                if not is_array_type(base_type):
                    errors.append(TypeCheckError(
                        message=f"Индексация применима только к массивам, а не к '{base_type}'",
                        tree=base_node,
                        tree_str=tree_view_to_str(base_node)
                    ))
                    return None, errors
                
                element_type = get_array_element_type(base_type)
                return element_type, errors
            
            return None, errors
        
        # 6. Бинарные операторы
        if label in ARITHMETIC_OPS:
            return self._check_binary_arithmetic(node, label, errors)
        
        if label in BITWISE_OPS:
            return self._check_binary_bitwise(node, label, errors)
        
        if label in LOGICAL_OPS:
            return self._check_binary_logical(node, label, errors)
        
        if label in COMPARISON_OPS:
            return self._check_comparison(node, label, errors)
        
        # 7. Унарные операторы
        if label in UNARY_LOGICAL_OPS:
            return self._check_unary_logical(node, label, errors)
        
        if label in UNARY_BITWISE_OPS:
            return self._check_unary_bitwise(node, label, errors)
        
        # Неизвестный узел
        errors.append(TypeCheckError(
            message=f"Неизвестный тип узла: {label}",
            tree=node,
            tree_str=tree_view_to_str(node)
        ))
        return None, errors
    
    def _check_call(self, node: TreeViewNode, func_name: str) -> List[TypeCheckError]:
        """Проверяет вызов функции: количество и типы аргументов."""
        errors: List[TypeCheckError] = []
        
        # Проверяем, что функция существует
        if func_name not in self.funcs_returns:
            errors.append(TypeCheckError(
                message=f"Вызов неизвестной функции: '{func_name}'",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            # Всё равно проверяем типы аргументов
            for arg_node in node.children:
                _, arg_errors = self.infer_type(arg_node)
                errors.extend(arg_errors)
            return errors
        
        # Получаем ожидаемые аргументы функции
        expected_args = self.get_function_args(func_name)
        expected_arg_list = list(expected_args.items())  # [(arg_name, (type, node)), ...]
        
        # Фактические аргументы - дети узла call
        actual_args = node.children
        
        # Проверяем количество аргументов
        if len(actual_args) != len(expected_arg_list):
            errors.append(TypeCheckError(
                message=f"Функция '{func_name}' ожидает {len(expected_arg_list)} "
                        f"аргумент(ов), но передано {len(actual_args)}",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            # Проверяем типы для минимального количества
            check_count = min(len(actual_args), len(expected_arg_list))
        else:
            check_count = len(actual_args)
        
        # Проверяем типы аргументов
        for i in range(check_count):
            actual_node = actual_args[i]
            arg_name, (expected_type, _) = expected_arg_list[i]

            actual_type, arg_errors = self.infer_type(actual_node)
            errors.extend(arg_errors)

            if actual_type is not None and expected_type is not None:
                # UNTYPED_INT автоматически приводится к числовому типу аргумента
                if is_untyped_int(actual_type) and expected_type in NUMERIC_TYPES:
                    # Литерал приводится к типу аргумента - сохраняем разрешённый тип
                    self.set_resolved_type(actual_node, expected_type)
                elif actual_type != expected_type:
                    errors.append(TypeCheckError(
                        message=f"Несоответствие типа аргумента '{arg_name}' "
                                f"в вызове '{func_name}': ожидается '{expected_type}', "
                                f"но передан '{resolve_type(actual_type)}'",
                        tree=actual_node,
                        tree_str=tree_view_to_str(actual_node)
                    ))

        return errors
    
    def infer_and_resolve_type(
        self,
        node: TreeViewNode,
        type_hint: Optional[str] = None
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """
        Выводит тип для узла AST с учётом подсказки типа из контекста.
        
        Если узел имеет UNTYPED_INT и передана подсказка числового типа,
        используется подсказка. Разрешённый тип сохраняется в кэш.
        
        Также рекурсивно пропагирует типы к дочерним узлам.
        """
        # Сначала получаем базовый тип
        base_type, errors = self.infer_type(node)
        
        # Определяем финальный тип
        if is_untyped_int(base_type) and type_hint is not None and type_hint in NUMERIC_TYPES:
            resolved = type_hint
        else:
            resolved = resolve_type(base_type)
        
        # Сохраняем в кэш
        self.set_resolved_type(node, resolved)
        
        # Пропагируем тип к дочерним узлам
        self._propagate_types_to_children(node, resolved)
        
        return resolved, errors
    
    def _propagate_types_to_children(self, node: TreeViewNode, parent_type: Optional[str]):
        """
        Пропагирует типы к дочерним узлам.
        
        Для бинарных операций и присваиваний передаёт тип контекста
        дочерним узлам с UNTYPED_INT.
        """
        if not node.children:
            return
        
        label = node.label
        
        # Для store - пропагируем тип переменной к правой части
        if label.startswith('store(') and not label.startswith('store_at('):
            var_name = parse_store_name(label)
            if var_name:
                var_type = self.get_variable_type(var_name)
                if var_type and node.children:
                    self._resolve_subtree(node.children[0], var_type)
        
        # Для store_at - пропагируем тип элемента массива
        elif label.startswith('store_at('):
            arr_name = parse_store_at_name(label)
            if arr_name:
                arr_type = self.get_variable_type(arr_name)
                if arr_type and is_array_type(arr_type):
                    element_type = get_array_element_type(arr_type)
                    if element_type and len(node.children) >= 2:
                        # Индексы - int, значение - тип элемента
                        for idx_node in node.children[:-1]:
                            self._resolve_subtree(idx_node, 'int')
                        self._resolve_subtree(node.children[-1], element_type)
        
        # Для бинарных операций - пропагируем унифицированный тип
        elif label in ARITHMETIC_OPS | BITWISE_OPS | COMPARISON_OPS:
            if len(node.children) == 2:
                left_node, right_node = node.children
                
                # Получаем типы операндов
                left_type, _ = self.infer_type(left_node)
                right_type, _ = self.infer_type(right_node)
                
                # Унифицируем
                unified = unify_types(left_type, right_type)
                if unified:
                    self._resolve_subtree(left_node, unified)
                    self._resolve_subtree(right_node, unified)
        
        # Для call - пропагируем типы аргументов
        elif label.startswith('call('):
            func_name = parse_call_name(label)
            if func_name:
                expected_args = self.get_function_args(func_name)
                expected_arg_list = list(expected_args.items())
                for i, child in enumerate(node.children):
                    if i < len(expected_arg_list):
                        _, (expected_type, _) = expected_arg_list[i]
                        if expected_type:
                            self._resolve_subtree(child, expected_type)
        
        # Для index - индекс должен быть int
        elif label == 'index':
            if len(node.children) == 2:
                base_node, index_node = node.children
                self._resolve_subtree(index_node, 'int')
                # Для базы рекурсивно вызываем
                self._propagate_types_to_children(base_node, None)
        
        # Для унарных операций
        elif label in UNARY_BITWISE_OPS:
            if node.children:
                # Унарный ~ сохраняет тип операнда
                self._resolve_subtree(node.children[0], parent_type)
        
        elif label in UNARY_LOGICAL_OPS:
            if node.children:
                self._resolve_subtree(node.children[0], 'bool')
    
    def _resolve_subtree(self, node: TreeViewNode, type_hint: Optional[str]):
        """
        Рекурсивно разрешает типы в поддереве с учётом подсказки.
        """
        base_type, _ = self.infer_type(node)
        
        # Определяем финальный тип
        if is_untyped_int(base_type) and type_hint is not None and type_hint in NUMERIC_TYPES:
            resolved = type_hint
        else:
            resolved = resolve_type(base_type)
        
        # Сохраняем в кэш
        self.set_resolved_type(node, resolved)
        
        # Рекурсивно обрабатываем детей
        self._propagate_types_to_children(node, resolved)

    def _check_binary_op(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
        allowed_types: Set[str],
        type_category: str,
    ) -> Tuple[Optional[str], Optional[str], List[TypeCheckError]]:
        """
        Общая проверка бинарного оператора.
        Возвращает (unified_type, unified_type, errors).
        
        Поддерживает автоматическое приведение UNTYPED_INT к конкретному
        числовому типу.
        """
        if len(node.children) != 2:
            errors.append(TypeCheckError(
                message=f"Оператор '{op}' требует 2 операнда",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            return None, None, errors

        left_node, right_node = node.children

        left_type, left_errors = self.infer_type(left_node)
        errors.extend(left_errors)

        right_type, right_errors = self.infer_type(right_node)
        errors.extend(right_errors)

        # Проверяем, что типы разрешены (учитываем UNTYPED_INT)
        if left_type is not None and left_type not in allowed_types:
            errors.append(TypeCheckError(
                message=f"Оператор '{op}' не применим к типу '{resolve_type(left_type)}' "
                        f"(ожидается {type_category})",
                tree=left_node,
                tree_str=tree_view_to_str(left_node)
            ))

        if right_type is not None and right_type not in allowed_types:
            errors.append(TypeCheckError(
                message=f"Оператор '{op}' не применим к типу '{resolve_type(right_type)}' "
                        f"(ожидается {type_category})",
                tree=right_node,
                tree_str=tree_view_to_str(right_node)
            ))

        # Унифицируем типы (UNTYPED_INT автоматически приводится)
        if left_type is not None and right_type is not None:
            unified = unify_types(left_type, right_type)
            if unified is None:
                # Типы несовместимы
                errors.append(TypeCheckError(
                    message=f"Несоответствие типов операндов для '{op}': "
                            f"'{resolve_type(left_type)}' и '{resolve_type(right_type)}' "
                            f"(строгая типизация: типы должны совпадать)",
                    tree=node,
                    tree_str=tree_view_to_str(node)
                ))
            else:
                # Сохраняем разрешённые типы для дочерних узлов
                if is_untyped_int(left_type):
                    self.set_resolved_type(left_node, unified)
                if is_untyped_int(right_type):
                    self.set_resolved_type(right_node, unified)
                # Возвращаем унифицированный тип
                return unified, unified, errors

        return left_type, right_type, errors
    
    def _check_binary_arithmetic(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """Проверка арифметического оператора."""
        left_type, right_type, errors = self._check_binary_op(
            node, op, errors, ARITHMETIC_TYPES, "числовой тип"
        )

        # _check_binary_op уже унифицировал типы
        # left_type и right_type теперь одинаковые (или None)
        result_type = left_type or right_type
        # Разрешаем UNTYPED_INT в int
        return resolve_type(result_type), errors
    
    def _check_binary_bitwise(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """Проверка битового оператора."""
        left_type, right_type, errors = self._check_binary_op(
            node, op, errors, BITWISE_TYPES, "целочисленный тип"
        )

        # _check_binary_op уже унифицировал типы
        result_type = left_type or right_type
        return resolve_type(result_type), errors
    
    def _check_binary_logical(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """Проверка логического оператора."""
        left_type, right_type, errors = self._check_binary_op(
            node, op, errors, {'bool'}, "bool"
        )
        
        # Логические операторы всегда возвращают bool
        return 'bool', errors
    
    def _check_comparison(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """Проверка оператора сравнения."""
        left_type, right_type, errors = self._check_binary_op(
            node, op, errors, COMPARABLE_TYPES, "сравнимый тип"
        )
        
        # Операторы сравнения всегда возвращают bool
        return 'bool', errors
    
    def _check_unary_logical(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """Проверка унарного логического оператора (!)."""
        if len(node.children) != 1:
            errors.append(TypeCheckError(
                message=f"Унарный оператор '{op}' требует 1 операнд",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            return None, errors
        
        operand_type, operand_errors = self.infer_type(node.children[0])
        errors.extend(operand_errors)
        
        if operand_type is not None and operand_type != 'bool':
            errors.append(TypeCheckError(
                message=f"Оператор '{op}' применим только к типу 'bool', "
                        f"а не к '{operand_type}'",
                tree=node.children[0],
                tree_str=tree_view_to_str(node.children[0])
            ))
        
        return 'bool', errors
    
    def _check_unary_bitwise(
        self,
        node: TreeViewNode,
        op: str,
        errors: List[TypeCheckError],
    ) -> Tuple[Optional[str], List[TypeCheckError]]:
        """Проверка унарного битового оператора (~)."""
        if len(node.children) != 1:
            errors.append(TypeCheckError(
                message=f"Унарный оператор '{op}' требует 1 операнд",
                tree=node,
                tree_str=tree_view_to_str(node)
            ))
            return None, errors
        
        operand_type, operand_errors = self.infer_type(node.children[0])
        errors.extend(operand_errors)
        
        if operand_type is not None and operand_type not in BITWISE_TYPES:
            errors.append(TypeCheckError(
                message=f"Оператор '{op}' применим только к целочисленным типам, "
                        f"а не к '{operand_type}'",
                tree=node.children[0],
                tree_str=tree_view_to_str(node.children[0])
            ))
        
        return operand_type, errors


def check_types_in_cfg(
    cfg,  # CFG object
    func_name: str,
    checker: TypeChecker,
) -> TypeCheckResult:
    """
    Проверяет типы во всех блоках CFG функции.
    Присваивает типы узлам через node.type.
    """
    result = TypeCheckResult(func_name=func_name)
    checker.set_context(func_name)

    for block_id, block in cfg.blocks.items():
        if block.tree is not None:
            # Присваиваем типы узлам дерева
            node_type, errors = checker.assign_types(block.tree)
            result.errors.extend(errors)
            result.typed_blocks[block_id] = [(block.tree, node_type)]

    return result


def check_all_functions(
    not_typed_data: dict,
    funcs_vars: Dict[str, Dict[str, Tuple[Optional[str], object]]],
    funcs_calls: Dict[str, Dict[str, Tuple[Optional[str], object]]],
    funcs_returns: Dict[str, Tuple[Optional[str], object]],
) -> Dict[str, TypeCheckResult]:
    """
    Проверяет типы во всех функциях и присваивает типы узлам.

    not_typed_data: { func_name: (references, _, cfg, tree) }

    Возвращает: { func_name: TypeCheckResult }
    
    После вызова этой функции, в not_typed_data узлы будут иметь
    заполненные поля node.type.
    """
    checker = TypeChecker(funcs_vars, funcs_calls, funcs_returns)
    results: Dict[str, TypeCheckResult] = {}
    
    for func_name, (references, _, cfg, tree) in not_typed_data.items():
        # Пропускаем псевдо-узлы файлов и функции без CFG
        if func_name.startswith('<file:'):
            continue
        if cfg is None:
            continue
        
        result = check_types_in_cfg(cfg, func_name, checker)
        results[func_name] = result
    
    return results


def format_type_errors(results: Dict[str, TypeCheckResult]) -> Dict[str, List[str]]:
    """
    Форматирует ошибки типов в читаемый формат.
    
    Возвращает: { func_name: [error_messages] }
    """
    formatted: Dict[str, List[str]] = {}
    
    for func_name, result in results.items():
        if result.errors:
            formatted[func_name] = [
                f"{err.message}\n  Дерево:\n{err.tree_str}"
                for err in result.errors
            ]
    
    return formatted


#######################################################################
# TYPED TREE RENDERING
#######################################################################

def typed_tree_view_to_str(node: TreeViewNode) -> str:
    """
    Возвращает строковое представление дерева с типами в формате,
    аналогичном tree_view_to_str.
    
    Читает типы из node.type (должны быть предварительно заполнены).
    """
    VBAR, SPACE, TEE, ELBOW = ("│   ", "    ", "├── ", "└── ")

    lines: List[str] = []

    def walk(n: TreeViewNode, anc_has_next: List[bool], is_last: bool) -> None:
        # Формируем префикс
        if not anc_has_next:
            prefix = ""
        else:
            base = "".join(VBAR if has_next else SPACE for has_next in anc_has_next)
            prefix = base + (ELBOW if is_last else TEE)

        # Добавляем тип из node.type
        type_str = f" : {n.type}" if n.type else ""
        lines.append(f"{prefix}{n.label}{type_str}")

        # Рекурсивно обходим детей
        child_anc = [*anc_has_next, not is_last]
        for i, ch in enumerate(n.children):
            walk(ch, child_anc, i == len(n.children) - 1)

    walk(node, [], True)
    return "\n".join(lines)


def render_typed_cfg(
    cfg,  # CFG object с типизированными деревьями
    filename: str,
    fmt: str = "svg"
) -> None:
    """
    Рендерит CFG с типизированными деревьями.
    
    Типы должны быть уже заполнены в node.type.
    """
    from graphviz import Digraph
    
    dot = Digraph(name="TypedCFG")
    dot.attr("node", shape="box")
    
    for block in cfg.blocks.values():
        if block.tree is not None:
            # Создаём типизированное представление дерева (читает node.type)
            typed_label = typed_tree_view_to_str(block.tree)
            # Escape для graphviz
            lines = typed_label.splitlines()
            node_label = ""
            for line in lines:
                # Экранируем специальные символы
                escaped = line.replace("\\", "\\\\").replace('"', '\\"')
                node_label += escaped + "\\l"
        else:
            node_label = block.label
        
        dot.node(str(block.id), label=node_label)
    
    # Добавляем рёбра
    for block in cfg.blocks.values():
        for succ_id, edge_label in block.succs:
            if succ_id not in cfg.blocks:
                continue
            edge_kwargs = {}
            if edge_label is not None:
                edge_kwargs["label"] = edge_label
            dot.edge(str(block.id), str(succ_id), **edge_kwargs)
    
    dot.render(filename, format=fmt, cleanup=True)


def render_all_typed_cfgs(
    typed_data: dict,
    output_dir: str,
    fmt: str = "svg"
) -> None:
    """
    Рендерит все типизированные CFG в указанную директорию.
    
    typed_data: { func_name: (references, _, cfg, tree) } - с заполненными типами.
    """
    from pathlib import Path
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    for func_name, (references, _, cfg, tree) in typed_data.items():
        if func_name.startswith('<file:'):
            continue
        if cfg is None:
            continue
        
        # Создаём имя файла
        safe_name = func_name.replace('"', '').replace('<', '').replace('>', '')
        filename = out_path / safe_name
        
        render_typed_cfg(cfg, str(filename), fmt)
