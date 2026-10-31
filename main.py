import pygame
import sys
import random
import asyncio
import math

# --- CONFIGURATION & COLORS ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 850
BOARD_SIZE = 750
PANEL_WIDTH = SCREEN_WIDTH - BOARD_SIZE
CENTER_X = BOARD_SIZE // 2
CENTER_Y = BOARD_SIZE // 2

# Modern Palette
C_BG = (235, 245, 235)       # Mint Cream (Background)
C_BOARD = (255, 253, 208)    # Cream (Board base)
C_PANEL = (45, 55, 65)       # Dark Slate (Side Panel)
C_TEXT_MAIN = (20, 20, 20)
C_TEXT_LIGHT = (220, 220, 220)
C_ACCENT = (70, 130, 180)    # Steel Blue
C_HIGHLIGHT = (255, 215, 0)  # Gold
C_ERROR = (220, 60, 60)      # Red
C_SUCCESS = (60, 180, 80)    # Green
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Country/Group Colors
COLORS = {
    "Start": (200, 230, 200),
    "Korea": (255, 105, 180),   # Hot Pink
    "Spain": (255, 215, 0),     # Gold
    "Malaysia": (139, 69, 19),  # Brown
    "SAfrica": (169, 169, 169), # Grey
    "Russia": (220, 20, 60),    # Crimson
    "USA": (30, 144, 255),      # Dodger Blue
    "India": (255, 140, 0),     # Orange
    "Japan": (255, 192, 203),   # Pink
    "Station": (50, 50, 50),    # Black/Dark Grey
    "Tax": (160, 82, 45),       # Sienna
    "Special": (255, 255, 255), # White (Cards)
    "Prison": (80, 80, 80),
    "Vacation": (0, 200, 200),
    "Jump": (100, 0, 100)
}

# --- 3D MATH & RENDERING ENGINE ---

def rotate_pt(x, y, z, ax, ay, az):
    rad_x, rad_y, rad_z = math.radians(ax), math.radians(ay), math.radians(az)
    # Rotate around X
    y1 = y * math.cos(rad_x) - z * math.sin(rad_x)
    z1 = y * math.sin(rad_x) + z * math.cos(rad_x)
    # Rotate around Y
    x2 = x * math.cos(rad_y) + z1 * math.sin(rad_y)
    z2 = -x * math.sin(rad_y) + z1 * math.cos(rad_y)
    # Rotate around Z
    x3 = x2 * math.cos(rad_z) - y1 * math.sin(rad_z)
    y3 = x2 * math.sin(rad_z) + y1 * math.cos(rad_z)
    return x3, y3, z2

PIP_PATTERNS = {
    1: [(0, 0)],
    2: [(-0.5, -0.5), (0.5, 0.5)],
    3: [(-0.5, -0.5), (0, 0), (0.5, 0.5)],
    4: [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)],
    5: [(-0.5, -0.5), (0.5, -0.5), (0, 0), (-0.5, 0.5), (0.5, 0.5)],
    6: [(-0.5, -0.6), (-0.5, 0), (-0.5, 0.6), (0.5, -0.6), (0.5, 0), (0.5, 0.6)],
}

DICE_FACES = [
    {'val': 1, 'origin': (0, 0, 1), 'u': (1, 0, 0), 'v': (0, 1, 0), 'norm': (0, 0, 1)},
    {'val': 6, 'origin': (0, 0, -1), 'u': (-1, 0, 0), 'v': (0, 1, 0), 'norm': (0, 0, -1)},
    {'val': 2, 'origin': (0, 1, 0), 'u': (1, 0, 0), 'v': (0, 0, -1), 'norm': (0, 1, 0)},
    {'val': 5, 'origin': (0, -1, 0), 'u': (-1, 0, 0), 'v': (0, 0, -1), 'norm': (0, -1, 0)},
    {'val': 3, 'origin': (1, 0, 0), 'u': (0, 1, 0), 'v': (0, 0, -1), 'norm': (1, 0, 0)},
    {'val': 4, 'origin': (-1, 0, 0), 'u': (0, -1, 0), 'v': (0, 0, -1), 'norm': (-1, 0, 0)},
]

TARGET_DICE_ANGLES = {
    1: (20, -25, 0),
    2: (110, -25, 0),
    3: (20, -115, 0),
    4: (20, 65, 0),
    5: (-70, -25, 0),
    6: (20, 155, 0),
}

def draw_die_shadow(surface, cx, cy, z, size=52):
    scale = 1.0 + (z / 90.0) * 0.45
    alpha = max(18, int(110 * max(0.0, 1.0 - z / 130.0)))
    sw = int(size * 0.62 * scale)
    sh = int(size * 0.32 * scale)
    s_surf = pygame.Surface((sw * 2 + 4, sh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(s_surf, (0, 0, 0, alpha), (2, 2, sw * 2, sh * 2))
    surface.blit(s_surf, (cx - sw - 2, cy - sh // 2 - 2))

def draw_3d_die(surface, cx, cy, size, ax, ay, az):
    s = size / 2.0
    lx, ly, lz = -0.4, -0.6, 0.7
    l_mag = math.sqrt(lx*lx + ly*ly + lz*lz)
    lx, ly, lz = lx/l_mag, ly/l_mag, lz/l_mag
    transformed_faces = []
    for f in DICE_FACES:
        nx, ny, nz = rotate_pt(*f['norm'], ax, ay, az)
        if nz <= 0:
            continue
        ox, oy, oz = f['origin']
        ux, uy, uz = f['u']
        vx, vy, vz = f['v']
        corners_3d = [
            (ox - ux - vx, oy - uy - vy, oz - uz - vz),
            (ox + ux - vx, oy + uy - vy, oz + uz - vz),
            (ox + ux + vx, oy + uy + vy, oz + uz + vz),
            (ox - ux + vx, oy - uy + vy, oz - uz + vz),
        ]
        corners_rot = [rotate_pt(px*s, py*s, pz*s, ax, ay, az) for px, py, pz in corners_3d]
        pts_2d = [(cx + px, cy - py) for px, py, pz in corners_rot]
        dot = max(0.0, nx*lx + ny*ly + nz*lz)
        shade = 0.58 + 0.42 * dot
        face_col = (int(248 * shade), int(248 * shade), int(244 * shade))
        pips_2d = []
        for pu, pv in PIP_PATTERNS[f['val']]:
            p3d = (ox + ux*pu + vx*pv, oy + uy*pu + vy*pv, oz + uz*pu + vz*pv)
            px, py, pz = rotate_pt(p3d[0]*s, p3d[1]*s, p3d[2]*s, ax, ay, az)
            pips_2d.append((cx + px, cy - py))
        transformed_faces.append((nz, pts_2d, face_col, pips_2d))
        
    transformed_faces.sort(key=lambda item: item[0])
    for nz, pts_2d, col, pips in transformed_faces:
        pygame.draw.polygon(surface, col, pts_2d)
        pygame.draw.polygon(surface, (65, 65, 65), pts_2d, 2)
        for px, py in pips:
            pygame.draw.circle(surface, (28, 28, 28), (int(px), int(py)), max(2, int(size * 0.055)))

def draw_3d_pawn(screen, x, y, z, color, is_active=False, squash=0.0):
    # 1. Board Contact Shadow
    shadow_scale = 1.0 + (z / 70.0) * 0.4
    shadow_alpha = max(25, int(130 * max(0.0, 1.0 - z / 100.0)))
    sw = int(18 * shadow_scale)
    sh = int(8 * shadow_scale)
    
    shadow_surf = pygame.Surface((sw * 2 + 4, sh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (2, 2, sw * 2, sh * 2))
    screen.blit(shadow_surf, (x - sw - 2, y - sh // 2 - 2))

    # 2. Elevated pawn position
    py = y - z
    
    # Squash & stretch deformation when landing
    scale_x = 1.0 + squash * 0.25
    scale_y = 1.0 - squash * 0.2
    
    cr, cg, cb = color
    c_light = (min(255, int(cr * 1.35)), min(255, int(cg * 1.35)), min(255, int(cb * 1.35)))
    c_dark = (int(cr * 0.62), int(cg * 0.62), int(cb * 0.62))
    c_darker = (int(cr * 0.42), int(cg * 0.42), int(cb * 0.42))
    
    # Pedestal base
    bw = int(12 * scale_x)
    bh = int(5 * scale_y)
    pygame.draw.ellipse(screen, c_darker, (x - bw - 1, py - bh + 2, (bw + 1) * 2, bh * 2))
    pygame.draw.ellipse(screen, color, (x - bw, py - bh, bw * 2, bh * 2))
    pygame.draw.ellipse(screen, c_light, (x - bw + 2, py - bh + 1, (bw - 2) * 2, max(2, (bh - 1) * 2)))

    # Conical body
    body_pts = [
        (x - int(8 * scale_x), py - 2),
        (x + int(8 * scale_x), py - 2),
        (x + int(4 * scale_x), py - int(18 * scale_y)),
        (x - int(4 * scale_x), py - int(18 * scale_y))
    ]
    pygame.draw.polygon(screen, color, body_pts)
    hl_pts = [
        (x - int(8 * scale_x), py - 2),
        (x - 2, py - 2),
        (x - 1, py - int(18 * scale_y)),
        (x - int(4 * scale_x), py - int(18 * scale_y))
    ]
    pygame.draw.polygon(screen, c_light, hl_pts)
    sh_pts = [
        (x + 2, py - 2),
        (x + int(8 * scale_x), py - 2),
        (x + int(4 * scale_x), py - int(18 * scale_y)),
        (x + 1, py - int(18 * scale_y))
    ]
    pygame.draw.polygon(screen, c_dark, sh_pts)
    pygame.draw.polygon(screen, (35, 35, 35), body_pts, 1)

    # Collar ring
    cw = int(6 * scale_x)
    ch = max(2, int(4 * scale_y))
    pygame.draw.ellipse(screen, c_dark, (x - cw, py - int(21 * scale_y), cw * 2, ch))
    pygame.draw.ellipse(screen, c_light, (x - cw, py - int(22 * scale_y), cw * 2, ch))

    # Spherical 3D head
    hr = int(7 * scale_x)
    hy = py - int(28 * scale_y)
    pygame.draw.circle(screen, c_dark, (x + 1, hy + 1), hr)
    pygame.draw.circle(screen, color, (x, hy), hr)
    pygame.draw.circle(screen, c_light, (x - 2, hy - 2), max(2, hr - 2))
    pygame.draw.circle(screen, (255, 255, 255), (x - 3, hy - 3), 2)
    pygame.draw.circle(screen, (35, 35, 35), (x, hy), hr, 1)

    # Floating golden halo / indicator for active player
    if is_active and z <= 2:
        bob = math.sin(pygame.time.get_ticks() * 0.007) * 3
        ind_y = hy - hr - 8 + bob
        pygame.draw.polygon(screen, C_HIGHLIGHT, [(x, ind_y + 4), (x - 5, ind_y - 4), (x + 5, ind_y - 4)])
        pygame.draw.polygon(screen, (150, 110, 0), [(x, ind_y + 4), (x - 5, ind_y - 4), (x + 5, ind_y - 4)], 1)

def draw_3d_house(surface, x, y, size=11):
    c_wall = (46, 139, 87)
    c_wall_dark = (30, 95, 60)
    c_roof = (60, 185, 115)
    c_roof_dark = (35, 115, 70)
    w, h, d = size, int(size * 0.75), int(size * 0.5)
    
    sh_surf = pygame.Surface((w + d + 4, d * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_surf, (0, 0, 0, 75), (0, 0, w + d + 2, d * 2))
    surface.blit(sh_surf, (x - 1, y - d))
    
    pygame.draw.rect(surface, c_wall, (x, y - h, w, h))
    side_pts = [(x + w, y - h), (x + w + d, y - h - int(d * 0.6)), (x + w + d, y - int(d * 0.6)), (x + w, y)]
    pygame.draw.polygon(surface, c_wall_dark, side_pts)
    roof_front = [(x - 1, y - h), (x + w // 2, y - h - d), (x + w + 1, y - h)]
    pygame.draw.polygon(surface, c_roof, roof_front)
    roof_side = [(x + w // 2, y - h - d), (x + w // 2 + d, y - h - d - int(d * 0.6)), (x + w + 1 + d, y - h - int(d * 0.6)), (x + w + 1, y - h)]
    pygame.draw.polygon(surface, c_roof_dark, roof_side)

def draw_3d_hotel(surface, x, y, size=16):
    c_wall = (210, 45, 45)
    c_wall_dark = (150, 30, 30)
    c_roof = (235, 75, 75)
    c_roof_dark = (175, 40, 40)
    w, h, d = size, int(size * 1.1), int(size * 0.55)
    
    sh_surf = pygame.Surface((w + d + 6, d * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_surf, (0, 0, 0, 80), (0, 0, w + d + 4, d * 2))
    surface.blit(sh_surf, (x - 2, y - d))
    
    pygame.draw.rect(surface, c_wall, (x, y - h, w, h))
    for wx in [x + 3, x + 9]:
        for wy in [y - h + 3, y - h + 9]:
            pygame.draw.rect(surface, (255, 235, 150), (wx, wy, 3, 3))
    side_pts = [(x + w, y - h), (x + w + d, y - h - int(d * 0.6)), (x + w + d, y - int(d * 0.6)), (x + w, y)]
    pygame.draw.polygon(surface, c_wall_dark, side_pts)
    roof_front = [(x - 1, y - h), (x + w // 2, y - h - int(d * 0.9)), (x + w + 1, y - h)]
    pygame.draw.polygon(surface, c_roof, roof_front)
    roof_side = [(x + w // 2, y - h - int(d * 0.9)), (x + w // 2 + d, y - h - int(d * 0.9) - int(d * 0.6)), (x + w + 1 + d, y - h - int(d * 0.6)), (x + w + 1, y - h)]
    pygame.draw.polygon(surface, c_roof_dark, roof_side)

def get_space_center(i, player_idx=0, total_players=1):
    cell_w = BOARD_SIZE / 11.0
    if 0 <= i <= 10:
        rx = BOARD_SIZE - cell_w - (i * cell_w)
        ry = BOARD_SIZE - cell_w
    elif 11 <= i <= 20:
        rx = 0
        ry = BOARD_SIZE - cell_w - ((i - 10) * cell_w)
    elif 21 <= i <= 30:
        rx = (i - 20) * cell_w
        ry = 0
    else:
        rx = BOARD_SIZE - cell_w
        ry = (i - 30) * cell_w
        
    cx = rx + cell_w / 2.0
    cy = ry + cell_w / 2.0
    
    if total_players > 1:
        off_x = (player_idx * 7) - (total_players * 3.5)
        off_y = (player_idx % 2) * 5 - 2
        return cx + off_x, cy + off_y
    return cx, cy

# --- 3D ANIMATION CONTROLLERS ---

class Dice3DRollAnimation:
    def __init__(self, d1, d2, on_complete=None):
        self.d1 = d1
        self.d2 = d2
        self.on_complete = on_complete
        self.frame = 0
        self.total_roll_frames = 36
        self.settle_pause_frames = 16
        self.is_done = False
        
        self.pos1 = [CENTER_X - 55, CENTER_Y + 10]
        self.z1 = 125.0
        self.vz1 = -2.0
        self.ang1 = [random.randint(0, 360), random.randint(0, 360), random.randint(0, 360)]
        self.spin1 = [random.uniform(20, 32), random.uniform(16, 28), random.uniform(12, 22)]
        self.target_ang1 = TARGET_DICE_ANGLES[d1]
        
        self.pos2 = [CENTER_X + 55, CENTER_Y - 10]
        self.z2 = 140.0
        self.vz2 = -1.5
        self.ang2 = [random.randint(0, 360), random.randint(0, 360), random.randint(0, 360)]
        self.spin2 = [random.uniform(-32, -18), random.uniform(18, 30), random.uniform(-25, -14)]
        self.target_ang2 = TARGET_DICE_ANGLES[d2]

    def update(self):
        self.frame += 1
        if self.frame <= self.total_roll_frames:
            t = self.frame / float(self.total_roll_frames)
            for d in [1, 2]:
                z = self.z1 if d == 1 else self.z2
                vz = self.vz1 if d == 1 else self.vz2
                ang = self.ang1 if d == 1 else self.ang2
                spin = self.spin1 if d == 1 else self.spin2
                target_ang = self.target_ang1 if d == 1 else self.target_ang2
                
                vz -= 0.7
                z += vz
                if z <= 0:
                    z = 0
                    vz = -vz * 0.45
                    spin[0] *= 0.6
                    spin[1] *= 0.6
                    spin[2] *= 0.6
                
                if t > 0.58:
                    blend = (t - 0.58) / 0.42
                    ease = blend * blend * (3 - 2 * blend)
                    for k in range(3):
                        diff = (target_ang[k] - ang[k] + 180) % 360 - 180
                        ang[k] += diff * min(1.0, 0.25 + 0.75 * ease)
                else:
                    for k in range(3):
                        ang[k] = (ang[k] + spin[k]) % 360
                
                if d == 1:
                    self.z1, self.vz1 = z, vz
                else:
                    self.z2, self.vz2 = z, vz
        else:
            self.z1, self.z2 = 0, 0
            self.ang1 = list(self.target_ang1)
            self.ang2 = list(self.target_ang2)
            if self.frame >= self.total_roll_frames + self.settle_pause_frames:
                if not self.is_done:
                    self.is_done = True
                    if self.on_complete:
                        self.on_complete()

    def draw(self, screen):
        draw_die_shadow(screen, self.pos1[0], self.pos1[1], self.z1, size=52)
        draw_die_shadow(screen, self.pos2[0], self.pos2[1], self.z2, size=52)
        draw_3d_die(screen, self.pos1[0], self.pos1[1] - self.z1, 52, self.ang1[0], self.ang1[1], self.ang1[2])
        draw_3d_die(screen, self.pos2[0], self.pos2[1] - self.z2, 52, self.ang2[0], self.ang2[1], self.ang2[2])

class PawnHop3DAnimation:
    def __init__(self, player, total_steps, on_pass_start=None, on_complete=None):
        self.player = player
        self.total_steps = total_steps
        self.steps_left = total_steps
        self.on_pass_start = on_pass_start
        self.on_complete = on_complete
        
        self.current_tile = player.position
        self.next_tile = (self.current_tile + 1) % 40
        self.hop_progress = 0.0
        self.hop_speed = 0.12  # ~8 frames per hop
        self.max_height = 36.0 # Max height in pixels
        self.is_done = False
        self.squash = 0.0

    def update(self):
        if self.is_done:
            return
            
        if self.squash > 0:
            self.squash -= 0.2
            if self.squash <= 0 and self.steps_left <= 0:
                self.is_done = True
                if self.on_complete:
                    self.on_complete()
            return
            
        self.hop_progress += self.hop_speed
        if self.hop_progress >= 1.0:
            self.hop_progress = 0.0
            self.current_tile = self.next_tile
            self.player.position = self.current_tile
            self.steps_left -= 1
            
            if self.current_tile == 0 and self.on_pass_start:
                self.on_pass_start(self.player)
                    
            if self.steps_left > 0:
                self.next_tile = (self.current_tile + 1) % 40
            else:
                self.squash = 1.0

    def get_current_draw_pos(self):
        x0, y0 = get_space_center(self.current_tile)
        x1, y1 = get_space_center(self.next_tile)
        t = self.hop_progress
        gx = x0 + (x1 - x0) * t
        gy = y0 + (y1 - y0) * t
        z = self.max_height * math.sin(math.pi * t)
        return gx, gy, z

# --- UI CLASSES ---

class Button:
    def __init__(self, x, y, w, h, text, color, hover_color, action_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action_id = action_id
        self.is_hovered = False

    def draw(self, screen, font):
        col = self.hover_color if self.is_hovered else self.color
        # Shadow
        pygame.draw.rect(screen, (30,30,30), (self.rect.x+2, self.rect.y+4, self.rect.w, self.rect.h), border_radius=8)
        # Main Body
        pygame.draw.rect(screen, col, self.rect, border_radius=8)
        # Text
        txt = font.render(self.text, True, C_TEXT_LIGHT if sum(col)<400 else C_TEXT_MAIN)
        text_rect = txt.get_rect(center=self.rect.center)
        screen.blit(txt, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

class ToggleSwitch:
    def __init__(self, x, y, w, h, label, active=True, on_color=(30, 144, 255), action_id=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.active = active
        self.on_color = on_color
        self.off_color = (95, 100, 108)  # Grayscale
        self.action_id = action_id
        self.is_hovered = False

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def toggle(self):
        self.active = not self.active
        return self.active

    def draw(self, screen, font, small_font):
        bg_col = (65, 76, 90) if self.is_hovered else (52, 62, 74)
        pygame.draw.rect(screen, (30, 30, 30), (self.rect.x + 2, self.rect.y + 3, self.rect.w, self.rect.h), border_radius=8)
        pygame.draw.rect(screen, bg_col, self.rect, border_radius=8)
        pygame.draw.rect(screen, (80, 92, 105), self.rect, 1, border_radius=8)
        
        # Label
        lbl = small_font.render(self.label, True, C_TEXT_LIGHT)
        screen.blit(lbl, (self.rect.x + 16, self.rect.y + (self.rect.h - lbl.get_height()) // 2))
        
        # Switch Pill
        sw_w = 70
        sw_h = 28
        sw_x = self.rect.right - sw_w - 16
        sw_y = self.rect.y + (self.rect.h - sw_h) // 2
        sw_rect = pygame.Rect(sw_x, sw_y, sw_w, sw_h)
        
        track_col = self.on_color if self.active else self.off_color
        pygame.draw.rect(screen, track_col, sw_rect, border_radius=sw_h // 2)
        
        knob_r = (sw_h - 6) // 2
        if self.active:
            knob_center = (sw_rect.right - knob_r - 3, sw_rect.centery)
            txt = small_font.render("ON", True, WHITE)
            screen.blit(txt, (sw_rect.x + 9, sw_rect.centery - txt.get_height() // 2))
        else:
            knob_center = (sw_rect.x + knob_r + 3, sw_rect.centery)
            txt = small_font.render("OFF", True, (215, 215, 215))
            screen.blit(txt, (sw_rect.right - txt.get_width() - 8, sw_rect.centery - txt.get_height() // 2))
            
        pygame.draw.circle(screen, WHITE, knob_center, knob_r)
        pygame.draw.circle(screen, (50, 50, 50), knob_center, knob_r, 1)

class Dropdown:
    def __init__(self, x, y, w, h, label, options, selected_value, action_id=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.options = options
        self.selected_value = selected_value
        self.action_id = action_id
        self.is_open = False
        self.is_hovered = False

    def get_option_rects(self):
        rects = []
        for idx, opt in enumerate(self.options):
            rects.append((opt, pygame.Rect(self.rect.x, self.rect.bottom + idx * self.rect.h, self.rect.w, self.rect.h)))
        return rects

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.is_open = not self.is_open
            return True, None
        elif self.is_open:
            for opt, r in self.get_option_rects():
                if r.collidepoint(pos):
                    self.selected_value = opt
                    self.is_open = False
                    return True, opt
            self.is_open = False
            return True, None
        return False, None

    def draw_closed(self, screen, font, small_font):
        bg_col = (65, 76, 90) if self.is_hovered else (52, 62, 74)
        pygame.draw.rect(screen, (30, 30, 30), (self.rect.x + 2, self.rect.y + 3, self.rect.w, self.rect.h), border_radius=8)
        pygame.draw.rect(screen, bg_col, self.rect, border_radius=8)
        pygame.draw.rect(screen, C_ACCENT if self.is_open else (80, 92, 105), self.rect, 2 if self.is_open else 1, border_radius=8)
        
        lbl = small_font.render(self.label, True, C_TEXT_LIGHT)
        screen.blit(lbl, (self.rect.x + 16, self.rect.y + (self.rect.h - lbl.get_height()) // 2))
        
        val_str = f"Rs {self.selected_value}  {'▲' if self.is_open else '▼'}"
        val = small_font.render(val_str, True, C_HIGHLIGHT)
        screen.blit(val, (self.rect.right - val.get_width() - 16, self.rect.y + (self.rect.h - val.get_height()) // 2))

    def draw_open_menu(self, screen, font, mouse_pos):
        if not self.is_open:
            return
        total_h = len(self.options) * self.rect.h
        pygame.draw.rect(screen, (20, 20, 20), (self.rect.x + 2, self.rect.bottom + 2, self.rect.w, total_h), border_radius=8)
        
        for opt, r in self.get_option_rects():
            opt_hover = r.collidepoint(mouse_pos)
            if opt_hover:
                opt_bg = (40, 110, 180)
            elif opt == self.selected_value:
                opt_bg = (55, 75, 100)
            else:
                opt_bg = (38, 48, 60)
                
            pygame.draw.rect(screen, opt_bg, r)
            pygame.draw.rect(screen, (75, 90, 105), r, 1)
            
            col = C_HIGHLIGHT if opt == self.selected_value else WHITE
            txt = font.render(f"Rs {opt}", True, col)
            screen.blit(txt, (r.x + (r.w - txt.get_width()) // 2, r.y + (r.h - txt.get_height()) // 2))

class Space:
    def __init__(self, name, type, group=None, price=0, rent=0, house_cost=0):
        self.name = name
        self.type = type # Property, Station, Card, Tax, Start, Prison, Vacation, Jump
        self.group = group
        self.price = price
        self.rent_base = rent
        self.house_cost = house_cost
        self.owner = None
        self.houses = 0 
        self.mortgaged = False

    def get_rent(self):
        if self.mortgaged: return 0
        if self.type == "Station":
            if self.owner:
                station_count = sum(1 for p in self.owner.properties if p.type == "Station")
                return self.rent_base * (2 ** max(0, station_count - 1))
            return self.rent_base
        if self.type == "Property":
            mult = [1, 5, 15, 45, 80, 120] # 0 to 5 houses
            base_mult = mult[min(self.houses, 5)]
            if self.houses == 0 and self.owner:
                group_sizes = {
                    "Korea": 3, "Spain": 3, "Malaysia": 2, "SAfrica": 3,
                    "Russia": 3, "USA": 2, "India": 3, "Japan": 3
                }
                owned_in_group = sum(1 for p in self.owner.properties if p.group == self.group)
                if owned_in_group == group_sizes.get(self.group, 3):
                    return self.rent_base * 2
            return self.rent_base * base_mult
        return 0

class Player:
    def __init__(self, name, color, money):
        self.name = name
        self.color = color
        self.money = money
        self.position = 0
        self.in_prison = False
        self.prison_turns = 0
        self.properties = []
        self.loan = 0
        self.loan_turns = 0

class GameEngine:
    def __init__(self):
        self.players = []
        self.curr_idx = 0
        self.board = self.setup_board()
        self.state = "SETTINGS" # SETTINGS, LOBBY, IDLE, ROLLING_DICE, HOPPING, ACTION, POPUP, GAME_OVER
        self.log = ["Welcome to Monopoly!"]
        self.vacation_pot = 0
        self.dice = (1, 1)
        self.popup_timer = 0
        self.popup_msg = ""
        self.winner = None
        self.dice_anim = None
        self.hop_anim = None
        self.pending_hop_steps = 0
        
        # Settings
        self.s_money = 1500
        self.s_players = 4
        self.s_loans = True
        self.s_mortgage = True
        self.s_build = True
        self.s_vacation = True

    def sync_players(self):
        colors = [(220, 20, 60), (30, 144, 255), (34, 139, 34), (255, 215, 0)]
        existing_names = [p.name for p in self.players]
        self.players = []
        for i in range(self.s_players):
            name = existing_names[i] if (i < len(existing_names) and existing_names[i]) else f"Player {i+1}"
            self.players.append(Player(name, colors[i % len(colors)], self.s_money))

    def log_msg(self, text):
        self.log.append(text)
        if len(self.log) > 16: self.log.pop(0)

    def can_build_house(self, player):
        if not self.s_build or not player or not player.properties:
            return False, "Building is disabled or no properties"
        group_sizes = {
            "Korea": 3, "Spain": 3, "Malaysia": 2, "SAfrica": 3,
            "Russia": 3, "USA": 2, "India": 3, "Japan": 3
        }
        monopolies = []
        for grp, target_cnt in group_sizes.items():
            cnt = sum(1 for p in player.properties if p.group == grp and p.type == "Property")
            if cnt == target_cnt:
                monopolies.append(grp)
        if not monopolies:
            return False, "Need full color set to build"
            
        eligible = [p for p in player.properties if p.group in monopolies and p.houses < 5 and player.money >= p.house_cost]
        if not eligible:
            return False, "Cannot afford house or all at max (Hotel)"
            
        min_h = min(p.houses for p in eligible)
        target = next(p for p in eligible if p.houses == min_h)
        return True, target

    def build_house(self):
        if not self.players: return
        p = self.players[self.curr_idx]
        can_b, target = self.can_build_house(p)
        if can_b and target:
            p.money -= target.house_cost
            target.houses += 1
            h_label = "Hotel" if target.houses == 5 else f"House #{target.houses}"
            self.log_msg(f"Built {h_label} on {target.name} (-Rs {target.house_cost})")
        else:
            msg = target if isinstance(target, str) else "Cannot build"
            self.log_msg(f"Build: {msg}")

    def check_bankruptcy(self, player, creditor=None):
        if player.money >= 0:
            return False
        
        self.log_msg(f"{player.name} went BANKRUPT!")
        for prop in list(player.properties):
            if creditor:
                prop.owner = creditor
                creditor.properties.append(prop)
            else:
                prop.owner = None
                prop.houses = 0
                prop.mortgaged = False
        player.properties.clear()
        
        if creditor and player.money > 0:
            creditor.money += player.money
            
        is_current = (self.players[self.curr_idx] == player)
        p_idx = self.players.index(player)
        self.players.remove(player)
        
        if len(self.players) <= 1:
            self.state = "GAME_OVER"
            self.winner = self.players[0] if self.players else None
            if self.winner:
                self.log_msg(f"GAME OVER! {self.winner.name} WINS!")
            return True
            
        if is_current:
            self.curr_idx = p_idx % len(self.players)
            self.log_msg(f"--- {self.players[self.curr_idx].name}'s Turn ---")
        elif p_idx < self.curr_idx:
            self.curr_idx -= 1
            
        return True

    def setup_board(self):
        # 40 Spaces mapping exactly to your request
        s = []
        # Bottom (Right to Left) -> 0 is Start
        s.append(Space("Start", "Start", "Start"))
        s.append(Space("Busan", "Property", "Korea", 220, 18, 100))
        s.append(Space("Seoul", "Property", "Korea", 240, 20, 100))
        s.append(Space("Treasure", "Card", "Special"))
        s.append(Space("Incheon", "Property", "Korea", 220, 18, 100))
        s.append(Space("N. Central", "Station", "Station", 200, 25))
        s.append(Space("Madrid", "Property", "Spain", 260, 22, 100))
        s.append(Space("Income Tax", "Tax", "Tax"))
        s.append(Space("Barcelona", "Property", "Spain", 260, 22, 100))
        s.append(Space("Seville", "Property", "Spain", 280, 24, 100))
        
        # Left (Bottom to Top)
        s.append(Space("Prison", "Prison", "Prison"))
        s.append(Space("K. Lumpur", "Property", "Malaysia", 140, 10, 100))
        s.append(Space("Lottery", "Card", "Special"))
        s.append(Space("Penang", "Property", "Malaysia", 160, 12, 100))
        s.append(Space("Surprise", "Card", "Special"))
        s.append(Space("E. Central", "Station", "Station", 200, 25))
        s.append(Space("Jo'burg", "Property", "SAfrica", 180, 14, 100))
        s.append(Space("Cape Town", "Property", "SAfrica", 180, 14, 100))
        s.append(Space("Lottery", "Card", "Special"))
        s.append(Space("Durban", "Property", "SAfrica", 200, 16, 100))

        # Top (Left to Right)
        s.append(Space("Vacation", "Vacation", "Vacation"))
        s.append(Space("Moscow", "Property", "Russia", 320, 28, 200))
        s.append(Space("St. Pete", "Property", "Russia", 320, 28, 200))
        s.append(Space("Treasure", "Card", "Special"))
        s.append(Space("Chernobyl", "Property", "Russia", 350, 35, 200))
        s.append(Space("S. Central", "Station", "Station", 200, 25))
        s.append(Space("Surprise", "Card", "Special"))
        s.append(Space("Washington", "Property", "USA", 360, 38, 200))
        s.append(Space("Prop Tax", "Tax", "Tax"))
        s.append(Space("LA", "Property", "USA", 380, 40, 200))

        # Right (Top to Bottom)
        s.append(Space("Jump", "Jump", "Jump"))
        s.append(Space("Mumbai", "Property", "India", 450, 50, 200))
        s.append(Space("Bangalore", "Property", "India", 400, 45, 200))
        s.append(Space("Lottery", "Card", "Special"))
        s.append(Space("N. Delhi", "Property", "India", 420, 48, 200))
        s.append(Space("W. Central", "Station", "Station", 200, 25))
        s.append(Space("Tokyo", "Property", "Japan", 300, 26, 200))
        s.append(Space("Kyoto", "Property", "Japan", 300, 26, 200))
        s.append(Space("Lottery", "Card", "Special"))
        s.append(Space("Osaka", "Property", "Japan", 320, 28, 200))
        
        return s

    def roll(self):
        self.start_roll()

    def start_roll(self):
        if not self.players:
            return
        p = self.players[self.curr_idx]
        
        # Loan Check
        if self.s_loans and p.loan > 0:
            p.loan_turns -= 1
            if p.loan_turns <= 0:
                interest = int(p.loan * 1.15)
                p.money -= interest
                self.log_msg(f"LOAN DUE! Paid Rs {interest}")
                p.loan = 0
                if self.check_bankruptcy(p):
                    return

        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.dice = (d1, d2)
        total = d1 + d2
        self.log_msg(f"{p.name} rolling 3D dice...")
        
        self.state = "ROLLING_DICE"
        
        def on_dice_settled():
            self.log_msg(f"{p.name} rolled {total} ({d1} + {d2})")
            # Prison Logic
            if p.in_prison:
                if d1 == d2:
                    p.in_prison = False
                    self.log_msg("Doubles! Free from Prison!")
                else:
                    p.prison_turns += 1
                    if p.prison_turns >= 3:
                        p.in_prison = False
                        p.money -= 25
                        self.log_msg("Time served. Paid Rs 25.")
                        if self.check_bankruptcy(p):
                            return
                    else:
                        self.state = "IDLE"
                        self.next_turn()
                        return

            self.start_pawn_hop(p, total, on_complete=self.handle_land)
            
        self.dice_anim = Dice3DRollAnimation(d1, d2, on_complete=on_dice_settled)

    def start_pawn_hop(self, player, steps, on_complete=None):
        self.state = "HOPPING"
        self.hop_anim = PawnHop3DAnimation(player, steps, on_pass_start=self._on_pass_start, on_complete=on_complete)

    def _on_pass_start(self, player):
        player.money += 250
        self.log_msg(f"{player.name} passed Start! +Rs 250")

    def handle_land(self):
        if not self.players:
            return
        p = self.players[self.curr_idx]
        s = self.board[p.position]
        
        if s.type == "Property" or s.type == "Station":
            if s.owner is None:
                self.state = "ACTION" # Can Buy
            elif s.owner != p and not s.mortgaged:
                rent = s.get_rent()
                p.money -= rent
                s.owner.money += rent
                self.log_msg(f"Paid rent Rs {rent} to {s.owner.name}")
                if self.check_bankruptcy(p, creditor=s.owner):
                    return
                self.state = "IDLE"
            else:
                self.state = "IDLE"

        elif s.type == "Tax":
            tax = int(p.money * 0.1) if "Income" in s.name else int((p.money+sum(x.price for x in p.properties))*0.05)
            tax = max(tax, 50)
            p.money -= tax
            if self.s_vacation:
                self.vacation_pot += int(tax * 0.9)
            self.log_msg(f"Tax Paid: Rs {tax}")
            if self.check_bankruptcy(p):
                return
            self.state = "IDLE"
            
        elif s.type == "Vacation":
            if self.s_vacation and self.vacation_pot > 0:
                p.money += self.vacation_pot
                self.log_msg(f"Vacation! Won Rs {self.vacation_pot}")
                self.vacation_pot = 0
            self.state = "IDLE"
            
        elif s.type == "Jump":
            self.log_msg("Go to Start!")
            p.position = 0
            p.money += 400
            self.state = "IDLE"
            
        elif s.type == "Prison":
            self.log_msg("Just Visiting")
            self.state = "IDLE"
            
        elif s.type == "Card":
            card = random.choice(['Won 100', 'Pay 50', 'Move 3 Spaces'])
            self.popup_msg = f"{s.name}: {card}"
            if "Won" in card:
                p.money += 100
            elif "Pay" in card:
                p.money -= 50
                if self.check_bankruptcy(p):
                    return
            elif "Move" in card:
                self.pending_hop_steps = 3
            self.state = "POPUP"
            self.popup_timer = 50 # frames

    def buy_prop(self):
        if not self.players:
            return
        p = self.players[self.curr_idx]
        s = self.board[p.position]
        if s.owner is None and p.money >= s.price:
            p.money -= s.price
            s.owner = p
            p.properties.append(s)
            self.log_msg(f"Bought {s.name} for Rs {s.price}")
            self.state = "IDLE"
        elif p.money < s.price:
            self.log_msg("Not enough money to buy!")
    
    def next_turn(self):
        if not self.players:
            return
        self.curr_idx = (self.curr_idx + 1) % len(self.players)
        self.log_msg(f"--- {self.players[self.curr_idx].name}'s Turn ---")

# --- DRAWING UTILS ---

def draw_dice(screen, dice, x, y):
    for i, val in enumerate(dice):
        dx = x + (i * 70)
        draw_die_shadow(screen, dx + 26, y + 26, 0, size=46)
        draw_3d_die(screen, dx + 26, y + 26, 46, *TARGET_DICE_ANGLES[val])

def draw_board(screen, engine, font, small_font):
    pygame.draw.rect(screen, C_BOARD, (0, 0, BOARD_SIZE, BOARD_SIZE))
    
    # Grid sizes
    cell_w = BOARD_SIZE / 11
    
    # Draw each space
    for i in range(40):
        s = engine.board[i]
        
        # Calculate Coordinates
        if 0 <= i <= 10:   # Bottom
            x, y = BOARD_SIZE - ((i+0.5) * cell_w), BOARD_SIZE - cell_w
            w, h = cell_w, cell_w
            if i==0: x, w = BOARD_SIZE-cell_w, cell_w # Corner fix
        elif 11 <= i <= 20: # Left
            x, y = 0, BOARD_SIZE - ((i-10+0.5) * cell_w)
            w, h = cell_w, cell_w
            if i==20: y, h = 0, cell_w
        elif 21 <= i <= 30: # Top
            x, y = (i-20-0.5) * cell_w, 0
            w, h = cell_w, cell_w
            if i==30: x, w = BOARD_SIZE-cell_w, cell_w
        else: # Right
            x, y = BOARD_SIZE - cell_w, (i-30-0.5) * cell_w
            w, h = cell_w, cell_w

        # Adjust for corners
        if i in [0, 10, 20, 30]: 
            # Corners are special, handled by generic loop but let's ensure square
            pass 
        
        # Correct pixel placement for exact alignment
        # (Simplified math for brevity - improved over previous version)
        if 0 <= i <= 10: # Bottom Row
            rx = BOARD_SIZE - cell_w - (i * cell_w)
            ry = BOARD_SIZE - cell_w
        elif 11 <= i <= 20: # Left Col
            rx = 0
            ry = BOARD_SIZE - cell_w - ((i-10) * cell_w)
        elif 21 <= i <= 30: # Top Row
            rx = (i-20) * cell_w
            ry = 0
        else: # Right Col
            rx = BOARD_SIZE - cell_w
            ry = (i-30) * cell_w
            
        # Draw Border
        pygame.draw.rect(screen, (80,80,80), (rx, ry, cell_w, cell_w), 1)
        
        # Draw Color Strip
        if s.type in ["Property", "Station", "Tax", "Start", "Prison", "Vacation", "Jump"]:
            c = COLORS.get(s.group, (200,200,200))
            if s.type == "Property":
                # Orientation of strip
                if 0 <= i <= 10: pygame.draw.rect(screen, c, (rx, ry, cell_w, 20))
                elif 11 <= i <= 20: pygame.draw.rect(screen, c, (rx+cell_w-20, ry, 20, cell_w)) 
                elif 21 <= i <= 30: pygame.draw.rect(screen, c, (rx, ry+cell_w-20, cell_w, 20))
                else: pygame.draw.rect(screen, c, (rx, ry, 20, cell_w))
        
        # Space Text / Vacation Box Pot
        if s.type == "Vacation":
            txt = small_font.render("VACATION", True, (0, 110, 120))
            screen.blit(txt, (rx + (cell_w - txt.get_width()) / 2, ry + 10))
            
            # Dedicated pot container inside the vacation space
            pot_badge = pygame.Rect(rx + 4, ry + 28, cell_w - 8, cell_w - 34)
            pygame.draw.rect(screen, (220, 245, 245), pot_badge, border_radius=4)
            pygame.draw.rect(screen, (0, 160, 170), pot_badge, 1, border_radius=4)
            
            p_lbl = small_font.render("POT", True, (70, 90, 100))
            screen.blit(p_lbl, (rx + (cell_w - p_lbl.get_width()) / 2, ry + 30))
            
            amt_col = (200, 40, 40) if engine.vacation_pot > 0 else (100, 100, 100)
            p_amt = small_font.render(f"Rs {engine.vacation_pot}", True, amt_col)
            screen.blit(p_amt, (rx + (cell_w - p_amt.get_width()) / 2, ry + 44))
        else:
            lines = s.name.split(" ")
            ty = ry + 25
            for line in lines:
                txt = small_font.render(line, True, BLACK)
                screen.blit(txt, (rx + (cell_w - txt.get_width())/2, ty))
                ty += 12

        # Owner Dot & 3D Houses / Hotel
        if s.owner:
            pygame.draw.circle(screen, s.owner.color, (rx+cell_w-10, ry+cell_w-10), 6)
            if s.houses > 0:
                if s.houses == 5:
                    draw_3d_hotel(screen, rx + int(cell_w/2) - 8, ry + int(cell_w) - 18, size=15)
                else:
                    spacing = 11
                    start_hx = rx + int((cell_w - (s.houses * spacing - 2)) / 2)
                    for h_idx in range(s.houses):
                        draw_3d_house(screen, start_hx + h_idx * spacing, ry + int(cell_w) - 16, size=9)
        elif s.price > 0:
            p_surf = small_font.render(f"Rs {s.price}", True, (110, 110, 110))
            screen.blit(p_surf, (rx + (cell_w - p_surf.get_width()) / 2, ry + cell_w - 18))
            
    # Center Logo
    title = font.render("MONOPOLY", True, C_PANEL)
    screen.blit(title, (CENTER_X - title.get_width()//2, CENTER_X - 25))
    edition = small_font.render("International Edition", True, (130, 140, 150))
    screen.blit(edition, (CENTER_X - edition.get_width()//2, CENTER_X + 15))

def draw_ui(screen, engine, font, small_font, buttons, selected_player_idx=0):
    # Panel Background
    pygame.draw.rect(screen, C_PANEL, (BOARD_SIZE, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    bx = BOARD_SIZE + 45

    # State: SETTINGS
    if engine.state == "SETTINGS":
        t = font.render("GAME SETTINGS", True, C_HIGHLIGHT)
        screen.blit(t, (bx, 30))
        sub = small_font.render("Configure player setup, money, and rules:", True, C_TEXT_LIGHT)
        screen.blit(sub, (bx, 64))
        
        lbl_p = small_font.render("NUMBER OF PLAYERS", True, C_HIGHLIGHT)
        screen.blit(lbl_p, (bx, 94))
        return

    # State: LOBBY
    if engine.state == "LOBBY":
        t = font.render("LOBBY", True, C_HIGHLIGHT)
        screen.blit(t, (bx, 30))
        sub = small_font.render(f"{len(engine.players)} Players configured. Click START or customize names below:", True, C_TEXT_LIGHT)
        screen.blit(sub, (bx, 64))
        y = 98
        for i, p in enumerate(engine.players):
            card_rect = pygame.Rect(bx, y, 440, 40)
            is_sel = (i == selected_player_idx)
            bg_col = (65, 82, 102) if is_sel else (50, 60, 72)
            pygame.draw.rect(screen, bg_col, card_rect, border_radius=6)
            if is_sel:
                pygame.draw.rect(screen, C_HIGHLIGHT, card_rect, 2, border_radius=6)
            pygame.draw.circle(screen, p.color, (bx + 20, y + 20), 8)
            p_txt = font.render(p.name, True, WHITE)
            screen.blit(p_txt, (bx + 38, y + 6))
            bal_txt = small_font.render(f"Rs {p.money}", True, (80, 200, 100))
            screen.blit(bal_txt, (card_rect.right - bal_txt.get_width() - 15, y + 12))
            y += 46
        return

    # State: GAME_OVER
    if engine.state == "GAME_OVER":
        t = font.render("GAME OVER", True, C_ERROR)
        screen.blit(t, (bx, 40))
        if engine.winner:
            w_txt = font.render(f"{engine.winner.name} WINS!", True, C_HIGHLIGHT)
            screen.blit(w_txt, (bx, 90))
            bal_txt = small_font.render(f"Final Balance: Rs {engine.winner.money}", True, C_TEXT_LIGHT)
            screen.blit(bal_txt, (bx, 130))
        return

    # State: GAME
    if not engine.players:
        return
    curr = engine.players[engine.curr_idx]
    
    # Card-like Player Info
    pygame.draw.rect(screen, WHITE, (BOARD_SIZE+20, 20, PANEL_WIDTH-40, 140), border_radius=15)
    pygame.draw.rect(screen, curr.color, (BOARD_SIZE+20, 20, PANEL_WIDTH-40, 140), 4, border_radius=15)
    
    name_t = font.render(curr.name, True, BLACK)
    money_t = font.render(f"Rs {curr.money}", True, (34,139,34))
    screen.blit(name_t, (BOARD_SIZE+40, 30))
    screen.blit(money_t, (BOARD_SIZE+40, 68))
    
    pos_name = engine.board[curr.position].name
    stats_t = small_font.render(f"Props: {len(curr.properties)}  |  At: {pos_name}", True, C_TEXT_MAIN)
    screen.blit(stats_t, (BOARD_SIZE+40, 105))
    if curr.loan > 0:
        loan_t = small_font.render(f"Loan: Rs {curr.loan} (Due in {curr.loan_turns} turns)", True, C_ERROR)
        screen.blit(loan_t, (BOARD_SIZE+40, 125))
    
    # Dice
    draw_dice(screen, engine.dice, BOARD_SIZE+40, 175)
    
    # Log Box
    pygame.draw.rect(screen, (30,40,50), (BOARD_SIZE+20, 245, PANEL_WIDTH-40, 390), border_radius=10)
    pygame.draw.rect(screen, (100,100,100), (BOARD_SIZE+20, 245, PANEL_WIDTH-40, 390), 1, border_radius=10)
    ly = 255
    for line in engine.log[-18:]:
        l_txt = small_font.render(line, True, C_TEXT_LIGHT)
        screen.blit(l_txt, (BOARD_SIZE+30, ly))
        ly += 20
        
    # Buttons are drawn by main loop

# --- MAIN ---

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Monopoly Game")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont('Arial', 24, bold=True)
    small_font = pygame.font.SysFont('Arial', 14)
    btn_font = pygame.font.SysFont('Arial', 18, bold=True)
    
    engine = GameEngine()
    input_text = ""
    selected_player_idx = 0
    money_options = [1000, 1500, 2000, 2500]

    bx = BOARD_SIZE + 45
    bw = 440

    # 1. Player Count Selector Buttons (2, 3, 4 players)
    btns_player_count = [
        Button(bx, 118, 140, 42, "2 Players", (80, 85, 95), (100, 105, 115), "P_2"),
        Button(bx + 150, 118, 140, 42, "3 Players", (80, 85, 95), (100, 105, 115), "P_3"),
        Button(bx + 300, 118, 140, 42, "4 Players", (80, 85, 95), (100, 105, 115), "P_4"),
    ]

    # 2. Starting Money Dropdown
    dd_money = Dropdown(bx, 180, bw, 46, "Starting Money", money_options, engine.s_money, "S_MON")

    # 3. Settings Toggles (Red / Blue when ON, Grayscaled when OFF)
    toggles_settings = [
        ToggleSwitch(bx, 245, bw, 46, "Bank Loans (15% Interest)", active=engine.s_loans, on_color=(220, 50, 60), action_id="S_LOA"),
        ToggleSwitch(bx, 305, bw, 46, "Vacation Pot Jackpot", active=engine.s_vacation, on_color=(30, 144, 255), action_id="S_VAC"),
        ToggleSwitch(bx, 365, bw, 46, "House & Hotel Building", active=engine.s_build, on_color=(30, 144, 255), action_id="S_BLD"),
    ]

    # 4. Settings to Lobby Button
    btn_to_lobby = Button(bx, 435, bw, 52, "GO TO LOBBY", C_SUCCESS, (80, 205, 100), "TO_LOBBY")

    # 5. Lobby Buttons
    btn_set_name = Button(bx + 320, 310, 120, 42, "SET NAME", C_ACCENT, (100, 160, 220), "SET_NAME")
    btn_lobby_start = Button(bx, 370, bw, 52, "START GAME", C_SUCCESS, (80, 205, 100), "START_G")
    btn_lobby_back = Button(bx, 435, bw, 42, "← BACK TO SETTINGS", (80, 85, 95), (100, 105, 115), "BACK_SETTINGS")

    # 6. Gameplay Sidebar Buttons
    btns_game = [
        Button(bx, 650, 130, 48, "ROLL", C_SUCCESS, (80,200,100), "ROLL"),
        Button(bx+155, 650, 130, 48, "BUY", C_ACCENT, (100,160,220), "BUY"),
        Button(bx+310, 650, 130, 48, "BUILD", (70,130,180), (90,150,200), "BUILD"),
        Button(bx, 715, 210, 46, "END TURN", C_ERROR, (240,80,80), "END"),
        Button(bx+230, 715, 210, 46, "LOAN (+500)", C_HIGHLIGHT, (255,235,100), "LOAN"),
    ]

    btn_play_again = Button(bx, 180, bw, 50, "PLAY AGAIN", C_SUCCESS, (80, 200, 80), "PLAY_AGAIN")

    running = True
    while running:
        screen.fill(C_BG)
        mouse_pos = pygame.mouse.get_pos()
        
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            
            # Text Input (Lobby rename)
            if engine.state == "LOBBY" and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif e.key == pygame.K_RETURN:
                    if input_text.strip() and engine.players:
                        engine.players[selected_player_idx].name = input_text.strip()
                        selected_player_idx = (selected_player_idx + 1) % len(engine.players)
                        input_text = engine.players[selected_player_idx].name
                elif len(input_text) < 14 and e.unicode.isprintable():
                    input_text += e.unicode

            # Clicks
            if e.type == pygame.MOUSEBUTTONDOWN:
                if engine.state == "SETTINGS":
                    # Check dropdown first to handle click priority
                    handled, new_money = dd_money.handle_click(e.pos)
                    if handled:
                        if new_money is not None:
                            engine.s_money = new_money
                            for p in engine.players:
                                p.money = engine.s_money
                    else:
                        # Player count buttons
                        for b in btns_player_count:
                            if b.rect.collidepoint(e.pos):
                                count = int(b.action_id.split("_")[1])
                                engine.s_players = count
                        
                        # Toggles
                        for t in toggles_settings:
                            if t.rect.collidepoint(e.pos):
                                is_on = t.toggle()
                                if t.action_id == "S_LOA":
                                    engine.s_loans = is_on
                                elif t.action_id == "S_VAC":
                                    engine.s_vacation = is_on
                                elif t.action_id == "S_BLD":
                                    engine.s_build = is_on
                                    
                        # Go to lobby button
                        if btn_to_lobby.rect.collidepoint(e.pos):
                            engine.sync_players()
                            selected_player_idx = 0
                            input_text = engine.players[0].name if engine.players else ""
                            engine.state = "LOBBY"
                
                elif engine.state == "LOBBY":
                    if btn_lobby_back.rect.collidepoint(e.pos):
                        engine.state = "SETTINGS"
                    elif btn_lobby_start.rect.collidepoint(e.pos) and len(engine.players) >= 2:
                        engine.state = "IDLE"
                        engine.log_msg(f"Game started with {len(engine.players)} players! {engine.players[0].name}'s Turn")
                    elif btn_set_name.rect.collidepoint(e.pos):
                        if input_text.strip() and engine.players:
                            engine.players[selected_player_idx].name = input_text.strip()
                            selected_player_idx = (selected_player_idx + 1) % len(engine.players)
                            input_text = engine.players[selected_player_idx].name
                    else:
                        # Check clicking on player card in lobby to select for editing
                        y_chk = 98
                        for idx, p in enumerate(engine.players):
                            c_rect = pygame.Rect(bx, y_chk, bw, 40)
                            if c_rect.collidepoint(e.pos):
                                selected_player_idx = idx
                                input_text = p.name
                            y_chk += 46
                
                elif engine.state == "GAME_OVER":
                    if btn_play_again.rect.collidepoint(e.pos):
                        engine = GameEngine()
                        input_text = ""
                        selected_player_idx = 0
                        dd_money.selected_value = engine.s_money
                        toggles_settings[0].active = engine.s_loans
                        toggles_settings[1].active = engine.s_vacation
                        toggles_settings[2].active = engine.s_build
                
                elif engine.state in ["IDLE", "ACTION"]:
                    for b in btns_game:
                        if b.rect.collidepoint(e.pos):
                            if b.action_id == "ROLL" and engine.state == "IDLE": 
                                engine.start_roll()
                            elif b.action_id == "BUY" and engine.state == "ACTION": 
                                engine.buy_prop()
                            elif b.action_id == "END": 
                                if engine.state not in ["MOVING", "ROLLING_DICE", "HOPPING"]: 
                                    engine.state = "IDLE"
                                    engine.next_turn()
                            elif b.action_id == "LOAN" and engine.s_loans:
                                p = engine.players[engine.curr_idx]
                                if p.loan == 0:
                                    p.loan = 500
                                    p.money += 500
                                    p.loan_turns = 5
                                    engine.log_msg(f"{p.name} took loan 500")
                                else:
                                    engine.log_msg("Already have active loan!")
                            elif b.action_id == "BUILD" and engine.s_build:
                                engine.build_house()

        # --- UPDATE ANIMATIONS ---
        if engine.state == "ROLLING_DICE" and engine.dice_anim:
            engine.dice_anim.update()
        elif engine.state == "HOPPING" and engine.hop_anim:
            engine.hop_anim.update()

        # --- RENDER ---
        draw_board(screen, engine, font, small_font)
        
        # Draw 3D Figurine Pawns on Board
        if engine.state not in ["SETTINGS", "LOBBY"]:
            for idx, p in enumerate(engine.players):
                is_turn = (engine.players and engine.players[engine.curr_idx] == p and engine.state in ["IDLE", "ACTION"])
                if engine.state == "HOPPING" and engine.hop_anim and engine.hop_anim.player == p:
                    gx, gy, z = engine.hop_anim.get_current_draw_pos()
                    draw_3d_pawn(screen, int(gx), int(gy), z, p.color, is_active=True, squash=engine.hop_anim.squash)
                else:
                    gx, gy = get_space_center(p.position, idx, len(engine.players))
                    draw_3d_pawn(screen, int(gx), int(gy), 0, p.color, is_active=is_turn)

        # Draw 3D Tumbling Dice on Board Center
        if engine.state == "ROLLING_DICE" and engine.dice_anim:
            engine.dice_anim.draw(screen)

        draw_ui(screen, engine, font, small_font, [], selected_player_idx)

        # Draw Contextual Controls
        if engine.state == "SETTINGS":
            # 1. Player Count Buttons
            for b in btns_player_count:
                count = int(b.action_id.split("_")[1])
                is_sel = (engine.s_players == count)
                b.color = (30, 144, 255) if is_sel else (80, 85, 95)
                b.hover_color = (70, 170, 255) if is_sel else (100, 105, 115)
                b.check_hover(mouse_pos)
                b.draw(screen, btn_font)
                
            # 2. Closed Dropdown
            dd_money.check_hover(mouse_pos)
            dd_money.draw_closed(screen, font, small_font)
            
            # 3. Toggle Switches
            for t in toggles_settings:
                t.check_hover(mouse_pos)
                t.draw(screen, font, small_font)
                
            # 4. Go to Lobby Button
            btn_to_lobby.check_hover(mouse_pos)
            btn_to_lobby.draw(screen, btn_font)
            
            # 5. Open Dropdown Options list (drawn on top of all other widgets)
            dd_money.draw_open_menu(screen, font, mouse_pos)
        
        elif engine.state == "LOBBY":
            # Rename Input Box
            input_rect = pygame.Rect(bx, 310, 310, 42)
            pygame.draw.rect(screen, WHITE, input_rect, border_radius=6)
            pygame.draw.rect(screen, C_ACCENT, input_rect, 2, border_radius=6)
            
            if input_text:
                txt_surf = font.render(input_text, True, BLACK)
            else:
                txt_surf = small_font.render(f"Name for Player {selected_player_idx + 1}...", True, (160, 160, 160))
            screen.blit(txt_surf, (bx + 12, 310 + (42 - txt_surf.get_height()) // 2))
            
            btn_set_name.check_hover(mouse_pos)
            btn_set_name.draw(screen, btn_font)
            
            btn_lobby_start.check_hover(mouse_pos)
            btn_lobby_start.draw(screen, btn_font)
            
            btn_lobby_back.check_hover(mouse_pos)
            btn_lobby_back.draw(screen, btn_font)
                
        elif engine.state == "GAME_OVER":
            btn_play_again.check_hover(mouse_pos)
            btn_play_again.draw(screen, btn_font)
            
        else:
            # Game Buttons
            curr_p = engine.players[engine.curr_idx] if engine.players else None
            for b in btns_game:
                if b.action_id == "BUY":
                    b.color = C_ACCENT if engine.state == "ACTION" else (100, 100, 100)
                elif b.action_id == "ROLL":
                    b.color = C_SUCCESS if engine.state == "IDLE" else (100, 100, 100)
                elif b.action_id == "BUILD":
                    can_b, _ = engine.can_build_house(curr_p) if curr_p else (False, None)
                    b.color = (70, 130, 180) if (engine.s_build and can_b) else (100, 100, 100)
                elif b.action_id == "LOAN":
                    b.color = C_HIGHLIGHT if (engine.s_loans and curr_p and curr_p.loan == 0) else (100, 100, 100)
                
                b.check_hover(mouse_pos)
                b.draw(screen, btn_font)
                
        # Popup Overlay
        if engine.state == "POPUP":
            engine.popup_timer -= 1
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,128))
            screen.blit(overlay, (0,0))
            
            # Card
            pygame.draw.rect(screen, WHITE, (CENTER_X-150, CENTER_Y-100, 300, 200), border_radius=10)
            pygame.draw.rect(screen, C_ACCENT, (CENTER_X-150, CENTER_Y-100, 300, 200), 4, border_radius=10)
            
            msg = font.render(engine.popup_msg, True, BLACK)
            screen.blit(msg, (CENTER_X - msg.get_width()//2, CENTER_Y))
            
            if engine.popup_timer <= 0:
                if engine.pending_hop_steps > 0:
                    curr_p = engine.players[engine.curr_idx]
                    engine.start_pawn_hop(curr_p, engine.pending_hop_steps, on_complete=engine.handle_land)
                    engine.pending_hop_steps = 0
                else:
                    engine.state = "IDLE"

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())