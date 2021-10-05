"""Convert from SVG to other formats.

All formats supported by reportlab, plus PDF, can be used.

"""
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM, renderPS


def convert(from_svg_path, to_path, format):
    drawing = svg2rlg(from_svg_path)
    if format == 'pdf':
        renderPDF.drawToFile(drawing, to_path)
    elif format == 'eps':
        renderPS.drawToFile(drawing, to_path, fmt=format.upper())
    else:
        renderPM.drawToFile(drawing, to_path, fmt=format.upper())
