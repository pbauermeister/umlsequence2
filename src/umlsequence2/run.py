#!/usr/bin/env python3

"""Command-line UML sequence diagram generator (version 2).
Converts a textual UML sequence description into a graphic file.
-----
See https://github.com/pbauermeister/umlsequence2/ for information,
syntax and examples.
-----
(C) Copyright 2021 by Pascal Bauermeister.
-----
Usage:
  umlsequence2 -h                 print help for options
  umlsequence2 FILE.umlsequence   generates FILE.svg

See README.md for more information.
"""

import argparse
import io
import os
import re
import sys
import tempfile

from umlsequence2 import generate_svg
from umlsequence2.convert import convert

def run(input_fp, output_path, percent_zoom, debug, bgcolor, format):
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


def main():
    parts = [each.strip() for each in __doc__.split('-----')]
    parser = argparse.ArgumentParser(
        description=parts[0],
        epilog=parts[1])

    parser.add_argument('INPUT_FILE',
                        action="store",
                        default=None, nargs="?",
                        help="UML sequence input file; "
                        "if omitted, stdin is used")

    parser.add_argument('--output-file', '-o',
                        required=False,
                        help="output file name; pass '-' to use stdout; "
                        "if omitted, use INPUT_FILE base name with '.svg' "
                        "extension, or stdout")

    parser.add_argument('--markdown', '-m',
                        action='store_true',
                        help="consider snippets between opening marker: "
                        "```umlsequence OUTFILE, and closing marker: ```");

    parser.add_argument('--format', '-f',
                        required=False,
                        default="svg",
                        help="output format: any supported by ImageMagick; default is ps")

    parser.add_argument('--percent-zoom', '-p',
                        required=False,
                        default=100, type=int,
                        help="magnification percentage; default is 100")

    parser.add_argument('--background-color', '-b',
                        required=False,
                        default="white",
                        help="background color name (including 'none' for"
                        " transparent) in web color notation; see"
                        " https://developer.mozilla.org/en-US/docs/Web/CSS/color_value"
                        " for a list of valid names; default is white")

    parser.add_argument('--debug',
                        action="store_true",
                        default=False,
                        help="emits debug messages")

    args = parser.parse_args()
    args.format = args.format.lower()

    # treat input
    if args.INPUT_FILE is None:
        inp = sys.stdin
    else:
        inp = open(args.INPUT_FILE)


    # markdown
    if args.markdown:
        rx = re.compile(r"^```\s*umlsequence\s+(?P<output>.*?)\s*"
                        r"^(?P<src>.*?)^\s*```", re.DOTALL | re.M
        )
        md = inp.read()
        for snippet in rx.finditer(md):
            inp = io.StringIO(snippet['src'])
            name = snippet['output']
            inp.name = name
            run(inp, name, args.percent_zoom, args.debug, args.background_color,
                args.format)
            print(f'{sys.argv[0]}: generated {name}', file=sys.stderr)
        sys.exit(0)

    # treat output
    if args.output_file is None:
        if args.INPUT_FILE is not None:
            name = os.path.splitext(args.INPUT_FILE)[0] + '.' + args.format
        else:
            name = "-"
    else:
        name = args.output_file

    if name == "-":
        # output to stdout
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'file.svg')
            run(inp, path, args.percent_zoom, args.debug, args.background_color,
                args.format)
            with open(path) as f:
                print(f.read())
    else:
        # output to file
        run(inp, name, args.percent_zoom, args.debug, args.background_color,
            args.format)
    sys.exit(0)

if __name__ == "__main__":
    main()
