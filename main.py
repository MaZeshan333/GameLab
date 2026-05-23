import pygame
import random
import nltk
import requests
import json
import threading
import math
from nltk.corpus import words

# --- Firebase Configuration ---
FIREBASE_URL = "https://gamelab-6855e-default-rtdb.firebaseio.com/leaderboard.json"

# Initializing Dictionary
try:
    word_set = set(w.upper() for w in words.words())
except:
    print("Downloading dictionary data...")
    nltk.download("words")
    word_set = set(w.upper() for w in words.words())

# --- Configurable Match Time Settings ---
ARCADE_START_SECONDS = 300   # Switched default timer limit to 300s
ARCADE_BONUS_SECONDS = 3    # Change this to set the seconds rewarded per word

# --- Configuration ---
FPS = 60
GRID_SIZE = 7
CELL_SIZE = 70
GRID_OFFSET_X = 40
GRID_OFFSET_Y = 120

SCREEN_WIDTH = (CELL_SIZE * GRID_SIZE) + 260
SCREEN_HEIGHT = (CELL_SIZE * GRID_SIZE) + 240

# --- Modern & Elegant Color Palette ---
BG_COLOR = (24, 24, 28)          
CARD_BG = (36, 36, 44)           
TEXT_MAIN = (240, 240, 245)      
TEXT_MUTED = (140, 140, 160)     

COLOR_BLUE = (59, 130, 246)      
COLOR_GREEN = (16, 185, 129)     
COLOR_RED = (239, 68, 68)        
COLOR_GOLD = (245, 158, 11)      
COLOR_PURPLE = (139, 92, 246)    

# High contrast borders for matrix visibility
GRID_BORDER_COLOR = (80, 80, 100)  

LETTER_FREQ = {
    "A": 0.078, "B": 0.020, "C": 0.040, "D": 0.038, "E": 0.110,
    "F": 0.014, "G": 0.030, "H": 0.023, "I": 0.086, "J": 0.0025,
    "K": 0.0097, "L": 0.053, "M": 0.027, "N": 0.072, "O": 0.061,
    "P": 0.028, "Q": 0.0019, "R": 0.073, "S": 0.087, "T": 0.067,
    "U": 0.033, "V": 0.010, "W": 0.0091, "X": 0.0027, "Y": 0.016, "Z": 0.0044,
}

class CloudWordBattle:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("7x7 Word Battle - Premium Edition")
        self.clock = pygame.time.Clock()

        # --- Safe Font Loader Engine (Bypasses Corrupted Win32 Registries) ---
        try:
            self.title_font = pygame.font.SysFont("Segoe UI", 44, bold=True)
            self.main_font = pygame.font.SysFont("Segoe UI", 30, bold=True)
            self.ui_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
            self.small_font = pygame.font.SysFont("Segoe UI", 15, bold=False)
            self.rule_font = pygame.font.SysFont("Segoe UI", 17)
        except TypeError:
            print("[System Alert] Windows font registry anomalies detected. Safe fallback initialized.")
            self.title_font = pygame.font.Font(None, 54)
            self.main_font = pygame.font.Font(None, 38)
            self.ui_font = pygame.font.Font(None, 26)
            self.small_font = pygame.font.Font(None, 20)
            self.rule_font = pygame.font.Font(None, 22)

        # Game States: RULES, NAME_ENTRY, MODE_SELECT, PLAYING, FINISH
        self.state = "RULES"  
        self.selected_mode = None  
        self.player_name = ""
        self.leaderboard_data = []
        
        # UI Animations & Controls
        self.current_rule_page = 0
        self.animation_timer = 0.0
        
        # Base Game Parameters Initialization
        self.grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_letter = self.get_random_letter()
        self.score = 0
        self.input_text = ""
        self.status_msg = "Click on a column to drop letters!"
        self.start_ticks = 0
        self.game_active = True
        self.uploading = False

        # Background Floating Particles for Rules
        self.particles = [{"x": random.randint(0, SCREEN_WIDTH), "y": random.randint(150, SCREEN_HEIGHT-100), 
                           "char": random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), "speed": random.uniform(0.3, 0.8)} for _ in range(15)]

        # Fetch cloud ranks instantly
        threading.Thread(target=self.fetch_leaderboard, daemon=True).start()

    def reset_game(self):
        """Resets only structural game elements, preservation of player identity"""
        self.grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_letter = self.get_random_letter()
        self.score = 0
        self.input_text = ""
        self.status_msg = "Click on a column to drop letters!"
        self.game_active = True
        self.uploading = False

    def get_random_letter(self):
        return random.choices(
            population=list(LETTER_FREQ.keys()), weights=list(LETTER_FREQ.values()), k=1
        )[0]

    def fetch_leaderboard(self):
        try:
            response = requests.get(FIREBASE_URL, timeout=5)
            if response.status_code == 200 and response.json():
                data = response.json()
                raw_list = list(data.values()) if isinstance(data, dict) else data
                # Filter out everything that isn't uploaded as an ARCADE run
                filtered_list = [x for x in raw_list if isinstance(x, dict) and x.get("mode") == "ARCADE"]
                self.leaderboard_data = sorted(
                    filtered_list, key=lambda x: x["score"], reverse=True
                )[:20]
        except Exception as e:
            print(f"Fetch Error: {e}")

    def upload_score(self):
        # Strict Restriction: Only upload score streams if current module is ARCADE
        if self.selected_mode != "ARCADE" or self.score <= 0 or not self.player_name:
            return
        self.uploading = True
        payload = {"name": self.player_name, "score": self.score, "mode": "ARCADE"}
        try:
            requests.post(FIREBASE_URL, json=payload, timeout=5)
            self.fetch_leaderboard()
        except Exception as e:
            print(f"Upload Error: {e}")
        self.uploading = False

    def is_game_over(self):
        for c in range(GRID_SIZE):
            if self.grid[0][c] != "":
                return True
        return False

    def drop_letter(self, col):
        for r in range(GRID_SIZE - 1, -1, -1):
            if self.grid[r][col] == "":
                self.grid[r][col] = self.next_letter
                self.next_letter = self.get_random_letter()
                return True
        return False

    def check_and_remove(self, word):
        word = word.upper().strip()
        if not (word in word_set and len(word) >= 2):
            self.status_msg = f"'{word}' is invalid!"
            return False

        found = False
        cells_to_clear = set()

        def mark_matches(sequence, coords):
            nonlocal found
            for target in (word, word[::-1]):
                start = sequence.find(target)
                if start != -1:
                    for i in range(start, start + len(target)):
                        cells_to_clear.add(coords[i])
                    found = True
                    return True
            return False

        # Horizontal Analysis
        for r in range(GRID_SIZE):
            row_str = "".join([self.grid[r][c] if self.grid[r][c] != "" else " " for c in range(GRID_SIZE)])
            row_coords = [(r, c) for c in range(GRID_SIZE)]
            if mark_matches(row_str, row_coords): break

        # Vertical Analysis
        if not found:
            for c in range(GRID_SIZE):
                col_str = "".join([self.grid[r][c] if self.grid[r][c] != "" else " " for r in range(GRID_SIZE)])
                col_coords = [(r, c) for r in range(GRID_SIZE)]
                if mark_matches(col_str, col_coords): break

        # Diagonal Analysis
        if not found:
            for start_nodes in [
                [(0, c) for c in range(GRID_SIZE)] + [(r, 0) for r in range(1, GRID_SIZE)],
                [(0, c) for c in range(GRID_SIZE)] + [(r, GRID_SIZE - 1) for r in range(1, GRID_SIZE)],
            ]:
                is_back = start_nodes[-1][1] != 0
                for r, c in start_nodes:
                    diag_str, coords = "", []
                    curr_r, curr_c = r, c
                    while 0 <= curr_r < GRID_SIZE and 0 <= curr_c < GRID_SIZE:
                        diag_str += self.grid[curr_r][curr_c] if self.grid[curr_r][curr_c] != "" else " "
                        coords.append((curr_r, curr_c))
                        curr_r, curr_c = (curr_r + 1, curr_c - 1) if is_back else (curr_r + 1, curr_c + 1)
                    if mark_matches(diag_str, coords): break
                if found: break

        if found:
            for r, c in cells_to_clear:
                self.grid[r][c] = ""
            
            # Re-apply Matrix Gravity
            for c in range(GRID_SIZE):
                letters = [self.grid[r][c] for r in range(GRID_SIZE) if self.grid[r][c] != ""]
                new_col = [""] * (GRID_SIZE - len(letters)) + letters
                for r in range(GRID_SIZE):
                    self.grid[r][c] = new_col[r]

            bonus = len(word) * 30
            self.score += bonus
            
            if self.selected_mode == "ARCADE":
                self.start_ticks += (ARCADE_BONUS_SECONDS * 1000)  
            
            self.status_msg = f"Cleared '{word}'! +{bonus} pts"
            
            if self.selected_mode == "PRACTICE" and self.is_game_over():
                self.game_active = False
                self.state = "FINISH"
                
        return found

    def draw_rules(self):
        self.screen.fill(BG_COLOR)
        self.animation_timer += 0.05
        pulse_val = int((math.sin(self.animation_timer) + 1) * 30)

        # Draw elegant shifting particles background
        for p in self.particles:
            p["x"] += p["speed"]
            if p["x"] > SCREEN_WIDTH + 20:
                p["x"] = -20
                p["y"] = random.randint(150, SCREEN_HEIGHT-100)
            p_surface = self.small_font.render(p["char"], True, (40, 45, 60))
            self.screen.blit(p_surface, (int(p["x"]), int(p["y"])))

        # Header Title
        title = self.title_font.render("GAME MANUAL", True, TEXT_MAIN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 35))
        
        page_text = self.ui_font.render(f"{self.current_rule_page + 1} / 3", True, TEXT_MUTED)
        self.screen.blit(page_text, (SCREEN_WIDTH - 80, 45))

        # Main Info Box Frame
        rule_box = pygame.Rect(40, 110, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 230)
        pygame.draw.rect(self.screen, CARD_BG, rule_box, border_radius=12)
        
        r_glow = max(0, min(255, 60 + pulse_val))
        g_glow = max(0, min(255, 100 + pulse_val))
        b_glow = max(0, min(255, 200 + pulse_val))
        border_color = (r_glow, g_glow, b_glow)
        pygame.draw.rect(self.screen, border_color, rule_box, 2, border_radius=12)

        # Content Rendering Engine based on active index
        y_offset = 135
        if self.current_rule_page == 0:
            # Academic/Course metadata banner at the absolute beginning of the rulesheet
            meta_label = self.small_font.render("WordPuyo  GameLab CS 2025 - 2026 | Authors: Zeshan MA & Luke OGURO", True, COLOR_GOLD)
            self.screen.blit(meta_label, (65, y_offset))
            y_offset += 35

            items = ["🎯 CORE OBJECTIVE", "", "1. Letters drop down sequentially upon clicking columns.", 
                     "2. Link letters to forge valid words inside the grid structure via:", 
                     "   • Horizontal Rows (Left to Right)", "   • Vertical Columns (Top to Bottom)", "   • Diagonals (Both orientations)", 
                     "", "3. Words can be evaluated forwards OR backwards seamlessly.", "4. Minimum required word validation threshold is 2 letters.",
                     "5. Validated strings vanish, collapsing upper cells downward."]
        elif self.current_rule_page == 1:
            items = ["🎮 SYSTEM INTERACTION", "", "鼠标 MOUSE COMMANDS:", "   • Left-Click specified column array to deploy targeted token.",
                     "", "键盘 HARDWARE KEYBOARD:", "   • Input letters dynamically into your live input buffer.", "   • Press [ ENTER ] to evaluate and submit data.",
                     "   • Press [ BACKSPACE ] to erase recent buffered tokens.", "   • Press [ ESC ] at any state to fallback to primary menus."]
        else:
            items = ["⭐ SCORING Mechanics & MODULES", "", "• Score Generation: (Word Length × 30 Points)", "• Mathematical Target: Longer patterns generate maximum yields.", 
                     "", "⚔️ ARCADE CRITERIA:", f"   • Dynamic {ARCADE_START_SECONDS}-Second Session deployment.", f"   • Successful extractions append +{ARCADE_BONUS_SECONDS} Seconds directly to the delta.",
                     "   • Arcade metrics are uploaded to the Cloud ranking grid.", "", "📚 PRACTICE ENVIRONMENT:", "   • Standard structural parameters without timeline limits.", "   • Practice entries only display scores and bypass global ranks."]

        for line in items:
            if line == "":
                y_offset += 12
                continue
            color = COLOR_BLUE if ("🎯" in line or "🎮" in line or "⭐" in line) else TEXT_MAIN
            font = self.main_font if ("🎯" in line or "🎮" in line or "⭐" in line) else self.rule_font
            if "•" in line: color = COLOR_GOLD
            
            surf = font.render(line, True, color)
            self.screen.blit(surf, (65, y_offset))
            y_offset += 28

        # UI Nav Buttons Setup
        self.prev_rect = pygame.Rect(40, SCREEN_HEIGHT - 90, 120, 45)
        self.next_rect = pygame.Rect(SCREEN_WIDTH - 160, SCREEN_HEIGHT - 90, 120, 45)
        self.start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 90, 200, 45)

        if self.current_rule_page > 0:
            pygame.draw.rect(self.screen, COLOR_BLUE, self.prev_rect, border_radius=8)
            self.screen.blit(self.ui_font.render("PREV", True, TEXT_MAIN), (self.prev_rect.x + 35, self.prev_rect.y + 10))
        else:
            pygame.draw.rect(self.screen, (45, 45, 55), self.prev_rect, border_radius=8)
            self.screen.blit(self.ui_font.render("PREV", True, TEXT_MUTED), (self.prev_rect.x + 35, self.prev_rect.y + 10))

        if self.current_rule_page < 2:
            pygame.draw.rect(self.screen, COLOR_BLUE, self.next_rect, border_radius=8)
            self.screen.blit(self.ui_font.render("NEXT", True, TEXT_MAIN), (self.next_rect.x + 35, self.next_rect.y + 10))
        else:
            pygame.draw.rect(self.screen, COLOR_GREEN, self.start_rect, border_radius=8)
            self.screen.blit(self.ui_font.render("PROCEED 🚀", True, TEXT_MAIN), (self.start_rect.x + 50, self.start_rect.y + 10))

        hint = self.small_font.render("Tip: You can press ESC anytime to skip configuration pages", True, TEXT_MUTED)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 35))

    def draw_name_entry(self):
        self.screen.fill(BG_COLOR)
        
        title = self.title_font.render("WORD STACK BATTLE", True, COLOR_BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 90))
        
        lbl = self.ui_font.render("IDENTIFICATION INITIALS", True, TEXT_MAIN)
        self.screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, 200))
        
        box = pygame.Rect(SCREEN_WIDTH // 2 - 160, 250, 320, 55)
        pygame.draw.rect(self.screen, CARD_BG, box, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BLUE, box, 2, border_radius=8)
        
        disp = self.main_font.render(self.player_name if self.player_name else "|", True, TEXT_MAIN)
        self.screen.blit(disp, (box.x + 20, box.y + 8))
        
        i1 = self.small_font.render("Limitation: Max 10 characters [Alpha-Numeric characters only]", True, TEXT_MUTED)
        i2 = self.small_font.render("Press [ ENTER ] to confirm structural login profile", True, TEXT_MUTED)
        i3 = self.small_font.render("Press [ ESC ] to abort execution pipeline", True, TEXT_MUTED)
        
        self.screen.blit(i1, (SCREEN_WIDTH // 2 - i1.get_width() // 2, 350))
        self.screen.blit(i2, (SCREEN_WIDTH // 2 - i2.get_width() // 2, 380))
        self.screen.blit(i3, (SCREEN_WIDTH // 2 - i3.get_width() // 2, 410))

    def draw_mode_select(self):
        self.screen.fill(BG_COLOR)
        
        # Injected course identity and creator name strings inside the Main Menu Header
        gamelab_banner = self.small_font.render("WordPuyo    -  GameLab CS 2025 - 2026", True, COLOR_GOLD)
        creator_banner = self.small_font.render("DEVELOPED BY: ZESHAN MA & LUKE OGURO", True, TEXT_MUTED)
        self.screen.blit(gamelab_banner, (SCREEN_WIDTH // 2 - gamelab_banner.get_width() // 2, 15))
        self.screen.blit(creator_banner, (SCREEN_WIDTH // 2 - creator_banner.get_width() // 2, 35))

        p_info = self.ui_font.render(f"OPERATOR: {self.player_name}", True, COLOR_BLUE)
        self.screen.blit(p_info, (SCREEN_WIDTH // 2 - p_info.get_width() // 2, 65))
        
        title = self.main_font.render("SELECT OPERATIONAL ARCHETYPE", True, TEXT_MAIN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 115))
        
        self.arcade_rect = pygame.Rect(SCREEN_WIDTH // 2 - 190, 185, 175, 240)
        self.practice_rect = pygame.Rect(SCREEN_WIDTH // 2 + 15, 185, 175, 240)
        
        m_pos = pygame.mouse.get_pos()
        
        # Draw Arcade Deck Selection Frame
        arc_col = COLOR_RED if self.arcade_rect.collidepoint(m_pos) else (45, 45, 55)
        pygame.draw.rect(self.screen, CARD_BG, self.arcade_rect, border_radius=12)
        pygame.draw.rect(self.screen, arc_col, self.arcade_rect, 2, border_radius=12)
        
        self.screen.blit(self.ui_font.render("⚔️ ARCADE", True, COLOR_RED), (self.arcade_rect.x + 25, self.arcade_rect.y + 20))
        self.screen.blit(self.small_font.render("Timeline Sync:", True, TEXT_MAIN), (self.arcade_rect.x + 20, self.arcade_rect.y + 75))
        
        self.screen.blit(self.main_font.render(f"{ARCADE_START_SECONDS}s", True, COLOR_RED), (self.arcade_rect.x + 20, self.arcade_rect.y + 100))
        self.screen.blit(self.small_font.render(f"Clearance adds +{ARCADE_BONUS_SECONDS}s", True, TEXT_MUTED), (self.arcade_rect.x + 20, self.arcade_rect.y + 150))
        self.screen.blit(self.small_font.render("Global Cloud Rank", True, TEXT_MUTED), (self.arcade_rect.x + 20, self.arcade_rect.y + 185))

        # Draw Practice Deck Selection Frame
        prac_col = COLOR_GREEN if self.practice_rect.collidepoint(m_pos) else (45, 45, 55)
        pygame.draw.rect(self.screen, CARD_BG, self.practice_rect, border_radius=12)
        pygame.draw.rect(self.screen, prac_col, self.practice_rect, 2, border_radius=12)
        
        self.screen.blit(self.ui_font.render("📚 PRACTICE", True, COLOR_GREEN), (self.practice_rect.x + 20, self.practice_rect.y + 20))
        self.screen.blit(self.small_font.render("Infinite timeline", True, TEXT_MAIN), (self.practice_rect.x + 20, self.practice_rect.y + 75))
        self.screen.blit(self.small_font.render("Matrix focus engine", True, TEXT_MUTED), (self.practice_rect.x + 20, self.practice_rect.y + 120))
        self.screen.blit(self.small_font.render("Local Score Only", True, COLOR_GREEN), (self.practice_rect.x + 20, self.practice_rect.y + 150))

        inst = self.small_font.render("Select interactive module panel above to boot game engine loop", True, TEXT_MUTED)
        self.screen.blit(inst, (SCREEN_WIDTH // 2 - inst.get_width() // 2, 470))
        
        b_inst = self.small_font.render("Press [ ESC ] to revert back to registration terminal", True, TEXT_MUTED)
        self.screen.blit(b_inst, (SCREEN_WIDTH // 2 - b_inst.get_width() // 2, 500))

    def draw_playing(self):
        self.screen.fill(BG_COLOR)
        
        # Metrics Top Panel
        if self.selected_mode == "ARCADE":
            elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
            time_left = max(0, ARCADE_START_SECONDS - elapsed)  
            t_color = COLOR_RED if time_left < 10 else TEXT_MAIN
            t_surf = self.ui_font.render(f"TIMELINE: {time_left}s", True, t_color)
            self.screen.blit(t_surf, (GRID_OFFSET_X, 25))
        else:
            msg = "⚠️ CEILING CRITICAL! ⚠️" if self.is_game_over() else "UNLIMITED TIME PRACTICE"
            col = COLOR_RED if self.is_game_over() else COLOR_GREEN
            self.screen.blit(self.ui_font.render(msg, True, col), (GRID_OFFSET_X, 25))
            
        self.screen.blit(self.ui_font.render(f"SCORE: {self.score}", True, COLOR_GREEN), (240, 25))
        self.screen.blit(self.small_font.render(f"AGENT: {self.player_name}", True, COLOR_BLUE), (GRID_OFFSET_X, 60))
        self.screen.blit(self.small_font.render(f"SYSTEM: {self.status_msg}", True, TEXT_MUTED), (240, 60))

        m_col = COLOR_RED if self.selected_mode == "ARCADE" else COLOR_GREEN
        m_ind = self.small_font.render(f"MOD: {self.selected_mode}", True, m_col)
        self.screen.blit(m_ind, (SCREEN_WIDTH - 150, 25))

        # Preview Container Block Layout
        p_x = GRID_OFFSET_X + (GRID_SIZE * CELL_SIZE) + 35
        p_box = pygame.Rect(p_x, GRID_OFFSET_Y, 85, 95)
        pygame.draw.rect(self.screen, CARD_BG, p_box, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BLUE, p_box, 2, border_radius=8)
        
        self.screen.blit(self.small_font.render("NEXT TOKEN", True, TEXT_MUTED), (p_x + 6, GRID_OFFSET_Y - 22))
        c_surf = self.title_font.render(self.next_letter, True, COLOR_BLUE)
        self.screen.blit(c_surf, c_surf.get_rect(center=p_box.center))

        # Matrix Core Grid Interface Rendering
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                rect = pygame.Rect(GRID_OFFSET_X + c * CELL_SIZE, GRID_OFFSET_Y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                # Filled Block Base Layer or Empty Placeholder
                pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=4)
                
                # HIGH CONTRAST OUTLINES: Enhanced visibility using explicit GRID_BORDER_COLOR line drawing
                pygame.draw.rect(self.screen, GRID_BORDER_COLOR, rect, 2, border_radius=4)
                
                if r == 0 and self.selected_mode == "PRACTICE" and self.grid[r][c]:
                    pygame.draw.rect(self.screen, COLOR_RED, rect, 2, border_radius=4)

                if self.grid[r][c]:
                    cell_col = COLOR_BLUE
                    if r == 0 and self.selected_mode == "PRACTICE": cell_col = COLOR_PURPLE
                    
                    inner_node = rect.inflate(-6, -6)
                    pygame.draw.rect(self.screen, cell_col, inner_node, border_radius=6)
                    
                    char = self.main_font.render(self.grid[r][c], True, TEXT_MAIN)
                    self.screen.blit(char, char.get_rect(center=rect.center))

        # Input Live String Buffer Block
        i_rect = pygame.Rect(GRID_OFFSET_X, SCREEN_HEIGHT - 75, (GRID_SIZE * CELL_SIZE), 45)
        pygame.draw.rect(self.screen, CARD_BG, i_rect, border_radius=6)
        pygame.draw.rect(self.screen, (60, 60, 75), i_rect, 1, border_radius=6)
        
        self.screen.blit(self.ui_font.render(f"INPUT BUFFER:  {self.input_text}", True, TEXT_MAIN), (i_rect.x + 15, i_rect.y + 10))
        
        hint = self.small_font.render("Esc: Return to operational archetype deck selection module", True, TEXT_MUTED)
        self.screen.blit(hint, (GRID_OFFSET_X, SCREEN_HEIGHT - 25))

    def draw_finish(self):
        self.screen.fill(BG_COLOR)
        
        title = self.title_font.render("SESSION TERMINATED", True, COLOR_RED)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 25))
        
        self.screen.blit(self.main_font.render(f"FINAL SCORE: {self.score}", True, TEXT_MAIN), (50, 110))
        self.screen.blit(self.small_font.render(f"OPERATOR INITIALS: {self.player_name}", True, COLOR_BLUE), (50, 160))
        
        m_label = f"ARCHETYPE MODULE: {self.selected_mode}"
        m_color = COLOR_RED if self.selected_mode == "ARCADE" else COLOR_GREEN
        self.screen.blit(self.small_font.render(m_label, True, m_color), (50, 190))
        
        # Leaderboard Isolation Logic
        if self.selected_mode == "ARCADE":
            # Show Global Leaderboard Only for ARCADE module runs
            leader_box = pygame.Rect(SCREEN_WIDTH - 280, 95, 250, SCREEN_HEIGHT - 210)
            pygame.draw.rect(self.screen, CARD_BG, leader_box, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_GOLD, leader_box, 1, border_radius=10)
            
            self.screen.blit(self.ui_font.render("🏆 CLOUD LEADERS", True, COLOR_GOLD), (leader_box.x + 35, leader_box.y + 15))

            y_offset = leader_box.y + 55
            for i, entry in enumerate(self.leaderboard_data[:14]):
                is_self = entry["name"] == self.player_name
                color = COLOR_GREEN if is_self else TEXT_MAIN
                
                medal = f"{i+1}. "
                if i == 0: medal = "🥇 "
                elif i == 1: medal = "🥈 "
                elif i == 2: medal = "🥉 "
                
                txt = f"{medal}{entry['name'][:8]}: {entry['score']} ⚔️"
                
                font_use = self.ui_font if is_self else self.small_font
                self.screen.blit(font_use.render(txt, True, color), (leader_box.x + 15, y_offset))
                y_offset += 24
        else:
            # Layout optimization frame when inside local PRACTICE mode
            info_box = pygame.Rect(50, 240, 420, 140)
            pygame.draw.rect(self.screen, CARD_BG, info_box, border_radius=10)
            self.screen.blit(self.ui_font.render("💡 Local Run Report", True, COLOR_GREEN), (info_box.x + 20, info_box.y + 20))
            self.screen.blit(self.rule_font.render("Practice runs focus on matrix endurance exploration.", True, TEXT_MAIN), (info_box.x + 20, info_box.y + 60))
            self.screen.blit(self.rule_font.render("Hence records bypass global cloud leaderboards.", True, TEXT_MUTED), (info_box.x + 20, info_box.y + 90))

        if self.uploading:
            self.screen.blit(self.small_font.render("📡 Uploading stream packet data to cloud...", True, COLOR_GOLD), (40, SCREEN_HEIGHT - 120))
        else:
            i1 = self.ui_font.render("Press [ R ] to restart identical session loop", True, COLOR_BLUE)
            i2 = self.ui_font.render("Press [ M ] to choose another archetype deck", True, TEXT_MAIN)
            i3 = self.small_font.render("Press [ ESC ] to wipe logs and head back to user registration", True, TEXT_MUTED)
            
            self.screen.blit(i1, (40, SCREEN_HEIGHT - 120))
            self.screen.blit(i2, (40, SCREEN_HEIGHT - 85))
            self.screen.blit(i3, (40, SCREEN_HEIGHT - 45))

    def draw(self):
        if self.state == "RULES": self.draw_rules()
        elif self.state == "NAME_ENTRY": self.draw_name_entry()
        elif self.state == "MODE_SELECT": self.draw_mode_select()
        elif self.state == "PLAYING": self.draw_playing()
        elif self.state == "FINISH": self.draw_finish()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            if self.state == "PLAYING" and self.selected_mode == "ARCADE":
                elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
                if elapsed >= ARCADE_START_SECONDS:  
                    self.state = "FINISH"
                    threading.Thread(target=self.upload_score, daemon=True).start()
            
            if self.state == "PLAYING" and self.selected_mode == "PRACTICE" and not self.game_active:
                self.state = "FINISH"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if self.state == "RULES":
                        if event.key == pygame.K_ESCAPE: self.state = "NAME_ENTRY"
                        elif event.key == pygame.K_RIGHT and self.current_rule_page < 2: self.current_rule_page += 1
                        elif event.key == pygame.K_LEFT and self.current_rule_page > 0: self.current_rule_page -= 1
                        elif event.key == pygame.K_RETURN and self.current_rule_page == 2: self.state = "NAME_ENTRY"
                    
                    elif self.state == "NAME_ENTRY":
                        if event.key == pygame.K_RETURN and self.player_name: self.state = "MODE_SELECT"
                        elif event.key == pygame.K_BACKSPACE: self.player_name = self.player_name[:-1]
                        elif event.key == pygame.K_ESCAPE: running = False
                        else:
                            if len(self.player_name) < 10 and event.unicode.isalnum():
                                self.player_name += event.unicode.upper()
                    
                    elif self.state == "MODE_SELECT":
                        if event.key == pygame.K_ESCAPE: self.state = "NAME_ENTRY"
                    
                    elif self.state == "PLAYING":
                        if event.key == pygame.K_RETURN:
                            self.check_and_remove(self.input_text)
                            self.input_text = ""
                        elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "MODE_SELECT"
                            self.selected_mode = None
                        else:
                            if len(self.input_text) < 20 and event.unicode.isalpha():
                                self.input_text += event.unicode.upper()
                    
                    elif self.state == "FINISH":
                        if event.key == pygame.K_r:
                            self.reset_game()
                            self.state = "PLAYING"
                            self.game_active = True
                            self.start_ticks = pygame.time.get_ticks()
                        elif event.key == pygame.K_m:
                            self.reset_game()
                            self.state = "MODE_SELECT"
                            self.selected_mode = None
                        elif event.key == pygame.K_ESCAPE:
                            self.reset_game()
                            self.state = "NAME_ENTRY"
                            self.selected_mode = None

                if event.type == pygame.MOUSEBUTTONDOWN:
                    m_pos = pygame.mouse.get_pos()
                    if self.state == "RULES":
                        if hasattr(self, 'prev_rect') and self.current_rule_page > 0 and self.prev_rect.collidepoint(m_pos):
                            self.current_rule_page -= 1
                        if hasattr(self, 'next_rect') and self.current_rule_page < 2 and self.next_rect.collidepoint(m_pos):
                            self.current_rule_page += 1
                        elif self.current_rule_page == 2 and hasattr(self, 'start_rect') and self.start_rect.collidepoint(m_pos):
                            self.state = "NAME_ENTRY"
                    
                    elif self.state == "MODE_SELECT":
                        if hasattr(self, 'arcade_rect') and self.arcade_rect.collidepoint(m_pos):
                            self.selected_mode = "ARCADE"
                            self.reset_game()
                            self.state = "PLAYING"
                            self.game_active = True
                            self.start_ticks = pygame.time.get_ticks()
                        elif hasattr(self, 'practice_rect') and self.practice_rect.collidepoint(m_pos):
                            self.selected_mode = "PRACTICE"
                            self.reset_game()
                            self.state = "PLAYING"
                            self.game_active = True
                    
                    elif self.state == "PLAYING":
                        mx, my = m_pos
                        if (GRID_OFFSET_X <= mx <= GRID_OFFSET_X + GRID_SIZE * CELL_SIZE
                            and GRID_OFFSET_Y <= my <= GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE):
                            col = (mx - GRID_OFFSET_X) // CELL_SIZE
                            if not self.drop_letter(col):
                                self.game_active = False
                                self.state = "FINISH"
                                threading.Thread(target=self.upload_score, daemon=True).start()

            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    CloudWordBattle().run()
