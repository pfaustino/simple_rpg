import pygame
from utils.constants import WHITE, BLACK

class Bar:
    """A UI component for drawing various types of bars (health, mana, xp, etc.)"""
    
    @staticmethod
    def draw_health_bar(screen, character, x, y, width=200, height=20):
        """Draw a health bar for a character
        
        Args:
            screen: The pygame surface to draw on
            character: The character whose health to display
            x: X coordinate for the bar
            y: Y coordinate for the bar
            width: Width of the bar (default: 200)
            height: Height of the bar (default: 20)
        """
        fill = (character.health / character.max_health) * width
        
        # Draw the background (red)
        pygame.draw.rect(screen, (255, 0, 0), (x, y, width, height))
        # Draw the fill (green)
        pygame.draw.rect(screen, (0, 255, 0), (x, y, fill, height))
        # Draw the border
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
        
        # Draw the text
        font = pygame.font.Font(None, 24)
        health_text = f"{character.name}: {character.health}/{character.max_health} HP"
        text_surface = font.render(health_text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.x = x
        text_rect.y = y - 20
        screen.blit(text_surface, text_rect)
    
    @staticmethod
    def draw_xp_bar(screen, character, x, y, width=200, height=20):
        """Draw an experience bar for a character
        
        Args:
            screen: The pygame surface to draw on
            character: The character whose XP to display
            x: X coordinate for the bar
            y: Y coordinate for the bar
            width: Width of the bar (default: 200)
            height: Height of the bar (default: 20)
        """
        xp_fill = (character.exp / (character.level * 100)) * width
        
        # Draw the background (gray)
        pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height))
        # Draw the fill (blue)
        pygame.draw.rect(screen, (0, 0, 255), (x, y, xp_fill, height))
        # Draw the border
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
        
        # Draw the text
        font = pygame.font.Font(None, 24)
        xp_text = f"Level {character.level} - XP: {character.exp}/{character.level * 100}"
        text_surface = font.render(xp_text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.x = x
        text_rect.y = y + height + 5
        screen.blit(text_surface, text_rect)
    
    @staticmethod
    def draw_mana_bar(screen, character, x, y, width=200, height=20):
        """Draw a mana bar for a character (placeholder for future use)
        
        Args:
            screen: The pygame surface to draw on
            character: The character whose mana to display
            x: X coordinate for the bar
            y: Y coordinate for the bar
            width: Width of the bar (default: 200)
            height: Height of the bar (default: 20)
        """
        if not hasattr(character, 'mana') or not hasattr(character, 'max_mana'):
            return
            
        fill = (character.mana / character.max_mana) * width
        
        # Draw the background (dark blue)
        pygame.draw.rect(screen, (0, 0, 100), (x, y, width, height))
        # Draw the fill (light blue)
        pygame.draw.rect(screen, (0, 128, 255), (x, y, fill, height))
        # Draw the border
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
        
        # Draw the text
        font = pygame.font.Font(None, 24)
        mana_text = f"MP: {character.mana}/{character.max_mana}"
        text_surface = font.render(mana_text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.x = x
        text_rect.y = y - 20
        screen.blit(text_surface, text_rect) 