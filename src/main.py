import argparse
import hashlib
import sys
from pathlib import Path

from cpu import CPU, InstructionError
from decoder import Decoder
from opcode_loader import load_opcodes
from registers import Registers

BOOT_MD5 = "32fbbd84168d3482956eb3c5051637f5"

parser = argparse.ArgumentParser()
parser.add_argument("--cartridge", help="Path to .gb file")
parser.add_argument("--boot", help="Path to boot .bin file")
args = parser.parse_args()

if args.cartridge == None:
    print("Cartridge file not specified")
    sys.exit(0)

if args.boot == None:
    print("Boot file not specified")
    sys.exit(0)

cartridge = Path(args.cartridge).read_bytes()
boot = Path(args.boot).read_bytes()
md5_hash = hashlib.md5(boot).hexdigest()

if BOOT_MD5 != md5_hash:
    print(
        f"Invalid boot.bin file. Make sure your boot.bin file is a dump of a DMG version of GameBoy.\nMD5\nGOT  {md5_hash}\nNEED {BOOT_MD5}"
    )
    sys.exit(0)

# create memory and load boot and cartridge
memory = bytearray(0xFFFF)
memory[:0x100] = boot[:0x100]
memory[0x100 : len(cartridge)] = cartridge[0x100:]

opcodes = load_opcodes()

decoder = Decoder.create(opcodes=opcodes, data=memory)
cpu = CPU(Registers(0, 0, 0, 0, 0, 0), decoder)

try:
    cpu.run()
except InstructionError as e:
    print(f"CPU exception: {e}")
