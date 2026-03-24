# hud.py
# HUD in-game : barre de PV, stats (position, vitesse, état sol)
#
# Usage dans Game :
#   from hud import HUD
#   self.hud = HUD(WIDTH, HEIGHT, self.batch)
#
# Chaque frame, dans update() :
#   self.hud.update(player=self.player)

import pyglet
from pyglet import shapes
from theme import (
    COLOR_ACCENT, COLOR_ACCENT2, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_BTN_NORMAL, COLOR_BTN_BORDER,
    FONT_UI, FONT_MONO,
    SIZE_BODY, SIZE_SMALL,
    make_label, draw_panel, draw_border,
)

# ── Barre de vie ───────────────────────────────────────────────────────────────

class HealthBar:
    """
    Barre de PV horizontale.

    Paramètres
    ----------
    x, y         : coin bas-gauche
    w, h         : dimensions totales
    max_hp       : valeur maximale
    batch, group : rendu pyglet
    """

    def __init__(self, x, y, w, h, max_hp, batch, group=None):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.max_hp = max_hp
        self._hp = max_hp

        # fond
        self._bg = shapes.Rectangle(x, y, w, h,
                                    color=COLOR_BTN_NORMAL[:3],
                                    batch=batch, group=group)
        # barre colorée
        self._bar = shapes.Rectangle(x, y, w, h,
                                     color=COLOR_ACCENT[:3],
                                     batch=batch, group=group)
        # bordure
        self._borders = draw_border(x, y, w, h, 2, batch, group)

        # libellé "HP"
        self._label = make_label(
            f"HP  {self._hp}/{self.max_hp}",
            x + 6, y + h // 2,
            batch, group,
            font_name=FONT_MONO, font_size=SIZE_SMALL,
            color=COLOR_TEXT,
            anchor_x="left", anchor_y="center",
        )

    def set_hp(self, hp: int):
        self._hp = max(0, min(hp, self.max_hp))
        ratio = self._hp / self.max_hp

        # couleur : vert→orange→rouge selon ratio
        if ratio > 0.5:
            color = COLOR_ACCENT[:3]
        elif ratio > 0.25:
            color = (200, 160, 40)
        else:
            color = COLOR_ACCENT2[:3]

        self._bar.width = max(0, int(self.w * ratio))
        self._bar.color = color
        self._label.text = f"HP  {self._hp}/{self.max_hp}"


# ── Panneau de stats ───────────────────────────────────────────────────────────

class StatsPanel:
    """
    Mini-panneau affichant position, vitesse et état au sol du joueur.
    Affiché en haut-droite de l'écran (mode debug / dev).
    """

    LINES = ["X", "Y", "VX", "VY", "GROUND"]

    def __init__(self, x, y, batch, group=None):
        self._labels = {}
        dy = 0
        for key in reversed(self.LINES):
            lbl = make_label(
                f"{key:8s}: —",
                x, y + dy,
                batch, group,
                font_name=FONT_MONO, font_size=SIZE_SMALL,
                color=COLOR_TEXT_DIM,
            )
            self._labels[key] = lbl
            dy += SIZE_SMALL + 4

    def update(self, player):
        self._labels["X"     ].text = f"{'X':8s}: {player.x:7.1f}"
        self._labels["Y"     ].text = f"{'Y':8s}: {player.y:7.1f}"
        self._labels["VX"    ].text = f"{'VX':8s}: {player.vel_x:7.1f}"
        self._labels["VY"    ].text = f"{'VY':8s}: {player.vel_y:7.1f}"
        self._labels["GROUND"].text = f"{'GROUND':8s}: {'YES' if player.on_ground else 'NO ':3s}"


# ── HUD principal ──────────────────────────────────────────────────────────────

class HUD:
    """
    Regroupe tous les éléments affichés pendant le jeu.

    Paramètres
    ----------
    width, height : dimensions de la fenêtre
    batch         : pyglet.graphics.Batch partagé
    max_hp        : PV maximum du joueur (défaut 100)
    show_stats    : afficher le panneau de debug (défaut True)
    """

    HP_BAR_W  = 200
    HP_BAR_H  = 20
    HP_BAR_X  = 16
    HP_BAR_Y  = None   # calculé depuis le haut

    def __init__(self, width, height, batch,
                 max_hp: int = 100, show_stats: bool = True):
        self._visible = True
        self._grp = pyglet.graphics.Group(order=5)

        bar_y = height - self.HP_BAR_H - 12

        # ── barre de vie ──────────────────────────────────────────────────────
        self._health = HealthBar(
            self.HP_BAR_X, bar_y,
            self.HP_BAR_W, self.HP_BAR_H,
            max_hp, batch, self._grp,
        )

        # ── libellé de score / placeholder ───────────────────────────────────
        self._score_label = make_label(
            "SCORE  0",
            width // 2, height - 14,
            batch, self._grp,
            font_name=FONT_UI, font_size=SIZE_SMALL,
            color=COLOR_TEXT,
            anchor_x="center", anchor_y="top",
        )

        # ── stats de debug ────────────────────────────────────────────────────
        self._stats: StatsPanel | None = None
        if show_stats:
            self._stats = StatsPanel(
                width - 180, height - 20 - (HUD.HP_BAR_H + 12),
                batch, self._grp,
            )

    # ── mise à jour ───────────────────────────────────────────────────────────

    def update(self, player, hp: int | None = None, score: int = 0):
        """
        Appeler chaque frame.

        player : instance Player (pour les stats)
        hp     : PV actuels (si None, utilise player.hp si disponible)
        score  : score courant
        """
        if not self._visible:
            return

        # PV
        if hp is None:
            hp = getattr(player, "hp", self._health.max_hp)
        self._health.set_hp(hp)

        # score
        self._score_label.text = f"SCORE  {score:06d}"

        # stats debug
        if self._stats:
            self._stats.update(player)

    # ── visibilité ────────────────────────────────────────────────────────────

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False
