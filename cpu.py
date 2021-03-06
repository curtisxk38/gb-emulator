import json


class CPU:
	def __init__(self, memory, is_debug):
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
		# interrupts: Vertical blanking, LCDC (STAT referenced), Timer overflow,
		#  Serio I/O transfer completed, P10-P13 terminal negative edge
		# technically the 2 registers below are actually memory mapped.
		#  so they should be in self.memory, not variables ... ?
		self.interrupt_enable = [True, True, True, True, True]
		self.interrupt_requests = [False, False, False, False, False]
		self.ime = True # interrupt master enable
		self.interrupt_handlers = [0x0040, 0x0048, 0x0050, 0x0058, 0x0060]

		opcode_details_file = "opcode_details.json"

		try:
			with open(opcode_details_file, "r") as f:
				opcodes = json.load(f)
		except FileNotFoundError:
			raise FileNotFoundError("Unable to load {} file. You may need to run gen_instr_chart.py".format(opcode_details_file))
		self.main_opcodes = opcodes["main"]
		self.cb_opcodes = opcodes["cb_prefix"]

		# debug stuff
		self.is_debug = is_debug
		self.stepping = True
		self.breakpoints = []

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
		"""
		Execute one instruction from memory[PC]
		"""
		opcode_details = self.decode()
		self.debug_print(opcode_details["name"])
		length = int(opcode_details["length"])
		
		name = opcode_details["name"].split(" ")
		mnemonic = name[0]
		try:
			args = name[1].split(",")
		except IndexError:
			args = None

		# debug stuff
		if self.pc in self.breakpoints:
			bp_hit = self.breakpoints.index(self.pc)
			self.debug_print("Hit Breakpoint {}".format(bp_hit + 1))
			self.stepping = True

		if self.is_debug and self.stepping:
			# wait for input to before next step
			while True:
				cmd = input(">")
				debug_args = cmd.split(" ")
				if debug_args[0] == "step" or cmd == "":
					break
				elif debug_args[0] == "break" or debug_args[0] == "b":
					if debug_args[1][:2] == "0x":
						addr = int(debug_args[1], 16)
					else:
						addr = int(debug_args[1])
					self.breakpoints.append(addr)
					# breakpoints displayed as indexing at 1
					self.debug_print("Breakpoint {} set at {}".format(len(self.breakpoints), addr))
				elif debug_args[0] == "continue" or debug_args[0] == "c":
					self.stepping = False
					break
				elif debug_args[0] == "delete" or debug_args[0] == "d":
					# breakpoint numbers indexed at 1
					bp = int(debug_args[1]) - 1
					self.breakpoints[bp] = None # pc will never be None
					self.debug_print("Removed breakpoint {}".format(debug_args[1]))
				else:
					try:
						eval(cmd)
					except Exception as e:
						self.debug_print(e)

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
				self.push_val(new_pc)
				# update pc to be immediate
				new_pc = self.get_immediate(1)
		elif mnemonic == "CP":
			if args[0] == "(HL)":
				n = self.memory[self.hl]
			elif args[0] == "d8":
				n = self.get_immediate(1)
			else:
				n = getattr(self, args[0].lower())
			val = self.a - n
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
				if self.is_debug:
					self.debug_print("Jump taken!")
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
			raise NotImplementedError
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
		elif mnemonic == "RET":
			if args is None or self.check_cc(args[0]):
				low = self.memory[self.sp]
				high = self.memory[self.sp + 1]
				stack_val = (high << 8) | low
				self.sp = self.sp + 2
				new_pc = stack_val
				if self.is_debug:
					self.debug_print("Return taken!")
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
		elif mnemonic == "SUB":
			if args[0] == "(HL)":
				n = self.memory[self.hl]
			elif args[0] == "d8":
				n = self.get_immediate(1)
			else:
				n = getattr(self, args[0].lower())
			val = self.a - n
			self.a = val
		elif mnemonic == "XOR":
			if args[0] == "(HL)":
				val = self.a ^ self.memory[self.hl]
			else:
				val = self.a ^ getattr(self, args[0].lower())
			self.a = val
		else:
			self.debug_print("Unkown operation: {}".format(mnemonic))
			raise NotImplementedError

		try:
			self.set_flags(opcode_details["flags"], val)
		except UnboundLocalError:
			# val wasn't set to anything
			# not sure if the next line is correct
			self.set_flags(opcode_details["flags"], None)
		self.pc = new_pc

		self.handle_interupts()

	def handle_interupts(self):
		# if no interrupts are allowed, just return
		if not self.ime:
			return
		# check if any interrupts are requested
		for idx, interrupt in enumerate(self.interrupt_requests):
			if interrupt and self.interrupts_enabled[idx]:
				# reset this interrupt we are handling
				self.interrupt_requests[idx] = False
				# disable interupts
				self.ime = False
				# push old pc to stack
				self.push_val(self.pc)
				# set pc to address of this interrupt handler
				#  aka jump to it
				self.pc = self.interrupt_handlers[idx]
				return

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
		value = (high << 8) | low
		self.sp = self.sp + 2
		setattr(self, reg_name, value)

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
		if self.is_debug:
			self.debug_print("\t{}".format(im))
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
				if i == 0:
					# Z flag
					self.flags[i] = val == 0
				elif i == 1:
					pass
				elif i == 2:
					pass
				elif i == 3:
					# C flag
					self.flags[i] = val > 0xFF

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

	def debug_print(self, to_print):
		if False:
			print(to_print)