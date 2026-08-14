from typing import Final

REGISTERS_LOW: Final = {"F": "AF", "C": "BC", "E": "DE", "L": "HL"}
REGISTERS_HIGH: Final = {"A": "AF", "B": "BC", "D": "DE", "H": "HL"}
REGISTERS: Final = {"AF", "BC", "DE", "HL", "PC", "SP"}
FLAGS: Final = {"c": 4, "h": 5, "n": 6, "z": 7}
REGISTER_LIST: Final = [*REGISTERS_LOW, *REGISTERS_HIGH, *REGISTERS]
BIT_MASKS: Final = {
    "0": 0b1,
    "1": 0b10,
    "2": 0b100,
    "3": 0b1000,
    "4": 0b10000,
    "5": 0b100000,
    "6": 0b1000000,
    "7": 0b10000000,
}
