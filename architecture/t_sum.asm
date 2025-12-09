# Test: push two constants, add, output low byte, halt

[section code, code]

ldsp 0x1000
push 48
push 3
add
outb
hlt
