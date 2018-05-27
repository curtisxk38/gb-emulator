import json




def main(rom_path):
	with open(rom_path, "rb") as f:
		rom = f.read()
	decode(rom)

def decode(rom):
	# rom is of type `bytes` which is immutable
	# convert to bytearray so we can pop off entries in it
	rom = bytearray(rom)
	with open("main_ops.json", "r") as f:
		opcodes = json.load(f)
	while True:
		try:
			first_byte = rom.pop(0)
		except IndexError:
			break
		if first_byte == 0xCB:
			raise ValueError("0xCB instructions not implemented")
		try:
			opcode_details = opcodes[str(first_byte)]		
		except KeyError:
			raise KeyError("Unknown opcode prefix: 0x{:x}".format(first_byte))
		print(opcode_details["name"])
		length = int(opcode_details["length"])
		instr = bytearray([first_byte])
		instr.extend(rom[:length-1])

		# remove rest of opcode from rom
		rom = rom[length-1:]

if __name__ == "__main__":
	main("DMG_ROM.bin")