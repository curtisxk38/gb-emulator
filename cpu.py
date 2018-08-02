import json
import binascii

import memory

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

		self.flags = {"Z":0,"N":0,"H":0,"C":0}

		self.endianness = "little"

		# 64K RAM
		self.memory = memory.Memory()

		opcode_details_file = "opcode_details.json"

		try:
			with open(opcode_details_file, "r") as f:
				opcodes = json.load(f)
		except FileNotFoundError:
			raise FileNotFoundError("Unable to load {} file. You may need to run gen_instr_chart.py".format(opcode_details_file))
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
			#opcode = self.memory[self.pc:self.pc+length]
			#print("{}:{} -> {}".format(self.pc, length, binascii.hexlify(opcode)))
			
			name = opcode_details["name"].split(" ")
			mnemonic = name[0]
			try:
				args = name[1].split(",")
			except IndexError:
				args = None
			flags = opcode_details["flags"]

			if mnemonic == "LD":
				self.load(args)
			elif mnemonic == "XOR":
				if args[0] == "(HL)":
					raise NotImplementedError
				else:
					val = self.a ^ getattr(self, args[0].lower())
					self.a = val
					self.set_flags(flags, val)

			self.pc += length

	def get_immediate(self, size_in_bytes):
		im = self.memory[self.pc+1:self.pc+1+size_in_bytes]
		im = int.from_bytes(im, self.endianness)
		return im
		

	def load(self, args):
		"""
		Execute Load instructions "LD" 
		(also "LDD", "LDI" mnemonics under different naming schemes)
		"""
		if args[1] == "d16":
			# load 16bit (2byte) immediate
			val = self.get_immediate(2)
		elif args[1] == "d8":
			# load 8 bit (1 byte) immediate
			val = self.get_immediate(1)
		elif args[1][0] == "(":
			# load from memory
			if len(args[1]) == 5 and args[1][3] == "-":
				val = self.memory[self.hl]
				self.hl -= 1
			elif len(args[1]) == 5 and args[1][3] == "+":
				val = self.memory[self.hl]
				self.hl += 1
			else:
				close_paren = args[1].find(")")
				reg_name = args[1][1:close_paren]
				if reg_name == "a16":
					address = self.get_immediate(2)
				else:
					address = getattr(self, reg_name.lower())
				val = self.memory[address]
		else:
			# load from register
			val = getattr(self, args[1].lower())

		if args[0][0] == "(":
			# set memory
			if len(args[0]) == 5 and args[0][3] == "-":
				self.memory[self.hl] = val
				self.hl -= 1
			elif len(args[0]) == 5 and args[0][3] == "+":
				self.memory[self.hl] = val
				self.hl += 1
			else:
				close_paren = args[0].find(")")
				reg_name = args[0][1:close_paren]
				if reg_name == "a16":
					address = self.get_immediate(2)
				else:
					address = getattr(self, reg_name.lower())
				self.memory[address] = val

		else:
			# set register
			setattr(self, args[0].lower(), val)
			print("{} <- {}".format(args[0].lower(), val))

	def set_flags(self, op_flags, val):
		if op_flags[0] == "Z" and val == 0:
			self.flags["Z"] = 1


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

