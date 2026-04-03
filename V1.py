import pygame
import random
import nltk
from nltk.corpus import words

# Initializing the dictionary
try:
    # This might take a second on the first run
    word_set = set(w.upper() for w in words.words())
except:
    print("Downloading dictionary data...")
    nltk.download('words')
    word_set = set(w.upper() for w in words.words())

# --- Configuration ---
FPS = 60
GRID_SIZE = 7        # Changed from 5 to 7
CELL_SIZE = 70       # Slightly smaller to fit the screen
GRID_OFFSET_X = 40
GRID_OFFSET_Y = 100

# Dynamic Screen Size based on Grid
SCREEN_WIDTH = (CELL_SIZE * GRID_SIZE) + 200 
SCREEN_HEIGHT = (CELL_SIZE * GRID_SIZE) + 200

# Colors
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GRAY = (180, 180, 180)
BLUE = (65, 105, 225)
GOLD = (255, 215, 0)
RED = (220, 20, 60)
GREEN = (34, 139, 34)

class WordTetris7x7:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("7x7 Word Stack - Dictionary Validated")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.main_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.ui_font = pygame.font.SysFont("Arial", 20, bold=True)
        
        # Game State
        self.grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_letter = self.get_random_letter()
        self.score = 0
        self.game_over = False
        self.input_text = ""
        self.status_msg = "Click a column to drop. Type a word to clear."

    def get_random_letter(self):
        # Increased weight for vowels to help with larger grids
        return random.choice("AEIOU" * 4 + "BCDFGHJKLMNPQRSTVWXYZ")

    def is_valid_english_word(self, word):
        return word.upper() in word_set and len(word) >= 2

    def drop_letter(self, col):
        # Drop logic from bottom to top
        for r in range(GRID_SIZE - 1, -1, -1):
            if self.grid[r][col] == '':
                self.grid[r][col] = self.next_letter
                self.next_letter = self.get_random_letter()
                return True
        return False

    def check_and_remove(self, word):
        word = word.upper().strip()
        
        if not self.is_valid_english_word(word):
            self.status_msg = f"'{word}' is not a valid word!"
            return False
        
        found = False
        # Horizontal Check
        for r in range(GRID_SIZE):
            row_str = "".join([c if c != '' else ' ' for c in self.grid[r]])
            if word in row_str:
                start_idx = row_str.find(word)
                for c in range(start_idx, start_idx + len(word)):
                    self.grid[r][c] = ''
                found = True

        # Vertical Check
        for c in range(GRID_SIZE):
            col_str = "".join([self.grid[r][c] if self.grid[r][c] != '' else ' ' for r in range(GRID_SIZE)])
            if word in col_str:
                start_idx = col_str.find(word)
                for r in range(start_idx, start_idx + len(word)):
                    self.grid[r][c] = ''
                found = True

        if found:
            self.apply_gravity()
            self.score += len(word) * 20 # Bonus for 7x7 difficulty
            self.status_msg = f"Awesome! '{word}' cleared. +{len(word)*20}"
        else:
            self.status_msg = f"'{word}' is valid, but not found on board."
        
        return found

    def apply_gravity(self):
        for c in range(GRID_SIZE):
            # Extract non-empty letters
            letters = [self.grid[r][c] for r in range(GRID_SIZE) if self.grid[r][c] != '']
            # Rebuild column with empty spaces at top
            new_col = [''] * (GRID_SIZE - len(letters)) + letters
            for r in range(GRID_SIZE):
                self.grid[r][c] = new_col[r]

    def draw(self):
        self.screen.fill(WHITE)
        
        # Display Score and Status
        score_surf = self.ui_font.render(f"SCORE: {self.score}", True, BLACK)
        self.screen.blit(score_surf, (GRID_OFFSET_X, 20))
        
        msg_color = GREEN if "Awesome" in self.status_msg else RED
        msg_surf = self.ui_font.render(self.status_msg, True, msg_color if self.status_msg[0] != 'C' else BLACK)
        self.screen.blit(msg_surf, (GRID_OFFSET_X, 50))

        # Next Letter Preview Box
        preview_x = GRID_OFFSET_X + (GRID_SIZE * CELL_SIZE) + 40
        pygame.draw.rect(self.screen, BLACK, (preview_x, GRID_OFFSET_Y, 80, 100), 2)
        next_lbl = self.ui_font.render("NEXT", True, BLACK)
        self.screen.blit(next_lbl, (preview_x + 15, GRID_OFFSET_Y - 25))
        letter_surf = self.main_font.render(self.next_letter, True, BLUE)
        self.screen.blit(letter_surf, (preview_x + 25, GRID_OFFSET_Y + 25))

        # Draw Grid and Letters
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                rect = pygame.Rect(GRID_OFFSET_X + c * CELL_SIZE, GRID_OFFSET_Y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, GRAY, rect, 1)
                
                if self.grid[r][c] != '':
                    # Letter tile styling
                    pygame.draw.rect(self.screen, BLUE, rect.inflate(-6, -6), border_radius=8)
                    char_surf = self.main_font.render(self.grid[r][c], True, WHITE)
                    # Center the letter
                    text_rect = char_surf.get_rect(center=rect.center)
                    self.screen.blit(char_surf, text_rect)

        # Input Area at Bottom
        input_rect = pygame.Rect(GRID_OFFSET_X, SCREEN_HEIGHT - 70, (GRID_SIZE * CELL_SIZE), 40)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)
        input_display = self.ui_font.render(f"TYPE WORD: {self.input_text}", True, BLACK)
        self.screen.blit(input_display, (GRID_OFFSET_X + 10, SCREEN_HEIGHT - 62))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 220))
            self.screen.blit(overlay, (0,0))
            go_surf = self.main_font.render("GAME OVER", True, RED)
            self.screen.blit(go_surf, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if not self.game_over:
                    # Drop letter on mouse click
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        if GRID_OFFSET_X <= mx <= GRID_OFFSET_X + GRID_SIZE * CELL_SIZE:
                            col = (mx - GRID_OFFSET_X) // CELL_SIZE
                            if not self.drop_letter(col):
                                self.game_over = True
                    
                    # Keyboard input for clearing words
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.check_and_remove(self.input_text)
                            self.input_text = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        else:
                            if event.unicode.isalpha():
                                self.input_text += event.unicode.upper()

            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = WordTetris7x7()
    game.run()