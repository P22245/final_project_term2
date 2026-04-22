import pygame
import math
import random


class _Dot:
    __slots__ = ("x", "y", "vx", "vy", "r", "color", "lifetime", "max_life", "alive", "shrink", "gravity")

    def __init__(self, x, y, vx, vy, color, radius=4, lifetime=600, shrink=True, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.r = radius
        self.color = color
        self.lifetime = lifetime
        self.max_life = lifetime
        self.alive = True
        self.shrink = shrink
        self.gravity = gravity

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.97
        self.vy *= 0.97
        self.lifetime -= int(dt * 1000)
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        ratio = max(0.0, self.lifetime / self.max_life)
        alpha = int(255 * ratio)
        r = max(1, int(self.r * ratio)) if self.shrink else max(1, int(self.r))
        ps = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*self.color[:3], alpha), (r + 1, r + 1), r)
        surface.blit(ps, (int(self.x) - r - 1, int(self.y) - r - 1))


class ParticleSystem:
    def __init__(self):
        self._particles = []

    def update(self, dt):
        for p in self._particles:
            p.update(dt)
        self._particles = [p for p in self._particles if p.alive]

    def draw(self, surface):
        for p in self._particles:
            p.draw(surface)

    # Emitters
    def explode(self, x, y, color, count=18, speed=3.5, size=5):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.4, speed)
            cr = max(0, min(255, color[0] + random.randint(-30, 30)))
            cg = max(0, min(255, color[1] + random.randint(-30, 30)))
            cb = max(0, min(255, color[2] + random.randint(-30, 30)))
            self._particles.append(_Dot(x,y,math.cos(angle) * spd, math.sin(angle) * spd,(cr, cg, cb), random.uniform(size * 0.5, size),random.randint(350, 700)))

    def boss_explode(self, x, y, color):
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(1.5, 7.0)
            self._particles.append(_Dot(
                x, y,
                math.cos(angle) * spd, math.sin(angle) * spd,
                color, random.uniform(4, 12), random.randint(500, 1200)
            ))
        for _ in range(25):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(4, 11)
            self._particles.append(_Dot(
                x, y,
                math.cos(angle) * spd, math.sin(angle) * spd,
                (255, 240, 180), 3, random.randint(400, 900)
            ))

    def hit_sparks(self, x, y, color=(255, 240, 120)):
        for _ in range(7):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(1.5, 4.5)
            self._particles.append(_Dot(
                x, y,
                math.cos(angle) * spd, math.sin(angle) * spd,
                color, random.uniform(2, 4), random.randint(180, 380)
            ))

    def damage_puff(self, x, y):
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(1, 3.5)
            self._particles.append(_Dot(
                x, y,
                math.cos(angle) * spd, math.sin(angle) * spd,
                (220, 60, 60), random.uniform(3, 6), random.randint(300, 600)
            ))

    def powerup_collect(self, x, y, color):
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(2, 6)
            self._particles.append(_Dot(
                x, y,
                math.cos(angle) * spd, math.sin(angle) * spd,
                color, random.uniform(3, 7), random.randint(400, 800)
            ))

    def dash_trail(self, x, y, color=(80, 220, 200)):
        for _ in range(4):
            self._particles.append(_Dot(
                x, y,
                random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8),
                color, random.uniform(3, 8), random.randint(150, 300)
            ))

    def zone_transition_burst(self, sw, sh, color):
        for _ in range(30):
            self._particles.append(_Dot(
                random.uniform(0, sw), random.uniform(0, sh),
                random.uniform(-1, 1), random.uniform(-1, 1),
                color, random.uniform(2, 6), random.randint(800, 1800)
            ))

    def combo_text_pop(self, x, y):
        colors = [(255, 215, 0), (255, 100, 180), (80, 220, 200), (100, 255, 60)]
        for _ in range(16):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(2, 5)
            self._particles.append(_Dot(
                x, y,
                math.cos(angle) * spd, math.sin(angle) * spd - 2,
                random.choice(colors), random.uniform(3, 6),
                random.randint(500, 900), gravity=0.1
            ))
