[section code, code]

ldsp 0xFFFC      ; even-aligned stack top (dword-aligned)
ldhp 0x0000      ; init heap base (example)
setbp            ; establish caller bp before first call

call main
hlt

main: 
    push 0           ; local slot at [bp-4] for result

    ; compute (const1 & const2)
    push 0x00000001  ; const1
    push 0x00000000  ; const2
    bnot_u             ; result -> TOS
    stbp -4          ; save result, pop

    ; output result bytes low -> high
    ldbp -4
    outb             ; byte 0

    ldbp -4
    push 8
    shr
    stbp -4
    ldbp -4
    outb             ; byte 1

    ldbp -4
    push 8
    shr
    stbp -4
    ldbp -4
    outb             ; byte 2

    ldbp -4
    push 8
    shr
    stbp -4
    ldbp -4
    outb             ; byte 3
    ret