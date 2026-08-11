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

boot = Path(args.boot).read_bytes()
md5_hash = hashlib.md5(boot).hexdigest()

if BOOT_MD5 != md5_hash:
    print(
        f"Invalid boot.bin file. Make sure your boot.bin file is a dump of a DMB version of GameBoy.\nMD5\nGOT  {md5_hash}\nNEED {BOOT_MD5}"
    )
    sys.exit(0)

# load cartridge and overwrite the first 256 bytes with boot
cartridge = bytearray(Path(args.cartridge).read_bytes())
cartridge = boot + cartridge[0x100:]

opcodes = load_opcodes()
cpu = CPU(Registers(0, 0, 0, 0, 0, 0), Decoder.create(opcodes=opcodes, data=cartridge))

try:
    cpu.run()
except InstructionError as e:
    print(f"CPU exception: {e}")


# FIELDS = [
#     (None, "="),  # "Native" endian.
#     (None, "xxxx"),  # 0x100-0x103 (entrypoint)
#     (None, "48x"),  # 0x104-0x133 (nintendo logo)
#     ("title", "15s"),  # 0x134-0x142 (cartridge title)
#     ("cgb", "B"),  # 0x143 (cgb flag)
#     ("new_licensee_code", "H"),  # 0x144-0x145 (new licensee code)
#     ("sgb", "B"),  # 0x146 (sgb `flag)
#     ("cartridge_type", "B"),  # 0x147 (cartridge type)
#     ("rom_size", "B"),  # 0x148 (ROM size)
#     ("ram_size", "B"),  # 0x149 (RAM size)
#     ("destination_code", "B"),  # 0x14A (destination code)
#     ("old_licensee_code", "B"),  # 0x14B (old licensee code)
#     ("mask_rom_version", "B"),  # 0x14C (mask rom version)
#     ("header_checksum", "B"),  # 0x14D (header checksum)
#     ("global_checksum", "H"),  # 0x14E-0x14F (global checksum)
# ]

# CARTRIDGE_HEADER = "".join(format_type for _, format_type in FIELDS)
# CartridgeMetadata = namedtuple(
#     "CartridgeMetadata",
#     [field_name for field_name, _ in FIELDS if field_name is not None],
# )


# def read_cartridge_metadata(buffer, offset: int = 0x100):
#     data = struct.unpack_from(CARTRIDGE_HEADER, buffer, offset=offset)
#     return CartridgeMetadata._make(data)


# print("Cartridge metadata")
# print(read_cartridge_metadata(cartridge))

# print("Instruction 0x150")
# print(instruction.print())

# decoder.disassemble(0x150, 16)
