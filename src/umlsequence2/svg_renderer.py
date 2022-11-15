"""Implement graphic primitives as SVG elements."""
from typing import Sequence

import svgwrite

from .config import get_config


def cm2px(cm: float) -> float:
    return cm * 35.43307
    return round(cm * 35.43307, 2)


def px2cm(px: float) -> float:
    return px / 35.43307
    return round(px / 35.43307, 2)


class SvgRenderer:
    def __init__(self, out_path: str, percent_zoom: int,
                 bg_color: str = 'white'):
        self.dwg = svgwrite.Drawing(filename=out_path, debug=True)
        self.zoom = percent_zoom/100.

        self.shapes = self.dwg.add(self.dwg.g(
            id='shapes',
            transform=f'scale({self.zoom})'
        ))
        self.add = self.shapes.add

        if bg_color!= 'none':
            self.add(self.dwg.rect(insert=(0, 0), size=('100%', '100%'),
                                   fill=bg_color))
        self.x_max: float = 0
        self.y_max: float = 0

    def set_max(self, x: float, y: float) -> None:
        self.x_max = max(self.x_max, x)
        self.y_max = max(self.y_max, y)

    def save(self) -> None:
        # compute and set real size
        w = int(round(self.x_max * self.zoom + .5, 0))
        h = int(round(self.y_max * self.zoom + .5, 0))
        #print(w, h)
        self.dwg.update(dict(width=f'{w}px', height=f'{h}px'))

        #print(self.dwg.tostring())
        self.dwg.save()

    def circle(self, x: float, y: float, r: float) -> None:
        xp, yp = cm2px(x), cm2px(y)
        rp = cm2px(r)
        a = dict(center=(xp, yp),
                 r=rp,
                 fill='white',
                 stroke='black',
                 stroke_width=1)
        self.add(self.dwg.circle(**a))
        self.set_max(xp + rp, yp + rp)

    def polyline(self, points: Sequence[tuple[float, float]],
                 grey: bool = False, filled: bool = False) -> None:
        points_px = [(cm2px(x), cm2px(y)) for x, y in points]
        a = dict(points=points_px,
                 fill='white' if filled else 'none',
                 stroke=get_config().COLOR_GREY if grey else 'black')
        self.add(self.dwg.polyline(**a))
        for xp, yp in points_px:
            self.set_max(xp, yp)

    def polygon(self, points: Sequence[tuple[float, float]]) -> None:
        points_px = [(cm2px(x), cm2px(y)) for x, y in points]
        a = dict(points=points_px, stroke='black', fill='black')
        self.add(self.dwg.polygon(**a))
        for xp, yp in points_px:
            self.set_max(xp, yp)

    def get_text_width(self, text: str) -> float:
        #FIXME
        return get_config().TEXT_CHAR_WIDTH * len(text)

    def text(self, x: float, y: float, text: str, underline: bool = False,
             start: bool = False, middle: bool = False, end: bool = False,
             light: bool = False) -> None:
        xp, yp = cm2px(x), cm2px(y)
        a = dict(fill='#444' if light else 'black',
                 insert=(xp, yp),
                 **get_config().TEXT_FONT)
        l = cm2px(self.get_text_width(text))
        if start or not start and not middle and not end:
            a['text_anchor'] = 'start'
            self.set_max(xp + l, yp)
        if middle:
            a['text_anchor'] = 'middle'
            self.set_max(xp + l/2, yp)
        if end:
            a['text_anchor'] = 'end'
            self.set_max(xp, yp)
        if underline:
            a['text_decoration'] = 'underline'
        self.add(self.dwg.text(text, **a))

    def rect(self, x: float, y: float, w: float, h: float,
             transparent: bool = False,
             grey: bool = False) -> None:
        xp, yp = cm2px(x), cm2px(y)
        wp, hp = cm2px(w), cm2px(h)
        a = dict(insert=(xp, yp),
                 size=(wp, hp),
                 fill='none' if transparent else 'white',
                 stroke=get_config().COLOR_GREY if grey else 'black',
                 stroke_width=1)
        self.add(self.dwg.rect(**a))
        self.set_max(xp + wp, yp + hp)

    def line(self, x1: float, y1: float, x2: float, y2: float,
             grey: bool = False,
             dashed: bool = False,
             dotted: bool = False,
             thick: bool = False) -> None:
        x1p, y1p = cm2px(x1), cm2px(y1)
        x2p, y2p = cm2px(x2), cm2px(y2)
        a = dict(start=(x1p, y1p),
                 end=(x2p, y2p),
                 stroke=get_config().COLOR_GREY if grey else 'black',
                 stroke_width=2 if thick else 1)
        if dashed:
            a['stroke_dasharray'] = '4'
        if dotted:
            a['stroke_dasharray'] = '2'
        self.add(self.dwg.line(**a))
        self.set_max(x1p, y1p)
        self.set_max(x2p, y2p)

    def actor(self, x: float, y: float) -> None:
        r = .13
        self.circle(x, y-r, r)
        vertices = [
            (
                (x - .3, y+.1),
                (x + .3, y+.1),
            ),
            (
                (x, y),
                (x, y + .4),
            ),
            (
                (x - .2, y + .8),
                (x     , y + .4),
                (x + .2, y + .8),
            )
        ]
        for points in vertices:
            self.polyline(points)

    def cross(self, x: float, y: float, size: float) -> None:
        d = size / 2
        x1, x2 = x-d, x+d
        y1, y2 = y-d, y+d
        self.line(x1, y2, x2, y1, thick=True)
        self.line(x1, y1, x2, y2, thick=True)

    def arrow_head(self, x: float, y: float, size: float,
                   full: bool, inv: bool) -> None:
        dx = size if inv else -size
        dy = size / 3
        points = [
            (x+dx, y+dy),
            (x,    y   ),
            (x+dx, y-dy),
        ]

        if full:
            self.polygon(points)
        else:
            self.polyline(points)

    def comment_box(self, x: float, y: float, width: float, height: float,
                    corner_size: float) -> None:
        d = corner_size
        points = [
            (x + width    , y + d),
            (x + width - d, y    ),
            (x            , y    ),
            (x            , y + height),
            (x + width    , y + height),

            (x + width    , y + d),
            (x + width - d, y + d),
            (x + width - d, y    ),
        ]
        self.polyline(points, filled=True, grey=True)

    def frame_label_box(self, x: float, y: float, width: float, height: float,
                        corner_size: float) -> None:
        d = corner_size
        points = [
            (x            , y             ),
            (x + width    , y             ),
            (x + width    , y + height - d),
            (x + width - d, y + height    ),
            (x            , y + height    ),
            (x            , y             ),
        ]
        self.polyline(points, filled=True, grey=True)
