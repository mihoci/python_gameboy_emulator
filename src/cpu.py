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
        # based on https://rgbds.gbdev.io/docs
        match instruction:
            case Instruction(mnemonic="NOP"):
                pass
            case Instruction(mnemonic="RST"):
                pass
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
            print(f"{address:04x}  {instruction.print()}")
            self.execute(instruction)
