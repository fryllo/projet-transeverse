# npc.py
import pyglet
from pyglet import shapes

TRIGGER_DIST = 100


class NPC:
    def __init__(self, x, y, sprite_path, dialogue, batch, sound=True):
        self.x            = float(x)
        self.y            = float(y)
        self.width        = 48
        self.height       = 64
        self.solid        = False
        self.dialogue     = dialogue
        self._batch       = batch
        self._active      = True
        self._show_bubble = False
        self._world_x     = x
        self._world_y     = y
        self._bw          = 220
        self._bh          = 60

        # Son selon le type de PNJ
        self._sound = None
        if sound:
            son_path = None
            if "champignon" in sprite_path:
                son_path = "musique/EM.ogg"
            elif "poisson" in sprite_path:
                son_path = "musique/PG.opus"
            if son_path:
                try:
                    self._sound = pyglet.media.load(son_path, streaming=False)
                except Exception as e:
                    print(f"[NPC] son : {e}")

        grp_sprite = pyglet.graphics.Group(order=6)
        grp_bubble = pyglet.graphics.Group(order=7)

        self._sprite = None
        try:
            img = pyglet.image.load(sprite_path)
            self._sprite = pyglet.sprite.Sprite(img, x=int(x), y=int(y),
                                                batch=batch, group=grp_sprite)
            self._sprite.scale_x = self.width  / img.width
            self._sprite.scale_y = self.height / img.height
        except Exception as e:
            print(f"[NPC] sprite : {e}")

        self._hint = pyglet.text.Label(
            "[E]", font_name="Segoe UI", font_size=10,
            x=int(x), y=int(y) + self.height + 10,
            color=(255, 255, 180, 0),
            anchor_x="center", anchor_y="bottom",
            batch=batch, group=grp_bubble,
        )

        bw, bh = self._bw, self._bh
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

        self._bubble_text = pyglet.text.Label(
            dialogue,
            font_name="Segoe UI", font_size=10,
            x=int(x), y=int(y) + self.height + 60,
            color=(30, 30, 30, 0),
            anchor_x="center", anchor_y="center",
            batch=batch, group=grp_bubble,
            width=210, multiline=True, align="center",
        )

    def _dist(self, player):
        return abs((player.x + player.width / 2) - self._world_x)

    def toggle_bubble(self, player):
        if self._dist(player) < TRIGGER_DIST:
            self._show_bubble = not self._show_bubble
            self._refresh_bubble()
            if self._show_bubble and self._sound:
                p = self._sound.play()
                p.volume = 100.0

    def _refresh_bubble(self):
        a  = 220 if self._show_bubble else 0
        at = 255 if self._show_bubble else 0
        self._bubble_bg.opacity     = a
        self._bubble_border.opacity = a
        self._bubble_text.color     = (30, 30, 30, at)

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

    def destroy(self):
        self._active = False
        for s in (self._bubble_bg, self._bubble_border,
                  self._hint, self._bubble_text):
            try: s.batch = None
            except: pass
        if self._sprite:
            try: self._sprite.delete()
            except: pass