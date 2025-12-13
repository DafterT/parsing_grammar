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

bool:            ; Builtin constructor: bool(size) -> array[] of bool
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 0  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

byte:            ; Builtin constructor: byte(size) -> array[] of byte
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 0  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

int:            ; Builtin constructor: int(size) -> array[] of int
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 1  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

uint:            ; Builtin constructor: uint(size) -> array[] of uint
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 1  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

long:            ; Builtin constructor: long(size) -> array[] of long
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 2  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

ulong:            ; Builtin constructor: ulong(size) -> array[] of ulong
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 2  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

char:            ; Builtin constructor: char(size) -> array[] of char
     ldbp 8             ; load len (size of array) from [bp+8] and push to stack
     push 0  ; push size_shift to stack
     call alloc         ; alloc(size_shift, len) -> result on TOS after ret
     stbp 8             ; store result at [bp+8] and pop
     ret

main: 
    push 0
    jz print

out:
    ret

print:
     push 49
     outb
     jmp out