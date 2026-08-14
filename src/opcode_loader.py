import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Operand:
    immediate: bool
    name: str
    bytes: int
    value: int | None
    adjust: Literal["+", "-"] | None
    increment: bool | None
    decrement: bool | None

    def create(self, value):
        return Operand(
            immediate=self.immediate,
            name=self.name,
            bytes=self.bytes,
            value=value,
            adjust=self.adjust,
            increment=self.increment,
            decrement=self.decrement,
        )

    def print(self):
        if self.adjust is None:
            adjust = ""
        else:
            adjust = self.adjust
        if self.value is not None:
            if self.bytes is not None:
                val = hex(self.value)
            else:
                val = self.value
            v = val
        else:
            v = self.name
        v = v + adjust
        if self.immediate:
            return v
        return f"({v})"


@dataclass
class Instruction:
    opcode: int
    immediate: bool
    operands: list[Operand]
    cycles: list[int]
    bytes: int
    mnemonic: str
    comment: str = ""

    def create(self, operands):
        return Instruction(
            opcode=self.opcode,
            immediate=self.immediate,
            operands=operands,
            cycles=self.cycles,
            bytes=self.bytes,
            mnemonic=self.mnemonic,
        )

    def print(self):
        ops = ", ".join(op.print() for op in self.operands)
        s = f"{self.mnemonic:<8} {ops}"
        if self.comment:
            s = s + f" ; {self.comment:<10}"
        return s


@dataclass
class Opcodes:
    prefixed: list[Instruction] = field(default_factory=list)
    unprefixed: list[Instruction] = field(default_factory=list)


def load_opcodes():
    opcode_json = json.loads(
        (Path(__file__).parent / "opcodes.json").read_text(encoding="utf-8")
    )

    opcodes = Opcodes()
    for opcode_type in opcode_json:
        for opcode in opcode_json[opcode_type]:
            instruction = opcode_json[opcode_type][opcode]
            getattr(opcodes, opcode_type).append(
                Instruction(
                    opcode=int(opcode, base=16),
                    immediate=instruction.get("immediate"),
                    operands=[
                        Operand(
                            immediate=operand.get("immediate"),
                            name=operand.get("name"),
                            bytes=operand.get("bytes", None),
                            value=operand.get("value"),
                            adjust=operand.get("adjust"),
                            increment=operand.get("increment"),
                            decrement=operand.get("decrement"),
                        )
                        for operand in instruction.get("operands")
                    ],
                    cycles=instruction.get("cycles"),
                    bytes=instruction.get("bytes"),
                    mnemonic=instruction.get("mnemonic"),
                )
            )

    return opcodes
