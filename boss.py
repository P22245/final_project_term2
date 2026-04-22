import pygame
import math
import random
from cell import Cell
from config import *


class _Proj:
    def __init__(self, x, y, vx, vy, damage, color=(220, 60, 80)):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.radius = 7
        self.alive = True
        self.color = color
        self._born = pygame.time.get_ticks()

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if pygame.time.get_ticks() - self._born > 3000:
            self.alive = False
        if not (0 <= self.x <= SCREEN_W and 0 <= self.y <= SCREEN_H):
            self.alive = False

    def draw(self, surface):
        r = self.radius
        glow = pygame.Surface((r * 6, r * 6),pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 50),(r * 3, r * 3), r * 3)
        surface.blit(glow, (int(self.x) - r * 3, int(self.y) - r * 3))
        pygame.draw.circle(surface,self.color,(int(self.x), int(self.y)), r)
        pygame.draw.circle(surface,WHITE,(int(self.x), int(self.y)), r - 3)


class Boss(Cell):
    ZONE_BOSSES = {"Bloodstream": {"name": "Blood Clot","color": (180, 20,  40),"nucleus": (120,0,20)},
        "Lung":{"name": "Pneumo Titan","color": (140, 60,  180),"nucleus": (90,30,130)},
        "Heart":{"name": "Cardiac Reaper","color": (220, 30,  30),"nucleus": (150,0,0)},
        "Brain":{"name": "Neuro Parasite","color": (60,  80,  200),"nucleus": (30,40,140)},
        "Liver":{"name": "Toxin Warlord","color": (180, 120, 20),"nucleus": (120,80,0)},
        "Stomach":{"name": "Acid Behemoth","color": (180, 180, 20),"nucleus": (120,120,0)}}

    def __init__(self, zone_name, wave):
        info = self.ZONE_BOSSES.get(zone_name, self.ZONE_BOSSES["Bloodstream"])
        hp_scale = 1.0 + (wave // BOSS_WAVE_INTERVAL) * 0.3
        super().__init__(SCREEN_W // 2, 120,BOSS_RADIUS,int(BOSS_BASE_HP * hp_scale),info["color"])
        self.nucleus_color = info["nucleus"]
        self.display_name = info["name"]
        self.zone_name = zone_name
        self.base_speed = BOSS_BASE_SPEED
        self.speed = BOSS_BASE_SPEED
        self.damage = BOSS_BASE_DAMAGE
        self.projectiles = []

        self.phase = 1
        self._shoot_timer = 0
        self._spawn_timer = 0
        self._move_angle = 0.0
        self._anim = 0.0
        self._phase2_done = False
        self._phase3_done = False
        self._proj_color = tuple(min(255, c + 60) for c in info["color"])

    def _check_phase(self):
        if self.hp_ratio <= 0.33 and not self._phase3_done:
            self.phase = 3
            self.speed = self.base_speed * 1.6
            self.damage = int(BOSS_BASE_DAMAGE * 2.0)
            self._phase3_done = True
        elif self.hp_ratio <= 0.66 and not self._phase2_done:
            self.phase = 2
            self.speed = self.base_speed * 1.25
            self.damage = int(BOSS_BASE_DAMAGE * 1.5)
            self._phase2_done = True

    def _shoot_radial(self, count):
        spd = ANTIBODY_SPEED * 0.7
        result = []
        for i in range(count):
            angle = math.pi * 2 / count * i
            result.append(_Proj(self.x, self.y,math.cos(angle) * spd,math.sin(angle) * spd,self.damage, self._proj_color))
        return result

    def _shoot_aimed(self, px, py, count):
        spd = ANTIBODY_SPEED * 0.85
        base = math.atan2(py - self.y, px - self.x)
        spread = math.radians(15)
        result = []
        for i in range(count):
            angle = base + (i - count // 2) * spread
            result.append(_Proj(self.x, self.y,math.cos(angle) * spd,math.sin(angle) * spd,self.damage, self._proj_color))
        return result

    def update(self, player_pos, bounds, now, dt, bacteria_list):
        self._check_phase()
        self._anim += 0.06

        self._move_angle += 0.008 * self.phase
        cx = SCREEN_W // 2
        cy = SCREEN_H // 4
        r = 160 + self.phase * 20
        tx = cx + math.cos(self._move_angle) * r
        ty = cy + math.sin(self._move_angle) * r * 0.5
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            self.move(dx / dist * self.speed, dy / dist * self.speed, bounds)

        shoot_interval = [200, 120, 70][self.phase - 1]
        self._shoot_timer += 1
        if self._shoot_timer >= shoot_interval:
            self._shoot_timer = 0
            if self.phase == 1:
                new_projs = self._shoot_radial(6)
            elif self.phase == 2:
                new_projs = self._shoot_radial(8) + self._shoot_aimed(player_pos.x, player_pos.y, 1)
            else:
                new_projs = self._shoot_radial(12) + self._shoot_aimed(player_pos.x, player_pos.y, 3)
            self.projectiles.extend(new_projs)

        if self.phase == 3:
            self._spawn_timer += 1
            if self._spawn_timer >= 240:
                self._spawn_timer = 0
                from bacteria import Bacteria
                for _ in range(2):bacteria_list.append(Bacteria(self.x + random.randint(-80, 80),self.y + random.randint(-80, 80),wave=2))

        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        r = self.radius

        glow_r = r + 20 + int(math.sin(self._anim) * 6)
        glow_col = [(*self.color, 40), (*self.color, 55), (*self.color, 70)][self.phase - 1]
        gs = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, glow_col, (glow_r * 2, glow_r * 2), glow_r * 2)
        surface.blit(gs, (ix - glow_r * 2, iy - glow_r * 2))

        spike_n = 6 + self.phase * 3
        for i in range(spike_n):
            a  = self._anim * 0.5 + math.pi * 2 / spike_n * i
            ex = ix + int(math.cos(a) * (r + 14))
            ey = iy + int(math.sin(a) * (r + 14))
            pygame.draw.line(surface, self.color, (ix, iy), (ex, ey), 3)

        pygame.draw.circle(surface, self.color,(ix, iy), r)
        pygame.draw.circle(surface, self.nucleus_color, (ix, iy), r // 2)

        font = pygame.font.SysFont("consolas", 13, bold=True)
        ph_txt = font.render(f"Phase {self.phase}", True, WHITE)
        surface.blit(ph_txt, (ix - ph_txt.get_width() // 2, iy + r + 4))

        for p in self.projectiles:
            p.draw(surface)

        self._draw_boss_bar(surface)

    def _draw_boss_bar(self, surface):
        bw, bh = 340, 18
        bx = SCREEN_W // 2 - bw // 2
        by = 36
        pygame.draw.rect(surface, (40, 10, 10),  (bx-2, by-2, bw+4, bh+4), border_radius=8)
        pygame.draw.rect(surface, (80, 20, 20),  (bx, by, bw, bh), border_radius=6)
        fw = int(bw * self.hp_ratio)
        if fw > 0:
            phase_colors = [RED, ORANGE, PURPLE]
            pygame.draw.rect(surface, phase_colors[self.phase - 1], (bx, by, fw, bh), border_radius=6)
        font = pygame.font.SysFont("consolas", 13, bold=True)
        lbl  = font.render(f"  {self.display_name}  [{self.zone_name}]  {self.hp}/{self.max_hp}",True, WHITE)
        surface.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, by + 2))
