"""Parse input code.

Tokenize and parse input code, and translate to intermediate commands.

"""
import re


def escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Parser:
    RE_MESSAGE = re.compile(
        "([A-Za-z_0-9]+?)([\+\-\#~!]?)"
        " *"
        "(\??-+>"
        "|<-+\??"
        "|\??=+>\??"
        "|\??<=+\??"
        "|\??#+>"
        "|<#+\??"
        "|\??:+>"
        "|<:+\??"
        "|//"
        "|:"
        "|>"
        "|\*"
        "|\["
        "|\]"
        "|\{_?\}"
        ")"
        " *"
        "([#A-Za-z_0-9]*)([\+\-\#~!]?)"
        " *"
        "(.*)")

    #RE_MESSAGE_call = re.compile("([A-Za-z_0-9]+) *(=) *(.*)")
    RE_MESSAGE_call = re.compile("(.*?) *(=) *(.*)")

    RE_OBJ_STATE = re.compile("([A-Za-z_0-9]+[\+\-\#~!]|:)+")

    RE_CONSTRAINT = re.compile("([A-Za-z_0-9]*)([\+\-\#~!]?) *(_?)\{(.*)\}")

    extensions = ['.dot']

    def __init__(self, raw):
        # save call arguments for later use in format()
        self.raw = raw.encode('utf-8')
        self.raw = raw.encode('latin1')
        self.raw = raw

        return

    def parse1(self, lines):
        cmds = []

        self.has_first_step = False
        self.objects = []

        def add_obj(name):
            if name not in self.objects:
                self.objects.append(name)

        def rem_obj(name):
            if name in self.objects:
                self.objects.remove(name)

        def nl2str(text):
            texts = text.split("\\n")
            texts = [t.strip() for t in texts]
            maxlen = max([len(t) for t in texts])
            text1 = ' " " '.join(texts)
            text2 = '\n'.join(texts)
            nlines = len(texts)
            return text1, text2, nlines, maxlen

        def parse_option(text, nb_options):
            if text.startswith("["):
                opts, text = text[1:].split("]", 1)
                options = (opts + ","*nb_options).split(",")[:nb_options]
            else:
                opts = ""
            options = (opts + ","*nb_options).split(",")[:nb_options]
            return [s.strip() for s in options], text.strip()

        def do_line(line_nr, line, level=0):
            if not line.strip():
                return

            def append(args):
                cmds.append(args)

            append(('#####', line_nr, line))
            oline = line

            line = line.strip()
            if not line:
                return

            if line.startswith("#"):
                return

            # try to match: [OBJECT[OP]] [_]{CONSTRAINT}
            terms = Parser.RE_CONSTRAINT.findall(line)
            if terms:
                l, lop, below, r = terms[0]
                r, _, nlines, maxlen = nl2str(r)
                if not l:
                    if not self.objects:
                        fail(line, 'Adding constraint to last object, '
                             'while no object is defined')
                    append(('oconstraint', self.objects[-1], r))
                elif not below:
                    append(('lconstraint', l, r))
                    if lop:
                        do_line(line_nr, l + lop, level + 1)
                else:
                    append(('lconstraint_below', l, r))
                    if lop:
                        do_line(line_nr, l + lop, level + 1)
                return

            # try to match: OBJECT[OP] OP OBJECT[OP] MORE
            terms = Parser.RE_MESSAGE.findall(line)
            if terms:
                l, lop, op, r, rop, edge = terms[0]

                async_head = False
                async_tail = False

                if len(op) > 1:
                    # trim '?'
                    if op[0] == "?":
                        op = op[1:]
                        if op.startswith("<"):
                            async_head = True
                        else:
                            async_tail = True

                    if op[-1] == "?":
                        op = op[:-1]
                        if op.endswith(">"):
                            async_head = True
                        else:
                            async_tail = True

                    # trim long arrows
                    if op[0] == "<":
                        op = op[:2]
                    elif op[-1] == ">":
                        op = op[-2:]

                # transform left arrow to right arrow
                if op[0] == "<":
                    op = op[1:] + ">"
                    l, r = r, l
                    lop, rop = rop, lop

                r2 = ' '.join((r, edge)).strip()

                # escape quotes
                r2 = r2.replace('"', '\\"')

                # implement primitives
                if op == ":"  and r2 and not r2.startswith("#"):
                    append(('object', l, r2))
                    add_obj(l)

                elif op == ":":
                    append(('pobject', l))

                elif op == "*":
                    if r2.startswith("#"):
                        r2 = ""
                    append(('actor', l, r2))
                    add_obj(l)

                elif op == "->":
                    edge, _, nlines, maxlen = nl2str(edge)
                    if edge.startswith("<(>"):
                        append(('message', l, r,
                                     edge[3:].strip(),
                                     async_tail, '('))
                    elif edge.startswith("<)>"):
                        append(('message', l, r,
                                     edge[3:].strip(),
                                     async_tail, ')'))
                    else:
                        append(('message', l, r,
                                     edge,
                                     async_tail, ''))
                    if lop:
                        do_line(line_nr, l + lop, level + 1)
                    if rop:
                        do_line(line_nr, r + rop, level + 1)

                elif op == ">":
                    r2, _, nlines, maxlen = nl2str(r2)
                    append(('active', l))
                    append(('message', l, l, r2, async_tail, ''))
                    append(('inactive', l))
                    if lop:
                        do_line(line_nr, l + lop, level + 1)

                elif op == ":>":
                    append(('cmessage', l, r, edge, None, True))
                    add_obj(r)
                    if lop:
                        do_line(line_nr, l + lop, level + 1)
                    if rop:
                        do_line(line_nr, r + rop, level + 1)

                elif op == "=>":
                    subterms = Parser.RE_MESSAGE_call.findall(edge)
                    if subterms:
                        subterms = subterms[0]

                    # treat case: A => B  result=call(args)
                    if subterms and len(subterms) == 3 and subterms[1] == "=":
                        # short hand for request+result
                        res, op, edge = subterms
                        append(('message', l, r, edge, async_tail, ''))
                        append(('active', r))
                        append(('rmessage', l, r, res, True))
                        append(('inactive', r))

                    # treat case: A => B  result
                    else:
                        # result only
                        append(('rmessage', r, l, edge, True))

                    # post-ops
                    if lop:
                        do_line(line_nr, l + lop, level + 1)
                    if rop:
                        do_line(line_nr, r + rop, level + 1)

                elif op == "#>":
                    append(('dmessage', r, l))
                    rem_obj(r)
                    if lop:
                        do_line(line_nr, l + lop, level + 1)
                    if rop:
                        do_line(line_nr, r + rop, level + 1)

                elif op == "//":
                    r2 = (r + " " + edge).strip()
                    opts, text = parse_option(r2, 2)
                    if not text:
                        append(('connect_to_comment', l, opts[0]))
                    else:
                        text1, text2, nlines, maxlen = nl2str(text)
                        append(('comment', l, opts, text2))
                    if lop:
                        do_line(line_nr, l + lop, level + 1)

                elif op == "[" or op == "]":
                    # Possible syntax:
                    #   frame_name [ object frame_title
                    #           ... activity ...
                    #                object ] frame_name
                    #
                    # Possible syntax:
                    #                object ] frame_name frame_title
                    #           ... activity ...
                    #   frame_name [ object
                    #
                    if edge:
                        if op == "]":
                            r, l = l, r
                        opts, text = parse_option(edge, 1)
                        append(('begin_frame', r, l, opts, text))
                    else:
                        if op == "[":
                            r, l = l, r
                        append(('end_frame', r, l))

                return

            # try to match: OBJECT[OP] [OBJECT[OP] ...]
            terms = Parser.RE_OBJ_STATE.findall(line)
            if terms == line.split():
                for term in terms:
                    l, op = term[:-1], term[-1]
                    if op == "+":
                        append(('active', l))
                    elif op == "-":
                        append(('inactive', l))
                    elif op == "!":
                        append(('blip', l))
                    elif op == "#":
                        rem_obj(l)
                        append(('complete', l))
                    elif op == "~":
                        rem_obj(l)
                        append(('delete', l))
                if ":" in terms:
                    append(('step',))
                return

            # all attemps to match by RE failed => output as-is

        for line_nr, line in enumerate(lines):
            do_line(line_nr+1, line)


        return cmds

    def preprocess(self, raw):
        # preprocess:
        # - remove tabs
        raw = raw.replace("\t", " ")
        # - join lines ending with '\' with the next one
        #   (lazy way, TODO: use regex)
        while raw.find("\\\n ") >= 0:
            raw = raw.replace("\\\n ", "\\\n")
        while raw.find(" \\\n") >= 0:
            raw = raw.replace(" \\\n", "\\\n")
        raw = raw.replace("\\\n", " ")
        lines = raw.split('\n')
        return lines

    def parse(self):
        """
        The parser's entry point
        """

        cmds = self.parse1(self.preprocess(self.raw))
        return cmds, self.raw
