# background.py
from pathlib import Path
import pyglet
from pyglet import shapes
from pyglet.gl import GL_NEAREST

BASE_DIR   = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets" / "backgrounds"
WORLD_W    = 5200


class ColorFillLayer:
    """Rectangle plein qui couvre toujours toute la fenêtre."""
    def __init__(self, screen_w, screen_h, color, batch):
        self._rect = shapes.Rectangle(
            0, 0, screen_w, screen_h,
            color=color[:3],
            batch=batch,
            group=pyglet.graphics.Group(order=0),
        )

    def update(self, camera_x): pass

    def on_resize(self, width, height):
        self._rect.width  = width
        self._rect.height = height

    def set_visible(self, v): self._rect.visible = v
    def clear(self): self._rect.delete()


class StaticImageLayer:
    """
    Image scalée pour couvrir exactement screen_w x screen_h.
    Reste fixe — aucune jointure possible.
    """
    def __init__(self, image_path, screen_w, screen_h, batch):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.batch    = batch

        full_path  = ASSETS_DIR / image_path
        self.image = pyglet.image.load(str(full_path))
        texture    = self.image.get_texture()
        texture.min_filter = GL_NEAREST
        texture.mag_filter = GL_NEAREST

        self.sprite = pyglet.sprite.Sprite(
            self.image, x=0, y=0,
            batch=batch,
            group=pyglet.graphics.Group(order=1),
        )
        self._rescale()

    def _rescale(self):
        self.sprite.scale_x = self.screen_w / self.image.width
        self.sprite.scale_y = self.screen_h / self.image.height

    def update(self, camera_x): pass

    def on_resize(self, width, height):
        self.screen_w = width
        self.screen_h = height
        self._rescale()

    def set_visible(self, v): self.sprite.visible = v
    def clear(self): self.sprite.delete()


class Background:
    def __init__(self, width, height, batch, layers=None, base_color=(0,0,0)):
        self.width      = width
        self.height     = height
        self.batch      = batch
        self.layers     = layers or []
        self.base_color = base_color

    def add_layer(self, layer): self.layers.append(layer)

    def update(self, camera_x):
        for layer in self.layers:
            layer.update(camera_x)

    def on_resize(self, width, height):
        self.width  = width
        self.height = height
        for layer in self.layers:
            if hasattr(layer, "on_resize"):
                layer.on_resize(width, height)

    def set_visible(self, v):
        for layer in self.layers:
            layer.set_visible(v)

    def clear(self):
        for layer in self.layers:
            layer.clear()
        self.layers.clear()


class BackgroundBuilder:

    @staticmethod
    def _static_background(width, height, batch, image_path, base_color):
        bg = Background(width, height, batch, base_color=base_color)
        bg.add_layer(ColorFillLayer(width, height, base_color, batch))
        bg.add_layer(StaticImageLayer(image_path, width, height, batch))
        return bg

    @staticmethod
    def create_ground(width, height, batch):
        return BackgroundBuilder._static_background(
            width, height, batch,
            image_path="ground.jpg",
            base_color=(118, 205, 255),
        )

    @staticmethod
    def create_water(width, height, batch):
        return BackgroundBuilder._static_background(
            width, height, batch,
            image_path="water.jpg",
            base_color=(34, 120, 200),
        )

    @staticmethod
    def create_sky(width, height, batch):
        return BackgroundBuilder._static_background(
            width, height, batch,
            image_path="sky.jpg",
            base_color=(142, 214, 255),
        )