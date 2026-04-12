import pyglet
from pyglet.window import key
from pyglet import shapes
from pyglet.gl import GL_NEAREST

from ui      import MainMenu
from hud     import HUD
from menus   import OptionsMenu, StatsScreen
from enemies import EnemyManager, Projectile
from level_system import LevelManager
from ui import MainMenu, LevelSelect, Button, GameOverMenu, VictoryScreen

son_pas  = pyglet.media.load("musique/bruit_de_pas.wav", streaming=False)
son_saut = pyglet.media.load("musique/saut.flac",        streaming=False)


WIDTH        = 900
HEIGHT       = 600
GRAVITY      = 1800
PLAYER_SPEED = 300
JUMP_FORCE   = 650


# ── Entités ────────────────────────────────────────────────────────────────────

class Entity:
    def __init__(self, x, y, w, h, batch):
        self.x, self.y          = x, y
        self.width, self.height = w, h
        self.vel_x = self.vel_y = 0
        self.on_ground = False
        self.solid     = True
        self.shape = shapes.Rectangle(x, y, w, h, color=(200, 80, 80), batch=batch)

    def update(self, dt):
        pass

    def sync_graphics(self):
        self.shape.x = self.x
        self.shape.y = self.y


# ── Animation du joueur ───────────────────────────────────────────────────────

class PlayerSprite:
    """
    Gère les sprites animés du joueur selon :
      - le niveau (monture : cheval / dauphin / phénix)
      - l'état   : marche (3 frames), saut, chute
      - la direction : droite (_r) ou gauche (_left)
    """

    FRAME_DURATION = 0.2   # secondes entre chaque frame de marche

    # Sprites par monture : (walk_r1..3, walk_l1..3, jump, fall)
    MOUNTS = {
        "cheval":  "greta_cheval",
        "dauphin": "greta_dauphin",
        "phenix":  "greta_phenix",
    }

    def __init__(self, batch):
        self._batch    = batch
        self._sprite   = None
        self._images   = {}      # cache des images chargées
        self._mount    = "cheval"
        self._facing   = 1       # 1=droite, -1=gauche
        self._state    = "walk"  # walk | jump | fall
        self._frame    = 0
        self._timer    = 0.0

    def load_mount(self, mount_name):
        """Charge toutes les images d'une monture dans le cache."""
        self._mount = mount_name
        self._images.clear()
        prefix = self.MOUNTS.get(mount_name, "greta_cheval")
        keys = {}
        for i in range(1, 4):
            keys[f"walk_r{i}"] = f"assets/{prefix}_frame{i}.png"
        keys["jump"] = f"assets/{prefix}_saut.png"
        keys["fall"] = f"assets/{prefix}_chute.png"

        for k, path in keys.items():
            try:
                img = pyglet.image.load(path)
                self._images[k] = img
                # Créer version flippée
                self._images[k + "_l"] = self._flip_image(img)
            except Exception as e:
                print(f"[PlayerSprite] {path} : {e}")
                self._images[k] = None
                self._images[k + "_l"] = None

        first = self._images.get("walk_r1")
        if first:
            if self._sprite is None:
                self._sprite = pyglet.sprite.Sprite(first, x=0, y=0, batch=self._batch)
            else:
                self._sprite.image = first
        self._frame  = 0
        self._timer  = 0.0
        self._facing = 1
        self._state  = "walk"

    @staticmethod
    def _flip_image(img):
        """Retourne une copie de l'image flippée horizontalement, sans PIL."""
        try:
            data   = img.get_image_data()
            w, h   = data.width, data.height
            fmt    = 'RGBA'
            pitch  = w * 4
            raw    = data.get_data(fmt, pitch)
            rows   = []
            for r in range(h):
                row = raw[r*pitch:(r+1)*pitch]
                # Inverser les pixels 4 par 4
                pixels = [row[i*4:(i+1)*4] for i in range(w)]
                pixels.reverse()
                rows.append(b''.join(pixels))
            return pyglet.image.ImageData(w, h, fmt, b''.join(rows), pitch)
        except Exception as e:
            print(f"[flip] {e}")
            return img

    def _get_image(self):
        """Retourne l'image selon l'état et la direction."""
        suffix = "_l" if self._facing == -1 else ""
        if self._state == "jump":
            return self._images.get(f"jump{suffix}")
        if self._state == "fall":
            return self._images.get(f"fall{suffix}")
        return self._images.get(f"walk_r{self._frame + 1}{suffix}")

    def update(self, dt, player, held):
        """Met à jour l'état, la direction et l'animation."""
        # Hitstun : clignotement du sprite, pas de mise à jour direction/état
        if player.hitstun > 0:
            if self._sprite:
                self._timer += dt
                if self._timer >= 0.1:
                    self._timer = 0.0
                    self._sprite.opacity = 80 if self._sprite.opacity > 100 else 255
            return

        if self._sprite:
            self._sprite.opacity = 255

        # Direction — on utilise scale_x pour flipper
        if key.Q in held or key.LEFT in held:
            self._facing = -1
        elif key.D in held or key.RIGHT in held:
            self._facing = 1

        # État
        if not player.on_ground:
            self._state = "fall" if player.vel_y < 0 else "jump"
        else:
            self._state = "walk"

        # Avance les frames de marche
        if self._state == "walk":
            self._timer += dt
            if self._timer >= self.FRAME_DURATION:
                self._timer = 0.0
                self._frame = (self._frame + 1) % 3
        else:
            self._frame = 0
            self._timer = 0.0

        # Applique l'image selon direction
        if self._sprite:
            img = self._get_image()
            if img and self._sprite.image != img:
                self._sprite.image = img

    def apply_camera(self, player, offset_x):
        """Positionne le sprite à l'écran selon la caméra."""
        if self._sprite:
            self._sprite.x = int(player.x - offset_x)
            self._sprite.y = int(player.y)

    def delete(self):
        if self._sprite:
            try: self._sprite.delete()
            except: pass
            self._sprite = None
        self._images.clear()


class Player(Entity):
    def __init__(self, x, y, batch):
        super().__init__(x, y, 40, 60, batch)
        self.hp               = 10
        self.jumps            = 0
        self.deaths           = 0
        self.hitstun          = 0.0
        self._jumps_left      = 2    # sauts disponibles (2 = double saut)
        self.shape.visible    = False
        self.sprite_anim      = PlayerSprite(batch)

    def update(self, dt):
        pass


class Platform(Entity):
    def __init__(self, x, y, w, h, batch):
        super().__init__(x, y, w, h, batch)
        self.shape.color = (120, 200, 120)
        self._visual_sprites = []   # sprites visuels (décalés par caméra)
        self._trunk_rects    = []   # troncs/tiges (pyglet shapes)

    def set_sprite(self, image_path, theme, batch):
        """Charge le sprite de surface + génère le tronc/tige selon le thème."""
        try:
            img = pyglet.image.load(image_path)
            tex = img.get_texture()
            tex.min_filter = GL_NEAREST
            tex.mag_filter = GL_NEAREST
            # Sprite de surface étiré sur toute la largeur de la plateforme
            sp = pyglet.sprite.Sprite(img, x=self.x, y=self.y, batch=batch)
            sp.scale_x = self.width  / img.width
            sp.scale_y = self.height / img.height
            self._visual_sprites.append(sp)
            # Cacher le rectangle de collision
            self.shape.visible = False

            if theme == "ground":
                # Tronc brun qui descend de la plateforme jusqu'au sol (y=40)
                trunk_w  = max(6, self.width // 8)
                trunk_x  = self.x + (self.width - trunk_w) // 2
                trunk_h  = self.y - 40   # hauteur du tronc
                if trunk_h > 0:
                    # Corps du tronc
                    r = shapes.Rectangle(trunk_x, 40, trunk_w, trunk_h,
                                         color=(101, 67, 33), batch=batch)
                    self._trunk_rects.append(r)
                    # Reflet clair sur le bord gauche
                    r2 = shapes.Rectangle(trunk_x, 40, max(2, trunk_w//4),
                                          trunk_h, color=(139, 90, 43), batch=batch)
                    self._trunk_rects.append(r2)

            elif theme == "water":
                # Tige d'algue fine qui descend jusqu'au sol
                stem_w = max(4, self.width // 12)
                stem_x = self.x + (self.width - stem_w) // 2
                stem_h = self.y - 40
                if stem_h > 0:
                    r = shapes.Rectangle(stem_x, 40, stem_w, stem_h,
                                         color=(20, 120, 60), batch=batch)
                    self._trunk_rects.append(r)
                    r2 = shapes.Rectangle(stem_x, 40, max(2, stem_w//3),
                                          stem_h, color=(40, 180, 80), batch=batch)
                    self._trunk_rects.append(r2)
            # theme == "sky" : nuage flottant, pas de tige

        except Exception as e:
            print(f"[Platform] sprite non chargé : {e}")

    def apply_camera(self, offset_x):
        """Décale tous les visuels selon la caméra."""
        screen_x = self.x - offset_x
        for sp in self._visual_sprites:
            sp.x = screen_x
            sp.y = self.y
        for i, r in enumerate(self._trunk_rects):
            # Les troncs/tiges sont stockés par paires (corps + reflet)
            # On recalcule leur x relatif à self.x
            if i % 2 == 0:
                trunk_w = r.width
                r.x = screen_x + (self.width - trunk_w) // 2
            else:
                r.x = screen_x + (self.width - self._trunk_rects[i-1].width) // 2

    def clear_visuals(self):
        for sp in self._visual_sprites:
            try: sp.delete()
            except: pass
        for r in self._trunk_rects:
            try: r.batch = None
            except: pass
        self._visual_sprites.clear()
        self._trunk_rects.clear()

    def update(self, dt):
        pass


# ── Physique ───────────────────────────────────────────────────────────────────

class PhysicsWorld:
    def __init__(self):
        self.entities = []

    def add(self, e):
        self.entities.append(e)

    def update(self, dt):
        for e in self.entities:
            if isinstance(e, Platform):
                continue
            e.vel_y -= GRAVITY * dt
            e.x += e.vel_x * dt
            self._resolve(e, "x")
            e.y += e.vel_y * dt
            e.on_ground = False
            self._resolve(e, "y")
            # Réinitialiser les sauts disponibles quand on touche le sol
            if e.on_ground and hasattr(e, '_jumps_left'):
                e._jumps_left = 1
            e.sync_graphics()

    @staticmethod
    def _overlap(a, b):
        return (a.x < b.x + b.width  and a.x + a.width  > b.x and
                a.y < b.y + b.height and a.y + a.height > b.y)

    def _resolve(self, e, axis):
        for o in self.entities:
            if o is e or not o.solid:
                continue
            if self._overlap(e, o):
                if axis == "x":
                    e.x = o.x - e.width if e.vel_x > 0 else o.x + o.width
                    e.vel_x = 0
                else:
                    if e.vel_y < 0:
                        e.y, e.vel_y, e.on_ground = o.y + o.height, 0, True
                    else:
                        e.y, e.vel_y = o.y - e.height, 0


# ── Caméra ─────────────────────────────────────────────────────────────────────

class Camera:
    SMOOTH = 6.0

    def __init__(self, window, level_width=8000):
        self.window      = window
        self.level_width = level_width
        self.offset_x    = 0.0

    def reset(self):
        self.offset_x = 0.0

    def update(self, target, dt):
        ideal = target.x + target.width / 2 - self.window.width / 2
        self.offset_x += (ideal - self.offset_x) * self.SMOOTH * dt
        self.offset_x = max(0, min(self.offset_x, self.level_width))

    def apply(self, entities):
        for e in entities:
            e.shape.x = e.x - self.offset_x
            e.shape.y = e.y

    def apply_projectiles(self, projectiles):
        """Applique le décalage caméra aux projectiles du joueur."""
        for p in projectiles:
            p.shape.x = int(p.x - self.offset_x)
            p.shape.y = int(p.y)

    def apply_platforms(self, entities):
        """Décale les sprites visuels des plateformes selon la caméra."""
        for e in entities:
            if isinstance(e, Platform) and hasattr(e, 'apply_camera'):
                e.apply_camera(self.offset_x)

    def apply_enemies(self, enemies):
        """Applique le décalage caméra aux sprites animés des ennemis."""
        for e in enemies:
            if hasattr(e, 'animation'):
                e.animation.sprite.x = int(e.x - self.offset_x)
                e.animation.sprite.y = int(e.y)
            # Barre de vie aussi
            if hasattr(e, '_hp_bg'):
                e._hp_bg.x  = int(e.x - self.offset_x)
                e._hp_bg.y  = int(e.y + e.HEIGHT + 4)
            if hasattr(e, '_hp_bar'):
                e._hp_bar.x = int(e.x - self.offset_x)
                e._hp_bar.y = int(e.y + e.HEIGHT + 4)
            # Éclairs du NuageMechant
            if hasattr(e, '_lightning'):
                for bolt in e._lightning:
                    bolt.apply_camera(self.offset_x)
            # Flammes du Dragon
            if hasattr(e, '_flames'):
                for flame in e._flames:
                    flame.apply_camera(self.offset_x)
            # Plumes de l'Aigle
            if hasattr(e, '_feathers'):
                for feather in e._feathers:
                    feather.apply_camera(self.offset_x)
            # Orbes de l'Elfe
            if hasattr(e, '_orbs'):
                for orb in e._orbs:
                    orb.apply_camera(self.offset_x)


# ── Jeu ────────────────────────────────────────────────────────────────────────

class Game:

    # Cooldown entre deux tirs du joueur (secondes)
    SHOOT_CD = 0.3

    def __init__(self):
        self.window    = pyglet.window.Window(WIDTH, HEIGHT, "Platformer Engine", resizable=True)

        # Activer la transparence PNG globalement une seule fois
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.bg_batch  = pyglet.graphics.Batch()
        self.batch     = pyglet.graphics.Batch()
        self.hud_batch = pyglet.graphics.Batch()

        self.world         = PhysicsWorld()
        self.camera        = Camera(self.window)
        self.enemy_manager = EnemyManager(self.batch)

        self.PlatformClass = Platform

        self._score   = 0
        self._time    = 0.0
        self._running = False
        self._held    = set()

        # ── Tir joueur ────────────────────────────────────────────────────────
        self.player_projectiles = []
        self._shoot_timer       = 0.0   # cooldown entre deux tirs

        self.player = Player(100, 60, self.batch)
        self.world.add(self.player)

        self.level_manager = LevelManager(self)
        self.enemy_manager.set_world(self.world.entities)

        self._build_ui()
        self.main_menu.show()
        self.hud.hide()

        self.son_pas  = son_pas
        self.son_saut = son_saut
        self._step_timer = 0

        pyglet.clock.schedule_interval(self.update, 1 / 60)

        @self.window.event
        def on_key_press(symbol, modifiers):
            self._held.add(symbol)
            if symbol == key.F11:
                self.window.set_fullscreen(not self.window.fullscreen)
            if symbol == key.ESCAPE and self._running:
                self._on_back_to_main()
            if symbol == key.TAB and self._running:
                if self.level_manager._hub_active:
                    self._on_start_level(0)
                else:
                    self.level_manager.next_level()
                    self._load_player_mount(self.level_manager.index)
            if symbol == key.I and self._running:
                self._invincible = not getattr(self, '_invincible', False)
                print(f"[INVINCIBLE] {'ON' if self._invincible else 'OFF'}")
            if symbol == key.H and self._running and not self.level_manager._hub_active:
                self._on_exit_to_levels()
            if symbol == key.E and self._running:
                for npc in self.level_manager._npcs:
                    npc.toggle_bubble(self.player)
            # Double saut (déclenché sur pression unique, pas en hold)
            if (symbol in (key.SPACE, key.UP, key.Z) and self._running):
                p = self.player
                if not p.on_ground and p._jumps_left > 0 and p.hitstun <= 0:
                    p.vel_y       = JUMP_FORCE * 0.85   # légèrement moins fort
                    p._jumps_left -= 1
                    p.jumps      += 1
                    self.son_saut.play()

        @self.window.event
        def on_key_release(symbol, modifiers):
            self._held.discard(symbol)

        @self.window.event
        def on_draw():
            self.window.clear()
            self.bg_batch.draw()
            if self._running:
                self.batch.draw()
            self.hud_batch.draw()

        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            if self.game_over_menu._visible:
                self.game_over_menu.on_mouse_press(x, y, button, modifiers)
            elif self.victory_screen._visible:
                self.victory_screen.on_mouse_press(x, y, button, modifiers)
            elif self.level_menu._visible:
                self.level_menu.on_mouse_press(x, y, button, modifiers)
            elif self.options_menu.is_visible:
                self.options_menu.on_mouse_press(x, y, button, modifiers)
            elif self.stats_screen.is_visible:
                self.stats_screen.on_mouse_press(x, y, button, modifiers)
            elif self.main_menu._visible:
                self.main_menu.on_mouse_press(x, y, button, modifiers)
            elif self._running:
                self.exit_btn.on_mouse_press(x, y, button, modifiers)

        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            if self.game_over_menu._visible:
                self.game_over_menu.on_mouse_release(x, y, button, modifiers)
            elif self.victory_screen._visible:
                self.victory_screen.on_mouse_release(x, y, button, modifiers)
            elif self.level_menu._visible:
                self.level_menu.on_mouse_release(x, y, button, modifiers)
            elif self.options_menu.is_visible:
                self.options_menu.on_mouse_release(x, y, button, modifiers)
            elif self.stats_screen.is_visible:
                self.stats_screen.on_mouse_release(x, y, button, modifiers)
            elif self.main_menu._visible:
                self.main_menu.on_mouse_release(x, y, button, modifiers)
            elif self._running:
                self.exit_btn.on_mouse_release(x, y, button, modifiers)

        @self.window.event
        def on_mouse_motion(x, y, dx, dy):
            if self.main_menu._visible:
                self.main_menu.on_mouse_motion(x, y, dx, dy)
            elif self.victory_screen._visible:
                self.victory_screen.on_mouse_motion(x, y, dx, dy)
            elif self.level_menu._visible:
                self.level_menu.on_mouse_motion(x, y, dx, dy)
            elif self.options_menu.is_visible:
                self.options_menu.on_mouse_motion(x, y, dx, dy)
            elif self.stats_screen.is_visible:
                self.stats_screen.on_mouse_motion(x, y, dx, dy)
            elif self._running:
                self.exit_btn.on_mouse_motion(x, y, dx, dy)

        @self.window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self.options_menu.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        @self.window.event
        def on_resize(width, height):
            was_running = self._running
            self._build_ui()
            if self.level_manager._current_bg:
                self.level_manager._current_bg.on_resize(width, height)
            if was_running:
                self.main_menu.hide()
                self.level_menu.hide()
                self.hud.show()
                self.exit_btn.set_visible(True)
                self._running = True
            else:
                self.main_menu.show()
                self.hud.hide()
                self.exit_btn.set_visible(False)

    # ── Monture joueur ────────────────────────────────────────────────────────

    def _load_player_mount(self, level_index):
        """Charge la monture correspondant au niveau (0=cheval, 1=dauphin, 2=phénix)."""
        mounts = ["cheval", "dauphin", "phenix"]
        mount  = mounts[level_index % len(mounts)]
        print(f"[DEBUG] Chargement monture : niveau={level_index} → {mount}")
        self.player.sprite_anim.load_mount(mount)
        print(f"[DEBUG] Monture chargée. Images : {list(self.player.sprite_anim._images.keys())}")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        w, h = self.window.width, self.window.height
        self.hud_batch = pyglet.graphics.Batch()

        self.hud = HUD(w, h, self.hud_batch, max_hp=10, show_stats=True)

        self.game_over_menu = GameOverMenu(w, h, self.hud_batch,
                                           on_retry=self._on_retry,
                                           on_menu=self._on_back_to_main)

        self.exit_btn = Button(16, h - 110, 80, 40, "PORTIER",
                               self.hud_batch, self.hud._grp, self.hud._grp,
                               on_click=self._on_exit_to_levels)
        self.exit_btn.set_visible(False)

        self.main_menu = MainMenu(w, h, self.hud_batch,
                                  on_play=self._on_play,
                                  on_options=self._on_options,
                                  on_quit=pyglet.app.exit)

        self.level_menu   = LevelSelect(w, h, self.hud_batch, on_level_selected=self._on_start_level)
        self.options_menu = OptionsMenu(w, h, self.hud_batch, on_back=self._on_back_to_main)
        self.stats_screen = StatsScreen(w, h, self.hud_batch, on_back=self._on_back_to_main)
        self.victory_screen = VictoryScreen(w, h, self.hud_batch, on_menu=self._on_back_to_main)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_play(self):
        if not self.game_over_menu._visible:
            self.main_menu.hide()
            self.options_menu.hide()
            self.stats_screen.hide()
            self.hud.hide()
            self._start_hub()

    def _start_hub(self):
        """Lance le hub de sélection de niveau."""
        self.level_manager.load_hub()
        self._load_player_mount(0)
        self.hud.show()
        self.camera.reset()
        self._held.clear()
        self.player_projectiles.clear()
        self._shoot_timer = 0.0
        self.exit_btn.set_visible(False)
        self._running = True

    def _on_start_level(self, level_index):
        self.level_menu.hide()
        self.level_manager.load(level_index)
        self.enemy_manager.set_world(self.world.entities)
        self._load_player_mount(level_index)   # change de monture selon le niveau
        self.hud.show()
        self.camera.reset()
        self._held.clear()
        self.player_projectiles.clear()
        self._shoot_timer = 0.0
        self.exit_btn.set_visible(True)
        self._running = True

    def _on_exit_to_levels(self):
        """Quitte le niveau en cours pour revenir au hub."""
        self._running = False
        self.hud.hide()
        self.exit_btn.set_visible(False)
        self.main_menu.hide()
        self._start_hub()

    def _on_retry(self):
        self.game_over_menu.hide()
        self.player_projectiles.clear()
        self._shoot_timer = 0.0
        if self.level_manager._hub_active:
            self._start_hub()
        else:
            self.level_manager.load(self.level_manager.index)
            self.hud.show()
            self.exit_btn.set_visible(True)
            self._running = True

    def _on_victory(self):
        """Fin du jeu — affiche l'écran de victoire."""
        self._running = False
        self.hud.hide()
        self.exit_btn.set_visible(False)
        self.victory_screen.show()

    def _on_options(self):
        self.main_menu.hide()
        self.options_menu.show()

    def _on_back_to_main(self):
        self._running = False
        self._held.clear()
        self.options_menu.hide()
        self.stats_screen.hide()
        self.level_menu.hide()
        self.game_over_menu.hide()
        self.victory_screen.hide()
        self.exit_btn.set_visible(False)
        self.hud.hide()
        self.main_menu.show()

    # ── Tir joueur ────────────────────────────────────────────────────────────

    def _try_shoot(self):
        """Crée un projectile dans la direction où regarde le joueur (touche F)."""
        p = self.player
        # Direction : droite par défaut, gauche si le joueur se déplace à gauche
        direction = -1 if key.Q in self._held or key.LEFT in self._held else 1
        proj = Projectile(
            p.x + p.width  / 2,
            p.y + p.height / 2,
            direction, 0,
            damage=25,
            speed=700,
            color=(255, 230, 50),
            radius=8,
            batch=self.batch,
        )
        self.player_projectiles.append(proj)

    def _update_player_projectiles(self, dt):
        """Met à jour les projectiles du joueur et détecte les collisions."""
        for proj in self.player_projectiles:
            proj.update(dt)
            if not proj.alive:
                continue
            # Collision avec les ennemis
            for enemy in self.enemy_manager.enemies:
                if enemy.alive and proj.hits_rect(enemy):
                    enemy.take_damage(proj.damage)
                    self._score += 10        # +10 points par touche
                    proj.destroy()
                    break

        # Décalage caméra sur les projectiles du joueur
        self.camera.apply_projectiles(self.player_projectiles)

        # Nettoyage
        self.player_projectiles = [p for p in self.player_projectiles if p.alive]

    # ── Collisions dégâts ────────────────────────────────────────────────────

    def _check_damage(self, p):
        """
        Vérifie toutes les sources de dégâts en un seul endroit.
        Si le joueur n'est pas en hitstun et qu'une hitbox le touche :
          → -1 PV + hitstun selon la source
        """
        if p.hitstun > 0 or getattr(self, '_invincible', False):
            return   # invincible

        def rect_hit(ex, ey, ew, eh):
            """Collision AABB entre le joueur et un rectangle monde."""
            return (p.x < ex + ew and p.x + p.width  > ex and
                    p.y < ey + eh and p.y + p.height > ey)

        def circle_hit(cx, cy, radius):
            """Collision cercle/rectangle entre le joueur et un projectile."""
            import math
            pcx = p.x + p.width  / 2
            pcy = p.y + p.height / 2
            return math.hypot(cx - pcx, cy - pcy) < radius + min(p.width, p.height) / 2

        for e in self.enemy_manager.enemies:
            if not e.alive:
                continue

            # ── Contact direct avec le sprite de l'ennemi ──────────────────
            if rect_hit(e.x, e.y, e.width, e.height):
                hitstun = 2.0 if e.__class__.__name__ == "Requin" else 0.5
                print(f"[HIT] {e.__class__.__name__} px={p.x:.0f} py={p.y:.0f} ex={e.x:.0f} ey={e.y:.0f} ew={e.width} eh={e.height}")
                p.hp      = max(0, p.hp - 1)
                p.hitstun = hitstun
                return

            # ── Flammes du Dragon ──────────────────────────────────────────
            if hasattr(e, '_flames'):
                for f in e._flames:
                    if f.alive and circle_hit(f.x, f.y, 14):
                        p.hp      = max(0, p.hp - 1)
                        p.hitstun = 0.5
                        f.destroy()
                        return

            # ── Plumes de l'Aigle ──────────────────────────────────────────
            if hasattr(e, '_feathers'):
                for f in e._feathers:
                    if f.alive and rect_hit(f.x, f.y, 18, 4):
                        p.hp      = max(0, p.hp - 1)
                        p.hitstun = 0.3
                        f.destroy()
                        return

            # ── Orbes de l'Elfe ────────────────────────────────────────────
            if hasattr(e, '_orbs'):
                for orb in e._orbs:
                    if orb.alive and circle_hit(orb.x, orb.y, 10):
                        p.hp      = max(0, p.hp - 1)
                        p.hitstun = 0.4
                        orb.destroy()
                        return

            # ── Éclairs du NuageMechant ────────────────────────────────────
            if hasattr(e, '_lightning'):
                for bolt in e._lightning:
                    if bolt.alive:
                        pcx = p.x + p.width / 2
                        if (abs(pcx - bolt.cx) < 28 and
                                bolt.y_bottom <= p.y + p.height and
                                p.y <= bolt.y_top):
                            p.hp      = max(0, p.hp - 1)
                            p.hitstun = 0.4
                            bolt.destroy()
                            return

        # ── Projectiles ennemis génériques (Elfe, etc.) ────────────────────
        for proj in self.enemy_manager.projectiles:
            if proj.alive and circle_hit(proj.x, proj.y, proj.radius):
                p.hp      = max(0, p.hp - 1)
                p.hitstun = 0.4
                proj.destroy()
                return

    # ── Boucle ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if not self._running:
            return

        if not self.level_manager._hub_active and self.player.x > 7000:
            if self.level_manager.index == 2:
                self._on_victory()
                return
            else:
                self._start_hub()
                return

        self._time += dt
        p = self.player

        # ── Hitstun (invincibilité) ───────────────────────────────────────────
        if p.hitstun > 0:
            p.hitstun = max(0.0, p.hitstun - dt)
            p.vel_x = 0
        else:
            # ── Déplacement ───────────────────────────────────────────────────
            p.vel_x = 0
            if key.Q in self._held or key.LEFT in self._held:
                p.vel_x = -PLAYER_SPEED
            if key.D in self._held or key.RIGHT in self._held:
                p.vel_x = PLAYER_SPEED

            # ── Saut ──────────────────────────────────────────────────────────
            if (key.SPACE in self._held or key.UP in self._held or key.Z in self._held) and p.on_ground:
                p.vel_y        = JUMP_FORCE
                p.on_ground    = False
                p._jumps_left  = 1
                p._hub_lock    = False   # lever le lock au premier saut
                p.jumps       += 1
                self.son_saut.play()

        # ── Sons de pas ───────────────────────────────────────────────────────
        moving = p.vel_x != 0 and p.on_ground
        if moving:
            self._step_timer -= dt
            if self._step_timer <= 0:
                self.son_pas.play()
                self._step_timer = 0.4
        else:
            self._step_timer = 0

        # ── Tir (touche F) ────────────────────────────────────────────────────
        self._shoot_timer = max(0.0, self._shoot_timer - dt)
        if key.F in self._held and self._shoot_timer <= 0:
            self._try_shoot()
            self._shoot_timer = self.SHOOT_CD

        # ── Physique + ennemis ────────────────────────────────────────────────
        self.world.update(dt)
        self.enemy_manager.update(dt, p)
        self._check_damage(p)
        self._update_player_projectiles(dt)
        self.level_manager.update_background()

        # ── Mort du joueur ────────────────────────────────────────────────────
        if p.hp <= 0:
            self._running = False
            self.exit_btn.set_visible(False)
            self.game_over_menu.show()
            p.deaths += 1
            return

        # ── Animation joueur ──────────────────────────────────────────────────
        p.sprite_anim.update(dt, p, self._held)

        # ── Caméra ────────────────────────────────────────────────────────────
        self.camera.update(p, dt)
        self.camera.apply(self.world.entities)
        self.camera.apply_platforms(self.world.entities)
        self.camera.apply_enemies(self.enemy_manager.enemies)
        self.camera.apply_projectiles(self.player_projectiles)
        p.sprite_anim.apply_camera(p, self.camera.offset_x)
        self.hud.update(p, hp=p.hp, score=self._score)
        self.stats_screen.update_stats(
            time_sec=self._time, jumps=p.jumps,
            deaths=p.deaths, best_score=self._score,
        )


if __name__ == "__main__":
    game = Game()
    pyglet.app.run()