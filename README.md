umlsequence
===========

UML Sequence Diagrams Generator - Commandline tool to generate
diagrams as images in various formats (SVG, PNG, JPG, PDF, etc.) from
source text files.

This is a pure-Python rewrite of the
https://github.com/pbauermeister/umlsequence project which was based
on umlgraph.

Source text files are the so-called "umlsequence" syntax.

Umlsequence syntax example:

    # objects definitions
    E : # External Messages
    T : t:thread
    O : :Toolkit
    P :
    
    # messages and activations
    E  -> T+ a1:run(3)
    T  -> O+ run()
    O        >callbackLoop()
    
    # creation
    O+ :> P  p:Peer
    
    # message with response
    O- => P  result=handleExpose()
    
    # destruction
    O  #> P
    
    # deactivation
    T- O-

![example](https://raw.githubusercontent.com/pbauermeister/umlsequence2/master/examples/tut-4.svg "Example")

Syntax and Examples
-------------------

See http://moinmo.in/ParserMarket/UmlSequence/Examples.

Dependencies
------------

 * Python3
 * Python libraries: svgwrite, reportlab

Installing via pip3
-------------------

```
[sudo] pip3 install umlsequence2
```

Usage
-----

`umlsequence2 -h` says:

    usage: umlsequence2 [-h] [--output-file OUTPUT_FILE] [--format FORMAT]
                        [--percent-zoom PERCENT_ZOOM]
                        [--background-color BACKGROUND_COLOR] [--debug]
                        [INPUT_FILE]
    
    UML sequence command-line utility, version 2. (C) Copyright 2021 by Pascal
    Bauermeister. Converts a textual UML sequence description into an SVG drawing.
    See http://moinmo.in/ParserMarket/UmlSequence/Examples for syntax description
    and examples.
    
    positional arguments:
      INPUT_FILE            UML sequence input file; if omitted, stdin is used
    
    optional arguments:
      -h, --help            show this help message and exit
      --output-file OUTPUT_FILE, -o OUTPUT_FILE
                            output file name; pass '-' to use stdout; if omitted,
                            use INPUT_FILE base name with '.svg' extension, or
                            stdout
      --format FORMAT, -f FORMAT
                            output format: any supported by ImageMagick; default
                            is ps
      --percent-zoom PERCENT_ZOOM, -p PERCENT_ZOOM
                            magnification percentage; default is 100
      --background-color BACKGROUND_COLOR, -b BACKGROUND_COLOR
                            background color name (including 'none' for transparent) in web color notation; see
                            https://developer.mozilla.org/en-US/docs/Web/CSS/color_value for a list of valid names;
                            default is white
      --debug               emits debug messages
