import pygame
import math
import random
from config import POWERUP_RADIUS, POWERUP_LIFETIME


class PowerUp:
    KIND_HEALTH = "health"
    KIND_RAPID_FIRE = "rapid_fire"
    KIND_SPEED = "speed"
    KIND_SHIELD = "shield"
    KIND_BODY_HEAL = "body_heal"

    _META = {KIND_HEALTH:((60,220,100),"HP+"),KIND_RAPID_FIRE: ((80,220,200), "FAST"),KIND_SPEED:((240, 200, 50),  "SPD"),
        KIND_SHIELD:((160, 80,  220), "SHLD"),KIND_BODY_HEAL: ((255, 180, 50),  "BODY+")}
    KINDS = list(_META.keys())

    def __init__(self, x, y, kind=None):
        self.x = x
        self.y = y
        self.radius = POWERUP_RADIUS
        self.kind = kind or random.choice(self.KINDS)
        self.alive = True
        self._born = pygame.time.get_ticks()
        self._anim = random.uniform(0, math.pi * 2)
        self.color, self.label = self._META[self.kind]

    def update(self):
        self._anim += 0.06
        if pygame.time.get_ticks() - self._born > POWERUP_LIFETIME:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        bob_y = int(self.y + math.sin(self._anim) * 4)
        cx, cy = int(self.x), bob_y
        r = self.radius

        age = now - self._born
        if age > POWERUP_LIFETIME - 2000 and (age // 200) % 2 == 0:
            return

        glow = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
        pulse_alpha = int(40 + 30 * abs(math.sin(self._anim * 1.5)))
        pygame.draw.circle(glow, (*self.color, pulse_alpha), (r * 3, r * 3), r * 3)
        surface.blit(glow, (cx - r * 3, cy - r * 3))

        pygame.draw.circle(surface, (20, 20, 40),    (cx, cy), r + 2)
        pygame.draw.circle(surface, self.color,      (cx, cy), r)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r, 2)

        font = pygame.font.SysFont("consolas", 11, bold=True)
        lbl = font.render(self.label, True, (255, 255, 255))
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

    def collides_with_player(self, player):
        return math.hypot(self.x - player.x, self.y - player.y) < self.radius + player.radius

    def apply(self, player, body):
        if self.kind == self.KIND_HEALTH:
            amt = min(40, player.max_hp - player.hp)
            player.heal(amt)
            return f"+{amt} WBC HP"
        elif self.kind == self.KIND_RAPID_FIRE:
            player.apply_powerup("rapid_fire", 5000)
            return "Rapid Fire! (5s)"
        elif self.kind == self.KIND_SPEED:
            player.apply_powerup("speed_boost", 5000)
            return "Speed Boost! (5s)"
        elif self.kind == self.KIND_SHIELD:
            player.apply_powerup("shield", 4000)
            return "Shield! (4s)"
        elif self.kind == self.KIND_BODY_HEAL:
            amt = 15
            body.hp = min(body.max_hp, body.hp + amt)
            return f"+{amt} Body HP"
        return ""


def maybe_spawn(x, y, chance):
    return PowerUp(x, y) if random.random() < chance else None
