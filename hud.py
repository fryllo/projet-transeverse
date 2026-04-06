# hud.py
import pyglet
from pyglet import shapes
from theme import (
    COLOR_TEXT, COLOR_TEXT_DIM,
    FONT_UI, FONT_MONO, SIZE_SMALL,
    make_label,
)


# ── Cœur pixel art (dessiné en SVG-like avec rectangles) ─────────────────────

def _make_heart(cx, cy, batch, group, full=True):
    """
    Dessine un cœur pixel art avec des rectangles pyglet.
    full=True  → cœur rouge plein
    full=False → cœur gris (vide)
    """
    S = 3  # taille d'un pixel
    if full:
        c = (200, 30, 30)
        hi = (240, 80, 80)   # reflet clair
    else:
        c = (70, 70, 80)
        hi = (90, 90, 100)

    # Grille pixel du cœur (1=corps, 2=reflet, 0=vide)
    # 7x6 pixels
    grid = [
        [0, 1, 1, 0, 1, 1, 0],
        [1, 2, 1, 1, 2, 1, 1],
        [1, 2, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ]

    rects = []
    rows = len(grid)
    for row_i, row in enumerate(grid):
        for col_i, val in enumerate(row):
            if val == 0:
                continue
            color = hi if val == 2 else c
            x = cx + col_i * S - (len(row) * S) // 2
            y = cy + (rows - row_i - 1) * S - (rows * S) // 2
            r = shapes.Rectangle(x, y, S, S, color=color, batch=batch, group=group)
            rects.append(r)
    return rects


# ── Barre de vie pixel art ────────────────────────────────────────────────────

class PixelHealthBar:
    """
    Barre de vie style pixel art :
    [♥] [████████░░░░░░]
    Rouge plein → orange → gris selon les PV restants.
    """

    BAR_W    = 200
    BAR_H    = 18
    CELL_W   = 10   # largeur d'un bloc
    CELL_GAP = 2    # espace entre blocs
    BORDER   = 2    # épaisseur bordure

    def __init__(self, x, y, max_hp, batch, group=None):
        self.x, self.y   = x, y
        self.max_hp      = max_hp
        self._hp         = max_hp
        self._batch      = batch
        self._group      = group
        self._cells      = []
        self._heart      = []

        # Nombre de blocs
        self._n_cells = 20

        # Fond de la barre (gris foncé, style métal)
        bx = x + 28
        self._bg = shapes.Rectangle(
            bx - self.BORDER, y - self.BORDER,
            self.BAR_W + self.BORDER * 2,
            self.BAR_H + self.BORDER * 2,
            color=(20, 20, 25), batch=batch, group=group
        )
        # Bordure externe (pixel)
        self._border_top = shapes.Rectangle(
            bx - self.BORDER, y + self.BAR_H,
            self.BAR_W + self.BORDER * 2, self.BORDER,
            color=(60, 60, 70), batch=batch, group=group
        )
        self._border_bot = shapes.Rectangle(
            bx - self.BORDER, y - self.BORDER,
            self.BAR_W + self.BORDER * 2, self.BORDER,
            color=(60, 60, 70), batch=batch, group=group
        )

        # Blocs de la barre
        cell_w = (self.BAR_W - (self._n_cells - 1) * self.CELL_GAP) // self._n_cells
        for i in range(self._n_cells):
            cx = bx + i * (cell_w + self.CELL_GAP)
            # Fond gris du bloc (vide)
            bg = shapes.Rectangle(cx, y, cell_w, self.BAR_H,
                                  color=(45, 45, 55), batch=batch, group=group)
            # Bloc coloré (plein)
            fg = shapes.Rectangle(cx, y, cell_w, self.BAR_H,
                                  color=(200, 30, 30), batch=batch, group=group)
            # Reflet haut
            hl = shapes.Rectangle(cx, y + self.BAR_H - 4, cell_w, 3,
                                  color=(240, 80, 80), batch=batch, group=group)
            self._cells.append((bg, fg, hl))

        # Cœur pixel art à gauche
        heart_cx = x + 10
        heart_cy = y + self.BAR_H // 2
        self._heart = _make_heart(heart_cx, heart_cy, batch, group, full=True)
        self._heart_empty = _make_heart(heart_cx, heart_cy, batch, group, full=False)
        # Cacher le cœur vide au départ
        for r in self._heart_empty:
            r.visible = False

        self._refresh()

    def set_hp(self, hp):
        self._hp = max(0, min(hp, self.max_hp))
        self._refresh()

    def _refresh(self):
        ratio = self._hp / self.max_hp
        filled = round(ratio * self._n_cells)

        # Couleur selon ratio
        if ratio > 0.5:
            color_fg = (200, 30, 30)
            color_hl = (240, 80, 80)
        elif ratio > 0.25:
            color_fg = (200, 120, 20)
            color_hl = (240, 170, 60)
        else:
            color_fg = (160, 20, 20)
            color_hl = (200, 50, 50)

        for i, (bg, fg, hl) in enumerate(self._cells):
            if i < filled:
                fg.color   = color_fg
                hl.color   = color_hl
                fg.opacity = 255
                hl.opacity = 255
            else:
                fg.opacity = 0
                hl.opacity = 0

        # Cœur : plein si > 25%, vide sinon
        full = ratio > 0.0
        for r in self._heart:
            r.opacity = 255 if full else 0
        for r in self._heart_empty:
            r.opacity = 0 if full else 255


# ── Panneau de stats debug ────────────────────────────────────────────────────

class StatsPanel:
    LINES = ["X", "Y", "VX", "VY", "GROUND"]

    def __init__(self, x, y, batch, group=None):
        self._labels = {}
        dy = 0
        for k in reversed(self.LINES):
            lbl = make_label(f"{k:8s}: —", x, y + dy, batch, group,
                             font_name=FONT_MONO, font_size=SIZE_SMALL,
                             color=COLOR_TEXT_DIM)
            self._labels[k] = lbl
            dy += SIZE_SMALL + 4

    def update(self, player):
        self._labels["X"     ].text = f"{'X':8s}: {player.x:7.1f}"
        self._labels["Y"     ].text = f"{'Y':8s}: {player.y:7.1f}"
        self._labels["VX"    ].text = f"{'VX':8s}: {player.vel_x:7.1f}"
        self._labels["VY"    ].text = f"{'VY':8s}: {player.vel_y:7.1f}"
        self._labels["GROUND"].text = f"{'GROUND':8s}: {'YES' if player.on_ground else 'NO ':3s}"


# ── HUD principal ─────────────────────────────────────────────────────────────

class HUD:
    HP_BAR_X = 12
    HP_BAR_H = 18

    def __init__(self, width, height, batch, max_hp=100, show_stats=True):
        self._visible = True
        self._grp     = pyglet.graphics.Group(order=5)

        bar_y = height - self.HP_BAR_H - 14

        self._health = PixelHealthBar(
            self.HP_BAR_X, bar_y, max_hp, batch, self._grp
        )

        self._score_label = make_label(
            "SCORE  000000",
            width // 2, height - 14,
            batch, self._grp,
            font_name=FONT_UI, font_size=SIZE_SMALL,
            color=COLOR_TEXT,
            anchor_x="center", anchor_y="top",
        )

        self._stats = None
        if show_stats:
            self._stats = StatsPanel(
                width - 180, height - 20 - (self.HP_BAR_H + 12),
                batch, self._grp,
            )

    def update(self, player, hp=None, score=0):
        if not self._visible:
            return
        if hp is None:
            hp = getattr(player, "hp", 100)
        self._health.set_hp(hp)
        self._score_label.text = f"SCORE  {score:06d}"
        if self._stats:
            self._stats.update(player)

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False