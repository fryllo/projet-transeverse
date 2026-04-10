# level_system.py
from pyglet import shapes
from enemies import Dragon, Elfe, NuageMechant, Aigle, Requin, Champignon
from background import BackgroundBuilder


class Level:
    def __init__(self, name, theme, length, spawn, platforms, enemies):
        self.name = name
        self.theme = theme
        self.length = length
        self.spawn = spawn
        self.platforms = platforms
        self.enemies = enemies


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
                spawn=(100, 180),
                platforms=[
                    (0,    0, 8000, 40),   # sol
                    (0,    0,   50, 6000), # mur gauche
                    # -- zone 1 (x 180-1820) --
                    (180,  130, 130, 20),
                    (380,  190, 140, 20),
                    (620,  260, 160, 20),
                    (870,  160, 120, 20),
                    (1080, 240, 180, 20),
                    (1360, 320, 130, 20),
                    (1560, 220, 150, 20),
                    (1820, 280, 140, 20),
                    # -- zone 2 (x 2100-3900) --
                    (2100, 180, 150, 20),
                    (2350, 260, 130, 20),
                    (2560, 160, 140, 20),
                    (2780, 300, 160, 20),
                    (3020, 200, 120, 20),
                    (3220, 320, 150, 20),
                    (3460, 240, 130, 20),
                    (3680, 180, 160, 20),
                    (3900, 280, 140, 20),
                    # -- zone 3 (x 4150-5900) --
                    (4150, 200, 150, 20),
                    (4380, 300, 130, 20),
                    (4600, 160, 160, 20),
                    (4820, 260, 140, 20),
                    (5060, 340, 120, 20),
                    (5280, 220, 150, 20),
                    (5500, 300, 130, 20),
                    (5720, 180, 160, 20),
                    (5920, 260, 140, 20),
                    # -- zone 4 (x 6150-7500) --
                    (6150, 200, 150, 20),
                    (6380, 320, 130, 20),
                    (6600, 240, 160, 20),
                    (6820, 160, 140, 20),
                    (7060, 280, 130, 20),
                    (7280, 200, 150, 20),
                    (7500, 300, 120, 20),  # plateforme finale
                ],
                enemies=[
                    (Aigle,      520,  300),
                    (Dragon,    1500,   60),
                    (Aigle,     2700,  340),
                    (Dragon,    3500,   60),
                    (Aigle,     4900,  300),
                    (Dragon,    6000,   60),
                    # champignons (classe, x, y, x_min, x_max)
                    (Champignon,  300,  40,   250,  430),
                    (Champignon,  700,  40,   650,  830),
                    (Champignon,  640, 280,   620,  780),  # 4eme plateforme
                    (Champignon, 2370, 280,  2350, 2480),
                    (Champignon, 4840, 280,  4820, 4960),
                    (Champignon, 7520, 320,  7500, 7620),  # plateforme finale
                ],
            ),
            Level(
                name="Lagune",
                theme="water",
                length=8000,
                spawn=(100, 180),
                platforms=[
                    (0,    0, 8000, 40),
                    (0,    0,   50, 6000),
                    # -- zone 1 --
                    (160,  110, 120, 20),
                    (340,  170, 100, 20),
                    (520,  120, 150, 20),
                    (760,  210, 120, 20),
                    (980,  280, 160, 20),
                    (1250, 190, 140, 20),
                    (1490, 250, 130, 20),
                    (1740, 340, 150, 20),
                    # -- zone 2 --
                    (2000, 200, 130, 20),
                    (2220, 300, 110, 20),
                    (2420, 180, 150, 20),
                    (2650, 260, 120, 20),
                    (2880, 340, 140, 20),
                    (3100, 200, 130, 20),
                    (3320, 280, 150, 20),
                    (3560, 160, 120, 20),
                    (3780, 300, 140, 20),
                    # -- zone 3 --
                    (4020, 220, 130, 20),
                    (4240, 320, 110, 20),
                    (4460, 180, 150, 20),
                    (4700, 260, 130, 20),
                    (4920, 340, 120, 20),
                    (5160, 200, 140, 20),
                    (5380, 300, 130, 20),
                    (5600, 160, 150, 20),
                    (5820, 280, 120, 20),
                    # -- zone 4 --
                    (6060, 200, 140, 20),
                    (6280, 320, 130, 20),
                    (6500, 240, 150, 20),
                    (6720, 160, 120, 20),
                    (6940, 280, 140, 20),
                    (7160, 200, 130, 20),
                    (7380, 300, 120, 20),
                    (7600, 220, 150, 20),  # plateforme finale
                ],
                enemies=[
                    (Requin,       600,   40),
                    (NuageMechant, 1180, 320),
                    (Requin,      1620,   40),
                    (NuageMechant, 2500, 340),
                    (Requin,      3400,   40),
                    (NuageMechant, 4600, 380),
                    (Requin,      5800,   40),
                    (NuageMechant, 6800, 320),
                    (Requin,      7400,   40),
                ],
            ),
            Level(
                name="Cieux",
                theme="sky",
                length=8000,
                spawn=(100, 180),
                platforms=[
                    (0,    0, 8000, 40),
                    (0,    0,   50, 6000),
                    # -- zone 1 --
                    (320,  120, 110, 20),
                    (500,  210, 110, 20),
                    (680,  300, 110, 20),
                    (860,  230, 110, 20),
                    (1040, 340, 120, 20),
                    (1260, 260, 120, 20),
                    (1480, 380, 110, 20),
                    (1680, 300, 120, 20),
                    (1900, 420, 160, 20),
                    # -- zone 2 --
                    (2140, 280, 110, 20),
                    (2340, 380, 120, 20),
                    (2540, 260, 110, 20),
                    (2740, 360, 120, 20),
                    (2960, 240, 110, 20),
                    (3160, 340, 120, 20),
                    (3380, 200, 110, 20),
                    (3580, 320, 120, 20),
                    (3800, 420, 110, 20),
                    # -- zone 3 --
                    (4020, 300, 120, 20),
                    (4240, 200, 110, 20),
                    (4460, 360, 120, 20),
                    (4660, 260, 110, 20),
                    (4880, 380, 120, 20),
                    (5100, 240, 110, 20),
                    (5320, 340, 120, 20),
                    (5540, 200, 110, 20),
                    (5760, 320, 120, 20),
                    # -- zone 4 --
                    (5980, 420, 110, 20),
                    (6200, 300, 120, 20),
                    (6420, 200, 110, 20),
                    (6640, 360, 120, 20),
                    (6860, 260, 110, 20),
                    (7080, 380, 120, 20),
                    (7300, 240, 110, 20),
                    (7520, 340, 150, 20),  # plateforme finale
                ],
                enemies=[
                    (Elfe,   540,  250),
                    (Aigle,  900,  260),
                    (Dragon, 1540, 430),
                    (Elfe,  2560,  290),
                    (Aigle, 3400,  370),
                    (Dragon,4480,  390),
                    (Elfe,  5120,  270),
                    (Aigle, 6220,  330),
                    (Dragon,7100,  410),
                ],
            ),
        ]

    def _clear_world_platforms(self):
        keep = [self.game.player]
        for e in self.game.world.entities:
            if e is self.game.player:
                continue
            # Nettoyer les sprites visuels des plateformes
            if hasattr(e, 'clear_visuals'):
                e.clear_visuals()
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

        # Chemins des sprites selon le thème
        sprite_paths = {
            "ground": "assets/platform_tree.png",
            "water":  "assets/platform_algue.png",
            "sky":    "assets/platform_nuage.png",
        }
        sprite_path = sprite_paths.get(level.theme)

        for i, (x, y, w, h) in enumerate(level.platforms):
            p = self.game.PlatformClass(x, y, w, h, self.game.batch)
            if i in (0, 1):
                # Sol et mur : invisibles, collision uniquement
                p.shape.visible = False
            else:
                # Plateformes en l'air : sprite visuel
                if sprite_path:
                    p.set_sprite(sprite_path, level.theme, self.game.batch)
                else:
                    if level.theme == "ground":
                        p.shape.color = (130, 200, 110)
                    elif level.theme == "water":
                        p.shape.color = (80, 150, 180)
                    else:
                        p.shape.color = (210, 210, 220)
            self.game.world.add(p)

        for enemy_data in level.enemies:
            if len(enemy_data) == 5:
                enemy_cls, x, y, x_min, x_max = enemy_data
                self.game.enemy_manager.spawn(enemy_cls, x=x, y=y, x_min=x_min, x_max=x_max)
            else:
                enemy_cls, x, y = enemy_data
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