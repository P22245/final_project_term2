import pygame
import math

class Cell:
    def __init__(self, x, y, radius, max_hp, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.max_hp = max_hp
        self.hp = max_hp
        self.color = color
        self.alive = True

    # Geometry
    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def collides_with(self, other):
        return self.distance_to(other) < self.radius + other.radius

    # Health
    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    @property
    def hp_ratio(self):
        return self.hp / self.max_hp if self.max_hp else 0.0

    # Movement
    def move(self, dx, dy, bounds):
        self.x = max(bounds[0] + self.radius,min(bounds[2] - self.radius, self.x + dx))
        self.y = max(bounds[1] + self.radius,min(bounds[3] - self.radius, self.y + dy))

    # Draw helpers
    def draw_health_bar(self, surface, above=6):
        bw = self.radius * 2
        bh = 4
        bx = int(self.x - self.radius)
        by = int(self.y - self.radius - above - bh)
        pygame.draw.rect(surface, (60, 60, 60), (bx, by, bw, bh), border_radius=2)
        fw = int(bw * self.hp_ratio)
        if fw > 0:
            if self.hp_ratio > 0.5:
                color = (60, 220, 100)
            elif self.hp_ratio > 0.25:
                color = (240, 200, 50)
            else:
                color = (220, 60, 60)
            pygame.draw.rect(surface, color, (bx, by, fw, bh), border_radius=2)

    def draw(self,surface):
        raise NotImplementedError
