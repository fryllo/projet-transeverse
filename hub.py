# hub.py
# Hub de sélection de niveau — 3 zones (terre, eau, ciel)
# Le joueur marche vers un portail pour lancer le niveau correspondant.

import pyglet
import math
from pyglet import shapes
from pyglet.gl import GL_NEAREST


# ── Portail animé ──────────────────────────────────────────────────────────────

class Portal:
    """
    Portail visuel animé (anneau tournant + halo) positionné sur une plateforme.
    Quand le joueur entre dedans, on_enter() est appelé.
    """
    RADIUS    = 36
    RING_W    = 8
    LABEL_Y   = 90   # pixels au-dessus du centre

    def __init__(self, x, y, color, label, batch, group, on_enter):
        self.cx       = x
        self.cy       = y
        self.color    = color
        self.label    = label
        self.on_enter = on_enter
        self._timer   = 0.0
        self._active  = True
        self._entered = False

        r, g, b = color

        # Halo extérieur (large, semi-transparent)
        self._halo = shapes.Circle(x, y, self.RADIUS + 16,
                                   color=(r, g, b), batch=batch, group=group)
        self._halo.opacity = 60

        # Anneau principal
        self._ring = shapes.Circle(x, y, self.RADIUS,
                                   color=(r, g, b), batch=batch, group=group)
        self._ring.opacity = 180

        # Coeur blanc
        self._core = shapes.Circle(x, y, self.RADIUS - self.RING_W,
                                   color=(240, 245, 255), batch=batch, group=group)
        self._core.opacity = 200

        # Particules orbitales (8 petits cercles)
        self._particles = []
        for i in range(8):
            c = shapes.Circle(x, y, 5, color=(r, g, b), batch=batch, group=group)
            c.opacity = 220
            self._particles.append(c)

        # Label au-dessus
        self._label = pyglet.text.Label(
            label,
            font_name="Segoe UI", font_size=14,
            x=x, y=y + self.LABEL_Y,
            color=(r, g, b, 255),
            anchor_x="center", anchor_y="center",
            batch=batch, group=group,
        )

        # Numéro de niveau au centre
        num = {"PRAIRIE": "1", "LAGUNE": "2", "CIEUX": "3"}.get(label.upper(), "?")
        self._num = pyglet.text.Label(
            num,
            font_name="Segoe UI", font_size=22,
            x=x, y=y,
            color=(255, 255, 255, 230),
            anchor_x="center", anchor_y="center",
            batch=batch, group=group,
        )

    def update(self, dt, player, camera_offset):
        if not self._active:
            return

        self._timer += dt

        # Pulsation du halo
        pulse = abs(math.sin(self._timer * 2))
        self._halo.opacity  = int(40 + 40 * pulse)
        self._ring.opacity  = int(140 + 60 * pulse)
        self._core.opacity  = int(160 + 60 * pulse)

        # Particules orbitales
        for i, p in enumerate(self._particles):
            angle = self._timer * 1.8 + i * (math.pi / 4)
            r = self.RADIUS + 10
            p.x = int(self.cx - camera_offset + r * math.cos(angle))
            p.y = int(self.cy + r * math.sin(angle))

        # Position écran
        sx = int(self.cx - camera_offset)
        self._halo.x  = sx; self._ring.x  = sx; self._core.x  = sx
        self._label.x = sx; self._num.x   = sx

        # Détection entrée joueur
        px = player.x + player.width  / 2
        py = player.y + player.height / 2
        dist = math.hypot(px - self.cx, py - self.cy)
        if dist < self.RADIUS and not self._entered:
            self._entered = True
            self.on_enter()

        # Reset si joueur ressort
        if dist >= self.RADIUS + 10:
            self._entered = False

    def hide(self):
        self._active = False
        for s in ([self._halo, self._ring, self._core, self._label, self._num]
                  + self._particles):
            try: s.batch = None
            except: pass


# ── Panneau indicateur de zone ─────────────────────────────────────────────────

class ZoneSign:
    """Petit panneau flottant qui indique le nom de la zone."""

    def __init__(self, x, y, text, color, batch, group):
        self._label = pyglet.text.Label(
            text,
            font_name="Segoe UI", font_size=11,
            x=x, y=y,
            color=(*color, 200),
            anchor_x="center", anchor_y="center",
            batch=batch, group=group,
        )
        self._cx     = x
        self._timer  = 0.0

    def update(self, dt, camera_offset):
        self._timer += dt
        bob = math.sin(self._timer * 1.5) * 4
        self._label.x = int(self._cx - camera_offset)
        self._label.y = int(self._label.y + 0)  # y fixe

    def hide(self):
        try: self._label.batch = None
        except: pass


# ── Hub principal ──────────────────────────────────────────────────────────────

class Hub:
    """
    Map hub avec 3 zones :
      - Zone Terre  (x 0    → 1800) : background ground
      - Zone Eau    (x 1800 → 3600) : background water
      - Zone Ciel   (x 3600 → 5400) : background sky

    3 portails, un par zone, déclenchent le chargement du niveau correspondant.
    """

    LENGTH = 5500

    # Plateformes : (x, y, w, h)
    PLATFORMS = [
        # ── Sol + mur ──────────────────────────────────────────────────────
        (0,    0, 5500,  40),   # sol principal
        (0,    0,   50, 600),   # mur gauche

        # ── Zone Terre (x 0-1800) ──────────────────────────────────────────
        (150,  120, 160, 20),
        (400,  180, 140, 20),
        (620,  260, 160, 20),   # plateforme portail niveau 1
        (850,  160, 140, 20),
        (1050, 240, 160, 20),
        (1280, 140, 150, 20),
        (1500, 200, 160, 20),

        # ── Transition Terre→Eau (x 1700-1900) ────────────────────────────
        (1700, 100, 200, 20),

        # ── Zone Eau (x 1800-3600) ─────────────────────────────────────────
        (1950, 170, 140, 20),
        (2150, 240, 160, 20),
        (2380, 160, 140, 20),
        (2580, 260, 160, 20),   # plateforme portail niveau 2
        (2820, 180, 150, 20),
        (3020, 280, 140, 20),
        (3220, 200, 160, 20),
        (3420, 140, 150, 20),

        # ── Transition Eau→Ciel (x 3500-3700) ─────────────────────────────
        (3500, 100, 200, 20),

        # ── Zone Ciel (x 3600-5400) ────────────────────────────────────────
        (3700, 200, 130, 20),
        (3920, 300, 120, 20),
        (4120, 200, 130, 20),
        (4340, 320, 140, 20),
        (4540, 240, 130, 20),   # plateforme portail niveau 3
        (4760, 180, 140, 20),
        (4980, 300, 130, 20),
        (5200, 220, 140, 20),
    ]

    # Portails : (cx, cy, color_rgb, label, level_index)
    PORTAL_DEFS = [
        (700,  300, (130, 200,  80), "PRAIRIE", 0),
        (2660, 300, ( 60, 160, 220), "LAGUNE",  1),
        (4620, 280, (160, 200, 255), "CIEUX",   2),
    ]

    def __init__(self, game, on_level_selected):
        self._game             = game
        self._on_level_selected = on_level_selected
        self._portals          = []
        self._bgs              = []
        self._grp              = pyglet.graphics.Group(order=2)
        self._active           = False

    def load(self):
        """Charge le hub : plateformes, fonds et portails."""
        from moteur import Platform
        game = self._game

        # Vider le monde
        from level_system import LevelManager
        game.level_manager._clear_world_platforms()
        game.level_manager._clear_background()
        game.enemy_manager.clear()

        # Reset joueur
        game.player.x, game.player.y = 100, 80
        game.player.vel_x = game.player.vel_y = 0
        game.player.hp    = 10
        game.camera.reset()

        # ── Plateformes ───────────────────────────────────────────────────
        sprite_paths = {
            "ground": "assets/platform_tree.png",
            "water":  "assets/platform_algue.png",
            "sky":    "assets/platform_nuage.png",
        }

        for i, (x, y, w, h) in enumerate(self.PLATFORMS):
            p = Platform(x, y, w, h, game.batch)
            if i in (0, 1):
                p.shape.visible = False
            else:
                # Thème selon la zone x
                if x < 1800:
                    theme = "ground"
                elif x < 3600:
                    theme = "water"
                else:
                    theme = "sky"
                p.set_sprite(sprite_paths[theme], theme, game.batch)
            game.world.add(p)

        # ── Fonds (3 zones côte à côte) ───────────────────────────────────
        # On utilise des fonds statiques mais on les superpose
        # Le background se met à jour selon la position de la caméra
        self._ground_bg = None
        self._water_bg  = None
        self._sky_bg    = None

        # ── Portails ──────────────────────────────────────────────────────
        self._portals = []
        grp = pyglet.graphics.Group(order=3)
        for cx, cy, color, label, idx in self.PORTAL_DEFS:
            def make_cb(i=idx):
                return lambda: self._on_level_selected(i)
            portal = Portal(cx, cy, color, label,
                            game.batch, grp, make_cb())
            self._portals.append(portal)

        self._active = True

        # Charger les 3 bgs — on en affiche un seul à la fois selon la caméra
        w = game.window.width
        h = game.window.height
        from background import BackgroundBuilder
        self._ground_bg = BackgroundBuilder.create_ground(w, h, game.bg_batch)
        self._water_bg  = BackgroundBuilder.create_water(w, h, game.bg_batch)
        self._water_bg.set_visible(False)
        self._sky_bg    = BackgroundBuilder.create_sky(w, h, game.bg_batch)
        self._sky_bg.set_visible(False)

    def update(self, dt, player, camera_offset):
        if not self._active:
            return

        # Switcher le fond selon la zone du joueur
        px = player.x
        if px < 1800:
            self._ground_bg.set_visible(True)
            self._water_bg.set_visible(False)
            self._sky_bg.set_visible(False)
            self._ground_bg.update(camera_offset)
        elif px < 3600:
            self._ground_bg.set_visible(False)
            self._water_bg.set_visible(True)
            self._sky_bg.set_visible(False)
            self._water_bg.update(camera_offset)
        else:
            self._ground_bg.set_visible(False)
            self._water_bg.set_visible(False)
            self._sky_bg.set_visible(True)
            self._sky_bg.update(camera_offset)

        # Mettre à jour les portails
        for portal in self._portals:
            portal.update(dt, player, camera_offset)

    def hide(self):
        self._active = False
        for portal in self._portals:
            portal.hide()
        for bg in (self._ground_bg, self._water_bg, self._sky_bg):
            if bg:
                bg.set_visible(False)
