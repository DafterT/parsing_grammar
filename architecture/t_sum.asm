[section code, code]
ldsp 0xFFFC      ; even-aligned stack top
ldhp 0x0000      ; init heap base
setbp            ; establish caller bp before first call
call main
hlt

read_byte:      ; Builtin function: read_byte()
    inb         ; read in byte
    stbp 8      ; store at bp + 8
    ret

send_byte:      ; Builtin function: send_byte(b: byte)
    ldbp 8      ; load bp + 8
    outb        ; send byte
    ret

alloc:
     ; frame layout: [bp] saved bp, [bp+4] return, [bp+8] size_shift, [bp+12] len
     ldbp 12       ; push len
     ldbp 8        ; push size_shift
     shl           ; total_bytes = len << size_shift
     pushhp        ; old hp -> will be return value
     stbp 8        ; store return value at [bp+8], pop old hp
     addhp         ; hp = hp + total_bytes, pop total
     ret

bool:                   ; Builtin constructor: bool(size) -> array[] of bool
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 0             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

byte:                   ; Builtin constructor: byte(size) -> array[] of byte
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 0             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

int:                    ; Builtin constructor: int(size) -> array[] of int
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 1             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

uint:                   ; Builtin constructor: uint(size) -> array[] of uint
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 1             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

long:                   ; Builtin constructor: long(size) -> array[] of long
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 2             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

ulong:                  ; Builtin constructor: ulong(size) -> array[] of ulong
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 2             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

char:                   ; Builtin constructor: char(size) -> array[] of char
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 0             ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

test_unary:
    push 0    ; a
    push 0    ; b
test_unary_0:
    jmp test_unary_2
test_unary_1:
    jmp test_unary_out
test_unary_2:
    ldbp -8
    bnot_u
    stbp -4
    jmp test_unary_1
test_unary_out:
    ret

test_int_arithmetic:
    push 0    ; a
    push 0    ; b
    push 0    ; c
test_int_arithmetic_0:
    jmp test_int_arithmetic_2
test_int_arithmetic_1:
    jmp test_int_arithmetic_out
test_int_arithmetic_2:
    ldbp -8
    ldbp -12
    add
    stbp -4
    jmp test_int_arithmetic_3
test_int_arithmetic_3:
    ldbp -8
    ldbp -12
    sub
    stbp -4
    jmp test_int_arithmetic_4
test_int_arithmetic_4:
    ldbp -8
    ldbp -12
    mul
    stbp -4
    jmp test_int_arithmetic_5
test_int_arithmetic_5:
    ldbp -8
    ldbp -12
    div
    stbp -4
    jmp test_int_arithmetic_6
test_int_arithmetic_6:
    ldbp -8
    ldbp -12
    mod
    stbp -4
    jmp test_int_arithmetic_1
test_int_arithmetic_out:
    ret

test_uint_arithmetic:
    push 0    ; a
    push 0    ; b
    push 0    ; c
test_uint_arithmetic_0:
    jmp test_uint_arithmetic_2
test_uint_arithmetic_1:
    jmp test_uint_arithmetic_out
test_uint_arithmetic_2:
    ldbp -8
    ldbp -12
    add
    stbp -4
    jmp test_uint_arithmetic_3
test_uint_arithmetic_3:
    ldbp -8
    ldbp -12
    sub
    stbp -4
    jmp test_uint_arithmetic_4
test_uint_arithmetic_4:
    ldbp -8
    ldbp -12
    mul
    stbp -4
    jmp test_uint_arithmetic_5
test_uint_arithmetic_5:
    ldbp -8
    ldbp -12
    div
    stbp -4
    jmp test_uint_arithmetic_6
test_uint_arithmetic_6:
    ldbp -8
    ldbp -12
    mod
    stbp -4
    jmp test_uint_arithmetic_1
test_uint_arithmetic_out:
    ret

test_long_arithmetic:
    push 0    ; a
    push 0    ; b
    push 0    ; c
test_long_arithmetic_0:
    jmp test_long_arithmetic_2
test_long_arithmetic_1:
    jmp test_long_arithmetic_out
test_long_arithmetic_2:
    ldbp -8
    ldbp -12
    add
    stbp -4
    jmp test_long_arithmetic_3
test_long_arithmetic_3:
    ldbp -8
    ldbp -12
    sub
    stbp -4
    jmp test_long_arithmetic_4
test_long_arithmetic_4:
    ldbp -8
    ldbp -12
    mul
    stbp -4
    jmp test_long_arithmetic_1
test_long_arithmetic_out:
    ret

test_ulong_arithmetic:
    push 0    ; a
    push 0    ; b
    push 0    ; c
test_ulong_arithmetic_0:
    jmp test_ulong_arithmetic_2
test_ulong_arithmetic_1:
    jmp test_ulong_arithmetic_out
test_ulong_arithmetic_2:
    ldbp -8
    ldbp -12
    add
    stbp -4
    jmp test_ulong_arithmetic_3
test_ulong_arithmetic_3:
    ldbp -8
    ldbp -12
    mul
    stbp -4
    jmp test_ulong_arithmetic_4
test_ulong_arithmetic_4:
    ldbp -8
    ldbp -12
    div
    stbp -4
    jmp test_ulong_arithmetic_1
test_ulong_arithmetic_out:
    ret

test_byte_arithmetic:
    push 0    ; a
    push 0    ; b
    push 0    ; c
test_byte_arithmetic_0:
    jmp test_byte_arithmetic_2
test_byte_arithmetic_1:
    jmp test_byte_arithmetic_out
test_byte_arithmetic_2:
    ldbp -8
    ldbp -12
    add
    stbp -4
    jmp test_byte_arithmetic_3
test_byte_arithmetic_3:
    ldbp -8
    ldbp -12
    sub
    stbp -4
    jmp test_byte_arithmetic_4
test_byte_arithmetic_4:
    ldbp -8
    ldbp -12
    mul
    stbp -4
    jmp test_byte_arithmetic_1
test_byte_arithmetic_out:
    ret

test_int_bitwise:
    push 0    ; x
    push 0    ; y
    push 0    ; z
test_int_bitwise_0:
    jmp test_int_bitwise_2
test_int_bitwise_1:
    jmp test_int_bitwise_out
test_int_bitwise_2:
    ldbp -8
    ldbp -12
    bor
    stbp -4
    jmp test_int_bitwise_3
test_int_bitwise_3:
    ldbp -8
    ldbp -12
    band
    stbp -4
    jmp test_int_bitwise_4
test_int_bitwise_4:
    ldbp -8
    ldbp -12
    bxor
    stbp -4
    jmp test_int_bitwise_5
test_int_bitwise_5:
    ldbp -8
    ldbp -12
    shl
    stbp -4
    jmp test_int_bitwise_6
test_int_bitwise_6:
    ldbp -8
    ldbp -12
    shr
    stbp -4
    jmp test_int_bitwise_7
test_int_bitwise_7:
    ldbp -8
    bnot_u
    stbp -4
    jmp test_int_bitwise_1
test_int_bitwise_out:
    ret

test_uint_bitwise:
    push 0    ; x
    push 0    ; y
    push 0    ; z
test_uint_bitwise_0:
    jmp test_uint_bitwise_2
test_uint_bitwise_1:
    jmp test_uint_bitwise_out
test_uint_bitwise_2:
    ldbp -8
    ldbp -12
    bor
    stbp -4
    jmp test_uint_bitwise_3
test_uint_bitwise_3:
    ldbp -8
    ldbp -12
    band
    stbp -4
    jmp test_uint_bitwise_4
test_uint_bitwise_4:
    ldbp -8
    ldbp -12
    bxor
    stbp -4
    jmp test_uint_bitwise_5
test_uint_bitwise_5:
    ldbp -8
    bnot_u
    stbp -4
    jmp test_uint_bitwise_1
test_uint_bitwise_out:
    ret

test_byte_bitwise:
    push 0    ; x
    push 0    ; y
    push 0    ; z
test_byte_bitwise_0:
    jmp test_byte_bitwise_2
test_byte_bitwise_1:
    jmp test_byte_bitwise_out
test_byte_bitwise_2:
    ldbp -8
    ldbp -12
    bor
    stbp -4
    jmp test_byte_bitwise_3
test_byte_bitwise_3:
    ldbp -8
    ldbp -12
    band
    stbp -4
    jmp test_byte_bitwise_4
test_byte_bitwise_4:
    ldbp -8
    bnot_u
    stbp -4
    jmp test_byte_bitwise_1
test_byte_bitwise_out:
    ret

test_logical:
    push 0    ; flag1
    push 0    ; flag2
    push 0    ; result
test_logical_0:
    jmp test_logical_2
test_logical_1:
    jmp test_logical_out
test_logical_2:
    ldbp -4
    ldbp -8
    lor
    stbp -12
    jmp test_logical_3
test_logical_3:
    ldbp -4
    ldbp -8
    land
    stbp -12
    jmp test_logical_4
test_logical_4:
    ldbp -4
    not_u
    stbp -12
    jmp test_logical_1
test_logical_out:
    ret

test_int_comparison:
    push 0    ; a
    push 0    ; b
    push 0    ; result
test_int_comparison_0:
    jmp test_int_comparison_2
test_int_comparison_1:
    jmp test_int_comparison_out
test_int_comparison_2:
    ldbp -4
    ldbp -8
    eq
    stbp -12
    jmp test_int_comparison_3
test_int_comparison_3:
    ldbp -4
    ldbp -8
    ne
    stbp -12
    jmp test_int_comparison_4
test_int_comparison_4:
    ldbp -4
    ldbp -8
    gt
    stbp -12
    jmp test_int_comparison_5
test_int_comparison_5:
    ldbp -4
    ldbp -8
    ge
    stbp -12
    jmp test_int_comparison_6
test_int_comparison_6:
    ldbp -4
    ldbp -8
    lt
    stbp -12
    jmp test_int_comparison_7
test_int_comparison_7:
    ldbp -4
    ldbp -8
    le
    stbp -12
    jmp test_int_comparison_1
test_int_comparison_out:
    ret

test_uint_comparison:
    push 0    ; a
    push 0    ; b
    push 0    ; result
test_uint_comparison_0:
    jmp test_uint_comparison_2
test_uint_comparison_1:
    jmp test_uint_comparison_out
test_uint_comparison_2:
    ldbp -4
    ldbp -8
    eq
    stbp -12
    jmp test_uint_comparison_3
test_uint_comparison_3:
    ldbp -4
    ldbp -8
    ne
    stbp -12
    jmp test_uint_comparison_4
test_uint_comparison_4:
    ldbp -4
    ldbp -8
    gt
    stbp -12
    jmp test_uint_comparison_5
test_uint_comparison_5:
    ldbp -4
    ldbp -8
    lt
    stbp -12
    jmp test_uint_comparison_1
test_uint_comparison_out:
    ret

test_char_comparison:
    push 0    ; a
    push 0    ; b
    push 0    ; result
test_char_comparison_0:
    jmp test_char_comparison_2
test_char_comparison_1:
    jmp test_char_comparison_out
test_char_comparison_2:
    ldbp -4
    ldbp -8
    eq
    stbp -12
    jmp test_char_comparison_3
test_char_comparison_3:
    ldbp -4
    ldbp -8
    ne
    stbp -12
    jmp test_char_comparison_1
test_char_comparison_out:
    ret

test_int_array:
    push 0    ; arr
    push 0    ; idx
    push 0    ; val
test_int_array_0:
    jmp test_int_array_2
test_int_array_1:
    jmp test_int_array_out
test_int_array_2:
    stbp -4
    jmp test_int_array_3
test_int_array_3:
    ldbp -4
    ldbp -8
    push 2
    shl
    add
    load2
    stbp -12
    jmp test_int_array_4
test_int_array_4:
    ldbp -4
    ldbp -8
    push 2
    shl
    add
    ldbp -12
    add
    store2
    jmp test_int_array_1
test_int_array_out:
    ret

test_uint_array:
    push 0    ; arr
    push 0    ; idx
    push 0    ; val
test_uint_array_0:
    jmp test_uint_array_2
test_uint_array_1:
    jmp test_uint_array_out
test_uint_array_2:
    stbp -4
    jmp test_uint_array_3
test_uint_array_3:
    ldbp -4
    ldbp -8
    push 2
    shl
    add
    load2
    stbp -12
    jmp test_uint_array_4
test_uint_array_4:
    ldbp -4
    ldbp -8
    push 2
    shl
    add
    ldbp -12
    add
    store2
    jmp test_uint_array_1
test_uint_array_out:
    ret

test_byte_array:
    push 0    ; arr
    push 0    ; idx
    push 0    ; val
test_byte_array_0:
    jmp test_byte_array_2
test_byte_array_1:
    jmp test_byte_array_out
test_byte_array_2:
    stbp -4
    jmp test_byte_array_3
test_byte_array_3:
    ldbp -4
    ldbp -8
    push 1
    shl
    add
    load1
    stbp -12
    jmp test_byte_array_4
test_byte_array_4:
    ldbp -4
    ldbp -8
    push 1
    shl
    add
    ldbp -12
    add
    store1
    jmp test_byte_array_1
test_byte_array_out:
    ret

test_char_array:
    push 0    ; arr
    push 0    ; idx
    push 0    ; val
test_char_array_0:
    jmp test_char_array_2
test_char_array_1:
    jmp test_char_array_out
test_char_array_2:
    stbp -4
    jmp test_char_array_3
test_char_array_3:
    ldbp -4
    ldbp -8
    push 1
    shl
    add
    load1
    stbp -12
    jmp test_char_array_4
test_char_array_4:
    ldbp -4
    ldbp -8
    push 1
    shl
    add
    store1
    jmp test_char_array_1
test_char_array_out:
    ret

add_ints:
    push 0    ; sum
add_ints_0:
    jmp add_ints_2
add_ints_1:
    jmp add_ints_out
add_ints_2:
    ldbp 12
    ldbp 8
    add
    stbp -4
    jmp add_ints_1
add_ints_out:
    ret

add_uints:
    push 0    ; sum
add_uints_0:
    jmp add_uints_2
add_uints_1:
    jmp add_uints_out
add_uints_2:
    ldbp 12
    ldbp 8
    add
    stbp -4
    jmp add_uints_1
add_uints_out:
    ret

add_longs:
    push 0    ; sum
add_longs_0:
    jmp add_longs_2
add_longs_1:
    jmp add_longs_out
add_longs_2:
    ldbp 12
    ldbp 8
    add
    stbp -4
    jmp add_longs_1
add_longs_out:
    ret

test_call_int:
    push 0    ; a
    push 0    ; b
test_call_int_0:
    jmp test_call_int_2
test_call_int_1:
    jmp test_call_int_out
test_call_int_2:
    jmp test_call_int_1
test_call_int_out:
    ret

test_call_uint:
    push 0    ; a
    push 0    ; b
test_call_uint_0:
    jmp test_call_uint_2
test_call_uint_1:
    jmp test_call_uint_out
test_call_uint_2:
    jmp test_call_uint_1
test_call_uint_out:
    ret

test_call_long:
    push 0    ; a
    push 0    ; b
test_call_long_0:
    jmp test_call_long_2
test_call_long_1:
    jmp test_call_long_out
test_call_long_2:
    jmp test_call_long_1
test_call_long_out:
    ret

test_literals:
    push 0    ; i
    push 0    ; b
    push 0    ; c
    push 0    ; s
test_literals_0:
    jmp test_literals_2
test_literals_1:
    jmp test_literals_out
test_literals_2:
    stbp -4
    jmp test_literals_3
test_literals_3:
    stbp -4
    jmp test_literals_4
test_literals_4:
    stbp -4
    jmp test_literals_5
test_literals_5:
    stbp -8
    jmp test_literals_6
test_literals_6:
    stbp -8
    jmp test_literals_7
test_literals_7:
    stbp -12
    jmp test_literals_8
test_literals_8:
    stbp -16
    jmp test_literals_1
test_literals_out:
    ret

test_nested_expr:
    push 0    ; a
    push 0    ; b
    push 0    ; c
    push 0    ; d
test_nested_expr_0:
    jmp test_nested_expr_2
test_nested_expr_1:
    jmp test_nested_expr_out
test_nested_expr_2:
    ldbp -4
    ldbp -8
    add
    ldbp -12
    ldbp -4
    sub
    mul
    stbp -16
    jmp test_nested_expr_3
test_nested_expr_3:
    ldbp -4
    ldbp -8
    ldbp -12
    mul
    add
    stbp -16
    jmp test_nested_expr_1
test_nested_expr_out:
    ret

test_literals_auto_type:
    push 0    ; i
    push 0    ; u
    push 0    ; l
    push 0    ; ul
    push 0    ; b
test_literals_auto_type_0:
    jmp test_literals_auto_type_2
test_literals_auto_type_1:
    jmp test_literals_auto_type_out
test_literals_auto_type_2:
    stbp -4
    jmp test_literals_auto_type_3
test_literals_auto_type_3:
    ldbp -4
    add
    stbp -4
    jmp test_literals_auto_type_4
test_literals_auto_type_4:
    ldbp -4
    add
    stbp -4
    jmp test_literals_auto_type_5
test_literals_auto_type_5:
    stbp -8
    jmp test_literals_auto_type_6
test_literals_auto_type_6:
    ldbp -8
    add
    stbp -8
    jmp test_literals_auto_type_7
test_literals_auto_type_7:
    ldbp -8
    add
    stbp -8
    jmp test_literals_auto_type_8
test_literals_auto_type_8:
    stbp -12
    jmp test_literals_auto_type_9
test_literals_auto_type_9:
    ldbp -12
    add
    stbp -12
    jmp test_literals_auto_type_10
test_literals_auto_type_10:
    ldbp -12
    add
    stbp -12
    jmp test_literals_auto_type_11
test_literals_auto_type_11:
    stbp -16
    jmp test_literals_auto_type_12
test_literals_auto_type_12:
    ldbp -16
    add
    stbp -16
    jmp test_literals_auto_type_13
test_literals_auto_type_13:
    ldbp -16
    add
    stbp -16
    jmp test_literals_auto_type_14
test_literals_auto_type_14:
    stbp -20
    jmp test_literals_auto_type_15
test_literals_auto_type_15:
    ldbp -20
    add
    stbp -20
    jmp test_literals_auto_type_16
test_literals_auto_type_16:
    ldbp -20
    add
    stbp -20
    jmp test_literals_auto_type_1
test_literals_auto_type_out:
    ret

test_generated_functions:
    push 0    ; i
test_generated_functions_0:
    jmp test_generated_functions_2
test_generated_functions_1:
    jmp test_generated_functions_out
test_generated_functions_2:
    stbp -4
    jmp test_generated_functions_3
test_generated_functions_3:
    jmp test_generated_functions_1
test_generated_functions_out:
    ret

test_strings:
    push 0    ; i
test_strings_0:
    jmp test_strings_2
test_strings_1:
    jmp test_strings_out
test_strings_2:
    stbp -4
    jmp test_strings_3
test_strings_3:
    ldbp -4
    push 1
    shl
    add
    store1
    jmp test_strings_1
test_strings_out:
    ret

test_if_then:
    push 0    ; a
    push 0    ; b
test_if_then_0:
    jmp test_if_then_2
test_if_then_1:
    jmp test_if_then_out
test_if_then_2:
    ldbp -4
    ldbp -8
    gt
    jnz test_if_then_3
    jmp test_if_then_4
test_if_then_3:
    stbp -4
    jmp test_if_then_4
test_if_then_4:
    jmp test_if_then_1
test_if_then_out:
    ret

test_if_then_else:
    push 0    ; a
    push 0    ; b
    push 0    ; c
test_if_then_else_0:
    jmp test_if_then_else_2
test_if_then_else_1:
    jmp test_if_then_else_out
test_if_then_else_2:
    ldbp -4
    ldbp -8
    gt
    jnz test_if_then_else_3
    jmp test_if_then_else_5
test_if_then_else_3:
    stbp -12
    jmp test_if_then_else_4
test_if_then_else_4:
    jmp test_if_then_else_1
test_if_then_else_5:
    stbp -12
    jmp test_if_then_else_4
test_if_then_else_out:
    ret

test_while_do:
    push 0    ; i
    push 0    ; sum
test_while_do_0:
    jmp test_while_do_2
test_while_do_1:
    jmp test_while_do_out
test_while_do_2:
    ldbp -4
    gt
    jnz test_while_do_4
    jmp test_while_do_3
test_while_do_3:
    jmp test_while_do_1
test_while_do_4:
    jmp test_while_do_6
test_while_do_5:
    jmp test_while_do_2
test_while_do_6:
    ldbp -8
    ldbp -4
    add
    stbp -8
    jmp test_while_do_7
test_while_do_7:
    ldbp -4
    sub
    stbp -4
    jmp test_while_do_5
test_while_do_out:
    ret

test_repeat_while:
    push 0    ; i
test_repeat_while_0:
    jmp test_repeat_while_2
test_repeat_while_1:
    jmp test_repeat_while_out
test_repeat_while_2:
    jmp test_repeat_while_4
test_repeat_while_3:
    jmp test_repeat_while_1
test_repeat_while_4:
    ldbp -4
    add
    stbp -4
    jmp test_repeat_while_5
test_repeat_while_5:
    ldbp -4
    lt
    jnz test_repeat_while_2
    jmp test_repeat_while_3
test_repeat_while_out:
    ret

test_repeat_until:
    push 0    ; i
test_repeat_until_0:
    jmp test_repeat_until_2
test_repeat_until_1:
    jmp test_repeat_until_out
test_repeat_until_2:
    jmp test_repeat_until_4
test_repeat_until_3:
    jmp test_repeat_until_1
test_repeat_until_4:
    ldbp -4
    add
    stbp -4
    jmp test_repeat_until_5
test_repeat_until_5:
    ldbp -4
    ge
    jnz test_repeat_until_3
    jmp test_repeat_until_2
test_repeat_until_out:
    ret

test_nested_if:
    push 0    ; a
    push 0    ; b
    push 0    ; c
    push 0    ; result
test_nested_if_0:
    jmp test_nested_if_2
test_nested_if_1:
    jmp test_nested_if_out
test_nested_if_2:
    ldbp -4
    gt
    jnz test_nested_if_3
    jmp test_nested_if_8
test_nested_if_3:
    ldbp -8
    gt
    jnz test_nested_if_4
    jmp test_nested_if_6
test_nested_if_4:
    stbp -16
    jmp test_nested_if_5
test_nested_if_5:
    jmp test_nested_if_7
test_nested_if_6:
    stbp -16
    jmp test_nested_if_5
test_nested_if_7:
    jmp test_nested_if_1
test_nested_if_8:
    ldbp -12
    gt
    jnz test_nested_if_9
    jmp test_nested_if_11
test_nested_if_9:
    stbp -16
    jmp test_nested_if_10
test_nested_if_10:
    jmp test_nested_if_7
test_nested_if_11:
    stbp -16
    jmp test_nested_if_10
test_nested_if_out:
    ret

test_if_with_while:
    push 0    ; i
    push 0    ; flag
    push 0    ; count
test_if_with_while_0:
    jmp test_if_with_while_2
test_if_with_while_1:
    jmp test_if_with_while_out
test_if_with_while_2:
    ldbp -8
    jnz test_if_with_while_3
    jmp test_if_with_while_11
test_if_with_while_3:
    jmp test_if_with_while_5
test_if_with_while_4:
    jmp test_if_with_while_11
test_if_with_while_5:
    ldbp -4
    gt
    jnz test_if_with_while_7
    jmp test_if_with_while_6
test_if_with_while_6:
    jmp test_if_with_while_4
test_if_with_while_7:
    jmp test_if_with_while_9
test_if_with_while_8:
    jmp test_if_with_while_5
test_if_with_while_9:
    ldbp -12
    add
    stbp -12
    jmp test_if_with_while_10
test_if_with_while_10:
    ldbp -4
    sub
    stbp -4
    jmp test_if_with_while_8
test_if_with_while_11:
    jmp test_if_with_while_1
test_if_with_while_out:
    ret

test_while_with_break:
    push 0    ; i
test_while_with_break_0:
    jmp test_while_with_break_2
test_while_with_break_1:
    jmp test_while_with_break_out
test_while_with_break_2:
    ldbp -4
    lt
    jnz test_while_with_break_4
    jmp test_while_with_break_3
test_while_with_break_3:
    jmp test_while_with_break_1
test_while_with_break_4:
    jmp test_while_with_break_6
test_while_with_break_5:
    jmp test_while_with_break_2
test_while_with_break_6:
    ldbp -4
    eq
    jnz test_while_with_break_7
    jmp test_while_with_break_8
test_while_with_break_7:
    jmp test_while_with_break_3
test_while_with_break_8:
    jmp test_while_with_break_9
test_while_with_break_9:
    ldbp -4
    add
    stbp -4
    jmp test_while_with_break_5
test_while_with_break_out:
    ret

test_complex_branching:
    push 0    ; x
    push 0    ; y
    push 0    ; z
    push 0    ; result
test_complex_branching_0:
    jmp test_complex_branching_2
test_complex_branching_1:
    jmp test_complex_branching_out
test_complex_branching_2:
    ldbp -4
    ldbp -8
    gt
    jnz test_complex_branching_3
    jmp test_complex_branching_8
test_complex_branching_3:
    ldbp -4
    ldbp -12
    gt
    jnz test_complex_branching_4
    jmp test_complex_branching_6
test_complex_branching_4:
    ldbp -4
    stbp -16
    jmp test_complex_branching_5
test_complex_branching_5:
    jmp test_complex_branching_7
test_complex_branching_6:
    ldbp -12
    stbp -16
    jmp test_complex_branching_5
test_complex_branching_7:
    jmp test_complex_branching_12
test_complex_branching_8:
    ldbp -8
    ldbp -12
    gt
    jnz test_complex_branching_9
    jmp test_complex_branching_11
test_complex_branching_9:
    ldbp -8
    stbp -16
    jmp test_complex_branching_10
test_complex_branching_10:
    jmp test_complex_branching_7
test_complex_branching_11:
    ldbp -12
    stbp -16
    jmp test_complex_branching_10
test_complex_branching_12:
    ldbp -16
    gt
    jnz test_complex_branching_14
    jmp test_complex_branching_13
test_complex_branching_13:
    jmp test_complex_branching_1
test_complex_branching_14:
    jmp test_complex_branching_16
test_complex_branching_15:
    jmp test_complex_branching_12
test_complex_branching_16:
    ldbp -16
    mod
    eq
    jnz test_complex_branching_17
    jmp test_complex_branching_19
test_complex_branching_17:
    ldbp -16
    div
    stbp -16
    jmp test_complex_branching_18
test_complex_branching_18:
    jmp test_complex_branching_15
test_complex_branching_19:
    ldbp -16
    sub
    stbp -16
    jmp test_complex_branching_18
test_complex_branching_out:
    ret

test_all_operations:
    push 0    ; a
    push 0    ; b
    push 0    ; c
    push 0    ; ua
    push 0    ; ub
    push 0    ; uc
    push 0    ; ba
    push 0    ; bb
    push 0    ; bc
    push 0    ; flag1
    push 0    ; flag2
    push 0    ; result
    push 0    ; ch1
    push 0    ; ch2
test_all_operations_0:
    jmp test_all_operations_2
test_all_operations_1:
    jmp test_all_operations_out
test_all_operations_2:
    ldbp -8
    ldbp -12
    add
    stbp -4
    jmp test_all_operations_3
test_all_operations_3:
    ldbp -8
    ldbp -12
    sub
    stbp -4
    jmp test_all_operations_4
test_all_operations_4:
    ldbp -8
    ldbp -12
    mul
    stbp -4
    jmp test_all_operations_5
test_all_operations_5:
    ldbp -8
    ldbp -12
    div
    stbp -4
    jmp test_all_operations_6
test_all_operations_6:
    ldbp -8
    ldbp -12
    mod
    stbp -4
    jmp test_all_operations_7
test_all_operations_7:
    ldbp -20
    ldbp -24
    add
    stbp -16
    jmp test_all_operations_8
test_all_operations_8:
    ldbp -20
    ldbp -24
    sub
    stbp -16
    jmp test_all_operations_9
test_all_operations_9:
    ldbp -20
    ldbp -24
    mul
    stbp -16
    jmp test_all_operations_10
test_all_operations_10:
    ldbp -20
    ldbp -24
    div
    stbp -16
    jmp test_all_operations_11
test_all_operations_11:
    ldbp -20
    ldbp -24
    mod
    stbp -16
    jmp test_all_operations_12
test_all_operations_12:
    ldbp -8
    ldbp -12
    shl
    stbp -4
    jmp test_all_operations_13
test_all_operations_13:
    ldbp -8
    ldbp -12
    shr
    stbp -4
    jmp test_all_operations_14
test_all_operations_14:
    ldbp -8
    ldbp -12
    bor
    stbp -4
    jmp test_all_operations_15
test_all_operations_15:
    ldbp -8
    ldbp -12
    band
    stbp -4
    jmp test_all_operations_16
test_all_operations_16:
    ldbp -8
    ldbp -12
    bxor
    stbp -4
    jmp test_all_operations_17
test_all_operations_17:
    ldbp -20
    ldbp -24
    bor
    stbp -16
    jmp test_all_operations_18
test_all_operations_18:
    ldbp -20
    ldbp -24
    band
    stbp -16
    jmp test_all_operations_19
test_all_operations_19:
    ldbp -20
    ldbp -24
    bxor
    stbp -16
    jmp test_all_operations_20
test_all_operations_20:
    ldbp -32
    ldbp -36
    bor
    stbp -28
    jmp test_all_operations_21
test_all_operations_21:
    ldbp -32
    ldbp -36
    band
    stbp -28
    jmp test_all_operations_22
test_all_operations_22:
    ldbp -32
    ldbp -36
    bxor
    stbp -28
    jmp test_all_operations_23
test_all_operations_23:
    ldbp -40
    ldbp -44
    lor
    stbp -48
    jmp test_all_operations_24
test_all_operations_24:
    ldbp -40
    ldbp -44
    land
    stbp -48
    jmp test_all_operations_25
test_all_operations_25:
    ldbp -4
    ldbp -8
    eq
    stbp -48
    jmp test_all_operations_26
test_all_operations_26:
    ldbp -4
    ldbp -8
    ne
    stbp -48
    jmp test_all_operations_27
test_all_operations_27:
    ldbp -4
    ldbp -8
    gt
    stbp -48
    jmp test_all_operations_28
test_all_operations_28:
    ldbp -4
    ldbp -8
    lt
    stbp -48
    jmp test_all_operations_29
test_all_operations_29:
    ldbp -4
    ldbp -8
    ge
    stbp -48
    jmp test_all_operations_30
test_all_operations_30:
    ldbp -4
    ldbp -8
    le
    stbp -48
    jmp test_all_operations_31
test_all_operations_31:
    ldbp -16
    ldbp -20
    eq
    stbp -48
    jmp test_all_operations_32
test_all_operations_32:
    ldbp -16
    ldbp -20
    ne
    stbp -48
    jmp test_all_operations_33
test_all_operations_33:
    ldbp -16
    ldbp -20
    gt
    stbp -48
    jmp test_all_operations_34
test_all_operations_34:
    ldbp -16
    ldbp -20
    lt
    stbp -48
    jmp test_all_operations_35
test_all_operations_35:
    ldbp -16
    ldbp -20
    ge
    stbp -48
    jmp test_all_operations_36
test_all_operations_36:
    ldbp -16
    ldbp -20
    le
    stbp -48
    jmp test_all_operations_37
test_all_operations_37:
    ldbp -52
    ldbp -56
    eq
    stbp -48
    jmp test_all_operations_38
test_all_operations_38:
    ldbp -52
    ldbp -56
    ne
    stbp -48
    jmp test_all_operations_39
test_all_operations_39:
    ldbp -40
    not_u
    stbp -48
    jmp test_all_operations_40
test_all_operations_40:
    ldbp -8
    bnot_u
    stbp -4
    jmp test_all_operations_41
test_all_operations_41:
    ldbp -20
    bnot_u
    stbp -16
    jmp test_all_operations_42
test_all_operations_42:
    ldbp -32
    bnot_u
    stbp -28
    jmp test_all_operations_1
test_all_operations_out:
    ret

test_all_array_types:
    push 0    ; arr_int
    push 0    ; arr_uint
    push 0    ; arr_long
    push 0    ; arr_ulong
    push 0    ; arr_byte
    push 0    ; arr_char
    push 0    ; arr_bool
    push 0    ; idx
    push 0    ; val_int
    push 0    ; val_uint
    push 0    ; val_long
    push 0    ; val_ulong
    push 0    ; val_byte
    push 0    ; val_char
    push 0    ; val_bool
test_all_array_types_0:
    jmp test_all_array_types_2
test_all_array_types_1:
    jmp test_all_array_types_out
test_all_array_types_2:
    stbp -4
    jmp test_all_array_types_3
test_all_array_types_3:
    ldbp -4
    ldbp -32
    push 2
    shl
    add
    load2
    stbp -36
    jmp test_all_array_types_4
test_all_array_types_4:
    ldbp -4
    ldbp -32
    push 2
    shl
    add
    ldbp -36
    store2
    jmp test_all_array_types_5
test_all_array_types_5:
    stbp -8
    jmp test_all_array_types_6
test_all_array_types_6:
    ldbp -8
    ldbp -32
    push 2
    shl
    add
    load2
    stbp -40
    jmp test_all_array_types_7
test_all_array_types_7:
    ldbp -8
    ldbp -32
    push 2
    shl
    add
    ldbp -40
    store2
    jmp test_all_array_types_8
test_all_array_types_8:
    stbp -12
    jmp test_all_array_types_9
test_all_array_types_9:
    ldbp -12
    ldbp -32
    push 4
    shl
    add
    load
    stbp -44
    jmp test_all_array_types_10
test_all_array_types_10:
    ldbp -12
    ldbp -32
    push 4
    shl
    add
    ldbp -44
    store
    jmp test_all_array_types_11
test_all_array_types_11:
    stbp -16
    jmp test_all_array_types_12
test_all_array_types_12:
    ldbp -16
    ldbp -32
    push 4
    shl
    add
    load
    stbp -48
    jmp test_all_array_types_13
test_all_array_types_13:
    ldbp -16
    ldbp -32
    push 4
    shl
    add
    ldbp -48
    store
    jmp test_all_array_types_14
test_all_array_types_14:
    stbp -20
    jmp test_all_array_types_15
test_all_array_types_15:
    ldbp -20
    ldbp -32
    push 1
    shl
    add
    load1
    stbp -52
    jmp test_all_array_types_16
test_all_array_types_16:
    ldbp -20
    ldbp -32
    push 1
    shl
    add
    ldbp -52
    store1
    jmp test_all_array_types_17
test_all_array_types_17:
    stbp -24
    jmp test_all_array_types_18
test_all_array_types_18:
    ldbp -24
    ldbp -32
    push 1
    shl
    add
    load1
    stbp -56
    jmp test_all_array_types_19
test_all_array_types_19:
    ldbp -24
    ldbp -32
    push 1
    shl
    add
    store1
    jmp test_all_array_types_20
test_all_array_types_20:
    stbp -28
    jmp test_all_array_types_21
test_all_array_types_21:
    ldbp -28
    ldbp -32
    push 1
    shl
    add
    load1
    stbp -60
    jmp test_all_array_types_22
test_all_array_types_22:
    ldbp -28
    ldbp -32
    push 1
    shl
    add
    store1
    jmp test_all_array_types_1
test_all_array_types_out:
    ret

main:
main_0:
    jmp main_2
main_1:
    jmp main_out
main_2:
    jmp main_3
main_3:
    jmp main_4
main_4:
    jmp main_5
main_5:
    jmp main_6
main_6:
    jmp main_7
main_7:
    jmp main_8
main_8:
    jmp main_9
main_9:
    jmp main_10
main_10:
    jmp main_11
main_11:
    jmp main_12
main_12:
    jmp main_13
main_13:
    jmp main_14
main_14:
    jmp main_15
main_15:
    jmp main_16
main_16:
    jmp main_17
main_17:
    jmp main_18
main_18:
    jmp main_19
main_19:
    jmp main_20
main_20:
    jmp main_21
main_21:
    jmp main_22
main_22:
    jmp main_23
main_23:
    jmp main_24
main_24:
    jmp main_25
main_25:
    jmp main_26
main_26:
    jmp main_27
main_27:
    jmp main_28
main_28:
    jmp main_29
main_29:
    jmp main_30
main_30:
    jmp main_31
main_31:
    jmp main_32
main_32:
    jmp main_33
main_33:
    jmp main_34
main_34:
    jmp main_35
main_35:
    jmp main_36
main_36:
    jmp main_37
main_37:
    jmp main_1
main_out:
    ret
