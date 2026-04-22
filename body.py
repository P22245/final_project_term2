from config import BODY_MAX_HP, BODY_REGEN_PER_KILL

class Body:
    def __init__(self):
        self.max_hp = BODY_MAX_HP
        self.hp = float(BODY_MAX_HP)
        self.regen_bonus = 1.0

    def take_infection(self, damage=8):
        self.hp = max(0.0, self.hp - damage)

    def on_bacteria_killed(self, regen_mult=1.0):
        self.hp = min(self.max_hp, self.hp + BODY_REGEN_PER_KILL * regen_mult)

    @property
    def hp_ratio(self):
        return self.hp / self.max_hp

    @property
    def is_dead(self):
        return self.hp <= 0
