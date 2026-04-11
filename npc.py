# npc.py
# PNJ avec sprite, bulle de dialogue (touche E pour interagir)
# Aucune collision — purement décoratif/narratif

import pyglet
from pyglet import shapes

TRIGGER_DIST = 100   # distance pour afficher l'indication "E"


class NPC:
    """
    PNJ statique avec sprite et bulle de dialogue.
    La bulle s'affiche quand le joueur appuie sur E à proximité.
    Aucune collision avec le monde physique.
    """

    def __init__(self, x, y, sprite_path, dialogue, batch):
        self.x         = float(x)
        self.y         = float(y)
        self.width     = 48
        self.height    = 64
        self.solid     = False
        self.dialogue  = dialogue
        self._batch    = batch
        self._active   = True
        self._show_bubble = False

        grp_sprite = pyglet.graphics.Group(order=6)
        grp_bubble = pyglet.graphics.Group(order=7)

        # Sprite
        try:
            img = pyglet.image.load(sprite_path)
            self._sprite = pyglet.sprite.Sprite(img, x=int(x), y=int(y),
                                                 batch=batch, group=grp_sprite)
            self._sprite.scale_x = self.width  / img.width
            self._sprite.scale_y = self.height / img.height
        except Exception as e:
            print(f"[NPC] sprite non chargé : {e}")
            self._sprite = None

        # Indicateur [E]
        self._hint = pyglet.text.Label(
            "[E]", font_name="Segoe UI", font_size=10,
            x=int(x), y=int(y) + self.height + 10,
            color=(255, 255, 180, 0),
            anchor_x="center", anchor_y="bottom",
            batch=batch, group=grp_bubble,
        )

        # Bulle
        bw, bh = 220, 60
        self._bw = bw
        self._bh = bh
        self._bubble_border = shapes.Rectangle(
            int(x) - bw//2 - 2, int(y) + self.height + 28,
            bw + 4, bh + 4,
            color=(80, 80, 80), batch=batch, group=grp_bubble
        )
        self._bubble_border.opacity = 0
        self._bubble_bg = shapes.Rectangle(
            int(x) - bw//2, int(y) + self.height + 30,
            bw, bh,
            color=(255, 255, 240), batch=batch, group=grp_bubble
        )
        self._bubble_bg.opacity = 0
        self._bubble_tip_outer = shapes.Triangle(
            int(x) - 8, int(y) + self.height + 30,
            int(x) + 8, int(y) + self.height + 30,
            int(x),     int(y) + self.height + 18,
            color=(80, 80, 80), batch=batch, group=grp_bubble
        )
        self._bubble_tip_outer.opacity = 0
        self._bubble_tip = shapes.Triangle(
            int(x) - 6, int(y) + self.height + 32,
            int(x) + 6, int(y) + self.height + 32,
            int(x),     int(y) + self.height + 22,
            color=(255, 255, 240), batch=batch, group=grp_bubble
        )
        self._bubble_tip.opacity = 0
        self._bubble_text = pyglet.text.Label(
            dialogue,
            font_name="Segoe UI", font_size=10,
            x=int(x), y=int(y) + self.height + 60,
            color=(30, 30, 30, 0),
            anchor_x="center", anchor_y="center",
            batch=batch, group=grp_bubble,
            width=210, multiline=True, align="center",
        )

        self._world_x = x
        self._world_y = y

    def _dist(self, player):
        return abs((player.x + player.width/2) - self._world_x)

    def toggle_bubble(self, player):
        """Appelé quand le joueur appuie sur E."""
        if self._dist(player) < TRIGGER_DIST:
            self._show_bubble = not self._show_bubble
            self._refresh_bubble()

    def _refresh_bubble(self):
        a = 220 if self._show_bubble else 0
        at = 255 if self._show_bubble else 0
        self._bubble_bg.opacity         = a
        self._bubble_border.opacity     = a
        self._bubble_tip.opacity        = a
        self._bubble_tip_outer.opacity  = a
        self._bubble_text.color         = (30, 30, 30, at)

    def update(self, player, camera_offset):
        if not self._active:
            return
        sx = int(self._world_x - camera_offset)
        sy = int(self._world_y)
        bw = self._bw

        if self._sprite:
            self._sprite.x = sx
            self._sprite.y = sy

        near = self._dist(player) < TRIGGER_DIST and not self._show_bubble
        self._hint.color = (255, 255, 180, 200 if near else 0)
        self._hint.x = sx
        self._hint.y = sy + self.height + 8

        self._bubble_border.x = sx - bw//2 - 2
        self._bubble_border.y = sy + self.height + 28
        self._bubble_bg.x     = sx - bw//2
        self._bubble_bg.y     = sy + self.height + 30
        self._bubble_text.x   = sx
        self._bubble_text.y   = sy + self.height + 60
        # Repositionner les triangles via les vertices
        h = self.height
        self._bubble_tip_outer.vertices = [
            sx - 8, sy + h + 30,
            sx + 8, sy + h + 30,
            sx,     sy + h + 18,
        ]
        self._bubble_tip.vertices = [
            sx - 6, sy + h + 32,
            sx + 6, sy + h + 32,
            sx,     sy + h + 22,
        ]

    def destroy(self):
        self._active = False
        for s in (self._bubble_bg, self._bubble_border,
                  self._bubble_tip, self._bubble_tip_outer,
                  self._hint, self._bubble_text):
            try: s.batch = None
            except: pass
        if self._sprite:
            try: self._sprite.delete()
            except: pass