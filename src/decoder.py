import sys
from dataclasses import dataclass, replace

from opcode_loader import Instruction, Opcodes


@dataclass
class Decoder:
    data: bytes
    prefixed_instructions: Instruction
    instructions: Instruction

    @classmethod
    def create(cls, opcodes: Opcodes, data: bytes):
        return cls(
            prefixed_instructions=opcodes.prefixed,
            instructions=opcodes.unprefixed,
            data=data,
        )

    def read(self, address: int, count: int = 1):
        if 0 <= address + count <= len(self.data):
            v = self.data[address : address + count]
            return int.from_bytes(v, sys.byteorder)
        else:
            raise IndexError(f"{address=} + {count=} is out of range")

    def decode(self, address: int):
        opcode = self.read(address)
        address += 1

        if opcode == 0xCB:
            opcode = self.read(address)
            address += 1
            instruction = self.prefixed_instructions[opcode]
        else:
            instruction = self.instructions[opcode]

        new_operands = []
        for operand in instruction.operands:
            if operand.bytes is not None:
                value = self.read(address, operand.bytes)
                address += operand.bytes
                new_operands.append(replace(operand, value=value))
            else:
                new_operands.append(operand)

        decoded_instruction = replace(instruction, operands=new_operands)
        return address, decoded_instruction

    def disassemble(self, address: int, count: int):
        for _ in range(count):
            try:
                new_address, instruction = self.decode(address)
                pp = instruction.print()
                print(f"{address:>04X} {pp}")
                address = new_address
            except IndexError as e:
                print(f"ERROR - {e!s}")
                break
