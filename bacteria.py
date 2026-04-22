import pygame
import math
import random
from cell import Cell
from config import *

SEPARATION_RADIUS = 120
SEPARATION_FORCE = 0.8
SWARM_STOP_DIST = 160

class Bacteria(Cell):
    def __init__(self, x, y, wave=1):
        tier = min(wave - 1, len(BACTERIA_COLORS) - 1)
        radius = BACTERIA_BASE_RADIUS + min(wave // 3, 6)
        max_hp = int(BACTERIA_BASE_HP * (1 + (wave - 1) * BACTERIA_HP_WAVE_MULT))
        super().__init__(x,y,radius,max_hp, BACTERIA_COLORS[tier])
        self._swarm_active = False
        self._swarm_timer = 0
        self.speed = BACTERIA_BASE_SPEED
        self.wave = wave

        self.splits_on_death = False
        self.alpha = 255
        self.toxic = False
        self.regen_rate = 0
        self.swarm_mode = False

        self._spread_timer = pygame.time.get_ticks()
        self.has_spread = False

        self._target_x = x + random.uniform(-120, 120)
        self._target_y = y + random.uniform(-120, 120)
        self._wander_timer = pygame.time.get_ticks()
        self._wobble = random.uniform(0, 6.28)
        self._wobble_speed = random.uniform(0.04, 0.09)
        self._angle = 0.0
        self._flagella = [(random.uniform(0, 6.28), random.choice([-1, 1]))for _ in range(random.randint(2, 4))]

    def reset_spread(self, now):
        self.has_spread = False
        self._spread_timer = now

    def update(self, player_pos, bounds, now, dt, all_bacteria=None):
            if not self.alive:
                return

            if self.regen_rate:
                self.heal(self.regen_rate * dt)

            self._wobble += self._wobble_speed
            self._angle  += 1.5

            # random every 2 secs see swarm or not
            if self.swarm_mode:
                if now - self._swarm_timer > 2000:
                    self._swarm_timer = now
                    self._swarm_active = random.random() < 0.3

            # find target
            if self.swarm_mode and self._swarm_active:
                dist_to_player = math.hypot(player_pos.x - self.x, player_pos.y - self.y)
                if dist_to_player > SWARM_STOP_DIST:
                    tx, ty = player_pos.x, player_pos.y
                else:
                    angle = math.atan2(self.y - player_pos.y, self.x - player_pos.x)
                    angle += 0.03
                    tx = player_pos.x + math.cos(angle) * SWARM_STOP_DIST
                    ty = player_pos.y + math.sin(angle) * SWARM_STOP_DIST
            else:
                if now - self._wander_timer > random.randint(2000, 3000):
                    self._wander_timer = now
                    self._target_x = random.uniform(bounds[0] + 30, bounds[2] - 30)
                    self._target_y = random.uniform(bounds[1] + 30, bounds[3] - 30)
                tx, ty = self._target_x, self._target_y

            # move to target
            dx,dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            if dist > 2:
                self.move(dx / dist * self.speed, dy / dist * self.speed, bounds)

            # Separation
            if all_bacteria:
                sep_x, sep_y = 0.0, 0.0
                for other in all_bacteria:
                    if other is self or not other.alive:
                        continue
                    odx = self.x - other.x
                    ody = self.y - other.y
                    odist = math.hypot(odx, ody)
                    if 0 < odist < SEPARATION_RADIUS:
                        force = (SEPARATION_RADIUS - odist) / SEPARATION_RADIUS
                        sep_x += (odx / odist) * force
                        sep_y += (ody / odist) * force
                if sep_x or sep_y:
                    sep_len = math.hypot(sep_x, sep_y) or 1
                    self.move(sep_x / sep_len * SEPARATION_FORCE,sep_y / sep_len * SEPARATION_FORCE,bounds)

            # Spread infection
            if not self.has_spread and now - self._spread_timer > BACTERIA_SPREAD_TIME:
                self.has_spread = True

    def draw(self, surface):
        if not self.alive:
            return

        cx,cy = int(self.x), int(self.y)
        r = self.radius
        wobble_r = r + int(math.sin(self._wobble) * 2)
        alpha = self.alpha

        s = pygame.Surface((wobble_r * 2 + 10, wobble_r * 2 + 10), pygame.SRCALPHA)

        for i, (angle_offset, side) in enumerate(self._flagella):
            base_a = math.radians(self._angle * side + i * 60) + angle_offset
            for seg in range(4):
                fx = (wobble_r + 5) + math.cos(base_a + seg * 0.3) * (r + 4 + seg * 5)
                fy = (wobble_r + 5) + math.sin(base_a + seg * 0.3) * (r + 4 + seg * 5)
                pygame.draw.circle(s, (*self.color, max(40, alpha - seg * 40)),(int(fx), int(fy)), max(1, 3 - seg))

        pygame.draw.circle(s, (*self.color, alpha),(wobble_r + 5, wobble_r + 5), wobble_r)
        nucleus = tuple(max(0, min(255, c - 40)) for c in self.color)
        pygame.draw.circle(s, (*nucleus, alpha), (wobble_r + 5, wobble_r + 5), wobble_r // 2)

        if self.toxic:
            pygame.draw.circle(s, (180, 60, 220, 60),(wobble_r + 5, wobble_r + 5), wobble_r + 4, 3)

        surface.blit(s,(cx - wobble_r - 5, cy - wobble_r - 5))
        self.draw_health_bar(surface)

    def spawn_children(self):
        children = []
        for _ in range(2):
            child = Bacteria(self.x + random.uniform(-30, 30),self.y + random.uniform(-30, 30),max(1, self.wave - 1))
            child.max_hp = max(10, self.max_hp // 2)
            child.hp = child.max_hp
            child.radius = max(6, self.radius - 4)
            child.speed = self.speed * 1.1
            children.append(child)
        return children