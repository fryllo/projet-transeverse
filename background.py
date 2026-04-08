# backgrounds.py
from pyglet import shapes

WORLD_W = 2600
PX = 4


class ParallaxLayer:
    def __init__(self, factor: float):
        self.factor = factor
        self.items = []

    def add(self, shape, base_x, base_y):
        self.items.append((shape, base_x, base_y))

    def clear(self):
        for shape, _, _ in self.items:
            shape.batch = None
        self.items.clear()


class Background:
    def __init__(self, width, height, batch):
        self.width = width
        self.height = height
        self.layers = []

    def add_layer(self, factor: float):
        layer = ParallaxLayer(factor)
        self.layers.append(layer)
        return layer

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        if hasattr(self, 'layers') and self.layers and self.layers[0].items:
            bg_rect = self.layers[0].items[0][0]
            bg_rect.width = width
            bg_rect.height = height

    def update(self, camera_x):
        for layer in self.layers:
            for shape, base_x, base_y in layer.items:
                shape.x = base_x - camera_x * layer.factor
                if hasattr(shape, "y"):
                    shape.y = base_y

    def set_visible(self, visible: bool):
        alpha = 255 if visible else 0
        for layer in self.layers:
            for shape, _, _ in layer.items:
                if hasattr(shape, "opacity"):
                    shape.opacity = alpha

    def clear(self):
        for layer in self.layers:
            layer.clear()
        self.layers.clear()


class BackgroundBuilder:
    # ─────────────────────────────────────────────────────────────
    # Helpers de base
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _rect(layer, x, y, w, h, color, batch, opacity=255):
        r = shapes.Rectangle(x, y, w, h, color=color, batch=batch)
        r.opacity = opacity
        layer.add(r, x, y)
        return r

    @staticmethod
    def _pixel(layer, x, y, color, batch, size=PX, opacity=255):
        r = shapes.Rectangle(x, y, size, size, color=color, batch=batch)
        r.opacity = opacity
        layer.add(r, x, y)
        return r

    @staticmethod
    def _pixel_row(layer, x, y, count, color, batch, size=PX, opacity=255):
        for i in range(count):
            BackgroundBuilder._pixel(layer, x + i * size, y, color, batch, size=size, opacity=opacity)

    @staticmethod
    def _pixel_block(layer, x, y, w, h, color, batch, size=PX, opacity=255):
        for iy in range(h):
            for ix in range(w):
                BackgroundBuilder._pixel(layer, x + ix * size, y + iy * size, color, batch, size=size, opacity=opacity)

    @staticmethod
    def _pattern_dots(layer, width, height, batch):
        for x in range(0, width, 18):
            for y in range(height - 220, height, 14):
                d = shapes.Rectangle(x, y, 2, 2, color=(175, 228, 250), batch=batch)
                d.opacity = 40
                layer.add(d, x, y)

    @staticmethod
    def _kelp(layer, x, y, h, batch,
              dark=(18, 118, 78),
              mid=(34, 152, 98),
              light=(62, 188, 126)):
        for i in range(h // 12):
            yy = y + i * 12
            dx = (-1 if i % 2 == 0 else 1) * 3
            BackgroundBuilder._rect(layer, x + dx, yy, 8, 12, dark, batch)
            BackgroundBuilder._rect(layer, x + dx + 2, yy + 2, 4, 8, mid, batch, opacity=180)
        BackgroundBuilder._rect(layer, x + 2, y + h - 8, 4, 8, light, batch, opacity=180)

    @staticmethod
    def _coral(layer, x, y, scale, batch,
               base=(180, 118, 116),
               hi=(224, 168, 160),
               accent=(236, 196, 112)):
        p = max(2, int(PX * scale))
        rows = [
            "0000101000",
            "0001111100",
            "0011111110",
            "0011222110",
            "0111222211",
            "0111111111",
            "0011111110",
            "0001111100",
        ]
        for j, row in enumerate(reversed(rows)):
            for i, val in enumerate(row):
                if val == "0":
                    continue
                color = base if val == "1" else hi if val == "2" else accent
                BackgroundBuilder._pixel(layer, x + i * p, y + j * p, color, batch, size=p)

    @staticmethod
    def _rock_cluster(layer, x, y, scale, batch,
                      dark=(72, 94, 112),
                      mid=(94, 120, 140),
                      light=(124, 154, 176)):
        p = max(2, int(PX * scale))
        rows = [
            "00011110000",
            "00122221000",
            "01222222100",
            "12223322210",
            "12222222210",
            "01222222100",
            "00111111000",
        ]
        for j, row in enumerate(reversed(rows)):
            for i, val in enumerate(row):
                if val == "0":
                    continue
                color = dark if val == "1" else mid if val == "2" else light
                BackgroundBuilder._pixel(layer, x + i * p, y + j * p, color, batch, size=p)

    @staticmethod
    def _bubble_column(layer, x, y0, y1, batch):
        y = y0
        step = 26
        i = 0
        while y < y1:
            r = 4 + (i % 3)
            BackgroundBuilder._rect(layer, x, y, r, r, (188, 235, 255), batch, opacity=95)
            BackgroundBuilder._rect(layer, x + 1, y + r - 2, max(1, r - 2), 1, (245, 250, 255), batch, opacity=150)
            y += step + (i % 2) * 5
            i += 1

    @staticmethod
    def _floating_island_detailed(layer, x, y, w, batch):
        BackgroundBuilder._rect(layer, x, y, w, 16, (150, 118, 84), batch)
        BackgroundBuilder._rect(layer, x, y + 14, w, 8, (96, 194, 98), batch)
        BackgroundBuilder._rect(layer, x, y + 20, w, 4, (132, 224, 118), batch)
        BackgroundBuilder._rect(layer, x, y, w, 3, (108, 78, 55), batch, opacity=170)

        # petites dents sous l'île
        for dx in range(10, w - 10, 22):
            h = 8 + (dx // 22) % 3 * 6
            BackgroundBuilder._rect(layer, x + dx, y - h, 8, h, (136, 104, 72), batch)

        # petites touffes
        for dx in range(8, w - 14, 18):
            BackgroundBuilder._rect(layer, x + dx, y + 22, 6, 4, (82, 182, 84), batch)
            BackgroundBuilder._rect(layer, x + dx + 2, y + 26, 2, 4, (132, 228, 118), batch, opacity=180)

    @staticmethod
    def _small_cloud_platform(layer, x, y, batch):
        BackgroundBuilder._rect(layer, x, y, 68, 12, (244, 246, 240), batch, opacity=180)
        BackgroundBuilder._rect(layer, x + 10, y + 10, 48, 6, (216, 230, 245), batch, opacity=150)
        BackgroundBuilder._rect(layer, x + 8, y + 6, 10, 6, (244, 246, 240), batch, opacity=180)
        BackgroundBuilder._rect(layer, x + 48, y + 6, 12, 6, (244, 246, 240), batch, opacity=180)

    # ─────────────────────────────────────────────────────────────
    # Nuages pixel art
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _pixel_cloud(layer, x, y, scale, batch,
                     c1=(245, 245, 235),
                     c2=(220, 232, 236),
                     c3=(205, 220, 228)):
        p = max(2, int(PX * scale))

        rows = [
            "000111100011110000",
            "001111110111111000",
            "011111111111111100",
            "111122111111221110",
            "111111111111111111",
            "011111111111111110",
            "001111111111111100",
            "000111122221111000",
            "000001111111000000",
        ]

        for j, row in enumerate(reversed(rows)):
            for i, val in enumerate(row):
                if val == "0":
                    continue
                color = c1 if val == "1" else c2 if val == "2" else c3
                BackgroundBuilder._pixel(layer, x + i * p, y + j * p, color, batch, size=p)

    @staticmethod
    def _cloud_band(layer, batch, y, width):
        step = 44
        for x in range(0, width + 120, step):
            h = ((x // step) % 3) * 4
            BackgroundBuilder._pixel_cloud(layer, x, y + h, 1.0, batch,
                                           c1=(240, 242, 228),
                                           c2=(220, 232, 236),
                                           c3=(205, 220, 228))

    # ─────────────────────────────────────────────────────────────
    # Skyline / ville simple pixel art
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _skyline_building(layer, x, y, w, h, batch,
                          body=(188, 225, 214),
                          edge=(168, 209, 198),
                          shade=(155, 196, 188)):
        BackgroundBuilder._rect(layer, x, y, w, h, body, batch, opacity=125)
        BackgroundBuilder._rect(layer, x + w - 4, y, 4, h, shade, batch, opacity=120)
        BackgroundBuilder._rect(layer, x, y + h - 4, w, 4, edge, batch, opacity=120)

        # fenêtres en grille simple
        for wx in range(x + 6, x + w - 6, 8):
            for wy in range(y + 8, y + h - 8, 10):
                BackgroundBuilder._rect(layer, wx, wy, 3, 5, (210, 238, 228), batch, opacity=90)

    @staticmethod
    def _city_band(layer, batch, y, width):
        x = 0
        pattern = [(20, 48), (30, 66), (18, 42), (26, 78), (22, 54), (34, 86), (18, 40)]
        idx = 0
        while x < width + 60:
            w, h = pattern[idx % len(pattern)]
            BackgroundBuilder._skyline_building(layer, x, y, w, h, batch)
            x += w + 8
            idx += 1

    # ─────────────────────────────────────────────────────────────
    # Buissons / arbres pixel art
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _bush(layer, x, y, scale, batch,
              dark=(82, 190, 82),
              mid=(104, 214, 98),
              light=(138, 232, 120)):
        p = max(2, int(PX * scale))
        rows = [
            "000011100000",
            "000111110000",
            "001122211000",
            "011222221100",
            "112222222110",
            "122233322210",
            "122222222210",
            "011222221100",
            "001111111000",
        ]
        for j, row in enumerate(reversed(rows)):
            for i, val in enumerate(row):
                if val == "0":
                    continue
                color = dark if val == "1" else mid if val == "2" else light
                BackgroundBuilder._pixel(layer, x + i * p, y + j * p, color, batch, size=p)

    @staticmethod
    def _tree_pixel(layer, x, y, scale, batch):
        p = max(2, int(PX * scale))

        # tronc
        BackgroundBuilder._pixel_block(layer, x + 10 * p, y, 4, 10, (102, 74, 44), batch, size=p)
        BackgroundBuilder._pixel_block(layer, x + 13 * p, y, 1, 10, (76, 52, 28), batch, size=p)

        # feuillage
        rows = [
            "000000111100000000",
            "000011222211000000",
            "000122222221100000",
            "001222333322210000",
            "012223333333221000",
            "122223333333222100",
            "122233333333222100",
            "012223333333221000",
            "001222333322210000",
            "000122222221100000",
            "000011222211000000",
        ]
        ox = x
        oy = y + 8 * p
        for j, row in enumerate(reversed(rows)):
            for i, val in enumerate(row):
                if val == "0":
                    continue
                color = (58, 142, 62) if val == "1" else (94, 188, 86) if val == "2" else (136, 220, 114)
                BackgroundBuilder._pixel(layer, ox + i * p, oy + j * p, color, batch, size=p)

    @staticmethod
    def _vegetation_band(layer, batch, y, width, near=False):
        x = 0
        while x < width + 100:
            if near and (x // 120) % 3 == 0:
                BackgroundBuilder._tree_pixel(layer, x, y, 1.2, batch)
                x += 84
            else:
                scale = 1.0 if near else 0.8
                BackgroundBuilder._bush(layer, x, y, scale, batch,
                                        dark=(72, 176, 72) if not near else (62, 160, 62),
                                        mid=(102, 210, 96) if not near else (92, 194, 88),
                                        light=(142, 228, 120) if not near else (128, 216, 108))
                x += 44 if not near else 52

    # ─────────────────────────────────────────────────────────────
    # Sol
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _grass_top(layer, width, batch, y=36):
        for x in range(0, width, 8):
            BackgroundBuilder._rect(layer, x, y, 8, 8, (84, 210, 78), batch)
            BackgroundBuilder._rect(layer, x, y + 6, 8, 3, (128, 236, 112), batch)
            BackgroundBuilder._rect(layer, x, y - 1, 8, 2, (46, 144, 48), batch, opacity=180)

    @staticmethod
    def _ground_tiles(layer, width, batch, top_y=36):
        tile = 32
        for x in range(0, width, tile):
            for y in range(top_y - 128, top_y, tile):
                base = (174, 100, 80) if ((x // tile) + (y // tile)) % 2 == 0 else (164, 92, 74)
                BackgroundBuilder._rect(layer, x, y, tile, tile, base, batch)
                BackgroundBuilder._rect(layer, x, y + tile - 3, tile, 3, (120, 64, 50), batch)
                BackgroundBuilder._rect(layer, x + tile // 2 - 1, y + 4, 2, tile - 8, (116, 60, 48), batch, opacity=180)

                # fissures simples
                BackgroundBuilder._rect(layer, x + 8, y + 10, 2, 8, (96, 48, 42), batch, opacity=190)
                BackgroundBuilder._rect(layer, x + 10, y + 14, 8, 2, (96, 48, 42), batch, opacity=190)

    # ─────────────────────────────────────────────────────────────
    # Niveau terre détaillé
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_ground(width, height, batch):
        bg = Background(width, height, batch)

        sky = bg.add_layer(0.00)
        far = bg.add_layer(0.05)
        mid = bg.add_layer(0.12)
        near = bg.add_layer(0.22)

        # ciel
        BackgroundBuilder._rect(sky, 0, 0, WORLD_W, height, (95, 192, 214), batch)
        BackgroundBuilder._pattern_dots(sky, WORLD_W, height, batch)

        # bande nuageuse
        BackgroundBuilder._cloud_band(far, batch, 108, WORLD_W)

        # skyline discrète
        BackgroundBuilder._city_band(far, batch, 52, WORLD_W)

        # végétation lointaine
        BackgroundBuilder._vegetation_band(mid, batch, 34, WORLD_W, near=False)
        BackgroundBuilder._rect(mid, 0, 28, WORLD_W, 10, (110, 214, 104), batch, opacity=160)

        # végétation proche
        BackgroundBuilder._vegetation_band(near, batch, 32, WORLD_W, near=True)
        BackgroundBuilder._rect(near, 0, 26, WORLD_W, 8, (88, 188, 82), batch, opacity=180)

        # sol
        BackgroundBuilder._grass_top(near, WORLD_W, batch, y=36)
        BackgroundBuilder._ground_tiles(near, WORLD_W, batch, top_y=36)

        return bg

    # ─────────────────────────────────────────────────────────────
    # Eau
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_water(width, height, batch):
        bg = Background(width, height, batch)

        sky = bg.add_layer(0.00)
        far = bg.add_layer(0.08)
        mid = bg.add_layer(0.18)
        near = bg.add_layer(0.30)

        # Fond marin bleu profond
        BackgroundBuilder._rect(sky, 0, 0, WORLD_W, height, (36, 122, 196), batch)
        BackgroundBuilder._rect(sky, 0, height - 120, WORLD_W, 120, (82, 182, 232), batch, opacity=110)
        BackgroundBuilder._pattern_dots(sky, WORLD_W, height, batch)

        # Colonnes de lumière
        for x in range(0, WORLD_W, 110):
            w = 34 + (x // 110 % 3) * 8
            BackgroundBuilder._rect(far, x, 80, w, height - 80, (126, 214, 255), batch, opacity=22)
            BackgroundBuilder._rect(far, x + 8, 100, w // 2, height - 120, (190, 238, 255), batch, opacity=14)

        # Rochers lointains
        for x in range(20, WORLD_W, 180):
            BackgroundBuilder._rock_cluster(far, x, 40, 1.0, batch,
                                            dark=(70, 92, 110),
                                            mid=(92, 118, 138),
                                            light=(118, 146, 168))

        # Bulles
        for x in range(60, WORLD_W, 220):
            BackgroundBuilder._bubble_column(far, x, 90, height - 60, batch)

        # Coraux et algues plan moyen
        for x in range(30, WORLD_W, 120):
            BackgroundBuilder._coral(mid, x, 42, 1.0 + ((x // 120) % 2) * 0.2, batch,
                                     base=(164, 110, 120),
                                     hi=(214, 156, 162),
                                     accent=(230, 194, 118))

        for x in range(70, WORLD_W, 90):
            h = 60 + (x // 90 % 4) * 18
            BackgroundBuilder._kelp(mid, x, 36, h, batch)

        # Bande rocheuse proche
        for x in range(0, WORLD_W, 84):
            h = 22 + (x // 84 % 3) * 8
            BackgroundBuilder._rect(near, x, 36, 84, h, (88, 96, 108), batch)
            BackgroundBuilder._rect(near, x, 36 + h - 4, 84, 4, (124, 134, 146), batch, opacity=170)

        # Sol sableux
        BackgroundBuilder._rect(near, 0, 0, WORLD_W, 44, (154, 126, 92), batch)
        BackgroundBuilder._rect(near, 0, 36, WORLD_W, 10, (206, 180, 126), batch)
        BackgroundBuilder._rect(near, 0, 44, WORLD_W, 4, (228, 206, 152), batch, opacity=150)

        # Petits détails de sol
        for x in range(0, WORLD_W, 34):
            BackgroundBuilder._rect(near, x + 8, 10, 4, 2, (182, 156, 112), batch, opacity=180)
            if (x // 34) % 3 == 0:
                BackgroundBuilder._rect(near, x + 14, 16, 6, 3, (132, 110, 82), batch, opacity=170)

        # Reflets de surface
        for x in range(0, WORLD_W, 38):
            BackgroundBuilder._rect(near, x, height - 118, 22, 3, (176, 238, 255), batch, opacity=150)
            BackgroundBuilder._rect(near, x + 8, height - 124, 14, 2, (128, 212, 245), batch, opacity=120)

        return bg

    # ─────────────────────────────────────────────────────────────
    # Ciel
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_sky(width, height, batch):
        bg = Background(width, height, batch)

        sky = bg.add_layer(0.00)
        far = bg.add_layer(0.08)
        mid = bg.add_layer(0.16)
        near = bg.add_layer(0.28)

        # Grand ciel
        BackgroundBuilder._rect(sky, 0, 0, WORLD_W, height, (136, 212, 255), batch)
        BackgroundBuilder._rect(sky, 0, height - 140, WORLD_W, 140, (178, 228, 255), batch, opacity=90)
        BackgroundBuilder._pattern_dots(sky, WORLD_W, height, batch)

        # Petits nuages lointains
        for x in range(40, WORLD_W, 190):
            yy = 455 + (x // 190 % 3) * 18
            BackgroundBuilder._pixel_cloud(far, x, yy, 0.9, batch,
                                           c1=(248, 248, 240),
                                           c2=(224, 236, 246),
                                           c3=(205, 222, 236))

        # Gros nuages détaillés
        for x in range(120, WORLD_W, 420):
            yy = 290 + (x // 420 % 3) * 35
            BackgroundBuilder._pixel_cloud(mid, x, yy, 2.2, batch,
                                           c1=(248, 248, 242),
                                           c2=(224, 236, 246),
                                           c3=(206, 222, 236))
            BackgroundBuilder._pixel_cloud(mid, x + 90, yy - 10, 1.5, batch,
                                           c1=(248, 248, 242),
                                           c2=(224, 236, 246),
                                           c3=(206, 222, 236))

        # Îles flottantes détaillées
        islands = [
            (120, 180, 140),
            (380, 270, 200),
            (690, 220, 150),
            (980, 330, 220),
            (1320, 250, 170),
            (1640, 360, 220),
            (1980, 280, 180),
            (2290, 410, 150),
        ]
        for x, y, w in islands:
            BackgroundBuilder._floating_island_detailed(mid, x, y, w, batch)

        # Mini nuages-plateformes
        for x in range(0, WORLD_W, 260):
            yy = 100 + (x // 260 % 4) * 28
            BackgroundBuilder._small_cloud_platform(near, x + 30, yy, batch)

        # Quelques petits nuages au premier plan
        for x in range(80, WORLD_W, 360):
            yy = 150 + (x // 360 % 3) * 40
            BackgroundBuilder._pixel_cloud(near, x, yy, 1.2, batch,
                                           c1=(250, 250, 244),
                                           c2=(228, 238, 248),
                                           c3=(210, 226, 238))

        return bg