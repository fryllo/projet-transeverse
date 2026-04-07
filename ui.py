# ui.py
# Menu principal : Play / Options / Quit
#
# Usage dans Game.__init__ :
#   from ui import MainMenu
#   self.main_menu = MainMenu(WIDTH, HEIGHT, self.batch,
#                             on_play=self.start_game,
#                             on_options=self.open_options,
#                             on_quit=pyglet.app.exit)
#   self.main_menu.show()

import pyglet
from pyglet import shapes
from theme import (
    COLOR_BG, COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_BTN_NORMAL, COLOR_BTN_HOVER, COLOR_BTN_PRESS, COLOR_BTN_BORDER,
    FONT_TITLE, FONT_UI, SIZE_TITLE, SIZE_BODY,
    make_label, draw_border,
)

# ── Bouton générique ───────────────────────────────────────────────────────────

class Button:
    """Bouton rectangulaire cliquable avec état hover / pressed."""

    def __init__(self, x, y, w, h, text, batch, group_bg=None, group_fg=None,
                 on_click=None):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.on_click = on_click
        self._hovered = False
        self._pressed = False
        self.visible = True

        self._bg = shapes.Rectangle(x, y, w, h,
                                    color=COLOR_BTN_NORMAL[:3],
                                    batch=batch, group=group_bg)
        self._borders = draw_border(x, y, w, h, 2, batch, group=group_fg)
        self._label = make_label(text, x + w // 2, y + h // 2,
                                 batch, group=group_fg,
                                 font_name=FONT_UI, font_size=SIZE_BODY,
                                 color=COLOR_TEXT,
                                 anchor_x="center", anchor_y="center")

    # ── état ──────────────────────────────────────────────────────────────────

    def _refresh_color(self):
        if self._pressed:
            c = COLOR_BTN_PRESS[:3]
        elif self._hovered:
            c = COLOR_BTN_HOVER[:3]
        else:
            c = COLOR_BTN_NORMAL[:3]
        self._bg.color = c

    def set_visible(self, v: bool):
        self.visible = v
        alpha = 255 if v else 0
        self._bg.opacity = alpha
        for b in self._borders:
            b.opacity = alpha
        self._label.color = (*COLOR_TEXT[:3], alpha)

    # ── hit-test ──────────────────────────────────────────────────────────────

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    # ── handlers (à brancher sur la fenêtre) ──────────────────────────────────

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.visible:
            return
        self._hovered = self.contains(x, y)
        self._refresh_color()

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.visible:
            return
        if self.contains(x, y):
            self._pressed = True
            self._refresh_color()

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.visible:
            return
        if self._pressed and self.contains(x, y) and self.on_click:
            self.on_click()
        self._pressed = False
        self._refresh_color()


# ── Menu principal ─────────────────────────────────────────────────────────────

class MainMenu:
    """
    Superpose un menu principal sur la fenêtre de jeu.

    Paramètres
    ----------
    width, height   : dimensions de la fenêtre
    batch           : pyglet.graphics.Batch partagé
    on_play         : callback bouton Play
    on_options      : callback bouton Options
    on_quit         : callback bouton Quit
    """

    BTN_W = 260
    BTN_H = 52
    BTN_GAP = 18

    def __init__(self, width, height, batch,
                 on_play=None, on_options=None, on_quit=None):
        self.width = width
        self.height = height
        self._visible = False

        # groupes de rendu (menu au-dessus du jeu)
        self._grp_bg  = pyglet.graphics.Group(order=10)
        self._grp_mid = pyglet.graphics.Group(order=11)
        self._grp_fg  = pyglet.graphics.Group(order=12)

        cx = width // 2

        # ── fond opaque ───────────────────────────────────────────────────────
        self._bg = shapes.Rectangle(0, 0, width, height,
                                    color=COLOR_BG[:3],
                                    batch=batch, group=self._grp_bg)
        self._bg.opacity = 0

        # ── titre ─────────────────────────────────────────────────────────────
        self._title = make_label(
            "Cop Adventure",
            cx, height - 120,
            batch, group=self._grp_fg,
            font_name=FONT_TITLE, font_size=SIZE_TITLE,
            color=COLOR_ACCENT,
            anchor_x="center", anchor_y="center",
        )
        self._subtitle = make_label(
            "— amuse toi bien —",
            cx, height - 165,
            batch, group=self._grp_fg,
            font_size=13, color=COLOR_TEXT_DIM,
            anchor_x="center", anchor_y="center",
        )

        # ── boutons ───────────────────────────────────────────────────────────
        labels   = ["▶  PLAY",  "⚙  OPTIONS", "✕  QUIT"]
        callbacks = [on_play, on_options, on_quit]
        total_h  = len(labels) * (self.BTN_H + self.BTN_GAP) - self.BTN_GAP
        start_y  = (height - total_h) // 2

        self._buttons = []
        for i, (txt, cb) in enumerate(zip(labels, callbacks)):
            by = start_y + (len(labels) - 1 - i) * (self.BTN_H + self.BTN_GAP)
            bx = cx - self.BTN_W // 2
            btn = Button(bx, by, self.BTN_W, self.BTN_H, txt,
                         batch, self._grp_mid, self._grp_fg,
                         on_click=cb)
            btn.set_visible(False)
            self._buttons.append(btn)

        # ── crédits ───────────────────────────────────────────────────────────
        self._credits = make_label(
            "Arrows / WASD · Space to jump",
            cx, 22, batch, group=self._grp_fg,
            font_size=12, color=COLOR_TEXT_DIM,
            anchor_x="center", anchor_y="bottom",
        )
        self._credits.opacity = 0

    # ── visibilité ────────────────────────────────────────────────────────────

    # Dans ui.py -> classe MainMenu

    def show(self):
        self._visible = True
        self._bg.opacity = 230
        self._credits.opacity = 180
        self._title.opacity = 255
        self._subtitle.opacity = 255
        for btn in self._buttons:
            btn.set_visible(True)

    def hide(self):
        self._visible = False
        self._bg.opacity = 0
        self._credits.opacity = 0
        self._title.opacity = 0
        self._subtitle.opacity = 0
        for btn in self._buttons:
            btn.set_visible(False)

    @property
    def is_visible(self):
        return self._visible

    # ── handlers souris (à brancher sur la fenêtre) ──────────────────────────

    def on_mouse_motion(self, x, y, dx, dy):
        if not self._visible:
            return
        for btn in self._buttons:
            btn.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self._visible:
            return
        for btn in self._buttons:
            btn.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if not self._visible:
            return
        for btn in self._buttons:
            btn.on_mouse_release(x, y, button, modifiers)