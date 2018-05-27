import json


class CPU:
	def __init__(self):
		self.a = 0
		self.b = 0
		self.c = 0
		self.d = 0
		self.e = 0
		self.h = 0
		self.l = 0

		self.sp = 0
		self.pc = 0

		self.flags = 0

		# 64K RAM
		self.memory = [0] * 64 * 2**10

		with open("opcode_details.json", "r") as f:
			opcodes = json.load(f)
		self.main_opcodes = opcodes["main"]
		self.cb_opcodes = opcodes["cb_prefix"]

	@property
	def bc(self):
		return (self.b << 8) | self.c

	@bc.setter
	def bc(self, value):
		self.b = value >> 8
		self.c = value & 0xFF

	@property
	def de(self):
		return (self.d << 8) | self.e

	@de.setter
	def de(self, value):
		self.d = value >> 8
		self.e = value & 0xFF

	@property
	def hl(self):
		return (self.h << 8) | self.l

	@hl.setter
	def hl(self, value):
		self.h = value >> 8
		self.l = value & 0xFF

	def update(self):
		while True:
			opcode_details = self.decode()
			print(opcode_details["name"])
			length = int(opcode_details["length"])
			opcode = self.memory[self.pc:length]
			self.pc += length


	def decode(self):
		first_byte = self.memory[self.pc]
		if first_byte == 0xCB:
			# use 2nd byte of instruction to key the cb_opcodes
			#  2nd byte = byte after 0xCB prefix
			try:
				second_byte = self.memory[self.pc+1]
			except IndexError:
				raise IndexError("Tried to execute 0xCB as last byte of memory?")
			try:
				opcode_details = self.cb_opcodes[str(second_byte)]
			except KeyError:
				raise KeyError("Unkown 0xCB prefix opcode: 0x{:x}".format(second_byte))
		else:
			try:
				opcode_details = self.main_opcodes[str(first_byte)]		
			except KeyError:
				raise KeyError("Unknown opcode prefix: 0x{:x}".format(first_byte))
		return opcode_details

