from builtin_funcs import *
from file_parser_to_graph import BUILTIN_TYPES
import re

# Словарь встроенных функций и их возвращаемых типов
# True означает, что функция возвращает значение, False - нет
BUILTIN_RETURNS = {
    'read_byte': True,  # возвращает byte
    'send_byte': False,  # не возвращает значение
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

def process_store(tree, params_dict, f, vars_dict, var):
    assert len(tree.children) == 1
    
    process_ast(tree.children[0], params_dict, f, vars_dict)
    
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

def process_bin_op(tree, params_dict, f, vars_dict, bin_op_type):
    assert len(tree.children) == 2
    process_ast(tree.children[0], params_dict, f, vars_dict)
    process_ast(tree.children[1], params_dict, f, vars_dict)
    asm_command = BINOP_TO_CMD.get(bin_op_type, None)
    if asm_command is None:
        raise ValueError(f"Не обработанная бинарная инструкция {bin_op_type}")
    f.write(f'    {asm_command}\n')
    
UNOP_TO_CMD = {
    "!": "not_u",
    "~": "bnot_u",
}

def process_un_op(tree, params_dict, f, vars_dict, un_op_type):
    assert len(tree.children) == 1
    process_ast(tree.children[0], params_dict, f, vars_dict)
    asm_command = UNOP_TO_CMD.get(un_op_type, None)
    if asm_command is None:
        raise ValueError(f"Не обработанная унарная инструкция {un_op_type}")
    f.write(f'    {asm_command}\n')

TYPE_TO_SHIFT = {
    "bool": 1,    # 1 byte
    "byte": 1,    # 1 byte
    "int": 2,     # 2 bytes
    "uint": 2,    # 2 bytes
    "long": 4,    # 4 bytes
    "ulong": 4,   # 4 bytes
}

def process_index_op(tree, params_dict, f, vars_dict):
    assert len(tree.children) == 2
    process_ast(tree.children[0], params_dict, f, vars_dict)
    process_ast(tree.children[1], params_dict, f, vars_dict)
    shift = TYPE_TO_SHIFT.get(tree.type)
    f.write(f'    push {shift}\n')
    f.write(f'    shl\n')
    f.write(f'    add\n')
    f.write(f'    load{shift if shift != 4 else ''}\n')

def process_load_op(tree, params_dict, f, vars_dict, var_name):
    assert len(tree.children) == 0
    if var_name in vars_dict:
        f.write(f'    ldbp {vars_dict[var_name][1]}\n')
    elif var_name in params_dict:
        f.write(f'    ldbp {params_dict[var_name][1]}\n')
    else:
        raise ValueError(f"Не нашел переменную {var_name}")

def process_store_at_op(tree, params_dict, f, vars_dict, var_name):
    assert len(tree.children) == 2
    if var_name in vars_dict:
        var = vars_dict[var_name]
    elif var_name in params_dict:
        var = params_dict[var_name]
    else:
        raise ValueError(f"Не нашел переменную {var_name}")
    
    f.write(f'    ldbp {var[1]}\n')
    process_ast(tree.children[0], params_dict, f, vars_dict)
    shift = TYPE_TO_SHIFT.get(var[0].split(' ')[-1])
    f.write(f'    push {shift}\n')
    f.write(f'    shl\n')
    f.write(f'    add\n')
    process_ast(tree.children[1], params_dict, f, vars_dict)
    f.write(f'    store{shift if shift != 4 else ''}\n')

def process_call_op(tree, params_dict, f, vars_dict, func_name):
    has_return = BUILTIN_RETURNS.get(func_name, False)
    
    for tree_child in tree.children:
        process_ast(tree_child, params_dict, f, vars_dict)
    
    if len(tree.children) == 0 and has_return:
        f.write(f'    push 0  ; for return value\n')
        
    f.write(f'    call {func_name}\n')
    
    for _ in range(len(tree.children) - (1 if has_return else 0)):
        if has_return:
            f.write(f'    swap\n')
        f.write(f'    drop\n')

def process_const_op():
    pass

STORE_RE = re.compile(r'^store\(([A-Za-z_][A-Za-z_0-9]*)\)$')
BIN_OP_RE = re.compile(r'^(<<|>>|<=|>=|=|!=|\+|-|\*|/|%|&|\||\^|<|>|\|\||&&)$')
UN_OP_RE = re.compile(r'^(~|!)$')
INDEX_RE = re.compile(r'^index$')
LOAD_RE = re.compile(r'^load\(([A-Za-z_][A-Za-z_0-9]*)(\[\])?\)$')
STORE_AT_RE = re.compile(r'^store_at\(([A-Za-z_][A-Za-z_0-9]*)\)$')
CALL_RE = re.compile(r'^call\(([A-Za-z_][A-Za-z_0-9]*)\)$')
CONST_RE = re.compile(r'^const\((.*)\((.*)\)\)$')

def process_ast(tree, params_dict, f, vars_dict):
    if tree is None:
        return
    
    store_match = STORE_RE.match(tree.label)
    if store_match:
        process_store(tree, params_dict, f, vars_dict, store_match.group(1))
        return
    
    bin_op_match = BIN_OP_RE.match(tree.label)
    if bin_op_match:
        process_bin_op(tree, params_dict, f, vars_dict, bin_op_match.group(1))
        return
    
    un_op_match = UN_OP_RE.match(tree.label)
    if un_op_match:
        process_un_op(tree, params_dict, f, vars_dict, un_op_match.group(1))
        return
    
    index_match = INDEX_RE.match(tree.label)
    if index_match:
        process_index_op(tree, params_dict, f, vars_dict)
        return

    load_match = LOAD_RE.match(tree.label)
    if load_match:
        process_load_op(tree, params_dict, f, vars_dict, load_match.group(1))
        return
    
    store_at_match = STORE_AT_RE.match(tree.label)
    if store_at_match:
        process_store_at_op(tree, params_dict, f, vars_dict, store_at_match.group(1))
        return

    call_match = CALL_RE.match(tree.label)
    if call_match:
        process_call_op(tree, params_dict, f, vars_dict, call_match.group(1))
        return
    
    const_match = CONST_RE.match(tree.label)
    if const_match:
        return
        process_const_op(tree, params_dict, f, vars_dict, const_match.group(1), const_match.group(2))
        return
    #const
    pass

def process_block(f_name, block, params_dict, f, vars_dict):
    f.write(f'{f_name}_{block.id}:\n')
    
    process_ast(block.tree, params_dict, f, vars_dict)
    
    if len(block.succs) == 0:
        f.write(f'    jmp {f_name}_out\n')
    elif len(block.succs) == 1:
        succ_id, _ = block.succs[0]
        f.write(f'    jmp {f_name}_{succ_id}\n')
    else:
        # Два перехода: True и False
        true_succ = next(succ_id for succ_id, label in block.succs if label.lower() == "true")
        false_succ = next(succ_id for succ_id, label in block.succs if label.lower() == "false")
        f.write(f'    jnz {f_name}_{true_succ}\n')
        f.write(f'    jmp {f_name}_{false_succ}\n')

def process_cfg(f_name, f_cfg, f_tree, params_dict, out_file, vars_dict):
    for _, block in f_cfg.blocks.items():
        process_block(f_name, block, params_dict, out_file, vars_dict)

def process_func(f_name, f_cfg, f_tree, f_params, out_file, vars):
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
    
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write(f'\n{f_name}:\n')
        
        for var_name, var_type in vars:
            f.write(f'    push 0    ; {var_name}\n')
        
        process_cfg(f_name, f_cfg, f_tree, params_dict, f, vars_dict)
        f.write(f'{f_name}_out:\n')
        f.write('    ret\n')

def generate_asm(typed_blocks, out_file):
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
        process_func(f_name, cfg, tree, params, out_file, vars)