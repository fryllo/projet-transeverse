# theme.py
# Harmonisation graphique : couleurs, polices, boutons, icônes

import pyglet
from pyglet import shapes

# ── Palette ────────────────────────────────────────────────────────────────────

COLOR_BG          = (15,  20,  35, 255)   # fond sombre
COLOR_PANEL       = (25,  35,  55, 220)   # panneaux semi-transparents
COLOR_ACCENT      = (80, 160, 255, 255)   # bleu vif (focus / survol)
COLOR_ACCENT2     = (255, 120,  60, 255)  # orange (danger / vie faible)
COLOR_TEXT        = (220, 230, 255, 255)  # texte principal
COLOR_TEXT_DIM    = (120, 140, 180, 255)  # texte secondaire
COLOR_BTN_NORMAL  = (40,  55,  85, 255)   # bouton normal
COLOR_BTN_HOVER   = (60,  90, 140, 255)   # bouton survolé
COLOR_BTN_PRESS   = (30,  45,  70, 255)   # bouton pressé
COLOR_BTN_BORDER  = (80, 130, 200, 255)   # bordure bouton

# ── Polices ────────────────────────────────────────────────────────────────────
# Pyglet utilise les polices système ; adaptez selon votre OS.

FONT_TITLE  = "Segoe UI"     # titre principal
FONT_UI     = "Segoe UI"     # texte interface
FONT_MONO   = "Consolas"     # stats / valeurs numériques

SIZE_TITLE  = 48
SIZE_HEADER = 28
SIZE_BODY   = 18
SIZE_SMALL  = 13

# ── Helpers ────────────────────────────────────────────────────────────────────

def rgba(color, alpha=255):
    """Retourne un tuple RGBA depuis un tuple RGB ou RGBA."""
    if len(color) == 4:
        return color
    return (*color[:3], alpha)


def draw_panel(x, y, w, h, batch, group=None):
    """Rectangle de panneau semi-transparent."""
    return shapes.Rectangle(x, y, w, h,
                            color=COLOR_PANEL[:3],
                            batch=batch, group=group)


def draw_border(x, y, w, h, thickness, batch, group=None):
    """Cadre (4 rectangles) autour d'une zone."""
    t = thickness
    c = COLOR_BTN_BORDER[:3]
    rects = [
        shapes.Rectangle(x,         y,         w, t, color=c, batch=batch, group=group),   # bas
        shapes.Rectangle(x,         y + h - t, w, t, color=c, batch=batch, group=group),   # haut
        shapes.Rectangle(x,         y,         t, h, color=c, batch=batch, group=group),   # gauche
        shapes.Rectangle(x + w - t, y,         t, h, color=c, batch=batch, group=group),   # droite
    ]
    return rects


def make_label(text, x, y, batch, group=None,
               font_name=FONT_UI, font_size=SIZE_BODY,
               color=COLOR_TEXT, anchor_x="left", anchor_y="bottom"):
    """Crée un pyglet.text.Label avec les réglages par défaut du thème."""
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
