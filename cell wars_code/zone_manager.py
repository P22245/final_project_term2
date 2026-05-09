import pygame
import math
import random
from config import ORGAN_ZONES, SCREEN_W, SCREEN_H, TOTAL_ZONES

class ZoneManager:
    def __init__(self):
        self.zone_index = 0
        self.zone = ORGAN_ZONES[0]
        self._bg_cache = {}
        self._anim_timer = 0
        self._transitioning = False
        self._transition_alpha = 0
        self._next_zone_idx = 0
        self._build_bg(0)

    def advance_zone(self):
        self._next_zone_idx = min(self.zone_index + 1, TOTAL_ZONES - 1)
        self._transitioning = True
        self._transition_alpha = 0

    def update(self):
        self._anim_timer += 1
        if self._transitioning:
            self._transition_alpha += 8
            if self._transition_alpha >= 255:
                self.zone_index = self._next_zone_idx
                self.zone = ORGAN_ZONES[self.zone_index]
                self._build_bg(self.zone_index)
                self._transitioning = False
                self._transition_alpha = 255
                return True
        elif self._transition_alpha > 0:
            self._transition_alpha = max(0, self._transition_alpha - 8)
        return False

    @property
    def zone_name(self):
        return self.zone["name"]
    def bacteria_speed_mult(self):
        return self.zone["bacteria_speed_mult"]
    def player_speed_mult(self):
        return self.zone["player_speed_mult"]
    def regen_mult(self):           
        return self.zone["regen_mult"]
    def shoot_delay_mult(self):     
        return self.zone.get("shoot_delay_mult", 1.0)
    def antibody_damage_mult(self): 
        return self.zone.get("antibody_damage_mult", 1.0)

    def _build_bg(self, idx):
        z = ORGAN_ZONES[idx]
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill(z["bg"])
        wall_h = 50
        for rect in [(0, 0, SCREEN_W, wall_h),(0, SCREEN_H - wall_h, SCREEN_W, wall_h),(0, 0, wall_h, SCREEN_H),(SCREEN_W - wall_h, 0, wall_h, SCREEN_H)]:
            pygame.draw.rect(surf, z["wall"], rect)

        rng = random.Random(idx * 777)
        accent = z["accent"]
        name = z["name"]

        if name == "Bloodstream":
            for _ in range(25):
                rx, ry = rng.randint(60, SCREEN_W-60), rng.randint(60, SCREEN_H-60)
                rr = rng.randint(4, 12)
                a = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
                pygame.draw.circle(a, (*accent, 25), (rr, rr), rr)
                surf.blit(a, (rx-rr, ry-rr))

        elif name == "Lung":
            for _ in range(18):
                rx, ry = rng.randint(80, SCREEN_W-80), rng.randint(80, SCREEN_H-80)
                rr = rng.randint(8, 24)
                a = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
                pygame.draw.circle(a, (*accent, 18), (rr, rr), rr)
                surf.blit(a, (rx-rr, ry-rr))
            for _ in range(6):
                sx, sy = rng.randint(80, SCREEN_W-80), rng.randint(80, SCREEN_H-80)
                pygame.draw.line(surf, (*accent, 30),(sx, sy),(sx + rng.randint(-120, 120), sy + rng.randint(-120, 120)), 2)

        elif name == "Heart":
            for ring in range(4):
                rr = 80 + ring * 60
                a = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
                pygame.draw.circle(a, (*accent, 15), (rr, rr), rr, 3)
                surf.blit(a, (SCREEN_W//2 - rr, SCREEN_H//2 - rr))

        elif name == "Brain":
            nodes = [(rng.randint(80, SCREEN_W-80), rng.randint(80, SCREEN_H-80)) for _ in range(14)]
            for i, (nx, ny) in enumerate(nodes):
                for j, (mx, my) in enumerate(nodes):
                    if i < j and math.hypot(nx-mx, ny-my) < 220:
                        la = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                        pygame.draw.line(la, (*accent, 20), (nx, ny), (mx, my), 1)
                        surf.blit(la, (0, 0))
                a = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(a, (*accent, 50), (6, 6), 6)
                surf.blit(a, (nx-6, ny-6))

        elif name == "Liver":
            for row in range(6):
                for col in range(8):
                    hx = 80 + col * 140 + (row % 2) * 70
                    hy = 80 + row * 100
                    hr = 35
                    pts = [(hx + hr * math.cos(math.radians(60*i)),hy + hr * math.sin(math.radians(60*i))) for i in range(6)]
                    la = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    pygame.draw.polygon(la, (*accent, 12), pts)
                    pygame.draw.polygon(la, (*accent, 20), pts, 1)
                    surf.blit(la, (0, 0))

        elif name == "Stomach":
            for _ in range(30):
                rx, ry = rng.randint(60, SCREEN_W-60), rng.randint(60, SCREEN_H-60)
                rr = rng.randint(5, 18)
                a = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
                pygame.draw.circle(a, (*accent, 20), (rr, rr), rr)
                pygame.draw.circle(a, (*accent, 35), (rr, rr), rr, 2)
                surf.blit(a, (rx-rr, ry-rr))

        self._bg_cache[idx] = surf

    def draw_bg(self, surface):
        bg = self._bg_cache.get(self.zone_index)
        if bg:
            surface.blit(bg, (0, 0))
        if self._anim_timer % 3 == 0:
            pulse   = abs(math.sin(self._anim_timer * 0.015)) * 30
            accent  = self.zone["accent"]
            wall_h  = 50
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            for rect in [(0, 0, SCREEN_W, wall_h),(0, SCREEN_H - wall_h, SCREEN_W, wall_h),(0, 0, wall_h, SCREEN_H),(SCREEN_W - wall_h, 0, wall_h, SCREEN_H),]:
                pygame.draw.rect(overlay, (*accent, int(pulse)), rect)
            surface.blit(overlay, (0, 0))

    def draw_transition(self, surface):
        if self._transition_alpha <= 0:
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(255, self._transition_alpha)))
        surface.blit(overlay, (0, 0))
        if self._transition_alpha > 200:
            nz = ORGAN_ZONES[self._next_zone_idx]
            font = pygame.font.SysFont("consolas", 36, bold=True)
            txt = font.render(f"Entering {nz['name']}...", True, nz["accent"])
            sub = pygame.font.SysFont("consolas", 18).render(nz["buff"], True, (200, 200, 200))
            surface.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - 30))
            surface.blit(sub, (SCREEN_W//2 - sub.get_width()//2, SCREEN_H//2 + 20))
