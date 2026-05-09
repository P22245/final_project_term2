import pygame
import random
import math
import os
import sys

from white_blood_cell import WhiteBloodCell
from bacteria         import Bacteria
from boss             import Boss
from body_cell        import BodyCell, spawn_body_cells
from mutation         import roll_mutations, apply_mutations
from particles        import ParticleSystem
from powerup          import PowerUp, maybe_spawn
from body             import Body
from hud              import HUD
from zone_manager     import ZoneManager
from audio            import audio_init, audio_play, audio_toggle_mute
from stats_tracker    import StatsTracker
from stats_window     import open_stats_window, refresh_stats
from config import *

# Game states
S_NAME = "name_input"
S_START = "start"
S_PLAY = "playing"
S_PAUSE = "paused"
S_INTERM = "intermission"
S_BOSS = "boss"
S_ZONE = "zone_transition"
S_OVER = "game_over"
S_WIN = "win"
S_STATS = "stats"
S_BOARD = "leaderboard"

PERKS = [{"id": "medic", "name": "Field Medic", "color": (60, 220, 100), "tag": "SURVIVAL",
        "stats": ["+50 max HP", "Body regen x2", "Regen starts wave 1"],
        "desc": "Built to last. Keeps the body alive when things get messy."},
    {"id": "gunner", "name": "Gunner", "color": (80, 200, 255), "tag": "OFFENSE",
        "stats": ["Fire rate +35%", "Antibody dmg +25%", "Antibody range +30%"],
        "desc": "Glass cannon. Kill faster before they kill the body."},
    {"id": "sprinter", "name": "Sprinter", "color": (240, 200, 50), "tag": "MOBILITY",
        "stats": ["Move speed +30%", "Dash cooldown -35%", "Dash speed +20%"],
        "desc": "Never stop moving. Hard to hit, easy to reposition."},
    {"id": "veteran", "name": "Veteran", "color": (160, 80, 220), "tag": "UTILITY",
        "stats": ["Start with Shield", "Combo window +50%", "I-frames +40%"],
        "desc": "Experienced fighter. Better combos, survives longer."},]


def _font(size, bold=False):
    for name in ("Tahoma", "TH Sarabun New", "Leelawadee UI", "consolas", "arial"):
        f = pygame.font.SysFont(name, size, bold=bold)
        if f:
            return f
    return pygame.font.Font(None, size)


def _hits(a, b):
    return math.hypot(a.x - b.x, a.y - b.y) < a.radius + b.radius


def _apply_perk(perk_id, player, body):
    if perk_id == "medic":
        player.max_hp = PLAYER_MAX_HP + 50
        player.hp = player.max_hp
        body.regen_bonus = 2.0
        player.regen_override = 0

    elif perk_id == "gunner":
        player._shoot_delay_override = int(PLAYER_SHOOT_DELAY * 0.65)
        player.damage_bonus = 1.25
        player.antibody_lifetime_bonus = 1.3

    elif perk_id == "sprinter":
        player.speed_bonus = 1.30
        player.dash_cooldown_bonus = 0.65
        player.dash_speed_bonus = 1.20

    elif perk_id == "veteran":
        player.apply_powerup("shield",8000)
        player.combo_window_bonus = 1.50
        player.iframes_bonus = 1.40


class GameManager:
    BOUNDS = (50, 60, SCREEN_W - 50, SCREEN_H - 50)

    def __init__(self, screen):
        self.screen = screen
        self._surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self.state = S_NAME
        self.player_name  = ""
        self._chosen_perk = None
        self._stats_surf = None
        self._board_from = S_OVER
        self._initialized = False
        self._shake = 0.0
        self._shake_off = (0, 0)
        self._stats_btn_rect = None

        self._font_title = _font(42, True)
        self._font_lg = _font(28, True)
        self._font_md = _font(20)
        self._font_sm = _font(20)

    # New game
    def _init_game(self):
        self.wave = 0
        self.result = ""

        # random perk
        self._chosen_perk = random.choice(PERKS)

        self.player = WhiteBloodCell(SCREEN_W // 2, SCREEN_H // 2)
        self.bacteria = []
        self.boss = None
        self.powerups = []
        self.body_cells = []

        self.body = Body()
        self.zone_mgr = ZoneManager()
        self.hud = HUD(SCREEN_W, SCREEN_H)
        self.tracker = StatsTracker(self.player_name, self._chosen_perk["name"])
        self.particles = ParticleSystem()

        # apply perk realtime
        _apply_perk(self._chosen_perk["id"], self.player, self.body)
        self.tracker._combo_window_mult = self.player.combo_window_bonus

        self._active_mutations = []
        self._interm_start = 0
        self._boss_killed = False
        self._sample_timer = 0
        self._initialized = True

        self.state = S_START

    # Main loop
    def run(self, clock):
        while True:
            dt = clock.tick(FPS) / 1000.0
            now = pygame.time.get_ticks()
            self._events(now)
            self._update(now, dt)
            self._draw(now)

    # Events
    def _events(self, now):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self._quit()

            # Mouse click — Stats button / start screen
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = self._mouse()
                if self._stats_btn_rect and self._stats_btn_rect.collidepoint(mx, my):
                    open_stats_window()

            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key

            # V open stats every page
            if k == pygame.K_v:
                open_stats_window()
                continue

            if self.state == S_NAME:
                if k == pygame.K_ESCAPE:
                    self._quit()
                elif k == pygame.K_RETURN:
                    if not self.player_name.strip():
                        self.player_name = "Player"
                    self._init_game()
                elif k == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif len(self.player_name) < 20 and ev.unicode and ev.unicode.isprintable():
                    self.player_name += ev.unicode
                continue

            if k == pygame.K_m:
                muted = audio_toggle_mute()
                if self._initialized:
                    self.hud.notify("[ Muted ]" if muted else "[ Sound ON ]", now, CYAN)
            if k in (pygame.K_ESCAPE, pygame.K_q):
                self._quit()

            if self.state == S_START:
                if k == pygame.K_RETURN:
                    self._start_wave()
                elif k == pygame.K_r:
                    self._init_game()

            # Pause / Resume
            elif self.state in (S_PLAY, S_BOSS):
                if k == pygame.K_p:
                    self.state = S_PAUSE

            elif self.state == S_PAUSE:
                if k == pygame.K_p:
                    # resume
                    self.state = self._pre_pause_state

            elif self.state in (S_OVER, S_WIN):
                if   k == pygame.K_r: self._init_game()
                elif k == pygame.K_l: self._board_from = self.state; self.state = S_BOARD
                elif k == pygame.K_n: self.player_name = ""; self.state = S_NAME

            elif self.state == S_STATS:
                if k in (pygame.K_RETURN, pygame.K_BACKSPACE):
                    self.state = S_OVER

            elif self.state == S_BOARD:
                if k in (pygame.K_RETURN, pygame.K_BACKSPACE):
                    self.state = self._board_from

    def _quit(self):
        if self._initialized and self.state in (S_PLAY, S_BOSS, S_INTERM, S_ZONE):
            self.tracker.save(self.body.hp, "quit", self.wave)
            self.tracker.save_to_leaderboard("quit", self.wave)
        pygame.quit()
        sys.exit()

    # Update
    def _update(self, now, dt):
        if self.state in (S_NAME, S_START, S_OVER, S_WIN, S_STATS, S_BOARD, S_PAUSE):
            return

        self._shake *= SHAKE_DECAY
        self._shake_off = ((int(random.uniform(-self._shake, self._shake)),int(random.uniform(-self._shake, self._shake))) if self._shake > 0.5 else (0, 0))

        if self.state == S_ZONE:
            if self.zone_mgr.update():
                self.particles.zone_transition_burst(SCREEN_W, SCREEN_H, self.zone_mgr.zone["accent"])
                audio_play("zone")
                self._interm_start = now
                self.state = S_INTERM
            self.particles.update(dt)
            return

        if self.state == S_INTERM:
            self.zone_mgr.update()
            self.particles.update(dt)
            if now - self._interm_start >= WAVE_INTERMISSION:
                self._start_wave()
            return

        # Active gameplay
        keys = pygame.key.get_pressed()
        mouse_pos = self._mouse()
        mouse_btn = pygame.mouse.get_pressed()

        self.player.speed = PLAYER_SPEED * self.zone_mgr.player_speed_mult() * self.player.speed_bonus
        self.player.set_shoot_delay(int(self.player._shoot_delay_override * self.zone_mgr.shoot_delay_mult()))

        dmg_mult = self.zone_mgr.antibody_damage_mult() * self.tracker.damage_multiplier * self.player.damage_bonus
        old_shots = self.player.total_shots

        self.player.handle_input(keys, mouse_pos, mouse_btn, now, self.BOUNDS)
        self.player.update(now)

        regen_start = self.player.regen_override
        if self.wave >= regen_start:
            bonus = max(0, self.wave - regen_start) // 5
            self.player.heal((PLAYER_REGEN_HP_PER_S + bonus * 0.5) * dt)

        if self.player.dash_active:
            self.particles.dash_trail(self.player.x, self.player.y)

        if self.player.total_shots > old_shots:
            audio_play("shoot")

        # Body cells
        for cell in self.body_cells[:]:
            result = cell.update(self.bacteria, self.player.antibodies, now, dt)
            if result == "spawn":
                bac = Bacteria(cell.x, cell.y, self.wave)
                apply_mutations(bac, self._active_mutations)
                self.bacteria.append(bac)
                self.particles.explode(cell.x, cell.y, (255, 100, 0))
                self.hud.notify("Cell hatched! New bacteria!", now, (255, 120, 0))
                self._shake = max(self._shake, 4.0)
                self.body_cells.remove(cell)
            elif result == "destroyed":
                self.tracker.score += 300
                self.hud.score_pop("+300 STOPPED!", cell.x, cell.y - 20, now)
                self.particles.hit_sparks(cell.x, cell.y, (100, 255, 120))
                self.body_cells.remove(cell)
            elif not cell.alive:
                self.body_cells.remove(cell)

        # Bacteria update
        new_bac = []
        for bac in self.bacteria:
            bac.speed = BACTERIA_BASE_SPEED * self.zone_mgr.bacteria_speed_mult() * (1 + (self.wave - 1) * BACTERIA_SPEED_WAVE_MULT)
            bac.update(pygame.Vector2(self.player.x, self.player.y), self.BOUNDS, now, dt,all_bacteria=self.bacteria)
            if bac.has_spread and bac.alive:
                bac.reset_spread(now)
                self.body.take_infection(BACTERIA_DAMAGE)
                self._shake = max(self._shake, SHAKE_PLAYER_HIT)
                self.tracker.on_infection_spread()
            if bac.toxic and bac.alive and bac.collides_with(self.player):
                self.player.take_damage(1)

        # Antibody → bacteria
        for ab in self.player.antibodies[:]:
            ab.damage = int(ANTIBODY_DAMAGE * dmg_mult)
            for bac in self.bacteria:
                if bac.alive and _hits(ab, bac):
                    bac.take_damage(ab.damage)
                    ab.alive = False
                    self.particles.hit_sparks(ab.x, ab.y, bac.color)
                    if not bac.alive:
                        self.particles.explode(bac.x, bac.y, bac.color)
                        pts = self.tracker.on_kill()
                        self.hud.score_pop(f"+{pts}", bac.x, bac.y - 20, now)
                        if self.tracker.combo >= 3 and self.tracker.combo % 3 == 0:
                            self.particles.combo_text_pop(bac.x, bac.y)
                            audio_play("combo")
                        else:
                            audio_play("kill")
                        regen_mult = self.zone_mgr.regen_mult() * getattr(self.body, "regen_bonus", 1.0)
                        self.body.on_bacteria_killed(regen_mult)
                        self.tracker.on_bacteria_killed()
                        if bac.splits_on_death:
                            for child in bac.spawn_children():
                                new_bac.append(child)
                        pu = maybe_spawn(bac.x, bac.y, POWERUP_DROP_CHANCE)
                        if pu:
                            self.powerups.append(pu)
                    break

        # Antibody → boss
        if self.boss and self.boss.alive:
            for ab in self.player.antibodies[:]:
                if ab.alive and _hits(ab, self.boss):
                    self.boss.take_damage(ab.damage)
                    ab.alive = False
                    self.particles.hit_sparks(ab.x, ab.y, self.boss.color)
                    self._shake = max(self._shake, SHAKE_BOSS_HIT)
                    audio_play("boss_hit")
                    if not self.boss.alive:
                        self._boss_killed = True
                        pts = self.tracker.on_boss_kill()
                        self.hud.score_pop(f"BOSS +{pts}!", self.boss.x, self.boss.y - 40, now)
                        self.particles.boss_explode(self.boss.x, self.boss.y, self.boss.color)
                        self._shake = SHAKE_BOSS_PHASE * 2
                        audio_play("boss_kill")
                    break

        # Boss update
        if self.boss and self.boss.alive:
            self.boss.update(pygame.Vector2(self.player.x, self.player.y),
                             self.BOUNDS, now, dt, self.bacteria)
            for bp in self.boss.projectiles:
                if bp.alive and _hits(bp, self.player):
                    self.player.take_damage(bp.damage)
                    bp.alive = False
                    if self.player.hp > 0:
                        self.particles.damage_puff(self.player.x, self.player.y)
                        self._shake = max(self._shake, SHAKE_PLAYER_HIT)
                        audio_play("player_hit")

        # Bacteria touch player
        for bac in self.bacteria:
            if bac.alive and bac.collides_with(self.player) and not self.player.invincible:
                self.player.take_damage(BACTERIA_DAMAGE // 2)
                self.particles.damage_puff(self.player.x, self.player.y)
                audio_play("player_hit")
                break

        # Power-ups
        for pu in self.powerups[:]:
            pu.update()
            if pu.collides_with_player(self.player):
                msg = pu.apply(self.player, self.body)
                self.particles.powerup_collect(pu.x, pu.y, pu.color)
                self.hud.powerup_notify(f">> {msg}", now)
                audio_play("powerup")
                pu.alive = False
        self.powerups = [p for p in self.powerups if p.alive]

        self.bacteria.extend(new_bac)
        self.bacteria = [b for b in self.bacteria if b.alive]
        self.particles.update(dt)
        self.zone_mgr.update()

        # Check game end
        if self.body.is_dead or not self.player.alive:
            self._end("loss")
            return

        alive_enemies = [b for b in self.bacteria if b.alive]
        boss_done = self.boss is None or not self.boss.alive
        if len(alive_enemies) == 0 and boss_done:
            wave_pts = self.tracker.on_wave_clear(self.body.hp, self.body.max_hp)
            safe = sum(1 for c in self.body_cells if c.state == "S" and c.alive)
            safe_bonus = safe * 100
            if safe_bonus > 0:
                self.tracker.score += safe_bonus
                self.hud.score_pop(f"+{safe_bonus} CELLS SAFE!", SCREEN_W//2, SCREEN_H//2 - 40, now)
            self.hud.score_pop(f"Wave +{wave_pts}", SCREEN_W//2, SCREEN_H//2 + 40, now)
            audio_play("wave_clear")
            self.tracker.on_wave_end()
            refresh_stats()

            if self.wave % BOSS_WAVE_INTERVAL == 0:
                if self.zone_mgr.zone_index + 1 >= TOTAL_ZONES and self._boss_killed:
                    self._end("win")
                    return
                self.zone_mgr.advance_zone()
                self.state = S_ZONE
            else:
                self._interm_start = now
                self.state = S_INTERM
            self.boss = None

    # Wave
    def _start_wave(self):
        self.wave += 1
        self._active_mutations = roll_mutations(self.wave)
        active_names = [m["name"] for m in self._active_mutations]
        memory_info = self.tracker.process_wave_memory(self.wave, active_names)

        self.body_cells = spawn_body_cells(self.wave, self.BOUNDS) if self.wave >= CELL_INFECT_START_WAVE else []

        count = WAVE_BASE_COUNT + (self.wave - 1) * WAVE_COUNT_GROWTH
        self.bacteria.clear()
        self.powerups.clear()
        self.boss = None
        self._boss_killed = False

        for _ in range(count):
            bac = self._spawn_bac()
            apply_mutations(bac, self._active_mutations)
            bac.speed *= self.zone_mgr.bacteria_speed_mult()
            self.bacteria.append(bac)

        if self.wave % BOSS_WAVE_INTERVAL == 0:
            self.boss = Boss(self.zone_mgr.zone_name, self.wave)
            self.state = S_BOSS
            self._pre_pause_state = S_BOSS
        else:
            self.state = S_PLAY
            self._pre_pause_state = S_PLAY

        self.hud.flash_wave(self.wave, active_names, pygame.time.get_ticks(),zone_index=self.zone_mgr.zone_index,has_boss=(self.boss is not None),memory_info=memory_info)

    def _spawn_bac(self):
        m = 80
        e = random.choice(["t", "b", "l", "r"])
        if   e == "t": bx,by = random.randint(m, SCREEN_W-m),random.randint(70, 130)
        elif e == "b": bx,by = random.randint(m, SCREEN_W-m),random.randint(SCREEN_H-130, SCREEN_H-70)
        elif e == "l": bx,by = random.randint(70, 130),random.randint(m, SCREEN_H-m)
        else:
            bx, by = random.randint(SCREEN_W-130, SCREEN_W-70), random.randint(m, SCREEN_H-m)
        return Bacteria(bx, by, self.wave)

    def _end(self, result):
        self.result = result
        self.state  = S_WIN if result == "win" else S_OVER
        self.tracker.save(self.body.hp, result, self.wave)
        self.tracker.save_to_leaderboard(result, self.wave)
        refresh_stats()

    # Draw
    def _draw(self, now):
        surf = self._surf

        if self.state == S_NAME:
            self._draw_name_screen(surf, now)
            self._blit(surf)
            return
        if self.state == S_START:
            self._stats_btn_rect = self.hud.draw_start_screen(surf, self.player_name, self._chosen_perk, now)
            self._blit(surf)
            return
        if self.state == S_STATS:
            self._draw_stats_screen(surf)
            self._blit(surf)
            return
        if self.state == S_BOARD:
            self.hud.draw_leaderboard(surf, StatsTracker.load_leaderboard())
            self._blit(surf)
            return

        sx, sy = self._shake_off
        world  = pygame.Surface((SCREEN_W, SCREEN_H))
        self.zone_mgr.draw_bg(world)

        for cell in self.body_cells: cell.draw(world, now)
        for pu   in self.powerups:   pu.draw(world)
        for bac  in self.bacteria:   bac.draw(world)
        if self.boss and self.boss.alive:
            self.boss.draw(world)
        self.player.draw(world)
        self.particles.draw(world)
        self._draw_aim_line(world, self._mouse())

        surf.fill((0, 0, 0))
        surf.blit(world, (sx, sy))

        self.hud.draw(surf, self.player, self.body, self.wave, self.tracker,now, self.player_name, self.body_cells,
                      chosen_perk=self._chosen_perk,zone_index=self.zone_mgr.zone_index)
        self.zone_mgr.draw_transition(surf)

        if self.state == S_INTERM:
            self._draw_intermission(surf, now)
        if self.state == S_OVER:
            self.hud.draw_game_over(surf, self.tracker, self.result, self.player_name, self._chosen_perk)
        if self.state == S_WIN:
            self.hud.draw_win_screen(surf, self.tracker, self.player_name, self._chosen_perk)
        if self.state == S_PAUSE:
            self._draw_pause_overlay(surf)
        self._blit(surf)

    def _blit(self, surf):
        ww, wh = self.screen.get_size()
        if (ww, wh) == (SCREEN_W, SCREEN_H):
            self.screen.blit(surf, (0, 0))
        else:
            self.screen.blit(pygame.transform.scale(surf, (ww, wh)), (0, 0))
        pygame.display.flip()

    def _mouse(self):
        mx, my = pygame.mouse.get_pos()
        ww, wh = self.screen.get_size()
        return int(mx * SCREEN_W / ww), int(my * SCREEN_H / wh)

    def _draw_aim_line(self, surface, mouse_pos):
        if not self.player.alive:
            return
        mx,my = mouse_pos
        px,py = int(self.player.x), int(self.player.y)
        dx,dy = mx - px, my - py
        dist = math.hypot(dx, dy)
        if dist < 5:
            return
        nx,ny = dx / dist, dy / dist
        dot_gap = 14
        for i in range(int(min(dist - 5, 180) / dot_gap)):
            t = self.player.radius + 10 + i * dot_gap
            if t > dist - 10:
                break
            ds = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ds, (180, 255, 220, max(40, 180 - i * 20)), (3, 3), 2)
            surface.blit(ds, (int(px + nx * t) - 3, int(py + ny * t) - 3))
        cr = 10
        for pts in [((mx-cr, my), (mx-3, my)), ((mx+3, my), (mx+cr, my)),((mx, my-cr), (mx, my-3)), ((mx, my+3), (mx, my+cr))]:
            pygame.draw.line(surface, (180, 255, 220), pts[0], pts[1], 1)
        pygame.draw.circle(surface, (180, 255, 220), (mx, my), cr, 1)

    def _draw_intermission(self, surf, now):
        elapsed = now - self._interm_start
        remaining = max(0, (WAVE_INTERMISSION - elapsed) / 1000)
        nw = self.wave + 1
        is_boss = nw % BOSS_WAVE_INTERVAL == 0
        is_warn = nw == CELL_INFECT_START_WAVE

        lines = [f"Wave {self.wave}/{TOTAL_WAVES}  CLEARED!"]
        colors = [LIME]
        lines.append(f"Next: Wave {nw}" + ("  --- BOSS ---" if is_boss else ""))
        colors.append(RED if is_boss else CYAN)
        if is_warn:
            lines += ["WARNING: Body cells appear next wave!","Shoot infected (orange) cells before they hatch!"]
            colors += [ORANGE, (255, 180, 60)]
        lines.append(f"Starting in  {remaining:.1f}s ...")
        colors.append(GRAY)

        y = SCREEN_H // 2 + (10 if is_warn else 40)
        for line, col in zip(lines, colors):
            t = self._font_md.render(line, True, col)
            bg = pygame.Surface((t.get_width() + 28, t.get_height() + 12), pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 160), (0, 0, t.get_width()+28, t.get_height()+12), border_radius=6)
            pygame.draw.rect(bg, (*col, 50), (0, 0, t.get_width()+28, t.get_height()+12), 1, border_radius=6)
            surf.blit(bg, (SCREEN_W//2 - t.get_width()//2 - 14, y - 6))
            surf.blit(t,  (SCREEN_W//2 - t.get_width()//2, y))
            y += 36

    def _draw_stats_screen(self, surf):
        if self._stats_surf:
            surf.blit(self._stats_surf, (0, 0))
        else:
            surf.fill((0, 0, 20))
            msg = self._font_md.render("Play a session first to see stats!", True, YELLOW)
            surf.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H//2 - 20))
        back = self._font_sm.render("ENTER or BACKSPACE to go back", True, (180, 180, 200))
        surf.blit(back, (SCREEN_W//2 - back.get_width()//2, SCREEN_H - 30))

    def _open_stats(self):
        try:
            import importlib.util
            import csv as _csv
            from stats_tracker import CSV_PATH
            viz_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats_visualizer.py")
            chart_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats_chart.png")
            if not os.path.exists(CSV_PATH) or not list(_csv.DictReader(open(CSV_PATH))):
                self._stats_surf = None
                self.state = S_STATS
                return
            import matplotlib
            matplotlib.use("Agg")
            spec = importlib.util.spec_from_file_location("stats_visualizer", viz_path)
            viz = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(viz)
            viz.plot_save(viz.load_data())
            if os.path.exists(chart_path):
                img = pygame.image.load(chart_path)
                self._stats_surf = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
            else:
                self._stats_surf = None
        except Exception as e:
            print(f"[Stats] {e}")
            self._stats_surf = None
        self.state = S_STATS

    def _draw_pause_overlay(self, surf):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        title = self._font_title.render("PAUSED", True, CYAN)
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, SCREEN_H//2 - 60))

        hint = self._font_md.render("P  —  Resume", True, (180, 255, 200))
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H//2))

        stats_hint = self._font_sm.render("V  —  Open Stats Window", True, (120, 200, 255))
        surf.blit(stats_hint, (SCREEN_W//2 - stats_hint.get_width()//2, SCREEN_H//2 + 36))

        quit_hint = self._font_sm.render("ESC  —  Quit", True, (180, 100, 100))
        surf.blit(quit_hint, (SCREEN_W//2 - quit_hint.get_width()//2, SCREEN_H//2 + 62))

    def _draw_name_screen(self, surf, now):
        if not hasattr(self, "_title_bg"):
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg_title.png")
            try:
                raw = pygame.image.load(bg_path).convert()
                self._title_bg = pygame.transform.scale(raw, (SCREEN_W, SCREEN_H))
            except Exception:
                self._title_bg = None

        if self._title_bg:
            surf.blit(self._title_bg, (0, 0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 4, 14, 150))
            surf.blit(overlay, (0, 0))
        else:
            surf.fill((6, 3, 14))

        for i in range(18):
            px_ = (i * 397 + now // 30) % SCREEN_W
            py_ = (i * 263 + now // 45) % SCREEN_H
            a = int(22 + 18 * math.sin(now * 0.0008 + i * 1.1))
            ds = pygame.Surface((5, 5), pygame.SRCALPHA)
            pygame.draw.circle(ds, (120, 200, 255, max(0, a)), (2, 2), 2)
            surf.blit(ds, (px_, py_))

        title_font = _font(100, True)
        cell_s = title_font.render("CELL", True, (20, 20, 30))
        cell_b = title_font.render("CELL", True, (155, 162, 172))
        wars_s = title_font.render("WARS", True, (55, 0, 0))
        wars_b = title_font.render("WARS", True, (210, 28, 22))

        gap = 32
        total_w = cell_b.get_width() + gap + wars_b.get_width()
        tx = SCREEN_W // 2 - total_w // 2
        ty = 62
        cx, wx  = tx, tx + cell_b.get_width() + gap
        th = cell_b.get_height()

        for gr, ga in [(130, 40), (85, 60), (52, 80)]:
            gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (190, 20, 10, ga), (gr, gr), gr)
            surf.blit(gs, (wx + wars_b.get_width()//2 - gr, ty + th//2 - gr))

        surf.blit(cell_s, (cx + 5, ty + 5))
        surf.blit(wars_s, (wx + 5, ty + 5))
        surf.blit(cell_b, (cx, ty))
        surf.blit(wars_b, (wx, ty))

        sub_y = ty + th + 18
        sub = _font(19, True).render("Defend the human body from mutating bacteria!", True, (235, 205, 60))
        surf.blit(sub, (SCREEN_W//2 - sub.get_width()//2, sub_y))

        div_y = sub_y + sub.get_height() + 28
        dw = 280
        for xi in range(SCREEN_W//2 - dw, SCREEN_W//2 + dw):
            t = abs(xi - SCREEN_W//2) / dw
            alpha = int(100 * (1 - t * t))
            if alpha > 0:
                ds = pygame.Surface((1, 2), pygame.SRCALPHA)
                ds.fill((150, 110, 55, alpha))
                surf.blit(ds, (xi, div_y))

        card_w, card_h = 460, 152
        card_x = SCREEN_W // 2 - card_w // 2
        card_y = div_y + 40
        card_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_bg, (4, 8, 24, 215),    (0, 0, card_w, card_h), border_radius=16)
        pygame.draw.rect(card_bg, (45, 58, 115, 100), (0, 0, card_w, card_h), 1, border_radius=16)
        surf.blit(card_bg, (card_x, card_y))

        prompt = _font(13, True).render("ENTER YOUR NAME", True, (88, 118, 198))
        surf.blit(prompt, (SCREEN_W//2 - prompt.get_width()//2, card_y + 14))

        bw, bh = 400, 54
        bx, by = SCREEN_W//2 - bw//2, card_y + 40
        box_bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(box_bg, (8, 14, 42, 235), (0, 0, bw, bh), border_radius=11)
        border_col = (100, 175, 255) if self.player_name.strip() else (34, 54, 108)
        pygame.draw.rect(box_bg, (*border_col, 225), (0, 0, bw, bh), 2, border_radius=11)
        surf.blit(box_bg, (bx, by))

        cursor = "|" if (now // 500) % 2 == 0 else " "
        nt = _font(26, True).render(self.player_name + cursor, True, WHITE)
        surf.blit(nt, (bx + 20, by + 12))

        if self.player_name.strip():
            hint = _font(15).render("ENTER  to continue  ->", True, (68, 218, 108))
        else:
            hint = _font(15).render("Type your name, then press ENTER", True, (68, 84, 132))
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, card_y + 110))

        strip = pygame.Surface((SCREEN_W, 34), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 130))
        surf.blit(strip, (0, SCREEN_H - 34))
        ctrl = _font(16).render("WASD  .  Mouse aim  .  Click / Z shoot  .  SPACE dash  .  M mute  .  ESC quit",True, (65, 80, 115))
        surf.blit(ctrl, (SCREEN_W//2 - ctrl.get_width()//2, SCREEN_H - 25))

        # Stats button (center, below name input card)
        stats_lbl = _font(20, True).render("[V]  Stats", True, CYAN)
        sb_w = stats_lbl.get_width() + 40
        sb_h = stats_lbl.get_height() + 16
        sb_x = SCREEN_W // 2 - sb_w // 2
        sb_y = card_y + card_h + 24
        sb = pygame.Surface((sb_w, sb_h), pygame.SRCALPHA)
        pygame.draw.rect(sb, (10, 30, 55, 200),   (0, 0, sb_w, sb_h), border_radius=9)
        pygame.draw.rect(sb, (50, 150, 220, 200), (0, 0, sb_w, sb_h), 2, border_radius=9)
        surf.blit(sb, (sb_x, sb_y))
        surf.blit(stats_lbl, (sb_x + 20, sb_y + 8))
        self._stats_btn_rect = pygame.Rect(sb_x, sb_y, sb_w, sb_h)