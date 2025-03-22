import pygame
from utils.constants import WHITE, BLACK, RED, GREEN, BLUE, YELLOW, PURPLE

class Bar:
    """A UI component for drawing various types of bars (health, mana, xp, etc.)"""
    
    def __init__(self):
        self.bar_width = 200
        self.bar_height = 20
        self.border_width = 2
        self.border_color = WHITE
        self.health_color = GREEN
        self.xp_color = BLUE
        self.mp_color = BLUE
        self.text_color = WHITE
        self.font = pygame.font.Font(None, 24)
    
    def draw_health_bar(self, screen, character, x, y):
        """Draw a health bar for a character"""
        # Draw border
        pygame.draw.rect(screen, self.border_color, (x, y, self.bar_width, self.bar_height), self.border_width)
        
        # Calculate health percentage
        health_percent = character.health / character.max_health
        
        # Draw health bar with color based on health percentage
        health_width = int(self.bar_width * health_percent)
        health_color = GREEN if health_percent > 0.5 else YELLOW if health_percent > 0.2 else RED
        pygame.draw.rect(screen, health_color, 
                        (x + self.border_width, y + self.border_width, 
                         health_width - self.border_width * 2, 
                         self.bar_height - self.border_width * 2))
        
        # Draw health text with character name
        health_text = f"{character.name} - HP: {character.health}/{character.max_health}"
        text = self.font.render(health_text, True, self.text_color)
        text_rect = text.get_rect(center=(x + self.bar_width/2, y + self.bar_height/2))
        screen.blit(text, text_rect)
    
    def draw_xp_bar(self, surface, character, x, y):
        """Draw an XP bar with level label"""
        # Bar dimensions
        width = 200
        height = 20
        
        # Calculate XP percentage
        xp_percent = character.exp / character.exp_to_next_level
        fill_width = int(width * xp_percent)
        
        # Draw background
        xp_color = PURPLE
        pygame.draw.rect(surface, xp_color, (x, y, width, height))
        
        # Draw filled portion
        if fill_width > 0:
            pygame.draw.rect(surface, (0, 0, 255), (x, y, fill_width, height))
        
        # Draw border
        pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 1)
        
        # Draw level label inside bar
        font = pygame.font.Font(None, 24)
        level_text = f"Level: {character.level}"
        text_surface = font.render(level_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.midleft = (x + 5, y + height // 2)  # Position text 5 pixels from left edge
        surface.blit(text_surface, text_rect)
        
        # Draw XP text
        xp_text = f"{character.exp}/{character.exp_to_next_level} XP"
        text_surface = font.render(xp_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.midright = (x + width - 5, y + height // 2)  # Position text 5 pixels from right edge
        surface.blit(text_surface, text_rect)
    
    def draw_mp_bar(self, screen, character, x, y):
        """Draw a mana points bar for a character"""
        # Draw border
        pygame.draw.rect(screen, self.border_color, (x, y, self.bar_width, self.bar_height), self.border_width)
        
        # Calculate MP percentage
        mp_percent = character.mp / character.max_mp if character.max_mp > 0 else 0
        
        # Draw MP bar
        mp_width = int(self.bar_width * mp_percent)
        pygame.draw.rect(screen, self.mp_color, 
                        (x + self.border_width, y + self.border_width, 
                         mp_width - self.border_width * 2, 
                         self.bar_height - self.border_width * 2))
        
        # Draw MP text
        mp_text = f"MP: {character.mp}/{character.max_mp}"
        text = self.font.render(mp_text, True, self.text_color)
        text_rect = text.get_rect(center=(x + self.bar_width/2, y + self.bar_height/2))
        screen.blit(text, text_rect) 