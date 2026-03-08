import pygame
import imgui
import os
import random
import math
import time
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl

# ╔══════════════════════════════════════════════════════════════╗
# ║                     WINDOW / LAYOUT                         ║
# ╚══════════════════════════════════════════════════════════════╝
WINDOW_W  = 1300
WINDOW_H  = 800
PANEL_W   = 400          # right debug/control panel width
VIEW_W    = WINDOW_W - PANEL_W   # 900  — shared by both modes
MENUBAR_H = 20           # estimated menu bar height

# ── Snake grid ──────────────────────────────────────────────────
CELL_SIZE = 24
COLS      = VIEW_W  // CELL_SIZE   # 37
ROWS      = (WINDOW_H - MENUBAR_H) // CELL_SIZE   # 32

GAME_W = COLS * CELL_SIZE
GAME_H = ROWS * CELL_SIZE

UP    = (0, -1);  DOWN  = (0, 1)
LEFT  = (-1, 0);  RIGHT = (1, 0)

# ── Shared palette ───────────────────────────────────────────────
C_BG         = (0.06, 0.06, 0.08, 1.0)
C_GRID       = (0.13, 0.15, 0.17, 1.0)
C_SNAKE_HEAD = (0.20, 0.95, 0.40, 1.0)
C_SNAKE_BODY = (0.10, 0.72, 0.28, 1.0)
C_FOOD       = (0.95, 0.25, 0.30, 1.0)
C_FOOD_BONUS = (0.95, 0.80, 0.10, 1.0)

# ╔══════════════════════════════════════════════════════════════╗
# ║                      SNAKE GAME                             ║
# ╚══════════════════════════════════════════════════════════════╝
class SnakeState:
    def __init__(self):
        self.high_score = 0
        self.reset()

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake         = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.direction     = RIGHT
        self.next_dir      = RIGHT
        self.food          = self._spawn_food()
        self.bonus_food    = None
        self.bonus_timer   = 0.0
        self.score         = 0
        self.level         = 1
        self.alive         = True
        self.paused        = False
        self.tick_interval = 0.15
        self.last_tick     = time.time()
        self.elapsed       = 0.0
        self.move_count    = 0
        self.food_eaten    = 0
        self.death_reason  = ""
        self.speed_override = False
        self.custom_speed   = 0.15
        self.god_mode       = False
        self.show_grid      = True
        self.show_hitboxes  = False
        self.log: list = []
        self._log("Snake game started!")

    def _log(self, msg):
        self.log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(self.log) > 200: self.log.pop(0)

    def _spawn_food(self):
        occupied = set(getattr(self, 'snake', []))
        while True:
            pos = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
            if pos not in occupied: return pos

    def handle_key(self, key):
        mapping = {
            pygame.K_UP: UP,   pygame.K_w: UP,
            pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
            pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
            pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
        }
        if key in mapping:
            nd = mapping[key]
            if (nd[0]+self.direction[0], nd[1]+self.direction[1]) != (0,0):
                self.next_dir = nd
        elif key in (pygame.K_p, pygame.K_SPACE):
            if self.alive:
                self.paused = not self.paused
                self._log("Paused." if self.paused else "Resumed.")
        elif key == pygame.K_r:
            self.reset()

    def update(self, dt):
        if not self.alive or self.paused: return
        self.elapsed += dt
        if self.bonus_food:
            self.bonus_timer -= dt
            if self.bonus_timer <= 0:
                self._log("Bonus food expired!")
                self.bonus_food = None
        interval = self.custom_speed if self.speed_override else self.tick_interval
        now = time.time()
        if now - self.last_tick < interval: return
        self.last_tick = now
        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        nh = (hx+dx, hy+dy)
        if not (0 <= nh[0] < COLS and 0 <= nh[1] < ROWS):
            if not self.god_mode:
                self.death_reason = "Hit the wall"; self._die(); return
            else:
                nh = (nh[0]%COLS, nh[1]%ROWS)
        if nh in self.snake[:-1] and not self.god_mode:
            self.death_reason = "Ate itself"; self._die(); return
        self.snake.insert(0, nh)
        self.move_count += 1
        grew = False
        if nh == self.food:
            self.score += 10*self.level; self.food_eaten += 1
            self.food = self._spawn_food(); grew = True
            self._log(f"Food eaten! Score: {self.score}")
            if self.food_eaten % 5 == 0 and not self.bonus_food:
                self.bonus_food = self._spawn_food(); self.bonus_timer = 6.0
                self._log("Bonus food appeared! (6s)")
            if self.food_eaten % 10 == 0:
                self.level += 1
                self.tick_interval = max(0.06, self.tick_interval - 0.01)
                self._log(f"Level up! Now level {self.level}")
        if nh == self.bonus_food:
            self.score += 50*self.level; self.bonus_food = None; grew = True
            self._log(f"Bonus food eaten! +{50*self.level} pts")
        if not grew: self.snake.pop()
        if self.score > self.high_score: self.high_score = self.score

    def _die(self):
        self.alive = False
        self._log(f"GAME OVER — {self.death_reason}. Score: {self.score}")


def draw_snake_game(gs: SnakeState, ox: float, oy: float):
    dl = imgui.get_window_draw_list()
    dl.add_rect_filled(ox, oy, ox+GAME_W, oy+GAME_H, imgui.get_color_u32_rgba(*C_BG))
    if gs.show_grid:
        gc = imgui.get_color_u32_rgba(*C_GRID)
        for c in range(COLS+1):
            dl.add_line(ox+c*CELL_SIZE, oy, ox+c*CELL_SIZE, oy+GAME_H, gc)
        for r in range(ROWS+1):
            dl.add_line(ox, oy+r*CELL_SIZE, ox+GAME_W, oy+r*CELL_SIZE, gc)
    # food
    fx, fy = gs.food
    _fill_cell(dl, fx, fy, *C_FOOD[:3], ox=ox, oy=oy)
    pulse = 0.5 + 0.5*math.sin(time.time()*5)
    dl.add_circle(ox+fx*CELL_SIZE+CELL_SIZE//2, oy+fy*CELL_SIZE+CELL_SIZE//2,
                  CELL_SIZE*0.7+pulse*4,
                  imgui.get_color_u32_rgba(0.95,0.25,0.30,0.3+0.4*pulse), thickness=2)
    if gs.bonus_food:
        bx, by = gs.bonus_food
        bp = 0.5+0.5*math.sin(time.time()*8)
        _fill_cell(dl, bx, by, *C_FOOD_BONUS[:3], a=0.7+0.3*bp, ox=ox, oy=oy)
    # snake
    for i,(sc,sr) in enumerate(gs.snake):
        if i==0: r,g,b = C_SNAKE_HEAD[:3]
        else:
            fade = max(0.5, 1.0-i*0.015)
            r,g,b = C_SNAKE_BODY[0]*fade, C_SNAKE_BODY[1]*fade, C_SNAKE_BODY[2]*fade
        _fill_cell(dl, sc, sr, r, g, b, ox=ox, oy=oy, shrink=1.0 if i==0 else 0.82)
        if gs.show_hitboxes:
            dl.add_rect(ox+sc*CELL_SIZE+1, oy+sr*CELL_SIZE+1,
                        ox+sc*CELL_SIZE+CELL_SIZE-1, oy+sr*CELL_SIZE+CELL_SIZE-1,
                        imgui.get_color_u32_rgba(1,0.2,0.2,0.35), thickness=1)
    # overlay
    if not gs.alive:
        dl.add_rect_filled(ox,oy,ox+GAME_W,oy+GAME_H, imgui.get_color_u32_rgba(0,0,0,0.6))
        dl.add_text(ox+GAME_W//2-70, oy+GAME_H//2-20, imgui.get_color_u32_rgba(0.95,0.3,0.3,1), "GAME OVER")
        dl.add_text(ox+GAME_W//2-90, oy+GAME_H//2+10, imgui.get_color_u32_rgba(0.8,0.8,0.8,1), "Press R to restart")
    elif gs.paused:
        dl.add_rect_filled(ox,oy,ox+GAME_W,oy+GAME_H, imgui.get_color_u32_rgba(0,0,0,0.45))
        dl.add_text(ox+GAME_W//2-35, oy+GAME_H//2-10, imgui.get_color_u32_rgba(0.95,0.85,0.1,1), "PAUSED")


def _fill_cell(dl, col, row, r, g, b, a=1.0, ox=0, oy=0, shrink=1.0):
    pad = (CELL_SIZE - CELL_SIZE*shrink)/2
    x1 = ox+col*CELL_SIZE+pad; y1 = oy+row*CELL_SIZE+pad
    x2 = x1+CELL_SIZE*shrink;  y2 = y1+CELL_SIZE*shrink
    dl.add_rect_filled(x1, y1, x2, y2, imgui.get_color_u32_rgba(r,g,b,a), rounding=4)


def draw_snake_panel(gs: SnakeState):
    imgui.set_next_window_position(VIEW_W, MENUBAR_H, imgui.ONCE)
    imgui.set_next_window_size(PANEL_W-4, WINDOW_H-MENUBAR_H, imgui.ONCE)
    flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR
    with imgui.begin("##snake_panel", flags=flags):
        imgui.push_style_color(imgui.COLOR_TEXT, 0.3, 0.95, 0.5, 1)
        imgui.text("SNAKE  —  Debug Console"); imgui.pop_style_color()
        imgui.separator(); imgui.spacing()

        # stats
        imgui.columns(2, "sc", border=False)
        def stat(label, value, color=None):
            imgui.text(label); imgui.next_column()
            if color: imgui.push_style_color(imgui.COLOR_TEXT, *color)
            imgui.text(str(value))
            if color: imgui.pop_style_color()
            imgui.next_column()
        stat("Score",      gs.score,      (1,0.85,0.1,1))
        stat("High Score", gs.high_score, (1,0.5,0.2,1))
        stat("Level",      gs.level)
        stat("Length",     len(gs.snake))
        stat("Food Eaten", gs.food_eaten)
        stat("Moves",      gs.move_count)
        stat("Elapsed",    f"{gs.elapsed:.1f}s")
        stat("Head",       f"({gs.snake[0][0]},{gs.snake[0][1]})")
        dn = {UP:"UP",DOWN:"DOWN",LEFT:"LEFT",RIGHT:"RIGHT"}
        stat("Dir",        dn.get(gs.direction,"?"))
        eff = gs.custom_speed if gs.speed_override else gs.tick_interval
        stat("Tick",       f"{eff:.3f}s")
        sc = (0.2,0.9,0.3,1) if gs.alive else (0.9,0.2,0.2,1)
        stat("Status", "Alive" if gs.alive else "Dead", sc)
        imgui.columns(1)

        if gs.bonus_food:
            imgui.spacing()
            imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, 0.95,0.80,0.10,1.0)
            imgui.progress_bar(gs.bonus_timer/6.0, (-1,0), f"Bonus: {gs.bonus_timer:.1f}s")
            imgui.pop_style_color()

        imgui.spacing(); imgui.separator(); imgui.spacing()
        imgui.push_style_color(imgui.COLOR_TEXT, 0.4,0.75,1.0,1); imgui.text("TWEAKS"); imgui.pop_style_color()
        imgui.separator()
        _, gs.speed_override = imgui.checkbox("Override Speed", gs.speed_override)
        if gs.speed_override:
            imgui.same_line()
            imgui.push_item_width(130)
            ch, v = imgui.slider_float("##spd", gs.custom_speed, 0.03, 0.40, "%.3fs")
            imgui.pop_item_width()
            if ch: gs.custom_speed = v; gs._log(f"Speed -> {v:.3f}s")
        _, gs.god_mode = imgui.checkbox("God Mode", gs.god_mode)
        if imgui.is_item_hovered():
            with imgui.begin_tooltip(): imgui.text("Wrap walls, ignore self-collision")
        _, gs.show_grid      = imgui.checkbox("Grid",     gs.show_grid)
        imgui.same_line(spacing=16)
        _, gs.show_hitboxes  = imgui.checkbox("Hitboxes", gs.show_hitboxes)
        imgui.spacing()
        imgui.push_item_width(90)
        _, inject_val = imgui.input_int("##inj", 100, step=10)
        imgui.pop_item_width()
        imgui.same_line()
        if imgui.button("Add Score"):
            gs.score += inject_val
            gs.high_score = max(gs.high_score, gs.score)
            gs._log(f"Injected +{inject_val}")
        if imgui.button("Spawn Bonus"):
            if not gs.bonus_food:
                gs.bonus_food = gs._spawn_food(); gs.bonus_timer = 6.0
                gs._log("Bonus spawned via debug.")
        imgui.same_line()
        if imgui.button("Kill Snake") and gs.alive:
            gs.death_reason = "Debug kill"; gs._die()
        imgui.spacing()
        if imgui.button("  RESTART  "): gs.reset()

        imgui.spacing(); imgui.separator(); imgui.spacing()
        imgui.push_style_color(imgui.COLOR_TEXT, 0.85,0.55,1.0,1); imgui.text("CONTROLS"); imgui.pop_style_color()
        imgui.separator()
        imgui.push_style_color(imgui.COLOR_TEXT, 0.65,0.65,0.65,1)
        imgui.text("WASD / Arrows  Move")
        imgui.text("Space / P      Pause")
        imgui.text("R              Restart")
        imgui.pop_style_color()

        imgui.spacing(); imgui.separator(); imgui.spacing()
        imgui.push_style_color(imgui.COLOR_TEXT, 0.95,0.55,0.25,1)
        imgui.text(f"EVENT LOG  ({len(gs.log)})"); imgui.pop_style_color()
        imgui.separator()
        if imgui.button("Clear##slog"): gs.log.clear()
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0.04,0.04,0.06,1)
        with imgui.begin_child("slog", 0, 160, border=True):
            for e in reversed(gs.log):
                if "GAME OVER" in e or "kill" in e.lower():
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.95,0.3,0.3,1)
                elif "Level up" in e:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.4,0.9,0.4,1)
                elif "Bonus" in e:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.95,0.8,0.1,1)
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.7,0.7,0.7,1)
                imgui.text(e); imgui.pop_style_color()
        imgui.pop_style_color()

        imgui.spacing(); imgui.separator()
        fps = imgui.get_io().framerate
        bc = (0.2,0.8,0.2,1) if fps>=55 else (0.9,0.7,0.1,1) if fps>=30 else (0.9,0.2,0.2,1)
        imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, *bc)
        imgui.progress_bar(min(fps/60.0,1.0), (-1,0), f"FPS: {fps:.0f}")
        imgui.pop_style_color()


# ╔══════════════════════════════════════════════════════════════╗
# ║                  N-BODY / PROJECTILE SIM                    ║
# ╚══════════════════════════════════════════════════════════════╝
SIM_MODE_NBODY      = 0
SIM_MODE_PROJECTILE = 1

BODY_COLORS = [
    (0.95, 0.35, 0.20),  # sun-orange
    (0.25, 0.65, 0.95),  # sky-blue
    (0.30, 0.90, 0.40),  # green
    (0.95, 0.85, 0.15),  # yellow
    (0.75, 0.35, 0.95),  # purple
    (0.95, 0.50, 0.80),  # pink
    (0.35, 0.95, 0.88),  # cyan
    (0.95, 0.60, 0.25),  # amber
]


class Body:
    def __init__(self, x, y, vx, vy, mass, color_idx=0):
        self.x = float(x); self.y = float(y)
        self.vx = float(vx); self.vy = float(vy)
        self.mass = float(mass)
        self.color_idx = color_idx % len(BODY_COLORS)
        self.trail: list = []   # list of (x,y)
        self.ax = 0.0; self.ay = 0.0

    def color(self):
        return BODY_COLORS[self.color_idx]


class PhysicsState:
    def __init__(self):
        self.sim_mode   = SIM_MODE_NBODY
        self.paused     = False
        self.time_step  = 0.5
        self.G          = 500.0
        self.softening  = 8.0
        self.trail_len  = 300
        self.show_trail = True
        self.show_force_vectors = False
        self.show_velocity_vectors = False
        self.elapsed    = 0.0
        self.log: list  = []

        # Projectile
        self.proj_gravity  = 200.0
        self.proj_angle    = 45.0
        self.proj_speed    = 300.0
        self.proj_x0       = 60.0
        self.proj_y0       = GAME_H - 60.0
        self.proj_running  = False
        self.proj_t        = 0.0
        self.proj_path: list = []
        self.proj_air_resist = 0.0
        self.proj_vx       = 0.0
        self.proj_vy       = 0.0
        self.proj_x        = 0.0
        self.proj_y        = 0.0
        self.proj_landed   = False
        self.proj_range    = 0.0

        self.bodies: list = []
        self._preset_solar()

    def _log(self, msg):
        self.log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(self.log) > 200: self.log.pop(0)

    def _preset_solar(self):
        cx, cy = GAME_W/2, GAME_H/2
        self.bodies = [
            Body(cx,   cy,   0,      0,      8000, 0),   # central star
            Body(cx+160, cy, 0,    -56,       30, 1),   # planet 1
            Body(cx-250, cy, 0,     45,       20, 2),   # planet 2
            Body(cx+370, cy, 0,    -37,       15, 3),   # planet 3
            Body(cx,  cy-120, 52,    0,        8, 4),   # moon-ish
        ]
        self._log("Preset: Solar System loaded")

    def _preset_figure8(self):
        # Classic figure-8 three-body
        cx, cy = GAME_W/2, GAME_H/2
        s = 120
        self.bodies = [
            Body(cx - s*0.97,  cy - s*0.24,  93*0.4,  27*0.4,  200, 0),
            Body(cx + s*0.97,  cy + s*0.24, -93*0.4, -27*0.4,  200, 1),
            Body(cx,           cy,             0,       0,      200, 2),
        ]
        self._log("Preset: Figure-8 orbit loaded")

    def _preset_binary(self):
        cx, cy = GAME_W/2, GAME_H/2
        self.bodies = [
            Body(cx-100, cy,  0, -40, 2000, 0),
            Body(cx+100, cy,  0,  40, 2000, 1),
            Body(cx, cy-200, 65,   0,   50, 2),
            Body(cx, cy+200,-65,   0,   50, 3),
        ]
        self._log("Preset: Binary star + planets loaded")

    def add_body(self, x, y, vx, vy, mass):
        idx = len(self.bodies) % len(BODY_COLORS)
        self.bodies.append(Body(x, y, vx, vy, mass, idx))
        self._log(f"Body added at ({x:.0f},{y:.0f}) m={mass:.0f}")

    def remove_body(self, i):
        if 0 <= i < len(self.bodies):
            self.bodies.pop(i)
            self._log(f"Body {i} removed")

    def reset_trails(self):
        for b in self.bodies: b.trail.clear()

    def update_nbody(self, dt):
        if self.paused or not self.bodies: return
        real_dt = dt * self.time_step
        n = len(self.bodies)
        # Compute accelerations
        for i in range(n):
            self.bodies[i].ax = 0.0
            self.bodies[i].ay = 0.0
        for i in range(n):
            for j in range(i+1, n):
                bi = self.bodies[i]; bj = self.bodies[j]
                dx = bj.x - bi.x;  dy = bj.y - bi.y
                dist2 = dx*dx + dy*dy + self.softening**2
                dist  = math.sqrt(dist2)
                force = self.G * bi.mass * bj.mass / dist2
                fx = force * dx/dist; fy = force * dy/dist
                bi.ax += fx/bi.mass; bi.ay += fy/bi.mass
                bj.ax -= fx/bj.mass; bj.ay -= fy/bj.mass
        # Integrate
        for b in self.bodies:
            b.vx += b.ax * real_dt; b.vy += b.ay * real_dt
            b.x  += b.vx * real_dt; b.y  += b.vy * real_dt
            if self.show_trail:
                b.trail.append((b.x, b.y))
                if len(b.trail) > self.trail_len: b.trail.pop(0)
        self.elapsed += real_dt

    def launch_projectile(self):
        rad = math.radians(self.proj_angle)
        self.proj_vx  = self.proj_speed * math.cos(rad)
        self.proj_vy  = -self.proj_speed * math.sin(rad)   # screen y flipped
        self.proj_x   = self.proj_x0
        self.proj_y   = self.proj_y0
        self.proj_t   = 0.0
        self.proj_path = [(self.proj_x, self.proj_y)]
        self.proj_running = True
        self.proj_landed  = False
        self.proj_range   = 0.0
        self._log(f"Launch: angle={self.proj_angle:.1f}° speed={self.proj_speed:.0f}")

    def update_projectile(self, dt):
        if not self.proj_running or self.proj_landed or self.paused: return
        steps = 4
        sub = dt / steps
        for _ in range(steps):
            # air resistance  F_drag = -k*v
            drag = self.proj_air_resist
            self.proj_vx += (-drag * self.proj_vx) * sub
            self.proj_vy += (self.proj_gravity - drag * self.proj_vy) * sub
            self.proj_x  += self.proj_vx * sub
            self.proj_y  += self.proj_vy * sub
            self.proj_t  += sub
            self.proj_path.append((self.proj_x, self.proj_y))
            if self.proj_y >= self.proj_y0:
                self.proj_landed = True
                self.proj_running = False
                self.proj_range = abs(self.proj_x - self.proj_x0)
                self._log(f"Landed! Range={self.proj_range:.1f}px  t={self.proj_t:.2f}s")
                break
            if self.proj_x > GAME_W + 200 or self.proj_x < -200:
                self.proj_landed = True; self.proj_running = False
                self._log("Projectile left the field.")
                break


def draw_physics_sim(ps: PhysicsState, ox: float, oy: float):
    dl = imgui.get_window_draw_list()
    dl.add_rect_filled(ox, oy, ox+GAME_W, oy+GAME_H, imgui.get_color_u32_rgba(*C_BG))

    if ps.sim_mode == SIM_MODE_NBODY:
        _draw_nbody(dl, ps, ox, oy)
    else:
        _draw_projectile(dl, ps, ox, oy)


def _draw_nbody(dl, ps: PhysicsState, ox, oy):
    t = time.time()

    # Soft star-field background dots (static pattern based on position)
    random.seed(42)
    for _ in range(80):
        sx = ox + random.randint(0, int(GAME_W))
        sy = oy + random.randint(0, int(GAME_H))
        brightness = random.uniform(0.2, 0.6)
        dl.add_circle_filled(sx, sy, random.uniform(0.5,1.5),
                             imgui.get_color_u32_rgba(brightness,brightness,brightness+0.1,1))
    random.seed()

    # Trails
    if ps.show_trail:
        for b in ps.bodies:
            if len(b.trail) < 2: continue
            r,g,bv = b.color()
            for i in range(1, len(b.trail)):
                alpha = (i / len(b.trail)) * 0.6
                col = imgui.get_color_u32_rgba(r, g, bv, alpha)
                x1,y1 = b.trail[i-1]; x2,y2 = b.trail[i]
                dl.add_line(ox+x1, oy+y1, ox+x2, oy+y2, col, thickness=1.2)

    # Bodies
    for b in ps.bodies:
        r,g,bv = b.color()
        radius = max(4.0, math.sqrt(b.mass) * 0.18)
        # glow
        dl.add_circle_filled(ox+b.x, oy+b.y, radius*2.2,
                             imgui.get_color_u32_rgba(r,g,bv,0.12))
        dl.add_circle_filled(ox+b.x, oy+b.y, radius*1.5,
                             imgui.get_color_u32_rgba(r,g,bv,0.25))
        dl.add_circle_filled(ox+b.x, oy+b.y, radius,
                             imgui.get_color_u32_rgba(r,g,bv,1.0))
        # specular highlight
        dl.add_circle_filled(ox+b.x-radius*0.3, oy+b.y-radius*0.3, radius*0.35,
                             imgui.get_color_u32_rgba(1,1,1,0.35))

        # velocity vector
        if ps.show_velocity_vectors:
            scale = 0.4
            dl.add_line(ox+b.x, oy+b.y,
                        ox+b.x+b.vx*scale, oy+b.y+b.vy*scale,
                        imgui.get_color_u32_rgba(0.3,0.9,1.0,0.8), thickness=1.5)
        # force/accel vector
        if ps.show_force_vectors:
            scale = 800
            dl.add_line(ox+b.x, oy+b.y,
                        ox+b.x+b.ax*scale, oy+b.y+b.ay*scale,
                        imgui.get_color_u32_rgba(1.0,0.4,0.2,0.8), thickness=1.5)

    # Elapsed
    tc = imgui.get_color_u32_rgba(0.7,0.7,0.7,0.7)
    dl.add_text(ox+8, oy+8, tc, f"N-Body  |  Bodies: {len(ps.bodies)}  |  t = {ps.elapsed:.1f}")
    if ps.paused:
        dl.add_text(ox+GAME_W//2-35, oy+GAME_H//2,
                    imgui.get_color_u32_rgba(0.95,0.85,0.1,1), "PAUSED")


def _draw_projectile(dl, ps: PhysicsState, ox, oy):
    # Ground line
    gy = oy + ps.proj_y0
    dl.add_line(ox, gy, ox+GAME_W, gy, imgui.get_color_u32_rgba(0.3,0.55,0.3,1), thickness=2)
    # launch point marker
    dl.add_circle_filled(ox+ps.proj_x0, gy, 6, imgui.get_color_u32_rgba(0.5,0.5,0.5,1))

    # Angle guide line
    rad = math.radians(ps.proj_angle)
    guide_len = 80
    dl.add_line(ox+ps.proj_x0, gy,
                ox+ps.proj_x0+guide_len*math.cos(rad),
                gy - guide_len*math.sin(rad),
                imgui.get_color_u32_rgba(0.6,0.6,0.2,0.5), thickness=1)

    # Ideal trajectory (no drag) dashed preview
    if not ps.proj_running:
        prev = None
        spd = ps.proj_speed
        angle_rad = math.radians(ps.proj_angle)
        vx0 = spd*math.cos(angle_rad)
        vy0 = -spd*math.sin(angle_rad)
        for step in range(120):
            t_sim = step * 0.025
            px = ps.proj_x0 + vx0*t_sim
            py = ps.proj_y0 + vy0*t_sim + 0.5*ps.proj_gravity*t_sim*t_sim
            if py > ps.proj_y0: break
            if prev:
                dl.add_line(ox+prev[0], oy+prev[1], ox+px, oy+py,
                            imgui.get_color_u32_rgba(0.4,0.7,0.4,0.3), thickness=1)
            prev = (px, py)

    # Actual path
    if len(ps.proj_path) > 1:
        for i in range(1, len(ps.proj_path)):
            alpha = min(1.0, i / max(len(ps.proj_path),1))
            col = imgui.get_color_u32_rgba(0.3, 0.7+0.3*alpha, 0.95, 0.8)
            x1,y1 = ps.proj_path[i-1]; x2,y2 = ps.proj_path[i]
            dl.add_line(ox+x1, oy+y1, ox+x2, oy+y2, col, thickness=2)

    # Projectile ball (if flying or path exists)
    if ps.proj_path:
        px, py = ps.proj_path[-1]
        if not ps.proj_landed:
            dl.add_circle_filled(ox+px, oy+py, 8, imgui.get_color_u32_rgba(0.95,0.5,0.2,1))
            dl.add_circle_filled(ox+px-2, oy+py-2, 3, imgui.get_color_u32_rgba(1,1,1,0.5))
        else:
            dl.add_circle_filled(ox+px, oy+py, 8, imgui.get_color_u32_rgba(0.7,0.3,0.15,1))
            # range annotation
            dl.add_line(ox+ps.proj_x0, gy+14, ox+px, gy+14,
                        imgui.get_color_u32_rgba(0.9,0.9,0.2,0.7), thickness=1.5)
            dl.add_text(ox+(ps.proj_x0+px)/2-20, gy+18,
                        imgui.get_color_u32_rgba(0.9,0.9,0.2,1),
                        f"{ps.proj_range:.1f} px")

    # Info overlay
    tc = imgui.get_color_u32_rgba(0.7,0.7,0.7,0.7)
    dl.add_text(ox+8, oy+8, tc,
                f"Projectile  |  angle={ps.proj_angle:.1f}°  speed={ps.proj_speed:.0f}  g={ps.proj_gravity:.0f}")
    if ps.paused:
        dl.add_text(ox+GAME_W//2-35, oy+GAME_H//2,
                    imgui.get_color_u32_rgba(0.95,0.85,0.1,1), "PAUSED")


def draw_physics_panel(ps: PhysicsState):
    imgui.set_next_window_position(VIEW_W, MENUBAR_H, imgui.ONCE)
    imgui.set_next_window_size(PANEL_W-4, WINDOW_H-MENUBAR_H, imgui.ONCE)
    flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR
    with imgui.begin("##phys_panel", flags=flags):

        # Sub-mode tabs
        imgui.push_style_color(imgui.COLOR_TEXT, 0.4,0.80,1.0,1)
        imgui.text("PHYSICS SIM  —  Control Panel"); imgui.pop_style_color()
        imgui.separator(); imgui.spacing()

        if imgui.button("N-Body Gravity", width=140):
            ps.sim_mode = SIM_MODE_NBODY
            ps._log("Switched to N-Body mode")
        imgui.same_line()
        if imgui.button("Projectile Motion", width=150):
            ps.sim_mode = SIM_MODE_PROJECTILE
            ps._log("Switched to Projectile mode")
        imgui.spacing(); imgui.separator(); imgui.spacing()

        if ps.sim_mode == SIM_MODE_NBODY:
            _panel_nbody(ps)
        else:
            _panel_projectile(ps)

        imgui.spacing(); imgui.separator(); imgui.spacing()
        imgui.push_style_color(imgui.COLOR_TEXT, 0.95,0.55,0.25,1)
        imgui.text(f"EVENT LOG  ({len(ps.log)})"); imgui.pop_style_color()
        imgui.separator()
        if imgui.button("Clear##plog"): ps.log.clear()
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0.04,0.04,0.06,1)
        with imgui.begin_child("plog", 0, 130, border=True):
            for e in reversed(ps.log):
                imgui.push_style_color(imgui.COLOR_TEXT, 0.7,0.7,0.7,1)
                imgui.text(e); imgui.pop_style_color()
        imgui.pop_style_color()

        imgui.spacing(); imgui.separator()
        fps = imgui.get_io().framerate
        bc = (0.2,0.8,0.2,1) if fps>=55 else (0.9,0.7,0.1,1) if fps>=30 else (0.9,0.2,0.2,1)
        imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, *bc)
        imgui.progress_bar(min(fps/60.0,1.0), (-1,0), f"FPS: {fps:.0f}")
        imgui.pop_style_color()


def _panel_nbody(ps: PhysicsState):
    imgui.push_style_color(imgui.COLOR_TEXT, 0.3,0.95,0.7,1)
    imgui.text("N-BODY GRAVITY"); imgui.pop_style_color()
    imgui.separator()

    _, ps.paused = imgui.checkbox("Pause", ps.paused)
    imgui.same_line(spacing=16)
    if imgui.button("Reset Trails"): ps.reset_trails()

    imgui.spacing()
    # Presets
    imgui.text("Presets:")
    if imgui.button("Solar System"): ps._preset_solar(); ps.elapsed=0
    imgui.same_line()
    if imgui.button("Figure-8"):     ps._preset_figure8(); ps.elapsed=0
    imgui.same_line()
    if imgui.button("Binary Star"):  ps._preset_binary(); ps.elapsed=0

    imgui.spacing(); imgui.separator(); imgui.spacing()
    imgui.text("Simulation Parameters")

    imgui.push_item_width(180)
    _, ps.time_step = imgui.slider_float("Time Step", ps.time_step, 0.05, 5.0, "%.2f")
    _, ps.G         = imgui.slider_float("Gravity G", ps.G, 50.0, 3000.0, "%.0f")
    _, ps.softening = imgui.slider_float("Softening", ps.softening, 1.0, 40.0, "%.1f")
    _, ps.trail_len = imgui.slider_int ("Trail Len", ps.trail_len, 20, 800)
    imgui.pop_item_width()

    _, ps.show_trail            = imgui.checkbox("Show Trails",   ps.show_trail)
    imgui.same_line(spacing=10)
    _, ps.show_velocity_vectors = imgui.checkbox("Velocity Vec",  ps.show_velocity_vectors)
    _, ps.show_force_vectors    = imgui.checkbox("Force Vec",     ps.show_force_vectors)

    imgui.spacing(); imgui.separator(); imgui.spacing()
    imgui.text(f"Bodies: {len(ps.bodies)}")
    for i, b in enumerate(ps.bodies):
        r,g,bv = b.color()
        imgui.push_style_color(imgui.COLOR_TEXT, r, g, bv, 1.0)
        imgui.text(f"  [{i}] m={b.mass:.0f}  v=({b.vx:.1f},{b.vy:.1f})")
        imgui.pop_style_color()
        imgui.same_line()
        if imgui.button(f"X##{i}"):
            ps.remove_body(i); break

    imgui.spacing()
    if imgui.button("Add Random Body"):
        mx = random.uniform(GAME_W*0.2, GAME_W*0.8)
        my = random.uniform(GAME_H*0.2, GAME_H*0.8)
        speed = random.uniform(20, 60)
        angle = random.uniform(0, math.pi*2)
        mass  = random.uniform(20, 300)
        ps.add_body(mx, my, speed*math.cos(angle), speed*math.sin(angle), mass)

    imgui.spacing()
    imgui.push_style_color(imgui.COLOR_TEXT, 0.6,0.6,0.6,1)
    imgui.text(f"Elapsed sim time: {ps.elapsed:.1f}")
    imgui.pop_style_color()


def _panel_projectile(ps: PhysicsState):
    imgui.push_style_color(imgui.COLOR_TEXT, 1.0,0.65,0.25,1)
    imgui.text("PROJECTILE MOTION"); imgui.pop_style_color()
    imgui.separator()

    imgui.push_item_width(200)
    _, ps.proj_angle    = imgui.slider_float("Launch Angle",  ps.proj_angle,    1.0,  89.0, "%.1f deg")
    _, ps.proj_speed    = imgui.slider_float("Launch Speed",  ps.proj_speed,   50.0, 800.0, "%.0f px/s")
    _, ps.proj_gravity  = imgui.slider_float("Gravity",       ps.proj_gravity,  50.0, 600.0, "%.0f px/s²")
    _, ps.proj_air_resist= imgui.slider_float("Air Drag",     ps.proj_air_resist,0.0,   4.0, "%.2f")
    imgui.pop_item_width()

    imgui.spacing()
    if imgui.button("  LAUNCH  "):
        ps.launch_projectile()
    imgui.same_line()
    if imgui.button("Clear Path"):
        ps.proj_path.clear(); ps.proj_landed=False; ps.proj_running=False

    imgui.spacing(); imgui.separator(); imgui.spacing()
    imgui.text("Physics Readout")
    imgui.columns(2, "pr", border=False)
    def pstat(l, v):
        imgui.text(l); imgui.next_column()
        imgui.text(str(v)); imgui.next_column()
    rad = math.radians(ps.proj_angle)
    vx0 = ps.proj_speed*math.cos(rad)
    vy0 = ps.proj_speed*math.sin(rad)
    t_flight_ideal = 2*vy0/ps.proj_gravity if ps.proj_gravity>0 else 0
    range_ideal    = vx0*t_flight_ideal
    max_h_ideal    = vy0**2/(2*ps.proj_gravity) if ps.proj_gravity>0 else 0

    pstat("Vx (launch)",  f"{vx0:.1f}")
    pstat("Vy (launch)",  f"{vy0:.1f}")
    pstat("Ideal Range",  f"{range_ideal:.1f}")
    pstat("Ideal Height", f"{max_h_ideal:.1f}")
    pstat("Ideal t",      f"{t_flight_ideal:.2f}s")
    if ps.proj_landed:
        pstat("Actual Range", f"{ps.proj_range:.1f}")
        pstat("Actual t",     f"{ps.proj_t:.2f}s")
    state_str = "Flying" if ps.proj_running else ("Landed" if ps.proj_landed else "Ready")
    pstat("State", state_str)
    imgui.columns(1)

    imgui.spacing(); imgui.separator(); imgui.spacing()
    _, ps.paused = imgui.checkbox("Pause Simulation", ps.paused)

    imgui.spacing()
    imgui.push_style_color(imgui.COLOR_TEXT, 0.6,0.6,0.6,1)
    imgui.text("Green dashed = ideal (no drag)")
    imgui.text("Blue path   = actual trajectory")
    imgui.pop_style_color()


# ╔══════════════════════════════════════════════════════════════╗
# ║                       MAIN LOOP                             ║
# ╚══════════════════════════════════════════════════════════════╝
MODE_SNAKE   = 0
MODE_PHYSICS = 1

def main():
    pygame.init()
    size = (WINDOW_W, WINDOW_H)
    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("ImGui App — Snake & Physics Sim")

    imgui.create_context()
    renderer = PygameRenderer()
    io = imgui.get_io()
    io.display_size = size

    imgui.style_colors_dark()
    style = imgui.get_style()
    style.window_rounding    = 6.0
    style.frame_rounding     = 4.0
    style.grab_rounding      = 4.0
    style.scrollbar_rounding = 4.0
    style.window_border_size = 1.0
    style.frame_padding      = (6, 4)
    style.item_spacing       = (8, 5)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path  = os.path.join(script_dir, "font", "Chandler42 Regular.otf")
    if os.path.exists(font_path):
        io.fonts.add_font_from_file_ttf(font_path, 18, io.fonts.get_glyph_ranges_thai())
        renderer.rebuild_font_atlas()
    else:
        print(f"[info] Font not found at {font_path}, using default.")

    gs    = SnakeState()
    ps    = PhysicsState()
    clock = pygame.time.Clock()
    app_mode = MODE_SNAKE    # current app mode

    # State for "Add Body" inline form in panel (kept outside loop for persistence)
    new_body_inputs = [GAME_W/2, GAME_H/2, 0.0, -50.0, 100.0]

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if app_mode == MODE_SNAKE:
                    gs.handle_key(event.key)
                else:
                    if event.key == pygame.K_SPACE:
                        ps.paused = not ps.paused
                    elif event.key == pygame.K_RETURN and ps.sim_mode == SIM_MODE_PROJECTILE:
                        ps.launch_projectile()
            renderer.process_event(event)

        renderer.process_inputs()

        if app_mode == MODE_SNAKE:
            gs.update(dt)
        else:
            if ps.sim_mode == SIM_MODE_NBODY:
                ps.update_nbody(dt)
            else:
                ps.update_projectile(dt)

        imgui.new_frame()

        # ── Menu Bar ──────────────────────────────────────────────
        with imgui.begin_main_menu_bar() as mb:
            if mb.opened:
                with imgui.begin_menu("App", True) as m:
                    if m.opened:
                        clicked, _ = imgui.menu_item("Snake Game",       "", app_mode==MODE_SNAKE,   True)
                        if clicked: app_mode = MODE_SNAKE
                        clicked, _ = imgui.menu_item("Physics Sim",      "", app_mode==MODE_PHYSICS, True)
                        if clicked: app_mode = MODE_PHYSICS
                        imgui.separator()
                        clicked, _ = imgui.menu_item("Quit", "Alt+F4", False, True)
                        if clicked: running = False

                if app_mode == MODE_SNAKE:
                    with imgui.begin_menu("Snake", True) as m:
                        if m.opened:
                            if imgui.menu_item("Restart", "R")[0]:      gs.reset()
                            imgui.menu_item("God Mode",  "", gs.god_mode, True)
                            if imgui.menu_item("God Mode Toggle")[0]:    gs.god_mode = not gs.god_mode
                            if imgui.menu_item("Toggle Grid")[0]:        gs.show_grid = not gs.show_grid
                            if imgui.menu_item("Toggle Hitboxes")[0]:    gs.show_hitboxes = not gs.show_hitboxes

                if app_mode == MODE_PHYSICS:
                    with imgui.begin_menu("Simulation", True) as m:
                        if m.opened:
                            if imgui.menu_item("N-Body Mode")[0]:
                                ps.sim_mode = SIM_MODE_NBODY
                            if imgui.menu_item("Projectile Mode")[0]:
                                ps.sim_mode = SIM_MODE_PROJECTILE
                            imgui.separator()
                            if imgui.menu_item("Solar Preset")[0]:  ps._preset_solar(); ps.elapsed=0
                            if imgui.menu_item("Figure-8 Preset")[0]: ps._preset_figure8(); ps.elapsed=0
                            if imgui.menu_item("Binary Star Preset")[0]: ps._preset_binary(); ps.elapsed=0
                            imgui.separator()
                            if imgui.menu_item("Pause / Resume", "Space")[0]: ps.paused = not ps.paused
                            if imgui.menu_item("Reset Trails")[0]: ps.reset_trails()

                # FPS in menu bar (right-aligned approx)
                fps = io.framerate
                fps_text = f"FPS: {fps:.0f}"
                imgui.set_cursor_pos_x(WINDOW_W - 80)
                col = (0.3,0.9,0.3,1) if fps>=55 else (0.9,0.7,0.1,1) if fps>=30 else (0.9,0.3,0.3,1)
                imgui.push_style_color(imgui.COLOR_TEXT, *col)
                imgui.text(fps_text)
                imgui.pop_style_color()

        # ── Game / Sim viewport window ─────────────────────────────
        imgui.set_next_window_position(0, MENUBAR_H)
        imgui.set_next_window_size(VIEW_W, WINDOW_H - MENUBAR_H)
        imgui.set_next_window_bg_alpha(0.0)
        no_deco = (imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE |
                   imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_MOVE)
        with imgui.begin("##viewport", flags=no_deco):
            wp = imgui.get_window_position()
            view_oy = wp.y
            if app_mode == MODE_SNAKE:
                top_pad = ((WINDOW_H - MENUBAR_H) - GAME_H) // 2
                draw_snake_game(gs, wp.x, view_oy + max(0, top_pad))
                dl = imgui.get_window_draw_list()
                dl.add_text(wp.x+8, view_oy+6,
                            imgui.get_color_u32_rgba(1,1,1,0.8),
                            f"Score: {gs.score}   Level: {gs.level}   Hi: {gs.high_score}")
            else:
                draw_physics_sim(ps, wp.x, view_oy)

        # ── Side panel ─────────────────────────────────────────────
        if app_mode == MODE_SNAKE:
            draw_snake_panel(gs)
        else:
            draw_physics_panel(ps)

        # ── Render ─────────────────────────────────────────────────
        gl.glClearColor(0.06, 0.06, 0.08, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        renderer.render(imgui.get_draw_data())
        pygame.display.flip()

    renderer.shutdown()
    pygame.quit()


if __name__ == "__main__":
    main()