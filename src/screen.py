import tkinter as tk
from dataclasses import dataclass

from decoder import Decoder


@dataclass
class Screen:
    decoder: Decoder

    def display(self):
        colors = [
            [0x08, 0x18, 0x20],
            [0x32, 0x68, 0x56],
            [0x88, 0xC0, 0x70],
            [0xE0, 0xF8, 0xD0],
        ]

        width = 144
        height = 160

        def update():
            ppm_header = f"P6\n{width} {height}\n255\n".encode()
            pixel_data = bytearray()

            for x in range(height):
                for y in range(width // 8):
                    address = 0x8000 + (y * 16) + (x * 2)
                    block_data = self.decoder.read_bytes(address, address + 2)
                    # if int.from_bytes(block_data):
                    #     self.decoder.print(address, address + 16)
                    if address == 0x8000:
                        block_data = bytearray(b"\x3c\x7e")
                    if address in [0x8002, 0x8004, 0x8006]:
                        block_data = bytearray(b"\x42\x42")
                    if address == 0x8008:
                        block_data = bytearray(b"\x7e\x5e")
                    if address == 0x800A:
                        block_data = bytearray(b"\x7e\x0a")
                    if address == 0x800C:
                        block_data = bytearray(b"\x7c\x56")
                    if address == 0x800E:
                        block_data = bytearray(b"\x38\x7c")

                    byte1 = block_data[0]
                    byte2 = block_data[1]

                    for bit in range(8):
                        lsb = (byte1 >> 7 - bit) & 1
                        msb = ((byte2 >> 7 - bit) & 1) << 1

                        sum = lsb ^ msb
                        pixel_data.extend(colors[sum])

            ppm_data = ppm_header + pixel_data
            img = tk.PhotoImage(data=ppm_data).zoom(4, 4)
            label.config(image=img)
            label.image = img

            root.after(1, update)

        root = tk.Tk()
        label = tk.Label(root)
        label.pack()
        update()
        root.mainloop()
