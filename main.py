import json
import argparse

from cpu import CPU

def main():
	bootstrap_rom = "DMG_ROM.bin"

	parser = argparse.ArgumentParser()
	parser.add_argument("--rom", "-r", dest="rom_path", help="path to ROM to run", default=bootstrap_rom)
	parser.add_argument("--debug", "-d", dest="debug", action="store_true", help="run in step mode")

	args = parser.parse_args()

	with open(args.rom_path, "rb") as f:
		rom = f.read()
	rom = list(rom)
	cpu = CPU()
	cpu.memory[:len(rom)] = rom
	while True:
		cpu.update(args.debug)



if __name__ == "__main__":
	main()