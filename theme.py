# theme.py
# Harmonisation graphique : couleurs, polices, boutons, pixel-art

import pyglet
from pyglet import shapes

# ── Palette UI ─────────────────────────────────────────────────────────────────

COLOR_BG          = (15,  20,  35, 255)
COLOR_PANEL       = (25,  35,  55, 220)
COLOR_ACCENT      = (80, 160, 255, 255)
COLOR_ACCENT2     = (255, 120,  60, 255)
COLOR_TEXT        = (220, 230, 255, 255)
COLOR_TEXT_DIM    = (120, 140, 180, 255)
COLOR_BTN_NORMAL  = (40,  55,  85, 255)
COLOR_BTN_HOVER   = (60,  90, 140, 255)
COLOR_BTN_PRESS   = (30,  45,  70, 255)
COLOR_BTN_BORDER  = (80, 130, 200, 255)

# ── Palette pixel-art ──────────────────────────────────────────────────────────

PIXEL = 4  # taille d'un "pixel" pixel-art en pixels écran

PX_RED_LIGHT  = (255,  80,  80)   # reflet segment rouge
PX_RED_MID    = (200,  30,  30)   # corps segment rouge
PX_RED_DARK   = (120,  10,  10)   # ombre segment rouge
PX_GRAY_LIGHT = ( 90,  90,  90)   # reflet segment vide
PX_GRAY_MID   = ( 55,  55,  55)   # corps segment vide
PX_GRAY_DARK  = ( 30,  30,  30)   # fond barre
PX_OUTLINE    = (  0,   0,   0)   # contour noir
PX_HEART_RED  = (220,  30,  30)   # cœur plein
PX_HEART_SHIN = (255, 120, 120)   # reflet cœur
PX_HEART_DARK = ( 80,   0,   0)   # ombre cœur

# ── Polices ────────────────────────────────────────────────────────────────────

FONT_TITLE  = "Segoe UI"
FONT_UI     = "Segoe UI"
FONT_MONO   = "Consolas"

SIZE_TITLE  = 48
SIZE_HEADER = 28
SIZE_BODY   = 18
SIZE_SMALL  = 13

# ── Cœur pixel-art ────────────────────────────────────────────────────────────
# 1=rouge, 2=reflet, 3=sombre, 0=transparent

_HEART_FULL = [
    [0, 1, 1, 0, 1, 1, 0],
    [1, 2, 1, 1, 1, 2, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
]

_HEART_EMPTY = [
    [0, 3, 3, 0, 3, 3, 0],
    [3, 2, 3, 3, 3, 2, 3],
    [3, 3, 3, 3, 3, 3, 3],
    [3, 3, 3, 3, 3, 3, 3],
    [0, 3, 3, 3, 3, 3, 0],
    [0, 0, 3, 3, 3, 0, 0],
    [0, 0, 0, 3, 0, 0, 0],
]

HEART_W = 7 * PIXEL   # largeur du cœur en pixels écran
HEART_H = 7 * PIXEL   # hauteur du cœur en pixels écran


def _heart_color(val, empty):
    if empty:
        if val == 2: return PX_GRAY_LIGHT
        if val == 3: return PX_GRAY_MID
    else:
        if val == 2: return PX_HEART_SHIN
        if val == 1: return PX_HEART_RED
        if val == 3: return PX_HEART_DARK
    return None


def make_heart(x, y, batch, group=None, empty=False):
    """
    Dessine un cœur pixel-art à la position (x, y).
    Retourne la liste des rectangles créés.
    """
    rects = []
    grid  = _HEART_EMPTY if empty else _HEART_FULL
    p     = PIXEL
    rows  = len(grid)

    for row_i, row in enumerate(grid):
        for col_i, val in enumerate(row):
            if val == 0:
                continue
            color = _heart_color(val, empty)
            if color is None:
                continue
            px = x + col_i * p
            py = y + (rows - 1 - row_i) * p
            rects.append(
                shapes.Rectangle(px, py, p, p, color=color,
                                 batch=batch, group=group)
            )
    return rects


# ── Helpers UI ─────────────────────────────────────────────────────────────────

def rgba(color, alpha=255):
    if len(color) == 4:
        return color
    return (*color[:3], alpha)


def draw_panel(x, y, w, h, batch, group=None):
    return shapes.Rectangle(x, y, w, h,
                            color=COLOR_PANEL[:3],
                            batch=batch, group=group)


def draw_border(x, y, w, h, thickness, batch, group=None):
    t = thickness
    c = COLOR_BTN_BORDER[:3]
    return [
        shapes.Rectangle(x, y,         w, t, color=c, batch=batch, group=group),
        shapes.Rectangle(x, y + h - t, w, t, color=c, batch=batch, group=group),
        shapes.Rectangle(x, y,         t, h, color=c, batch=batch, group=group),
        shapes.Rectangle(x + w - t, y, t, h, color=c, batch=batch, group=group),
    ]


def make_label(text, x, y, batch, group=None,
               font_name=FONT_UI, font_size=SIZE_BODY,
               color=COLOR_TEXT, anchor_x="left", anchor_y="bottom"):
    return pyglet.text.Label(
        text,
        font_name=font_name,
        font_size=font_size,
        x=x, y=y,
        color=rgba(color),
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        batch=batch,
        group=group,
    )