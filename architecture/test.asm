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
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    push 0  ; for return value
    call read_byte
    call send_byte
    drop
    jmp .id1
.out:
    ret

test_builtin_func:
    push 0    ; a
    push 0    ; b
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    push 49 ; dec = 49
    stbp -4
    jmp .id3
.id3:
    push 0 ; dec = 0
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp -8
    jmp .id4
.id4:
    push 4 ; dec = 4
    jmp .id5
.id5:
    ldbp -4
    call uint_to_int
    ldbp -8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp .id6
.id6:
    push 1 ; dec = 1
    jmp .id7
.id7:
    push 49 ; dec = 49
    call send_byte
    drop
    jmp .id1
.out:
    ret

test_math:
    push 0    ; a
    push 0    ; b
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    push 200 ; dec = 200
    stbp -8
    jmp .id3
.id3:
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
    jmp .id4
.id4:
    ldbp -4
    call uint_to_int
    call int_to_byte
    call send_byte
    drop
    jmp .id1
.out:
    ret

test_if:
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 8
    push 3 ; dec = 3
    eq
    jnz .id3
    jmp .id5
.id3:
    push 50 ; dec = 50
    call send_byte
    drop
    jmp .id4
.id4:
    jmp .id1
.id5:
    ldbp 8
    push 4 ; dec = 4
    eq
    jnz .id6
    jmp .id8
.id6:
    push 48 ; dec = 48
    call send_byte
    drop
    jmp .id7
.id7:
    jmp .id4
.id8:
    push 49 ; dec = 49
    call send_byte
    drop
    jmp .id7
.out:
    ret

test_req:
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 8
    push 0 ; dec = 0
    eq
    jnz .id3
    jmp .id5
.id3:
    push 48 ; dec = 48
    call send_byte
    drop
    jmp .id4
.id4:
    jmp .id1
.id5:
    jmp .id7
.id6:
    jmp .id4
.id7:
    push 48 ; dec = 48
    ldbp 8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp .id8
.id8:
    ldbp 8
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    call test_req
    drop
    jmp .id9
.id9:
    push 48 ; dec = 48
    ldbp 8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp .id6
.out:
    ret

test_while:
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 8
    push 0 ; dec = 0
    ne
    jnz .id4
    jmp .id3
.id3:
    jmp .id1
.id4:
    jmp .id6
.id5:
    jmp .id2
.id6:
    ldbp 8
    push 48 ; dec = 48
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp .id7
.id7:
    ldbp 8
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp 8
    jmp .id5
.out:
    ret

test_break:
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 8
    push 0 ; dec = 0
    ne
    jnz .id4
    jmp .id3
.id3:
    jmp .id1
.id4:
    jmp .id6
.id5:
    jmp .id2
.id6:
    ldbp 8
    push 48 ; dec = 48
    add
    push 65535  ; mask for int
    band        ; apply type mask
    call int_to_byte
    call send_byte
    drop
    jmp .id7
.id7:
    ldbp 8
    push 1 ; dec = 1
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp 8
    jmp .id8
.id8:
    ldbp 8
    push 3 ; dec = 3
    eq
    jnz .id9
    jmp .id10
.id9:
    jmp .id3
.id10:
    jmp .id5
.out:
    ret

test_many_operands:
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 16
    call send_byte
    drop
    jmp .id3
.id3:
    ldbp 12
    call send_byte
    drop
    jmp .id4
.id4:
    push 48 ; dec = 48
    ldbp 8
    call bool_to_byte
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id1
.out:
    ret

test_mas:
    push 0    ; b
    push 0    ; c
    push 0    ; d
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 8
    call int
    stbp -4
    jmp .id3
.id3:
    ldbp -4
    push 0 ; dec = 0
    push 1
    shl
    add
    push 50 ; dec = 50
    store2
    jmp .id4
.id4:
    ldbp -4
    push 2 ; dec = 2
    push 1
    shl
    add
    push 51 ; dec = 51
    store2
    jmp .id5
.id5:
    ldbp -4
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp .id6
.id6:
    ldbp -4
    push 2 ; dec = 2
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp .id7
.id7:
    ldbp 8
    call int
    stbp -8
    jmp .id8
.id8:
    ldbp -8
    push 0 ; dec = 0
    push 1
    shl
    add
    push 52 ; dec = 52
    store2
    jmp .id9
.id9:
    ldbp -8
    push 9 ; dec = 9
    push 1
    shl
    add
    push 53 ; dec = 53
    store2
    jmp .id10
.id10:
    ldbp -8
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp .id11
.id11:
    ldbp -8
    push 9 ; dec = 9
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp .id12
.id12:
    ldbp 8
    call int
    stbp -12
    jmp .id13
.id13:
    ldbp -12
    push 0 ; dec = 0
    push 1
    shl
    add
    push 12337 ; hex = 0x3031
    store2
    jmp .id14
.id14:
    ldbp -12
    push 1 ; dec = 1
    push 1
    shl
    add
    push 13106 ; hex = 0x3332
    store2
    jmp .id15
.id15:
    ldbp -12
    push 0 ; dec = 0
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp .id16
.id16:
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
    jmp .id17
.id17:
    ldbp -12
    push 1 ; dec = 1
    push 1
    shl
    add
    load2
    call int_to_byte
    call send_byte
    drop
    jmp .id18
.id18:
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
    jmp .id1
.out:
    ret

test_return:
    push 0    ; test_return
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    push 48 ; dec = 48
    stbp -4
    jmp .id1
.out:
    ldbp -4  ; load return value from test_return
    stbp 8  ; store return value at bp + 8
    ret

test_return_2:
    push 0    ; test_return_2
.id0:
    jmp .id1
.id1:
    jmp .out
.out:
    ldbp -4  ; load return value from test_return_2
    stbp 8  ; store return value at bp + 8
    ret

calculate_complex:
    push 0    ; temp1
    push 0    ; temp2
    push 0    ; result
    push 0    ; calculate_complex
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    ldbp 16
    ldbp 12
    add
    push 65535  ; mask for int
    band        ; apply type mask
    stbp -4
    jmp .id3
.id3:
    ldbp 12
    ldbp 8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    stbp -8
    jmp .id4
.id4:
    ldbp -4
    ldbp -8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    ldbp 12
    sub
    push 65535  ; mask for int
    band        ; apply type mask
    stbp -12
    jmp .id5
.id5:
    ldbp -12
    stbp -16
    jmp .id1
.out:
    ldbp -16  ; load return value from calculate_complex
    stbp 8  ; store return value at bp + 8
    ret

test_calculate_complex:
    push 0    ; res1
    push 0    ; res2
    push 0    ; final_result
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    push 5 ; dec = 5
    push 10 ; dec = 10
    push 15 ; dec = 15
    call calculate_complex
    swap
    drop
    swap
    drop
    stbp -4
    jmp .id3
.id3:
    push 3 ; dec = 3
    push 7 ; dec = 7
    push 11 ; dec = 11
    call calculate_complex
    swap
    drop
    swap
    drop
    stbp -8
    jmp .id4
.id4:
    ldbp -4
    ldbp -8
    add
    push 65535  ; mask for int
    band        ; apply type mask
    stbp -12
    jmp .id5
.id5:
    ldbp -4
    call int_to_byte
    call send_byte
    drop
    jmp .id6
.id6:
    ldbp -8
    call int_to_byte
    call send_byte
    drop
    jmp .id7
.id7:
    ldbp -12
    call int_to_byte
    call send_byte
    drop
    jmp .id1
.out:
    ret

main:
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    call test_send_one_byte
    jmp .id3
.id3:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id4
.id4:
    call test_builtin_func
    jmp .id5
.id5:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id6
.id6:
    call test_math
    jmp .id7
.id7:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id8
.id8:
    push 5 ; dec = 5
    call test_if
    drop
    jmp .id9
.id9:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id10
.id10:
    push 3 ; dec = 3
    call test_if
    drop
    jmp .id11
.id11:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id12
.id12:
    push 4 ; dec = 4
    call test_if
    drop
    jmp .id13
.id13:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id14
.id14:
    push 0 ; dec = 0
    call test_req
    drop
    jmp .id15
.id15:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id16
.id16:
    push 5 ; dec = 5
    call test_req
    drop
    jmp .id17
.id17:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id18
.id18:
    push 9 ; dec = 9
    call test_while
    drop
    jmp .id19
.id19:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id20
.id20:
    push 9 ; dec = 9
    call test_break
    drop
    jmp .id21
.id21:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id22
.id22:
    push 50 ; dec = 50
    push 49 ; dec = 49
    push 1 ; bool = true
    call test_many_operands
    drop
    drop
    drop
    jmp .id23
.id23:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id24
.id24:
    push 10 ; dec = 10
    call test_mas
    drop
    jmp .id25
.id25:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id26
.id26:
    push 0  ; for return value
    call test_return
    call int_to_byte
    call send_byte
    drop
    jmp .id27
.id27:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id28
.id28:
    call test_calculate_complex
    jmp .id29
.id29:
    push 10 ; hex = 0x0A
    call send_byte
    drop
    jmp .id30
.id30:
    push 0  ; for return value
    call test_return_2
    call int_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id1
.out:
    ret
