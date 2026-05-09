import random
def _armor(b):
    bonus = int(b.max_hp * 0.40)
    b.max_hp += bonus
    b.hp += bonus


MUTATIONS = [
    {"name": "Speed Up","shift":(20,-10,-20),
     "apply": lambda b: setattr(b,"speed", min(b.speed * 1.30,7.0))},
    {"name": "Armor","shift": (-30,-30,40),
     "apply": lambda b: _armor(b)},
    {"name": "Split","shift": (10,40,-20),
     "apply": lambda b: setattr(b,"splits_on_death",True)},
    {"name": "Camouflage","shift": (-40,-40,-40),
     "apply": lambda b: setattr(b,"alpha", max(60, b.alpha - 70))},
    {"name": "Toxic","shift": (30,-40,30),
     "apply": lambda b: setattr(b,"toxic",True)},
    {"name": "Regeneration","shift": (-20,50,-20),
     "apply": lambda b: setattr(b,"regen_rate",3)},
    {"name": "Swarm","shift": (40,20,-40),
     "apply": lambda b: setattr(b,"swarm_mode",True)},
]


def roll_mutations(wave):
    count = min(3, wave // 2)
    return random.sample(MUTATIONS, min(count, len(MUTATIONS)))


def apply_mutations(bacteria, mutations):
    for m in mutations:
        m["apply"](bacteria)
        dr, dg, db = m["shift"]
        r, g, b    = bacteria.color
        bacteria.color = (max(0, min(255, r + dr)),max(0, min(255, g + dg)),max(0, min(255, b + db)),)
