import pygame
import math
from cell import Cell
from config import *


class _Shot:
    def __init__(self, x, y, vx, vy, lifetime=ANTIBODY_LIFETIME):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.radius = ANTIBODY_RADIUS
        self.damage = ANTIBODY_DAMAGE
        self.alive = True
        self._born = pygame.time.get_ticks()
        self._lifetime = lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if pygame.time.get_ticks()-self._born > self._lifetime:
            self.alive = False
        if not (0 <= self.x <= SCREEN_W and 0 <= self.y <= SCREEN_H):
            self.alive = False

    def draw(self, surface):
        r = self.radius
        glow = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*ANTIBODY_COLOR[:3], 60), (r * 3, r * 3), r * 3)
        surface.blit(glow, (int(self.x) - r * 3, int(self.y) - r * 3))
        pygame.draw.circle(surface, ANTIBODY_COLOR, (int(self.x), int(self.y)), r)


class WhiteBloodCell(Cell):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS, PLAYER_MAX_HP, WBC_COLOR)
        self.speed = PLAYER_SPEED
        self.antibodies = []

        self._last_shot = 0
        self._shoot_delay_override = PLAYER_SHOOT_DELAY
        self._dash_active = False
        self._dash_vx = 0.0
        self._dash_vy = 0.0
        self._dash_start = 0
        self._dash_last = -DASH_COOLDOWN
        self._hit_time = -PLAYER_IFRAMES
        self._powerups = {}
        self._pulse = 0.0

        self.total_shots = 0
        self.distance_traveled = 0.0

        # perk bonuses (set by game_manager._apply_perk)
        self.speed_bonus = 1.0
        self.dash_cooldown_bonus = 1.0
        self.dash_speed_bonus = 1.0
        self.damage_bonus = 1.0
        self.antibody_lifetime_bonus = 1.0
        self.combo_window_bonus = 1.0
        self.iframes_bonus = 1.0
        self.regen_override = PLAYER_REGEN_START_WAVE

    # Power-ups
    def apply_powerup(self, name, duration_ms):
        self._powerups[name] = pygame.time.get_ticks() + duration_ms

    def has_powerup(self, name):
        if pygame.time.get_ticks() < self._powerups.get(name, 0):
            return True
        self._powerups.pop(name, None)
        return False

    @property
    def shielded(self):
        return self.has_powerup("shield")

    @property
    def rapid_fire(self):
        return self.has_powerup("rapid_fire")

    @property
    def speed_boosted(self):
        return self.has_powerup("speed_boost")

    # I-frames
    @property
    def invincible(self):
        iframes = int(PLAYER_IFRAMES * self.iframes_bonus)
        return self.shielded or (pygame.time.get_ticks() - self._hit_time < iframes)

    def take_damage(self, amount):
        if self.invincible:
            return
        super().take_damage(amount)
        self._hit_time = pygame.time.get_ticks()

    # Input
    def handle_input(self, keys, mouse_pos, mouse_buttons, now, bounds):
        dx, dy = 0.0, 0.0
        move_speed = self.speed * (1.3 if self.speed_boosted else 1.0)

        if not self._dash_active:
            if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            length = math.hypot(dx, dy)
            if length:
                dx, dy = dx / length * move_speed, dy / length * move_speed

        dash_cd = int(DASH_COOLDOWN * self.dash_cooldown_bonus)
        if keys[pygame.K_SPACE] and not self._dash_active:
            if now - self._dash_last >= dash_cd:
                self._start_dash(dx or 1.0, dy)

        if self._dash_active:
            if now - self._dash_start < DASH_DURATION:
                dx, dy = self._dash_vx, self._dash_vy
            else:
                self._dash_active = False

        old_x, old_y = self.x, self.y
        self.move(dx, dy, bounds)
        self.distance_traveled += math.hypot(self.x - old_x, self.y - old_y)

        if mouse_buttons[0] or keys[pygame.K_z]:
            self._shoot(mouse_pos, now)

    def _start_dash(self, dx, dy):
        length = math.hypot(dx, dy) or 1.0
        dash_spd = DASH_SPEED * self.dash_speed_bonus
        self._dash_vx = dx / length * dash_spd
        self._dash_vy = dy / length * dash_spd
        self._dash_active = True
        self._dash_start = pygame.time.get_ticks()
        self._dash_last = pygame.time.get_ticks()

    def _shoot(self, mouse_pos, now):
        delay = int(self._shoot_delay_override * (0.45 if self.rapid_fire else 1.0))
        if now - self._last_shot < delay:
            return
        self._last_shot = now
        mx, my = mouse_pos
        dx, dy = mx - self.x, my - self.y
        length = math.hypot(dx, dy) or 1.0
        lifetime = int(ANTIBODY_LIFETIME * self.antibody_lifetime_bonus)
        self.antibodies.append(_Shot(self.x, self.y,dx / length * ANTIBODY_SPEED,dy / length * ANTIBODY_SPEED,lifetime=lifetime))
        self.total_shots += 1

    def update(self, now):
        self._pulse = (self._pulse + 0.05) % (2 * math.pi)
        for ab in self.antibodies:
            ab.update()
        self.antibodies = [ab for ab in self.antibodies if ab.alive]

    def set_shoot_delay(self, delay_ms):
        self._shoot_delay_override = delay_ms

    @property
    def dash_cooldown_ratio(self):
        dash_cd = int(DASH_COOLDOWN * self.dash_cooldown_bonus)
        return min(1.0, (pygame.time.get_ticks() - self._dash_last) / dash_cd)

    @property
    def dash_active(self):
        return self._dash_active

    def active_powerup_timers(self):
        now = pygame.time.get_ticks()
        return [(name, exp) for name, exp in self._powerups.items() if exp > now]

    # Draw
    def draw(self, surface):
        for ab in self.antibodies:
            ab.draw(surface)

        now = pygame.time.get_ticks()
        hit_age = now - self._hit_time
        iframes = int(PLAYER_IFRAMES * self.iframes_bonus)

        if 0 < hit_age < iframes and not self.shielded:
            if (hit_age // 80) % 2 == 1:
                return

        pulse_r = int(self.radius + 6 + math.sin(self._pulse) * 3)

        if self.shielded:
            sr = pulse_r + 10
            sa = pygame.Surface((sr * 2 + 10, sr * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(sa, (160, 80, 220, 80),  (sr + 5, sr + 5), sr)
            pygame.draw.circle(sa, (200, 120, 255, 180), (sr + 5, sr + 5), sr, 3)
            surface.blit(sa, (int(self.x) - sr - 5, int(self.y) - sr - 5))

        if self.speed_boosted:
            body_color = (200, 255, 150)
        elif self.rapid_fire:
            body_color = (150, 220, 255)
        else:
            body_color = WBC_COLOR

        glow = pygame.Surface((pulse_r * 2 + 10, pulse_r * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*body_color[:3], 40), (pulse_r + 5, pulse_r + 5), pulse_r)
        surface.blit(glow, (int(self.x) - pulse_r - 5, int(self.y) - pulse_r - 5))

        pygame.draw.circle(surface, body_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WBC_CORE,   (int(self.x), int(self.y)), self.radius // 2)

        if self._dash_active:
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 3)

        self.draw_health_bar(surface)
