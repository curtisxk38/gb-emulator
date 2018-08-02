import json

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

		self.flags = [False, False, False, False] # Z, N ,H, C

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

	def update(self, is_debug):
		while True:
			opcode_details = self.decode()
			print(opcode_details["name"])
			length = int(opcode_details["length"])
			
			name = opcode_details["name"].split(" ")
			mnemonic = name[0]
			try:
				args = name[1].split(",")
			except IndexError:
				args = None
			flags = opcode_details["flags"]

			# default new pc
			new_pc = self.pc + length

			if False:
				# temporary until all instructions are implemented
				pass
			elif mnemonic == "BIT":
				bit = int(args[0])
				if args[1][0] == "(":
					to_test = self.memory[self.hl]
				else:
					to_test = getattr(self, args[1].lower())
				val = 1 & (to_test >> bit)
				self.set_flags(flags, val)
			elif mnemonic == "JR":
				if len(args) == 1:
					new_pc = self.pc + self.get_immediate(1)
				elif (args[0] == "Z" and self.flags[0]) \
						or (args[0] == "C" and self.flags[3]) \
						or (args[0] == "NZ" and not self.flags[0]) \
						or (args[0] == "NC" and not self.flags[3]):
						new_pc = self.pc + self.get_immediate(1)
				else:
					raise NotImplementedError


			elif mnemonic == "LD":
				self.load(args)
			elif mnemonic == "XOR":
				if args[0] == "(HL)":
					raise NotImplementedError
				else:
					val = self.a ^ getattr(self, args[0].lower())
					self.a = val
					self.set_flags(flags, val)

			self.pc = new_pc

			if is_debug:
				# wait for input to before next step
				input()

	def get_immediate(self, size_in_bytes):
		im = self.memory[self.pc+1:self.pc+1+size_in_bytes]
		print(im)
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

	def set_flags(self, op_flags, val):
		for i, op_flag in enumerate(op_flags):
			if op_flag == "0":
				self.flags[i] = False
			elif op_flag == "1":
				self.flags[i] = True
			elif op_flag == "-":
				# don't change this flag
				pass
			else:
				if i == 0 and val == 0:
					# Z flag
					self.flags[i] = True
				elif i == 1:
					pass
				elif i == 2:
					pass
				elif i == 3:
					pass


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

