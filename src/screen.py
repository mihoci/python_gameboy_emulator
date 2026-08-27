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
            viewport_position = self.decoder.read_bytes(0xFF42, 0xFF44)
            vy = viewport_position[0]
            vx = viewport_position[1]

            for y in range(height):
                y_block = ((y + vy) // 8) * 32
                y_block_line = ((y + vy) % 8) * 2
                for x in range(width // 8):
                    bg_map_address = 0x9800 + (x + vx) + y_block
                    bg_map_data = self.decoder.read(bg_map_address)
                    tile_address = 0x8000 + (bg_map_data * 16) + y_block_line
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

            # set line being drawn to 0x90 to indicate vblank period
            self.decoder.write(0xFF44, 0x90.to_bytes())
            root.after(17, update)

        root = tk.Tk()
        label = tk.Label(root)
        label.pack()
        update()
        root.mainloop()
