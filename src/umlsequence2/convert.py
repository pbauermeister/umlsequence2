from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM


def convert(from_svg_path, to_path, format):
    drawing = svg2rlg(from_svg_path)
    if format == 'pdf':
        renderPDF.drawToFile(drawing, to_path)
    else:
        renderPM.drawToFile(drawing, to_path, fmt=format.upper())
