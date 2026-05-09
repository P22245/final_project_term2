# CELL WARS

## Project Description

- Project by : Panisara Niyathirakul (6810545751)
- Game Genre : Action, Survival, Wave Defense

Cell Wars is a top-down shooter made with Python and Pygame. The concept is simple, let's imagine that you're a White Blood Cell, and your job is to protect the human body from waves of bacteria trying to destroy it from the inside. Each run is 9 waves split across 3 zones. Bacteria mutate differently every wave, a boss shows up every 3 waves, and starting from Wave 3, infected body cells begin appearing on the field that you need to deal with before they hatch into more enemies. Each zone takes place in a different organ that chosen from Bloodstream, Lung, Heart, Brain, Liver, or Stomach and each one changes how the fight plays out. You also get a perk at the start that changes your whole playstyle, whether you want to tank, shoot fast, move quickly, or build combos. There's a live stats window you can open anytime, and a leaderboard that saves your best runs.

---

## Installation
To Clone this project:
```sh
git clone https://github.com/P22245/final_project_term2.git
```

To create and run Python Environment for This project:

Window:
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Mac:
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide
After activate Python Environment of this project, you can process to run the game by:

Window:
```bat
python main.py
```

Mac:
```sh
python3 main.py
```

---

## Tutorial / Usage
1. Enter your name
The game opens on the title screen with a text box. Type your name and hit ENTER. If you skip it, it defaults to "Player". Your name shows up on the leaderboard so it's worth putting something in.

2. Check your perk
You'll land on a start screen showing your randomly assigned perk alongside the full control reference. This perk sticks with you the whole run, it affects your HP, fire rate, move speed, or combo mechanics depending on which one you got. Hit ENTER to start, or R if you want to reroll.

3. Play the wave
Bacteria spawn from all four edges of the screen and move toward you and the body. You move with WASD, aim with your mouse, and shoot with left click (or Z). The goal each wave is to kill everything before the body takes too much damage. If bacteria reach the body, it loses HP. If the body dies, you lose.
Between waves there's a short 4 seconds intermission that tells you what's coming next, then the next wave starts automatically.

4. Watch out for infected body cells (Wave 3+)
Starting at Wave 3, body cells appear scattered around the field. A cell turns orange once bacteria get close enough to it for 2.5 seconds. That's when it becomes infected and the hatch countdown begins. From that point, you have 7 seconds to shoot it before it hatches into a new bacteria mid-wave. Stopping a hatch gives +300 score. Cells that survive the whole wave uninfected give +100 each.

5. Boss waves (Wave 3, 6, and 9)
Every 3 waves a Boss shows up instead of a normal crowd. Each boss is named after the zone and has 3 phases that getting faster and more aggressive as its HP drops. In Phase 3, it also starts spawning bacteria around itself. Keep moving, dodge the shots, and chip away at it. Killing it gives a big score bonus and triggers a zone transition.

6. Zone transitions
After each boss, the game moves to a new zone (a different organ). The background changes, the rules shift. Bacteria might get faster or slower, your fire rate might increase, regen rates change. A transition animation plays, then a brief intermission before the next wave.

7. Win or lose
- Win -> clear all 9 waves and kill the Wave 9 boss
- Lose -> body HP hits zero, or your White Blood Cell dies

From the end screen:
- R to restart
- L to see the leaderboard (top 8 scores with name, score, wave, combo, and result)
- N to change your name and start fresh (end screen only)

### Controls

| Key / Input | Action |
|---|---|
| WASD | Move your White Blood Cell |
| Mouse | Aim target direction |
| Left Click / Z | Shoot antibody |
| SPACE | Dash (brief speed burst + invincibility, has cooldown) |
| N | New game (end screen only) |
| R | Restart |
| P | Pause / Resume |
| M | Mute / Unmute sound |
| V | Open stats data window |
| ESC / Q | Quit the game |

---

## Game Features

### Wave-based survival
The game runs for 9 waves total. Each wave spawns more bacteria than the last, and they get faster as the wave count goes up. Clear everything on screen to end the wave.

### Mutation system
Each wave randomly rolls up to 3 mutations that apply to all bacteria that wave. There are 7 possible mutations:

| Mutation | Effect |
|---|---|
| Speed Up | Bacteria move 30% faster |
| Armor | Bacteria gain +40% max HP |
| Split | Bacteria split into two when killed |
| Camouflage | Bacteria become semi-transparent and harder to see |
| Toxic | Bacteria deal passive damage just by being near you |
| Regeneration | Bacteria slowly recover HP over time |
| Swarm | Bacteria enter swarm mode and cluster together |

Active mutations are shown on the HUD at the start of each wave. Mutated bacteria also shift color so you can spot them visually.

### Zone progression
The game has 6 possible organ zones and each run travels through 3 of them. Every zone has its own passive effect:

| Zone | Effect |
|---|---|
| Bloodstream | Normal conditions, no modifiers |
| Lung | Body regen +50%, bacteria slightly slower |
| Heart | Bacteria +30% faster, body regen reduced |
| Brain | Fire rate +25%, bacteria and player both slightly faster |
| Liver | Player -10% slower, bacteria slower, body regen +20% |
| Stomach | Antibody damage +20% |

### Boss fights
A boss spawns every 3 waves (Wave 3, 6, 9). Each boss is themed after its zone and has a unique name. All bosses have 3 phases that activate as their HP drops:

| Phase | HP Range | Behavior |
|---|---|---|
| Phase 1 | 100%–67% | Fires 6 projectiles in a radial spread |
| Phase 2 | 66%–34% | Fires 8 radial + 1 aimed shot at you, moves faster |
| Phase 3 | 33%–0% | Fires 12 radial + 3 aimed shots, moves even faster, spawns bacteria around itself |

Boss HP scales up with each boss wave, so the Wave 9 boss is significantly tougher than the Wave 3 one.

### Infected body cells (Wave 3+)
From Wave 3 onward, body cells appear on the field each wave. Infection happens in two stages:

1. A cell turns orange when bacteria stay within range of it for 2.5 seconds and it becomes infected
2. Once infected, you have 7 seconds to shoot it before it hatches into a new bacteria

Shooting an infected cell in time gives +300 score. Cells that make it through the wave uninfected give +100 each.

### Perks
One perk is assigned randomly at the start of each run and affects your stats for the whole session:

| Perk | Style | What it does |
|---|---|---|
| Field Medic | Survival | +50 max HP, body regen ×2, player regen starts immediately |
| Gunner | Offense | Fire rate +35%, antibody damage +25%, range +30% |
| Sprinter | Mobility | Move speed +30%, dash cooldown −35%, dash speed +20% |
| Veteran | Utility | Start with a shield, combo window +50%, i-frames +40% |

Without a perk, player regen only kicks in from Wave 7 onward. Field Medic is the only perk that enables it from the very start.

### Power-up drops
Bacteria have a 20% chance to drop a power-up when killed. Walk over them to collect. There are 5 types:

| Power-up | Effect |
|---|---|
| HP+ | Restores up to 40 player HP |
| Rapid Fire | Fire rate boosted for 5 seconds |
| Speed Boost | Move speed boosted for 5 seconds |
| Shield | Grants a shield for 4 seconds |
| Body+ | Restores 15 Body HP |

### Combo kill system
Kill bacteria quickly back-to-back to build a combo. The combo window is 3 seconds and chain kills within that window and each one gives more score. Hit 3+ in a row and you get a combo text pop-up and a sound effect. Miss the window and it resets.

### HUD
The HUD shows everything you need in real time:

| Element | Location | What it shows |
|---|---|---|
| Body HP bar | Top-center | Human body's HP, color shifts green → red as it drops |
| Player HP bar | Top-left | White Blood Cell's HP, turns purple when shielded |
| Score | Center below body bar | Current score in gold |
| Wave badge | Top-right | Current wave, zone name, zone buff, and perk name |
| Dash cooldown arc | Top-left | Circular arc that fills up as dash recharges |
| Active power-up timers | Top-left | Countdown bars for Rapid Fire, Speed Boost, and Shield |
| Combo meter | Bottom-right | Combo count, multiplier, and time window bar |
| Body cell status | Bottom-left | Healthy vs infected cell count during body cell waves |
| Immune Memory badge | Top-right | Damage bonus when recognizing a previous mutation combo |
| Session stats card | Bottom-left | Bacteria killed and infection spread count |

Floating score pop-ups and notifications appear directly on the game world as things happen.

### Immune Memory system
The game tracks which mutation combinations you've faced across waves. If the same mutation combo appears again, you get an antibody damage bonus that scales with how many times you've seen it. The HUD shows this as a green "Immune Memory" badge with a progress bar. New mutation combos trigger a "Body is learning" notification.

### Stats tracker & leaderboard
Press V anytime to open a separate stats window (Tkinter + Matplotlib) showing session history, kill counts, and score charts. Every session is automatically recorded to `gameplay_stats.csv` and visualized in the stats window. After each run, your result is also saved to `highscores.json`. The leaderboard shows the top 8 scores with name, score, wave reached, max combo, and win/loss result which viewable from the end screen with L.

### Resizable window
The game window can be resized freely. The internal resolution stays fixed and scales to fit whatever size you set.

### Screen shake
Big hits and boss events shake the screen. Intensity scales with the event, boss explosions shake more than a regular hit. Fades out smoothly.

### Particle system
Visual feedback for everything that explosions on kills, sparks on hits, dash trails, damage puffs, power-up collect bursts, combo text pop-ups, and a full-screen particle burst on zone transitions.

---

## Known Bugs
No bugs were found during development and testing.

---

## Unfinished Works
All planned features have been completed.

---

## External sources
Acknowledge to:
- Pygame documentation and examples, https://www.pygame.org/docs/ [game framework reference]
- Matplotlib documentation, https://matplotlib.org/stable/index.html [stats visualization]
- Cover / title background image, bg_title.png — Image generated by AI (Gemini)