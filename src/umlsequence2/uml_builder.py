"""Render intermediate UML code to graphic primitives."""
import sys
import re
from subprocess import Popen, PIPE
from collections import OrderedDict, namedtuple

from .config import CONFIG as C
from .svg_renderer import SvgRenderer

RX_COMMENT_POS = re.compile(r'\s*(\S+)\s+(\S+)')
RX_FRAME_OPTS = re.compile(r'\s*(\S+)\s+(\S+)')

Object  = namedtuple('object', 'type index name label ypos row')
Comment = namedtuple('comment', 'x y width height')
Frame   = namedtuple('frame', 'xpos ypos label out')


def error(message, builder):
    print(f'ERROR: {message}:', file=sys.stderr)
    print(f'  {builder.line_nr}: {builder.line}', file=sys.stderr)
    sys.exit(1)


class CheckedOrderedDict(OrderedDict):
    def __init__(self, name, builder):
        self.name = name
        self.builder = builder
        super().__init__()

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            error(f'There is no {self.name} named "{key}"', self.builder)
            sys.exit(1)


class UmlBuilder:
    def __init__(self, lines, out_path, percent_zoom, bg_color):
        self.lines = lines
        self.gfx = SvgRenderer(out_path, percent_zoom, bg_color)
        self.warnings = set()
        self.g = {}

    def run(self):
        self.last_cmd = None
        self.objects_dic = CheckedOrderedDict('object', self)
        self.dead_objects_dic = CheckedOrderedDict('object', self)
        self.activity_dic = CheckedOrderedDict('object', self)
        self.ypos = C.STEP_NORMAL
        self.activity_boxes = []
        self.activity_row = 0
        self.comment_dic = CheckedOrderedDict('comment', self)
        self.frame_dic = CheckedOrderedDict('frame', self)
        self.line_nr = 0
        self.line = None
        self.x_max = 0
        self.y_max = 0

        # execute each line
        for line in self.lines:
            cmd = line[0]
            args = line[1:]
            self.handle_cmd(cmd, args)

        # some commands are rendered on command change, so have a fake cmd
        self.handle_cmd(None, None)

        # close remaining activations
        self.ypos += C.STEP_NORMAL/2
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
        for x, y, w, h in self.activity_boxes:
            self.add(1, self.gfx.rect, x, y, w, h)

        # render graphics
        layers = sorted(self.g.keys())
        for layer in layers:
            for fn, args, kw in self.g[layer]:
                fn(*args, **kw)

        # done
        self.gfx.save()

    def add(self, layer, fn, *args, **kw):
        if layer not in self.g: self.g[layer] = []
        self.g[layer].append((fn, args, kw))

    def set_max(self, x, y):
        self.x_max = max(self.x_max, x)
        self.y_max = max(self.y_max, y)

    def get_x(self, obj, center=False, activity=False):
        x = obj.index * (C.COLUMN_WIDTH + C.COLUMN_SPACING)
        if center:
            x += C.COLUMN_WIDTH / 2
        if activity:
            x += self.nb_active(obj.name) * C.ACTIVITY_WIDTH/2
        return x

    def warn(self, cmd, args, warning):
        text = f'WARNING: {warning}: {cmd} {args}'
        if text not in self.warnings:
            self.warnings.add(text)
            print(text, file=sys.stderr)

    def nb_active(self, name):
        return len(self.activity_dic.get(name, []))

    def compute_object_index(self):
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

    def handle_trace(self, cmd, args):
        if cmd != 'trace': return
        self.line_nr, self.line = args

    def handle_object(self, cmd, args):
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
            if cmd == 'actor': ypos += C.ACTOR_DESCENT
            self.objects_dic[name] = Object(cmd, index, name, label,
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
                    x, y = self.get_x(o, True), self.ypos - C.ACTOR_ASCENT
                    self.add(1, self.gfx.actor, x, y)
                    x, y = self.get_x(o, True), self.ypos + C.ACTOR_LABEL_Y
                    self.add(1, self.gfx.text, x, y, o.label, middle=True)
                else:  # regular object
                    x, y = self.get_x(o), self.ypos
                    self.add(1, self.gfx.rect, x, y,
                             C.COLUMN_WIDTH, C.OBJECT_HEIGHT)
                    x, y = self.get_x(o, True), self.ypos + C.OBJECT_LABEL_Y
                    self.add(1, self.gfx.text, x, y, o.label,
                             middle=True, underline=True)
            self.ypos += C.OBJECT_STEP
            self.activity_row += 1

    def handle_pobject(self, cmd, args):
        return

    def handle_actor(self, cmd, args):
        return

    def handle_oconstraint(self, cmd, args):
        if cmd != 'oconstraint': return
        name, text = args
        o = self.objects_dic[name]
        x, y = self.get_x(o), o.ypos - C.TEXT_MARGIN_Y
        self.add(1, self.gfx.text, x, y, text)
        return True

    def handle_lconstraint(self, cmd, args):
        if cmd != 'lconstraint': return
        name, text = args
        o = self.objects_dic[name]
        x = self.get_x(o, True, True)  + C.TEXT_MARGIN_X
        y = self.ypos - C.TEXT_MARGIN_Y
        self.add(1, self.gfx.text, x, y, text)
        self.ypos += C.STEP_SMALL

    def handle_lconstraint_below(self, cmd, args):
        if cmd != 'lconstraint_below': return
        name, text = args
        o = self.objects_dic[name]
        x = self.get_x(o, True, True) + C.TEXT_MARGIN_X
        y = self.ypos - C.TEXT_MARGIN_Y + C.STEP_SMALL
        self.add(1, self.gfx.text, x, y, text)

    def handle_active(self, cmd, args):
        if cmd == 'active':
            name, = args
            self.activity_dic[name].append(self.ypos)

    def handle_inactive(self, cmd, args):
        if cmd == 'inactive':
            name, = args
            self.inactivate(name)

    def handle_message(self, cmd, args):
        if cmd != 'message': return
        src, dst, txt, asynch, align = args
        self._handle_message(src, dst, txt, False, asynch, align=align)

    def handle_cmessage(self, cmd, args):
        if cmd != 'cmessage': return
        src, dst, label, message, asynch = args
        self.ypos += C.STEP_NORMAL
        save1_y = self.ypos
        self.handle_object('object', (dst, label))  # create
        self.last_cmd = 'object'

        self.handle_object('', None)  # draw
        save2_y = self.ypos
        self.ypos = save1_y - C.OBJECT_STEP/2
        text = message or "«create»"
        self._handle_message(src, dst, text, True, True,
                             shorten=C.COLUMN_WIDTH/2)
        self.ypos = save2_y

    def handle_dmessage(self, cmd, args):
        if cmd != 'dmessage': return
        dst, src = args
        text = "«destroy»"
        self._handle_message(src, dst, text, True, True)
        o = self.objects_dic[dst]
        x = self.get_x(o, True)
        self.add(2, self.gfx.cross, x, self.ypos, C.CROSS_SIZE)

        self.handle_complete('complete', [dst])
        self.ypos += C.STEP_NORMAL


    def handle_rmessage(self, cmd, args):
        if cmd != 'rmessage': return
        src, dst, txt, asynch = args
        self._handle_message(dst, src, txt, True, True)

    def _handle_message(self, src, dst, txt, dashed, asynch,
                        shorten=0, align=''):
        self.ypos += C.STEP_NORMAL
        o1 = self.objects_dic[src]
        o2 = self.objects_dic[dst]
        inv = o1.index >= o2.index
        if inv:
            o1, o2 = o2, o1
            shorten = -shorten

        if src == dst:
            if txt:
                x = self.get_x(o1, True, True) + C.TEXT_MARGIN_X
                y = self.ypos
                self.add(2, self.gfx.text, x, y, txt)

            sgn = 1
            x0 = self.get_x(o1, True, True)
            xa = x0 + C.MESSAGE_SPACING
            xb = x0 + C.COLUMN_WIDTH / 2
            x1 = x0 + C.MESSAGE_SPACING
            step = C.STEP_NORMAL
            xtext = x0 + C.TEXT_MARGIN_Y

            # "U" line
            points = [
                (xa, self.ypos + C.TEXT_MARGIN_Y),
                (xb, self.ypos + C.TEXT_MARGIN_Y),
                (xb, self.ypos + step),
                (x1, self.ypos + step),
            ]
            self.add(2, self.gfx.polyline, points)
            self.ypos += step
        else:
            if txt:
                start = middle = end = False
                if align == '(':
                    x = self.get_x(o1, True, True) + C.TEXT_MARGIN_X
                    start = True
                elif align == ')':
                    x = self.get_x(o2, True) - C.TEXT_MARGIN_Y - shorten
                    end = True
                else:
                    x = (self.get_x(o1, True) + self.get_x(o2, True) - shorten)/2
                    middle = True
                y = self.ypos
                self.add(2, self.gfx.text, x, y, txt,
                         start=start, middle=middle, end=end)
                self.ypos += C.TEXT_MARGIN_Y

            x1 = self.get_x(o1, True, True) + C.MESSAGE_SPACING
            x2 = self.get_x(o2, True) - shorten - C.MESSAGE_SPACING
            x2 -= C.ACTIVITY_WIDTH / 2 if self.nb_active(o2.name) else 0

            # head line
            if inv: x1 += C.MESSAGE_SPACING
            else: x2 -= C.MESSAGE_SPACING
            self.add(2, self.gfx.line, x1, self.ypos, x2, self.ypos, dashed=dashed)
            if inv: x1 -= C.MESSAGE_SPACING
            else: x2 += C.MESSAGE_SPACING

        # arrow head
        self.add(2, self.gfx.arrow_head, x1 if inv else x2, self.ypos,
                 C.ARROW_HEAD_SIZE, not asynch, inv)

    def handle_step(self, cmd, args):
        if cmd != 'step': return
        self.ypos += C.STEP_NORMAL

    def handle_blip(self, cmd, args):
        if cmd != 'blip': return
        name, = args
        self.handle_active('active', [name])
        self.ypos += C.STEP_NORMAL
        self.handle_inactive('inactive', [name])

    def handle_comment(self, cmd, args):
        if cmd != 'comment': return
        name, options, text = args
        comment_name, pos = options

        o = self.objects_dic[name]
        height = len(text.split('\n')) * C.TEXT_HEIGHT + C.TEXT_MARGIN_Y
        x1, y1 = self.get_x(o, True), self.ypos
        x2, y2 = x1, y1 - height/2
        x2offset = C.COLUMN_WIDTH/4

        lines = text.split('\n')
        length = max([self.gfx.get_text_width(l) for l in lines])
        width = length + C.TEXT_MARGIN_X + C.TEXT_DOGEAR

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

        comment = Comment(x2, y2, width, height)
        if comment_name:
            self.comment_dic[comment_name] = comment

        self.add(3, self.gfx.comment_box, x2, y2, width, height, C.TEXT_DOGEAR)
        self.make_comment_connector(x1, y1, comment)

        dx = C.TEXT_MARGIN_X
        dy = C.TEXT_HEIGHT
        for line in lines:
            self.add(3, self.gfx.text, x2+dx, y2+dy, line, light=True)
            dy += C.TEXT_HEIGHT

    def make_comment_connector(self, x, y, comment):
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

    def handle_connect_to_comment(self, cmd, args):
        if cmd != 'connect_to_comment': return
        src, dst = args
        o = self.objects_dic[src]
        c = self.comment_dic[dst]
        x1, y1 = self.get_x(o, True), self.ypos
        self.make_comment_connector(x1, y1, c)

    def handle_begin_frame(self, cmd, args):
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
        self.ypos += C.STEP_SMALL
        o = self.objects_dic[src]
        x = self.get_x(o)
        y = self.ypos
        self.frame_dic[fname] = Frame(x, y, label, out)
        self.ypos += C.STEP_NORMAL

    def handle_end_frame(self, cmd, args):
        if cmd != 'end_frame': return
        fname, dst = args
        o = self.objects_dic.get(dst) or self.dead_objects_dic.get(dst)
        frame = self.frame_dic[fname]
        self.ypos += C.STEP_SMALL
        x1, x2 = frame.xpos, self.get_x(o)
        if x1 > x2: x1, x2 = x2, x1
        x, y = x1, frame.ypos
        w, h = x2 + C.COLUMN_WIDTH - x, self.ypos - y
        if frame.out:
            x -= frame.out
            w += frame.out*2

        self.add(2, self.gfx.rect, x, y, w, h, transparent=True, grey=True)
        d = C.TEXT_DOGEAR
        width = self.gfx.get_text_width(frame.label) + C.TEXT_MARGIN_X*2 + d
        height = C.TEXT_HEIGHT + C.TEXT_MARGIN_Y
        self.add(2, self.gfx.frame_label_box, x, y, width, height, d)

        dx = C.TEXT_MARGIN_X
        dy = C.TEXT_HEIGHT
        self.add(2, self.gfx.text, x+dx, y+dy, frame.label, light=True)
        self.ypos += C.STEP_SMALL

    def handle_delete(self, cmd, args):
        if cmd != 'delete': return
        name, = args
        o = self.objects_dic[name]
        x = self.get_x(o, True)
        self.add(2, self.gfx.cross, x, self.ypos + C.CROSS_SIZE/2, C.CROSS_SIZE)
        self.handle_complete('complete', [name])
        self.ypos += C.STEP_NORMAL

    def handle_complete(self, cmd, args):
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
                y1 = o.ypos + C.STEP_NORMAL
                y2 = self.ypos + .1
                self.add(1, self.gfx.line, x, y1, x, y2,dashed=True, grey=True)
            self.dead_objects_dic[name] = self.objects_dic[name]
            del self.objects_dic[name]

        elif self.last_cmd == 'complete':
            self.ypos += C.STEP_NORMAL

    def handle_cmd(self, cmd, args):
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

    def inactivate(self, name):
        o = self.objects_dic[name]
        x = self.get_x(o, True) + self.nb_active(name)*C.ACTIVITY_WIDTH/2 \
            - C.ACTIVITY_WIDTH
        if not len(self.activity_dic[name]):
            error(f'Cannot inactivate {name} because it is not active', self)
        y = self.activity_dic[name][-1]
        w = C.ACTIVITY_WIDTH
        h = self.ypos-self.activity_dic[name][-1]
        if h == 0:
            self.ypos += C.STEP_NORMAL
            h = self.ypos-self.activity_dic[name][-1]
        self.activity_boxes.append((x, y, w, h))
        self.activity_dic[name].pop()
