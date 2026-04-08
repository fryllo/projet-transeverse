import pyglet
from pyglet import shapes

class NPC:
    def __init__(self, x, y, batch, text):
        self.x, self.y = x, y
        self.width, self.height = 40, 60
        self.text = text
        self.shape = shapes.Rectangle(x, y, 40, 60, color=(80, 80, 200), batch=batch)

    def sync_graphics(self, camera_x):
        self.shape.x = self.x - camera_x
        self.shape.y = self.y