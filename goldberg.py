#!usr/bin/python

from collections import defaultdict
from re import findall
import numpy as np
from math import sqrt, sin, cos, atan, pi
import random
import Tkinter
import ttk

class gvector(defaultdict):

    def __init__(self, contents):
        defaultdict.__init__(self, int, contents)

    def encode(self):
        return "".join([k+str(self[k]) for k in sorted(self.keys())])

    @classmethod
    def decode(cls, code):
        return cls({p[0]: int(p[1:]) for p in findall("[A-Z][0-9]+", code)})

    @classmethod
    def sum(cls, *args):
        return sum([cls.decode(s) for s in args],cls.decode("")).encode()

    def __add__(self, other):
        return gvector({k:self[k]+other[k] for k in self.keys()+other.keys() if self[k]+other[k] != 0})

    def __mul__(self, factor):
        return gvector({k:self[k]*factor for k in self.keys()})

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + -other

    def __repr__(self):
        return "gvector(" + dict.__repr__(self) + ")"

    def __str__(self):
        return self.encode()

class gnet(dict):

    seed = {
        'A': 'BCDEF',
        'B': 'AFGHC',
        'C': 'ABHID',
        'D': 'ACIJE',
        'E': 'ADJKF',
        'F': 'AEKGB',
        'G': 'FKLHB',
        'H': 'BGLIC',
        'I': 'CHLJD',
        'J': 'DILKE',
        'K': 'EJLGF',
        'L': 'KJIHG'
        }

    basis = { 'A': np.array([1,0,0]) }
    rlat = atan(2)
    rz = cos(rlat)
    rx = sin(rlat)
    for k, t in {'B':0, 'C':1, 'D':2, 'E':3, 'F':4}.iteritems():
        rlong = 2*pi*t/5
        basis[k] = np.array([rz, rx*sin(rlong), rx*cos(rlong)])
    for k, op in {'A':'L', 'B':'J', 'C':'K', 'D':'G', 'E':'H', 'F':'I'}.iteritems():
        basis[op] = -basis[k]

    def __init__(self, M=1, N=0):
        dict.__init__(self,{})

        T = M*M + M*N + N*N

        p, q = M, N
        # gcd
        while q:
            p, q, = q, p % q

        L = T/p
        m, n = M/p, N/p

        done = set()
        doing = set(['A' + str(L)])

        while doing:
            next = set()

            for x in doing:
                X = gvector.decode(x)
                vectors = []
                if len(X) == 1:
                    # vertex
                    k = X.keys()[0]
                    for i in range(len(self.seed[k])):
                        right = self.seed[k][i]
                        left = self.seed[k][i-1]
                        vectors.append(self.step(k, left, right, m, n))
                else:
                    if len(X) == 2:
                        # edge
                        u, v = sorted(X.keys())
                        w = [k for k in self.seed[u] if k in self.seed[v] and u+v in self.seed[k]*2]
                        if not w: raise ValueError(X)
                        w = w[0]
                    elif len(X) == 3:
                        # face
                        u,v,w = X.keys()
                        if v+w not in self.seed[u]*2:
                            v,w = w,v
                    else:
                        raise ValueError(X)

                    du = self.step(u, v, w, m, n)
                    dv = self.step(v, w, u, m, n)
                    dw = self.step(w, u, v, m, n)
                    vectors = [du, -dw, dv, -du, dw, -dv] 

                neighbors = []
                for v in vectors:
                    N = self.fix(X + v).encode()
                    neighbors.append(N)
                    if N not in done and N not in doing:
                        next.add(N)

                self[x] = neighbors
                done.add(x)

            doing = next

        self.faces_by_edge = {}
        self.verts_by_edge = {}
        self.faces_by_vert = {}
        self.edges_by_vert = {}

        for p in self:
            for q in self[p]:
                e = gvector.sum(p, q)
                if e not in self.faces_by_edge:
                    self.faces_by_edge[e] = sorted([p, q])
            for i in range(len(self[p])):
                v = gvector.sum(p, self[p][i-1], self[p][i])
                if v not in self.faces_by_vert:
                    fs = [p, self[p][i-1], self[p][i]]
                    self.faces_by_vert[v] = fs
                    self.edges_by_vert[v] = [ gvector.sum(fs[i-1], fs[i]) for i in range(3) ]
                    for e in self.edges_by_vert[v]:
                        if e not in self.verts_by_edge: self.verts_by_edge[e] = []
                        self.verts_by_edge[e].append(v)

    def step(self, k, left, right, m, n):
        return gvector({k:-m-n, right:m, left:n})

    def fix(self, v):
        negs = [k for k in v.keys() if v[k] < 0]
        if not negs: return v
        if len(negs) == 1:
            neg = negs[0]
            if len(v) != 3: raise ValueError(v)
            pos = [k for k in v.keys() if v[k] > 0]
            flip = [k for k in self.seed[pos[0]] if k in self.seed[pos[1]] and k != neg]
            if not flip: raise ValueError(v)
            flip = flip[0]
            s = -v[neg]
            d = gvector({neg:s, pos[0]:-s, pos[1]:-s, flip:s})
            return v+d
        else:
            raise ValueError(v)

    @classmethod
    def gv_to_v3(cls, s):
        gv = gvector.decode(s)
        v = sum([cls.basis[k]*gv[k] for k in gv.keys()])
        return v/np.sqrt(v.dot(v))

    def faces(self):
        return [p for p in self]

    def edges(self):
        return [p for p in self.faces_by_edge]

    def verts(self):
        return [p for p in self.faces_by_vert]

    def faces_for_face(self, p):
        return self[p]

    def edges_for_face(self, p):
        return [gvector.sum(p, q) for q in self[p]]

    def verts_for_face(self, p):
        return [gvector.sum(p, self[p][i-1], self[p][i]) for i in range(len(self[p]))]

    def faces_for_edge(self, p):
        return self.faces_by_edge[p]

    def verts_for_edge(self, p):
        return self.verts_by_edge[p]

    def faces_for_vert(self, p):
        return self.faces_by_vert[p]

    def edges_for_vert(self, p):
        return self.edges_by_vert[p]

class gcanvas():
    def __init__(self, g, scale=300, zoom=0.85, bg='gray'):
        self.g = g

        self.m = np.array([[1,0,0],[0,1,0],[0,0,1]])
        self.scale=scale
        self.zoom = zoom
        self.bg = bg
        self.drag_xy = None

        self.player_select = None
        self.verb_select = None

        self.width = self.scale * 2
        self.height = self.scale * 2
        self.center = np.array([1.0,1.0])

    def run(self):
        c = Tkinter.Canvas(width=self.width, height=self.height, bg=self.bg)
        c.pack()
        c.bind("<Button-1>", self.click1)
        c.bind("<Button-2>", self.click2)
        c.bind("<ButtonRelease-2>", self.release2)
        c.bind("<B2-Motion>", self.drag2)
        c.winfo_toplevel().resizable(0, 0)

        frame = Tkinter.Frame()

        self.player_var = Tkinter.StringVar(c)
        self.player_select = ttk.OptionMenu(frame, self.player_var)
        self.player_var.trace('w', self.set_current_player)
        self.player_select.pack()

        self.verb_var = Tkinter.StringVar(c)
        self.verb_select = ttk.OptionMenu(frame, self.verb_var)
        self.verb_var.trace('w', self.set_current_verb)
        self.verb_select.pack()

        self.get_menus()

        self.undo_button = Tkinter.Button(frame, text="Undo", command=self.undo, state=Tkinter.DISABLED)
        self.undo_button.pack()

        c.create_window(0,0,window=frame,anchor=Tkinter.NW)
        frame.pack

        self.canvas = c

        self.create_handles()
        self.draw_all()
        c.mainloop()

    def undo(self):
        self.g.undo()
        self.get_menus()
        if not self.g.undo_stack: self.undo_button['state']=Tkinter.DISABLED
        self.draw_all()

    def get_menus(self):
        self.player_select.set_menu(self.g.current_player or self.g.players[0], *self.g.players)
        self.verb_select.set_menu(self.g.current_verb or self.g.verbs[0].name, *[v.name for v in self.g.verbs])

    def set_current_player(self, *args):
        self.g.current_player = self.player_var.get()

    def set_current_verb(self, *args):
        self.g.current_verb = self.verb_var.get()

    def click1(self, e):
        v = self.g.get_verb(self.verb_var.get())
        clicked = [ i for i in self.canvas.find_overlapping(e.x, e.y, e.x, e.y)
                    if "handle_"+v.target in self.canvas.gettags(i) ]
        if not clicked: return
        p = [ t for t in self.canvas.gettags(clicked[0]) if v.target+"_" in t ][0][5:]
        # print p

        old_verbs = self.g.verbs

        self.g.do_verb(v, p, self.player_var.get())

        if self.g.beep:
            self.canvas.bell()
            self.g.beep = False

        if self.g.undo_stack: self.undo_button['state']=Tkinter.NORMAL
        if not self.g.undo_stack: self.undo_button['state']=Tkinter.DISABLED

        self.get_menus()

        if old_verbs != self.g.verbs:
            self.clear_handles()
            self.create_handles()
        
        self.draw_all()

    def click2(self, e):
        self.drag_xy = np.array([e.x, e.y])
        self.clear_handles()

    def release2(self, e):
        self.drag_xy = None
        self.create_handles()
        # print self.m

    def drag2(self, e):
        if self.drag_xy is not None:
            new_xy = np.array([e.x, e.y])
            delta = new_xy - self.drag_xy
            self.update_m(delta)
            self.drag_xy = new_xy

    def update_m(self, xy):
        xy = xy / (self.scale*self.zoom)
        # print xy

        dx, dy = xy

        T = np.array([[1,0,dx],[0,1,dy],[-dx,-dy,1]])

        self.m = T.dot(self.m)

        self.m[0] /= np.sqrt(self.m[0].dot(self.m[0]))

        self.m[2] = np.cross(self.m[0], self.m[1])
        self.m[2] /= np.sqrt(self.m[2].dot(self.m[2]))

        self.m[1] = np.cross(self.m[2], self.m[0])
        self.m[1] /= np.sqrt(self.m[1].dot(self.m[1]))

        self.draw_all()

    def clear_handles(self):
        self.canvas.delete("handle_face")
        self.canvas.delete("handle_edge")
        self.canvas.delete("handle_vert")

    def create_handles(self):
        targets = [ v.target for v in self.g.verbs ]
        if "face" in targets:
            for p in self.g.gn:
                if self.is_visible(p):
                    self.canvas.create_polygon(
                        [ tuple(self.gv_to_xy(v)) for v in self.g.gn.verts_for_face(p) ],
                        tag=("handle_face", "face_"+p),
                        fill = "",outline = ""
                        )
        if "vert" in targets:
            for p in self.g.gn.verts():
                if self.is_visible(p):
                    self.canvas.create_polygon(
                        [ tuple(self.gv_to_xy(f)) for f in self.g.gn.faces_for_vert(p) ],
                        tag=("handle_vert", "vert_"+p),
                        fill = "",outline = ""
                        )
        if "edge" in targets:
            for p in self.g.gn.edges():
                if self.is_visible(p):
                    faces = self.g.gn.faces_for_edge(p)
                    verts = self.g.gn.verts_for_edge(p)
                    self.canvas.create_polygon(
                        [ tuple(self.gv_to_xy(v)) for v in [ faces[0], verts[0], faces[1], verts[1] ] ],
                        tag=("handle_edge", "edge_"+p),
                        fill = "",outline = ""
                        )

    def is_visible(self, p):
        if not p: return false
        z = self.m.dot(gnet.gv_to_v3(p))[2]
        return z >= 0

    def gv_to_xy(self, p):
        xyz = self.m.dot(gnet.gv_to_v3(p))
        return (xyz[0:2]*self.zoom+self.center)*self.scale

    def draw_all(self):
        self.canvas.delete("thing")
        self.draw_all_things()

    def draw_all_things(self):
        for t in sorted(self.g.all_things(), key = lambda t: t.layer):
            if t.location: self.draw_thing(t)

    def draw_thing(self, t):
        p = t.location
        if self.is_visible(p):
            t.draw(self)

class gcanvas_f(gcanvas):
    def __init__(self, g, focus=999999.9, **kwargs):
        gcanvas.__init__(self, g, **kwargs)
        self.focus = focus

    def is_visible(self, p):
        if not p: return false
        z = self.m.dot(gnet.gv_to_v3(p))[2]
        if z <= -self.focus: return False
        if z < -1.0/self.focus: return False
        if self.zoom*sqrt(1.0-z*z)*(self.focus+1)/(self.focus+z) > 2: return False
        return True

    def gv_to_xy(self, p):
        xyz = self.m.dot(gnet.gv_to_v3(p))
        return (xyz[0:2]*self.zoom*(self.focus+1)/(self.focus+xyz[2])+self.center)*self.scale

class gcanvas_d(gcanvas):
    def __init__(self, *args, **kwargs):
        gcanvas.__init__(self, *args, **kwargs)
        self.width *= 2

        self.other_m = np.array([[-1,0,0],[0,1,0],[0,0,-1]])

    def duplex(self, action):
        action(self)

        c, m = self.center, self.m
        self.center = np.array([3.0,1.0])
        self.m = self.other_m.dot(self.m)

        action(self)

        self.center, self.m = c, m

    def create_handles(self):
        self.duplex(gcanvas.create_handles)

    def draw_all_things(self):
        self.duplex(gcanvas.draw_all_things)

class game:
    def __init__(self, M=1, N=0):
        self.gn = gnet(M,N)
        self.things = defaultdict(list)
        self.players = ["red", "blue"]

        self.undo_stack = []

        self.verbs = [verb('noop', 'face', self.noop)]

        self.current_player = None
        self.current_verb = None

        self.beep = False

    def get_verb(self, name):
        matching = [ v for v in self.verbs if v.name == name ]
        if matching: return matching[0]
        return verb('noop', 'face', self.noop)

    def all_things(self):
        return sum(self.things.values(), [])

    def add_thing(self, t):
        self.things[t.location].append(t)
        self.add_undo(lambda: self.things[t.location].remove(t))
        return t

    def remove_thing(self, t):
        self.things[t.location].remove(t)
        self.add_undo(lambda: self.things[t.location].append(t))
        return t

    def update_thing(self, t, **kwargs):
        for key, value in kwargs.items():
            if key == 'location': self.remove_thing(t)
            old_val = getattr(t, key)
            self.add_undo(lambda: setattr(t, key, old_val))
            setattr(t, key, value)
            if key == 'location': self.add_thing(t)
        return t

    def add_undo(self, f):
        if self.undo_stack:
            self.undo_stack[-1].append(f)

    def undo(self):
        if self.undo_stack:
            uf = self.undo_stack.pop()
            uf.reverse()
            for f in uf: f()

    def do_verb(self, v, p, c):
        self.undo_stack.append([])
        v.action(p, c)
        if self.undo_stack and not self.undo_stack[-1]: self.undo_stack.pop()

    def noop(self, p, player):
        pass

class example(game):
    def __init__(self, M=1, N=0):
        game.__init__(self, M, N)

        self.verbs = [
            verb('dot', 'face', self.dot),
            verb('robber', 'face', self.robber),
            ]

        for p in self.gn:
            self.add_thing(filled_hex(location=p, layer=0, type="hex", color="white"))

        self.robber = dot(location=None, layer=1, type='robber', color='black')
        self.add_thing(self.robber)

    def dot(self, p, player):
        ts = [ t for t in self.things[p] if t.type == "pawn" ]
        for t in ts: self.remove_thing(t)
        if not ts: self.add_thing(dot(location=p, layer=1, type="pawn", color=player))

    def robber(self, p, player):
        self.update_thing(self.robber, location=p)

class thing:
    def __init__(self, location=None, layer=0, type=None, color=None, **kwargs):
        self.layer = layer
        self.type = type
        self.color = color
        self.location = location

    def draw(self, gc):
        pass

    def draw_face(self, gc, r=1.0, location=None, outline="black", width=2, smooth=0, offset=(1,0)):
        p = location or self.location
        verts = [ gc.gv_to_xy(gv) for gv in gc.g.gn.verts_for_face(p) ]
        center = sum(verts)/len(verts)

        offset_to = (offset[0] if offset[0] in gc.g.gn.verts_for_face(p)
                     else gc.g.gn.verts_for_face(p)[offset[0]])
        offset_xy = (gc.gv_to_xy(offset_to) - center)*offset[1]

        gc.canvas.create_polygon(
            [ tuple(v*r+center*(1-r)+offset_xy) for v in verts ],
            tag=("thing"), fill = self.color, outline=outline, width=width, smooth=smooth
            )

    def draw_f_text(self, gc, location=None, font=('Helvetica',1.0), text='', fill='black', offset=(1,0)):
        p = location or self.location
        verts = [ gc.gv_to_xy(gv) for gv in gc.g.gn.verts_for_face(p) ]
        center = sum(verts)/len(verts)

        offset_to = (offset[0] if offset[0] in gc.g.gn.verts_for_face(p)
                     else gc.g.gn.verts_for_face(p)[offset[0]])
        offset_xy = (gc.gv_to_xy(offset_to) - center)*offset[1]

        font = list(font)
        font[1] = int(font[1]*500.0/sqrt(len(gc.g.gn)))
        font = tuple(font)

        gc.canvas.create_text(
            tuple(center + offset_xy),
            text=text,
            fill=fill,
            font=font,
            tag=('thing')
            )

    def draw_edge(self, gc, face=False, r=1.0, width=2, fill=None, **kwargs):
        p = self.location
        if not face: verts = [ gc.gv_to_xy(gv) for gv in gc.g.gn.verts_for_edge(p) ]
        if face: verts = [ gc.gv_to_xy(gv) for gv in gc.g.gn.faces_for_edge(p) ]
        center = sum(verts)/len(verts)
        gc.canvas.create_line(
            [ tuple(v*r+center*(1-r)) for v in verts ],
            tag=("thing"), fill = fill or self.color, width=width
            )

    def draw_vert_poly(self, gc, points, width=2, outline="black", smooth=0):
        c = gc.gv_to_xy(self.location)
        u, v, w = [ gc.gv_to_xy(f) - c for f in gc.g.gn.faces_for_vert(self.location) ]
        points = [ tuple(c + p[0]*u + p[1]*v + p[2]*w) for p in points ]
        gc.canvas.create_polygon(
            points,
            tag=("thing"), fill = self.color, outline=outline, width=width, smooth=smooth
            )

class filled_hex(thing):
    def draw(self, gc):
        self.draw_face(gc)

class dot(thing):
    def draw(self, gc):
        self.draw_face(gc, r=0.5, smooth=1)

class verb:
    def __init__(self, name, target, action):
        self.name = name
        self.target = target
        self.action = action
