from builtin_funcs import *

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

def process_cfg(f_name, f_cfg, f_tree, f_params, out_file, vars_dict):
    pass

def process_func(f_name, f_cfg, f_tree, f_params, out_file, vars):
    # Преобразуем vars из списка кортежей в словарь с смещениями
    vars_dict = {}
    for index, (var_name, var_type) in enumerate(vars):
        offset = (index + 1) * -4
        vars_dict[var_name] = (var_type, offset)
    
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write(f'{f_name}:\n')
        
        for var_name, var_type in vars:
            f.write(f'    push 0    ; {var_name}\n')
        
        process_cfg(f_name, f_cfg, f_tree, f_params, out_file, vars_dict)
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