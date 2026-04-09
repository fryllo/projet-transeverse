# level_system.py
from pyglet import shapes
from enemies import Dragon, Elfe, NuageMechant, Aigle, Requin, Champignon
from background import BackgroundBuilder
from npc import NPC




class Level:
    def __init__(self, name, theme, length, spawn, platforms, enemies, npcs):
        self.name = name
        self.theme = theme
        self.length = length
        self.spawn = spawn
        self.platforms = platforms
        self.enemies = enemies
        self.npcs = npcs


class LevelManager:
    def __init__(self, game):
        self.game = game
        self.index = 0
        self.levels = self._build_levels()
        self._bg_shapes = []
        self._current_bg = None

    def _build_levels(self):
        return [
            Level(
                name="Prairie",
                theme="ground",
                length=8000,
                spawn=(100, 80),
                platforms=[
                    (0,   0, 8000, 40),
                    (0, 0, 50, 6000),
                    (180, 130, 130, 20),
                    (380, 190, 140, 20),
                    (620, 260, 160, 20),
                    (870, 160, 120, 20),
                    (1080, 240, 180, 20),
                    (1360, 320, 130, 20),
                    (1560, 220, 150, 20),
                    (1820, 280, 140, 20),
                    (7500, 200, 120, 20),
                ],
                enemies=[
                    (Aigle, 520, 300),
                    (Champignon, 910, 40),
                    (Dragon, 1500, 60),
                ],
                npcs=[
                    ("La darone à ta grand mére","Bonjour aventurier !", 400, 40),
                    ("Le pedo of all time",["Le dragon est dangereux...","son bazouzou est énorme"], 1200, 40),
                ],
            ),
            Level(
                name="Lagune",
                npcs=[],
                theme="water",
                length=8000,
                spawn=(100, 80),
                platforms=[
                    (0,   0, 8000, 40),
                    (0, 0, 50, 6000),
                    (160, 110, 120, 20),
                    (340, 170, 100, 20),
                    (520, 120, 150, 20),
                    (760, 210, 120, 20),
                    (980, 280, 160, 20),
                    (1250, 190, 140, 20),
                    (1490, 250, 130, 20),
                    (1740, 340, 150, 20),
                ],
                enemies=[
                    (Requin, 600, 40),
                    (NuageMechant, 1180, 420),
                    (Requin, 1620, 40),
                ],
            ),
            Level(
                name="Cieux",
                theme="sky",
                npcs=[],
                length=8000,
                spawn=(100, 120),
                platforms=[
                    (0,   0, 8000, 40),
                    (0, 0, 50, 6000),
                    (320, 120, 110, 20),
                    (500, 210, 110, 20),
                    (680, 300, 110, 20),
                    (860, 230, 110, 20),
                    (1040, 340, 120, 20),
                    (1260, 260, 120, 20),
                    (1480, 380, 110, 20),
                    (1680, 300, 120, 20),
                    (1900, 420, 160, 20),
                ],
                enemies=[
                    (Elfe, 540, 250),
                    (Aigle, 900, 260),
                    (Dragon, 1540, 430),
                ],
            ),
        ]

    def _clear_world_platforms(self):
        keep = [self.game.player]
        for e in self.game.world.entities:
            if e is self.game.player:
                continue
            if hasattr(e, "shape"):
                e.shape.batch = None
        self.game.world.entities = keep

    def _clear_background(self):
        if self._current_bg:
            self._current_bg.set_visible(False)
        self._current_bg = None

    def load(self, index):
        self.index = index % len(self.levels)
        level = self.levels[self.index]

        self._clear_world_platforms()
        self._clear_background()
        self.game.enemy_manager.clear()

        self.game.player.x, self.game.player.y = level.spawn
        self.game.player.vel_x = 0
        self.game.player.vel_y = 0
        self.game.player.on_ground = False
        self.game.player.hp = 100

        for name, text, x, y in level.npcs:
            npc = NPC(x, y, self.game.batch, text)
            self.game.world.add(npc)

        for x, y, w, h in level.platforms:
            p = self.game.PlatformClass(x, y, w, h, self.game.batch)
            if level.theme == "ground":
                p.shape.color = (130, 200, 110)
            elif level.theme == "water":
                p.shape.color = (80, 150, 180)
            else:
                p.shape.color = (210, 210, 220)
            self.game.world.add(p)

        for enemy_cls, x, y in level.enemies:
            self.game.enemy_manager.spawn(enemy_cls, x=x, y=y)

        if level.theme == "ground":
            self._current_bg = BackgroundBuilder.create_ground(self.game.window.width, self.game.window.height, self.game.bg_batch)
        elif level.theme == "water":
            self._current_bg = BackgroundBuilder.create_water(self.game.window.width, self.game.window.height, self.game.bg_batch)
        else:
            self._current_bg = BackgroundBuilder.create_sky(self.game.window.width, self.game.window.height, self.game.bg_batch)

    def update_background(self):
        if self._current_bg:
            self._current_bg.update(self.game.camera.offset_x)

    @property
    def current_level(self):
        return self.levels[self.index]

    def next_level(self):
        self.load(self.index + 1)