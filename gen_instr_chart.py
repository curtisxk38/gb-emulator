import requests
from bs4 import BeautifulSoup

import json

def scrape():
	url = "http://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html"
	page = requests.get(url)
	bs = BeautifulSoup(page.content, "html.parser")

	tables = bs.find_all("table")

	main_ops = parse_table(tables[0])
	cb_ops = parse_table(tables[1])

	all_ops = {"main": main_ops, "cb_prefix": cb_ops}

	serialized = json.dumps(all_ops)

	with open("opcode_details.json", "w") as f:
		f.write(serialized)


def parse_table(table):
	main_ops = {}

	# skip the first row, since its just the column labels
	for top_nib, row in enumerate(table.find_all("tr")[1:]):
		# likewise, the first td in the row is the row label
		for bot_nib, op in enumerate(row.find_all("td")[1:]):
			if len(op.contents) > 1:
				name = op.contents[0]
				length, _, duration = op.contents[2].split("\xa0")
				flags = op.contents[4].split(" ")
				opcode = (top_nib << 4) | bot_nib
				main_ops[opcode] = {
					"name": name,
					"length": length,
					"duration": duration,
					"flags": flags,
				}

	return main_ops

if __name__ == "__main__":
	scrape()