[section code, code]

 ldsp 0xFFFE      ; even-aligned stack top
 ldhp 0x8000      ; init heap base (example)
 setbp            ; establish caller bp before first call

 push 48          ; arg0
 push 1           ; arg1
 call main        ; result will be at bp+6 -> becomes TOS after ret
 outb             ; output low byte of result
hlt

main:
     ; frame layout: [bp] saved bp, [bp+2] saved hp, [bp+4] ret, [bp+6] arg1, [bp+8] arg0
     ldbp 6        ; arg1
     ldbp 8        ; arg0
     add           ; sum -> TOS
     stbp 6        ; place return value at [bp+6] (TOS after ret)
    ret