from builtin_funcs import *
from file_parser_to_graph import BUILTIN_TYPES
import re

# Словарь встроенных функций и их возвращаемых типов
# True означает, что функция возвращает значение, False - нет
BUILTIN_RETURNS = {
    'read_byte': True,  # возвращает byte
    'send_byte': False,  # не возвращает значение
    'bool_to_byte': True,  # возвращает byte
    'byte_to_bool': True,  # возвращает bool
    'byte_to_int': True,  # возвращает int
    'int_to_byte': True,  # возвращает byte
    'int_to_uint': True,  # возвращает uint
    'uint_to_int': True,  # возвращает int
    'int_to_long': True,  # возвращает long
    'long_to_int': True,  # возвращает int
    'long_to_ulong': True,  # возвращает ulong
    'ulong_to_long': True,  # возвращает long
}
# Конструкторы типов возвращают массивы
for t_name in BUILTIN_TYPES:
    BUILTIN_RETURNS[t_name] = True

def generate_preparation(out_file):
    """Записывает подготовительные инструкции в файл."""
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("""[section code, code]
ldsp 0xFFFC      ; even-aligned stack top
ldhp 0x0000      ; init heap base
setbp            ; establish caller bp before first call
call main
hlt
""")


def generate_builtin_func(out_file):
    """Генерирует код для всех встроенных функций."""
    generate_read_byte(out_file)
    generate_send_byte(out_file)
    generate_alloc(out_file)
    generate_bool_constructor(out_file)
    generate_byte_constructor(out_file)
    generate_int_constructor(out_file)
    generate_uint_constructor(out_file)
    generate_long_constructor(out_file)
    generate_ulong_constructor(out_file)
    generate_char_constructor(out_file)
    generate_bool_to_byte(out_file)
    generate_byte_to_bool(out_file)
    generate_byte_to_int(out_file)
    generate_int_to_byte(out_file)
    generate_int_to_uint(out_file)
    generate_uint_to_int(out_file)
    generate_int_to_long(out_file)
    generate_long_to_int(out_file)
    generate_long_to_ulong(out_file)
    generate_ulong_to_long(out_file)

def process_store(tree, params_dict, f, vars_dict, var, funcs_returns=None):
    assert len(tree.children) == 1
    
    process_ast(tree.children[0], params_dict, f, vars_dict, funcs_returns)
    
    if var in vars_dict:
        f.write(f'    stbp {vars_dict[var][1]}\n')
    elif var in params_dict:
        f.write(f'    stbp {params_dict[var][1]}\n')
    else:
        raise ValueError(f"Не нашел переменную {var}")

BINOP_TO_CMD = {
    "+":  "add",
    "-":  "sub",
    "*":  "mul",
    "/":  "div",
    "%":  "mod",
    "<<": "shl",
    ">>": "shr",
    "|":  "bor",
    "&":  "band",
    "^":  "bxor",
    "||": "lor",
    "&&": "land",
    "=": "eq",
    "!=": "ne",
    ">":  "gt",
    "<":  "lt",
    ">=": "ge",
    "<=": "le",
}

def process_bin_op(tree, params_dict, f, vars_dict, bin_op_type, funcs_returns=None):
    assert len(tree.children) == 2
    process_ast(tree.children[0], params_dict, f, vars_dict, funcs_returns)
    process_ast(tree.children[1], params_dict, f, vars_dict, funcs_returns)
    asm_command = BINOP_TO_CMD.get(bin_op_type, None)
    if asm_command is None:
        raise ValueError(f"Не обработанная бинарная инструкция {bin_op_type}")
    f.write(f'    {asm_command}\n')
    
    # Применяем маску для арифметических и битовых операций над целочисленными типами
    # Не применяем маску для логических операций (||, &&) и операций сравнения
    arithmetic_ops = {'+', '-', '*', '/', '%'}
    bitwise_ops = {'<<', '>>', '|', '&', '^'}
    if bin_op_type in arithmetic_ops or bin_op_type in bitwise_ops:
        apply_type_mask(f, tree.type)
    
UNOP_TO_CMD = {
    "!": "not_u",
    "~": "bnot_u",
}

def process_un_op(tree, params_dict, f, vars_dict, un_op_type, funcs_returns=None):
    assert len(tree.children) == 1
    process_ast(tree.children[0], params_dict, f, vars_dict, funcs_returns)
    asm_command = UNOP_TO_CMD.get(un_op_type, None)
    if asm_command is None:
        raise ValueError(f"Не обработанная унарная инструкция {un_op_type}")
    f.write(f'    {asm_command}\n')
    
    # Применяем маску для битовых унарных операций над целочисленными типами
    # Не применяем маску для логических операций (!)
    if un_op_type == '~':  # битовая инверсия
        apply_type_mask(f, tree.type)

TYPE_TO_SHIFT = {
    "bool": 0,    # 1 byte
    "byte": 0,    # 1 byte
    "int": 1,     # 2 bytes
    "uint": 1,    # 2 bytes
    "long": 2,    # 4 bytes
    "ulong": 2,   # 4 bytes
}

LOAD_TYPE = {
    "bool": '1',    # 1 byte
    "byte": '1',    # 1 byte
    "int": '2',     # 2 bytes
    "uint": '2',    # 2 bytes
    "long": '',    # 4 bytes
    "ulong": '',   # 4 bytes
}

# Маски для ограничения размера типов
# Применяются после арифметических и битовых операций
# 32-битные типы (long, ulong) не маскируются, так как они уже занимают полное слово
TYPE_TO_MASK = {
    "bool": 0xFF,        # 8 bits
    "byte": 0xFF,        # 8 bits
    "int": 0xFFFF,       # 16 bits (знаковый)
    "uint": 0xFFFF,      # 16 bits (беззнаковый)
}

def get_type_mask(type_str):
    """Возвращает значение маски для типа или None, если маска не нужна."""
    if type_str is None:
        return None
    # Нормализуем тип (убираем пробелы, приводим к нижнему регистру)
    type_str = type_str.strip().lower()
    # Массивы - это указатели, их не маскируем
    # При обращении к элементам массива тип уже будет типом элемента, а не массива
    if 'array' in type_str:
        return None
    return TYPE_TO_MASK.get(type_str)

def apply_type_mask(f, type_str):
    """Применяет маску к результату на стеке, если это необходимо."""
    mask = get_type_mask(type_str)
    if mask is not None:
        f.write(f'    push {mask}  ; mask for {type_str}\n')
        f.write(f'    band        ; apply type mask\n')
        # Для знаковых типов расширяем знак
        if type_str and type_str.strip().lower() == 'int':
            # Sign-extension для 16-битного int: (x ^ 0x8000) - 0x8000
            f.write(f'    push 0x8000  ; sign bit mask for int\n')
            f.write(f'    bxor         ; flip sign bit\n')
            f.write(f'    push 0x8000  ; prepare for subtraction\n')
            f.write(f'    sub           ; sign extend 16->32\n')

def process_index_op(tree, params_dict, f, vars_dict, funcs_returns=None):
    assert len(tree.children) == 2
    process_ast(tree.children[0], params_dict, f, vars_dict, funcs_returns)
    process_ast(tree.children[1], params_dict, f, vars_dict, funcs_returns)
    shift = TYPE_TO_SHIFT.get(tree.type)
    if shift != 0:
        f.write(f'    push {shift}\n')
        f.write(f'    shl\n')
    f.write(f'    add\n')
    load = LOAD_TYPE.get(tree.type)
    f.write(f'    load{load}\n') # TODO check
    # Для знаковых типов после загрузки из памяти нужно расширить знак
    # (load1 и load2 делают zero-extension, но для int нужен sign-extension)
    if tree.type and tree.type.strip().lower() == 'int' and load == '2':
        # Sign-extension для 16-битного int: (x ^ 0x8000) - 0x8000
        f.write(f'    push 0x8000  ; sign bit mask for int\n')
        f.write(f'    bxor         ; flip sign bit\n')
        f.write(f'    push 0x8000  ; prepare for subtraction\n')
        f.write(f'    sub           ; sign extend 16->32\n')

def process_load_op(tree, params_dict, f, vars_dict, var_name):
    assert len(tree.children) == 0
    if var_name in vars_dict:
        f.write(f'    ldbp {vars_dict[var_name][1]}\n')
    elif var_name in params_dict:
        f.write(f'    ldbp {params_dict[var_name][1]}\n')
    else:
        raise ValueError(f"Не нашел переменную {var_name}")

def process_store_at_op(tree, params_dict, f, vars_dict, var_name, funcs_returns=None):
    assert len(tree.children) == 2
    if var_name in vars_dict:
        var = vars_dict[var_name]
    elif var_name in params_dict:
        var = params_dict[var_name]
    else:
        raise ValueError(f"Не нашел переменную {var_name}")
    
    f.write(f'    ldbp {var[1]}\n')
    process_ast(tree.children[0], params_dict, f, vars_dict, funcs_returns)
    shift = TYPE_TO_SHIFT.get(var[0].split(' ')[-1])
    if shift != 0:
        f.write(f'    push {shift}\n')
        f.write(f'    shl\n')
    f.write(f'    add\n')
    process_ast(tree.children[1], params_dict, f, vars_dict, funcs_returns)
    load = LOAD_TYPE.get(tree.type)
    f.write(f'    store{load}\n')

def process_call_op(tree, params_dict, f, vars_dict, func_name, funcs_returns=None):
    # Проверяем, возвращает ли функция значение
    has_return = False
    if funcs_returns:
        func_type = funcs_returns.get(func_name)
        if func_type and func_type[0] is not None:
            has_return = True
    else:
        # Fallback на встроенные функции
        has_return = BUILTIN_RETURNS.get(func_name, False)
    
    for tree_child in tree.children:
        process_ast(tree_child, params_dict, f, vars_dict, funcs_returns)
    
    if len(tree.children) == 0 and has_return:
        f.write(f'    push 0  ; for return value\n')
        
    f.write(f'    call {func_name}\n')
    
    for _ in range(len(tree.children) - (1 if has_return else 0)):
        if has_return:
            f.write(f'    swap\n')
        f.write(f'    drop\n')

def process_const_op(tree, params_dict, f, vars_dict, const_name, const_val):
    assert len(tree.children) == 0 
    match const_name:
        case 'bool':
            val_for_push = 0 if const_val.lower() == 'false' else 1
            f.write(f'    push {val_for_push} ; bool = {const_val.lower()}\n')
        case 'char':
            val_for_push = ord(const_val[1])
            f.write(f'    push {val_for_push} ; char = {const_val}\n')
        case 'hex':
            val_for_push = int(const_val[2:], 16)
            f.write(f'    push {val_for_push} ; hex = {const_val}\n')
        case 'bits':
            val_for_push = int(const_val[2:], 2)
            f.write(f'    push {val_for_push} ; bits = {const_val}\n')
        case 'dec':
            val_for_push = int(const_val)
            f.write(f'    push {val_for_push} ; dec = {const_val}\n')
        case 'str':
            val_for_push = const_val[1:-1]
            f.write(f'    push {len(val_for_push)} ; string = {val_for_push}\n')
            f.write(f'    call byte\n') # Создал масив байтов нужного размера
            for index, symbol in enumerate(val_for_push):
                f.write(f'    dup\n')
                f.write(f'    push {index}\n')
                f.write(f'    add\n')
                f.write(f'    push {ord(symbol)} ; char = {symbol}\n')
                f.write(f'    store1\n')
        case '_':
            raise ValueError(f"Неизвестное обозначение {const_name}")
        

STORE_RE = re.compile(r'^store\(([A-Za-z_][A-Za-z_0-9]*)\)$')
BIN_OP_RE = re.compile(r'^(<<|>>|<=|>=|=|!=|\+|-|\*|/|%|&|\||\^|<|>|\|\||&&)$')
UN_OP_RE = re.compile(r'^(~|!)$')
INDEX_RE = re.compile(r'^index$')
LOAD_RE = re.compile(r'^load\(([A-Za-z_][A-Za-z_0-9]*)(\[\])?\)$')
STORE_AT_RE = re.compile(r'^store_at\(([A-Za-z_][A-Za-z_0-9]*)\)$')
CALL_RE = re.compile(r'^call\(([A-Za-z_][A-Za-z_0-9]*)\)$')
CONST_RE = re.compile(r'^const\((.*)\((.*)\)\)$')

def process_ast(tree, params_dict, f, vars_dict, funcs_returns=None):
    if tree is None:
        return
    
    store_match = STORE_RE.match(tree.label)
    if store_match:
        process_store(tree, params_dict, f, vars_dict, store_match.group(1), funcs_returns)
        return
    
    bin_op_match = BIN_OP_RE.match(tree.label)
    if bin_op_match:
        process_bin_op(tree, params_dict, f, vars_dict, bin_op_match.group(1), funcs_returns)
        return
    
    un_op_match = UN_OP_RE.match(tree.label)
    if un_op_match:
        process_un_op(tree, params_dict, f, vars_dict, un_op_match.group(1), funcs_returns)
        return
    
    index_match = INDEX_RE.match(tree.label)
    if index_match:
        process_index_op(tree, params_dict, f, vars_dict, funcs_returns)
        return

    load_match = LOAD_RE.match(tree.label)
    if load_match:
        process_load_op(tree, params_dict, f, vars_dict, load_match.group(1))
        return
    
    store_at_match = STORE_AT_RE.match(tree.label)
    if store_at_match:
        process_store_at_op(tree, params_dict, f, vars_dict, store_at_match.group(1), funcs_returns)
        return

    call_match = CALL_RE.match(tree.label)
    if call_match:
        process_call_op(tree, params_dict, f, vars_dict, call_match.group(1), funcs_returns)
        return
    
    const_match = CONST_RE.match(tree.label)
    if const_match:
        process_const_op(tree, params_dict, f, vars_dict, const_match.group(1), const_match.group(2))
        return
    
    raise ValueError(f"Неизвестный элемент {tree.label}")

def process_block(f_name, block, params_dict, f, vars_dict, funcs_returns=None):
    f.write(f'.id{block.id}:\n')
    
    process_ast(block.tree, params_dict, f, vars_dict, funcs_returns)
    
    if len(block.succs) == 0:
        f.write(f'    jmp .out\n')
    elif len(block.succs) == 1:
        succ_id, _ = block.succs[0]
        f.write(f'    jmp .id{succ_id}\n')
    else:
        # Два перехода: True и False
        true_succ = next(succ_id for succ_id, label in block.succs if label.lower() == "true")
        false_succ = next(succ_id for succ_id, label in block.succs if label.lower() == "false")
        f.write(f'    jnz .id{true_succ}\n')
        f.write(f'    jmp .id{false_succ}\n')

def process_cfg(f_name, f_cfg, f_tree, params_dict, out_file, vars_dict, funcs_returns=None):
    for _, block in f_cfg.blocks.items():
        process_block(f_name, block, params_dict, out_file, vars_dict, funcs_returns)

def process_func(f_name, f_cfg, f_tree, f_params, out_file, vars, funcs_returns=None):
    # Преобразуем vars из списка кортежей в словарь с смещениями
    vars_dict = {}
    for index, (var_name, var_type) in enumerate(vars):
        offset = (index + 1) * -4
        vars_dict[var_name] = (var_type, offset)
    
    # Преобразуем f_params из списка кортежей в словарь с смещениями
    params_dict = {}
    for index, (param_name, param_type) in enumerate(f_params):
        offset = 4 * (len(f_params) - index + 1)
        params_dict[param_name] = (param_type, offset)
    
    # Проверяем, возвращает ли функция значение
    has_return = False
    if funcs_returns:
        func_type = funcs_returns.get(f_name)
        if func_type and func_type[0] is not None:
            has_return = True
    
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write(f'\n{f_name}:\n')
        
        for var_name, var_type in vars:
            f.write(f'    push 0    ; {var_name}\n')
        
        process_cfg(f_name, f_cfg, f_tree, params_dict, f, vars_dict, funcs_returns)
        f.write(f'.out:\n')
        
        # Если функция возвращает значение, перемещаем его из переменной с именем функции в bp + 8
        if has_return and f_name in vars_dict:
            var_offset = vars_dict[f_name][1]
            f.write(f'    ldbp {var_offset}  ; load return value from {f_name}\n')
            f.write(f'    stbp 8  ; store return value at bp + 8\n')
        
        f.write('    ret\n')

def generate_asm(typed_blocks, out_file, funcs_returns=None):
    # Записываем подготовительные инструкции
    generate_preparation(out_file)
    
    # Записываем встроенные функции
    generate_builtin_func(out_file)
    
    # Обрабатываем пользовательские функции
    for f_name, (_, _, cfg, tree, params, vars) in typed_blocks.items():
        # Пропускаем псевдо-узлы файлов
        if f_name.startswith('<file:'):
            continue
        # Пропускаем функции без CFG
        if cfg is None:
            continue
        process_func(f_name, cfg, tree, params, out_file, vars, funcs_returns)