
def main(rom_path):
	with open(rom_path, "rb") as f:
		rom = f.read()
	print(rom)


if __name__ == "__main__":
	main("DMG_ROM.bin")