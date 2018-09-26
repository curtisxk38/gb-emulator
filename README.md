A GameBoy emulator written in python.

## Install
```
pip install pygame
```

## Run
Start running with a given rom:
```
python3 main.py -r path_to_rom.gb
```
For more options see:
```
python3 main.py --help
```

## Generating instruction chart

You should not have to generate the instruction chart, since `opcode_details.json` is provided in this repository.

However, if you are curious, `gen_instr_chart.py` was used to make it.

But the website that is scraped in `gen_instr_chart.py` has a few errors, so after you run it, you have to make a few edits to `opcode_details.json` manually:

```
LD A,(C) has a length of 1 not 2
LD (C), A has a length of 1 not 2
```
