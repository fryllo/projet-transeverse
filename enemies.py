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

MELEE_RANGE_PX  = MELEE_RANGE_M  * PIXEL_PER_METER
RANGED_RANGE_PX = RANGED_RANGE_M * PIXEL_PER_METER

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
        # Le sprite et les barres de vie sont positionnés par camera.apply_enemies()
        # On stocke juste les coordonnées monde ici

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

class FlameParticle:
    """Petite boule de feu animée qui compose le souffle du dragon."""
    DURATION   = 0.6
    FLASH_RATE = 0.05

    def __init__(self, x, y, dx, dy, batch, speed=320):
        self.alive   = True
        self._timer  = 0.0
        self._flash  = 0.0
        self._vis    = True
        import math
        length = math.hypot(dx, dy) or 1
        self.vx = dx / length * speed
        self.vy = dy / length * speed
        self.x, self.y = float(x), float(y)
        # 3 cercles concentriques : coeur blanc, milieu orange, halo rouge
        self._c0 = shapes.Circle(int(x), int(y), 14, color=(255, 60,  10), batch=batch)
        self._c1 = shapes.Circle(int(x), int(y),  9, color=(255,160,  30), batch=batch)
        self._c2 = shapes.Circle(int(x), int(y),  4, color=(255,240, 180), batch=batch)
        self._c0.opacity = 220
        self._c1.opacity = 200
        self._c2.opacity = 255
        self._batch = batch

    def update(self, dt):
        if not self.alive:
            return
        self._timer += dt
        self._flash += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Clignotement
        if self._flash >= self.FLASH_RATE:
            self._flash = 0.0
            self._vis   = not self._vis
            a0 = 220 if self._vis else 80
            a1 = 200 if self._vis else 60
            a2 = 255 if self._vis else 120
            self._c0.opacity = a0
            self._c1.opacity = a1
            self._c2.opacity = a2
        # Rétrécissement progressif
        ratio = 1.0 - self._timer / self.DURATION
        self._c0.radius = max(1, int(14 * ratio))
        self._c1.radius = max(1, int( 9 * ratio))
        self._c2.radius = max(1, int( 4 * ratio))
        ix, iy = int(self.x), int(self.y)
        self._c0.x = ix; self._c0.y = iy
        self._c1.x = ix; self._c1.y = iy
        self._c2.x = ix; self._c2.y = iy
        if self._timer >= self.DURATION:
            self.destroy()

    def hits(self, player):
        if not self.alive:
            return False
        import math
        cx = player.x + player.width  / 2
        cy = player.y + player.height / 2
        return math.hypot(self.x - cx, self.y - cy) < 18 + player.width / 2

    def apply_camera(self, offset_x):
        sx = int(self.x - offset_x)
        self._c0.x = sx; self._c1.x = sx; self._c2.x = sx

    def destroy(self):
        self.alive = False
        for c in (self._c0, self._c1, self._c2):
            try: c.batch = None
            except: pass


class Dragon(Enemy):
    COLOR          = (200, 60, 20)
    WIDTH          = 25   # taille divisée par 2
    HEIGHT         = 20   # taille divisée par 2
    HP             = 120
    SPEED          = 60
    DAMAGE         = 1    # 1 PV par flamme
    ATTACK_CD      = 3.0
    IS_RANGED      = True
    FRAME_PATHS = [
        "assets/dragon_frame1.png",
        "assets/dragon_frame2.png",
        "assets/dragon_frame3.png",
    ]
    FRAME_DURATION = 1.0   # 1 seconde par frame

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation.sprite.scale = 0.5
        self._flames  = []
        self._facing  = 1   # 1=droite, -1=gauche
        # Patrouille bornée à 1500px
        self._patrol_range = 1500

    def update(self, dt, player, projectiles):
        if not self.alive:
            return

        self._cd = max(0.0, self._cd - dt)

        # Patrouille gauche-droite sur 1500px
        self._patrol(dt)

        # Direction vers le joueur pour le sprite et la bouche
        self._facing = 1 if player.x >= self.x else -1
        self.animation.sprite.scale_x = 0.5 * self._facing

        # Avancer la frame (1s par frame)
        self.animation.update(dt)
        current_frame = self.animation.frame_index

        # Attaque sur la frame 3 (index 2)
        if current_frame == 2 and self._cd <= 0:
            self._fire(player)
            self._cd = self.ATTACK_CD

        # Mettre à jour les flammes
        for f in self._flames:
            f.update(dt)
            if f.alive and f.hits(player):
                pass  # dégâts gérés centralement
        self._flames = [f for f in self._flames if f.alive]

        self._sync()

    def _fire(self, player):
        """Lance une rafale de 5 boules de feu depuis la bouche du dragon."""
        import math
        # Bouche à droite si facing=1, à gauche si facing=-1
        if self._facing == 1:
            cx = self.x + self.WIDTH
        else:
            cx = self.x
        cy = self.y + int(self.HEIGHT * 0.80)
        dx = (player.x + player.width  / 2) - cx
        dy = (player.y + player.height / 2) - cy
        for i in range(5):
            angle_offset = (i - 2) * 0.15
            rdx = dx * math.cos(angle_offset) - dy * math.sin(angle_offset)
            rdy = dx * math.sin(angle_offset) + dy * math.cos(angle_offset)
            self._flames.append(FlameParticle(cx, cy, rdx, rdy, self._batch, speed=960))

    def destroy(self):
        for f in self._flames:
            f.destroy()
        self._flames.clear()
        super().destroy()

    def attack(self, player, projectiles):
        pass  # géré dans update()


class EnergyOrb:
    """Boule d'énergie verte lumineuse tirée par l'elfe."""
    DURATION = 2.5

    def __init__(self, x, y, dx, dy, batch):
        self.x, self.y = float(x), float(y)
        self.alive     = True
        self._timer    = 0.0
        self._flash    = 0.0
        self._vis      = True
        speed  = 280
        length = math.hypot(dx, dy) or 1
        self.vx = dx / length * speed
        self.vy = dy / length * speed
        # Halo extérieur + coeur
        self._outer = shapes.Circle(int(x), int(y), 10, color=(60, 220, 80),  batch=batch)
        self._inner = shapes.Circle(int(x), int(y),  5, color=(200, 255, 180), batch=batch)
        self._outer.opacity = 180
        self._inner.opacity = 255

    def update(self, dt):
        if not self.alive:
            return
        self._timer += dt
        self._flash += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Clignotement léger
        if self._flash >= 0.08:
            self._flash = 0.0
            self._vis   = not self._vis
            self._outer.opacity = 180 if self._vis else 80
            self._inner.opacity = 255 if self._vis else 150
        ix, iy = int(self.x), int(self.y)
        self._outer.x = ix; self._outer.y = iy
        self._inner.x = ix; self._inner.y = iy
        if self._timer >= self.DURATION:
            self.destroy()

    def apply_camera(self, offset_x):
        sx = int(self.x - offset_x)
        self._outer.x = sx
        self._inner.x = sx

    def destroy(self):
        self.alive = False
        for c in (self._outer, self._inner):
            try: c.batch = None
            except: pass


class Elfe(Enemy):
    COLOR          = (60, 180, 80)
    WIDTH          = 28
    HEIGHT         = 50
    HP             = 60
    SPEED          = 0       # statique
    DAMAGE         = 1
    ATTACK_CD      = 0.5    # tir toutes les 0.5s
    IS_RANGED      = True
    FRAME_PATHS = [
        "assets/elfe_frame1.png",
        "assets/elfe_frame2.png",
        "assets/elfe_frame3.png",
    ]
    FRAME_DURATION = 0.3

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation.sprite.scale = 1 / 2.5
        self._orbs       = []
        self._angle      = 0.0   # angle courant de tir (radians, sens horaire)

    def update(self, dt, player, projectiles):
        if not self.alive:
            return

        self._cd = max(0.0, self._cd - dt)

        # Tourelle statique — pas de déplacement

        # Orienter le sprite vers le joueur
        facing = 1 if player.x >= self.x else -1
        self.animation.sprite.scale_x = (1 / 2.5) * facing
        self.animation.update(dt)

        # Tir en rotation dans le sens des aiguilles d'une montre
        if self._cd <= 0:
            self._shoot_orb()
            # Avancer l'angle dans le sens horaire (angle négatif en coordonnées pyglet)
            self._angle -= math.pi / 4   # 8 directions, 45° par tir
            self._cd = self.ATTACK_CD

        # Mettre à jour les orbes
        for orb in self._orbs:
            orb.update(dt)
        self._orbs = [o for o in self._orbs if o.alive]

        self._sync()

    def _shoot_orb(self):
        cx = self.x + self.WIDTH  / 2
        cy = self.y + self.HEIGHT / 2
        dx = math.cos(self._angle)
        dy = math.sin(self._angle)
        self._orbs.append(EnergyOrb(cx, cy, dx, dy, self._batch))

    def attack(self, player, projectiles):
        pass  # géré dans update()

    def destroy(self):
        for o in self._orbs:
            o.destroy()
        self._orbs.clear()
        super().destroy()


class LightningBolt:
    """
    Eclair qui tombe depuis le nuage jusqu'au sol ou à la première plateforme.
    Animé comme un halo de foudre (segments qui clignotent).
    """
    DURATION   = 0.5    # secondes d'affichage total
    FLASH_RATE = 0.06   # secondes entre chaque clignotement

    def __init__(self, cx, y_top, y_bottom, damage, batch, world_entities):
        self.cx       = cx          # centre x de l'éclair
        self.y_top    = y_top       # y de départ (sous le nuage)
        self.y_bottom = y_bottom    # y d'arrivée (sol ou plateforme)
        self.damage   = damage
        self.alive    = True
        self._timer   = 0.0
        self._flash   = 0.0
        self._visible = True
        self._batch   = batch

        # Trouver la vraie y_bottom : première plateforme sous le nuage
        bolt_h = y_top - y_bottom
        self._shapes = self._build(batch)

    def _build(self, batch):
        shapes_list = []
        width  = 16
        bolt_h = int(self.y_top - self.y_bottom)
        # Halo extérieur très large et lumineux
        r_outer = shapes.Rectangle(
            int(self.cx - 40), int(self.y_bottom),
            80, bolt_h,
            color=(255, 255, 100), batch=batch,
        )
        r_outer.opacity = 120
        shapes_list.append(r_outer)
        # Corps principal : rectangle jaune-vert vif
        r = shapes.Rectangle(
            int(self.cx - width//2), int(self.y_bottom),
            width, bolt_h,
            color=(200, 255, 80), batch=batch,
        )
        r.opacity = 230
        shapes_list.append(r)
        # Coeur blanc brillant
        r_core = shapes.Rectangle(
            int(self.cx - 4), int(self.y_bottom),
            8, bolt_h,
            color=(255, 255, 255), batch=batch,
        )
        r_core.opacity = 200
        shapes_list.append(r_core)
        # Cercle d'impact en bas
        c = shapes.Circle(int(self.cx), int(self.y_bottom), 28,
                          color=(255, 255, 150), batch=batch)
        c.opacity = 220
        shapes_list.append(c)
        # Cercle d'impact intérieur blanc
        c2 = shapes.Circle(int(self.cx), int(self.y_bottom), 14,
                           color=(255, 255, 255), batch=batch)
        c2.opacity = 255
        shapes_list.append(c2)
        return shapes_list

    def update(self, dt):
        if not self.alive:
            return
        self._timer += dt
        self._flash += dt
        if self._flash >= self.FLASH_RATE:
            self._flash = 0.0
            self._visible = not self._visible
            if self._shapes:
                self._shapes[0].opacity = 120 if self._visible else 40   # halo outer
                self._shapes[1].opacity = 230 if self._visible else 100  # corps
                self._shapes[2].opacity = 200 if self._visible else 60   # coeur
                self._shapes[3].opacity = 220 if self._visible else 80   # impact
                self._shapes[4].opacity = 255 if self._visible else 120  # impact core
        if self._timer >= self.DURATION:
            self.destroy()

    def hits(self, player):
        """Retourne True si le joueur est dans la zone de l'éclair."""
        if not self.alive:
            return False
        pcx = player.x + player.width / 2
        return (abs(pcx - self.cx) < 28 and
                self.y_bottom <= player.y + player.height and
                player.y <= self.y_top)

    def apply_camera(self, offset_x):
        sx = int(self.cx - offset_x)
        if self._shapes:
            w0 = self._shapes[0].width
            self._shapes[0].x = sx - w0//2
            self._shapes[1].x = sx - 20
            self._shapes[2].x = sx

    def destroy(self):
        self.alive = False
        for s in self._shapes:
            try: s.batch = None
            except: pass
        self._shapes.clear()


class NuageMechant(Enemy):
    COLOR          = (180, 180, 200)
    WIDTH          = 60
    HEIGHT         = 30
    HP             = 80
    SPEED          = 55
    DAMAGE         = 1       # 1 PV par attaque
    ATTACK_CD      = 3.0     # cooldown après une attaque
    DETECT_DELAY   = 0.3     # délai avant frappe quand joueur en dessous
    DIR_MIN        = 3.0     # changement de direction min (secondes)
    DIR_MAX        = 5.0     # changement de direction max (secondes)
    IS_RANGED      = True
    FRAME_PATHS = [
        "assets/nuage_mechant_frame1.png",
        "assets/nuage_mechant_frame2.png",
        "assets/nuage_mechant_frame3.png",
    ]
    FRAME_DURATION = 0.25

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        import random
        self._dir_timer   = random.uniform(self.DIR_MIN, self.DIR_MAX)
        self._detect_cd   = 0.0   # compte à rebours avant frappe
        self._detecting   = False  # joueur actuellement en dessous ?
        self._lightning   = []     # éclairs actifs
        self._world       = None   # injecté par EnemyManager

    def _player_below(self, player):
        """Retourne True si le joueur est dans la colonne verticale du nuage."""
        pcx = player.x + player.width / 2
        return (self.x - 20 <= pcx <= self.x + self.WIDTH + 20 and
                player.y < self.y)

    def _find_bolt_bottom(self, player):
        """
        Cherche la première plateforme entre le nuage et le joueur.
        Si une plateforme bloque, l'éclair s'arrête dessus.
        Sinon, va jusqu'au sol (y=40).
        """
        cx = self.x + self.WIDTH / 2
        y_start = self.y
        y_end   = 40  # sol par défaut

        if self._world is None:
            return y_end

        from moteur import Platform
        for entity in self._world:
            if not isinstance(entity, Platform):
                continue
            # La plateforme est-elle dans la colonne de l'éclair ?
            if not (entity.x < cx < entity.x + entity.width):
                continue
            # Est-elle entre le nuage et le joueur (en dessous du nuage) ?
            plat_top = entity.y + entity.height
            if entity.y < y_start and plat_top > y_end:
                # Arrêter l'éclair au sommet de cette plateforme
                y_end = plat_top

        return y_end

    def update(self, dt, player, projectiles):
        if not self.alive:
            return

        # Déplacement gauche-droite avec changement de direction aléatoire
        import random
        self._dir_timer -= dt
        if self._dir_timer <= 0:
            self._dir *= -1
            self._dir_timer = random.uniform(self.DIR_MIN, self.DIR_MAX)

        self.x += self.SPEED * self._dir * dt
        self._cd = max(0.0, self._cd - dt)

        # Mise à jour des éclairs actifs
        for bolt in self._lightning:
            bolt.update(dt)
            if bolt.alive and bolt.hits(player):
                pass  # dégâts gérés centralement  # un seul impact par éclair
        self._lightning = [b for b in self._lightning if b.alive]

        # Détection joueur en dessous
        below = self._player_below(player)
        if below and self._cd <= 0:
            if not self._detecting:
                self._detecting  = True
                self._detect_cd  = self.DETECT_DELAY
            else:
                self._detect_cd -= dt
                if self._detect_cd <= 0:
                    self._fire_lightning(player, projectiles)
                    self._cd       = self.ATTACK_CD
                    self._detecting = False
        else:
            if not below:
                self._detecting = False

        # Contact direct : 1 PV
        if self._touches(player) and self._cd <= 0:
            pass  # dégâts gérés centralement
            self._cd  = self.ATTACK_CD

        self._sync()
        # Frame 3 quand le joueur est dans la colonne du nuage (même condition que l'attaque)
        if self._player_below(player):
            self.animation.sprite.image = self.animation.frames[2]
        else:
            self.animation.frame_index = 0
            self.animation.update(dt)

    def _fire_lightning(self, player, projectiles):
        y_bottom = self._find_bolt_bottom(player)
        bolt = LightningBolt(
            cx         = self.x + self.WIDTH / 2,
            y_top      = self.y,
            y_bottom   = y_bottom,
            damage     = self.DAMAGE,
            batch      = self._batch,
            world_entities = self._world,
        )
        self._lightning.append(bolt)

    def _touches(self, player):
        return (self.x < player.x + player.width and
                self.x + self.WIDTH > player.x and
                self.y < player.y + player.height and
                self.y + self.HEIGHT > player.y)

    def attack(self, player, projectiles):
        pass  # tout géré dans update()

    def destroy(self):
        for bolt in self._lightning:
            bolt.destroy()
        self._lightning.clear()
        super().destroy()


# ══════════════════════════════════════════════════════════════════════════════
# ── ENNEMIS MÊLÉE ─────────────────────────────────────────────════════════════
# ══════════════════════════════════════════════════════════════════════════════

class Feather:
    """Plume animée tirée par l'aigle vers le joueur."""
    DURATION = 1.2

    def __init__(self, x, y, dx, dy, damage, batch):
        self.x, self.y = float(x), float(y)
        self.damage    = damage
        self.alive     = True
        self._timer    = 0.0
        self._angle    = 0.0
        speed = 380
        length = math.hypot(dx, dy) or 1
        self.vx = dx / length * speed
        self.vy = dy / length * speed

        # Plume = rectangle fin orienté dans la direction du tir
        self._body = shapes.Rectangle(
            int(x), int(y), 18, 4,
            color=(160, 120, 40), batch=batch
        )
        self._tip = shapes.Rectangle(
            int(x), int(y), 6, 4,
            color=(220, 190, 100), batch=batch
        )
        self._body.opacity = 230
        self._tip.opacity  = 255

    def update(self, dt):
        if not self.alive:
            return
        self._timer += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Rotation simulée : oscille l'opacité pour effet de vrille
        self._angle += dt * 12
        osc = int(abs(math.sin(self._angle)) * 180) + 60
        self._body.opacity = osc
        self._tip.opacity  = min(255, osc + 60)
        ix, iy = int(self.x), int(self.y)
        self._body.x = ix
        self._body.y = iy
        self._tip.x  = ix + 12
        self._tip.y  = iy
        if self._timer >= self.DURATION:
            self.destroy()

    def hits(self, player):
        if not self.alive:
            return False
        return (player.x < self.x + 18 and player.x + player.width > self.x and
                player.y < self.y + 4  and player.y + player.height > self.y)

    def apply_camera(self, offset_x):
        sx = int(self.x - offset_x)
        self._body.x = sx
        self._tip.x  = sx + 12

    def destroy(self):
        self.alive = False
        for s in (self._body, self._tip):
            try: s.batch = None
            except: pass


class Aigle(Enemy):
    COLOR          = (160, 120, 40)
    WIDTH          = 34
    HEIGHT         = 30
    HP             = 40
    SPEED          = 80
    DAMAGE         = 1
    ATTACK_CD      = 3.0
    IS_RANGED      = True
    FRAME_PATHS = [
        "assets/aigle_frame1.png",
        "assets/aigle_frame2.png",
        "assets/aigle_frame3.png",
    ]
    FRAME_DURATION = 0.2

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        self.animation.sprite.scale = 1/3
        self._feathers = []
        self._facing   = 1

    def update(self, dt, player, projectiles):
        if not self.alive:
            return

        self._cd = max(0.0, self._cd - dt)

        # Patrouille normale
        self._patrol(dt)

        # Direction vers le joueur
        self._facing = 1 if player.x >= self.x else -1
        self.animation.sprite.scale_x = (1/3) * self._facing

        # Animation
        self.animation.update(dt)

        # Attaque toutes les 3s
        if self._cd <= 0:
            self._shoot_feathers(player)
            self._cd = self.ATTACK_CD

        # Mettre à jour les plumes
        for f in self._feathers:
            f.update(dt)
            if f.alive and f.hits(player):
                pass  # dégâts gérés centralement
        self._feathers = [f for f in self._feathers if f.alive]

        self._sync()

    def _shoot_feathers(self, player):
        """Tire 3 plumes en éventail vers le joueur."""
        if self._facing == 1:
            cx = self.x + self.WIDTH
        else:
            cx = self.x
        cy = self.y + self.HEIGHT * 0.6
        dx = (player.x + player.width  / 2) - cx
        dy = (player.y + player.height / 2) - cy
        for i in range(3):
            angle_offset = (i - 1) * 0.2
            rdx = dx * math.cos(angle_offset) - dy * math.sin(angle_offset)
            rdy = dx * math.sin(angle_offset) + dy * math.cos(angle_offset)
            self._feathers.append(Feather(cx, cy, rdx, rdy, self.DAMAGE, self._batch))

    def attack(self, player, projectiles):
        pass  # géré dans update()

    def destroy(self):
        for f in self._feathers:
            f.destroy()
        self._feathers.clear()
        super().destroy()


class Requin(Enemy):
    COLOR          = (60, 100, 180)
    WIDTH          = 50
    HEIGHT         = 36
    HP             = 100
    SPEED          = 70
    SPEED_CHASE    = 220    # vitesse quand il fonce sur le joueur
    DAMAGE         = 1      # 1 PV par morsure
    ATTACK_CD      = 2.5
    CHASE_DIST     = 180    # distance de détection (~ une plateforme)
    DIR_MIN        = 7.0    # changement de direction min (secondes)
    DIR_MAX        = 10.0   # changement de direction max (secondes)
    FLEE_DURATION  = 3.0    # durée de fuite après morsure
    IS_RANGED      = False
    FRAME_PATHS = [
        "assets/requin_frame1.png",
        "assets/requin_frame2.png",
        "assets/requin_frame3.png",
    ]
    FRAME_DURATION = 0.18

    # Frame 4 (crocs) chargée séparément
    BITE_FRAME_PATH = "assets/requin_frame4.png"

    def __init__(self, x, y, batch):
        super().__init__(x, y, batch)
        import random
        self._dir_timer  = random.uniform(self.DIR_MIN, self.DIR_MAX)
        self._state      = "patrol"
        self._flee_timer = 0.0
        self._bite_timer = 0.0
        self._flee_dir   = 1
        try:
            self._bite_frame = pyglet.image.load(self.BITE_FRAME_PATH)
        except:
            self._bite_frame = None

    def _facing(self):
        return self._dir

    def _set_frame(self, index, facing):
        """Frame 3 si va à gauche, frames 1-2 si va à droite."""
        frames = self.animation.frames
        if facing == -1:
            # Toujours frame 3 quand va à gauche
            self.animation.sprite.image = frames[2]
        else:
            # Frames 1-2 alternées quand va à droite
            frame_idx = index % 2  # alterne entre 0 et 1
            self.animation.sprite.image = frames[frame_idx]
        self.animation.sprite.scale_x = abs(self.animation.sprite.scale_x) * facing

    def _dist_to_player(self, player):
        cx_s = self.x + self.WIDTH / 2
        cx_p = player.x + player.width / 2
        return abs(cx_s - cx_p)

    def _touches(self, player):
        return (self.x < player.x + player.width and
                self.x + self.WIDTH > player.x and
                self.y < player.y + player.height and
                self.y + self.HEIGHT > player.y)

    def update(self, dt, player, projectiles):
        if not self.alive:
            return
        import random

        self._cd = max(0.0, self._cd - dt)
        dist = self._dist_to_player(player)
        facing = self._facing()

        # ── Machine à états ───────────────────────────────────────────────────
        if self._state == "bite":
            # Immobile pendant la frame crocs (0.4s)
            self._bite_timer -= dt
            if self._bite_timer <= 0:
                self._state = "flee"
                self._flee_timer = self.FLEE_DURATION
                self._flee_dir = -1 if player.x > self.x else 1

        elif self._state == "flee":
            # Fuite dans la direction opposée au joueur
            self._flee_timer -= dt
            self.x += self.SPEED_CHASE * self._flee_dir * dt
            facing = self._flee_dir
            if self._flee_timer <= 0:
                self._state = "patrol"
                self._dir_timer = random.uniform(self.DIR_MIN, self.DIR_MAX)

        elif self._state == "chase":
            # Fonce vers le joueur
            chase_dir = 1 if player.x > self.x else -1
            self.x += self.SPEED_CHASE * chase_dir * dt
            facing = chase_dir
            # Morsure si contact et joueur pas en hitstun
            if self._touches(player) and player.hitstun <= 0:
                self._cd = self.ATTACK_CD
                self._state = "bite"
                self._bite_timer = 0.4
            # Repassage en patrol si trop loin
            elif dist > self.CHASE_DIST * 1.5:
                self._state = "patrol"

        else:  # patrol
            # Patrouille normale
            self._dir_timer -= dt
            if self._dir_timer <= 0:
                self._dir *= -1
                self._dir_timer = random.uniform(self.DIR_MIN, self.DIR_MAX)
            self.x += self.SPEED * self._dir * dt
            facing = self._dir
            # Passer en chase si le joueur est proche
            if dist < self.CHASE_DIST:
                self._state = "chase"
            # Morsure si contact même en patrol
            if self._touches(player) and player.hitstun <= 0:
                self._cd = self.ATTACK_CD
                self._state = "bite"
                self._bite_timer = 0.4

        # ── Visuel ────────────────────────────────────────────────────────────
        self._sync()

        if self._state == "bite" and self._bite_frame:
            self.animation.sprite.image = self._bite_frame
            self.animation.sprite.scale_x = abs(self.animation.sprite.scale_x) * facing
        else:
            # Animation normale avec direction
            self.animation.update(dt)
            idx = self.animation.frame_index
            self._set_frame(idx, facing)

    def attack(self, player, projectiles):
        pass  # tout géré dans update()


class Champignon(Enemy):
    COLOR          = (140, 60, 160)
    WIDTH          = 15
    HEIGHT         = 19
    HP             = 55
    SPEED          = 55
    DAMAGE         = 10
    ATTACK_CD      = 0.8
    IS_RANGED      = False
    FRAME_PATHS = [
        "assets/champignon_frame1.png",
        "assets/champignon_frame2.png",
        "assets/champignon_frame3.png",
    ]
    FRAME_DURATION = 0.22

    def __init__(self, x, y, batch, x_min=None, x_max=None):
        super().__init__(x, y, batch)
        self._hp_bg.width  = self.WIDTH
        self._hp_bar.width = self.WIDTH
        self.animation.sprite.scale = 0.5
        # Bornes de patrouille : si non fournies, 120px autour du spawn
        self._x_min = float(x_min) if x_min is not None else float(x) - 120
        self._x_max = float(x_max) if x_max is not None else float(x) + 120

    def update(self, dt, player, projectiles):
        if not self.alive:
            return
        # Déplacement gauche-droite
        self.x += self.SPEED * self._dir * dt
        # Demi-tour exact au bord de la plateforme
        if self.x <= self._x_min:
            self.x   = self._x_min
            self._dir = 1
        elif self.x + self.WIDTH >= self._x_max:
            self.x   = self._x_max - self.WIDTH
            self._dir = -1
        # Dégâts au contact joueur
        self._cd = max(0.0, self._cd - dt)
        if self._touches(player) and self._cd <= 0:
            pass  # dégâts gérés centralement
            self._cd  = self.ATTACK_CD
        self._sync()
        self.animation.update(dt)

    def _touches(self, player):
        return (self.x < player.x + player.width  and
                self.x + self.WIDTH  > player.x   and
                self.y < player.y + player.height  and
                self.y + self.HEIGHT > player.y)

    def attack(self, player, projectiles):
        pass  # pas de projectiles, tout est dans update()


# ══════════════════════════════════════════════════════════════════════════════
# ── GESTIONNAIRE D'ENNEMIS ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class EnemyManager:
    def __init__(self, batch):
        self._batch      = batch
        self.enemies     = []
        self.projectiles = []
        self._world      = None

    def spawn(self, enemy_class, x, y, **kwargs):
        e = enemy_class(x, y, self._batch, **kwargs)
        self.enemies.append(e)
        return e

    def set_world(self, world_entities):
        """Injecte la liste des entités du monde (pour la détection de plateformes)."""
        self._world = world_entities
        for e in self.enemies:
            if hasattr(e, '_world'):
                e._world = world_entities

    def update(self, dt, player):
        for e in self.enemies:
            # Injecter le monde aux NuageMechant si pas encore fait
            if hasattr(e, '_world') and e._world is None and hasattr(self, '_world'):
                e._world = self._world
            e.update(dt, player, self.projectiles)

        for p in self.projectiles:
            p.update(dt)
            # dégâts gérés par moteur._check_damage
            if p.alive and p.hits(player):
                pass

        self.enemies     = [e for e in self.enemies     if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

    def clear(self):
        for e in self.enemies:
            e.destroy()
        for p in self.projectiles:
            p.destroy()
        self.enemies.clear()
        self.projectiles.clear()