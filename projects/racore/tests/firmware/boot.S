.section .text.init
.global _start

_start:
    # Initialize stack pointer (set to end of 1MB scratchpad)
    li sp, 0x00100000

    # Call main
    call main

    # Halt the CPU (custom instruction or loop)
1:  j 1b
