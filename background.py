# background.py
import math
from pathlib import Path
import pyglet
from pyglet.gl import GL_NEAREST

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets" / "backgrounds"
WORLD_W = 5200


class SingleImageBackgroundLayer:
    def __init__(self, image_path, screen_w, screen_h, batch, parallax=0.0, y=0):
        self.image_path = image_path
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.batch = batch
        self.parallax = parallax
        self.base_y = y

        full_path = ASSETS_DIR / image_path
        self.image = pyglet.image.load(str(full_path))

        texture = self.image.get_texture()
        texture.min_filter = GL_NEAREST
        texture.mag_filter = GL_NEAREST

        self.sprite = pyglet.sprite.Sprite(self.image, x=0, y=y, batch=batch)
        self._rescale()

    def _rescale(self):
        self.sprite.scale_x = self.screen_w / self.image.width
        self.sprite.scale_y = self.screen_h / self.image.height

    def update(self, camera_x):
        self.sprite.x = round(-camera_x * self.parallax)
        self.sprite.y = self.base_y

    def on_resize(self, width, height):
        self.screen_w = width
        self.screen_h = height
        self._rescale()

    def set_visible(self, visible: bool):
        self.sprite.visible = visible

    def clear(self):
        self.sprite.delete()

class RepeatingImageLayer:
    def __init__(self, image_path, world_w, screen_w, screen_h, batch, parallax=0.0, y=0):
        self.image_path = image_path
        self.world_w = world_w
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.batch = batch
        self.parallax = parallax
        self.base_y = y
        self.sprites = []

        full_path = ASSETS_DIR / image_path
        self.image = pyglet.image.load(str(full_path))

        texture = self.image.get_texture()
        texture.min_filter = GL_NEAREST
        texture.mag_filter = GL_NEAREST

        self.scale = screen_h / self.image.height
        self.tile_w = int(self.image.width * self.scale)

        self._build_sprites()

    def _build_sprites(self):
        self.clear()
        count = math.ceil(self.screen_w / self.tile_w) + 3

        for i in range(count):
            s = pyglet.sprite.Sprite(
                self.image,
                x=i * self.tile_w,
                y=self.base_y,
                batch=self.batch
            )
            s.scale = self.scale
            self.sprites.append(s)

    def update(self, camera_x):
        offset = (-camera_x * self.parallax) % self.tile_w
        start_x = -offset - self.tile_w

        for i, sprite in enumerate(self.sprites):
            sprite.x = round(start_x + i * self.tile_w)
            sprite.y = self.base_y

    def on_resize(self, width, height):
        self.screen_w = width
        self.screen_h = height
        self.scale = height / self.image.height
        self.tile_w = int(self.image.width * self.scale)
        self._build_sprites()

    def set_visible(self, visible: bool):
        for sprite in self.sprites:
            sprite.visible = visible

    def clear(self):
        for sprite in self.sprites:
            try:
                sprite.delete()
            except Exception:
                pass
        self.sprites.clear()


class Background:
    def __init__(self, width, height, batch, layers=None, base_color=(0, 0, 0)):
        self.width = width
        self.height = height
        self.batch = batch
        self.layers = layers or []
        self.base_color = base_color

    def add_layer(self, layer):
        self.layers.append(layer)

    def update(self, camera_x):
        for layer in self.layers:
            layer.update(camera_x)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        for layer in self.layers:
            if hasattr(layer, "on_resize"):
                layer.on_resize(width, height)

    def set_visible(self, visible: bool):
        for layer in self.layers:
            layer.set_visible(visible)

    def clear(self):
        for layer in self.layers:
            layer.clear()
        self.layers.clear()


class BackgroundBuilder:
    @staticmethod
    def _single_image_background(width, height, batch, image_path, parallax, base_color):
        bg = Background(width, height, batch, base_color=base_color)
        bg.add_layer(
            SingleImageBackgroundLayer(
                image_path=image_path,
                screen_w=width,
                screen_h=height,
                batch=batch,
                parallax=parallax,
                y=0
            )
        )
        return bg

    @staticmethod
    def create_ground(width, height, batch):
        return BackgroundBuilder._single_image_background(
            width=width,
            height=height,
            batch=batch,
            image_path="ground.jpg",
            parallax=0.10,
            base_color=(118, 205, 255)
        )

    @staticmethod
    def create_water(width, height, batch):
        return BackgroundBuilder._single_image_background(
            width=width,
            height=height,
            batch=batch,
            image_path="water.jpg",
            parallax=0.14,
            base_color=(34, 120, 200)
        )

    @staticmethod
    def create_sky(width, height, batch):
        return BackgroundBuilder._single_image_background(
            width=width,
            height=height,
            batch=batch,
            image_path="sky.jpg",
            parallax=0.08,
            base_color=(142, 214, 255)
        )

