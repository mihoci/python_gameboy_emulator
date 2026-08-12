from dataclasses import dataclass

from decoder import Decoder
from opcode_loader import Instruction
from registers import REGISTERS, REGISTERS_HIGH, REGISTERS_LOW, Registers

REGISTER_LIST = [*REGISTERS_LOW, *REGISTERS_HIGH, *REGISTERS]


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
            case Instruction(mnemonic="LD"):
                to_register = instruction.operands[0]
                from_register = instruction.operands[1]

                VERIFIED_OPCODES = [0x31, 0x21, 0x32]
                if instruction.opcode not in VERIFIED_OPCODES:
                    print(f"Not yet verified {hex(instruction.opcode)}")

                if from_register.name not in [*REGISTER_LIST, "n16"]:
                    print(f"Unknown opcode name{to_register.name}")

                assert to_register.name in REGISTER_LIST

                if from_register.immediate:
                    value = from_register.value or self.registers[from_register.name]
                elif from_register.name in REGISTER_LIST:
                    value = self.decoder.read(from_register.name)
                else:
                    raise InstructionError(f"Unimplemented operand from {instruction}")

                if to_register.immediate:
                    self.registers[to_register.name] = value
                elif to_register.name in REGISTER_LIST:
                    self.decoder.write(
                        self.registers[to_register.name], value.to_bytes()
                    )
                else:
                    raise InstructionError(f"Unimplemented operand to {instruction}")

                if from_register.increment:
                    self.registers[from_register.name] += 1
                elif from_register.decrement:
                    self.registers[from_register.name] -= 1

                if to_register.increment:
                    self.registers[to_register.name] += 1
                elif to_register.decrement:
                    self.registers[to_register.name] -= 1

            case Instruction(mnemonic="XOR"):
                VERIFIED_OPCODES = [0xAF]
                if instruction.opcode not in VERIFIED_OPCODES:
                    print(f"Not yet verified {hex(instruction.opcode)}")
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
