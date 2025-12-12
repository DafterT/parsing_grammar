[section code, code]

ldsp 0xFFFC      ; even-aligned stack top (dword-aligned)
ldhp 0x0000      ; init heap base (example)
setbp            ; establish caller bp before first call

call main
hlt

main: 
    ; allocate array: len=4 elements, elem size = 4 bytes (size_shift=2)
    push 0           ; reserve local slot at [bp-4] (array ptr)
    push 0           ; reserve local slot at [bp-8] (temp value)

    push 4           ; arg0 = length
    push 2           ; arg1 = size_shift (2 => 4B)
    call alloc       ; returns heap address in [bp+8] -> TOS after ret
    stbp -4          ; store ptr into local slot, pop it

    ; store value 0x11223344 into element index 1 (elem size 4)
    ldbp -4          ; base ptr
    push 1           ; index
    push 2           ; size_shift
    shl              ; offset = index << size_shift (4 bytes)
    add              ; addr = base + offset
    push 0x11223345  ; value
    store            ; write 4 bytes

    ; load back element index 1 and output all 4 bytes low->high
    ldbp -4          ; base ptr
    push 1
    push 2
    shl
    add              ; addr
    load             ; value on TOS (32-bit)
    stbp -8          ; save value into temp slot, pop

    ; byte 0
    ldbp -8
    outb
    ; byte 1
    ldbp -8
    push 8
    shr
    stbp -8          ; update temp
    ldbp -8
    outb
    ; byte 2
    ldbp -8
    push 8
    shr
    stbp -8
    ldbp -8
    outb
    ; byte 3
    ldbp -8
    push 8
    shr
    stbp -8
    ldbp -8
    outb
    ret

; alloc(len, size_shift): element size = 1 << size_shift (0->1B,1->2B,2->4B)
; returns: pointer to allocated block (old hp); advances hp by len * elem_size
alloc:
     ; frame layout: [bp] saved bp, [bp+4] return, [bp+8] size_shift, [bp+12] len
     ldbp 12       ; push len
     ldbp 8        ; push size_shift
     shl           ; total_bytes = len << size_shift
     pushhp        ; old hp -> will be return value
     stbp 8        ; store return value at [bp+8], pop old hp
     addhp         ; hp = hp + total_bytes, pop total
     ret