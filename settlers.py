from goldberg import *
import random
import sys

class settlers(game):
    def __init__(self, size='small', player_count=3):
        M, N = {'small':(1,1), 'medium':(2,0), 'large':(2,1)}[size]
        game.__init__(self, M, N)

        self.players = ['red', 'white', 'cyan', 'orange', 'purple', 'green'][0:player_count]

        self.verbs = [
            verb('shuffle all', 'face', self.shuffle_all),

            verb('swap hex', 'face', self.swap_hex),
            verb('swap number', 'face', self.swap_number),
            verb('swap port', 'edge', self.swap_port),

            verb('finish setup', 'face', self.finish_setup)
            ]

        hex_inventory = [
            ('lawn green', 4),
            ('forest green', 4),
            ('gold', 4),
            ('brown', 3),
            ('slate gray', 3),
            ('blue', 14),

            ('lawn green', 1),
            ('forest green', 1),
            ('gold', 1),
            ('brown', 1),
            ('slate gray', 1),
            ('blue', 5),

            ('lawn green', 3),
            ('forest green', 3),
            ('gold', 3),
            ('brown', 2),
            ('slate gray', 2),
            ('blue', 17),
            ]

        hex_colors = []
        for color, count in hex_inventory:
            for i in range(count):
                hex_colors.append(color)

        for color in hex_colors[0:len(self.gn)]:
            self.add_thing(filled_hex(location=None, layer=0, type='hex', color=color))

        numbers = [ 2, 3,3, 4,4, 5,5, 6,6, 8,8, 9,9, 10,10, 11,11, 12,
                    2, 3,   4,   5,   6,
                    2, 3,   4,   5,   6,   8,8, 9,9, 10,10, 11,    12, ]

        for n in numbers[0:len([ t for t in self.all_things() if t.type == 'hex' and t.color != 'blue' ])]:
            self.add_thing(number(n))

        port_inventory = [
            ('lawn green', 1),
            ('forest green', 1),
            ('gold', 1),
            ('brown', 1),
            ('slate gray', 1),
            ('white', 3),

            ('lawn green', 1),
            ('white', 1),

            ('forest green', 1),
            ('gold', 1),
            ('brown', 1),
            ('slate gray', 1),
            ('white', 2),            
            ]

        port_colors = []
        for color, count in port_inventory:
            for i in range(count):
                port_colors.append(color)

        for color in port_colors[0:int(len(self.gn)/5 + 2)]:
            self.add_thing(port(color))

        self.swap_cursor = self.add_thing(cursor())

        self.robber = self.add_thing(robber())
        self.pirate = self.add_thing(robber())

        self.shuffle_all()

    def shuffle_all(self, *args):
        hexes = [ t for t in self.all_things() if t.type == 'hex' ]
        faces = self.gn.faces()
        random.shuffle(faces)
        for hex, face in zip(hexes, faces):
            self.update_thing(hex, location=face)

        numbers = [ t for t in self.all_things() if t.type == 'number' ]
        land_hexes = [ t for t in self.all_things() if t.type == 'hex' and t.color != 'blue' ]
        random.shuffle(land_hexes)
        for n, h in zip(numbers, land_hexes):
            self.update_thing(n, location=h.location)

        port_edges = [ e for e in self.gn.edges() if
                       len([ f for f in self.gn.faces_for_edge(e) if
                             [ t for t in self.things[f] if t.type == 'hex' and t.color == 'blue' ]]
                           ) == 1 ]
        random.shuffle(port_edges)
        all_ports = [ t for t in self.all_things() if t.type == 'port' ]
        random.shuffle(all_ports)
        for p in all_ports:
            try:
                e = port_edges.pop()
                while [ v for v in self.gn.verts_for_edge(e) if
                        [ oe for oe in self.gn.edges_for_vert(v) if
                          [ t for t in self.things[oe] if t.type == 'port' ] ] ]:
                        e = port_edges.pop()
            except IndexError:
                e = None

            self.update_thing(p, location=e)

    def swap_hex(self, p, *args):
        q = self.swap_cursor.location
        if q not in self.gn.faces():
            self.update_thing(self.swap_cursor, location=p)
        else:
            P = [ t for t in self.things[p] if t.type == 'hex' ]
            Q = [ t for t in self.things[q] if t.type == 'hex' ]
            if P: self.update_thing(P[0], location = q)
            if Q: self.update_thing(Q[0], location = p)
            self.swap_number(p)

    def swap_number(self, p, *args):
        q = self.swap_cursor.location
        if q not in self.gn.faces():
            self.update_thing(self.swap_cursor, location=p)
        else:
            P = [ t for t in self.things[p] if t.type == 'number' ]
            Q = [ t for t in self.things[q] if t.type == 'number' ]
            if P: self.update_thing(P[0], location = q)
            if Q: self.update_thing(Q[0], location = p)
            self.update_thing(self.swap_cursor, location=None)

    def swap_port(self, p, *args):
        q = self.swap_cursor.location
        if q not in self.gn.edges():
            self.update_thing(self.swap_cursor, location=p)
        else:
            P = [ t for t in self.things[p] if t.type == 'port' ]
            Q = [ t for t in self.things[q] if t.type == 'port' ]
            if P: self.update_thing(P[0], location = q)
            if Q: self.update_thing(Q[0], location = p)
            self.update_thing(self.swap_cursor, location=None)
 
    def finish_setup(self, *args):
        self.remove_thing(self.swap_cursor)

        for c in self.players:
            for i in range(15): self.add_thing(road(c))
            for i in range(15): self.add_thing(ship(c))
            for i in range(5): self.add_thing(settlement(c))
            for i in range(4): self.add_thing(city(c))

        self.undo_stack = []

        self.verbs = [
            verb('robber/pirate', 'face', self.move_robber),
            verb('road', 'edge', self.road),
            verb('ship', 'edge', self.ship),
            verb('settlement', 'vert', self.settlement),
            verb('city', 'vert', self.city)
            ]

        self.current_verb = 'settlement'

    def move_robber(self, p, *args):
        hex = [ t for t in self.things[p] if t.type == 'hex' ][0]
        active = self.pirate if hex.color == 'blue' else self.robber
        if active.location == p: p = None
        self.update_thing(active, location=p)

    def road(self, p, player):
        has = [ t for t in self.things[None] if t.type == 'road' and t.color == player ]
        existing = [ t for t in self.things[p] if t.layer == 1 ]
        if has and not existing:
            self.update_thing(has[0], location=p)
        else:
            self.beep = True

    def ship(self, p, player):
        has = [ t for t in self.things[None] if t.type == 'ship' and t.color == player ]
        existing = [ t for t in self.things[p] if t.layer == 1 ]
        if has and not existing:
            self.update_thing(has[0], location=p)
        elif existing and existing[0].type == 'ship' and existing[0].color == player:
            self.update_thing(existing[0], location=None)            
        else:
            self.beep = True

    def settlement(self, p, player):
        has = [ t for t in self.things[None] if t.type == 'settlement' and t.color == player ]
        existing = [ t for t in self.things[p] if t.layer == 1 ]
        if has and not existing:
            self.update_thing(has[0], location=p)
        else:
            self.beep = True

    def city(self, p, player):
        has = [ t for t in self.things[None] if t.type == 'city' and t.color == player ]
        existing = [ t for t in self.things[p] if t.layer == 1 ]
        if has and existing and existing[0].type == 'settlement' and existing[0].color == player:
            self.update_thing(existing[0], location=None)
            self.update_thing(has[0], location=p)
        else:
            self.beep = True

    def run(self):
        gcanvas_d(self).run()

class cursor(thing):
    def __init__(self):
        thing.__init__(self, location=None, layer=1, type='cursor', color='')

    def draw(self, gc):
        if self.location in gc.g.gn.faces():
            self.draw_face(gc, r=0.75, outline='white', width=3)
        elif self.location in gc.g.gn.edges():
            faces_blue_first = sorted(
                gc.g.gn.faces_for_edge(self.location),
                key = lambda f: len([ t for t in gc.g.things[f] if t.type == 'hex' and t.color == 'blue' ]),
                reverse = True
                )
            f = faces_blue_first[0]
            verts = gc.g.gn.verts_for_edge(self.location)
            for v in verts:
                self.draw_face(
                    gc,
                    location = f,
                    offset = (v, 0.75),
                    r = 0.23,
                    outline = 'white',
                    width = 3
                    )

class number(thing):
    def __init__(self, n):
        thing.__init__(self, location=None, layer=0.5, type='number', color='bisque')
        self.value = n

    def draw(self, gc):
        self.draw_face(gc, r=0.4, smooth=1)
        self.draw_f_text(
            gc,
            text = str(self.value),
            font = ('Helvetica',0.3,'bold'),
            fill = 'red' if self.value in [6,8] else 'black'
            )

class port(thing):
    def __init__(self, c):
        thing.__init__(self, location=None, layer=0.5, type='port', color=c)

    def draw(self, gc):
        faces_blue_first = sorted(
            gc.g.gn.faces_for_edge(self.location),
            key = lambda f: len([ t for t in gc.g.things[f] if t.type == 'hex' and t.color == 'blue' ]),
            reverse = True
            )
        f = faces_blue_first[0]
        if gc.is_visible(f):
            verts = gc.g.gn.verts_for_edge(self.location)
            for v in verts:
                self.draw_face(
                    gc,
                    location = f,
                    offset = (v, 0.75),
                    r = 0.2,
                    smooth = 1
                    )

class robber(thing):
    def __init__(self):
        thing.__init__(self, location=None, layer=1, type='robber', color='black')

    def draw(self, gc):
        self.draw_face(gc, r=0.3, smooth=1)

class road(thing):
    def __init__(self, c):
        thing.__init__(self, location=None, layer=1, type='road', color=c)

    def draw(self, gc):
        self.draw_edge(gc, r=0.64, width=13, fill='black')
        self.draw_edge(gc, r=0.6, width=9)

class ship(thing):
    def __init__(self, c):
        thing.__init__(self, location=None, layer=1, type='ship', color=c)

    def draw(self, gc):
        self.draw_edge(gc, r=0.40, width=16, fill='black')
        self.draw_edge(gc, r=0.18, width=26, fill='black')
        self.draw_edge(gc, r=0.36, width=12)
        self.draw_edge(gc, r=0.14, width=22)

class settlement(thing):
    def __init__(self, c):
        thing.__init__(self, location=None, layer=1, type='settlement', color=c)

    def draw(self, gc):
        self.draw_vert_poly(gc, [
                (0.175, 0,     0),
                (0.175, 0.175, 0),
                (0,     0.175, 0),
                (0,     0.175, 0.175),
                (0,     0,     0.175),
                (0.175, 0,     0.175)
                ])
            
class city(thing):
    def __init__(self, c):
        thing.__init__(self, location=None, layer=1, type='city', color=c)

    def draw(self, gc):
        self.draw_vert_poly(gc, [
                (0.25 , 0,    0),

                (0.25, 0.15, 0),
                (0.15, 0.15, 0),
                (0.15, 0.25, 0),

                (0,    0.25, 0),

                (0,    0.25, 0.15),
                (0,    0.15, 0.15),
                (0,    0.15, 0.25),

                (0,    0,    0.25),

                (0.15, 0,    0.25),
                (0.15, 0,    0.15),
                (0.25, 0,    0.15)
                ])

if __name__ == '__main__':
    size = 'small'
    players = 3
    for arg in sys.argv[1:]:
        if arg in ['small', 'medium', 'large']: size = arg
        elif int(arg) - 1 in range(6): players = int(arg)
        else: raise ValueError("unrecognized argument: " + arg)
    settlers(size, players).run()
