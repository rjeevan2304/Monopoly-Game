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
        self.state = "SETTINGS" # SETTINGS, LOBBY, IDLE, MOVING, ACTION, POPUP, GAME_OVER
        self.log = ["Welcome to Monopoly!"]
        self.vacation_pot = 0
        self.dice = (1, 1)
        self.popup_timer = 0
        self.popup_msg = ""
        self.winner = None
        
        # Settings
        self.s_money = 1500
        self.s_loans = True
        self.s_mortgage = True
        self.s_build = True
        self.s_vacation = True

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

        d1 = random.randint(1,6)
        d2 = random.randint(1,6)
        self.dice = (d1, d2)
        total = d1 + d2
        self.log_msg(f"{p.name} rolled {total}")
        
        # Prison Logic
        if p.in_prison:
            if d1 == d2:
                p.in_prison = False
                self.log_msg("Doubles! Free!")
            else:
                p.prison_turns += 1
                if p.prison_turns >= 3:
                    p.in_prison = False
                    p.money -= 25
                    self.log_msg("Time served. Paid 25.")
                    if self.check_bankruptcy(p):
                        return
                else:
                    self.state = "IDLE"
                    self.next_turn()
                    return

        # Move
        old_pos = p.position
        p.position = (p.position + total) % 40
        if p.position < old_pos:
            p.money += 250
            self.log_msg("Passed Start! +250")

        self.handle_land()

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
                p.position = (p.position + 3) % 40
                self.handle_land()
                return
            self.state = "POPUP"
            self.popup_timer = 60 # 2 seconds

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
    # Draw two dice faces
    for i, val in enumerate(dice):
        dx = x + (i * 60)
        pygame.draw.rect(screen, WHITE, (dx, y, 50, 50), border_radius=8)
        pygame.draw.rect(screen, BLACK, (dx, y, 50, 50), 2, border_radius=8)
        
        # Dots
        c = (dx+25, y+25)
        pts = []
        if val == 1: pts = [c]
        elif val == 2: pts = [(dx+15, y+15), (dx+35, y+35)]
        elif val == 3: pts = [(dx+15, y+15), c, (dx+35, y+35)]
        elif val == 4: pts = [(dx+15, y+15), (dx+35, y+15), (dx+15, y+35), (dx+35, y+35)]
        elif val == 5: pts = [(dx+15, y+15), (dx+35, y+15), c, (dx+15, y+35), (dx+35, y+35)]
        elif val == 6: pts = [(dx+15, y+15), (dx+35, y+15), (dx+15, y+25), (dx+35, y+25), (dx+15, y+35), (dx+35, y+35)]
        
        for pt in pts:
            pygame.draw.circle(screen, BLACK, pt, 4)

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
                if 0 <= i <= 10: pygame.draw.rect(screen, c, (rx, ry, cell_w, 20)) # Top of cell (which is actually bottom of board?)
                elif 11 <= i <= 20: pygame.draw.rect(screen, c, (rx+cell_w-20, ry, 20, cell_w)) 
                elif 21 <= i <= 30: pygame.draw.rect(screen, c, (rx, ry+cell_w-20, cell_w, 20))
                else: pygame.draw.rect(screen, c, (rx, ry, 20, cell_w))
        
        # Text
        lines = s.name.split(" ")
        ty = ry + 25
        for line in lines:
            txt = small_font.render(line, True, BLACK)
            screen.blit(txt, (rx + (cell_w - txt.get_width())/2, ty))
            ty += 12

        # Owner Dot & Houses
        if s.owner:
            pygame.draw.circle(screen, s.owner.color, (rx+cell_w-10, ry+cell_w-10), 6)
            if s.houses > 0:
                h_text = "HOTEL" if s.houses == 5 else f"{s.houses}H"
                h_col = C_ERROR if s.houses == 5 else (34, 139, 34)
                h_surf = small_font.render(h_text, True, h_col)
                screen.blit(h_surf, (rx + 4, ry + cell_w - 18))
        elif s.price > 0:
            p_surf = small_font.render(f"Rs {s.price}", True, (110, 110, 110))
            screen.blit(p_surf, (rx + (cell_w - p_surf.get_width()) / 2, ry + cell_w - 18))
            
    # Center Logo
    title = font.render("MONOPOLY", True, C_PANEL)
    screen.blit(title, (CENTER_X - title.get_width()//2, CENTER_X - 40))
    pot = small_font.render(f"Vacation Pot: Rs {engine.vacation_pot}", True, C_ACCENT)
    screen.blit(pot, (CENTER_X - pot.get_width()//2, CENTER_X + 20))

def draw_ui(screen, engine, font, small_font, buttons):
    # Panel Background
    pygame.draw.rect(screen, C_PANEL, (BOARD_SIZE, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    
    # State: SETTINGS
    if engine.state == "SETTINGS":
        t = font.render("GAME SETTINGS", True, C_HIGHLIGHT)
        screen.blit(t, (BOARD_SIZE + 50, 40))
        sub = small_font.render("Click options to customize rules:", True, C_TEXT_LIGHT)
        screen.blit(sub, (BOARD_SIZE + 50, 75))
        return

    # State: LOBBY
    if engine.state == "LOBBY":
        t = font.render("LOBBY", True, C_HIGHLIGHT)
        screen.blit(t, (BOARD_SIZE + 50, 40))
        sub = small_font.render("Add 2-4 players to start the game:", True, C_TEXT_LIGHT)
        screen.blit(sub, (BOARD_SIZE + 50, 75))
        y = 105
        for p in engine.players:
            pygame.draw.circle(screen, p.color, (BOARD_SIZE + 50, y + 8), 7)
            p_txt = small_font.render(f"{p.name} (Rs {p.money})", True, C_TEXT_LIGHT)
            screen.blit(p_txt, (BOARD_SIZE + 65, y))
            y += 26
        return

    # State: GAME_OVER
    if engine.state == "GAME_OVER":
        t = font.render("GAME OVER", True, C_ERROR)
        screen.blit(t, (BOARD_SIZE + 50, 40))
        if engine.winner:
            w_txt = font.render(f"{engine.winner.name} WINS!", True, C_HIGHLIGHT)
            screen.blit(w_txt, (BOARD_SIZE + 50, 90))
            bal_txt = small_font.render(f"Final Balance: Rs {engine.winner.money}", True, C_TEXT_LIGHT)
            screen.blit(bal_txt, (BOARD_SIZE + 50, 130))
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
    
    font = pygame.font.SysFont('Arial', 28, bold=True)
    small_font = pygame.font.SysFont('Arial', 14)
    btn_font = pygame.font.SysFont('Arial', 20, bold=True)
    
    engine = GameEngine()
    input_text = ""
    money_options = [1000, 1500, 2000, 2500]

    def add_player():
        nonlocal input_text
        name = input_text.strip()
        if name and len(engine.players) < 4:
            colors = [(220, 20, 60), (30, 144, 255), (34, 139, 34), (255, 215, 0)]
            c = colors[len(engine.players) % len(colors)]
            engine.players.append(Player(name, c, engine.s_money))
            input_text = ""
    
    # Button Definitions
    bx = BOARD_SIZE + 40
    btns_game = [
        Button(bx, 650, 120, 50, "ROLL", C_SUCCESS, (80,200,100), "ROLL"),
        Button(bx+140, 650, 120, 50, "BUY", C_ACCENT, (100,160,220), "BUY"),
        Button(bx, 715, 260, 45, "END TURN", C_ERROR, (240,80,80), "END"),
        Button(bx, 775, 120, 40, "LOAN", C_HIGHLIGHT, (255,235,100), "LOAN"),
        Button(bx+140, 775, 120, 40, "BUILD", (70,130,180), (90,150,200), "BUILD"),
    ]
    
    btn_lobby_add = Button(bx+170, 230, 90, 40, "ADD", C_SUCCESS, (80,200,100), "ADD_P")
    btn_lobby_start = Button(bx, 290, 260, 50, "START GAME", C_ACCENT, (100,160,220), "START_G")

    btns_settings = [
        Button(bx, 110, 260, 40, f"START MONEY: {engine.s_money}", (100,100,100), (120,120,120), "S_MON"),
        Button(bx, 165, 260, 40, f"LOANS: {'ON' if engine.s_loans else 'OFF'}", (100,100,100), (120,120,120), "S_LOA"),
        Button(bx, 220, 260, 40, f"VACATION POT: {'ON' if engine.s_vacation else 'OFF'}", (100,100,100), (120,120,120), "S_VAC"),
        Button(bx, 275, 260, 40, f"HOUSE BUILDING: {'ON' if engine.s_build else 'OFF'}", (100,100,100), (120,120,120), "S_BLD"),
        Button(bx, 350, 260, 50, "GO TO LOBBY", C_SUCCESS, (80,200,80), "TO_LOBBY")
    ]

    btn_play_again = Button(bx, 180, 260, 50, "PLAY AGAIN", C_SUCCESS, (80, 200, 80), "PLAY_AGAIN")

    running = True
    while running:
        screen.fill(C_BG)
        mouse_pos = pygame.mouse.get_pos()
        
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            
            # Text Input (Lobby)
            if engine.state == "LOBBY" and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif e.key == pygame.K_RETURN:
                    add_player()
                elif len(input_text) < 14 and e.unicode.isprintable():
                    input_text += e.unicode

            # Clicks
            if e.type == pygame.MOUSEBUTTONDOWN:
                if engine.state == "SETTINGS":
                    for b in btns_settings:
                        if b.rect.collidepoint(e.pos):
                            if b.action_id == "TO_LOBBY":
                                engine.state = "LOBBY"
                            elif b.action_id == "S_MON":
                                m_idx = (money_options.index(engine.s_money) + 1) % len(money_options)
                                engine.s_money = money_options[m_idx]
                                b.text = f"START MONEY: {engine.s_money}"
                            elif b.action_id == "S_LOA":
                                engine.s_loans = not engine.s_loans
                                b.text = f"LOANS: {'ON' if engine.s_loans else 'OFF'}"
                            elif b.action_id == "S_VAC":
                                engine.s_vacation = not engine.s_vacation
                                b.text = f"VACATION POT: {'ON' if engine.s_vacation else 'OFF'}"
                            elif b.action_id == "S_BLD":
                                engine.s_build = not engine.s_build
                                b.text = f"HOUSE BUILDING: {'ON' if engine.s_build else 'OFF'}"
                
                elif engine.state == "LOBBY":
                    if btn_lobby_add.rect.collidepoint(e.pos):
                        add_player()
                    elif btn_lobby_start.rect.collidepoint(e.pos) and len(engine.players) >= 2:
                        engine.state = "IDLE"
                        engine.log_msg(f"Game started! {engine.players[0].name}'s Turn")
                
                elif engine.state == "GAME_OVER":
                    if btn_play_again.rect.collidepoint(e.pos):
                        engine = GameEngine()
                        input_text = ""
                
                elif engine.state in ["IDLE", "ACTION"]:
                    for b in btns_game:
                        if b.rect.collidepoint(e.pos):
                            if b.action_id == "ROLL" and engine.state == "IDLE": 
                                engine.state = "MOVING"
                                engine.roll()
                            elif b.action_id == "BUY" and engine.state == "ACTION": 
                                engine.buy_prop()
                            elif b.action_id == "END": 
                                if engine.state != "MOVING": 
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

        # --- RENDER ---
        draw_board(screen, engine, font, small_font)
        
        # Draw Players on Board
        if engine.state not in ["SETTINGS", "LOBBY"]:
            for idx, p in enumerate(engine.players):
                cell_w = BOARD_SIZE/11
                i = p.position
                if 0<=i<=10: cx, cy = BOARD_SIZE - cell_w - (i*cell_w) + cell_w/2, BOARD_SIZE - cell_w/2
                elif 11<=i<=20: cx, cy = cell_w/2, BOARD_SIZE - cell_w - ((i-10)*cell_w) + cell_w/2
                elif 21<=i<=30: cx, cy = (i-20)*cell_w + cell_w/2, cell_w/2
                else: cx, cy = BOARD_SIZE - cell_w/2, (i-30)*cell_w + cell_w/2
                
                off = (idx*6) - 9
                pygame.draw.circle(screen, BLACK, (int(cx+off), int(cy+off)), 10)
                pygame.draw.circle(screen, p.color, (int(cx+off), int(cy+off)), 8)

        draw_ui(screen, engine, font, small_font, [])

        # Draw Contextual Buttons
        if engine.state == "SETTINGS":
            for b in btns_settings:
                b.check_hover(mouse_pos)
                b.draw(screen, btn_font)
        
        elif engine.state == "LOBBY":
            # Input Box
            input_rect = pygame.Rect(bx, 230, 160, 40)
            pygame.draw.rect(screen, WHITE, input_rect, border_radius=6)
            pygame.draw.rect(screen, C_ACCENT, input_rect, 2, border_radius=6)
            
            if input_text:
                txt_surf = small_font.render(input_text, True, BLACK)
            else:
                txt_surf = small_font.render("Player name...", True, (160, 160, 160))
            screen.blit(txt_surf, (bx + 10, 242))
            
            btn_lobby_add.check_hover(mouse_pos)
            btn_lobby_add.draw(screen, btn_font)
            
            if len(engine.players) >= 2:
                btn_lobby_start.check_hover(mouse_pos)
                btn_lobby_start.draw(screen, btn_font)
                
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
                engine.state = "IDLE"

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())