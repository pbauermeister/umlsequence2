"""Render intermediate UML code to graphic primitives."""
from __future__ import annotations

import re
import sys
from collections import OrderedDict
from typing import Any, Callable, TypeVar

from .config import get_config
from .svg_renderer import SvgRenderer

from. import model

RX_COMMENT_POS = re.compile(r'\s*(\S+)\s+(\S+)')
RX_FRAME_OPTS = re.compile(r'\s*(\S+)\s+(\S+)')


def error(message: str, builder: UmlBuilder) -> None:
    raise model.UmlSequenceError(
        f'ERROR: {message}:\n'
        f'  {builder.line_nr}: {builder.line}')


T = TypeVar("T")


class CheckedOrderedDict(OrderedDict[str, T]):
    def __init__(self, name: str, builder: UmlBuilder):
        self.name = name
        self.builder = builder
        super().__init__()

    def __getitem__(self, key: str) -> T:
        try:
            res = super().__getitem__(key)
        except KeyError:
            error(f'There is no {self.name} named "{key}"', self.builder)
        return res

CODict = CheckedOrderedDict


class UmlBuilder:
    def __init__(self, lines: list[model.Command], out_path: str,
                 percent_zoom: int, bg_color: str) -> None:
        self.lines = lines
        self.gfx = SvgRenderer(out_path, percent_zoom, bg_color)
        self.warnings: set[str] = set()
        self.g: dict[int, Any] = {}  # Any = (fn, args, kw)
        self.cfg = get_config()

    def run(self) -> None:
        self.last_cmd: str = None
        self.objects_dic: CODict[model.Object] = CODict('object', self)
        self.dead_objects_dic: CODict[model.Object] = CODict('object', self)
        self.activity_dic: CODict[list[float]] = CODict('object', self)
        self.ypos = self.cfg.STEP_NORMAL
        self.activity_boxes: list[model.Rectangle] = []
        self.activity_row = 0
        self.comment_dic: CODict[model.Comment] = CODict('comment', self)
        self.frame_dic: CODict[model.Frame] = CODict('frame', self)
        self.line_nr = 0
        self.line = None
        self.x_max = 0.
        self.y_max = 0.

        # execute each line
        for line in self.lines:
            cmd = line.cmd
            args = line.args
            self.handle_cmd(cmd, args)

        # some commands are rendered on command change, so have a fake cmd
        self.handle_cmd(None, None)

        # close remaining activations
        self.ypos += self.cfg.STEP_NORMAL/2
        for name, stack in self.activity_dic.items():
            for i in range(len(stack)):
                self.inactivate(name)

        # complete remaining objects
        names = list(self.objects_dic.keys())
        for name in names:
            o = self.objects_dic[name]
            self.handle_complete('complete', [name])

        # draw activations in reverse order
        self.activity_boxes.reverse()
        for rect in self.activity_boxes:
            self.add(1, self.gfx.rect, rect.x, rect.y, rect.w, rect.h)

        # render graphics
        layers = sorted(self.g.keys())
        for layer in layers:
            for fn, args, kw in self.g[layer]:
                fn(*args, **kw)

        # done
        self.gfx.save()

    def add(self, layer: int, fn: Callable[..., Any], *args: Any, **kw: Any) -> None:
        if layer not in self.g: self.g[layer] = []
        self.g[layer].append((fn, args, kw))

    def set_max(self, x: float, y: float) -> None:
        self.x_max = max(self.x_max, x)
        self.y_max = max(self.y_max, y)

    def get_x(self, obj: model.Object, center: bool = False,
              activity: bool = False) -> float:
        x = obj.index * (self.cfg.COLUMN_WIDTH + self.cfg.COLUMN_SPACING)
        if center:
            x += self.cfg.COLUMN_WIDTH / 2
        if activity:
            x += self.nb_active(obj.name) * self.cfg.ACTIVITY_WIDTH/2
        return x

    def warn(self, cmd: str, args: list[Any], warning: str) -> None:
        text = f'WARNING: {warning}: {cmd} {args}'
        if text not in self.warnings:
            self.warnings.add(text)
            print(text, file=sys.stderr)

    def nb_active(self, name: str) -> int:
        return len(self.activity_dic.get(name, []))

    def compute_object_index(self) -> int:
        if not self.objects_dic:
            index = 0
        else:
            index = None
            indices = [o.index for o in self.objects_dic.values()]
            for i in range(len(self.objects_dic)):
                if i not in indices:
                    index = i
                    break
            if index is None:
                index = max(indices) + 1
        return index

    def handle_trace(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'trace': return
        self.line_nr, self.line = args

    def handle_object(self, cmd: str, args: list[Any]) -> None:
        olike = ('object', 'pobject', 'actor')
        if cmd in olike:
            # create objects
            if cmd in ('object', 'actor'):
                name, label = args
            else:
                name, = args
                label = None

            if name in self.objects_dic:
                index = self.objects_dic[name].index
            else:
                index = self.compute_object_index()


            ypos = self.ypos
            if cmd == 'actor': ypos += self.cfg.ACTOR_DESCENT
            self.objects_dic[name] = model.Object(cmd, index, name, label,
                                            ypos, self.activity_row)
            self.activity_dic[name] = []
        elif self.last_cmd in olike:
            # draw objects
            for o in self.objects_dic.values():
                if o.type == 'pobject':
                    continue
                if self.activity_row != o.row:
                    continue
                if o.type == 'actor':
                    x, y = self.get_x(o, True), self.ypos - self.cfg.ACTOR_ASCENT
                    self.add(1, self.gfx.actor, x, y)
                    x, y = self.get_x(o, True), self.ypos + self.cfg.ACTOR_LABEL_Y
                    self.add(1, self.gfx.text, x, y, o.label, middle=True)
                else:  # regular object
                    x, y = self.get_x(o), self.ypos
                    self.add(1, self.gfx.rect, x, y,
                             self.cfg.COLUMN_WIDTH, self.cfg.OBJECT_HEIGHT)
                    x, y = self.get_x(o, True), self.ypos + self.cfg.OBJECT_LABEL_Y
                    self.add(1, self.gfx.text, x, y, o.label,
                             middle=True, underline=True)
            self.ypos += self.cfg.OBJECT_STEP
            self.activity_row += 1

    def handle_pobject(self, cmd: str, args: list[Any]) -> None:
        return

    def handle_actor(self, cmd: str, args: list[Any]) -> None:
        return

    def handle_oconstraint(self, cmd: str, args: list[Any]) -> bool:
        if cmd != 'oconstraint': return False
        name, text = args
        o = self.objects_dic[name]
        x, y = self.get_x(o), o.ypos - self.cfg.TEXT_MARGIN_Y
        self.add(1, self.gfx.text, x, y, text)
        return True

    def handle_lconstraint(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'lconstraint': return
        name, text = args
        o = self.objects_dic[name]
        x = self.get_x(o, True, True)  + self.cfg.TEXT_MARGIN_X
        y = self.ypos - self.cfg.TEXT_MARGIN_Y
        self.add(1, self.gfx.text, x, y, text)
        self.ypos += self.cfg.STEP_SMALL

    def handle_lconstraint_below(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'lconstraint_below': return
        name, text = args
        o = self.objects_dic[name]
        x = self.get_x(o, True, True) + self.cfg.TEXT_MARGIN_X
        y = self.ypos - self.cfg.TEXT_MARGIN_Y + self.cfg.STEP_SMALL
        self.add(1, self.gfx.text, x, y, text)

    def handle_active(self, cmd: str, args: list[Any]) -> None:
        if cmd == 'active':
            name, = args
            self.activity_dic[name].append(self.ypos)

    def handle_inactive(self, cmd: str, args: list[Any]) -> None:
        if cmd == 'inactive':
            name, = args
            self.inactivate(name)

    def handle_message(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'message': return
        src, dst, txt, asynch, align = args
        self._handle_message(src, dst, txt, False, asynch, align=align)

    def handle_cmessage(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'cmessage': return
        src, dst, label, message, asynch = args
        self.ypos += self.cfg.STEP_NORMAL
        save1_y = self.ypos
        self.handle_object('object', [dst, label])  # create
        self.last_cmd = 'object'

        self.handle_object('', None)  # draw
        save2_y = self.ypos
        self.ypos = save1_y - self.cfg.OBJECT_STEP/2
        text = message or "«create»"
        self._handle_message(src, dst, text, True, True,
                             shorten=self.cfg.COLUMN_WIDTH/2)
        self.ypos = save2_y

    def handle_dmessage(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'dmessage': return
        dst, src = args
        text = "«destroy»"
        self._handle_message(src, dst, text, True, True)
        o = self.objects_dic[dst]
        x = self.get_x(o, True)
        self.add(2, self.gfx.cross, x, self.ypos, self.cfg.CROSS_SIZE)

        self.handle_complete('complete', [dst])
        self.ypos += self.cfg.STEP_NORMAL

    def handle_rmessage(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'rmessage': return
        src, dst, txt, asynch = args
        self._handle_message(dst, src, txt, True, True)

    def _handle_message(self, src: str, dst: str, txt: str,
                        dashed: bool, asynch: bool,
                        shorten:float = 0, align: str = '') -> None:
        self.ypos += self.cfg.STEP_NORMAL
        o1 = self.objects_dic[src]
        o2 = self.objects_dic[dst]
        inv = o1.index >= o2.index
        if inv:
            o1, o2 = o2, o1
            shorten = -shorten

        if src == dst:
            if txt:
                x = self.get_x(o1, True, True) + self.cfg.TEXT_MARGIN_X
                y = self.ypos
                self.add(2, self.gfx.text, x, y, txt)

            sgn = 1
            x0 = self.get_x(o1, True, True)
            xa = x0 + self.cfg.MESSAGE_SPACING
            xb = x0 + self.cfg.COLUMN_WIDTH / 2
            x1 = x0 + self.cfg.MESSAGE_SPACING
            step = self.cfg.STEP_NORMAL
            xtext = x0 + self.cfg.TEXT_MARGIN_Y

            # "U" line
            points = [
                (xa, self.ypos + self.cfg.TEXT_MARGIN_Y),
                (xb, self.ypos + self.cfg.TEXT_MARGIN_Y),
                (xb, self.ypos + step),
                (x1, self.ypos + step),
            ]
            self.add(2, self.gfx.polyline, points)
            self.ypos += step
        else:
            if txt:
                start = middle = end = False
                if align == '(':
                    x = self.get_x(o1, True, True) + self.cfg.TEXT_MARGIN_X
                    start = True
                elif align == ')':
                    x = self.get_x(o2, True) - self.cfg.TEXT_MARGIN_Y - shorten
                    end = True
                else:
                    x = (self.get_x(o1, True) + self.get_x(o2, True) - shorten)/2
                    middle = True
                y = self.ypos
                self.add(2, self.gfx.text, x, y, txt,
                         start=start, middle=middle, end=end)
                self.ypos += self.cfg.TEXT_MARGIN_Y

            x1 = self.get_x(o1, True, True) + self.cfg.MESSAGE_SPACING
            x2 = self.get_x(o2, True) - shorten - self.cfg.MESSAGE_SPACING
            x2 -= self.cfg.ACTIVITY_WIDTH / 2 if self.nb_active(o2.name) else 0

            # head line
            if inv: x1 += self.cfg.MESSAGE_SPACING
            else: x2 -= self.cfg.MESSAGE_SPACING
            self.add(2, self.gfx.line, x1, self.ypos, x2, self.ypos, dashed=dashed)
            if inv: x1 -= self.cfg.MESSAGE_SPACING
            else: x2 += self.cfg.MESSAGE_SPACING

        # arrow head
        self.add(2, self.gfx.arrow_head, x1 if inv else x2, self.ypos,
                 self.cfg.ARROW_HEAD_SIZE, not asynch, inv)

    def handle_step(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'step': return
        self.ypos += self.cfg.STEP_NORMAL

    def handle_blip(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'blip': return
        name, = args
        self.handle_active('active', [name])
        self.ypos += self.cfg.STEP_NORMAL
        self.handle_inactive('inactive', [name])

    def handle_comment(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'comment': return
        name, options, text = args
        comment_name, pos = options

        o = self.objects_dic[name]
        height = len(text.split('\n')) * self.cfg.TEXT_HEIGHT + self.cfg.TEXT_MARGIN_Y
        x1, y1 = self.get_x(o, True), self.ypos
        x2, y2 = x1, y1 - height/2
        x2offset = self.cfg.COLUMN_WIDTH/4

        lines = text.split('\n')
        length = max([self.gfx.get_text_width(l) for l in lines])
        width = length + self.cfg.TEXT_MARGIN_X + self.cfg.TEXT_DOGEAR

        pos_terms = RX_COMMENT_POS.findall(pos)
        for key, value in pos_terms:
            value = float(value)
            if key == 'down':
                y2 += value
            elif key == 'up':
                y2 -= value
            elif key == 'left':
                x2offset = -value
                x2 -= width
            elif key == 'right':
                x2offset = value
            else:
                self.warn(cmd, args,
                          f'Unknown layout option "{key} {value}"')
        x2 += x2offset

        comment = model.Comment(x2, y2, width, height)
        if comment_name:
            self.comment_dic[comment_name] = comment

        self.add(3, self.gfx.comment_box, x2, y2, width, height, self.cfg.TEXT_DOGEAR)
        self.make_comment_connector(x1, y1, comment)

        dx = self.cfg.TEXT_MARGIN_X
        dy = self.cfg.TEXT_HEIGHT
        for line in lines:
            self.add(3, self.gfx.text, x2+dx, y2+dy, line, light=True)
            dy += self.cfg.TEXT_HEIGHT

    def make_comment_connector(self, x: float, y: float, comment: model.Comment) -> None:
        if comment.x > x:
            x2 = comment.x
            y2 = comment.y + comment.height/2
        elif comment.x + comment.width < x:
            x2 = comment.x + comment.width
            y2 = comment.y + comment.height/2
        elif comment.y > y:
            x2 = comment.x + comment.width/2
            y2 = comment.y
        elif comment.y + comment.height < y:
            x2 = comment.x + comment.width/2
            y2 = comment.y + comment.height
        else:
            return
        self.add(3, self.gfx.line, x, y, x2, y2, grey=True, dotted=True)

    def handle_connect_to_comment(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'connect_to_comment': return
        src, dst = args
        o = self.objects_dic[src]
        c = self.comment_dic[dst]
        x1, y1 = self.get_x(o, True), self.ypos
        self.make_comment_connector(x1, y1, c)

    def handle_begin_frame(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'begin_frame': return
        src, fname, options, label = args
        out = 0

        if options and options[0]:
            opt_terms = RX_FRAME_OPTS.findall(options[0])
            for key, value in opt_terms:
                value = float(value)
                if key == 'in':
                    out = -value
                elif key == 'out':
                    out = value
                else:
                    self.warn(cmd, args,
                              f'Unknown option "{key} {value}"')
        self.ypos += self.cfg.STEP_SMALL
        o = self.objects_dic[src]
        x = self.get_x(o)
        y = self.ypos
        self.frame_dic[fname] = model.Frame(x, y, label, out)
        self.ypos += self.cfg.STEP_NORMAL

    def handle_end_frame(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'end_frame': return
        fname, dst = args
        o = self.objects_dic.get(dst) or self.dead_objects_dic.get(dst)
        frame = self.frame_dic[fname]
        self.ypos += self.cfg.STEP_SMALL
        x1, x2 = frame.xpos, self.get_x(o)
        if x1 > x2: x1, x2 = x2, x1
        x, y = x1, frame.ypos
        w, h = x2 + self.cfg.COLUMN_WIDTH - x, self.ypos - y
        if frame.out:
            x -= frame.out
            w += frame.out*2

        self.add(2, self.gfx.rect, x, y, w, h, transparent=True, grey=True)
        d = self.cfg.TEXT_DOGEAR
        width = self.gfx.get_text_width(frame.label) + self.cfg.TEXT_MARGIN_X*2 + d
        height = self.cfg.TEXT_HEIGHT + self.cfg.TEXT_MARGIN_Y
        self.add(2, self.gfx.frame_label_box, x, y, width, height, d)

        dx = self.cfg.TEXT_MARGIN_X
        dy = self.cfg.TEXT_HEIGHT
        self.add(2, self.gfx.text, x+dx, y+dy, frame.label, light=True)
        self.ypos += self.cfg.STEP_SMALL

    def handle_delete(self, cmd: str, args: list[Any]) -> None:
        if cmd != 'delete': return
        name, = args
        o = self.objects_dic[name]
        x = self.get_x(o, True)
        self.add(2, self.gfx.cross, x, self.ypos + self.cfg.CROSS_SIZE/2, self.cfg.CROSS_SIZE)
        self.handle_complete('complete', [name])
        self.ypos += self.cfg.STEP_NORMAL

    def handle_complete(self, cmd: str, args: list[Any]) -> None:
        if cmd == 'complete':
            name, = args
            stack = self.activity_dic[name]
            # inactivate all levels
            for i in range(len(stack)):
                self.inactivate(name)
            # draw lifeline
            o = self.objects_dic[name]
            if o.label is not None:
                x = self.get_x(o, True)
                y1 = o.ypos + self.cfg.STEP_NORMAL
                y2 = self.ypos + .1
                self.add(1, self.gfx.line, x, y1, x, y2,dashed=True, grey=True)
            self.dead_objects_dic[name] = self.objects_dic[name]
            del self.objects_dic[name]

        elif self.last_cmd == 'complete':
            self.ypos += self.cfg.STEP_NORMAL

    def handle_cmd(self, cmd: str, args: list[Any]) -> None:
        if cmd == '#####':
            cmd = 'trace'
            self.handle_trace(cmd, args)
            return

        if cmd:
            f = getattr(self, 'handle_' + cmd)  # check we have a handler

        if self.handle_oconstraint(cmd, args):
            return
        self.handle_object(cmd, args)
        self.handle_active(cmd, args)
        self.handle_inactive(cmd, args)
        self.handle_message(cmd, args)
        self.handle_cmessage(cmd, args)
        self.handle_dmessage(cmd, args)
        self.handle_rmessage(cmd, args)
        self.handle_step(cmd, args)
        self.handle_blip(cmd, args)
        self.handle_lconstraint(cmd, args)
        self.handle_lconstraint_below(cmd, args)
        self.handle_comment(cmd, args)
        self.handle_connect_to_comment(cmd, args)
        self.handle_begin_frame(cmd, args)
        self.handle_end_frame(cmd, args)
        self.handle_complete(cmd, args)
        self.handle_delete(cmd, args)

        self.last_cmd = cmd

    def inactivate(self, name: str) -> None:
        o = self.objects_dic[name]
        x = self.get_x(o, True) + self.nb_active(name)*self.cfg.ACTIVITY_WIDTH/2 \
            - self.cfg.ACTIVITY_WIDTH
        if not len(self.activity_dic[name]):
            error(f'Cannot inactivate {name} because it is not active', self)
        y = self.activity_dic[name][-1]
        w = self.cfg.ACTIVITY_WIDTH
        h = self.ypos-self.activity_dic[name][-1]
        if h == 0:
            self.ypos += self.cfg.STEP_NORMAL
            h = self.ypos-self.activity_dic[name][-1]
        self.activity_boxes.append(model.Rectangle(x, y, w, h))
        self.activity_dic[name].pop()
