#!/usr/bin/env python3

def li(rd, imm):
    """LUI + ADDI to load a 32-bit immediate"""
    hi = (imm + 0x800) >> 12
    lo = imm & 0xFFF
    
    lui = (hi << 12) | (rd << 7) | 0x37
    addi = (lo << 20) | (rd << 15) | (rd << 7) | 0x13
    return [lui, addi]

def sw(rs2, rs1, imm):
    """Store Word"""
    imm11_5 = (imm >> 5) & 0x7F
    imm4_0 = imm & 0x1F
    return (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (2 << 12) | (imm4_0 << 7) | 0x23

def lw(rd, rs1, imm):
    """Load Word"""
    return (imm << 20) | (rs1 << 15) | (2 << 12) | (rd << 7) | 0x03

def j(imm):
    """Jump (JAL x0)"""
    imm20 = (imm >> 20) & 1
    imm10_1 = (imm >> 1) & 0x3FF
    imm11 = (imm >> 11) & 1
    imm19_12 = (imm >> 12) & 0xFF
    return (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12) | 0x6F

def gen_bootrom():
    instructions = []
    
    # 0. Set SP = 0x00100000 (1MB scratchpad limit)
    instructions.extend(li(2, 0x00100000))
    
    # 1. Read PtahCore ID from 0x30000000
    instructions.extend(li(5, 0x30000000)) # x5 = 0x30000000
    instructions.append(lw(6, 5, 0))       # x6 = lw(x5, 0) # KAI_ID
    
    # 2. Check if ID == KAI_MAGIC
    instructions.extend(li(7, 0x4B4D54))   # x7 = KAI_MAGIC
    # Wait, need an AND to mask out block ID
    # x8 = 0xFFFFFF
    instructions.extend(li(8, 0xFFFFFF))
    # AND x6, x6, x8
    instructions.append((0 << 25) | (8 << 20) | (6 << 15) | (7 << 12) | (6 << 7) | 0x33) # and x6, x6, x8
    
    # BNE x6, x7, loop
    # branch is complex to encode by hand, just infinite loop for now
    
    # loop:
    instructions.append(j(0)) # j 0
    
    with open("bootrom.hex", "w") as f:
        for ins in instructions:
            f.write(f"{ins:08X}\n")

if __name__ == '__main__':
    gen_bootrom()
