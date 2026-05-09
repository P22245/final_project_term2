import pygame
import math
from config import *

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ("Tahoma", "TH Sarabun New", "Leelawadee UI", "consolas", "arial"):
        f = pygame.font.SysFont(name, size, bold=bold)
        if f:
            return f
    return pygame.font.Font(None, size)


def _alpha_rect(surf, x, y, w, h, fill, alpha=180, radius=8):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*fill[:3], alpha), (0, 0, w, h), border_radius=radius)
    surf.blit(s, (x, y))


def _border_rect(surf, x, y, w, h, fill, border, alpha=180, border_alpha=220, radius=8):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*fill[:3], alpha),(0,0,w,h), border_radius=radius)
    pygame.draw.rect(s, (*border[:3], border_alpha), (0,0,w,h), 2, border_radius=radius)
    surf.blit(s, (x, y))


def _gradient_bar(surf, x, y, w, h, ratio, col_full, col_empty=(40, 40, 55), radius=5):
    pygame.draw.rect(surf, col_empty, (x, y, w, h), border_radius=radius)
    fw = int(w * max(0, min(1, ratio)))
    if fw > 2:
        pygame.draw.rect(surf, col_full, (x, y, fw, h), border_radius=radius)


def _blit_text(surf, font, text: str, x: int, y: int, color: tuple,
               shadow: bool = True, shadow_col: tuple = (0, 0, 0),
               shadow_offset: int = 2, outline: bool = False):
    if outline:
        for dx, dy in ((-1,-1),(1,-1),(-1,1),(1,1),(0,-1),(0,1),(-1,0),(1,0)):
            surf.blit(font.render(text, True, shadow_col), (x+dx, y+dy))
    elif shadow:
        surf.blit(font.render(text, True, shadow_col), (x+shadow_offset, y+shadow_offset))
    surf.blit(font.render(text, True, color), (x, y))


class HUD:
    def __init__(self, sw: int, sh: int):
        self.sw, self.sh = sw, sh
        self.font_xl = _font(48, True)
        self.font_lg = _font(26, True)
        self.font_md = _font(18)
        self.font_sm = _font(14)
        self.font_xs = _font(12)
        self.font_title = _font(38, True)

        self._wave_flash_until = 0
        self._wave_text = ""
        self._wave_subtext = ""
        self._has_boss = False
        self._zone_index = 0 
        self._mutation_lines: list[tuple[str, int]] = []
        self._memory_lines: list[tuple[str, int]] = []
        self._score_pops: list[tuple[str, float, float, int]] = []
        self._powerup_msg: list[tuple[str, int]] = []
        self._notify_msg: list[tuple[str, int, tuple]] = []

    # Public API
    def flash_wave(self, wave: int, mutations: list, now: int,zone_index: int = 0, has_boss: bool = False,memory_info: dict = None):
        zone_name = ORGAN_ZONES[zone_index]["name"]
        self._zone_index = zone_index   # save for badge use
        self._wave_text = (f"Wave {wave} / {TOTAL_WAVES}"+ ("   ★ BOSS ★" if has_boss else ""))
        self._wave_subtext = f"Zone {zone_index+1}/{TOTAL_ZONES}  ·  {zone_name}"
        self._wave_flash_until = now + WAVE_FLASH_DURATION
        self._has_boss = has_boss

        self._mutation_lines = []
        if mutations:
            self._mutation_lines.append(("[ MUTATION ACTIVE ]", now + MUTATION_FLASH_DURATION))
            for m in mutations:
                self._mutation_lines.append((f"  ›  {m}", now + MUTATION_FLASH_DURATION))

        self._memory_lines = []
        if memory_info:
            bonus = memory_info.get("bonus", 0)
            if bonus > 0:
                pct = int(bonus * 100)
                self._memory_lines = [("[ IMMUNE MEMORY ACTIVE ]",   now + MUTATION_FLASH_DURATION),(f"  Antibody boost  +{pct}%", now + MUTATION_FLASH_DURATION),]
                new_mut = memory_info.get("new_mutations", [])
                if new_mut:
                    self._memory_lines.append(
                        (f"  New variant: {', '.join(new_mut)}",
                         now + MUTATION_FLASH_DURATION))
            elif memory_info.get("is_new_combo"):
                self._memory_lines = [("[ NEW PATHOGEN — no memory ]",now + MUTATION_FLASH_DURATION),("  Body is learning...",now + MUTATION_FLASH_DURATION),]

    def score_pop(self, text: str, x: float, y: float, now: int):
        self._score_pops.append((text, x, y, now + 1200))

    def powerup_notify(self, msg: str, now: int):
        self._powerup_msg.append((msg, now + 2500))

    def notify(self, msg: str, now: int, color: tuple = CYAN):
        self._notify_msg.append((msg, now + 2000, color))

    # Main gameplay HUD
    def draw(self, surface, player, body, wave: int, tracker,
             now: int, player_name: str = "", body_cells=None,
             chosen_perk: dict = None, zone_index: int = 0):
        self._zone_index = zone_index
        self._draw_body_bar(surface,body, now)
        self._draw_wbc_bar(surface,player)
        self._draw_dash(surface,player, now)
        self._draw_score(surface,tracker)
        self._draw_combo(surface, tracker, now)
        self._draw_powerup_timers(surface, player, now)
        self._draw_wave_badge(surface, wave, now, chosen_perk)
        self._draw_player_name(surface, player_name)
        self._draw_stats_card(surface, tracker)
        self._draw_body_cell_status(surface, body_cells, now)
        self._draw_immune_memory_badge(surface, tracker)
        self._draw_controls_hint(surface)
        self._draw_wave_flash(surface, now)
        self._draw_mutation_tags(surface, now)
        self._draw_memory_flash(surface, now)
        self._draw_score_pops(surface, now)
        self._draw_powerup_msgs(surface, now)
        self._draw_notifications(surface, now)

    # Body HP bar (top-center)
    def _draw_body_bar(self, surface, body, now):
        bw, bh = 420, 24
        bx = self.sw // 2 - bw // 2
        by = 10
        _alpha_rect(surface, bx-3, by-3, bw+6, bh+6, (0, 0, 0), 120, 12)
        _alpha_rect(surface, bx, by, bw, bh, (50, 10, 10), 220, 10)

        fw  = int(bw * body.hp_ratio)
        col = (HEALTH_BAR_HIGH if body.hp_ratio > 0.5 else
               HEALTH_BAR_MED  if body.hp_ratio > 0.25 else HEALTH_BAR_LOW)

        if fw > 2:
            for xi in range(fw):
                t = xi / max(1, fw)
                r = int(col[0] * (0.7 + 0.3 * t))
                g = int(col[1] * (0.7 + 0.3 * t))
                b = int(col[2] * (0.7 + 0.3 * t))
                pygame.draw.rect(surface, (r, g, b), (bx + xi, by, 1, bh))
            shine = pygame.Surface((fw, bh // 3), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 30))
            surface.blit(shine, (bx, by))
            pygame.draw.rect(surface, col, (bx, by, fw, bh), border_radius=10)

        border_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(border_s, (*col[:3], 120), (0, 0, bw, bh), 2, border_radius=10)
        surface.blit(border_s, (bx, by))

        if body.hp_ratio < 0.25:
            pulse = int(abs(math.sin(now * 0.006)) * 180)
            ov    = pygame.Surface((bw+8, bh+8), pygame.SRCALPHA)
            pygame.draw.rect(ov, (*HEALTH_BAR_LOW, pulse), (0, 0, bw+8, bh+8), 3, border_radius=12)
            surface.blit(ov, (bx-4, by-4))

        lbl_text = f"BODY  {int(body.hp)} / {body.max_hp}"
        _blit_text(surface, self.font_sm, lbl_text,
                   bx + bw//2 - self.font_sm.size(lbl_text)[0]//2, by + 4,
                   WHITE, shadow=True, shadow_col=(0,0,0), shadow_offset=1)

    # WBC HP bar (top-left)
    def _draw_wbc_bar(self, surface, player):
        bw, bh = 170, 16
        bx, by = 16, 16
        _alpha_rect(surface, bx-2, by-2, bw+4, bh+4, (0, 0, 0), 100, 7)
        _alpha_rect(surface, bx, by, bw, bh, (20, 20, 50), 200, 5)
        fw  = int(bw * player.hp_ratio)
        col = PURPLE if player.shielded else WBC_COLOR
        if fw > 2:
            pygame.draw.rect(surface, col, (bx, by, fw, bh), border_radius=5)
            shine = pygame.Surface((fw, bh//2), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 25))
            surface.blit(shine, (bx, by))
        border_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(border_s, (*col[:3], 100), (0, 0, bw, bh), 1, border_radius=5)
        surface.blit(border_s, (bx, by))
        _blit_text(surface, self.font_xs, f"WBC  {player.hp} / {player.max_hp}",
                   bx, by + bh + 3, (180, 210, 255),
                   outline=True, shadow_col=(0,0,0))

    # Dash cooldown arc (top-left below WBC) 
    def _draw_dash(self, surface, player, now):
        cx, cy, r = 32, 108, 18
        ratio = player.dash_cooldown_ratio
        ready = ratio >= 1.0

        _alpha_rect(surface, cx-r-2, cy-r-2, (r+2)*2, (r+2)*2, (0, 0, 0), 80, r+2)
        pygame.draw.circle(surface, (30, 30, 55), (cx, cy), r, 3)

        if ratio > 0.01:
            pts   = [(cx, cy)]
            steps = max(3, int(ratio * 36))
            for i in range(steps + 1):
                a = -math.pi/2 + (i / steps) * ratio * 2 * math.pi
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            if len(pts) >= 3:
                col = CYAN if ready else (50, 120, 160)
                pygame.draw.polygon(surface, col, pts)

        ring_col = (100, 240, 220) if ready else (40, 80, 110)
        pygame.draw.circle(surface, ring_col, (cx, cy), r, 2)
        _blit_text(surface, self.font_xs, "DASH",
                   cx - self.font_xs.size("DASH")[0]//2, cy + r + 3,
                   (100, 240, 220) if ready else (60, 90, 110),
                   outline=True, shadow_col=(0, 0, 0))

    # Score (center below body bar)
    def _draw_score(self, surface, tracker):
        score_text = f"  {tracker.score:,}"
        x = self.sw//2 - self.font_lg.size(score_text)[0]//2
        glow = pygame.Surface((self.font_lg.size(score_text)[0] + 24,self.font_lg.get_height() + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow, (180, 140, 0, 22), (0, 0, glow.get_width(), glow.get_height()), border_radius=6)
        surface.blit(glow, (x - 12, 37))
        _blit_text(surface, self.font_lg, score_text, x, 40,GOLD, shadow=True, shadow_col=(60, 40, 0), shadow_offset=2)

    # Combo (bottom-right)
    def _draw_combo(self, surface, tracker, now):
        if tracker.combo < 2:
            return
        c = tracker.combo
        mult  = 1 + (c - 1) * 0.25
        ratio = tracker.combo_ratio()
        pw, ph = 190, 50
        px = self.sw - pw - 14
        py = self.sh - ph - 36

        glow_alpha = int(30 + 20 * abs(math.sin(now * 0.004)))
        glow = pygame.Surface((pw+8, ph+8), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*GOLD[:3], glow_alpha), (0, 0, pw+8, ph+8), border_radius=12)
        surface.blit(glow, (px-4, py-4))

        _border_rect(surface, px, py, pw, ph,fill=(18, 10, 35), border=GOLD, alpha=210, radius=10)

        combo_text = f"COMBO  x{c}   ×{mult:.2f}"
        tw = self.font_sm.size(combo_text)[0]
        _blit_text(surface, self.font_sm, combo_text,px + pw//2 - tw//2, py + 7,GOLD, shadow=True, shadow_col=(60, 40, 0), shadow_offset=1)

        bw, bh = pw - 22, 6
        bx, by = px + 11, py + ph - bh - 9
        _alpha_rect(surface, bx, by, bw, bh, (30, 15, 60), 200, 3)
        fw = int(bw * ratio)
        if fw > 0:
            pygame.draw.rect(surface, GOLD if ratio > 0.5 else ORANGE,(bx, by, fw, bh), border_radius=3)

    # Power-up timers (top-left)
    def _draw_powerup_timers(self, surface, player, now):
        TIMER_META = {"rapid_fire":("[>>] RAPID",  (80,  220, 200)),"speed_boost":("[->] SPEED",  (240, 200, 50)),
            "shield":("[ S] SHIELD", (160, 80,  220))}
        x, y = 16, 146
        for name, exp in player.active_powerup_timers():
            if name not in TIMER_META:
                continue
            label, color = TIMER_META[name]
            remaining = (exp - now) / 1000
            bw, bh = 136, 5
            _border_rect(surface, x-4, y-17, bw+8, bh+24,fill=(8, 8, 20), border=color, alpha=160, border_alpha=120, radius=5)
            _alpha_rect(surface, x, y, bw, bh, (20, 20, 40), 200, 2)
            fw = int(bw * min(1.0, remaining / 5.0))
            if fw > 0:
                pygame.draw.rect(surface, color, (x, y, fw, bh), border_radius=2)
            _blit_text(surface, self.font_xs, f"{label}  {remaining:.1f}s",x, y - 14, color, outline=True, shadow_col=(0, 0, 0))
            y += 32

    # Wave + Zone badge (top-right)
    def _draw_wave_badge(self, surface, wave: int, now: int, chosen_perk: dict = None):
        if now > 0 and now < self._wave_flash_until:
            return
        # wave number, which is wrong during boss waves and zone transitions.
        zone_idx = self._zone_index
        zone = ORGAN_ZONES[zone_idx]
        accent = zone["accent"]

        t1 = f"Wave  {wave} / {TOTAL_WAVES}"
        t2 = f"Zone {zone_idx+1}  ·  {zone['name']}"
        t3 = zone["buff"]
        t4 = f"[ {chosen_perk['name']} ]" if chosen_perk else ""

        w1 = self.font_lg.size(t1)[0]
        w2 = self.font_sm.size(t2)[0]
        w3 = self.font_xs.size(t3)[0]
        w4 = self.font_xs.size(t4)[0] if t4 else 0
        extra_h = self.font_xs.get_height() + 4 if t4 else 0

        pw = max(w1, w2, w3, w4) + 28
        ph = (self.font_lg.get_height() + self.font_sm.get_height()+self.font_xs.get_height() + extra_h + 22)
        px = self.sw - pw - 12
        py = 10

        _border_rect(surface, px, py, pw, ph,fill=(8, 8, 20), border=accent, alpha=210, radius=10)
        strip = pygame.Surface((pw, 4), pygame.SRCALPHA)
        pygame.draw.rect(strip, (*accent, 120), (0, 0, pw, 4), border_radius=2)
        surface.blit(strip, (px, py))

        cy = py + 8
        _blit_text(surface, self.font_lg, t1, px + pw//2 - w1//2,cy,YELLOW,shadow=True, shadow_col=(50,40,0))
        cy += self.font_lg.get_height() + 4
        _blit_text(surface, self.font_sm, t2, px + pw//2 - w2//2,cy,accent,shadow=True, shadow_col=(0,0,0))
        cy += self.font_sm.get_height() + 2
        _blit_text(surface, self.font_xs, t3, px + pw//2 - w3//2, cy,GRAY,outline=True, shadow_col=(0,0,0))
        cy += self.font_xs.get_height() + 4
        if t4:
            _blit_text(surface,self.font_xs,t4,px + pw//2 - w4//2, cy,chosen_perk["color"],outline=True, shadow_col=(0,0,0))

    def _draw_player_name(self, surface, name: str):
        if not name:
            return
        _blit_text(surface, self.font_xs, f"[ {name} ]",self.sw - self.font_xs.size(f"[ {name} ]")[0] - 14, 100,(160, 185, 240), outline=True, shadow_col=(0,0,0))

    # Session stats card (bottom-left)
    def _draw_stats_card(self, surface, tracker):
        cw, ch = 218, 92
        cx, cy = 12, self.sh - ch - 32

        _border_rect(surface, cx, cy, cw, ch,fill=(8, 16, 8), border=(40, 160, 60), alpha=215, radius=10)

        hdr = pygame.Surface((cw, 22), pygame.SRCALPHA)
        pygame.draw.rect(hdr, (20, 80, 25, 200), (0, 0, cw, 22), border_radius=6)
        surface.blit(hdr, (cx, cy))
        _blit_text(surface, self.font_xs, "SESSION STATS",cx + cw//2 - self.font_xs.size("SESSION STATS")[0]//2, cy + 4,
                   LIME, outline=True, shadow_col=(0,30,0))

        _blit_text(surface, self.font_xs, "Bacteria killed",cx + 10, cy + 27, (160, 230, 160), outline=True, shadow_col=(0,0,0))
        _blit_text(surface, self.font_lg, str(tracker.bacteria_killed),cx + cw - self.font_lg.size(str(tracker.bacteria_killed))[0] - 10,
                   cy + 24, LIME, shadow=True, shadow_col=(0,50,0))

        div = pygame.Surface((cw - 20, 1), pygame.SRCALPHA)
        div.fill((40, 100, 40, 180))
        surface.blit(div, (cx + 10, cy + 52))

        spreads = tracker.infection_spread_count
        s_col   = RED if spreads > 0 else (60, 130, 60)
        _blit_text(surface, self.font_xs, "Infection spread",cx + 10, cy + 57, (230, 150, 150), outline=True, shadow_col=(0,0,0))
        _blit_text(surface, self.font_lg, str(spreads),cx + cw - self.font_lg.size(str(spreads))[0] - 10, cy + 55,
                   s_col, shadow=True, shadow_col=(50,0,0))

    # ── Body cell status (left side, above stats card) ────
    def _draw_body_cell_status(self, surface, body_cells, now: int):
        if not body_cells:
            return
        healthy = sum(1 for c in body_cells if c.state == "S" and c.alive)
        infected = sum(1 for c in body_cells if c.state == "I" and c.alive)
        if healthy + infected == 0:
            return

        cw, ch = 218, 92
        card_top = self.sh - ch - 32
        pw, ph = 218, 46
        px = 12
        py = card_top - ph - 6

        bcol = (200, 80, 0) if infected else (40, 140, 60)
        _border_rect(surface, px, py, pw, ph,fill=(18, 6, 0) if infected else (4, 14, 4),border=bcol, alpha=185, radius=8)

        hs = pygame.Surface((pw, 20), pygame.SRCALPHA)
        hfill = (80, 30, 0, 180) if infected else (10, 60, 15, 180)
        pygame.draw.rect(hs, hfill, (0, 0, pw, 20), border_radius=6)
        surface.blit(hs, (px, py))
        htxt_str = "BODY CELLS" if not infected else "BODY CELLS"
        htxt_col = (255, 160, 60) if infected else (100, 220, 100)
        htxt = self.font_xs.render(htxt_str, True, htxt_col)
        surface.blit(htxt, (px + pw//2 - htxt.get_width()//2, py + 4))

        if infected > 0:
            pulse = int(150 + 105 * abs(math.sin(pygame.time.get_ticks() * 0.007)))
            dot = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot, (255, 120, 0, pulse), (4, 4), 4)
            surface.blit(dot, (px + 10, py + 27))
            inf_lbl = self.font_xs.render(f"{infected} infected  ·  shoot orange dots!",True, (255, 150, 50))
            saf_lbl = self.font_xs.render(f"{healthy} safe", True, (160, 220, 160))
            surface.blit(inf_lbl, (px + 22, py + 24))
            surface.blit(saf_lbl, (px + pw - saf_lbl.get_width() - 8, py + 24))
        else:
            ok_lbl = self.font_xs.render(f"All {healthy} cells healthy", True, (100, 220, 100))
            surface.blit(ok_lbl, (px + pw//2 - ok_lbl.get_width()//2, py + 26))

    # Immune memory badge
    def _draw_immune_memory_badge(self, surface, tracker):
        if tracker is None or not tracker.has_memory():
            return
        bonus_pct = tracker.current_bonus_pct
        enc_count = tracker.memory_encounter_count
        pw, ph = 196, 52
        px = self.sw - pw - 12
        py = 108

        glow = pygame.Surface((pw+10, ph+10), pygame.SRCALPHA)
        pygame.draw.rect(glow, (60, 200, 80, 25), (0, 0, pw+10, ph+10), border_radius=12)
        surface.blit(glow, (px-5, py-5))

        _border_rect(surface, px, py, pw, ph,fill=(4, 18, 4), border=(50, 190, 60), alpha=220, radius=10)

        hs = pygame.Surface((pw, 20), pygame.SRCALPHA)
        pygame.draw.rect(hs, (20, 80, 25, 180), (0, 0, pw, 20), border_radius=6)
        surface.blit(hs, (px, py))
        hdr = self.font_xs.render("IMMUNE MEMORY", True, (100, 255, 110))
        surface.blit(hdr, (px + pw//2 - hdr.get_width()//2, py + 3))

        bw = pw - 24
        bx = px + 12
        by = py + 24
        _alpha_rect(surface, bx, by, bw, 7, (15, 40, 15), 200, 3)
        fw = int(bw * min(1.0, bonus_pct / 75))
        if fw > 0:
            for xi in range(fw):
                t   = xi / max(1, fw)
                col = (int(40 + 40*t), int(180 + 40*t), int(50 + 30*t))
                pygame.draw.rect(surface, col, (bx + xi, by, 1, 7))

        val = self.font_xs.render(f"+{bonus_pct}% damage  ·  seen x{enc_count}", True, (140, 255, 150))
        surface.blit(val, (px + pw//2 - val.get_width()//2, by + 10))

    # Controls hint (bottom-center)
    def _draw_controls_hint(self, surface):
        hint_text = "WASD  ·  Mouse aim  ·  Click / Z  Shoot  ·  SPACE  Dash  ·  M  Mute  ·  ESC  Quit"
        tw = self.font_xs.size(hint_text)[0]
        pw = tw + 30
        ph = self.font_xs.get_height() + 10
        bx = self.sw//2 - pw//2
        by = self.sh - ph - 4
        _alpha_rect(surface, bx, by, pw, ph, (0, 0, 0), 110, 6)
        _blit_text(surface, self.font_xs, hint_text,self.sw//2 - tw//2, by + 5,(80, 100, 130), outline=True, shadow_col=(0,0,0))

    # Wave flash (center)
    def _draw_wave_flash(self, surface, now):
        if now > self._wave_flash_until:
            return
        alpha = min(255, int((self._wave_flash_until - now) / 700 * 255))
        col = RED    if self._has_boss else YELLOW
        sub_col = ORANGE if self._has_boss else CYAN

        w1 = self.font_lg.size(self._wave_text)[0]
        w2 = self.font_md.size(self._wave_subtext)[0]
        bw = max(w1, w2) + 60
        bh = self.font_lg.get_height() + self.font_md.get_height() + 36
        bx = self.sw//2 - bw//2
        by = self.sh//2 - 120

        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(bg,(0, 0, 0, min(200, alpha)),(0,0,bw,bh), border_radius=14)
        pygame.draw.rect(bg,(*col, min(180, alpha)),(0,0,bw,bh), 2, border_radius=14)
        pygame.draw.rect(bg,(*col, min(alpha, 100)),(0,0,bw,4),border_radius=2)
        surface.blit(bg,(bx,by))

        for text, y_off, tc, sh_col in [(self._wave_text,12,col,(0,0,0)),
            (self._wave_subtext, 12 + self.font_lg.get_height() + 8, sub_col, (0,0,0)),
        ]:
            font = self.font_lg if y_off == 12 else self.font_md
            tw_ = font.size(text)[0]
            sh_s = font.render(text, True, sh_col)
            fg_s = font.render(text, True, tc)
            for surf_r, ox, oy in [(sh_s, 2, 2), (fg_s, 0, 0)]:
                tmp = pygame.Surface(surf_r.get_size(), pygame.SRCALPHA)
                tmp.blit(surf_r, (0, 0))
                tmp.set_alpha(alpha)
                surface.blit(tmp, (self.sw//2 - tw_//2 + ox, by + y_off + oy))

    # Mutation flash
    def _draw_mutation_tags(self, surface, now):
        self._mutation_lines = [(t, e) for t, e in self._mutation_lines if now < e]
        if not self._mutation_lines:
            return
        bw = 320
        bh = len(self._mutation_lines) * 24 + 18
        bx = self.sw//2 - bw//2
        by = self.sh//2 + 30
        _border_rect(surface, bx, by, bw, bh,fill=(22, 5, 40), border=ORANGE, alpha=195, radius=10)
        y = by + 9
        for text, expire in self._mutation_lines:
            alpha = min(255, int((expire - now) / 900 * 255))
            col = ORANGE if "MUTATION" in text else (220, 180, 100)
            sh_s = self.font_sm.render(text, True, (0, 0, 0))
            fg_s = self.font_sm.render(text, True, col)
            tw_ = fg_s.get_width()
            for surf_r, ox, oy in [(sh_s, 2, 2), (fg_s, 0, 0)]:
                tmp = pygame.Surface(surf_r.get_size(), pygame.SRCALPHA)
                tmp.blit(surf_r, (0, 0))
                tmp.set_alpha(alpha)
                surface.blit(tmp, (self.sw//2 - tw_//2 + ox, y + oy))
            y += 24

    def _draw_memory_flash(self, surface, now):
        self._memory_lines = [(t, e) for t, e in self._memory_lines if now < e]
        if not self._memory_lines:
            return
        bw = 360
        bh = len(self._memory_lines) * 24 + 18
        bx = self.sw//2 - bw//2
        by = self.sh//2 + 30 + (len(self._mutation_lines) + 1) * 24 + 16
        _border_rect(surface, bx, by, bw, bh,fill=(3, 20, 4), border=(50, 190, 60), alpha=200, radius=10)
        y = by + 9
        for text, expire in self._memory_lines:
            alpha = min(255, int((expire - now) / 900 * 255))
            col = (90, 255, 100) if ("IMMUNE" in text or "NEW PATHOGEN" in text) else (160, 230, 165)
            txt = self.font_sm.render(text, True, col)
            s = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            s.blit(txt, (0, 0))
            s.set_alpha(alpha)
            surface.blit(s, (self.sw//2 - txt.get_width()//2, y))
            y += 24

    # Score pops
    def _draw_score_pops(self, surface, now):
        alive = []
        for text, x, y, expire in self._score_pops:
            if now > expire:
                continue
            prog = (expire - now) / 1200
            fy = y - (1 - prog) * 44
            alpha = int(255 * prog)
            sh_s = self.font_sm.render(text, True, (0, 0, 0))
            fg_s = self.font_sm.render(text, True, GOLD)
            for surf_r, ox, oy in [(sh_s, 2, 2), (fg_s, 0, 0)]:
                tmp = pygame.Surface(surf_r.get_size(), pygame.SRCALPHA)
                tmp.blit(surf_r, (0, 0))
                tmp.set_alpha(alpha)
                surface.blit(tmp, (int(x) + ox, int(fy) + oy))
            alive.append((text, x, y, expire))
        self._score_pops = alive

    def _draw_powerup_msgs(self, surface, now):
        self._powerup_msg = [(m, e) for m, e in self._powerup_msg if now < e]
        y = self.sh//2 + 65
        for msg, expire in self._powerup_msg:
            alpha = min(255, int((expire - now) / 600 * 255))
            tw_   = self.font_md.size(msg)[0]
            _alpha_rect(surface, self.sw//2 - tw_//2 - 10, y - 3,
                        tw_+20, self.font_md.get_height()+6, (0, 0, 0), 150, 6)
            sh_s = self.font_md.render(msg, True, (0, 30, 40))
            fg_s = self.font_md.render(msg, True, CYAN)
            for surf_r, ox, oy in [(sh_s, 2, 2), (fg_s, 0, 0)]:
                tmp = pygame.Surface(surf_r.get_size(), pygame.SRCALPHA)
                tmp.blit(surf_r, (0, 0))
                tmp.set_alpha(alpha)
                surface.blit(tmp, (self.sw//2 - tw_//2 + ox, y + oy))
            y += 28

    def _draw_notifications(self, surface, now):
        self._notify_msg = [(m, e, c) for m, e, c in self._notify_msg if now < e]
        y = 92
        for msg, expire, color in self._notify_msg:
            alpha = min(255, int((expire - now) / 500 * 255))
            tw_   = self.font_xs.size(msg)[0]
            _alpha_rect(surface, self.sw//2 - tw_//2 - 6, y - 2,
                        tw_ + 12, self.font_xs.get_height() + 4, (0, 0, 0), 120, 4)
            sh_s = self.font_xs.render(msg, True, (0, 0, 0))
            fg_s = self.font_xs.render(msg, True, color)
            for surf_r, ox, oy in [(sh_s, 1, 1), (fg_s, 0, 0)]:
                tmp = pygame.Surface(surf_r.get_size(), pygame.SRCALPHA)
                tmp.blit(surf_r, (0, 0))
                tmp.set_alpha(alpha)
                surface.blit(tmp, (self.sw//2 - tw_//2 + ox, y + oy))
            y += 18

    # PERK SELECTION SCREEN
    def draw_perk_screen(self, surface, perks: list, selected: int,player_name: str, now: int):
        surface.fill((5, 3, 12))
        for i in range(self.sh):
            t = i / self.sh
            pygame.draw.line(surface, (int(5+t*6), int(3+t*4), int(12+t*18)),(0, i), (self.sw, i))

        for i in range(20):
            px_ = (i * 397 + now // 20) % self.sw
            py_ = (i * 251 + now // 35) % self.sh
            a  = int(15 + 12 * math.sin(now * 0.001 + i * 0.9))
            ds = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(ds, (*perks[selected]["color"], max(0, a)), (2, 2), 2)
            surface.blit(ds, (px_, py_))

        title_font = _font(38, True)
        title = title_font.render("CHOOSE YOUR LOADOUT", True, (200, 210, 255))
        surface.blit(title, (self.sw//2 - title.get_width()//2, 28))

        if player_name:
            sub = _font(16).render(f"Welcome, {player_name}", True, (120, 140, 190))
            surface.blit(sub, (self.sw//2 - sub.get_width()//2, 76))

        n_perks = len(perks)
        card_w = 220
        card_h = 230
        gap = 22
        total_w = n_perks * card_w + (n_perks - 1) * gap
        start_x = self.sw//2 - total_w//2
        card_y = 108

        for i, perk in enumerate(perks):
            cx = start_x + i * (card_w + gap)
            col = perk["color"]
            is_sel = (i == selected)

            if is_sel:
                pulse = 0.5 + 0.5 * math.sin(now * 0.005)
                for gr, ga in [(card_w//2+20, int(30*pulse)), (card_w//2, int(50*pulse))]:
                    gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (*col, ga), (gr, gr), gr)
                    surface.blit(gs, (cx + card_w//2 - gr, card_y + card_h//2 - gr))

            bg_alpha = 230 if is_sel else 160
            _alpha_rect(surface, cx, card_y, card_w, card_h, (12, 10, 25), bg_alpha, 14)

            border_alpha = 240 if is_sel else 80
            border_s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            border_w = 3 if is_sel else 1
            pygame.draw.rect(border_s, (*col, border_alpha),(0, 0, card_w, card_h), border_w, border_radius=14)
            surface.blit(border_s, (cx, card_y))

            strip_h = 5
            strip_s = pygame.Surface((card_w, strip_h), pygame.SRCALPHA)
            pygame.draw.rect(strip_s, (*col, 200 if is_sel else 80),(0, 0, card_w, strip_h), border_radius=3)
            surface.blit(strip_s, (cx, card_y))

            tag_font = _font(11, True)
            tag = tag_font.render(perk["tag"], True, col)
            tag_bg = pygame.Surface((tag.get_width()+14, tag.get_height()+6), pygame.SRCALPHA)
            pygame.draw.rect(tag_bg, (*col, 40),  (0, 0, tag.get_width()+14, tag.get_height()+6), border_radius=4)
            pygame.draw.rect(tag_bg, (*col, 120), (0, 0, tag.get_width()+14, tag.get_height()+6), 1, border_radius=4)
            surface.blit(tag_bg, (cx + card_w//2 - (tag.get_width()+14)//2, card_y + 12))
            surface.blit(tag, (cx + card_w//2 - tag.get_width()//2, card_y + 15))

            name_col = col if is_sel else (180, 185, 210)
            name_font = _font(20, True)
            name_lbl = name_font.render(perk["name"], True, name_col)
            surface.blit(name_lbl, (cx + card_w//2 - name_lbl.get_width()//2, card_y + 42))

            div_s = pygame.Surface((card_w - 30, 1), pygame.SRCALPHA)
            div_s.fill((*col, 60 if is_sel else 30))
            surface.blit(div_s, (cx + 15, card_y + 70))

            stat_font = _font(13)
            for j, stat in enumerate(perk["stats"]):
                sc = (180, 230, 180) if is_sel else (120, 130, 150)
                dot = _font(13).render("›", True, col)
                stl = stat_font.render(stat, True, sc)
                surface.blit(dot, (cx + 18, card_y + 80 + j * 22))
                surface.blit(stl, (cx + 32, card_y + 80 + j * 22))

            desc_col = (200, 205, 225) if is_sel else (100, 105, 125)
            desc_font = _font(12)
            words = perk["desc"].split()
            lines_ = []
            line_  = ""
            for w in words:
                test = (line_ + " " + w).strip()
                if desc_font.size(test)[0] < card_w - 28:
                    line_ = test
                else:
                    if line_:
                        lines_.append(line_)
                    line_ = w
            if line_:
                lines_.append(line_)
            dy_ = card_y + 152
            for dl in lines_:
                dl_s = desc_font.render(dl, True, desc_col)
                surface.blit(dl_s, (cx + card_w//2 - dl_s.get_width()//2, dy_))
                dy_ += 16

            if is_sel:
                sel_lbl = _font(13, True).render("SELECTED", True, col)
                surface.blit(sel_lbl, (cx + card_w//2 - sel_lbl.get_width()//2, card_y + card_h - 26))
            else:
                idx_lbl = _font(13).render(f"{i+1}", True, (70, 75, 100))
                surface.blit(idx_lbl, (cx + card_w//2 - idx_lbl.get_width()//2, card_y + card_h - 24))

        hint_y = card_y + card_h + 24
        nav = _font(15).render("◄ / A      Arrow keys to select      D / ►", True, (90, 100, 140))
        confirm = _font(17, True).render("ENTER  to confirm", True, perks[selected]["color"])
        back = _font(13).render("BACKSPACE  to go back", True, (60, 70, 95))
        surface.blit(nav,(self.sw//2 - nav.get_width()//2,hint_y))
        surface.blit(confirm,(self.sw//2 - confirm.get_width()//2,hint_y + 28))
        surface.blit(back,(self.sw//2 - back.get_width()//2,hint_y + 54))


    # START SCREEN
    def draw_start_screen(self, surface, player_name: str,chosen_perk: dict, now: int):
        surface.fill((5, 3, 12))
        for i in range(self.sh):
            t = i / self.sh
            pygame.draw.line(surface, (int(5+t*8), int(3+t*5), int(12+t*20)),(0, i), (self.sw, i))

        col = chosen_perk["color"] if chosen_perk else YELLOW
        pulse = 0.5 + 0.5 * math.sin(now * 0.004)
        pulse2 = 0.6 + 0.4 * abs(math.sin(now * 0.003))

        # Title
        title_font = _font(58, True)
        title = title_font.render("CELL WARS", True, (90, 220, 255))
        gx = self.sw//2 - title.get_width()//2
        gy = 55
        for gr, ga in [(110, 20), (75, 35), (48, 55)]:
            gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (30, 100, 200, ga), (gr, gr), gr)
            surface.blit(gs, (gx + title.get_width()//2 - gr, gy + title.get_height()//2 - gr))
        surface.blit(title, (gx, gy))

        # Player name
        name_y = gy + title.get_height() + 12
        if player_name:
            pl = _font(30, True).render(f"Player :  {player_name}", True, (180, 210, 255))
            surface.blit(pl, (self.sw//2 - pl.get_width()//2, name_y))

        # card layout
        pad = 24
        cw = 340
        ctrl_w  = 400
        total_w = cw + pad + ctrl_w
        start_x = self.sw//2 - total_w//2
        cards_y = name_y + 70

        # Perk card
        ch  = 280
        cx_ = start_x
        cy_ = cards_y

        for gr, ga in [(cw//2 + 20, int(18*pulse)), (cw//2, int(35*pulse))]:
            gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*col, ga), (gr, gr), gr)
            surface.blit(gs, (cx_ + cw//2 - gr, cy_ + ch//2 - gr))

        _border_rect(surface, cx_, cy_, cw, ch,fill=(12, 10, 25), border=col, alpha=235, radius=14)

        hs = pygame.Surface((cw, 32), pygame.SRCALPHA)
        pygame.draw.rect(hs, (*col, 70), (0, 0, cw, 32), border_radius=8)
        surface.blit(hs, (cx_, cy_))
        tag = _font(13, True).render(chosen_perk["tag"] if chosen_perk else "", True, col)
        surface.blit(tag, (cx_ + cw//2 - tag.get_width()//2, cy_ + 9))

        pn = _font(26, True).render(chosen_perk["name"] if chosen_perk else "—", True, col)
        surface.blit(pn, (cx_ + cw//2 - pn.get_width()//2, cy_ + 42))

        dv = pygame.Surface((cw - 30, 1), pygame.SRCALPHA)
        dv.fill((*col, 60))
        surface.blit(dv, (cx_ + 15, cy_ + 80))

        if chosen_perk:
            for j, stat in enumerate(chosen_perk["stats"]):
                dot = _font(15, True).render(">", True, col)
                stl = _font(15).render(stat, True, (190, 235, 190))
                surface.blit(dot, (cx_ + 22, cy_ + 92 + j * 30))
                surface.blit(stl, (cx_ + 42, cy_ + 92 + j * 30))

        lbl = _font(18, True).render("YOUR PERK  (random)", True, (220, 225, 255))
        surface.blit(lbl, (cx_ + cw//2 - lbl.get_width()//2, cy_ + ch - 35))

        # Controls card
        controls = [("WASD / Arrows","Move"),
            ("Mouse + Click","Aim and shoot"),
            ("Z key","Alternative fire"),
            ("SPACE","Dash  —  invincibility burst"),
            ("M","Toggle sound on / off"),
            ("P","Pause / Resume"),
            ("V","Open Stats window"),
            ("ESC","Quit game"),]
        row_h = 28
        c_pad = 14
        ctrl_h = 34 + len(controls) * row_h + c_pad * 2
        ctrl_x = start_x + cw + pad
        ctrl_y = cards_y

        _border_rect(surface, ctrl_x, ctrl_y, ctrl_w, ctrl_h,fill=(10, 10, 28), border=(60, 80, 150), alpha=220, radius=12)

        hdr_s = pygame.Surface((ctrl_w, 34), pygame.SRCALPHA)
        pygame.draw.rect(hdr_s, (20, 30, 85, 210), (0, 0, ctrl_w, 34), border_radius=8)
        surface.blit(hdr_s, (ctrl_x, ctrl_y))
        hdr_lbl = _font(14, True).render("CONTROLS", True, (130, 160, 230))
        surface.blit(hdr_lbl, (ctrl_x + ctrl_w//2 - hdr_lbl.get_width()//2, ctrl_y + 9))

        row_y = ctrl_y + 34 + c_pad
        for key, desc in controls:
            k_s = _font(15, True).render(key,  True, (190, 210, 255))
            d_s = _font(15, True).render(desc, True, (210, 220, 240))
            surface.blit(k_s, (ctrl_x + 18, row_y))
            surface.blit(d_s, (ctrl_x + 178, row_y))
            row_y += row_h

        # ENTER button
        btn_y = max(cy_ + ch, ctrl_y + ctrl_h) + 32
        start_lbl = _font(26, True).render("ENTER  —  Start Game", True,tuple(int(c * pulse2) for c in col))
        bw_ = start_lbl.get_width() + 64
        bx_ = self.sw//2 - bw_//2
        _border_rect(surface, bx_, btn_y - 10, bw_, start_lbl.get_height() + 22,fill=(10, 15, 30), border=col, alpha=195, radius=12)
        surface.blit(start_lbl, (self.sw//2 - start_lbl.get_width()//2, btn_y))

        reroll = _font(20).render("[R]  Reroll perk", True, (110, 140, 110))
        surface.blit(reroll, (self.sw//2 - reroll.get_width()//2, btn_y + 56))

        # Stats button
        stats_lbl = _font(17, True).render("[V]  Stats", True, (100, 200, 255))
        sb_w = stats_lbl.get_width() + 26
        sb_h = stats_lbl.get_height() + 14
        sb_x = self.sw - sb_w - 14
        sb_y = 10
        sb = pygame.Surface((sb_w, sb_h), pygame.SRCALPHA)
        pygame.draw.rect(sb, (10, 30, 55, 215),  (0, 0, sb_w, sb_h), border_radius=8)
        pygame.draw.rect(sb, (50, 155, 225, 210), (0, 0, sb_w, sb_h), 2, border_radius=8)
        surface.blit(sb, (sb_x, sb_y))
        surface.blit(stats_lbl, (sb_x + 13, sb_y + 7))
        return pygame.Rect(sb_x, sb_y, sb_w, sb_h)


    # WIN / GAME OVER
    def draw_win_screen(self, surface, tracker, player_name: str,chosen_perk: dict = None):
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        title = _font(36, True).render("[ BODY SAVED ]", True, GOLD)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 90))

        sub = _font(17).render(f"All {TOTAL_ZONES} organ zones cleared!", True, CYAN)
        surface.blit(sub, (self.sw//2 - sub.get_width()//2, 138))

        if player_name:
            pc  = chosen_perk["color"] if chosen_perk else YELLOW
            pid = f"  [ {chosen_perk['name']} ]" if chosen_perk else ""
            nl  = _font(16).render(f"{player_name}{pid}", True, pc)
            surface.blit(nl, (self.sw//2 - nl.get_width()//2, 166))

        sc = _font(28, True).render(f"{tracker.score:,}", True, GOLD)
        surface.blit(_font(16).render("SCORE", True, (160, 140, 60)),
                     (self.sw//2 - _font(16).size("SCORE")[0]//2, 196))
        surface.blit(sc, (self.sw//2 - sc.get_width()//2, 216))

        rows = [("Bacteria Killed",tracker.bacteria_killed,LIME),("Waves Survived",tracker.waves_survived,CYAN),
            ("Max Combo",tracker.max_combo,GOLD),("Spreads",tracker.infection_spread_count,RED)]
        self._draw_result_rows(surface, rows, 258)
        self._draw_result_buttons(surface,[("[R] Again", HEALTH_BAR_HIGH), ("[V] Stats", CYAN), ("[L] Scores", GOLD),
             ("[N] Name",  YELLOW),("[ESC] Quit", GRAY)],start_y=360, spacing=130)

    def draw_game_over(self, surface, tracker, result: str,player_name: str = "", chosen_perk: dict = None):
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        text  = "[ BODY OVERWHELMED ]"   if result == "loss" else "[ SESSION ENDED ]"
        color = RED                      if result == "loss" else HEALTH_BAR_HIGH
        title = _font(32, True).render(text, True, color)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 130))

        if player_name:
            pc  = chosen_perk["color"] if chosen_perk else YELLOW
            pid = f"  [ {chosen_perk['name']} ]" if chosen_perk else ""
            nl  = _font(16).render(f"{player_name}{pid}", True, pc)
            surface.blit(nl, (self.sw//2 - nl.get_width()//2, 174))

        sc = _font(28, True).render(f"{tracker.score:,}", True, GOLD)
        surface.blit(_font(15).render("SCORE", True, (150, 130, 50)),(self.sw//2 - _font(15).size("SCORE")[0]//2, 198))
        surface.blit(sc, (self.sw//2 - sc.get_width()//2, 216))

        rows = [("Bacteria Killed",tracker.bacteria_killed,LIME),("Waves Survived",tracker.waves_survived,CYAN),
            ("Max Combo",tracker.max_combo,GOLD),("Infection Spreads",tracker.infection_spread_count,RED)]
        self._draw_result_rows(surface, rows, 270)
        self._draw_result_buttons(surface,[("[R] Again", HEALTH_BAR_HIGH), ("[V] Stats", CYAN), ("[L] Scores", GOLD),
             ("[N] Name",  YELLOW),("[ESC] Quit", GRAY)],start_y=386, spacing=126)

    def _draw_result_rows(self, surface, rows: list, start_y: int):
        fw = 340
        fx = self.sw//2 - fw//2
        _alpha_rect(surface, fx, start_y - 6, fw, len(rows)*26 + 12, (10, 10, 25), 180, 10)
        y = start_y
        for label, val, col in rows:
            lbl = _font(15).render(f"{label}", True, (160, 165, 190))
            val_s = _font(15, True).render(str(val), True, col)
            surface.blit(lbl,(fx + 16, y))
            surface.blit(val_s,(fx + fw - val_s.get_width() - 16, y))
            y += 26

    def _draw_result_buttons(self, surface, buttons: list,start_y: int, spacing: int):
        total_w = len(buttons) * spacing - (spacing - 100)
        bx      = self.sw//2 - total_w//2
        for i, (lbl, col) in enumerate(buttons):
            bt = _font(15, True).render(lbl, True, col)
            _alpha_rect(surface, bx + i*spacing - 5, start_y - 4,
                        bt.get_width()+10, bt.get_height()+8, (0, 0, 0), 100, 6)
            surface.blit(bt, (bx + i * spacing, start_y))


    # LEADERBOARD
    def draw_leaderboard(self, surface, scores: list):
        import math as _m
        surface.fill((4, 4, 16))
        for i in range(self.sh):
            t = i / self.sh
            pygame.draw.line(surface,(int(4+t*8), int(4+t*4), int(16+t*24)),(0, i), (self.sw, i))

        now = pygame.time.get_ticks()
        for i in range(40):
            sx = (i * 317 + 50) % self.sw
            sy = (i * 211 + 30) % self.sh
            pulse = 0.5 + 0.5 * _m.sin(now * 0.001 + i * 0.8)
            ds = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(ds, (180, 160, 80, int(40 + pulse * 80)), (2, 2), 2)
            surface.blit(ds, (sx, sy))

        def draw_trophy(surf, cx, cy, size=38):
            g1, g2 = (255, 215, 0), (200, 160, 20)
            cup = [(cx-size*.55, cy-size*.6), (cx-size*.55, cy+size*.1),(cx-size*.3,  cy+size*.55),(cx+size*.3,  cy+size*.55),
                (cx+size*.55, cy+size*.1), (cx+size*.55, cy-size*.6)]
            pygame.draw.polygon(surf, g2, [(int(x), int(y)) for x, y in cup])
            pygame.draw.polygon(surf, g1, [(int(x), int(y)) for x, y in cup], 2)
            pygame.draw.arc(surf, g1,(int(cx-size*.85), int(cy-size*.45), int(size*.35), int(size*.5)),_m.radians(30), _m.radians(150), 3)
            pygame.draw.arc(surf, g1,(int(cx+size*.5),  int(cy-size*.45), int(size*.35), int(size*.5)),_m.radians(30), _m.radians(150), 3)
            pygame.draw.rect(surf, g2,(int(cx-size*.1),  int(cy+size*.55), int(size*.2),  int(size*.28)))
            pygame.draw.rect(surf, g1,(int(cx-size*.38), int(cy+size*.83), int(size*.76), int(size*.15)),border_radius=3)

        pw, ph = 820, 490
        px = self.sw//2 - pw//2
        py = self.sh//2 - ph//2 - 10

        for offset, alpha in [(8, 20), (5, 40), (2, 90)]:
            glow = pygame.Surface((pw+offset*2, ph+offset*2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (200, 160, 0, alpha),(0, 0, pw+offset*2, ph+offset*2), border_radius=18+offset)
            surface.blit(glow, (px-offset, py-offset))

        _border_rect(surface, px, py, pw, ph,fill=(6, 6, 22), border=GOLD, alpha=235, radius=16)

        hdr = pygame.Surface((pw, 58), pygame.SRCALPHA)
        pygame.draw.rect(hdr, (28, 22, 4, 230),(0, 0, pw, 58), border_radius=12)
        pygame.draw.rect(hdr, (*GOLD, 200),(0, 0, pw, 58), 2, border_radius=12)
        surface.blit(hdr, (px, py))
        draw_trophy(surface,px + 54,py + 29, 22)
        draw_trophy(surface,px + pw - 54,py + 29, 22)
        title = _font(34,True).render("LEADERBOARD", True, GOLD)
        surface.blit(title,(px + pw//2 - title.get_width()//2, py + 14))

        tx = px + 24
        tw = pw - 48
        col_w = [52, 220, 190, 80, 90, 100]
        col_xs = [tx]
        for w in col_w[:-1]:
            col_xs.append(col_xs[-1] + w)
        hy = py + 72
        _alpha_rect(surface, tx, hy, tw, 28, (18, 18, 55), 170, 6)
        for i, h in enumerate(["#", "Name", "Score", "Wave", "Combo", "Result"]):
            lbl = _font(13, True).render(h, True, (100, 140, 220))
            surface.blit(lbl, (col_xs[i] + 6, hy + 6))

        if not scores:
            msg = _font(17).render("No scores yet — play a game first!", True, GRAY)
            surface.blit(msg, (self.sw//2 - msg.get_width()//2, py + 210))
        else:
            STYLES = {
                1: {"bg": (45,38,0),  "border": (255,215,0),   "text": GOLD,          "badge": "1st"},
                2: {"bg": (28,28,38), "border": (200,200,200), "text": (220,220,220),  "badge": "2nd"},
                3: {"bg": (36,20,4),  "border": (180,120,60),  "text": (200,140,80),   "badge": "3rd"}}
            y     = hy + 32
            row_h = 36
            for rank, entry in enumerate(scores[:8], 1):
                st = STYLES.get(rank, {"bg": (10,10,25) if rank%2==0 else (14,14,32),"border":(35,35,70), "text": (190,195,215), "badge": str(rank)})
                row_s = pygame.Surface((tw, row_h-2), pygame.SRCALPHA)
                pygame.draw.rect(row_s, (*st["bg"], 200),(0, 0, tw, row_h-2), border_radius=6)
                if rank <= 3:
                    pygame.draw.rect(row_s, (*st["border"], 160),(0, 0, tw, row_h-2), 1, border_radius=6)
                surface.blit(row_s, (tx, y))
                if rank == 1:
                    draw_trophy(surface, col_xs[0]+22, y+row_h//2, 14)
                else:
                    badge = _font(13).render(st["badge"], True, st["text"])
                    surface.blit(badge, (col_xs[0]+22-badge.get_width()//2,y+row_h//2-badge.get_height()//2))
                res_str = entry.get("result", "?").upper()
                res_col = (90, 210, 90) if res_str == "WIN" else (210, 70, 70)
                for val, ci, col in [("",0,st["text"]),(entry.get("name","?")[:16],1,st["text"]),
                    (f"{entry.get('score',0):,}",2,st["text"]),(str(entry.get("wave",0)),3,st["text"]),
                    (str(entry.get("combo",0)),4,st["text"]),(res_str,5,res_col),]:
                    if not val:
                        continue
                    lbl = _font(15).render(val, True, col)
                    surface.blit(lbl,(col_xs[ci]+8, y+row_h//2-lbl.get_height()//2))
                if rank <= 3:
                    pygame.draw.rect(surface, st["border"],(tx, y, 4, row_h-2), border_radius=2)
                y += row_h

        back = _font(12).render("ENTER  or  BACKSPACE  to go back", True, (80, 85, 115))
        surface.blit(back, (self.sw//2 - back.get_width()//2, self.sh - 22))