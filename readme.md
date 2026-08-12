# GameBoy Emulator

A simple GameBoy written in Python with hopefully no dependencies other than Python itself.

## Requirements

- Python >= 3.10

## Current Status

Just some printouts

## Run the project

You're gonna need a DMG boot ROM and a cartridge file. Boot ROM you're gonna have to get by yourself and for cartridge just pick one from https://hh.gbdev.io/

```python
python src/main.py --boot=path/to/boot.bin --cartridge=path/to/some_gb_file.gb
```