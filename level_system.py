# level_system.py
import math
import pyglet
from pyglet import shapes
from enemies import Dragon, Elfe, NuageMechant, Aigle, Requin, Champignon
from background import BackgroundBuilder
from npc import NPC


class Level:
    def __init__(self, name, theme, length, spawn, platforms, enemies):
        self.name = name
        self.theme = theme
        self.length = length
        self.spawn = spawn
        self.platforms = platforms
        self.enemies = enemies


# ── Portail simple ─────────────────────────────────────────────────────────────

class Portal:
    RADIUS = 36

    def __init__(self, world_x, world_y, color, label, batch, on_enter):
        self.world_x  = world_x
        self.world_y  = world_y
        self.on_enter = on_enter
        self._timer   = 0.0
        self._entered = False
        self._active  = True
        r, g, b       = color
        grp = pyglet.graphics.Group(order=10)

        self._halo = shapes.Circle(world_x, world_y, self.RADIUS + 16,
                                   color=(r,g,b), batch=batch, group=grp)
        self._halo.opacity = 60
        self._ring = shapes.Circle(world_x, world_y, self.RADIUS,
                                   color=(r,g,b), batch=batch, group=grp)
        self._ring.opacity = 180
        self._core = shapes.Circle(world_x, world_y, self.RADIUS - 8,
                                   color=(240,245,255), batch=batch, group=grp)
        self._core.opacity = 200
        self._particles = []
        for i in range(8):
            c = shapes.Circle(world_x, world_y, 5, color=(r,g,b),
                              batch=batch, group=grp)
            c.opacity = 220
            self._particles.append(c)
        self._label = pyglet.text.Label(
            label, font_name="Segoe UI", font_size=14,
            x=world_x, y=world_y + 80,
            color=(r, g, b, 255),
            anchor_x="center", anchor_y="center",
            batch=batch, group=grp)
        num = {"PRAIRIE": "1", "LAGUNE": "2", "CIEUX": "3"}.get(label.upper(), "?")
        self._num = pyglet.text.Label(
            num, font_name="Segoe UI", font_size=22,
            x=world_x, y=world_y,
            color=(255,255,255,230),
            anchor_x="center", anchor_y="center",
            batch=batch, group=grp)

    def update(self, dt, player, camera_offset):
        if not self._active:
            return
        self._timer += dt
        pulse = abs(math.sin(self._timer * 2))
        self._halo.opacity = int(40 + 40 * pulse)
        self._ring.opacity = int(140 + 60 * pulse)
        self._core.opacity = int(160 + 60 * pulse)

        sx = int(self.world_x - camera_offset)
        self._halo.x = sx; self._ring.x = sx; self._core.x = sx
        self._label.x = sx; self._num.x = sx

        for i, p in enumerate(self._particles):
            angle = self._timer * 1.8 + i * (math.pi / 4)
            p.x = int(sx + (self.RADIUS + 10) * math.cos(angle))
            p.y = int(self.world_y + (self.RADIUS + 10) * math.sin(angle))

        px = player.x + player.width  / 2
        py = player.y + player.height / 2
        if math.hypot(px - self.world_x, py - self.world_y) < self.RADIUS:
            if not self._entered:
                self._entered = True
                self.on_enter()
        else:
            self._entered = False

    def destroy(self):
        self._active = False
        for s in [self._halo, self._ring, self._core,
                  self._label, self._num] + self._particles:
            try: s.batch = None
            except: pass


# ── LevelManager ──────────────────────────────────────────────────────────────

class LevelManager:
    HUB_INDEX = 3   # index réservé au hub

    def __init__(self, game):
        self.game    = game
        self.index   = 0
        self.levels  = self._build_levels()
        self._bg_shapes   = []
        self._current_bg  = None
        self._portals     = []
        self._npcs        = []
        self._hub_bgs     = {}
        self._hub_active  = False

    def _build_levels(self):
        return [
            Level(
                name="Prairie",
                theme="ground",
                length=8000,
                spawn=(100, 80),
                platforms=[
                    (0,    0, 8000, 40),
                    (0,    0,   50, 6000),
                    (180,  130, 130, 20),
                    (380,  190, 140, 20),
                    (620,  260, 160, 20),
                    (870,  160, 120, 20),
                    (1080, 240, 180, 20),
                    (1360, 320, 130, 20),
                    (1560, 220, 150, 20),
                    (1820, 280, 140, 20),
                    (2100, 180, 150, 20),
                    (2350, 260, 130, 20),
                    (2560, 160, 140, 20),
                    (2780, 300, 160, 20),
                    (3020, 200, 120, 20),
                    (3220, 320, 150, 20),
                    (3460, 240, 130, 20),
                    (3680, 180, 160, 20),
                    (3900, 280, 140, 20),
                    (4150, 200, 150, 20),
                    (4380, 300, 130, 20),
                    (4600, 160, 160, 20),
                    (4820, 260, 140, 20),
                    (5060, 340, 120, 20),
                    (5280, 220, 150, 20),
                    (5500, 300, 130, 20),
                    (5720, 180, 160, 20),
                    (5920, 260, 140, 20),
                    (6150, 200, 150, 20),
                    (6380, 320, 130, 20),
                    (6600, 240, 160, 20),
                    (6820, 160, 140, 20),
                    (7060, 280, 130, 20),
                    (7280, 200, 150, 20),
                    (7500, 300, 120, 20),
                ],
                enemies=[
                    (Aigle,      520,  300),
                    (Dragon,    1500,   60),
                    (Aigle,     2700,  340),
                    (Dragon,    3500,   60),
                    (Aigle,     4900,  300),
                    (Dragon,    6000,   60),
                    (Champignon,  300,  40,   250,  430),
                    (Champignon,  700,  40,   650,  830),
                    (Champignon,  640, 280,   620,  780),
                    (Champignon, 2370, 280,  2350, 2480),
                    (Champignon, 4840, 280,  4820, 4960),
                    (Champignon, 7520, 320,  7500, 7620),
                ],
            ),
            Level(
                name="Lagune",
                theme="water",
                length=8000,
                spawn=(100, 80),
                platforms=[
                    (0,    0, 8000, 40),
                    (0,    0,   50, 6000),
                    (160,  110, 120, 20),
                    (340,  170, 100, 20),
                    (520,  120, 150, 20),
                    (760,  210, 120, 20),
                    (980,  280, 160, 20),
                    (1250, 190, 140, 20),
                    (1490, 250, 130, 20),
                    (1740, 340, 150, 20),
                    (2000, 200, 130, 20),
                    (2220, 300, 110, 20),
                    (2420, 180, 150, 20),
                    (2650, 260, 120, 20),
                    (2880, 340, 140, 20),
                    (3100, 200, 130, 20),
                    (3320, 280, 150, 20),
                    (3560, 160, 120, 20),
                    (3780, 300, 140, 20),
                    (4020, 220, 130, 20),
                    (4240, 320, 110, 20),
                    (4460, 180, 150, 20),
                    (4700, 260, 130, 20),
                    (4920, 340, 120, 20),
                    (5160, 200, 140, 20),
                    (5380, 300, 130, 20),
                    (5600, 160, 150, 20),
                    (5820, 280, 120, 20),
                    (6060, 200, 140, 20),
                    (6280, 320, 130, 20),
                    (6500, 240, 150, 20),
                    (6720, 160, 120, 20),
                    (6940, 280, 140, 20),
                    (7160, 200, 130, 20),
                    (7380, 300, 120, 20),
                    (7600, 220, 150, 20),
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
                spawn=(100, 120),
                platforms=[
                    (0,    0, 8000, 40),
                    (0,    0,   50, 6000),
                    (320,  120, 110, 20),
                    (500,  210, 110, 20),
                    (680,  300, 110, 20),
                    (860,  230, 110, 20),
                    (1040, 340, 120, 20),
                    (1260, 260, 120, 20),
                    (1480, 380, 110, 20),
                    (1680, 300, 120, 20),
                    (1900, 420, 160, 20),
                    (2140, 280, 110, 20),
                    (2340, 380, 120, 20),
                    (2540, 260, 110, 20),
                    (2740, 360, 120, 20),
                    (2960, 240, 110, 20),
                    (3160, 340, 120, 20),
                    (3380, 200, 110, 20),
                    (3580, 320, 120, 20),
                    (3800, 420, 110, 20),
                    (4020, 300, 120, 20),
                    (4240, 200, 110, 20),
                    (4460, 360, 120, 20),
                    (4660, 260, 110, 20),
                    (4880, 380, 120, 20),
                    (5100, 240, 110, 20),
                    (5320, 340, 120, 20),
                    (5540, 200, 110, 20),
                    (5760, 320, 120, 20),
                    (5980, 420, 110, 20),
                    (6200, 300, 120, 20),
                    (6420, 200, 110, 20),
                    (6640, 360, 120, 20),
                    (6860, 260, 110, 20),
                    (7080, 380, 120, 20),
                    (7300, 240, 110, 20),
                    (7520, 340, 150, 20),
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
                    (Elfe,  6640,  370),
                ],
            ),
        ]

    # ── Hub comme niveau spécial ───────────────────────────────────────────────

    def _hub_platforms(self):
        """Plateformes du hub — même format que les niveaux normaux."""
        return [
            # Sol + mur (index 0 et 1 = invisibles)
            (0,    0, 5500,  40),
            (0,    0,   50, 600),
            # Zone Terre
            (150,  120, 160, 20),
            (400,  180, 140, 20),
            (620,  260, 160, 20),
            (850,  160, 140, 20),
            (1050, 240, 160, 20),
            (1280, 140, 150, 20),
            (1500, 200, 160, 20),
            (1700, 100, 200, 20),
            # Zone Eau
            (1950, 170, 140, 20),
            (2150, 240, 160, 20),
            (2380, 160, 140, 20),
            (2580, 260, 160, 20),
            (2820, 180, 150, 20),
            (3020, 280, 140, 20),
            (3220, 200, 160, 20),
            (3420, 140, 150, 20),
            (3500, 100, 200, 20),
            # Zone Ciel
            (3700, 200, 130, 20),
            (3920, 300, 120, 20),
            (4120, 200, 130, 20),
            (4340, 320, 140, 20),
            (4540, 240, 130, 20),
            (4760, 180, 140, 20),
            (4980, 300, 130, 20),
            (5200, 220, 140, 20),
        ]

    def load_hub(self):
        """Charge le hub comme un niveau spécial."""
        self._clear_world_platforms()
        self._clear_background()
        self.game.enemy_manager.clear()
        self._clear_portals()

        self.index = self.HUB_INDEX
        self._hub_active = True

        # Reset joueur
        self.game.player.x         = 100
        self.game.player.y         = 80
        self.game.player.vel_x     = 0
        self.game.player.vel_y     = 0
        self.game.player.on_ground = False
        self.game.player.hp        = 10
        self.game.camera.reset()
        self.game.camera.level_width = 5500

        # Plateformes — même système que les niveaux normaux
        platforms = self._hub_platforms()
        sprite_paths = {
            "ground": "assets/platform_tree.png",
            "water":  "assets/platform_algue.png",
            "sky":    "assets/platform_nuage.png",
        }
        for i, (x, y, w, h) in enumerate(platforms):
            p = self.game.PlatformClass(x, y, w, h, self.game.batch)
            if i in (0, 1):
                p.shape.visible = False
            else:
                # Thème selon zone x
                if x < 1800:
                    theme = "ground"
                elif x < 3600:
                    theme = "water"
                else:
                    theme = "sky"
                p.set_sprite(sprite_paths[theme], theme, self.game.batch)
            self.game.world.add(p)

        # PNJ hub — champignon/poisson/oiseau près de chaque portail
        npc_defs = [
            (500,  40, "assets/npc_champignon.png", "Bienvenue dans\nle Niveau 1 !"),
            (2460, 40, "assets/npc_poisson.png",    "Bienvenue dans\nle Niveau 2 !"),
            (4420, 40, "assets/npc_oiseau.png",     "Bienvenue dans\nle Niveau 3 !"),
        ]
        for nx, ny, spr, txt in npc_defs:
            self._npcs.append(NPC(nx, ny, spr, txt, self.game.batch))

        # Portails
        portal_defs = [
            (700,  300, (130, 200,  80), "PRAIRIE", 0),
            (2660, 300, ( 60, 160, 220), "LAGUNE",  1),
            (4620, 280, (160, 200, 255), "CIEUX",   2),
        ]
        for cx, cy, color, label, idx in portal_defs:
            def make_cb(i=idx):
                return lambda: self._on_portal_enter(i)
            self._portals.append(
                Portal(cx, cy, color, label, self.game.batch, make_cb())
            )

        # Fonds des 3 zones
        w = self.game.window.width
        h = self.game.window.height
        self._hub_bgs["ground"] = BackgroundBuilder.create_ground(w, h, self.game.bg_batch)
        self._hub_bgs["water"]  = BackgroundBuilder.create_water(w, h, self.game.bg_batch)
        self._hub_bgs["water"].set_visible(False)
        self._hub_bgs["sky"]    = BackgroundBuilder.create_sky(w, h, self.game.bg_batch)
        self._hub_bgs["sky"].set_visible(False)

    def _on_portal_enter(self, level_index):
        """Appelé quand le joueur entre dans un portail."""
        self._hub_active = False
        self._clear_portals()
        for bg in self._hub_bgs.values():
            bg.set_visible(False)
        self._hub_bgs.clear()
        # Utiliser le callback du game
        self.game._on_start_level(level_index)

    def _clear_portals(self):
        for portal in self._portals:
            portal.destroy()
        self._portals.clear()
        for npc in self._npcs:
            npc.destroy()
        self._npcs.clear()

    def _clear_world_platforms(self):
        keep = [self.game.player]
        for e in self.game.world.entities:
            if e is self.game.player:
                continue
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
        self._hub_active = False
        self._clear_portals()  # nettoie aussi les NPCs
        for bg in self._hub_bgs.values():
            bg.set_visible(False)
        self._hub_bgs.clear()

        self.index = index % len(self.levels)
        level = self.levels[self.index]

        self._clear_world_platforms()
        self._clear_background()
        self.game.enemy_manager.clear()

        self.game.player.x, self.game.player.y = level.spawn
        self.game.player.vel_x = 0
        self.game.player.vel_y = 0
        self.game.player.on_ground = False
        self.game.player.hp = 10

        sprite_paths = {
            "ground": "assets/platform_tree.png",
            "water":  "assets/platform_algue.png",
            "sky":    "assets/platform_nuage.png",
        }
        sprite_path = sprite_paths.get(level.theme)

        for i, (x, y, w, h) in enumerate(level.platforms):
            p = self.game.PlatformClass(x, y, w, h, self.game.batch)
            if i in (0, 1):
                p.shape.visible = False
            else:
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

        # PNJ dans les niveaux (2 par niveau, dialogue vide)
        level_npcs = {
            "ground": [
                (800,  40, "assets/npc_champignon.png"),
                (3000, 40, "assets/npc_champignon.png"),
            ],
            "water": [
                (900,  40, "assets/npc_poisson.png"),
                (3200, 40, "assets/npc_poisson.png"),
            ],
            "sky": [
                (1000, 40, "assets/npc_oiseau.png"),
                (3500, 40, "assets/npc_oiseau.png"),
            ],
        }
        for nx, ny, spr in level_npcs.get(level.theme, []):
            self._npcs.append(NPC(nx, ny, spr, "", self.game.batch))

        if level.theme == "ground":
            self._current_bg = BackgroundBuilder.create_ground(self.game.window.width, self.game.window.height, self.game.bg_batch)
        elif level.theme == "water":
            self._current_bg = BackgroundBuilder.create_water(self.game.window.width, self.game.window.height, self.game.bg_batch)
        else:
            self._current_bg = BackgroundBuilder.create_sky(self.game.window.width, self.game.window.height, self.game.bg_batch)

    def update_background(self):
        if self._hub_active:
            # Switcher le fond selon la zone du joueur
            px = self.game.player.x
            if px < 1800:
                zone = "ground"
            elif px < 3600:
                zone = "water"
            else:
                zone = "sky"
            for k, bg in self._hub_bgs.items():
                bg.set_visible(k == zone)
                if k == zone:
                    bg.update(self.game.camera.offset_x)
            # Mettre à jour les portails et NPC
            for portal in self._portals:
                portal.update(0, self.game.player, self.game.camera.offset_x)
            for npc in self._npcs:
                npc.update(self.game.player, self.game.camera.offset_x)
        elif self._current_bg:
            self._current_bg.update(self.game.camera.offset_x)
            for npc in self._npcs:
                npc.update(self.game.player, self.game.camera.offset_x)

    @property
    def current_level(self):
        if self._hub_active or self.index >= len(self.levels):
            # Retourner un niveau factice pour le hub
            class _HubLevel:
                length = 5500
                name   = "Hub"
                theme  = "hub"
            return _HubLevel()
        return self.levels[self.index]

    def next_level(self):
        self.load(self.index + 1)