# hud.py
# HUD in-game : barre de PV pixel-art, stats debug, score

import pyglet
from pyglet import shapes
from theme import (
    COLOR_TEXT, COLOR_TEXT_DIM,
    FONT_UI, FONT_MONO, SIZE_SMALL,
    PIXEL, HEART_W, HEART_H,
    PX_RED_LIGHT, PX_RED_MID, PX_GRAY_MID, PX_GRAY_DARK, PX_OUTLINE,
    make_label, make_heart,
)


# ── Barre de vie pixel-art ─────────────────────────────────────────────────────

class HealthBar:
    """
    Barre de PV style pixel-art avec cœur et segments.

    x, y   : coin bas-gauche
    n_segs : nombre de segments
    max_hp : valeur maximum
    """

    SEG_W   = 16   # largeur d'un segment
    SEG_H   = 12   # hauteur d'un segment
    SEG_GAP = 2    # espace entre segments
    MARGIN  = 6    # espace entre cœur et barre

    def __init__(self, x, y, n_segs=10, max_hp=100, batch=None, group=None):
        self.x, self.y  = x, y
        self.n_segs     = n_segs
        self.max_hp     = max_hp
        self._hp        = max_hp

        # Cœur (plein et vide, on bascule la visibilité)
        self._heart_full  = make_heart(x, y, batch, group, empty=False)
        self._heart_empty = make_heart(x, y, batch, group, empty=True)
        self._set_heart(full=True)

        # Position de départ de la barre
        bx = x + HEART_W + self.MARGIN
        by = y + (HEART_H - self.SEG_H) // 2

        # Contour noir global
        total_w = n_segs * (self.SEG_W + self.SEG_GAP) - self.SEG_GAP
        self._outline = shapes.Rectangle(
            bx - 2, by - 2, total_w + 4, self.SEG_H + 4,
            color=PX_OUTLINE, batch=batch, group=group,
        )

        # Fond gris foncé
        self._bg = shapes.Rectangle(
            bx, by, total_w, self.SEG_H,
            color=PX_GRAY_DARK, batch=batch, group=group,
        )

        # Segments rouges (pleins) + reflets + gris (vides)
        self._full  = []
        self._shine = []
        self._empty = []

        for i in range(n_segs):
            sx = bx + i * (self.SEG_W + self.SEG_GAP)
            self._full.append(
                shapes.Rectangle(sx, by, self.SEG_W, self.SEG_H,
                                 color=PX_RED_MID, batch=batch, group=group)
            )
            self._shine.append(
                shapes.Rectangle(sx, by + self.SEG_H - PIXEL, self.SEG_W, PIXEL,
                                 color=PX_RED_LIGHT, batch=batch, group=group)
            )
            self._empty.append(
                shapes.Rectangle(sx, by, self.SEG_W, self.SEG_H,
                                 color=PX_GRAY_MID, batch=batch, group=group)
            )

        self._refresh()

    def _set_heart(self, full: bool):
        for r in self._heart_full:  r.visible = full
        for r in self._heart_empty: r.visible = not full

    def _refresh(self):
        filled = round(self._hp / self.max_hp * self.n_segs)
        for i in range(self.n_segs):
            is_full = i < filled
            self._full [i].visible  = is_full
            self._shine[i].visible  = is_full
            self._empty[i].visible  = not is_full
        self._set_heart(full=self._hp > 0)

    def set_hp(self, hp: int):
        self._hp = max(0, min(hp, self.max_hp))
        self._refresh()


# ── Panneau de stats debug ─────────────────────────────────────────────────────

class StatsPanel:
    LINES = ["X", "Y", "VX", "VY", "GROUND"]

    def __init__(self, x, y, batch, group=None):
        self._labels = {}
        dy = 0
        for key in reversed(self.LINES):
            self._labels[key] = make_label(
                f"{key:8s}: —", x, y + dy, batch, group,
                font_name=FONT_MONO, font_size=SIZE_SMALL, color=COLOR_TEXT_DIM,
            )
            dy += SIZE_SMALL + 4

    def update(self, player):
        self._labels["X"     ].text = f"{'X':8s}: {player.x:7.1f}"
        self._labels["Y"     ].text = f"{'Y':8s}: {player.y:7.1f}"
        self._labels["VX"    ].text = f"{'VX':8s}: {player.vel_x:7.1f}"
        self._labels["VY"    ].text = f"{'VY':8s}: {player.vel_y:7.1f}"
        self._labels["GROUND"].text = f"{'GROUND':8s}: {'YES' if player.on_ground else 'NO ':3s}"


# ── HUD principal ──────────────────────────────────────────────────────────────

class HUD:
    def __init__(self, width, height, batch,
                 max_hp: int = 100, show_stats: bool = True):
        self._visible = True
        self._grp     = pyglet.graphics.Group(order=5)

        # Barre de vie en haut à gauche
        self._health = HealthBar(
            x=16, y=height - 50,
            n_segs=10, max_hp=max_hp,
            batch=batch, group=self._grp,
        )

        # Score en haut au centre
        self._score_label = make_label(
            "SCORE  0", width // 2, height - 14,
            batch, self._grp,
            font_name=FONT_UI, font_size=SIZE_SMALL, color=COLOR_TEXT,
            anchor_x="center", anchor_y="top",
        )

        # Stats debug en haut à droite
        self._stats: StatsPanel | None = None
        if show_stats:
            self._stats = StatsPanel(
                width - 180, height - 20 - 32,
                batch, self._grp,
            )

    def update(self, player, hp: int | None = None, score: int = 0):
        if not self._visible:
            return
        if hp is None:
            hp = getattr(player, "hp", self._health.max_hp)
        self._health.set_hp(hp)
        self._score_label.text = f"SCORE  {score:06d}"
        if self._stats:
            self._stats.update(player)

    def show(self):
        self._visible = True
        self._grp.visible = True

    def hide(self):
        self._visible = False
        self._grp.visible = False