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
            # TODO add background scrolling
            viewport_position = self.decoder.read(0xFF42, 2)
            vy = viewport_position >> 8
            vx = viewport_position & 0xFF
            LCDC = self.decoder.read(0xFF40)

            if viewport_position and vx != 100:
                pass

            for y in range(height):
                y_block = y // 8
                y_block_line = y % 8
                for x in range(width // 8):
                    map_address = 0x9800 + x + (y_block * 32)
                    map_data = self.decoder.read(map_address)
                    tile_address = 0x8000 + (map_data * 16) + (y_block_line * 2)
                    tile_data = self.decoder.read_bytes(tile_address, tile_address + 2)

                    byte1 = tile_data[0]
                    byte2 = tile_data[1]

                    for bit in range(8):
                        lsb = (byte1 >> 7 - bit) & 1
                        msb = ((byte2 >> 7 - bit) & 1) << 1

                        sum = lsb ^ msb
                        pixel_data.extend(colors[sum])

            img = tk.PhotoImage(data=ppm_header + pixel_data).zoom(3, 3)
            label.config(image=img)
            label.image = img

            root.after(17, update)

        root = tk.Tk()
        label = tk.Label(root)
        label.pack()
        update()
        root.mainloop()
