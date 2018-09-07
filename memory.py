
class Memory:
	def __init__(self):
		# 64 KB of RAM
		self.memory = bytearray([0] * 64 * 2**10)

	def __getitem__(self, key):
		return self.memory[key]

	def __setitem__(self, key, value):
		# byte must be in range	[0, ..., 255]
		value = value % 256
		self.memory[key] = value

	def load_rom(self, rom):
		self.memory[:len(rom)] = rom
