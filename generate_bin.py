
import struct

#sample instructions
instructions = [
    0xE3A01004,  #MOV R1, #4
    0xE2812003,  #ADD R2, R1, #3
    0xE5812004,  #STR R2, [R1, #4]
    0xE5913004   #LDR R3, [R1, #4]
]

with open("test.bin", "wb") as f:
    for instr in instructions:
        f.write(struct.pack("<I", instr))
