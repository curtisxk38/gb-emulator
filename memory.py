
class Memory:
	def __init__(self):
		self.memory = bytearray([0] * 64 * 2**10)

	def __getitem__(self, key):
		return self.memory[key]

	def __setitem__(self, key, value):
		self.memory[key] = value
