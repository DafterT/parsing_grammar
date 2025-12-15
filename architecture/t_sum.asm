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

bool_to_byte:    ; Builtin function: bool_to_byte(b: bool) -> byte
    ret          ; value already at [bp+8], no conversion needed

byte_to_bool:    ; Builtin function: byte_to_bool(b: byte) -> bool
    ret          ; value already at [bp+8], no conversion needed

byte_to_int:     ; Builtin function: byte_to_int(b: byte) -> int
    ret          ; value already at [bp+8], already zero-extended to 32 bits

int_to_byte:     ; Builtin function: int_to_byte(i: int) -> byte
    ldbp 8       ; load int value from [bp+8]
    push 0xFF    ; mask for byte (8 bits)
    band         ; apply mask
    stbp 8       ; store result at [bp+8]
    ret

int_to_uint:     ; Builtin function: int_to_uint(i: int) -> uint
    ret          ; value already at [bp+8], no conversion needed

uint_to_int:     ; Builtin function: uint_to_int(u: uint) -> int
    ret          ; value already at [bp+8], no conversion needed

int_to_long:     ; Builtin function: int_to_long(i: int) -> long
    ldbp 8       ; load int value from [bp+8]
    push 0xFFFF  ; mask to get only lower 16 bits
    band         ; keep only lower 16 bits (clears upper 16 bits)
    push 0x8000  ; sign bit mask
    bxor         ; flip sign bit: (x ^ 0x8000)
    push 0x8000  ; prepare for subtraction
    sub          ; (x ^ 0x8000) - 0x8000 (sign extend 16->32)
    stbp 8       ; store result at [bp+8]
    ret

long_to_int:     ; Builtin function: long_to_int(l: long) -> int
    ldbp 8       ; load long value from [bp+8]
    push 0xFFFF  ; mask for int (16 bits)
    band         ; apply mask to get lower 16 bits
    stbp 8       ; store result at [bp+8]
    ret

long_to_ulong:   ; Builtin function: long_to_ulong(l: long) -> ulong
    ret          ; value already at [bp+8], no conversion needed

ulong_to_long:   ; Builtin function: ulong_to_long(u: ulong) -> long
    ret          ; value already at [bp+8], no conversion needed

test_send_one_byte:
test_send_one_byte_0:
    jmp test_send_one_byte_2
test_send_one_byte_1:
    jmp test_send_one_byte_out
test_send_one_byte_2:
    push 0  ; for return value
    call read_byte
    call send_byte
    drop
    jmp test_send_one_byte_1
test_send_one_byte_out:
    ret

test_builtin_func:
    push 0    ; a
    push 0    ; b
test_builtin_func_0:
    jmp test_builtin_func_2
test_builtin_func_1:
    jmp test_builtin_func_out
test_builtin_func_2:
    push 49 ; dec = 49
    stbp -4
    jmp test_builtin_func_3
test_builtin_func_3:
    push 0 ; dec = 0
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp -8
    jmp test_builtin_func_4
test_builtin_func_4:
    push 4 ; dec = 4
    jmp test_builtin_func_5
test_builtin_func_5:
    ldbp -4
    call uint_to_int
    ldbp -8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_builtin_func_6
test_builtin_func_6:
    push 1 ; dec = 1
    jmp test_builtin_func_7
test_builtin_func_7:
    push 49 ; dec = 49
    call send_byte
    drop
    jmp test_builtin_func_1
test_builtin_func_out:
    ret

test_math:
    push 0    ; a
    push 0    ; b
test_math_0:
    jmp test_math_2
test_math_1:
    jmp test_math_out
test_math_2:
    push 200 ; dec = 200
    stbp -8
    jmp test_math_3
test_math_3:
    push 5000 ; dec = 5000
    push 3000 ; dec = 3000
    add
    push 65535  ; mask for uint
    band        ; apply type mask
    push 4 ; dec = 4
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    ldbp -8
    push 10 ; dec = 10
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    sub
    push 65535  ; mask for uint
    band        ; apply type mask
    push 10 ; dec = 10
    div
    push 65535  ; mask for uint
    band        ; apply type mask
    push 97 ; dec = 97
    mod
    push 65535  ; mask for uint
    band        ; apply type mask
    ldbp -8
    push 5 ; dec = 5
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    push 25 ; dec = 25
    div
    push 65535  ; mask for uint
    band        ; apply type mask
    sub
    push 65535  ; mask for uint
    band        ; apply type mask
    ldbp -8
    push 6 ; dec = 6
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    push 3 ; dec = 3
    div
    push 65535  ; mask for uint
    band        ; apply type mask
    ldbp -8
    push 2 ; dec = 2
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    sub
    push 65535  ; mask for uint
    band        ; apply type mask
    push 7 ; dec = 7
    push 7 ; dec = 7
    sub
    push 65535  ; mask for uint
    band        ; apply type mask
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    push 99 ; dec = 99
    push 9 ; dec = 9
    mod
    push 65535  ; mask for uint
    band        ; apply type mask
    push 123 ; dec = 123
    push 1 ; dec = 1
    add
    push 65535  ; mask for uint
    band        ; apply type mask
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    add
    push 65535  ; mask for uint
    band        ; apply type mask
    push 500 ; dec = 500
    push 10 ; dec = 10
    div
    push 65535  ; mask for uint
    band        ; apply type mask
    push 50 ; dec = 50
    sub
    push 65535  ; mask for uint
    band        ; apply type mask
    ldbp -8
    mul
    push 65535  ; mask for uint
    band        ; apply type mask
    add
    push 65535  ; mask for uint
    band        ; apply type mask
    push 1 ; dec = 1
    div
    push 65535  ; mask for uint
    band        ; apply type mask
    add
    push 65535  ; mask for uint
    band        ; apply type mask
    stbp -4
    jmp test_math_4
test_math_4:
    ldbp -4
    call uint_to_int
    call int_to_byte
    call send_byte
    drop
    jmp test_math_1
test_math_out:
    ret

test_if:
test_if_0:
    jmp test_if_2
test_if_1:
    jmp test_if_out
test_if_2:
    ldbp 8
    push 3 ; dec = 3
    eq
    jnz test_if_3
    jmp test_if_5
test_if_3:
    push 50 ; dec = 50
    call send_byte
    drop
    jmp test_if_4
test_if_4:
    jmp test_if_1
test_if_5:
    ldbp 8
    push 4 ; dec = 4
    eq
    jnz test_if_6
    jmp test_if_8
test_if_6:
    push 48 ; dec = 48
    call send_byte
    drop
    jmp test_if_7
test_if_7:
    jmp test_if_4
test_if_8:
    push 49 ; dec = 49
    call send_byte
    drop
    jmp test_if_7
test_if_out:
    ret

test_req:
test_req_0:
    jmp test_req_2
test_req_1:
    jmp test_req_out
test_req_2:
    ldbp 8
    push 0 ; dec = 0
    eq
    jnz test_req_3
    jmp test_req_5
test_req_3:
    push 48 ; dec = 48
    call send_byte
    drop
    jmp test_req_4
test_req_4:
    jmp test_req_1
test_req_5:
    jmp test_req_7
test_req_6:
    jmp test_req_4
test_req_7:
    push 48 ; dec = 48
    ldbp 8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_req_8
test_req_8:
    ldbp 8
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    call test_req
    drop
    jmp test_req_9
test_req_9:
    push 48 ; dec = 48
    ldbp 8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_req_6
test_req_out:
    ret

test_while:
test_while_0:
    jmp test_while_2
test_while_1:
    jmp test_while_out
test_while_2:
    ldbp 8
    push 0 ; dec = 0
    ne
    jnz test_while_4
    jmp test_while_3
test_while_3:
    jmp test_while_1
test_while_4:
    jmp test_while_6
test_while_5:
    jmp test_while_2
test_while_6:
    ldbp 8
    push 48 ; dec = 48
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_while_7
test_while_7:
    ldbp 8
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp 8
    jmp test_while_5
test_while_out:
    ret

test_break:
test_break_0:
    jmp test_break_2
test_break_1:
    jmp test_break_out
test_break_2:
    ldbp 8
    push 0 ; dec = 0
    ne
    jnz test_break_4
    jmp test_break_3
test_break_3:
    jmp test_break_1
test_break_4:
    jmp test_break_6
test_break_5:
    jmp test_break_2
test_break_6:
    ldbp 8
    push 48 ; dec = 48
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_break_7
test_break_7:
    ldbp 8
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp 8
    jmp test_break_8
test_break_8:
    ldbp 8
    push 3 ; dec = 3
    eq
    jnz test_break_9
    jmp test_break_10
test_break_9:
    jmp test_break_3
test_break_10:
    jmp test_break_5
test_break_out:
    ret

test_many_operands:
test_many_operands_0:
    jmp test_many_operands_2
test_many_operands_1:
    jmp test_many_operands_out
test_many_operands_2:
    ldbp 16
    call send_byte
    drop
    jmp test_many_operands_3
test_many_operands_3:
    ldbp 12
    call send_byte
    drop
    jmp test_many_operands_4
test_many_operands_4:
    push 48 ; dec = 48
    ldbp 8
    call bool_to_byte
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp test_many_operands_1
test_many_operands_out:
    ret

test_mas:
    push 0    ; b
    push 0    ; c
    push 0    ; d
test_mas_0:
    jmp test_mas_2
test_mas_1:
    jmp test_mas_out
test_mas_2:
    ldbp 8
    call int
    stbp -4
    jmp test_mas_3
test_mas_3:
    ldbp -4
    push 0 ; dec = 0
    push 1
    shl
    add
    push 50 ; dec = 50
    store2
    jmp test_mas_4
test_mas_4:
    ldbp -4
    push 2 ; dec = 2
    push 1
    shl
    add
    push 51 ; dec = 51
    store2
    jmp test_mas_5
test_mas_5:
    ldbp -4
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_6
test_mas_6:
    ldbp -4
    push 2 ; dec = 2
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_7
test_mas_7:
    ldbp 8
    call int
    stbp -8
    jmp test_mas_8
test_mas_8:
    ldbp -8
    push 0 ; dec = 0
    push 1
    shl
    add
    push 52 ; dec = 52
    store2
    jmp test_mas_9
test_mas_9:
    ldbp -8
    push 9 ; dec = 9
    push 1
    shl
    add
    push 53 ; dec = 53
    store2
    jmp test_mas_10
test_mas_10:
    ldbp -8
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_11
test_mas_11:
    ldbp -8
    push 9 ; dec = 9
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_12
test_mas_12:
    ldbp 8
    call int
    stbp -12
    jmp test_mas_13
test_mas_13:
    ldbp -12
    push 0 ; dec = 0
    push 1
    shl
    add
    push 12337 ; hex = 0x3031
    store2
    jmp test_mas_14
test_mas_14:
    ldbp -12
    push 1 ; dec = 1
    push 1
    shl
    add
    push 13106 ; hex = 0x3332
    store2
    jmp test_mas_15
test_mas_15:
    ldbp -12
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_16
test_mas_16:
    ldbp -12
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    push 8 ; dec = 8
    shr
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_17
test_mas_17:
    ldbp -12
    push 1 ; dec = 1
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_18
test_mas_18:
    ldbp -12
    push 1 ; dec = 1
    push 1
    shl
    add
    load2
    push 8 ; dec = 8
    shr
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp test_mas_1
test_mas_out:
    ret

main:
main_0:
    jmp main_2
main_1:
    jmp main_out
main_2:
    call test_send_one_byte
    jmp main_3
main_3:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_4
main_4:
    call test_builtin_func
    jmp main_5
main_5:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_6
main_6:
    call test_math
    jmp main_7
main_7:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_8
main_8:
    push 5 ; dec = 5
    call test_if
    drop
    jmp main_9
main_9:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_10
main_10:
    push 3 ; dec = 3
    call test_if
    drop
    jmp main_11
main_11:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_12
main_12:
    push 4 ; dec = 4
    call test_if
    drop
    jmp main_13
main_13:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_14
main_14:
    push 0 ; dec = 0
    call test_req
    drop
    jmp main_15
main_15:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_16
main_16:
    push 5 ; dec = 5
    call test_req
    drop
    jmp main_17
main_17:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_18
main_18:
    push 9 ; dec = 9
    call test_while
    drop
    jmp main_19
main_19:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_20
main_20:
    push 9 ; dec = 9
    call test_break
    drop
    jmp main_21
main_21:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_22
main_22:
    push 50 ; dec = 50
    push 49 ; dec = 49
    push 1 ; bool = true
    call test_many_operands
    drop
    drop
    drop
    jmp main_23
main_23:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp main_24
main_24:
    push 10 ; dec = 10
    call test_mas
    drop
    jmp main_1
main_out:
    ret
