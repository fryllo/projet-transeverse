class Entity:
    def __init__(self, x, y, w, h, batch):
        from pyglet import shapes
        self.x, self.y          = x, y
        self.width, self.height = w, h
        self.vel_x = self.vel_y = 0
        self.on_ground = False
        self.solid     = True
        self.shape = shapes.Rectangle(x, y, w, h, color=(200, 80, 80), batch=batch)

    def update(self, dt):
        pass

    def sync_graphics(self):
        self.shape.x = self.x
        self.shape.y = self.y