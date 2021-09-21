import os
import sys

from .renderer import Renderer
from .parser import Parser

def generate_svg(input_fp, output_path, percent_zoom, debug, bgcolor):
    cmds, raw = Parser(input_fp.read()).parse()

    if debug:
        print(raw, file=sys.stderr)
        print("----------", file=sys.stderr)
        for cmd in cmds:
            print(cmd[0], ', '.join([repr(a) for a in cmd[1:]]))

    Renderer(cmds, output_path, percent_zoom, bgcolor).run()
