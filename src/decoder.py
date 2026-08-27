import sys
from dataclasses import dataclass, replace

from opcode_loader import Instruction, Opcodes


@dataclass
class Decoder:
    data: bytearray
    prefixed_instructions: Instruction
    instructions: Instruction

    @classmethod
    def create(cls, opcodes: Opcodes, data: bytearray):
        return cls(
            prefixed_instructions=opcodes.prefixed,
            instructions=opcodes.unprefixed,
            data=data,
        )

    def read(self, address: int, count: int = 1) -> int:
        if 0 <= address + count <= len(self.data):
            v = self.data[address : address + count]
            return int.from_bytes(v, sys.byteorder)
        else:
            raise IndexError(f"read {address=} + {count=} is out of range")

    def read_bytes(self, address_start: int, address_end: int) -> bytearray:
        if address_start < address_end and address_start <= len(self.data) and 0 <= address_end:
            return self.data[address_start:address_end]
        else:
            raise IndexError(f"read {address_start=}, {address_end=} is out of range")

    def write(self, address: int, byte_data: bytes):
        byte_data_len = len(byte_data)
        if 0 <= address + byte_data_len <= len(self.data):
            for byte in list(byte_data):
                self.data[address] = byte
                address += 1
        else:
            raise IndexError(f"write {address=} + {byte_data_len=} is out of range")

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

    def print(self, start=0, end=None, dump_to_file=False):
        """
        Prints a hex dump of byte data.
        """

        chunk_size = 16
        end = end if end is not None else len(self.data)
        actual_end = min(end, len(self.data))
        print_data = ""

        for i in range(start, actual_end, chunk_size):
            chunk = self.data[i : i + chunk_size]
            addr = i

            hex_data = " ".join(f"{b:02x}" for b in chunk)
            hex_data = hex_data.ljust(chunk_size * 3 - 1)

            print_data += f"{addr:04x}: {hex_data} |\n"

        if dump_to_file:
            with open("file.txt", "w") as f:
                f.write(print_data)
        else:
            print(print_data)
