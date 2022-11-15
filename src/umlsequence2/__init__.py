"""Command-line UML sequence diagram generator (version 2). Converts
a textual UML sequence description into a graphic file.

-----

See https://github.com/pbauermeister/umlsequence2/ for information,
syntax and examples.

-----

Orchestrate the work.

Parse commandline args, read input, generate diagram, and convert to
desired output format.
"""
import argparse
import io
import os
import re
import sys
import tempfile
from typing import TextIO

import pkg_resources

from .config import get_config, set_config
from .converter import convert
from .parser import Parser
from .uml_builder import UmlBuilder
from . import error, model

VERSION = pkg_resources.require("umlsequence2")[0].version


def generate_svg(input_fp: TextIO, output_path: str, percent_zoom: int,
                 debug: bool, bgcolor: str) -> None:
    cmds, raw = Parser(input_fp.read()).parse()

    if debug:
        print(raw, file=sys.stderr)
        print("----------", file=sys.stderr)
        for cmd in cmds:
            print(cmd.cmd, ', '.join([repr(a) for a in cmd.args]))

    UmlBuilder(cmds, output_path, percent_zoom, bgcolor).run()


def generate(input_fp: TextIO, output_path: str, percent_zoom: int,
             debug: bool, bgcolor: str, format: str) -> None:
    if debug:
        print(dict(input=input_fp.name,
                   output=output_path,
                   percent_zoom=percent_zoom,
                   debug=debug,
                   bgcolor=bgcolor,
                   format=format,
        ), file=sys.stderr)

    if format == 'svg':
        generate_svg(input_fp, output_path, percent_zoom, debug, bgcolor)
    else:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'file.svg')
            generate_svg(input_fp, path, percent_zoom, debug, bgcolor)
            convert(path, output_path, format)


def parse_args() -> argparse.Namespace:
    description, epilog = [each.strip() for each in __doc__.split('-----')[:2]]

    parser = argparse.ArgumentParser(description=description, epilog=epilog)

    parser.add_argument('INPUT_FILE',
                        action='store',
                        default=None, nargs='?',
                        help='UML sequence input file; '
                        'if omitted, stdin is used')

    parser.add_argument('--output-file', '-o',
                        required=False,
                        help='output file name; pass \'-\' to use stdout; '
                        'if omitted, use INPUT_FILE base name with \'.svg\' '
                        'extension, or stdout')

    parser.add_argument('--markdown', '-m',
                        action='store_true',
                        help='consider snippets between opening marker: '
                        '```umlsequence OUTFILE, and closing marker: ```');

    parser.add_argument('--format', '-f',
                        required=False,
                        default='svg',
                        help='output format: gif, jpg, tiff, bmp, pnm, eps, '
                        'pdf, svg (any supported by reportlab); default is svg')

    parser.add_argument('--percent-zoom', '-p',
                        required=False,
                        default=100, type=int,
                        help='magnification percentage; default is 100')

    parser.add_argument('--background-color', '-b',
                        required=False,
                        default='white',
                        help='background color name (including \'none\' for'
                        ' transparent) in web color notation; see'
                        ' https://developer.mozilla.org/en-US/docs/Web/CSS/color_value'
                        ' for a list of valid names; default is white')

    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='emits debug messages')

    parser.add_argument('--version', '-V',
                        action='store_true',
                        help='print the version and exit')

    # add config float values, e.g. COLUMN_WIDTH as --COLUMN-WIDTH
    cfg = get_config().__dict__
    conf_keys = [k for k, v in cfg.items() if isinstance(v, float)]
    for k in conf_keys:
        parser.add_argument('--' + k.replace('_', '-'),
                            metavar='FLOAT', type=float,
                            help=f'change {k} (default {cfg[k]})')

    args = parser.parse_args()
    args.format = args.format.lower()

    # parse back config modifiers args
    conf_args = {k:args.__dict__[k] for k in conf_keys
                 if args.__dict__[k] is not None}
    if conf_args:
        cfg.update(conf_args)
        set_config(model.Config(**cfg))

    return args


def run(args: argparse.Namespace) -> None:
    # treat input
    if args.INPUT_FILE is None:
        inp = sys.stdin
    else:
        inp = open(args.INPUT_FILE)


    # markdown
    if args.markdown:
        rx = re.compile(r'^```\s*umlsequence\s+(?P<output>.*?)\s*'
                        r'^(?P<src>.*?)^\s*```', re.DOTALL | re.M
        )
        md = inp.read()
        for snippet in rx.finditer(md):
            inp = io.StringIO(snippet['src'])
            name = snippet['output']
            inp.name = name
            generate(inp, name, args.percent_zoom, args.debug,
                     args.background_color, args.format)
            print(f'{sys.argv[0]}: generated {name}', file=sys.stderr)
        return

    # treat output
    if args.output_file is None:
        if args.INPUT_FILE is not None:
            name = os.path.splitext(args.INPUT_FILE)[0] + '.' + args.format
        else:
            name = '-'
    else:
        name = args.output_file

    if name == '-':
        # output to stdout
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'file.svg')
            generate(inp, path, args.percent_zoom, args.debug,
                     args.background_color, args.format)
            with open(path) as f:
                print(f.read())
    else:
        # output to file
        generate(inp, name, args.percent_zoom, args.debug,
                 args.background_color, args.format)


def main() -> None:
    args = parse_args()

    # version?
    if args.version:
        print('umlsequence2', VERSION)
        sys.exit(0)

    try:
        run(args)
    except model.UmlSequenceError as e:
        error.print_error(str(e))
        sys.exit(1)

    sys.exit(0)
