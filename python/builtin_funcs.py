def generate_alloc(out_file):
    """Генерирует код для функции alloc."""
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write("""
alloc:
     ; frame layout: [bp] saved bp, [bp+4] return, [bp+8] size_shift, [bp+12] len
     ldbp 12       ; push len
     ldbp 8        ; push size_shift
     shl           ; total_bytes = len << size_shift
     pushhp        ; old hp -> will be return value
     stbp 8        ; store return value at [bp+8], pop old hp
     addhp         ; hp = hp + total_bytes, pop total
     ret
""")


def _generate_type_constructor(out_file, type_name, size_shift):
    """
    Общая функция для генерации конструктора типа.
    
    Args:
        out_file: Путь к выходному файлу
        type_name: Имя типа (bool, byte, int, etc.)
        size_shift: Сдвиг размера для alloc (0 для 1 байта, 1 для 2 байт, 2 для 4 байт)
    """
    # Выравнивание комментариев: название функции до колонки 20, push до колонки 20
    label_col = 24
    push_col = 24
    indent = "     "  # 5 пробелов для отступа команд
    
    # Форматируем название функции с выравниванием комментария
    label_line = f"{type_name}:"
    label_padding = " " * (label_col - len(label_line))
    label_line = f"{label_line}{label_padding}; Builtin constructor: {type_name}(size) -> array[] of {type_name}"
    
    # Форматируем push с выравниванием комментария
    # Учитываем отступ (5 пробелов) + команда push + число
    push_cmd = f"push {size_shift}"
    total_push_len = len(indent) + len(push_cmd)
    push_padding = " " * (push_col - total_push_len)
    push_line = f"{indent}{push_cmd}{push_padding}; push size_shift to stack"
    
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write(f"""
{label_line}
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
{push_line}
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret
""")


def generate_read_byte(out_file): # Вызывать с 1 аргументом для результата
    """Генерирует код для встроенной функции read_byte."""
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write("""
read_byte:      ; Builtin function: read_byte()
    inb         ; read in byte
    stbp 8      ; store at bp + 8
    ret
""")

def generate_send_byte(out_file):
    """Генерирует код для встроенной функции send_byte."""
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write("""
send_byte:      ; Builtin function: send_byte(b: byte)
    ldbp 8      ; load bp + 8
    outb        ; send byte
    ret
""")


def generate_bool_constructor(out_file):
    """Генерирует код для конструктора типа bool (1 байт, size_shift=0)."""
    _generate_type_constructor(out_file, 'bool', 0)


def generate_byte_constructor(out_file):
    """Генерирует код для конструктора типа byte (1 байт, size_shift=0)."""
    _generate_type_constructor(out_file, 'byte', 0)


def generate_int_constructor(out_file):
    """Генерирует код для конструктора типа int (2 байта, size_shift=1)."""
    _generate_type_constructor(out_file, 'int', 1)


def generate_uint_constructor(out_file):
    """Генерирует код для конструктора типа uint (2 байта, size_shift=1)."""
    _generate_type_constructor(out_file, 'uint', 1)


def generate_long_constructor(out_file):
    """Генерирует код для конструктора типа long (4 байта, size_shift=2)."""
    _generate_type_constructor(out_file, 'long', 2)


def generate_ulong_constructor(out_file):
    """Генерирует код для конструктора типа ulong (4 байта, size_shift=2)."""
    _generate_type_constructor(out_file, 'ulong', 2)


def generate_char_constructor(out_file):
    """Генерирует код для конструктора типа char (1 байт, size_shift=0)."""
    _generate_type_constructor(out_file, 'char', 0)
