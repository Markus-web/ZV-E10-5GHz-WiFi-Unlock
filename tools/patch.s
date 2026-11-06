.syntax unified
.arm
.global _start
.section .text
_start:
    ldr r0, =filename
    mov r1, #2
    mov r2, #0
    mov r7, #5
    svc #0
    cmp r0, #0
    blt fail_open
    mov r4, r0
    mov r0, r4
    ldr r1, =byte_offset
    ldr r1, [r1]
    mov r2, #0
    mov r7, #19
    svc #0
    cmp r0, #0
    blt fail_seek
    mov r0, r4
    ldr r1, =buf
    mov r2, #1
    mov r7, #3
    svc #0
    cmp r0, #1
    bne fail_read
    ldr r1, =buf
    ldrb r1, [r1]
    ldr r2, =expected_byte
    ldrb r2, [r2]
    cmp r1, r2
    bne fail_compare
    mov r0, r4
    ldr r1, =byte_offset
    ldr r1, [r1]
    mov r2, #0
    mov r7, #19
    svc #0
    cmp r0, #0
    blt fail_seek
    mov r0, r4
    ldr r1, =replacement_byte
    mov r2, #1
    mov r7, #4
    svc #0
    cmp r0, #1
    bne fail_write
    mov r0, r4
    mov r7, #118
    svc #0
    cmp r0, #0
    bne fail_sync
    mov r0, r4
    ldr r1, =byte_offset
    ldr r1, [r1]
    mov r2, #0
    mov r7, #19
    svc #0
    cmp r0, #0
    blt fail_seek
    mov r0, r4
    ldr r1, =buf
    mov r2, #1
    mov r7, #3
    svc #0
    cmp r0, #1
    bne fail_read
    ldr r1, =buf
    ldrb r1, [r1]
    ldr r2, =replacement_byte
    ldrb r2, [r2]
    cmp r1, r2
    bne fail_verify
    mov r0, r4
    mov r7, #6
    svc #0
    mov r0, #0
    b exit
fail_open: mov r0, #10; b exit
fail_seek: mov r0, #11; b exit
fail_read: mov r0, #12; b exit
fail_compare: mov r0, #13; b exit
fail_write: mov r0, #14; b exit
fail_sync: mov r0, #15; b exit
fail_verify: mov r0, #16
exit:
    mov r7, #1
    svc #0
.section .data
filename: .asciz "/usr/lib/CautionConfig.so"
.align 2
byte_offset: .word 0xD778E4
expected_byte: .byte 0x20
replacement_byte: .byte 0x1b
buf: .byte 0
