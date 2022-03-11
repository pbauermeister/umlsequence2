umlsequence2
============

UML Sequence Diagrams Generator - Commandline tool to generate
diagrams as images in various formats (SVG, PNG, JPG, PDF, etc.) from
source text files.

Source code: https://github.com/pbauermeister/umlsequence2

(This is a pure-Python rewrite of the
https://github.com/pbauermeister/umlsequence project, which was itself
based on umlgraph by Diomidis Spinellis.)

Source text files are in the so-called "umlsequence" syntax.

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

![example](https://raw.githubusercontent.com/pbauermeister/umlsequence2/master/examples/example-04.svg "Example")

Syntax
------

See https://github.com/pbauermeister/umlsequence2/tree/master/doc/README.md.

Examples
--------

See https://github.com/pbauermeister/umlsequence2/tree/master/examples/README.md.

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

```
usage: umlsequence2 [-h] [--output-file OUTPUT_FILE] [--markdown]
                    [--format FORMAT] [--percent-zoom PERCENT_ZOOM]
                    [--background-color BACKGROUND_COLOR] [--debug]
                    [INPUT_FILE]

UML sequence command-line utility, version 2. (C) Copyright 2021 by Pascal
Bauermeister. Converts a textual UML sequence description into a graphic
file. See https://github.com/pbauermeister/umlsequence2/tree/master/examples
for examples.

positional arguments:
  INPUT_FILE            UML sequence input file; if omitted, stdin is used

optional arguments:
  -h, --help            show this help message and exit
  --output-file OUTPUT_FILE, -o OUTPUT_FILE
                        output file name; pass '-' to use stdout; if omitted,
                        use INPUT_FILE base name with '.svg' extension, or
                        stdout
  --markdown, -m        consider snippets between opening marker:
                        ```umlsequence OUTFILE, and closing marker: ```
  --format FORMAT, -f FORMAT
                        output format: any supported by ImageMagick; default
                        is ps
  --percent-zoom PERCENT_ZOOM, -p PERCENT_ZOOM
                        magnification percentage; default is 100
  --background-color BACKGROUND_COLOR, -b BACKGROUND_COLOR
                        background color name (including 'none' for
                        transparent) in web color notation; see
                        https://developer.mozilla.org/en-
                        US/docs/Web/CSS/color_value for a list of valid
                        names; default is white
  --debug               emits debug messages
  --ACTIVITY-WIDTH FLOAT
                        change ACTIVITY_WIDTH (default 0.2)
  --ACTOR-ASCENT FLOAT  change ACTOR_ASCENT (default 0.25)
  --ACTOR-DESCENT FLOAT
                        change ACTOR_DESCENT (default 0.45)
  --ACTOR-LABEL-Y FLOAT
                        change ACTOR_LABEL_Y (default 0.9)
  --ARROW-HEAD-SIZE FLOAT
                        change ARROW_HEAD_SIZE (default 0.3)
  --COLUMN-SPACING FLOAT
                        change COLUMN_SPACING (default 0.25)
  --COLUMN-WIDTH FLOAT  change COLUMN_WIDTH (default 2.75)
  --CROSS-SIZE FLOAT    change CROSS_SIZE (default 0.5)
  --MESSAGE-SPACING FLOAT
                        change MESSAGE_SPACING (default 0.05)
  --OBJECT-HEIGHT FLOAT
                        change OBJECT_HEIGHT (default 0.6)
  --OBJECT-LABEL-Y FLOAT
                        change OBJECT_LABEL_Y (default 0.4)
  --OBJECT-STEP FLOAT   change OBJECT_STEP (default 0.9)
  --STEP-NORMAL FLOAT   change STEP_NORMAL (default 0.6)
  --STEP-SMALL FLOAT    change STEP_SMALL (default 0.3)
  --TEXT-CHAR-WIDTH FLOAT
                        change TEXT_CHAR_WIDTH (default 0.145)
  --TEXT-DOGEAR FLOAT   change TEXT_DOGEAR (default 0.2)
  --TEXT-HEIGHT FLOAT   change TEXT_HEIGHT (default 0.4)
  --TEXT-MARGIN-X FLOAT
                        change TEXT_MARGIN_X (default 0.2)
  --TEXT-MARGIN-Y FLOAT
                        change TEXT_MARGIN_Y (default 0.15)

```
