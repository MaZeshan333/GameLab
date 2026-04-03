import pygame
import random
import nltk
import requests
import json
import threading
from nltk.corpus import words

# --- Firebase Configuration ---
# Your specific URL with the .json suffix added
FIREBASE_URL = "https://gamelab-6855e-default-rtdb.firebaseio.com/leaderboard.json"

# Initializing Dictionary
try:
    word_set = set(w.upper() for w in words.words())
except:
    print("Downloading dictionary data...")
    nltk.download('words')
    word_set = set(w.upper() for w in words.words())

# --- Configuration ---
FPS = 60
GRID_SIZE = 7
CELL_SIZE = 70
GRID_OFFSET_X = 40
GRID_OFFSET_Y = 100
GAME_DURATION = 60 

SCREEN_WIDTH = (CELL_SIZE * GRID_SIZE) + 240 
SCREEN_HEIGHT = (CELL_SIZE * GRID_SIZE) + 240

# Colors
WHITE, BLACK, GRAY = (245, 245, 245), (30, 30, 30), (180, 180, 180)
BLUE, RED, GREEN, GOLD = (65, 105, 225), (220, 20, 60), (34, 139, 34), (218, 165, 32)

class CloudWordBattle:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("7x7 Word Battle - Cloud Leaderboard")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.main_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.ui_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 16, bold=True)
        
        # Game State
        self.state = 'START' # START, PLAYING, FINISH
        self.player_name = "PLAYER1"
        self.leaderboard_data = []
        self.reset_game()
        
        # Fetch leaderboard immediately
        threading.Thread(target=self.fetch_leaderboard, daemon=True).start()

    def reset_game(self):
        self.grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_letter = self.get_random_letter()
        self.score = 0
        self.input_text = ""
        self.status_msg = "Enter a name to start!"
        self.start_ticks = 0
        self.time_left = GAME_DURATION
        self.uploading = False

    def get_random_letter(self):
        # High vowel frequency for better gameplay
        return random.choice("AEIOU" * 6 + "BCDFGHJKLMNPQRSTVWXYZ")

    # --- Cloud Functions ---
    def fetch_leaderboard(self):
        try:
            response = requests.get(FIREBASE_URL)
            if response.status_code == 200 and response.json():
                data = response.json()
                raw_list = list(data.values()) if isinstance(data, dict) else data
                self.leaderboard_data = sorted(raw_list, key=lambda x: x['score'], reverse=True)[:20]
        except Exception as e:
            print(f"Fetch Error: {e}")

    def upload_score(self):
        if self.score <= 0: return
        self.uploading = True
        payload = {"name": self.player_name, "score": self.score}
        try:
            requests.post(FIREBASE_URL, json=payload)
            self.fetch_leaderboard() 
        except Exception as e:
            print(f"Upload Error: {e}")
        self.uploading = False

    # --- Game Logic ---
    def drop_letter(self, col):
        for r in range(GRID_SIZE - 1, -1, -1):
            if self.grid[r][col] == '':
                self.grid[r][col] = self.next_letter
                self.next_letter = self.get_random_letter()
                return True
        return False

    def check_and_remove(self, word):
        word = word.upper().strip()
        if not (word in word_set and len(word) >= 2):
            self.status_msg = f"'{word}' is not a word!"
            return False
        
        found = False
        cells_to_clear = set()

        # Horizontal
        for r in range(GRID_SIZE):
            row_str = "".join([self.grid[r][c] if self.grid[r][c] != '' else ' ' for c in range(GRID_SIZE)])
            if word in row_str:
                idx = row_str.find(word)
                for c in range(idx, idx + len(word)): cells_to_clear.add((r, c))
                found = True

        # Vertical
        for c in range(GRID_SIZE):
            col_str = "".join([self.grid[r][c] if self.grid[r][c] != '' else ' ' for r in range(GRID_SIZE)])
            if word in col_str:
                idx = col_str.find(word)
                for r in range(idx, idx + len(word)): cells_to_clear.add((r, c))
                found = True

        # Diagonals (\ and /)
        for start_nodes in [[(0, c) for c in range(GRID_SIZE)] + [(r, 0) for r in range(1, GRID_SIZE)], 
                            [(0, c) for c in range(GRID_SIZE)] + [(r, GRID_SIZE-1) for r in range(1, GRID_SIZE)]]:
            is_back = (start_nodes[-1][1] != 0)
            for r, c in start_nodes:
                diag_str, coords = "", []
                curr_r, curr_c = r, c
                while 0 <= curr_r < GRID_SIZE and 0 <= curr_c < GRID_SIZE:
                    diag_str += self.grid[curr_r][curr_c] if self.grid[curr_r][curr_c] != '' else ' '
                    coords.append((curr_r, curr_c))
                    curr_r, curr_c = (curr_r+1, curr_c-1) if is_back else (curr_r+1, curr_c+1)
                if word in diag_str:
                    idx = diag_str.find(word)
                    for i in range(idx, idx + len(word)): cells_to_clear.add(coords[i])
                    found = True

        if found:
            for r, c in cells_to_clear: self.grid[r][c] = ''
            # Gravity
            for c in range(GRID_SIZE):
                letters = [self.grid[r][c] for r in range(GRID_SIZE) if self.grid[r][c] != '']
                new_col = [''] * (GRID_SIZE - len(letters)) + letters
                for r in range(GRID_SIZE): self.grid[r][c] = new_col[r]
            
            bonus = len(word) * 30
            self.score += bonus
            self.status_msg = f"Nice! '{word}' +{bonus}"
        return found

    def draw(self):
        self.screen.fill(WHITE)
        
        if self.state == 'START':
            self.screen.blit(self.main_font.render("WORD STACK CLOUD", True, BLUE), (SCREEN_WIDTH//2 - 145, 150))
            self.screen.blit(self.ui_font.render(f"NAME: {self.player_name}", True, BLACK), (SCREEN_WIDTH//2 - 80, 220))
            self.screen.blit(self.small_font.render("Type name then press SPACE", True, GRAY), (SCREEN_WIDTH//2 - 105, 280))

        elif self.state == 'PLAYING':
            t_color = RED if self.time_left < 10 else BLACK
            self.screen.blit(self.ui_font.render(f"TIME: {self.time_left}s", True, t_color), (40, 20))
            self.screen.blit(self.ui_font.render(f"SCORE: {self.score}", True, GREEN), (280, 20))
            self.screen.blit(self.small_font.render(self.status_msg, True, GRAY), (40, 60))

            # Preview
            p_x = GRID_OFFSET_X + (GRID_SIZE * CELL_SIZE) + 30
            pygame.draw.rect(self.screen, BLACK, (p_x, GRID_OFFSET_Y, 80, 90), 2)
            self.screen.blit(self.ui_font.render("NEXT", True, BLACK), (p_x+12, GRID_OFFSET_Y-25))
            self.screen.blit(self.main_font.render(self.next_letter, True, BLUE), (p_x+25, GRID_OFFSET_Y+25))

            # Grid
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    rect = pygame.Rect(GRID_OFFSET_X + c*CELL_SIZE, GRID_OFFSET_Y + r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, GRAY, rect, 1)
                    if self.grid[r][c]:
                        pygame.draw.rect(self.screen, BLUE, rect.inflate(-6, -6), border_radius=10)
                        char = self.main_font.render(self.grid[r][c], True, WHITE)
                        self.screen.blit(char, char.get_rect(center=rect.center))

            # Input
            i_rect = pygame.Rect(GRID_OFFSET_X, SCREEN_HEIGHT - 60, (GRID_SIZE * CELL_SIZE), 40)
            pygame.draw.rect(self.screen, BLACK, i_rect, 2)
            self.screen.blit(self.ui_font.render(f"INPUT: {self.input_text}", True, BLACK), (GRID_OFFSET_X+10, SCREEN_HEIGHT-55))

        elif self.state == 'FINISH':
            self.screen.blit(self.main_font.render("TIME UP!", True, RED), (SCREEN_WIDTH//2 - 65, 30))
            self.screen.blit(self.ui_font.render(f"YOUR SCORE: {self.score}", True, BLACK), (SCREEN_WIDTH//2 - 75, 75))
            
            # Leaderboard
            self.screen.blit(self.ui_font.render("-- TOP 20 GLOBAL --", True, GOLD), (SCREEN_WIDTH//2 - 95, 120))
            for i, entry in enumerate(self.leaderboard_data):
                color = GREEN if entry['name'] == self.player_name else BLACK
                txt = f"{i+1}. {entry['name'][:10]}: {entry['score']}"
                self.screen.blit(self.small_font.render(txt, True, color), (SCREEN_WIDTH//2 - 80, 150 + i*20))
            
            if self.uploading:
                self.screen.blit(self.small_font.render("Syncing...", True, GRAY), (20, SCREEN_HEIGHT-30))
            else:
                self.screen.blit(self.small_font.render("Press 'R' to Restart", True, BLUE), (20, SCREEN_HEIGHT-30))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            if self.state == 'PLAYING':
                elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
                self.time_left = max(0, GAME_DURATION - elapsed)
                if self.time_left <= 0:
                    self.state = 'FINISH'
                    threading.Thread(target=self.upload_score, daemon=True).start()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                
                if event.type == pygame.KEYDOWN:
                    if self.state == 'START':
                        if event.key == pygame.K_SPACE and self.player_name:
                            self.state = 'PLAYING'
                            self.start_ticks = pygame.time.get_ticks()
                        elif event.key == pygame.K_BACKSPACE: self.player_name = self.player_name[:-1]
                        else: 
                            if len(self.player_name) < 10 and event.unicode.isalnum():
                                self.player_name += event.unicode.upper()
                    
                    elif self.state == 'FINISH' and event.key == pygame.K_r:
                        self.reset_game()
                        self.state = 'START'
                        threading.Thread(target=self.fetch_leaderboard, daemon=True).start()

                    elif self.state == 'PLAYING':
                        if event.key == pygame.K_RETURN:
                            self.check_and_remove(self.input_text)
                            self.input_text = ""
                        elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                        else: self.input_text += event.unicode.upper()

                if event.type == pygame.MOUSEBUTTONDOWN and self.state == 'PLAYING':
                    mx, _ = pygame.mouse.get_pos()
                    if GRID_OFFSET_X <= mx <= GRID_OFFSET_X + GRID_SIZE * CELL_SIZE:
                        col = (mx - GRID_OFFSET_X) // CELL_SIZE
                        if not self.drop_letter(col):
                            self.state = 'FINISH'
                            threading.Thread(target=self.upload_score, daemon=True).start()

            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    CloudWordBattle().run()