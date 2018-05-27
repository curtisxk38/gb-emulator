import json

from cpu import CPU


def main(rom_path):
	with open(rom_path, "rb") as f:
		rom = f.read()
	rom = list(rom)
	cpu = CPU()
	cpu.memory[:len(rom)] = rom
	cpu.update()



if __name__ == "__main__":
	main("DMG_ROM.bin")