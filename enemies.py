# enemies.py
# Système d'ennemis : mêlée et rangé
# MODIFIÉ : animations 3 frames, shape caché, destroy() corrigé, hits_rect() ajouté

import pyglet
from pyglet import shapes
import math

# ── Constantes ────────────────────────────────────────────────────────────────

PIXEL_PER_METER = 40

MELEE_RANGE_M  = 10
RANGED_RANGE_M = 20

MELEE_RANGE_PX  = MELEE_RANGE_M  * PIXEL_PER_METER   # 400 px
RANGED_RANGE_PX = RANGED_RANGE_M * PIXEL_PER_METER   # 800 px

ATTACK_COOLDOWN = 1.5


# ── Animation 3 frames ────────────────────────────────────────────────────────

class SimpleAnimation:
    """Gère un sprite animé sur 3 frames chargées depuis des fichiers image."""

    def __init__(self, x, y, frame_paths, frame_duration=0.2, batch=None):
        self.frames = [pyglet.image.load(path) for path in frame_paths]
        self.sprite = pyglet.sprite.Sprite(self.frames[0], x=x, y=y, batch=batch)
        self.frame_index = 0
        self.timer = 0.0
        self.frame_duration = frame_duration

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.sprite.image = self.frames[self.frame_index]

    def set_position(self, x, y):
        self.sprite.x = int(x)
        self.sprite.y = int(y)

    def delete(self):
        self.sprite.delete()


# ── Projectile ────────────────────────────────────────────────────────────────

class Projectile:
    def __init__(self, x, y, dx, dy, damage, speed, color, radius, batch):
        self.x, self.y   = float(x), float(y)
        self.damage      = damage
        self.speed       = speed
        self.radius      = radius
        self.alive       = True
        length = math.hypot(dx, dy) or 1
        self.vx = dx / length * speed
        self.vy = dy / length * speed
        self.shape = shapes.Circle(int(x), int(y), radius, color=color, batch=batch)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.shape.x = int(self.x)
        self.shape.y = int(self.y)
        if self.x < -500 or self.x > 5000 or self.y < -200 or self.y > 2000:
            self.destroy()

    def hits(self, player):
        """Collision circulaire contre le joueur."""
        cx = player.x + player.width  / 2
        cy = player.y + player.height / 2
        return math.hypot(self.x - cx, self.y - cy) < self.radius + player.width / 2

    def hits_rect(self, entity):
        """Collision point-dans-rectangle contre un ennemi (pour les tirs du joueur)."""
        return (entity.x < self.x < entity.x + entity.width and
                entity.y < self.y < entity.y + entity.height)

    def destroy(self):
        self.alive = False
        self.shape.batch = None


# ── Classe de base Ennemi ─────────────────────────────────────────────────────

class Enemy:
    COLOR     = (180, 60, 60)
    WIDTH     = 36
    HEIGHT    = 48
    HP        = 50
    SPEED     = 80
    DAMAGE    = 10
    ATTACK_CD = 1.5
    IS_RANGED = False

    # Chemins des frames par défaut (à surcharger dans chaque sous-classe)
    FRAME_PATHS = [
        "assets/dragon_frame1.png",
        "assets/dragon_frame2.png",
        "assets/dragon_frame3.png",
    ]
    FRAME_DURATION = 0.2

    def __init__(self, x, y, batch):
        self.x, self.y          = float(x), float(y)
        self.width, self.height = self.WIDTH, self.HEIGHT
        self.hp                 = self.HP
        self.max_hp             = self.HP
        self.alive              = True
        self._cd                = 0.0
        self._dir               = 1
        self._patrol_origin     = float(x)
        self._patrol_range      = RANGED_RANGE_PX if self.IS_RANGED else MELEE_RANGE_PX
        self._batch             = batch

        # Corps (hitbox invisible — remplacé par le sprite animé)
        self.shape = shapes.Rectangle(
            int(x), int(y), self.WIDTH, self.HEIGHT,
            color=self.COLOR, batch=batch
        )
        self.shape.visible = False  # Le bloc coloré est caché, le sprite prend le relais

        # Barre de vie (fond rouge + barre verte)
        self._hp_bg  = shapes.Rectangle(int(x), int(y) + self.HEIGHT + 4,
                                         self.WIDTH, 5, color=(120, 30, 30), batch=batch)
        self._hp_bar = shapes.Rectangle(int(x), int(y) + self.HEIGHT + 4,
                                         self.WIDTH, 5, color=(60, 200, 60), batch=batch)

        # Animation 3 frames
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=self.FRAME_PATHS,
            frame_duration=self.FRAME_DURATION,
            batch=batch,
        )

    # ── Vie ───────────────────────────────────────────────────────────────────

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self._update_hp_bar()
        if self.hp <= 0:
            self.destroy()

    def _update_hp_bar(self):
        ratio = self.hp / self.max_hp
        self._hp_bar.width = max(0, int(self.WIDTH * ratio))

    def destroy(self):
        self.alive = False
        for s in (self.shape, self._hp_bg, self._hp_bar):
            s.batch = None
        if hasattr(self, 'animation'):
            self.animation.delete()

    # ── Synchronisation graphique ─────────────────────────────────────────────

    def _sync(self):
        ix, iy = int(self.x), int(self.y)
        self.shape.x   = ix
        self.shape.y   = iy
        self._hp_bg.x  = ix
        self._hp_bg.y  = iy + self.HEIGHT + 4
        self._hp_bar.x = ix
        self._hp_bar.y = iy + self.HEIGHT + 4
        self.animation.set_position(ix, iy)

    # ── Patrouille ────────────────────────────────────────────────────────────

    def _patrol(self, dt):
        self.x += self.SPEED * self._dir * dt
        if abs(self.x - self._patrol_origin) >= self._patrol_range:
            self._dir *= -1

    # ── Distance joueur ───────────────────────────────────────────────────────

    def _dist(self, player):
        cx_e = self.x + self.width  / 2
        cx_p = player.x + player.width / 2
        return abs(cx_e - cx_p)

    # ── Attaque (à surcharger) ────────────────────────────────────────────────

    def attack(self, player, projectiles):
        pass

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt, player, projectiles):
        if not self.alive:
            return

        self._cd = max(0.0, self._cd - dt)
        dist     = self._dist(player)
        detect   = self._patrol_range

        if dist < detect:
            if self._cd <= 0:
                self.attack(player, projectiles)
                self._cd = self.ATTACK_CD
            if not self.IS_RANGED:
                direction = 1 if player.x > self.x else -1
                self.x += self.SPEED * direction * dt
        else:
            self._patrol(dt)

        self._sync()
        self.animation.update(dt)


# ══════════════════════════════════════════════════════════════════════════════
# ── ENNEMIS RANGÉS ────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class Dragon(Enemy):
    COLOR     = (200, 60,  20)
    WIDTH     = 50
    HEIGHT    = 40
    HP        = 120
    SPEED     = 60
    DAMAGE    = 20
    ATTACK_CD = 2.0
    IS_RANGED = True
    FRAME_PATHS = [
        "assets/dragon_frame1.png",
        "assets/dragon_frame2.png",
        "assets/dragon_frame3.png",
    ]
    FRAME_DURATION = 0.2

    def attack(self, player, projectiles):
        dx = (player.x + player.width  / 2) - (self.x + self.WIDTH  / 2)
        dy = (player.y + player.height / 2) - (self.y + self.HEIGHT / 2)
        projectiles.append(Projectile(
            self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
            dx, dy,
            damage=self.DAMAGE, speed=400,
            color=(255, 120, 30), radius=10,
            batch=self._batch,
        ))


class Elfe(Enemy):
    COLOR     = (60, 180, 80)
    WIDTH     = 28
    HEIGHT    = 50
    HP        = 60
    SPEED     = 90
    DAMAGE    = 12
    ATTACK_CD = 1.2
    IS_RANGED = True
    FRAME_PATHS = [
        "assets/elfe_frame1.png",
        "assets/elfe_frame2.png",
        "assets/elfe_frame3.png",
    ]
    FRAME_DURATION = 0.18

    def attack(self, player, projectiles):
        dx = (player.x + player.width  / 2) - (self.x + self.WIDTH  / 2)
        dy = (player.y + player.height / 2) - (self.y + self.HEIGHT / 2)
        projectiles.append(Projectile(
            self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
            dx, dy,
            damage=self.DAMAGE, speed=550,
            color=(100, 255, 120), radius=6,
            batch=self._batch,
        ))


class NuageMechant(Enemy):
    COLOR     = (180, 180, 200)
    WIDTH     = 60
    HEIGHT    = 30
    HP        = 80
    SPEED     = 50
    DAMAGE    = 15
    ATTACK_CD = 1.8
    IS_RANGED = True
    FRAME_PATHS = [
        "assets/nuage_mechant_frame1.png",
        "assets/nuage_mechant_frame2.png",
        "assets/nuage_mechant_frame3.png",
    ]
    FRAME_DURATION = 0.25

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self._osc_timer = 0.0

    def update(self, dt, player, projectiles):
        if not self.alive:
            return
        self._osc_timer += dt
        self.y += math.sin(self._osc_timer * 2) * 15 * dt
        super().update(dt, player, projectiles)

    def attack(self, player, projectiles):
        tx = player.x + player.width / 2
        ty = player.y + player.height
        dx = tx - (self.x + self.WIDTH / 2)
        dy = ty - (self.y + self.HEIGHT / 2)
        projectiles.append(Projectile(
            self.x + self.WIDTH / 2, self.y,
            dx, dy,
            damage=self.DAMAGE, speed=500,
            color=(255, 255, 60), radius=7,
            batch=self._batch,
        ))


# ══════════════════════════════════════════════════════════════════════════════
# ── ENNEMIS MÊLÉE ─────────────────────────────────────────────════════════════
# ══════════════════════════════════════════════════════════════════════════════

class Aigle(Enemy):
    COLOR     = (160, 120, 40)
    WIDTH     = 34
    HEIGHT    = 30
    HP        = 40
    SPEED     = 160
    DAMAGE    = 8
    ATTACK_CD = 0.8
    IS_RANGED = False
    FRAME_PATHS = [
        "assets/aigle_frame1.png",
        "assets/aigle_frame2.png",
        "assets/aigle_frame3.png",
    ]
    FRAME_DURATION = 0.15

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


class Requin(Enemy):
    COLOR     = (60, 100, 180)
    WIDTH     = 50
    HEIGHT    = 36
    HP        = 100
    SPEED     = 70
    DAMAGE    = 25
    ATTACK_CD = 2.0
    IS_RANGED = False
    FRAME_PATHS = [
        "assets/requin_frame1.png",
        "assets/requin_frame2.png",
        "assets/requin_frame3.png",
    ]
    FRAME_DURATION = 0.18

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


class Champignon(Enemy):
    COLOR     = (140, 60, 160)
    WIDTH     = 30
    HEIGHT    = 38
    HP        = 55
    SPEED     = 55
    DAMAGE    = 10
    ATTACK_CD = 1.0
    IS_RANGED = False
    FRAME_PATHS = [
        "assets/champignon_frame1.png",
        "assets/champignon_frame2.png",
        "assets/champignon_frame3.png",
    ]
    FRAME_DURATION = 0.22

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


# ══════════════════════════════════════════════════════════════════════════════
# ── GESTIONNAIRE D'ENNEMIS ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class EnemyManager:
    def __init__(self, batch):
        self._batch      = batch
        self.enemies     = []
        self.projectiles = []

    def spawn(self, enemy_class, x, y):
        e = enemy_class(x, y, self._batch)
        self.enemies.append(e)
        return e

    def update(self, dt, player):
        for e in self.enemies:
            e.update(dt, player, self.projectiles)

        for p in self.projectiles:
            p.update(dt)
            if p.alive and p.hits(player):
                player.hp = max(0, player.hp - p.damage)
                p.destroy()

        self.enemies     = [e for e in self.enemies     if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

    def clear(self):
        for e in self.enemies:
            e.destroy()
        for p in self.projectiles:
            p.destroy()
        self.enemies.clear()
        self.projectiles.clear()