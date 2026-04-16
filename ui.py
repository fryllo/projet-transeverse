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
    FONT_TITLE, FONT_UI, SIZE_TITLE, SIZE_BODY,SIZE_HEADER,
    make_label, draw_panel, draw_border,

)
from pyglet.gl import GL_NEAREST
# ── Bouton générique ───────────────────────────────────────────────────────────

class VictoryScreen:
    PANEL_W = 480
    PANEL_H = 320

    def __init__(self, width, height, batch, on_menu=None):
        self._visible = False
        self._grp_bg  = pyglet.graphics.Group(order=40)
        self._grp_fg  = pyglet.graphics.Group(order=41)

        cx, cy = width // 2, height // 2
        px, py = cx - self.PANEL_W // 2, cy - self.PANEL_H // 2

        self._panel = draw_panel(px, py, self.PANEL_W, self.PANEL_H, batch, self._grp_bg)
        self._panel.opacity = 0

        self._title = make_label(
            "BIEN JOUÉ !",
            cx, py + self.PANEL_H - 60,
            batch, self._grp_fg,
            font_name=FONT_TITLE, font_size=SIZE_TITLE,
            color=(255, 220, 50, 0),
            anchor_x="center", anchor_y="center",
        )
        self._subtitle = make_label(
            "Tu as sauvé les 3 zones !\nGreta est fière de toi 🌱",
            cx, cy + 20,
            batch, self._grp_fg,
            font_size=SIZE_BODY,
            color=(200, 255, 180, 0),
            anchor_x="center", anchor_y="center",
        )
        self._btn = Button(cx - 100, py + 30, 200, 50, "MENU PRINCIPAL",
                           batch, self._grp_bg, self._grp_fg, on_click=on_menu)
        self.hide()

    def show(self):
        self._visible = True
        self._panel.opacity = 230
        self._title.color   = (255, 220, 50, 255)
        self._subtitle.color = (200, 255, 180, 255)
        self._btn.set_visible(True)

    def hide(self):
        self._visible = False
        self._panel.opacity  = 0
        self._title.color    = (255, 220, 50, 0)
        self._subtitle.color = (200, 255, 180, 0)
        self._btn.set_visible(False)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._visible:
            self._btn.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self._visible:
            self._btn.on_mouse_release(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self._visible:
            self._btn.on_mouse_motion(x, y, dx, dy)

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
    BTN_W = 260
    BTN_H = 52
    BTN_GAP = 18

    def __init__(self, width, height, batch,
                 on_play=None, on_options=None, on_quit=None,
                 bg_path=None):
        self.width = width
        self.height = height
        self._visible = False
        self._batch = batch
        self._bg_path = bg_path

        # Ordres de rendu
        self._grp_bg_img = pyglet.graphics.Group(order=9)
        self._grp_bg = pyglet.graphics.Group(order=10)
        self._grp_mid = pyglet.graphics.Group(order=11)
        self._grp_fg = pyglet.graphics.Group(order=12)

        cx = width // 2

        # Image de fond
        self._bg_sprite = None
        if bg_path:
            try:
                img = pyglet.image.load(bg_path)
                tex = img.get_texture()
                tex.min_filter = GL_NEAREST
                tex.mag_filter = GL_NEAREST

                self._bg_sprite = pyglet.sprite.Sprite(
                    img, x=0, y=0,
                    batch=batch, group=self._grp_bg_img
                )
                self._fit_background()
                self._bg_sprite.visible = False
            except Exception as e:
                print(f"[MainMenu] fond non chargé : {e}")
                self._bg_sprite = None

        # Overlay sombre pour lisibilité
        self._bg = shapes.Rectangle(
            0, 0, width, height,
            color=COLOR_BG[:3],
            batch=batch, group=self._grp_bg
        )
        self._bg.opacity = 0

        # Titre
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

        # Boutons
        labels = ["▶ PLAY", "⚙ OPTIONS", "✕ QUIT"]
        callbacks = [on_play, on_options, on_quit]
        total_h = len(labels) * (self.BTN_H + self.BTN_GAP) - self.BTN_GAP
        start_y = (height - total_h) // 2

        self._buttons = []
        for i, (txt, cb) in enumerate(zip(labels, callbacks)):
            by = start_y + (len(labels) - 1 - i) * (self.BTN_H + self.BTN_GAP)
            bx = cx - self.BTN_W // 2
            btn = Button(
                bx, by, self.BTN_W, self.BTN_H, txt,
                batch, self._grp_mid, self._grp_fg,
                on_click=cb
            )
            btn.set_visible(False)
            self._buttons.append(btn)

        # Crédits
        self._credits = make_label(
            "Arrows / WASD · Space to jump",
            cx, 22, batch, group=self._grp_fg,
            font_size=12, color=COLOR_TEXT_DIM,
            anchor_x="center", anchor_y="bottom",
        )
        self._credits.opacity = 0

        # Caché par défaut
        self._title.opacity = 0
        self._subtitle.opacity = 0

    def _fit_background(self):
        if not self._bg_sprite:
            return

        img = self._bg_sprite.image
        sx = self.width / img.width
        sy = self.height / img.height
        scale = max(sx, sy)

        self._bg_sprite.scale = scale

        drawn_w = img.width * scale
        drawn_h = img.height * scale
        self._bg_sprite.x = (self.width - drawn_w) / 2
        self._bg_sprite.y = (self.height - drawn_h) / 2

    def set_background(self, bg_path):
        self._bg_path = bg_path

        if self._bg_sprite:
            try:
                self._bg_sprite.delete()
            except:
                pass
            self._bg_sprite = None

        if not bg_path:
            return

        try:
            img = pyglet.image.load(bg_path)
            tex = img.get_texture()
            tex.min_filter = GL_NEAREST
            tex.mag_filter = GL_NEAREST

            self._bg_sprite = pyglet.sprite.Sprite(
                img, x=0, y=0,
                batch=self._batch, group=self._grp_bg_img
            )
            self._fit_background()
            self._bg_sprite.visible = self._visible
        except Exception as e:
            print(f"[MainMenu] fond non chargé : {e}")

    def on_resize(self, width, height):
        self.width = width
        self.height = height

        self._bg.width = width
        self._bg.height = height
        self._fit_background()

    def show(self):
        self._visible = True
        if self._bg_sprite:
            self._bg_sprite.visible = True
            self._bg_sprite.opacity = 255
        self._bg.opacity = 140
        self._credits.opacity = 180
        self._title.opacity = 255
        self._subtitle.opacity = 255
        for btn in self._buttons:
            btn.set_visible(True)

    def hide(self):
        self._visible = False
        if self._bg_sprite:
            self._bg_sprite.visible = False
        self._bg.opacity = 0
        self._credits.opacity = 0
        self._title.opacity = 0
        self._subtitle.opacity = 0
        for btn in self._buttons:
            btn.set_visible(False)

    @property
    def is_visible(self):
        return self._visible

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


# Dans ui.py (ou à ajouter à la fin du fichier)
class LevelSelect:
    PANEL_W = 400
    PANEL_H = 350

    def __init__(self, width, height, batch, on_level_selected):
        self._visible = False
        self._on_level_selected = on_level_selected

        # Groupes pour la superposition
        self._grp_bg = pyglet.graphics.Group(order=30)
        self._grp_fg = pyglet.graphics.Group(order=31)

        cx, cy = width // 2, height // 2
        px, py = cx - self.PANEL_W // 2, cy - self.PANEL_H // 2

        # Fond du menu
        self._panel = draw_panel(px, py, self.PANEL_W, self.PANEL_H, batch, self._grp_bg)
        self._title = make_label("CHOISIR NIVEAU", cx, py + self.PANEL_H - 40,
                                 batch, self._grp_fg, font_name=FONT_TITLE,
                                 font_size=SIZE_HEADER, color=COLOR_ACCENT, anchor_x="center")

        # Création des 3 boutons de niveau
        self._buttons = []
        for i in range(3):
            btn_y = py + self.PANEL_H - 120 - (i * 70)
            # On utilise une "closure" (lambda) pour passer l'index du niveau au clic
            b = Button(cx - 100, btn_y, 200, 50, f"NIVEAU {i + 1}",
                       batch, self._grp_bg, self._grp_fg,
                       on_click=lambda idx=i: self._on_level_selected(idx))
            self._buttons.append(b)

        self.hide()

    def set_visible(self, v):
        self._visible = v
        self._panel.opacity = 255 if v else 0
        self._title.color = (*COLOR_ACCENT[:3], 255 if v else 0)
        for b in self._buttons:
            b.set_visible(v)

    def show(self):
        self.set_visible(True)

    def hide(self):
        self.set_visible(False)

    def on_mouse_motion(self, x, y, dx, dy):
        if self._visible:
            for b in self._buttons: b.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._visible:
            for b in self._buttons: b.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self._visible:
            for b in self._buttons: b.on_mouse_release(x, y, button, modifiers)


class GameOverMenu:
    PANEL_W = 400
    PANEL_H = 300

    def __init__(self, width, height, batch, on_retry, on_menu):
        self._visible = False
        self._grp_bg = pyglet.graphics.Group(order=40)
        self._grp_fg = pyglet.graphics.Group(order=41)

        cx, cy = width // 2, height // 2
        px, py = cx - self.PANEL_W // 2, cy - self.PANEL_H // 2

        self._panel = draw_panel(px, py, self.PANEL_W, self.PANEL_H, batch, self._grp_bg)
        self._title = make_label("GAME OVER", cx, py + self.PANEL_H - 50,
                                 batch, self._grp_fg, font_name=FONT_TITLE,
                                 font_size=SIZE_HEADER, color=(255, 50, 50, 255), anchor_x="center")

        # Bouton Rejouer
        self._btn_retry = Button(cx - 100, py + 130, 200, 50, "REJOUER",
                                 batch, self._grp_bg, self._grp_fg, on_click=on_retry)

        # Bouton Menu Principal
        self._btn_menu = Button(cx - 100, py + 60, 200, 50, "MENU",
                                batch, self._grp_bg, self._grp_fg, on_click=on_menu)
        self.hide()

    def set_visible(self, v):
        self._visible = v
        self._panel.opacity = 230 if v else 0  # Un peu transparent pour voir le lieu du crime
        self._title.color = (255, 50, 50, 255 if v else 0)
        self._btn_retry.set_visible(v)
        self._btn_menu.set_visible(v)

    def show(self):
        self.set_visible(True)

    def hide(self):
        self.set_visible(False)
        self._panel.opacity = 0
        self._title.color = (255, 50, 50, 0)
        self._btn_retry.set_visible(False)
        self._btn_menu.set_visible(False)

    def on_mouse_motion(self, x, y, dx, dy):
        if self._visible:
            self._btn_retry.on_mouse_motion(x, y, dx, dy)
            self._btn_menu.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._visible:
            self._btn_retry.on_mouse_press(x, y, button, modifiers)
            self._btn_menu.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self._visible:
            self._btn_retry.on_mouse_release(x, y, button, modifiers)
            self._btn_menu.on_mouse_release(x, y, button, modifiers)
