# menus.py
import pyglet
from pyglet import shapes
from pyglet.gl import GL_NEAREST

from theme import (
    COLOR_PANEL, COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_BTN_NORMAL,
    FONT_TITLE, FONT_UI, FONT_MONO,
    SIZE_HEADER, SIZE_SMALL,
    make_label, draw_panel, draw_border,
)
from ui import Button


# ── Slider ─────────────────────────────────────────────────────────────────────

class Slider:
    TRACK_H = 6
    THUMB_R = 10

    def __init__(self, x, y, w, label, value, batch, group_bg=None, group_fg=None,
                 on_change=None):
        self.x, self.y, self.w = x, y, w
        self._value = max(0.0, min(1.0, value))
        self.on_change = on_change
        self._dragging = False
        self._visible = True

        track_y = y + self.THUMB_R - self.TRACK_H // 2
        self._track_bg = shapes.Rectangle(
            x, track_y, w, self.TRACK_H,
            color=COLOR_BTN_NORMAL[:3],
            batch=batch, group=group_bg
        )
        self._track_fill = shapes.Rectangle(
            x, track_y, int(w * self._value), self.TRACK_H,
            color=COLOR_ACCENT[:3],
            batch=batch, group=group_fg
        )
        self._thumb = shapes.Circle(
            x + int(w * self._value), y + self.THUMB_R,
            self.THUMB_R, color=COLOR_ACCENT[:3],
            batch=batch, group=group_fg
        )
        self._label = make_label(
            label, x - 12, y + self.THUMB_R,
            batch, group_fg,
            font_name=FONT_UI, font_size=SIZE_SMALL,
            color=COLOR_TEXT,
            anchor_x="right", anchor_y="center"
        )
        self._val_label = make_label(
            f"{int(self._value * 100)}%",
            x + w + 12, y + self.THUMB_R,
            batch, group_fg,
            font_name=FONT_MONO, font_size=SIZE_SMALL,
            color=COLOR_TEXT_DIM,
            anchor_x="left", anchor_y="center"
        )

    @property
    def value(self):
        return self._value

    def set_visible(self, v: bool):
        self._visible = v
        a = 255 if v else 0
        self._track_bg.opacity = a
        self._track_fill.opacity = a
        self._thumb.opacity = a
        self._label.color = (*COLOR_TEXT[:3], a)
        self._val_label.color = (*COLOR_TEXT_DIM[:3], a)

    def _set_value(self, val):
        self._value = max(0.0, min(1.0, val))
        self._track_fill.width = int(self.w * self._value)
        self._thumb.x = self.x + int(self.w * self._value)
        self._val_label.text = f"{int(self._value * 100)}%"
        if self.on_change:
            self.on_change(self._value)

    def _hit(self, mx, my):
        return (
            abs(mx - self._thumb.x) <= self.THUMB_R + 4 and
            abs(my - (self.y + self.THUMB_R)) <= self.THUMB_R + 4
        )

    def on_mouse_press(self, x, y, button, modifiers):
        if self._visible and self._hit(x, y):
            self._dragging = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._dragging:
            self._set_value((x - self.x) / self.w)

    def on_mouse_release(self, x, y, button, modifiers):
        self._dragging = False


# ── Base menu avec background image ────────────────────────────────────────────

class MenuBackgroundMixin:
    def _init_menu_bg(self, width, height, batch, bg_path=None, bg_order=18):
        self._menu_w = width
        self._menu_h = height
        self._bg_path = bg_path
        self._bg_group = pyglet.graphics.Group(order=bg_order)
        self._bg_sprite = None
        self._bg_overlay = shapes.Rectangle(
            0, 0, width, height,
            color=(0, 0, 0),
            batch=batch,
            group=pyglet.graphics.Group(order=bg_order + 1)
        )
        self._bg_overlay.opacity = 0

        if bg_path:
            self.set_background(bg_path, width, height, batch)

    def set_background(self, bg_path, width=None, height=None, batch=None):
        self._bg_path = bg_path
        if width is not None:
            self._menu_w = width
        if height is not None:
            self._menu_h = height

        if self._bg_sprite is not None:
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
                img,
                x=0,
                y=0,
                batch=batch if batch is not None else self._batch,
                group=self._bg_group
            )
            self._fit_bg_to_window()
            self._bg_sprite.visible = False
        except Exception as e:
            print(f"[MENU BG] impossible de charger '{bg_path}' : {e}")
            self._bg_sprite = None

    def _fit_bg_to_window(self):
        if not self._bg_sprite:
            return

        img = self._bg_sprite.image
        sx = self._menu_w / img.width
        sy = self._menu_h / img.height

        scale = max(sx, sy)
        self._bg_sprite.scale = scale

        drawn_w = img.width * scale
        drawn_h = img.height * scale

        self._bg_sprite.x = (self._menu_w - drawn_w) / 2
        self._bg_sprite.y = (self._menu_h - drawn_h) / 2

    def _set_bg_visible(self, visible: bool, overlay_opacity=110):
        if self._bg_sprite:
            self._bg_sprite.visible = visible
            self._bg_sprite.opacity = 255 if visible else 0
        self._bg_overlay.opacity = overlay_opacity if visible else 0

    def on_resize_bg(self, width, height):
        self._menu_w = width
        self._menu_h = height
        self._bg_overlay.width = width
        self._bg_overlay.height = height
        self._fit_bg_to_window()


# ── OptionsMenu ────────────────────────────────────────────────────────────────

class OptionsMenu(MenuBackgroundMixin):
    PANEL_W = 480
    PANEL_H = 360

    def __init__(self, width, height, batch, on_back=None, bg_path=None):
        self._visible = False
        self._batch = batch

        self._init_menu_bg(width, height, batch, bg_path=bg_path, bg_order=18)

        self._grp_bg = pyglet.graphics.Group(order=20)
        self._grp_mid = pyglet.graphics.Group(order=21)
        self._grp_fg = pyglet.graphics.Group(order=22)

        cx = width // 2
        cy = height // 2
        px = cx - self.PANEL_W // 2
        py = cy - self.PANEL_H // 2

        self._panel = draw_panel(px, py, self.PANEL_W, self.PANEL_H, batch, self._grp_bg)
        self._panel.opacity = 0
        self._borders = draw_border(px, py, self.PANEL_W, self.PANEL_H, 2, batch, self._grp_fg)
        self._title = make_label(
            "OPTIONS", cx, py + self.PANEL_H - 30,
            batch, self._grp_fg,
            font_name=FONT_TITLE, font_size=SIZE_HEADER,
            color=COLOR_ACCENT,
            anchor_x="center", anchor_y="center"
        )

        self._sliders = []
        configs = [
            ("Musique", 0.70, "music_volume"),
            ("Effets SFX", 0.90, "sfx_volume"),
            ("Vitesse", 0.60, "player_speed")
        ]
        for i, (lbl, default, attr) in enumerate(configs):
            sy = py + self.PANEL_H - 120 - i * 70
            s = Slider(cx + 40, sy, 180, lbl, default, batch, self._grp_mid, self._grp_fg)
            setattr(self, attr, s)
            self._sliders.append(s)

        self._back_btn = Button(
            cx - 80, py + 20, 160, 44, "← RETOUR",
            batch, self._grp_mid, self._grp_fg,
            on_click=on_back
        )

        self._set_opacity(0)
        self._back_btn.set_visible(False)
        for s in self._sliders:
            s.set_visible(False)

    def _set_opacity(self, a):
        self._panel.opacity = min(a, 210)
        for b in self._borders:
            b.opacity = a
        self._title.color = (*COLOR_ACCENT[:3], a)

    def show(self):
        self._visible = True
        self._set_bg_visible(True, overlay_opacity=95)
        self._set_opacity(255)
        self._back_btn.set_visible(True)
        for s in self._sliders:
            s.set_visible(True)

    def hide(self):
        self._visible = False
        self._set_bg_visible(False)
        self._set_opacity(0)
        self._back_btn.set_visible(False)
        for s in self._sliders:
            s.set_visible(False)

    @property
    def is_visible(self):
        return self._visible

    def on_resize(self, width, height):
        self.on_resize_bg(width, height)

    def on_mouse_motion(self, x, y, dx, dy):
        if self._visible:
            self._back_btn.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._visible:
            self._back_btn.on_mouse_press(x, y, button, modifiers)
            for s in self._sliders:
                s.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._visible:
            for s in self._sliders:
                s.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self._visible:
            self._back_btn.on_mouse_release(x, y, button, modifiers)
            for s in self._sliders:
                s.on_mouse_release(x, y, button, modifiers)


# ── StatsScreen ────────────────────────────────────────────────────────────────

class StatsScreen(MenuBackgroundMixin):
    PANEL_W = 420
    PANEL_H = 300

    def __init__(self, width, height, batch, on_back=None, bg_path=None):
        self._visible = False
        self._batch = batch

        self._init_menu_bg(width, height, batch, bg_path=bg_path, bg_order=18)

        self._grp_bg = pyglet.graphics.Group(order=20)
        self._grp_mid = pyglet.graphics.Group(order=21)
        self._grp_fg = pyglet.graphics.Group(order=22)

        cx = width // 2
        cy = height // 2
        px = cx - self.PANEL_W // 2
        py = cy - self.PANEL_H // 2

        self._panel = draw_panel(px, py, self.PANEL_W, self.PANEL_H, batch, self._grp_bg)
        self._panel.opacity = 0
        self._borders = draw_border(px, py, self.PANEL_W, self.PANEL_H, 2, batch, self._grp_fg)
        self._title = make_label(
            "STATISTIQUES", cx, py + self.PANEL_H - 30,
            batch, self._grp_fg,
            font_name=FONT_TITLE, font_size=SIZE_HEADER,
            color=COLOR_ACCENT,
            anchor_x="center", anchor_y="center"
        )

        stat_keys = ["Temps de jeu", "Sauts", "Morts", "Score max"]
        self._stat_labels = {}
        self._key_labels = []

        for i, key in enumerate(stat_keys):
            row_y = py + self.PANEL_H - 90 - i * 38
            kl = make_label(
                key + "  :", px + 24, row_y,
                batch, self._grp_fg,
                font_name=FONT_UI, font_size=SIZE_SMALL,
                color=COLOR_TEXT_DIM
            )
            vl = make_label(
                "—", px + self.PANEL_W - 24, row_y,
                batch, self._grp_fg,
                font_name=FONT_MONO, font_size=SIZE_SMALL,
                color=COLOR_TEXT,
                anchor_x="right", anchor_y="bottom"
            )
            self._key_labels.append(kl)
            self._stat_labels[key] = vl

        self._back_btn = Button(
            cx - 80, py + 16, 160, 44, "← RETOUR",
            batch, self._grp_mid, self._grp_fg,
            on_click=on_back
        )

        self._set_opacity(0)
        self._back_btn.set_visible(False)

    def _set_opacity(self, a):
        self._panel.opacity = min(a, 210)
        for b in self._borders:
            b.opacity = a
        self._title.color = (*COLOR_ACCENT[:3], a)
        for lbl in self._key_labels:
            lbl.color = (*COLOR_TEXT_DIM[:3], a)
        for lbl in self._stat_labels.values():
            lbl.color = (*COLOR_TEXT[:3], a)

    def update_stats(self, time_sec=0, jumps=0, deaths=0, best_score=0):
        m, s = divmod(int(time_sec), 60)
        self._stat_labels["Temps de jeu"].text = f"{m:02d}:{s:02d}"
        self._stat_labels["Sauts"].text = str(jumps)
        self._stat_labels["Morts"].text = str(deaths)
        self._stat_labels["Score max"].text = f"{best_score:06d}"

    def show(self):
        self._visible = True
        self._set_bg_visible(True, overlay_opacity=95)
        self._set_opacity(255)
        self._back_btn.set_visible(True)

    def hide(self):
        self._visible = False
        self._set_bg_visible(False)
        self._set_opacity(0)
        self._back_btn.set_visible(False)

    @property
    def is_visible(self):
        return self._visible

    def on_resize(self, width, height):
        self.on_resize_bg(width, height)

    def on_mouse_motion(self, x, y, dx, dy):
        if self._visible:
            self._back_btn.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._visible:
            self._back_btn.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self._visible:
            self._back_btn.on_mouse_release(x, y, button, modifiers)