import math
import pyglet
from pyglet import shapes
from enemies import Enemy, Projectile

# ─────────────────────────────────────────────────────────────────────────────
# Gestion d’animation simple 3 frames
# ─────────────────────────────────────────────────────────────────────────────
class SimpleAnimation:
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
        self.sprite.x = x
        self.sprite.y = y

    def delete(self):
        self.sprite.delete()


# ─────────────────────────────────────────────────────────────────────────────
# Dragon — ennemi à distance (souffle de feu)
# ─────────────────────────────────────────────────────────────────────────────
class Dragon(Enemy):
    COLOR     = (200, 60, 20)
    WIDTH     = 50
    HEIGHT    = 40
    HP        = 120
    SPEED     = 60
    DAMAGE    = 20
    ATTACK_CD = 2.0
    IS_RANGED = True

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=[
                "assets/dragon_frame1.png",
                "assets/dragon_frame2.png",
                "assets/dragon_frame3.png",
            ],
            frame_duration=0.2,
            batch=batch,
        )

    def update(self, dt, player, projectiles):
        super().update(dt, player, projectiles)
        self.animation.set_position(self.x, self.y)
        self.animation.update(dt)

    def destroy(self):
        super().destroy()
        self.animation.delete()

    def attack(self, player, projectiles):
        dx = (player.x + player.width/2) - (self.x + self.WIDTH/2)
        dy = (player.y + player.height/2) - (self.y + self.HEIGHT/2)
        projectiles.append(Projectile(
            self.x + self.WIDTH/2, self.y + self.HEIGHT/2,
            dx, dy,
            damage=self.DAMAGE, speed=400,
            color=(255, 120, 30), radius=10, batch=self._batch,
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Elfe — ennemi à distance (flèche magique)
# ─────────────────────────────────────────────────────────────────────────────
class Elfe(Enemy):
    COLOR     = (60, 180, 80)
    WIDTH     = 28
    HEIGHT    = 50
    HP        = 60
    SPEED     = 90
    DAMAGE    = 12
    ATTACK_CD = 1.2
    IS_RANGED = True

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=[
                "assets/elfe_frame1.png",
                "assets/elfe_frame2.png",
                "assets/elfe_frame3.png",
            ],
            frame_duration=0.18,
            batch=batch,
        )

    def update(self, dt, player, projectiles):
        super().update(dt, player, projectiles)
        self.animation.set_position(self.x, self.y)
        self.animation.update(dt)

    def destroy(self):
        super().destroy()
        self.animation.delete()

    def attack(self, player, projectiles):
        dx = (player.x + player.width/2) - (self.x + self.WIDTH/2)
        dy = (player.y + player.height/2) - (self.y + self.HEIGHT/2)
        projectiles.append(Projectile(
            self.x + self.WIDTH/2, self.y + self.HEIGHT/2,
            dx, dy,
            damage=self.DAMAGE, speed=550,
            color=(100, 255, 120), radius=6, batch=self._batch,
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Nuage Méchant — ennemi à distance (éclairs)
# ─────────────────────────────────────────────────────────────────────────────
class NuageMechant(Enemy):
    COLOR     = (180, 180, 200)
    WIDTH     = 60
    HEIGHT    = 30
    HP        = 80
    SPEED     = 50
    DAMAGE    = 15
    ATTACK_CD = 1.8
    IS_RANGED = True

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=[
                "assets/nuage_mechant_frame1.png",
                "assets/nuage_mechant_frame2.png",
                "assets/nuage_mechant_frame3.png",
            ],

            frame_duration=0.25,
            batch=batch,
        )
        self._osc_timer = 0.0

    def update(self, dt, player, projectiles):
        if not self.alive:
            return
        self._osc_timer += dt
        self.y += math.sin(self._osc_timer * 2) * 15 * dt
        super().update(dt, player, projectiles)
        self.animation.set_position(self.x, self.y)
        self.animation.update(dt)

    def destroy(self):
        super().destroy()
        self.animation.delete()

    def attack(self, player, projectiles):
        tx = player.x + player.width/2
        ty = player.y + player.height
        dx = tx - (self.x + self.WIDTH/2)
        dy = ty - (self.y + self.HEIGHT/2)
        projectiles.append(Projectile(
            self.x + self.WIDTH/2, self.y,
            dx, dy,
            damage=self.DAMAGE, speed=500,
            color=(255, 255, 90), radius=7, batch=self._batch,
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Aigle — ennemi de mêlée rapide (griffes)
# ─────────────────────────────────────────────────────────────────────────────
class Aigle(Enemy):
    COLOR     = (160, 120, 40)
    WIDTH     = 34
    HEIGHT    = 30
    HP        = 40
    SPEED     = 160
    DAMAGE    = 8
    ATTACK_CD = 0.8
    IS_RANGED = False

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=[
                "assets/aigle_frame1.png",
                "assets/aigle_frame2.png",
                "assets/aigle_frame3.png",
            ],
            frame_duration=0.15,
            batch=batch,
        )

    def update(self, dt, player, projectiles):
        super().update(dt, player, projectiles)
        self.animation.set_position(self.x, self.y)
        self.animation.update(dt)

    def destroy(self):
        super().destroy()
        self.animation.delete()

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


# ─────────────────────────────────────────────────────────────────────────────
# Requin — ennemi de mêlée (morsure)
# ─────────────────────────────────────────────────────────────────────────────
class Requin(Enemy):
    COLOR     = (60, 100, 180)
    WIDTH     = 50
    HEIGHT    = 36
    HP        = 100
    SPEED     = 70
    DAMAGE    = 25
    ATTACK_CD = 2.0
    IS_RANGED = False

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=[
                "assets/requin_frame1.png",
                "assets/requin_frame2.png",
                "assets/requin_frame3.png",
            ],
            frame_duration=0.18,
            batch=batch,
        )

    def update(self, dt, player, projectiles):
        super().update(dt, player, projectiles)
        self.animation.set_position(self.x, self.y)
        self.animation.update(dt)

    def destroy(self):
        super().destroy()
        self.animation.delete()

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


# ─────────────────────────────────────────────────────────────────────────────
# Champignon — ennemi au sol (spores)
# ─────────────────────────────────────────────────────────────────────────────
class Champignon(Enemy):
    COLOR     = (140, 60, 160)
    WIDTH     = 30
    HEIGHT    = 38
    HP        = 55
    SPEED     = 55
    DAMAGE    = 10
    ATTACK_CD = 1.0
    IS_RANGED = False

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation = SimpleAnimation(
            x, y,
            frame_paths=[
                "assets/champignon_frame1.png",
                "assets/champignon_frame2.png",
                "assets/champignon_frame3.png",
            ],
            frame_duration=0.22,
            batch=batch,
        )

    def update(self, dt, player, projectiles):
        super().update(dt, player, projectiles)
        self.animation.set_position(self.x, self.y)
        self.animation.update(dt)

    def destroy(self):
        super().destroy()
        self.animation.delete()

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)