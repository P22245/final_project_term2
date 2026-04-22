# Screen
SCREEN_W, SCREEN_H = 1200, 750
FPS = 60

# Wave structure
TOTAL_WAVES = 9
TOTAL_ZONES = 3
BOSS_WAVE_INTERVAL = 3
CELL_INFECT_START_WAVE = 3
WAVE_FLASH_DURATION = 5000
MUTATION_FLASH_DURATION = 7500

# Colors
BG_COLOR = (20,5,10)
WBC_COLOR = (200,230,255)
WBC_CORE = (100,180,255)
ANTIBODY_COLOR = (180,255,220)
HEALTH_BAR_HIGH = (60,220,100)
HEALTH_BAR_MED = (240,200,50)
HEALTH_BAR_LOW = (220,60,60)
WHITE = (255,255,255)
RED = (220,60,60)
YELLOW = (240,200,50)
CYAN = (80,220,200)
PURPLE = (160,80,220)
ORANGE = (240,140,40)
DARK_GRAY = (40,40,50)
GRAY = (120,120,140)
LIME = (100,255,60)
PINK = (255,100,180)
GOLD = (255,215,0)

BACTERIA_COLORS = [(180, 230, 80),(220, 180, 40),(230, 120, 40),(220, 60,  60),(160, 60,  220)]

# Player
PLAYER_SPEED = 6
PLAYER_RADIUS = 22
PLAYER_MAX_HP = 800
PLAYER_SHOOT_DELAY = 180
DASH_SPEED = 20
DASH_DURATION = 200
DASH_COOLDOWN = 900
PLAYER_IFRAMES = 600
PLAYER_REGEN_START_WAVE = 7
PLAYER_REGEN_HP_PER_S = 1.5

# Antibody
ANTIBODY_SPEED = 11
ANTIBODY_RADIUS = 8
ANTIBODY_DAMAGE = 35
ANTIBODY_LIFETIME = 2200

# Bacteria
BACTERIA_BASE_SPEED = 1.8
BACTERIA_BASE_HP = 45
BACTERIA_BASE_RADIUS = 14
BACTERIA_DAMAGE = 3
BACTERIA_SPREAD_TIME = 5500
BACTERIA_SPEED_WAVE_MULT = 0.10
BACTERIA_HP_WAVE_MULT = 0.35

# Body
BODY_MAX_HP = 1500
BODY_REGEN_PER_KILL = 0.6

# Waves
WAVE_BASE_COUNT = 7
WAVE_COUNT_GROWTH = 3
WAVE_INTERMISSION = 4000

# Score
SCORE_PER_KILL = 100
SCORE_PER_BOSS_KILL = 1000
SCORE_PER_WAVE = 250
COMBO_WINDOW_MS = 3000

# Stats
STATS_SAMPLE_INTERVAL = 5000

# Power-ups
POWERUP_DROP_CHANCE = 0.20
POWERUP_RADIUS = 14
POWERUP_LIFETIME = 8000

# Screen shake
SHAKE_BOSS_HIT = 6
SHAKE_PLAYER_HIT = 4
SHAKE_BOSS_PHASE = 10
SHAKE_DECAY = 0.85

# Organ zones
ORGAN_ZONES = [{"name": "Bloodstream", "bg": (15, 3, 8), "wall": (130, 20, 40),
        "accent": (220, 60, 80), "description": "The main circulatory highway",
        "buff": "Normal conditions","bacteria_speed_mult": 1.0, "player_speed_mult": 1.0,
        "regen_mult": 1.0, "shoot_delay_mult": 1.0, "antibody_damage_mult": 1.0,},
    {
        "name": "Lung", "bg": (10, 5, 25), "wall": (140, 70, 170),
        "accent": (190, 110, 220), "description": "Oxygen-rich environment",
        "buff": "Body regen +50%","bacteria_speed_mult": 0.9, "player_speed_mult": 1.0,
        "regen_mult": 1.5, "shoot_delay_mult": 1.0, "antibody_damage_mult": 1.0,
    },
    {
        "name": "Heart", "bg": (25, 3, 3), "wall": (180, 20, 20),
        "accent": (255, 60, 60), "description": "Danger zone",
        "buff": "Bacteria +30% faster",
        "bacteria_speed_mult": 1.3, "player_speed_mult": 1.0,
        "regen_mult": 0.8, "shoot_delay_mult": 1.0, "antibody_damage_mult": 1.0,
    },
    {
        "name": "Brain", "bg": (5, 10, 28), "wall": (55, 75, 180),
        "accent": (100, 140, 255), "description": "Neural network zone",
        "buff": "Fire rate +25%",
        "bacteria_speed_mult": 1.1, "player_speed_mult": 1.1,
        "regen_mult": 1.0, "shoot_delay_mult": 0.75, "antibody_damage_mult": 1.0,
    },
    {
        "name": "Liver", "bg": (20, 10, 3), "wall": (140, 80, 20),
        "accent": (200, 140, 40), "description": "Toxic filtration zone",
        "buff": "Player -10% slower",
        "bacteria_speed_mult": 0.8, "player_speed_mult": 0.9,
        "regen_mult": 1.2, "shoot_delay_mult": 1.0, "antibody_damage_mult": 1.0,
    },
    {
        "name": "Stomach", "bg": (15, 15, 5), "wall": (120, 120, 20),
        "accent": (200, 200, 40), "description": "Acidic environment",
        "buff": "Antibody damage +20%",
        "bacteria_speed_mult": 1.0, "player_speed_mult": 1.0,
        "regen_mult": 1.0, "shoot_delay_mult": 1.0, "antibody_damage_mult": 1.2,
    },
]

BOSS_BASE_HP = 350
BOSS_BASE_SPEED = 1.8
BOSS_BASE_DAMAGE = 15
BOSS_RADIUS = 40
