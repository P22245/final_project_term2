import csv
import json
import os
from datetime import datetime
import pygame
from config import *

_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_DIR, "gameplay_stats.csv")
SCORES_PATH = os.path.join(_DIR, "highscores.json")

FIELDNAMES = ["bacteria_killed","final_body_hp","waves_survived","infection_spread_count","result","perk"]

class StatsTracker:
    MAX_LEADERBOARD = 10
    def __init__(self, player_name="Player", perk_name=""):
        self.player_name = player_name or "Player"
        self.perk_name   = perk_name

        # 5 features
        self.bacteria_killed = 0
        self.waves_survived = 0
        self.infection_spread_count = 0

        # score + combo
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self._last_kill = -COMBO_WINDOW_MS
        self._combo_window_mult = 1.0

        # immune memory
        self._mem = {}
        self._cur_bonus = 0.0
        self._cur_combo = frozenset()
        self._new_mutations = []

        self._ensure_csv()

    # Score & combo
    def on_kill(self):
        now = pygame.time.get_ticks()
        window = int(COMBO_WINDOW_MS * self._combo_window_mult)
        if now - self._last_kill <= window:
            self.combo += 1
        else:
            self.combo = 1
        self._last_kill = now
        self.max_combo = max(self.max_combo, self.combo)
        mult = 1 + (self.combo - 1) * 0.25
        points = int(SCORE_PER_KILL * mult)
        self.score += points
        return points

    def on_boss_kill(self):
        self.score += SCORE_PER_BOSS_KILL
        self.combo = min(self.combo + 3, 20)
        self.max_combo = max(self.max_combo, self.combo)
        self._last_kill = pygame.time.get_ticks()
        return SCORE_PER_BOSS_KILL

    def on_wave_clear(self, body_hp, body_max):
        pts = SCORE_PER_WAVE + int(SCORE_PER_WAVE * (body_hp / body_max))
        self.score += pts
        return pts

    def combo_ratio(self):
        window = int(COMBO_WINDOW_MS * self._combo_window_mult)
        return max(0.0, 1.0 - (pygame.time.get_ticks() - self._last_kill) / window)

    # Event counters
    def on_bacteria_killed(self):
        self.bacteria_killed += 1

    def on_infection_spread(self):
        self.infection_spread_count += 1

    def on_wave_end(self):
        self.waves_survived += 1

    # Immune memory
    def process_wave_memory(self, wave, mutation_names):
        combo = frozenset(mutation_names)
        self._cur_combo = combo
        all_seen = {m for k in self._mem for m in k}
        self._new_mutations = [m for m in mutation_names if m not in all_seen]

        if combo not in self._mem:
            bonus = self._partial_memory(combo)
            is_new = True
            self._mem[combo] = {"encounters": 1}
        else:
            self._mem[combo]["encounters"] += 1
            bonus = min(0.75, self._mem[combo]["encounters"] * 0.15)
            is_new = False

        self._cur_bonus = bonus
        enc = self._mem[combo]["encounters"]
        return {"bonus":bonus,"is_new_combo":is_new,"new_mutations":self._new_mutations,"encounters":enc}

    def _partial_memory(self, combo):
        best = 0.0
        for k, rec in self._mem.items():
            overlap = len(combo & k) / max(1, len(combo | k))
            best = max(best, overlap * rec["encounters"] * 0.15)
        penalty = len(self._new_mutations) * 0.10
        return max(0.0, min(0.75, best - penalty))

    @property
    def damage_multiplier(self):
        return 1.0 + self._cur_bonus

    @property
    def current_bonus_pct(self):
        return int(self._cur_bonus * 100)

    @property
    def memory_encounter_count(self):
        rec = self._mem.get(self._cur_combo)
        return rec["encounters"] if rec else 0

    def has_memory(self):
        return self._cur_bonus > 0.01

    def save(self, final_body_hp, result, wave):
        row = {"bacteria_killed":self.bacteria_killed,"final_body_hp":round(final_body_hp, 1),"waves_survived":self.waves_survived,
            "infection_spread_count":self.infection_spread_count,"result":result,"perk":self.perk_name}
        write_header = not os.path.exists(CSV_PATH)
        with open(CSV_PATH,"a",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if write_header:
                w.writeheader()
            w.writerow(row)

    def get_summary(self):
        return {"bacteria_killed":self.bacteria_killed,"waves_survived":self.waves_survived,"infection_spread_count": self.infection_spread_count,
            "score":self.score,"max_combo":self.max_combo}

    # Leaderboard
    def save_to_leaderboard(self, result, wave):
        data = self._load_scores()
        data.append({"name":self.player_name,"score":self.score,"wave":wave,"combo":self.max_combo,"result": result})
        data.sort(key=lambda e: e["score"],reverse=True)
        with open(SCORES_PATH, "w") as f:
            json.dump(data[:self.MAX_LEADERBOARD],f,indent=2)

    @staticmethod
    def load_leaderboard():
        return StatsTracker._load_scores()

    @staticmethod
    def _load_scores():
        if not os.path.exists(SCORES_PATH):
            return []
        try:
            with open(SCORES_PATH) as f:
                return json.load(f)
        except Exception:
            return []

    def _ensure_csv(self):
        if not os.path.exists(CSV_PATH):
            with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()
