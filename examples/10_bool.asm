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

test_bool_ops:
    push 0    ; a
    push 0    ; b
    push 0    ; c
    push 0    ; result
.id0:
    jmp .id2
.id1:
    jmp .out
.id2:
    push 1 ; bool = true
    stbp -4
    jmp .id3
.id3:
    push 0 ; bool = false
    stbp -8
    jmp .id4
.id4:
    push 1 ; bool = true
    stbp -12
    jmp .id5
.id5:
    ldbp -4
    not_u
    stbp -16
    jmp .id6
.id6:
    ldbp -16
    call bool_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id7
.id7:
    ldbp -4
    ldbp -8
    land
    stbp -16
    jmp .id8
.id8:
    ldbp -16
    call bool_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id9
.id9:
    ldbp -4
    ldbp -8
    lor
    stbp -16
    jmp .id10
.id10:
    ldbp -16
    call bool_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id11
.id11:
    ldbp -4
    ldbp -8
    land
    ldbp -12
    lor
    stbp -16
    jmp .id12
.id12:
    ldbp -16
    call bool_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id13
.id13:
    ldbp -4
    ldbp -8
    land
    not_u
    stbp -16
    jmp .id14
.id14:
    ldbp -16
    call bool_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
    call send_byte
    drop
    jmp .id15
.id15:
    ldbp -4
    ldbp -8
    not_u
    lor
    stbp -16
    jmp .id16
.id16:
    ldbp -16
    call bool_to_byte
    push 48 ; dec = 48
    add
    push 255  ; mask for byte
    band        ; apply type mask
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
    call test_bool_ops
    jmp .id1
.out:
    ret
