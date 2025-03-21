import pygame
from utils.constants import *

class Bar:
    def __init__(self):
        self.bar_width = 200
        self.bar_height = 20
        self.border_width = 2

    def draw_health_bar(self, screen, character, pos):
        """Draw a health bar for a character"""
        x, y = pos
        
        # Draw border
        pygame.draw.rect(screen, WHITE, (x, y, self.bar_width, self.bar_height), self.border_width)
        
        # Calculate health percentage
        health_percent = character.health / character.max_health
        
        # Draw health bar
        health_width = int(self.bar_width * health_percent)
        health_color = GREEN if health_percent > 0.5 else YELLOW if health_percent > 0.2 else RED
        pygame.draw.rect(screen, health_color, (x + self.border_width, y + self.border_width, 
                                              health_width - self.border_width * 2, 
                                              self.bar_height - self.border_width * 2))
        
        # Draw health text
        health_text = f"{character.health}/{character.max_health}"
        text = pygame.font.Font(None, 20).render(health_text, True, WHITE)
        text_rect = text.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        screen.blit(text, text_rect)

    def draw_mp_bar(self, screen, character, pos):
        """Draw an MP bar for a character"""
        x, y = pos
        
        # Draw border
        pygame.draw.rect(screen, WHITE, (x, y, self.bar_width, self.bar_height), self.border_width)
        
        # Calculate MP percentage
        mp_percent = character.mp / character.max_mp if character.max_mp > 0 else 0
        
        # Draw MP bar
        mp_width = int(self.bar_width * mp_percent)
        mp_color = BLUE
        pygame.draw.rect(screen, mp_color, (x + self.border_width, y + self.border_width, 
                                          mp_width - self.border_width * 2, 
                                          self.bar_height - self.border_width * 2))
        
        # Draw MP text
        mp_text = f"{character.mp}/{character.max_mp}"
        text = pygame.font.Font(None, 20).render(mp_text, True, WHITE)
        text_rect = text.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        screen.blit(text, text_rect) 