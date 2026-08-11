from dataclasses import dataclass

from decoder import Decoder
from opcode_loader import Instruction
from registers import Registers


class InstructionError(Exception):
    pass


@dataclass
class CPU:
    registers: Registers
    decoder: Decoder

    def execute(self, instruction: Instruction):
        # based on https://gekkio.fi/files/gb-docs/gbctr.pdf
        match instruction:
            case Instruction(mnemonic="NOP"):
                pass
            case Instruction(mnemonic="LD", opcode=0x31):
                to_register = instruction.operands[0]
                from_register = instruction.operands[1]

                self.registers[to_register.name] = from_register.value

            case Instruction(mnemonic="XOR", opcode=0xAF):
                to_register = instruction.operands[0]
                from_register = instruction.operands[1]
                value1 = self.registers[to_register.name]
                value2 = self.registers[from_register.name]
                result = value1 ^ value2

                self.registers[to_register.name] = result
                if result == 0:
                    self.registers["z"] = 1

            case _:
                raise InstructionError(f"Cannot execute {instruction}")

    def run(self):
        while True:
            address = self.registers["PC"]
            try:
                next_address, instruction = self.decoder.decode(address)
            except IndexError:
                break

            self.registers["PC"] = next_address
            print(f"{address:04x} {instruction.opcode:02x}  {instruction.print()}")
            self.execute(instruction)
