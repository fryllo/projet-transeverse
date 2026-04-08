# enemies.py
# Système d'ennemis : mêlée et rangé
#
# Usage dans moteur.py :
#   from enemies import Dragon, Elfe, NuageMechant, Aigle, Requin, Champignon
#   self.enemy_manager = EnemyManager(self.batch, self.world)
#   self.enemy_manager.spawn(Dragon, x=500, y=40)
#   # Dans update() :
#   self.enemy_manager.update(dt, self.player)

import pyglet
from pyglet import shapes
import math

# ── Constantes ────────────────────────────────────────────────────────────────

PIXEL_PER_METER = 40   # 1 mètre = 40 pixels

MELEE_RANGE_M  = 10    # mètres
RANGED_RANGE_M = 20    # mètres

MELEE_RANGE_PX  = MELEE_RANGE_M  * PIXEL_PER_METER   # 400 px
RANGED_RANGE_PX = RANGED_RANGE_M * PIXEL_PER_METER   # 800 px

ATTACK_COOLDOWN = 1.5   # secondes entre chaque attaque


# ── Projectile ────────────────────────────────────────────────────────────────

class Projectile:
    """
    Projectile tiré par un ennemi rangé.
    color   : couleur du projectile
    damage  : dégâts infligés au joueur
    speed   : vitesse en px/s
    radius  : rayon visuel
    """

    def __init__(self, x, y, dx, dy, damage, speed, color, radius, batch):
        self.x, self.y   = float(x), float(y)
        self.damage      = damage
        self.speed       = speed
        self.radius      = radius
        self.alive       = True
        # Normaliser la direction
        length = math.hypot(dx, dy) or 1
        self.vx = dx / length * speed
        self.vy = dy / length * speed
        self.shape = shapes.Circle(int(x), int(y), radius, color=color, batch=batch)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.shape.x = int(self.x)
        self.shape.y = int(self.y)
        # Supprimer si hors écran (large marge)
        if self.x < -500 or self.x > 5000 or self.y < -200 or self.y > 2000:
            self.destroy()

    def hits(self, player):
        """Retourne True si le projectile touche le joueur."""
        cx = player.x + player.width  / 2
        cy = player.y + player.height / 2
        return math.hypot(self.x - cx, self.y - cy) < self.radius + player.width / 2

    def destroy(self):
        self.alive = False
        self.shape.batch = None


# ── Classe de base Ennemi ─────────────────────────────────────────────────────

class Enemy:
    """
    Classe de base pour tous les ennemis.

    Attributs à surcharger dans les sous-classes :
        COLOR       : couleur (R, G, B)
        WIDTH       : largeur en px
        HEIGHT      : hauteur en px
        HP          : points de vie
        SPEED       : vitesse de déplacement px/s
        DAMAGE      : dégâts par attaque
        ATTACK_CD   : cooldown d'attaque en secondes
        IS_RANGED   : True = rangé, False = mêlée
    """

    COLOR     = (180, 60, 60)
    WIDTH     = 36
    HEIGHT    = 48
    HP        = 50
    SPEED     = 80
    DAMAGE    = 10
    ATTACK_CD = 1.5
    IS_RANGED = False

    def __init__(self, x, y, batch):
        self.x, self.y          = float(x), float(y)
        self.width, self.height = self.WIDTH, self.HEIGHT
        self.hp                 = self.HP
        self.max_hp             = self.HP
        self.alive              = True
        self._cd                = 0.0
        self._dir               = 1       # direction de patrouille
        self._patrol_origin     = float(x)
        self._patrol_range      = RANGED_RANGE_PX if self.IS_RANGED else MELEE_RANGE_PX
        self._batch             = batch

        # Corps
        self.shape = shapes.Rectangle(
            int(x), int(y), self.WIDTH, self.HEIGHT,
            color=self.COLOR, batch=batch
        )
        # Barre de vie (fond rouge + barre verte)
        self._hp_bg  = shapes.Rectangle(int(x), int(y) + self.HEIGHT + 4,
                                         self.WIDTH, 5, color=(120, 30, 30), batch=batch)
        self._hp_bar = shapes.Rectangle(int(x), int(y) + self.HEIGHT + 4,
                                         self.WIDTH, 5, color=(60, 200, 60), batch=batch)

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

    # ── Synchronisation graphique ─────────────────────────────────────────────

    def _sync(self):
        ix, iy = int(self.x), int(self.y)
        self.shape.x   = ix
        self.shape.y   = iy
        self._hp_bg.x  = ix
        self._hp_bg.y  = iy + self.HEIGHT + 4
        self._hp_bar.x = ix
        self._hp_bar.y = iy + self.HEIGHT + 4

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
        """Appelé quand l'ennemi peut attaquer. Surcharger dans les sous-classes."""
        pass

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt, player, projectiles):
        if not self.alive:
            return

        self._cd = max(0.0, self._cd - dt)
        dist     = self._dist(player)
        detect   = self._patrol_range

        if dist < detect:
            # En portée : attaque si cooldown prêt
            if self._cd <= 0:
                self.attack(player, projectiles)
                self._cd = self.ATTACK_CD
            # Mêlée : se rapproche du joueur
            if not self.IS_RANGED:
                direction = 1 if player.x > self.x else -1
                self.x += self.SPEED * direction * dt
        else:
            self._patrol(dt)

        self._sync()


# ══════════════════════════════════════════════════════════════════════════════
# ── ENNEMIS RANGÉS ────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class Dragon(Enemy):
    """
    Rangé — souffle de feu.
    Tire une boule de feu orange rapide.
    """
    COLOR     = (200, 60,  20)
    WIDTH     = 50
    HEIGHT    = 40
    HP        = 120
    SPEED     = 60
    DAMAGE    = 20
    ATTACK_CD = 2.0
    IS_RANGED = True

    def attack(self, player, projectiles):
        dx = (player.x + player.width  / 2) - (self.x + self.WIDTH  / 2)
        dy = (player.y + player.height / 2) - (self.y + self.HEIGHT / 2)
        projectiles.append(Projectile(
            self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
            dx, dy,
            damage=self.DAMAGE,
            speed=400,
            color=(255, 120, 30),
            radius=10,
            batch=self._batch,
        ))


class Elfe(Enemy):
    """
    Rangé — flèche magique.
    Tire une flèche verte précise et rapide.
    """
    COLOR     = (60, 180, 80)
    WIDTH     = 28
    HEIGHT    = 50
    HP        = 60
    SPEED     = 90
    DAMAGE    = 12
    ATTACK_CD = 1.2
    IS_RANGED = True

    def attack(self, player, projectiles):
        dx = (player.x + player.width  / 2) - (self.x + self.WIDTH  / 2)
        dy = (player.y + player.height / 2) - (self.y + self.HEIGHT / 2)
        projectiles.append(Projectile(
            self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
            dx, dy,
            damage=self.DAMAGE,
            speed=550,
            color=(100, 255, 120),
            radius=6,
            batch=self._batch,
        ))


class NuageMechant(Enemy):
    """
    Rangé — éclair.
    Tire un éclair jaune vers le bas (tombe sur le joueur).
    """
    COLOR     = (180, 180, 200)
    WIDTH     = 60
    HEIGHT    = 30
    HP        = 80
    SPEED     = 50
    DAMAGE    = 15
    ATTACK_CD = 1.8
    IS_RANGED = True

    def attack(self, player, projectiles):
        # L'éclair tombe verticalement depuis le nuage vers le joueur
        tx = player.x + player.width / 2
        ty = player.y + player.height
        dx = tx - (self.x + self.WIDTH / 2)
        dy = ty - (self.y + self.HEIGHT / 2)
        projectiles.append(Projectile(
            self.x + self.WIDTH / 2, self.y,
            dx, dy,
            damage=self.DAMAGE,
            speed=500,
            color=(255, 255, 60),
            radius=7,
            batch=self._batch,
        ))


# ══════════════════════════════════════════════════════════════════════════════
# ── ENNEMIS MÊLÉE ─────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class Aigle(Enemy):
    """
    Mêlée — coup de griffe.
    Rapide et agile, fait peu de dégâts mais attaque vite.
    """
    COLOR     = (160, 120, 40)
    WIDTH     = 34
    HEIGHT    = 30
    HP        = 40
    SPEED     = 160
    DAMAGE    = 8
    ATTACK_CD = 0.8
    IS_RANGED = False

    def attack(self, player, projectiles):
        # Griffe : dégâts directs si très proche
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


class Requin(Enemy):
    """
    Mêlée — morsure.
    Lent mais très puissant, gros dégâts.
    """
    COLOR     = (60, 100, 180)
    WIDTH     = 50
    HEIGHT    = 36
    HP        = 100
    SPEED     = 70
    DAMAGE    = 25
    ATTACK_CD = 2.0
    IS_RANGED = False

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


class Champignon(Enemy):
    """
    Mêlée — spores empoisonnées (corps à corps).
    Inflige des dégâts modérés rapidement.
    """
    COLOR     = (140, 60, 160)
    WIDTH     = 30
    HEIGHT    = 38
    HP        = 55
    SPEED     = 55
    DAMAGE    = 10
    ATTACK_CD = 1.0
    IS_RANGED = False

    def attack(self, player, projectiles):
        if abs(self.x - player.x) < self.WIDTH + player.width:
            player.hp = max(0, player.hp - self.DAMAGE)


# ══════════════════════════════════════════════════════════════════════════════
# ── GESTIONNAIRE D'ENNEMIS ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class EnemyManager:
    """
    Gère tous les ennemis et projectiles en jeu.

    Usage :
        manager = EnemyManager(batch)
        manager.spawn(Dragon, x=600, y=40)
        manager.spawn(Requin, x=1200, y=40)

        # Chaque frame :
        manager.update(dt, player)
    """

    def __init__(self, batch):
        self._batch      = batch
        self.enemies     = []
        self.projectiles = []

    def spawn(self, enemy_class, x, y):
        e = enemy_class(x, y, self._batch)
        self.enemies.append(e)
        return e

    def update(self, dt, player):
        # Mettre à jour les ennemis
        for e in self.enemies:
            e.update(dt, player, self.projectiles)

        # Mettre à jour les projectiles
        for p in self.projectiles:
            p.update(dt)
            if p.alive and p.hits(player):
                player.hp = max(0, player.hp - p.damage)
                p.destroy()

        # Nettoyer les morts
        self.enemies     = [e for e in self.enemies     if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

    def clear(self):
        for e in self.enemies:
            e.destroy()
        for p in self.projectiles:
            p.destroy()
        self.enemies.clear()
        self.projectiles.clear()

