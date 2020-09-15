import sys
from goldberg import *
from numpy import array

class Y(game):
    def __init__(self, M=4):
        game.__init__(self, M, 0)
        self.players = ['black', 'white']
        self.verbs = [ verb('stone', 'face', self.stone) ]

        for e in self.gn.edges():
            color = None
            keys = gvector.decode(e).keys()
            if not [ k for k in keys if k not in ['K','L','I'] ]:
                color = 'red'
            elif not [ k for k in keys if k not in ['A','C','I'] ]:
                color = 'blue'
            elif not [ k for k in keys if k not in ['A','F','K'] ]:
                color = 'green'
            elif not [ k for k in keys if k in ['D', 'E', 'J'] ]:
                color = 'black'

            if color:
                self.add_thing(edge(location=e, layer=0, type="edge", color=color))

    def run(self):
        gc = gcanvas_f(self, zoom=0.575, focus=2, bg='burlywood2')
        gc.m = array([[0.9777,  0.0,  0.21],
                      [0.0,  1.0, 0.0],
                      [-0.21,  0.0,  0.9777]])
        gc.run()

    def stone(self, p, player):
        es = [ e for e in self.gn.edges_for_face(p) if
              [ t for t in self.things[e] if t.type == "edge" ] ]
        ts = [ t for t in self.things[p] if t.type == "stone" ]
        if es and not ts:
            self.add_thing(stone(location=p, layer=1, type="stone", color=player))
            self.update_thing(
                self,
                current_player = [ c for c in self.players if c != self.current_player ][0]
                )

class edge(thing):
    def draw(self, gc):
        self.draw_edge(gc, face=True, width=3)

class stone(thing):
    def draw(self, gc):
        self.draw_face(gc, r=0.85, smooth=1)

if __name__ == '__main__':
    M = 4
    if len(sys.argv) > 1: M = int(sys.argv[1])
    Y(M).run()
