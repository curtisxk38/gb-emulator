import json


class CPU:
	def __init__(self, memory):
		# 8 bit registers
		self.a = 0
		self.b = 0
		self.c = 0
		self.d = 0
		self.e = 0
		self.h = 0
		self.l = 0

		self.sp = 0 # stack pointer
		self.pc = 0 # program counter

		self.flags = [False, False, False, False] # Z, N ,H, C

		self.endianness = "little"

		# 64K RAM
		self.memory = memory
		self.interrupts_enabled = True

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
		"""
		Execute one instruction from memory[PC]
		"""
		opcode_details = self.decode()
		print(opcode_details["name"])
		length = int(opcode_details["length"])
		
		name = opcode_details["name"].split(" ")
		mnemonic = name[0]
		try:
			args = name[1].split(",")
		except IndexError:
			args = None

		# default new pc
		new_pc = self.pc + length

		if False:
			# temporary until all instructions are implemented
			pass
		elif mnemonic == "ADD":
			val = getattr(self, args[0].lower())
			if args[1] == "(HL)":
				val += self.memory[self.hl]
			elif args[1] == "d8":
				val += self.get_immediate(1)
			elif args[1] == "r8":
				val += self.get_immediate(1, signed=True)
			setattr(self, args[0].lower(), val)
		elif mnemonic == "BIT":
			bit = int(args[0])
			if args[1][0] == "(":
				to_test = self.memory[self.hl]
			else:
				to_test = getattr(self, args[1].lower())
			val = 1 & (to_test >> bit)
		elif mnemonic == "CALL":
			if len(args) == 1 or self.check_cc(args[0]):
				# push address of next instruction
				self.push_val(self.pc)
				# update pc to be immediate
				new_pc = self.get_immediate(1)
		elif mnemonic == "DEC":
			if args[0] == "(HL)":
				val = self.memory[self.hl] - 1
				self.memory[self.hl] = val
			else:
				val = getattr(self, args[0].lower()) - 1
				setattr(self, args[0].lower(), val)
		elif mnemonic == "DI":
			self.interrupts_enabled = False
		elif mnemonic == "INC":
			if args[0] == "(HL)":
				val = self.memory[self.hl] + 1
				self.memory[self.hl] = val
			else:
				val = getattr(self, args[0].lower()) + 1
				setattr(self, args[0].lower(), val)
		elif mnemonic == "JR":
			if len(args) == 1 or self.check_cc(args[0]):
				new_pc += self.get_immediate(1, signed=True)
				if is_debug:
					print("Jump taken!")
		elif mnemonic == "LD":
			self.ld(args)
		elif mnemonic == "LDH":
			if args[1] == "A":
				# LDH (a8),A
				self.memory[0xFF00 + self.get_immediate(1)] = self.a
			else:
				# LDH A,(a8)
				self.a = self.memory[0xFF00 + self.get_immediate(1)]
		elif mnemonic == "NOP":
			pass
		elif mnemonic == "POP":
			if args[0] == "AF":
				raise NotImplementedError
			self.pop_val(args[0].lower())
		elif mnemonic == "PUSH":
			if args[0] == "AF":
				raise NotImplementedError
			# get val from a 16bit register
			val = getattr(self, args[0].lower())
			self.push_val(val)
		elif mnemonic == "RL":
			if args[0] == "(HL)":
				val = self.memory[self.hl]
			else:
				val = getattr(self, args[0].lower())
			# save high bit of value 
			bit7 = (val >> 7) & 1
			# rotate to the left
			val = (val << 1) & 0xFF
			# put carry flag value into bit 0
			val = val | int(self.flags[3])
			# save old bit7 into carry flag
			self.flags[3] = bit7
			if args[0] == "(HL)":
				self.memory[self.hl] = val
			else:
				setattr(self, args[0].lower(), val)
		elif mnemonic == "RLA":
			val = self.a
			# save high bit of value 
			bit7 = (val >> 7) & 1
			# rotate to the left
			val = (val << 1) & 0xFF
			# put carry flag value into bit 0
			val = val | int(self.flags[3])
			# save old bit7 into carry flag
			self.flags[3] = bit7
			self.a = val
		elif mnemonic == "XOR":
			if args[0] == "(HL)":
				val = self.a ^ self.memory[self.hl]
			else:
				val = self.a ^ getattr(self, args[0].lower())
			self.a = val
		else:
			print("Unkown operation: {}".format(mnemonic))
			raise NotImplementedError

		try:
			self.set_flags(opcode_details["flags"], val)
		except UnboundLocalError:
			# val wasn't set to anything
			# not sure if the next line is correct
			self.set_flags(opcode_details["flags"], None)
		self.pc = new_pc
		
		if is_debug:
			# wait for input to before next step
			while True:
				cmd = input(">")
				if cmd == "step" or cmd == "":
					break
				else:
					try:
						eval(cmd)
					except Exception as e:
						print(e)

	def ld(self, args):
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

				if reg_name == "C":
					address += 0xFF00
				
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

				if reg_name == "C":
					address += 0xFF00
				
				self.memory[address] = val

		else:
			# set register
			setattr(self, args[0].lower(), val)

	def pop_val(self, reg_name):
		low = self.memory[self.sp]
		high = self.memory[self.sp + 1]
		new = (high << 8) | low
		self.sp = self.sp + 2
		setattr(self, reg_name, new)

	def push_val(self, val):
		"""
		push 16bit value onto stack
		"""
		# split into two 8 bit values
		low, high = self.split_16(val)
		# put on stack
		self.memory[self.sp - 1] = high
		self.memory[self.sp - 2] = low
		# update stack pointer
		self.sp = self.sp - 2

	def get_immediate(self, size_in_bytes, signed=False):
		"""
		Get the immediate value of size_in_bytes for the current instruction
		all instructions have 1 byte for the opcode, so we always start 1 after the PC
		"""
		im = self.memory[self.pc+1:self.pc+1+size_in_bytes]
		print(im)
		im = int.from_bytes(im, self.endianness)

		# the only signed immediates are 1 byte (r8 in JR and ADD instructions)
		#  so we this conversion to a signed value is only made to work for 1 byte signed values
		if signed and im > 127:
			return (256 - im) * -1
		return im
		
	def set_flags(self, op_flags, val):
		"""
		op_flags - list of what flags to set or reset based on the instruction the resultant value
		val - value that resulted from running the current instruction
		Set the flags based on the result of the current instruction
		"""
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
				elif i == 3 and val > 0xFF:
					# C
					self.flags[i] = True

	def check_cc(self, cc):
		"""
		Check whether the condition code parameter is true based on the flags
		"""
		return (cc == "Z" and self.flags[0]) \
			or (cc == "C" and self.flags[3]) \
			or (cc == "NZ" and not self.flags[0]) \
			or (cc == "NC" and not self.flags[3])

	def split_16(self, val_16bit):
		"""
		split 16bit value into 2 8 bit values
		"""
		low = val_16bit & 0x00FF
		high = val_16bit >> 8
		return low, high

	def decode(self):
		"""
		Decode machine code instruction into parsable format
		"""
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

