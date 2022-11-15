"""Convert from SVG to other formats.

All formats supported by reportlab, plus PDF, can be used.

"""
from reportlab.graphics import renderPDF, renderPM, renderPS
from svglib.svglib import svg2rlg


def convert(from_svg_path: str, to_path: str, format: str) -> None:
    drawing = svg2rlg(from_svg_path)
    if format == 'pdf':
        renderPDF.drawToFile(drawing, to_path)
    elif format == 'eps':
        renderPS.drawToFile(drawing, to_path, fmt=format.upper())
    else:
        renderPM.drawToFile(drawing, to_path, fmt=format.upper())
