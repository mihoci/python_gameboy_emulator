from dataclasses import dataclass

from constants import BIT_MASKS, REGISTER_LIST
from decoder import Decoder
from opcode_loader import Instruction
from registers import Registers


class InstructionError(Exception):
    pass


@dataclass
class CPU:
    registers: Registers
    decoder: Decoder

    def run(self):
        while True:
            address = self.registers["PC"]
            try:
                next_address, instruction = self.decoder.decode(address)
            except IndexError:
                break

            self.registers["PC"] = next_address
            print(f"{address:04x} {instruction.opcode:02x}  {instruction.print()}")

            # get instruction implementation
            # instructions implemented based on https://gekkio.fi/files/gb-docs/gbctr.pdf
            execute = getattr(self, instruction.mnemonic, self.instruction_not_found)
            execute(instruction)

    def instruction_not_found(self, instruction: Instruction):
        raise InstructionError(f"Cannot execute {instruction}")

    def BIT(self, instruction: Instruction) -> None:
        bit = instruction.operands[0].name
        target_register = instruction.operands[1]

        if target_register.immediate:
            value = self.registers[target_register.name]
        else:
            value = self.decoder.read(self.registers[target_register.name])

        self.registers["z"] = 1 if value & BIT_MASKS[bit] == 0 else 0
        self.registers["n"] = 0
        self.registers["h"] = 1

    def DI(self, instruction: Instruction) -> None:
        # TODO: implement after figuring out interrupts
        pass

    def JR(self, instruction: Instruction) -> None:
        to_register = instruction.operands[0]

        if len(instruction.operands) == 1:
            self.registers.PC += to_register.value * (
                1 if to_register.value & BIT_MASKS["7"] == 0 else -1
            )
        else:
            match to_register.name:
                case "NZ":
                    condition = self.registers["z"] == 0
                case "Z":
                    condition = self.registers["z"] == 1
                case "NC":
                    condition = self.registers["c"] == 0
                case "N":
                    condition = self.registers["c"] == 1

            if condition:
                self.registers.PC = (
                    self.registers.PC + instruction.operands[1].value
                ) & 0b11111111

    def LD(self, instruction: Instruction) -> None:
        to_register = instruction.operands[0]
        from_register = instruction.operands[1]

        VERIFIED_OPCODES = [0x31, 0x21, 0x32]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        if from_register.name not in [*REGISTER_LIST, "n16"]:
            print(f"Unknown opcode name {to_register.name}")

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
            self.decoder.write(self.registers[to_register.name], value.to_bytes())
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

    def NOP(self, instruction: Instruction) -> None:
        return

    def XOR(self, instruction: Instruction) -> None:
        VERIFIED_OPCODES = [0xAF]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        operand1 = instruction.operands[0]
        operand2 = instruction.operands[1]
        # operand 1 is always A register
        a_value = self.registers[operand1.name]

        if operand2.immediate:
            operand2_value = operand2.value or self.registers[operand2.name]
        else:
            operand2_value = self.decoder.read(self.registers[operand2.name])

        result = a_value ^ operand2_value
        self.registers[operand1.name] = result
        self.registers["n"] = 0
        self.registers["h"] = 0
        self.registers["c"] = 0
        self.registers["z"] = 1 if result == 0 else 0
