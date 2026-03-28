import pyglet
from pyglet.window import key  #permet de detecter touche du clavier
from pyglet import shapes

from ui    import MainMenu
from hud   import HUD
from menus import OptionsMenu, StatsScreen

WIDTH = 900
HEIGHT = 600
GRAVITY = 1800
PLAYER_SPEED = 300
JUMP_FORCE = 650


# ── Entités ────────────────────────────────────────────────────────────────────

class Entity:
    def __init__(self, x, y, w, h, batch):
        self.x, self.y = x, y
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


class Player(Entity):
    def __init__(self, x, y, batch):
        super().__init__(x, y, 40, 60, batch)
        self.hp     = 100
        self.jumps  = 0
        self.deaths = 0

    def update(self, dt):
        pass


class Platform(Entity):
    def __init__(self, x, y, w, h, batch):
        super().__init__(x, y, w, h, batch)
        self.shape.color = (120, 200, 120)

    def update(self, dt):
        pass


# ── Physique ───────────────────────────────────────────────────────────────────

class PhysicsWorld:
    def __init__(self):
        self.entities = []

    def add(self, e):
        self.entities.append(e)

    def update(self, dt):
        for e in self.entities:
            if isinstance(e, Platform):
                continue
            e.vel_y -= GRAVITY * dt
            e.x += e.vel_x * dt
            self._resolve(e, "x")
            e.y += e.vel_y * dt
            e.on_ground = False
            self._resolve(e, "y")
            e.sync_graphics()

    @staticmethod
    def _overlap(a, b):
        return (a.x < b.x + b.width  and a.x + a.width  > b.x and
                a.y < b.y + b.height and a.y + a.height > b.y)

    def _resolve(self, e, axis):
        for o in self.entities:
            if o is e or not o.solid:
                continue
            if self._overlap(e, o):
                if axis == "x":
                    e.x = o.x - e.width if e.vel_x > 0 else o.x + o.width
                    e.vel_x = 0
                else:
                    if e.vel_y < 0:  # tombe -> atterrit sur le dessus
                        e.y, e.vel_y, e.on_ground = o.y + o.height, 0, True
                    else:  # monte -> frappe le dessous
                        e.y, e.vel_y = o.y - e.height, 0


# ── Caméra ─────────────────────────────────────────────────────────────────────

class Camera:
    SMOOTH = 6.0

    def __init__(self, window):
        self.window   = window
        self.offset_x = 0.0

    def reset(self):
        self.offset_x = 0.0

    def update(self, target, dt):
        ideal = target.x + target.width / 2 - self.window.width / 2
        self.offset_x += (ideal - self.offset_x) * self.SMOOTH * dt

    def apply(self, entities):
        for e in entities:
            e.shape.x = e.x - self.offset_x
            e.shape.y = e.y


# ── Jeu ────────────────────────────────────────────────────────────────────────

class Game:

    def __init__(self):
        self.window = pyglet.window.Window(WIDTH, HEIGHT, "Platformer Engine", resizable=True)
        self.batch     = pyglet.graphics.Batch()
        self.hud_batch = pyglet.graphics.Batch()

        self.world    = PhysicsWorld()
        self.camera   = Camera(self.window)
        self._score   = 0
        self._time    = 0.0
        self._running = False

        # Touches pressées — set simple, géré manuellement
        self._held = set()

        self.create_level()
        self._build_ui()
        self.main_menu.show()
        self.hud.hide()

        pyglet.clock.schedule_interval(self.update, 1 / 60)

        # ── Handlers — définis EN DERNIER pour avoir priorité ─────────────────

        @self.window.event
        def on_key_press(symbol, modifiers):
            self._held.add(symbol)
            if symbol == key.F11:
                self.window.set_fullscreen(not self.window.fullscreen)
            if symbol == key.ESCAPE and self._running:
                self._on_back_to_main()

        @self.window.event
        def on_key_release(symbol, modifiers):
            self._held.discard(symbol)

        @self.window.event
        def on_draw():
            self.window.clear()
            if self._running:
                self.batch.draw()
            self.hud_batch.draw()

        @self.window.event
        def on_mouse_motion(x, y, dx, dy):
            self.main_menu.on_mouse_motion(x, y, dx, dy)
            self.options_menu.on_mouse_motion(x, y, dx, dy)
            self.stats_screen.on_mouse_motion(x, y, dx, dy)

        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            self.main_menu.on_mouse_press(x, y, button, modifiers)
            self.options_menu.on_mouse_press(x, y, button, modifiers)
            self.stats_screen.on_mouse_press(x, y, button, modifiers)

        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            self.main_menu.on_mouse_release(x, y, button, modifiers)
            self.options_menu.on_mouse_release(x, y, button, modifiers)
            self.stats_screen.on_mouse_release(x, y, button, modifiers)

        @self.window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self.options_menu.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        @self.window.event
        def on_resize(width, height):
            was = self._running
            self._build_ui()
            if was:
                self.hud.show()
            else:
                self.main_menu.show()
                self.hud.hide()

    # ── Niveau ────────────────────────────────────────────────────────────────

    def create_level(self):
        self.player = Player(100, 60, self.batch)
        self.world.add(self.player)
        for p in [
            Platform(   0,  0, 2000, 40, self.batch),
            Platform( 200, 150, 200, 20, self.batch),
            Platform( 500, 250, 200, 20, self.batch),
            Platform( 800, 350, 150, 20, self.batch),
            Platform(1100, 200, 200, 20, self.batch),
            Platform(1400, 300, 200, 20, self.batch),
            Platform(1700, 180, 150, 20, self.batch),
        ]:
            self.world.add(p)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        w, h = self.window.width, self.window.height
        self.hud_batch    = pyglet.graphics.Batch()
        self.main_menu    = MainMenu(w, h, self.hud_batch,
                                     on_play=self._on_play,
                                     on_options=self._on_options,
                                     on_quit=pyglet.app.exit)
        self.options_menu = OptionsMenu(w, h, self.hud_batch, on_back=self._on_back_to_main)
        self.stats_screen = StatsScreen(w, h, self.hud_batch, on_back=self._on_back_to_main)
        self.hud          = HUD(w, h, self.hud_batch, max_hp=100, show_stats=True)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_play(self):
        self.main_menu.hide()
        self.options_menu.hide()
        self.stats_screen.hide()
        self.hud.show()
        self.camera.reset()
        self._held.clear()
        self._running = True

    def _on_options(self):
        self.main_menu.hide()
        self.options_menu.show()

    def _on_back_to_main(self):
        self.options_menu.hide()
        self.stats_screen.hide()
        self._running = False
        self._held.clear()
        self.hud.hide()
        self.main_menu.show()

    # ── Boucle ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if not self._running:
            return

        self._time += dt
        p = self.player

        # Déplacement horizontal
        p.vel_x = 0
        if key.Q in self._held or key.LEFT in self._held:
            p.vel_x = -PLAYER_SPEED
        if key.D in self._held or key.RIGHT in self._held:
            p.vel_x = PLAYER_SPEED

        # Saut — vérifié chaque frame, pas de discard pour garder la réactivité
        if (key.SPACE in self._held or key.UP in self._held or key.Z in self._held) and p.on_ground:
            p.vel_y     = JUMP_FORCE
            p.on_ground = False
            p.jumps    += 1

        self.world.update(dt)
        self.camera.update(p, dt)
        self.camera.apply(self.world.entities)

        self.hud.update(p, hp=p.hp, score=self._score)
        self.stats_screen.update_stats(
            time_sec=self._time, jumps=p.jumps,
            deaths=p.deaths, best_score=self._score,
        )


if __name__ == "__main__":
    game = Game()
    pyglet.app.run()
