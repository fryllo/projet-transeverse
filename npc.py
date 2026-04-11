from pyglet import shapes
from entity import Entity

class NPC(Entity):
    def __init__(self, x, y, batch, text, name="???"):
        super().__init__(x, y, 40, 60, batch)
        self.shape.color = (80, 80, 200)
        self.text = text
        self.name = name
        self.solid = False

    def update(self, dt):
        pass