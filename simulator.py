
import struct

class RegisterFile:
    def __init__(self):
        self.regs = [0] * 16  #R0–R15 (R15 is PC)
        self.flags = {'N': 0, 'Z': 0, 'C': 0, 'V': 0}

    def get(self, reg): return self.regs[reg]
    def set(self, reg, value): self.regs[reg] = value & 0xFFFFFFFF

    def update_flags(self, result):
        self.flags['Z'] = int(result == 0)
        self.flags['N'] = int((result >> 31) & 1)

    def __str__(self):
        out = '\n'.join([f'R{i}: {hex(r)}' for i, r in enumerate(self.regs)])
        return out + f'\nFlags: {self.flags}'

class Memory:
    def __init__(self, size=4096):
        self.mem = bytearray(size)

    def load_binary(self, file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        for i, b in enumerate(data):
            self.mem[i] = b

    def read_word(self, addr):
        return int.from_bytes(self.mem[addr:addr+4], 'little')

    def write_word(self, addr, value):
        self.mem[addr:addr+4] = value.to_bytes(4, 'little')

def decode(instr):
    opcode = (instr >> 21) & 0xF
    rn = (instr >> 16) & 0xF
    rd = (instr >> 12) & 0xF
    imm = instr & 0xFF
    i_bit = (instr >> 25) & 0x1

    if i_bit == 1:
        if opcode == 0b1101:
            return ("MOV", rd, imm)
        elif opcode == 0b0100:
            return ("ADD", rd, rn, imm)
        elif opcode == 0b0010:
            return ("SUB", rd, rn, imm)
        elif opcode == 0b1010:
            return ("CMP", rn, imm)
        elif opcode == 0b0000:
            return ("AND", rd, rn, imm)
        elif opcode == 0b1100:
            return ("OR", rd, rn, imm)
        elif opcode == 0b0001:
            return ("XOR", rd, rn, imm)
        elif opcode == 0b0110:
            return ("MUL", rd, rn, imm)
        elif opcode == 0b1111:
            return ("MVN", rd, imm)
        elif opcode == 0b1000:
            return ("TST", rn, imm)
        elif opcode == 0b0011:  
            shift_amount = (instr >> 7) & 0x1F
            if (instr >> 5) & 0x3 == 0b00:
                return ("LSL", rd, rn, shift_amount)
            elif (instr >> 5) & 0x3 == 0b01:
                return ("LSR", rd, rn, shift_amount)
    elif ((instr >> 26) & 0b11) == 0b01:
        rd = (instr >> 12) & 0xF
        rn = (instr >> 16) & 0xF
        l_bit = (instr >> 20) & 1
        offset = instr & 0xFFF
        if l_bit == 1:
            return ("LDR", rd, rn, offset)
        else:
            return ("STR", rd, rn, offset)
    elif ((instr >> 24) & 0xF) == 0b1010:
        offset = instr & 0xFFFFFF
        return ("B", offset << 2)
    elif ((instr >> 24) & 0xF) == 0b1011:  
        offset = instr & 0xFFFFFF
        return ("BL", offset << 2)
    
    return ("UNKNOWN",)


def execute(decoded, rf: RegisterFile, mem: Memory):
    op = decoded[0]
    if op == "MOV":
        _, rd, imm = decoded
        rf.set(rd, imm)
        rf.update_flags(imm)
    elif op == "ADD":
        _, rd, rn, imm = decoded
        result = rf.get(rn) + imm
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "SUB":
        _, rd, rn, imm = decoded
        result = rf.get(rn) - imm
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "CMP":
        _, rn, imm = decoded
        result = rf.get(rn) - imm
        rf.update_flags(result)
    elif op == "LDR":
        _, rd, rn, offset = decoded
        addr = rf.get(rn) + offset
        val = mem.read_word(addr)
        rf.set(rd, val)
    elif op == "STR":
        _, rd, rn, offset = decoded
        addr = rf.get(rn) + offset
        mem.write_word(addr, rf.get(rd))
    elif op == "B":
        _, offset = decoded
        rf.set(15, rf.get(15) + offset - 4)
    elif op == "AND":
        _, rd, rn, imm = decoded
        result = rf.get(rn) & imm
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "OR":
        _, rd, rn, imm = decoded
        result = rf.get(rn) | imm
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "XOR":
        _, rd, rn, imm = decoded
        result = rf.get(rn) ^ imm
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "MUL":
        _, rd, rn, imm = decoded
        result = rf.get(rn) * imm
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "MVN":
        _, rd, imm = decoded
        result = ~imm & 0xFFFFFFFF
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "TST":
        _, rn, imm = decoded
        result = rf.get(rn) & imm
        rf.update_flags(result)
    elif op == "LSL":
        _, rd, rn, shift_amount = decoded
        result = (rf.get(rn) << shift_amount) & 0xFFFFFFFF
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "LSR":
        _, rd, rn, shift_amount = decoded
        result = rf.get(rn) >> shift_amount
        rf.set(rd, result)
        rf.update_flags(result)
    elif op == "BL":
        _, offset = decoded
        rf.set(14, rf.get(15) + 4)  
        rf.set(15, rf.get(15) + offset - 4)  
    else:
        print(f"Unknown instruction: {decoded}")

def simulate(file_path):
    mem = Memory()
    mem.load_binary(file_path)

    rf = RegisterFile()
    pc = 0
    file_size = len(open(file_path, "rb").read())
    while pc < file_size:
        instr = mem.read_word(pc)
        rf.set(15, pc)
        decoded = decode(instr)
        print(f"[{hex(pc)}] Executing: {decoded}")
        execute(decoded, rf, mem)
        pc = rf.get(15) + 4
        if decoded[0] == "UNKNOWN":
            break

    print("\n=== Final CPU State ===")
    print(rf)

if __name__ == "__main__":
    simulate("test.bin")
