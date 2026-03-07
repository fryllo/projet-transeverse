import pyglet
from pyglet.window import key
from pyglet import shapes

WIDTH = 900
HEIGHT = 600

#dimension de la fenetre

GRAVITY = 1800
PLAYER_SPEED = 300
JUMP_FORCE = 650

#variable utiles

class Entity:

    def __init__(self, x, y, w, h, batch):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

        self.vel_x = 0
        self.vel_y = 0

        self.on_ground = False
        self.solid = True

        self.shape = shapes.Rectangle(x, y, w, h, color=(200, 80, 80), batch=batch)

    def update(self, dt):
        pass

    def sync_graphics(self):
        self.shape.x = self.x
        self.shape.y = self.y

class Player(Entity):

    def __init__(self, x, y, batch, keys): #initialisation
        super().__init__(x, y, 40, 60, batch)
        self.keys = keys

    def update(self, dt): #mouvement de base

        self.vel_x = 0

        if self.keys[key.A] or self.keys[key.LEFT]:
            self.vel_x = -PLAYER_SPEED

        if self.keys[key.D] or self.keys[key.RIGHT]:
            self.vel_x = PLAYER_SPEED

        if (self.keys[key.SPACE] or self.keys[key.W]) and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

class Platform(Entity):

    def __init__(self, x, y, w, h, batch):
        super().__init__(x, y, w, h, batch)
        self.vel_x = 0
        self.vel_y = 0
        self.shape.color = (120, 200, 120)

    def update(self, dt):
        pass

class PhysicsWorld:

    def __init__(self):
        self.entities = []
        self.gravity = GRAVITY

    def add(self, entity):
        self.entities.append(entity)

    def update(self, dt):

        for e in self.entities:

            if isinstance(e, Platform):
                continue

            e.vel_y -= self.gravity * dt #gravite

            # colision horizontal
            e.x += e.vel_x * dt
            self.resolve_collisions(e, axis="x")

            # colision vertical
            e.y += e.vel_y * dt
            e.on_ground = False
            self.resolve_collisions(e, axis="y")

            e.sync_graphics()

    def collide(self, a, b):

        return (
            a.x < b.x + b.width and
            a.x + a.width > b.x and
            a.y < b.y + b.height and
            a.y + a.height > b.y
        )

    def resolve_collisions(self, entity, axis):

        for other in self.entities:

            if other == entity:
                continue

            if not other.solid:
                continue

            if self.collide(entity, other):

                if axis == "x":

                    if entity.vel_x > 0:
                        entity.x = other.x - entity.width

                    if entity.vel_x < 0:
                        entity.x = other.x + other.width

                    entity.vel_x = 0

                if axis == "y":

                    if entity.vel_y < 0:
                        entity.y = other.y + other.height
                        entity.vel_y = 0

                    elif entity.vel_y > 0:
                        entity.y = other.y - entity.height
                        entity.vel_y = 0
                        entity.on_ground = True


class Game:

    def __init__(self):

        self.window = pyglet.window.Window(WIDTH, HEIGHT, "Platformer Engine")

        self.batch = pyglet.graphics.Batch()

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)

        self.world = PhysicsWorld()

        self.create_level()

        pyglet.clock.schedule_interval(self.update, 1/60)

        @self.window.event
        def on_draw():
            self.window.clear()
            self.batch.draw()

    def create_level(self):

        self.player = Player(100, 300, self.batch, self.keys)
        self.world.add(self.player)

        platforms = [

            Platform(0, 0, 900, 40, self.batch),
            Platform(200, 150, 200, 20, self.batch),
            Platform(450, 250, 200, 20, self.batch),
            Platform(650, 350, 150, 20, self.batch)

        ]

        for p in platforms:
            self.world.add(p)

    def update(self, dt):

        for e in self.world.entities:
            e.update(dt)

        self.world.update(dt)