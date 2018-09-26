import json
import argparse

from cpu import CPU
from memory import Memory

import pygame

class Control():
	def __init__(self, config):
		self.MS_PER_UPDATE = 1000.0 / 60
		self.config = config
		self.screen = pygame.display.get_surface()
		
		self.game_done = False
		self.CLOCK = pygame.time.Clock()

		self.memory = Memory()
		self.cpu = CPU(self.memory, self.config.debug)

	def setup(self):
		with open(self.config.rom_path, "rb") as f:
			rom = f.read()
		rom = list(rom)
		self.cpu.memory.load_rom(rom)

	def update(self):
		# update cpu and draw
		self.cpu.update()

		background = pygame.Surface(self.screen.get_size())
		background = background.convert()
		
		pixel_array = pygame.PixelArray(background)

		pixel_array[:]=(255,0,0)
		pixel_array[10:20, 10:20] = (0,0,255)

		del pixel_array

		self.screen.blit(background, (0,0))
		pygame.display.flip()

	def event_loop(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.game_done = True
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					self.game_done = True
			# do stuff

	def main(self):
		lag = 0.0
		while not self.game_done:
			lag += self.CLOCK.tick()

			self.event_loop()
			while lag >= self.MS_PER_UPDATE:
				self.update()
				lag -= self.MS_PER_UPDATE

			pygame.display.update()


def main():
	bootstrap_rom = "DMG_ROM.bin"

	parser = argparse.ArgumentParser()
	parser.add_argument("--rom", "-r", dest="rom_path", help="path to ROM to run", default=bootstrap_rom)
	parser.add_argument("--debug", "-d", dest="debug", action="store_true", help="run in step mode")
	parser.add_argument('args', nargs=argparse.REMAINDER)

	args = parser.parse_args()

	resolution = [160, 144]
	pygame.display.set_mode(resolution)
	pygame.display.set_caption("Gameboy Curtis")

	control = Control(args)
	control.setup()
	control.main()


if __name__ == "__main__":
	main()