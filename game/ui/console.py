import pygame
from utils.constants import WHITE

class MessageConsole:
    def __init__(self, max_messages=6):
        self.messages = []
        self.max_messages = max_messages
        self.font = pygame.font.Font(None, 24)
        
    def add_message(self, message):
        """Add a message to the console"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
            
    def draw(self, surface, x, y, width, height):
        """Draw the message console on the given surface"""
        # Draw background
        pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height))
        pygame.draw.rect(surface, WHITE, (x, y, width, height), 1)
        
        # Draw messages
        message_height = height // self.max_messages
        for i, message in enumerate(self.messages[-self.max_messages:]):
            text_surface = self.font.render(message, True, WHITE)
            text_rect = text_surface.get_rect()
            text_rect.x = x + 5
            text_rect.y = y + (i * message_height) + 5
            surface.blit(text_surface, text_rect) 