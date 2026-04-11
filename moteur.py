import pyglet
from pyglet.window import key
from pyglet import shapes
from npc import NPC
from ui import MainMenu, LevelSelect, Button, GameOverMenu
from hud import HUD
from menus import OptionsMenu, StatsScreen
from enemies import EnemyManager, Dragon
from level_system import LevelManager

try:
    son_pas = pyglet.media.load("musique/bruit_de_pas.wav", streaming=False)
    son_saut = pyglet.media.load("musique/saut.flac", streaming=False)
except Exception:
    son_pas = None
    son_saut = None

WIDTH  = 900
HEIGHT = 600
GRAVITY      = 1800
PLAYER_SPEED = 300
JUMP_FORCE   = 650


# ── Entités ────────────────────────────────────────────────────────────────────

class Entity:
    def __init__(self, x, y, w, h, batch):
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
            if isinstance(e, NPC):
                e.sync_graphics()
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
                    if e.vel_y < 0:
                        e.y, e.vel_y, e.on_ground = o.y + o.height, 0, True
                    else:
                        e.y, e.vel_y = o.y - e.height, 0


# ── Caméra ─────────────────────────────────────────────────────────────────────

class Camera:
    SMOOTH = 6.0

    def __init__(self, window, level_width=8000):
        self.window      = window
        self.level_width = level_width
        self.offset_x    = 0.0

    def reset(self):
        self.offset_x = 0.0

    def update(self, target, dt):
        ideal = target.x + target.width / 2 - self.window.width / 2
        self.offset_x += (ideal - self.offset_x) * self.SMOOTH * dt
        self.offset_x = max(0, min(self.offset_x, self.level_width))

    def apply(self, entities):
        for e in entities:
            e.shape.x = e.x - self.offset_x
            e.shape.y = e.y


# ── Jeu ────────────────────────────────────────────────────────────────────────

class Game:

    def __init__(self):
        self.window = pyglet.window.Window(WIDTH, HEIGHT, "Platformer Engine", resizable=True)
        self.bg_batch  = pyglet.graphics.Batch()
        self.batch     = pyglet.graphics.Batch()
        self.hud_batch = pyglet.graphics.Batch()

        self.world         = PhysicsWorld()
        self.camera        = Camera(self.window)
        self.enemy_manager = EnemyManager(self.batch)
        self.PlatformClass = Platform

        self._score   = 0
        self._time    = 0.0
        self._running = False
        self._held    = set()

        self.player = Player(100, 60, self.batch)
        self.world.add(self.player)

        self.level_manager = LevelManager(self)
        self.level_manager.load(0)

        self.current_npc   = None
        self.show_dialogue = False

        self._build_ui()
        self.main_menu.show()
        self.hud.hide()

        self.son_pas      = son_pas
        self.son_saut     = son_saut
        self._step_timer  = 0

        pyglet.clock.schedule_interval(self.update, 1 / 60)

        @self.window.event
        def on_key_press(symbol, modifiers):
            self._held.add(symbol)
            if symbol == key.F11:
                self.window.set_fullscreen(not self.window.fullscreen)
            if symbol == key.ESCAPE and self._running:
                self._on_back_to_main()
            if symbol == key.TAB and self._running:
                self.level_manager.next_level()

            if symbol == key.E and self._running:
                try:
                    if self.show_dialogue:
                        self.show_dialogue = False
                        self.dialogue_label.text = ""
                        self.dialogue_name_label.text = ""
                        self._dialogue_hint.text = ""
                        self._dialogue_bg.batch = None
                        self._dialogue_border.batch = None
                    elif self.current_npc:
                        self.show_dialogue = True
                        self._dialogue_bg.batch = self.hud_batch
                        self._dialogue_border.batch = self.hud_batch
                        self.dialogue_name_label.text = getattr(self.current_npc, 'name', '???')
                        t = self.current_npc.text
                        self.dialogue_label.text = " ".join(t) if isinstance(t, list) else t
                        self._dialogue_hint.text = "[E] Fermer"
                except Exception as ex:
                    print("ERREUR dialogue:", ex)

        @self.window.event
        def on_key_release(symbol, modifiers):
            self._held.discard(symbol)

        @self.window.event
        def on_draw():
            self.window.clear()
            self.bg_batch.draw()
            if self._running:
                self.batch.draw()
            self.hud_batch.draw()

        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            if self.game_over_menu._visible:
                self.game_over_menu.on_mouse_press(x, y, button, modifiers)
            elif self.level_menu._visible:
                self.level_menu.on_mouse_press(x, y, button, modifiers)
            elif self.options_menu.is_visible:
                self.options_menu.on_mouse_press(x, y, button, modifiers)
            elif self.stats_screen.is_visible:
                self.stats_screen.on_mouse_press(x, y, button, modifiers)
            elif self.main_menu._visible:
                self.main_menu.on_mouse_press(x, y, button, modifiers)
            elif self._running:
                self.exit_btn.on_mouse_press(x, y, button, modifiers)

        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            if self.game_over_menu._visible:
                self.game_over_menu.on_mouse_release(x, y, button, modifiers)
            elif self.level_menu._visible:
                self.level_menu.on_mouse_release(x, y, button, modifiers)
            elif self.options_menu.is_visible:
                self.options_menu.on_mouse_release(x, y, button, modifiers)
            elif self.stats_screen.is_visible:
                self.stats_screen.on_mouse_release(x, y, button, modifiers)
            elif self.main_menu._visible:
                self.main_menu.on_mouse_release(x, y, button, modifiers)
            elif self._running:
                self.exit_btn.on_mouse_release(x, y, button, modifiers)

        @self.window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self.options_menu.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        @self.window.event
        def on_resize(width, height):
            was_running = self._running
            self._build_ui()
            if self.level_manager._current_bg:
                self.level_manager._current_bg.on_resize(width, height)
            if was_running:
                self.main_menu.hide()
                self.level_menu.hide()
                self.hud.show()
                self.exit_btn.set_visible(True)
                self._running = True
            else:
                self.main_menu.show()
                self.hud.hide()
                self.exit_btn.set_visible(False)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        w, h = self.window.width, self.window.height
        self.hud_batch = pyglet.graphics.Batch()

        self.hud = HUD(w, h, self.hud_batch, max_hp=100, show_stats=True)
        self.game_over_menu = GameOverMenu(w, h, self.hud_batch,
                                           on_retry=self._on_retry,
                                           on_menu=self._on_back_to_main)
        self.exit_btn = Button(16, h - 110, 80, 40, "PORTIER",
                               self.hud_batch, self.hud._grp, self.hud._grp,
                               on_click=self._on_exit_to_levels)
        self.exit_btn.set_visible(False)
        self.main_menu = MainMenu(w, h, self.hud_batch,
                                  on_play=self._on_play,
                                  on_options=self._on_options,
                                  on_quit=pyglet.app.exit)
        self.level_menu   = LevelSelect(w, h, self.hud_batch, on_level_selected=self._on_start_level)
        self.options_menu = OptionsMenu(w, h, self.hud_batch, on_back=self._on_back_to_main)
        self.stats_screen = StatsScreen(w, h, self.hud_batch, on_back=self._on_back_to_main)

        # Boîte de dialogue NPC
        self._dialogue_bg = shapes.Rectangle(
            50, 20, w - 100, 110, color=(20, 20, 40), batch=None)
        self._dialogue_border = shapes.BorderedRectangle(
            50, 20, w - 100, 110,
            border=2, color=(20, 20, 40),
            border_color=(200, 200, 255), batch=None)
        self.dialogue_name_label = pyglet.text.Label(
            "", font_name="Arial", font_size=14,
            color=(255, 220, 100, 255),
            x=70, y=115, batch=self.hud_batch)
        self.dialogue_label = pyglet.text.Label(
            "", font_name="Arial", font_size=13,
            color=(255, 255, 255, 255),
            x=70, y=75, width=w - 140,
            multiline=True, batch=self.hud_batch)
        self._dialogue_hint = pyglet.text.Label(
            "", font_name="Arial", font_size=10,
            color=(180, 180, 180, 255),
            x=w - 160, y=28, batch=self.hud_batch)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_play(self):
        if not self.game_over_menu._visible:
            self.main_menu.hide()
            self.options_menu.hide()
            self.stats_screen.hide()
            self.hud.hide()
            self.level_menu.show()
            self._running = False

    def _on_start_level(self, level_index):
        self.level_menu.hide()
        self.level_manager.load(level_index)
        self.hud.show()
        self.camera.reset()
        self._held.clear()
        self.exit_btn.set_visible(True)
        self._running = True

    def _on_exit_to_levels(self):
        self._running = False
        self.hud.hide()
        self.exit_btn.set_visible(False)
        self.main_menu.hide()
        self.level_menu.show()

    def _on_retry(self):
        self.game_over_menu.hide()
        self.level_manager.load(self.level_manager.index)
        self.hud.show()
        self.exit_btn.set_visible(True)
        self._running = True

    def _on_options(self):
        self.main_menu.hide()
        self.options_menu.show()

    def _on_back_to_main(self):
        self._running = False
        self._held.clear()
        self.options_menu.hide()
        self.stats_screen.hide()
        self.level_menu.hide()
        self.game_over_menu.hide()
        self.exit_btn.set_visible(False)
        self.hud.hide()
        self.main_menu.show()

    # ── Boucle ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if not self._running:
            return

        if self.player.x > self.level_manager.current_level.length - 80:
            self.level_manager.next_level()

        self._time += dt
        p = self.player

        # Cache le dialogue si show_dialogue est False
        if not self.show_dialogue:
            self.dialogue_label.text      = ""
            self.dialogue_name_label.text = ""
            self._dialogue_hint.text      = ""
            self._dialogue_bg.batch       = None
            self._dialogue_border.batch   = None

        # Son saut
        if (key.SPACE in self._held or key.UP in self._held or key.Z in self._held) and p.on_ground:
            p.vel_y     = JUMP_FORCE
            p.on_ground = False
            p.jumps    += 1
            if self.son_saut:
                self.son_saut.play()

        # Son de pas
        moving = p.vel_x != 0 and p.on_ground
        if moving:
            self._step_timer -= dt
            if self._step_timer <= 0:
                if self.son_pas:
                    self.son_pas.play()
                self._step_timer = 0.4
        else:
            self._step_timer = 0

        # Déplacement
        p.vel_x = 0
        if key.Q in self._held or key.LEFT in self._held:
            p.vel_x = -PLAYER_SPEED
        if key.D in self._held or key.RIGHT in self._held:
            p.vel_x = PLAYER_SPEED

        # Saut
        if (key.SPACE in self._held or key.UP in self._held or key.Z in self._held) and p.on_ground:
            p.vel_y     = JUMP_FORCE
            p.on_ground = False
            p.jumps    += 1

        self.world.update(dt)

        # Détection NPC proche
        self.current_npc = None
        for e in self.world.entities:
            if isinstance(e, NPC):
                if abs(self.player.x - e.x) < 80:
                    self.current_npc = e
                    break

        self.enemy_manager.update(dt, self.player)

        if p.hp <= 0:
            self._running = False
            self.exit_btn.set_visible(False)
            self.game_over_menu.show()
            p.deaths += 1
            return

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