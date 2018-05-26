

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
