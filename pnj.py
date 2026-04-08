
from pyglet import shapes

from moteur import Entity


class NPC(Entity):
    def __init__(self, x, y, batch, text):
        super().__init__(x, y, 40, 60, batch)
        self.shape.color = (80, 80, 200)
        self.text = text
        self.solid = False  # IMPORTANT → le joueur peut passer à travers

    def update(self, dt):
        pass