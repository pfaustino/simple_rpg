import pygame
from utils.constants import WHITE, BLACK, FONT_SIZE

class SystemMenu:
    def __init__(self, screen_width, screen_height):
        self.font = pygame.font.Font(None, int(FONT_SIZE * 1.5))
        self.title_font = pygame.font.Font(None, int(FONT_SIZE * 3))  # Larger font for RPG title
        self.options = ["Continue", "New Game", "Tools", "Quit Game"]
        self.selected_option = 0
        self.is_visible = False
        self.background_color = (0, 0, 0, 180)  # Semi-transparent black
        self.text_color = WHITE
        self.selected_color = (255, 255, 0)  # Yellow for selected option
        
        # Set initial dimensions
        self.menu_width = 300
        self.menu_height = len(self.options) * 50 + 80  # Padding for menu items and System Menu text
        
        # Update positions for initial screen size
        self.resize(screen_width, screen_height)
    
    def resize(self, screen_width, screen_height):
        """Update menu positions when screen size changes"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Recalculate menu position
        self.menu_x = (screen_width - self.menu_width) // 2
        self.menu_y = (screen_height - self.menu_height) // 2 + 50  # Move menu down to accommodate RPG title
        
        # Create menu background surface
        self.background = pygame.Surface((screen_width, screen_height))
        self.background.fill(self.background_color)
        
        # Create menu surface
        self.menu_surface = pygame.Surface((self.menu_width, self.menu_height))
        self.menu_surface.fill(BLACK)
        
        # Recalculate option positions
        self.option_rects = []
        for i in range(len(self.options)):
            rect = pygame.Rect(
                self.menu_x + 20,
                self.menu_y + 80 + i * 50,  # Adjusted spacing from top
                self.menu_width - 40,
                40
            )
            self.option_rects.append(rect)
    
    def show(self):
        """Show the system menu"""
        self.is_visible = True
        self.selected_option = 0
    
    def hide(self):
        """Hide the system menu"""
        self.is_visible = False
    
    def handle_event(self, event):
        """Handle input events for the menu"""
        if not self.is_visible:
            return None
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selected_option]
            elif event.key == pygame.K_ESCAPE:
                self.hide()
                return "Continue"
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_option = i
                        return self.options[i]
        
        return None
    
    def draw(self, screen):
        """Draw the system menu"""
        if not self.is_visible:
            return
            
        # Draw semi-transparent background
        screen.blit(self.background, (0, 0))
        
        # Draw RPG title above menu box
        rpg_title = self.title_font.render("RPG", True, WHITE)
        rpg_rect = rpg_title.get_rect(centerx=self.menu_x + self.menu_width // 2, bottom=self.menu_y - 20)
        screen.blit(rpg_title, rpg_rect)
        
        # Draw menu background
        pygame.draw.rect(screen, BLACK, (self.menu_x, self.menu_y, self.menu_width, self.menu_height))
        pygame.draw.rect(screen, WHITE, (self.menu_x, self.menu_y, self.menu_width, self.menu_height), 2)
        
        # Draw menu title
        title = self.font.render("System Menu", True, WHITE)
        title_rect = title.get_rect(centerx=self.menu_x + self.menu_width // 2, y=self.menu_y + 25)
        screen.blit(title, title_rect)
        
        # Draw options
        for i, option in enumerate(self.options):
            color = self.selected_color if i == self.selected_option else self.text_color
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(centerx=self.menu_x + self.menu_width // 2, y=self.menu_y + 80 + i * 50)
            screen.blit(text, text_rect)
            
            # Draw selection arrow
            if i == self.selected_option:
                arrow = self.font.render(">", True, self.selected_color)
                arrow_rect = arrow.get_rect(right=text_rect.left - 10, centery=text_rect.centery)
                screen.blit(arrow, arrow_rect) 