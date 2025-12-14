section .data
a   db 12
b   db 34
buf db 3

section .text
global _start

_start:
    mov al, [a]
    add al, [b]
    xor ah, ah
    mov bl, 10
    div byte bl
    add al, '0'
    mov [buf], al
    add ah, '0'
    mov [buf+1], ah
    mov byte [buf+2], 10
    mov eax, 4
    mov ebx, 1
    mov ecx, buf
    mov edx, 3
    int 0x80
    mov eax, 1
    xor ebx, ebx
    int 0x80
