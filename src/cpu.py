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
        count = 0
        while True:
            count += 1
            address = self.registers["PC"]
            try:
                next_address, instruction = self.decoder.decode(address)
            except IndexError:
                break

            self.registers["PC"] = next_address
            print(
                f"{count:08d} {address:04x} {instruction.opcode:02x}  {instruction.print()}"
            )

            # get instruction implementation
            # instructions implemented based on https://gekkio.fi/files/gb-docs/gbctr.pdf
            execute = getattr(self, instruction.mnemonic, self.instruction_not_found)
            execute(instruction)

    def get_signed_value(self, value):
        return (value ^ 128) - 128

    def instruction_not_found(self, instruction: Instruction):
        raise InstructionError(f"Cannot execute {instruction}")

    def BIT(self, instruction: Instruction) -> None:
        """
        Tests the bit of the 8-bit register
        """

        bit = instruction.operands[0].name
        target_register = instruction.operands[1]

        if target_register.immediate:
            value = self.registers[target_register.name]
        else:
            value = self.decoder.read(self.registers[target_register.name])

        self.registers["h"] = 1
        self.registers["n"] = 0
        self.registers["z"] = 1 if value & BIT_MASKS[bit] == 0 else 0

    def CALL(self, instruction: Instruction) -> None:
        """
        Conditional function call to the absolute address specified by the 16-bit operand
        """
        VERIFIED_OPCODES = [0xCD]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        to_register = instruction.operands[0]
        condition = True
        if len(instruction.operands) > 1:
            from_register = instruction.operands[1]
            match to_register.name:
                case "NZ":
                    condition = self.registers["z"] == 0
                case "Z":
                    condition = self.registers["z"] == 1
                case "NC":
                    condition = self.registers["c"] == 0
                case "N":
                    condition = self.registers["c"] == 1

        if not condition:
            return

        # decrease stack pointer by 2 and write 2 byte PC register in reverse order to the stack
        self.registers["SP"] -= 2
        self.decoder.write(
            self.registers["SP"], (self.registers["PC"]).to_bytes(2, "little")
        )

        self.registers["PC"] = to_register.value or from_register.value

    def CP(self, instruction: Instruction) -> None:
        """
        Subtracts from the register A the immediate data, address data or register data and updates flags based on the result.
        """
        VERIFIED_OPCODES = [0xFE]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        subtrahend = instruction.operands[1]
        if subtrahend.immediate:
            subtrahend_value = subtrahend.value or self.registers[subtrahend.name]
        else:
            subtrahend_value = self.decoder.read(self.registers[subtrahend.name])

        result = self.registers["A"] - subtrahend_value

        self.registers["c"] = self.registers["A"] < subtrahend_value
        self.registers["h"] = ((self.registers["A"] ^ 1 ^ result) & 0b00010000) >> 4
        self.registers["n"] = 1
        self.registers["z"] = 1 if result == 0 else 0

    def DEC(self, instruction: Instruction) -> None:
        """
        Increments data in the register or at the absolute address specified by the register HL
        """
        VERIFIED_OPCODES = [0x5, 0x3D, 0xD]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        operand = instruction.operands[0]
        bit_mask = 0xFF if len(operand.name) == 1 else 0xFFFF

        if operand.immediate:
            value = self.registers[operand.name]
            result = (value - 1) & bit_mask
            self.registers[operand.name] = result
        else:
            value = self.decoder.read(self.registers[operand.name])
            result = (value - 1) & bit_mask
            self.decoder.write(self.registers[operand.name], result)

        if len(operand.name) == 1 or not operand.immediate:
            self.registers["h"] = ((value ^ 1 ^ result) & 0b00010000) >> 4
            self.registers["n"] = 1
            self.registers["z"] = 1 if result == 0 else 0

    def DI(self, instruction: Instruction) -> None:
        # TODO: implement after figuring out interrupts
        pass

    def INC(self, instruction: Instruction) -> None:
        """
        Increments data in the register or at the absolute address specified by the register HL
        """

        operand = instruction.operands[0]
        bit_mask = 0xFF if len(operand.name) == 1 else 0xFFFF

        if operand.immediate:
            value = self.registers[operand.name]
            result = (value + 1) & bit_mask
            self.registers[operand.name] = result
        else:
            value = self.decoder.read(self.registers[operand.name])
            result = (value + 1) & bit_mask
            self.decoder.write(self.registers[operand.name], result)

        if len(operand.name) == 1 or not operand.immediate:
            self.registers["h"] = ((value ^ 1 ^ result) & 0b00010000) >> 4
            self.registers["n"] = 0
            self.registers["z"] = 1 if result == 0 else 0

    def JR(self, instruction: Instruction) -> None:
        """
        Unconditional or conditional jump to the relative address specified by the signed 8-bit operand
        """

        to_register = instruction.operands[0]

        if len(instruction.operands) == 1:
            self.registers["PC"] += self.get_signed_value(to_register.value)
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
                self.registers["PC"] += self.get_signed_value(
                    instruction.operands[1].value
                )

    def LD(self, instruction: Instruction) -> None:
        """
        Load data from register or address to specified register or address
        """
        VERIFIED_OPCODES = [
            0x31,
            0x21,
            0x32,
            0xE,
            0x3E,
            0x77,
            0x11,
            0x1A,
            0x4F,
            0x6,
            0x22,
            0x7B,
            0xEA,
            0x2E,
            0x67,
            0x57,
            0x1E,
        ]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        to_register = instruction.operands[0]
        from_register = instruction.operands[1]

        if from_register.immediate:
            value = from_register.value or self.registers[from_register.name]
        elif from_register.name in REGISTER_LIST:
            value = self.decoder.read(self.registers[from_register.name])
        else:
            raise InstructionError(f"Unimplemented operand from {instruction}")

        if to_register.immediate:
            self.registers[to_register.name] = value
        else:
            self.decoder.write(
                to_register.value or self.registers[to_register.name], value.to_bytes()
            )

        if from_register.increment:
            self.registers[from_register.name] += 1
        elif from_register.decrement:
            self.registers[from_register.name] -= 1

        if to_register.increment:
            self.registers[to_register.name] += 1
        elif to_register.decrement:
            self.registers[to_register.name] -= 1

    def LDH(self, instruction: Instruction) -> None:
        """
        Load data from register or address to specified register or address. Address is 16-bit obtained by setting the most significant byte to 0xFF and the least significant byte to the value from address or register
        """
        VERIFIED_OPCODES = [0xE2, 0xE0, 0xF0]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        to_register = instruction.operands[0]
        from_register = instruction.operands[1]

        if from_register.immediate:
            value = self.registers[from_register.name]
        else:
            value = self.decoder.read(
                0xFF00 | (from_register.value or self.registers[from_register.name])
            )

        if to_register.immediate:
            self.registers[to_register.name] = value
        else:
            self.decoder.write(
                0xFF00 | (to_register.value or self.registers[to_register.name]),
                value.to_bytes(),
            )

    def NOP(self, instruction: Instruction) -> None:
        """
        No operation
        """

    def POP(self, instruction: Instruction) -> None:
        """
        Pops the data from the stack to the 16-bit register
        """

        self.registers[instruction.operands[0].name] = self.decoder.read(
            self.registers["SP"], 2
        )
        self.registers["SP"] += 2

    def PUSH(self, instruction: Instruction) -> None:
        """
        Push to the stack memory, data from the 16-bit register
        """

        self.registers["SP"] -= 2
        self.decoder.write(
            self.registers["SP"],
            (self.registers[instruction.operands[0].name]).to_bytes(2, "little"),
        )

    def RET(self, instruction: Instruction) -> None:
        """
        Pop two bytes from stack & jump to that address.
        """

        VERIFIED_OPCODES = [0xC9]
        if instruction.opcode not in VERIFIED_OPCODES:
            print(f"Not yet verified {hex(instruction.opcode)}")

        condition = True
        if len(instruction.operands) == 1:
            match instruction.operands[0].name:
                case "NZ":
                    condition = self.registers["z"] == 0
                case "Z":
                    condition = self.registers["z"] == 1
                case "NC":
                    condition = self.registers["c"] == 0
                case "N":
                    condition = self.registers["c"] == 1

        if not condition:
            return

        self.registers["PC"] = self.decoder.read(self.registers["SP"], 2)
        self.registers["SP"] += 2

    def RL(self, instruction: Instruction) -> None:
        """
        Rotates the register or address value left through the carry flag
        """

        operand = instruction.operands[0]
        if operand.immediate:
            value = self.registers[operand.name]
        else:
            value = self.decoder.read(self.registers[operand.name])

        removed_bit = value >> 7
        result = ((value << 1) & 0xFF) | self.registers["c"]

        if operand.immediate:
            self.registers[operand.name] = result
        else:
            self.decoder.write(self.registers[operand.name], result.to_bytes())

        self.registers["c"] = removed_bit
        self.registers["h"] = 0
        self.registers["n"] = 0
        self.registers["z"] = 1 if result == 0 else 0

    def RLA(self, instruction: Instruction) -> None:
        """
        Rotates the A register value left through the carry flag
        """
        value = self.registers["A"]
        removed_bit = value >> 7
        result = ((value << 1) & 0xFF) | self.registers["c"]

        self.registers["A"] = result
        self.registers["c"] = removed_bit
        self.registers["h"] = 0
        self.registers["n"] = 0
        self.registers["z"] = 1 if result == 0 else 0

    def XOR(self, instruction: Instruction) -> None:
        """
        Performs a bitwise XOR operation between the A register and data in a register or at some address
        """
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
        self.registers["c"] = 0
        self.registers["h"] = 0
        self.registers["n"] = 0
        self.registers["z"] = 1 if result == 0 else 0
