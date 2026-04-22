import pygame
import math
import random
from config import *

class BodyCell:
    RADIUS       = 7
    INFECT_RANGE = 72
    INFECT_TIME  = 2500
    HATCH_TIME   = 7000
    SHOOT_RADIUS = 18

    def __init__(self, x, y):
        self.x       = float(x)
        self.y       = float(y)
        self.alive   = True
        self.state   = "S"
        self.hatched   = False
        self.destroyed = False

        self._exposed_since  = 0
        self._infected_since = 0
        self._anim           = random.uniform(0, math.pi * 2)

    def update(self, bacteria_list, antibodies, now, dt):
        self._anim += dt * 2.0

        if self.state == "S":
            near = any(b.alive and math.hypot(b.x - self.x, b.y - self.y) < self.INFECT_RANGE for b in bacteria_list)
            if near:
                if self._exposed_since == 0:
                    self._exposed_since = now
                elif now - self._exposed_since >= self.INFECT_TIME:
                    self.state = "I"
                    self._infected_since = now
                    self._exposed_since = 0
            else:
                self._exposed_since = 0

        elif self.state == "I":
            for ab in antibodies:
                if ab.alive and math.hypot(ab.x - self.x, ab.y - self.y) < self.SHOOT_RADIUS:
                    ab.alive = False
                    self.alive = False
                    self.destroyed = True
                    return "destroyed"

            if now - self._infected_since >= self.HATCH_TIME:
                self.alive = False
                self.hatched = True
                return "spawn"

        return None

    @property
    def hatch_progress(self):
        if self.state != "I" or self._infected_since == 0:
            return 0.0
        return min(1.0, (pygame.time.get_ticks() - self._infected_since) / self.HATCH_TIME)

    def draw(self, surface, now):
        if not self.alive:
            return
        x, y = int(self.x), int(self.y)

        if self.state == "S":
            pulse = 0.55 + 0.45 * math.sin(self._anim)
            gs    = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(gs, (200, 220, 255, int(40 * pulse)), (12, 12), 12)
            surface.blit(gs, (x - 12, y - 12))
            pygame.draw.circle(surface, (190, 210, 255), (x, y), self.RADIUS)
            pygame.draw.circle(surface, (220, 240, 255), (x, y), self.RADIUS, 1)

            if self._exposed_since > 0:
                prog = min(1.0, (now - self._exposed_since) / self.INFECT_TIME)
                r2   = self.RADIUS + 5
                for i in range(int(prog * 16)):
                    a  = -math.pi/2 + (i / 16) * prog * 2 * math.pi
                    px = x + int(math.cos(a) * r2)
                    py = y + int(math.sin(a) * r2)
                    pygame.draw.circle(surface, (255, 160, 0), (px, py), 1)

        elif self.state == "I":
            hp    = self.hatch_progress
            g_col = int(140 * (1.0 - hp))
            pulse = 0.4 + 0.6 * abs(math.sin(self._anim * (1.5 + hp * 2)))

            gr = int(self.RADIUS + 6 + hp * 10)
            gs = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (255, g_col // 2, 0, int(120 * pulse)), (gr, gr), gr)
            surface.blit(gs, (x - gr, y - gr))

            pygame.draw.circle(surface, (255, g_col, 0), (x, y), self.RADIUS)
            pygame.draw.circle(surface, (255, 220, 80), (x, y), max(2, int(self.RADIUS * 0.4 + pulse * 2)))

            remaining = 1.0 - hp
            ring_r    = self.RADIUS + 10
            if remaining > 0:
                steps = max(3, int(remaining * 28))
                pts   = []
                for i in range(steps + 1):
                    a = -math.pi/2 + (i / steps) * remaining * 2 * math.pi
                    pts.append((x + int(math.cos(a) * ring_r),
                                y + int(math.sin(a) * ring_r)))
                if len(pts) >= 2:
                    ring_col = (255, 255, 255) if hp < 0.6 else (255, 80, 0)
                    pygame.draw.lines(surface, ring_col, False, pts, 2 if hp < 0.8 else 3)

            if hp > 0.75:
                warn_alpha = int(200 + 55 * abs(math.sin(now * 0.008)))
                wt = pygame.Surface((10, 14), pygame.SRCALPHA)
                pygame.draw.rect(wt,   (255, 60, 0, warn_alpha), (3, 0, 4, 9))
                pygame.draw.circle(wt, (255, 60, 0, warn_alpha), (5, 12), 2)
                surface.blit(wt, (x - 5, y - ring_r - 16))


def spawn_body_cells(wave, bounds):
    x1, y1, x2, y2 = bounds
    margin = 90
    count = 12 + wave
    cells = []
    attempts = 0
    while len(cells) < count and attempts < count * 8:
        attempts += 1
        bx = random.randint(x1 + margin, x2 - margin)
        by = random.randint(y1 + margin, y2 - margin)
        if not any(math.hypot(c.x - bx, c.y - by) < 55 for c in cells):
            cells.append(BodyCell(bx, by))
    return cells
