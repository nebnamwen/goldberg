import sys
from goldberg import *
from numpy import array

class prohex(game):
    def __init__(self, M=4, N=0):
        game.__init__(self, M, N)
        self.players = ['black', 'white']
        self.verbs = [ verb('stone', 'face', self.stone) ]

        for f in self.gn:
            self.add_thing(hex(location=f, layer=0, type="hex", color='burlywood2'))

    def run(self):
        gc = gcanvas(self, bg='burlywood2')
        gc.run()

    def stone(self, p, player):
        ts = [ t for t in self.things[p] if t.type == "stone" ]
        if not ts:
            self.add_thing(stone(location=p, layer=1, type="stone", color=player))
            self.add_thing(stone(location=gnet.opposite_gv(p), layer=1, type="stone", color=player))
            self.update_thing(
                self,
                current_player = [ c for c in self.players if c != self.current_player ][0]
                )

class hex(thing):
    def draw(self, gc):
        self.draw_face(gc)

class stone(thing):
    def draw(self, gc):
        self.draw_face(gc, r=0.85, smooth=1)

if __name__ == '__main__':
    M = 4
    N = 0
    if len(sys.argv) > 1: M = int(sys.argv[1])
    if len(sys.argv) > 2: N = int(sys.argv[2])
    prohex(M).run()
