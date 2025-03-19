import pygame
from utils.constants import FONT_SIZE, BLACK, WHITE

class MessageConsole:
    def __init__(self, max_messages=6):
        self.messages = []
        self.max_messages = max_messages
        self.is_collapsed = False
        self.button_size = 20
        self.font = pygame.font.Font(None, int(FONT_SIZE * 0.75))  # 75% of original font size
        self.line_spacing = 18  # Reduced from 25 to 18 for tighter spacing
    
    def add_message(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def wrap_text(self, text, max_width):
        """Wrap text to fit within the given width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = self.font.render(word + ' ', True, WHITE)
            word_width = word_surface.get_width()
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:  # If we have words in the current line
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:  # Add the last line if it exists
            lines.append(' '.join(current_line))
        
        return lines
    
    def toggle_collapse(self, mouse_pos, console_rect):
        """Check if the collapse button was clicked and toggle if it was"""
        if self.is_collapsed:
            # When collapsed, only check the button area
            button_rect = pygame.Rect(
                console_rect.right - self.button_size - 5,
                console_rect.top + 5,
                self.button_size,
                self.button_size
            )
        else:
            # When expanded, check the entire console area
            button_rect = pygame.Rect(
                console_rect.right - self.button_size - 5,
                console_rect.top + 5,
                self.button_size,
                self.button_size
            )
        
        if button_rect.collidepoint(mouse_pos):
            self.is_collapsed = not self.is_collapsed
            return True
        return False
    
    def draw(self, screen, x, y, width, height):
        if self.is_collapsed:
            # When collapsed, only draw the button
            button_rect = pygame.Rect(
                x + width - self.button_size - 5,
                y + 5,
                self.button_size,
                self.button_size
            )
            pygame.draw.rect(screen, (0, 0, 0), button_rect)
            pygame.draw.rect(screen, WHITE, button_rect, 1)
            
            # Draw button text
            button_text = "+"
            text_surface = self.font.render(button_text, True, WHITE)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)
        else:
            # Create console background
            console_rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(screen, (0, 0, 0), console_rect)
            pygame.draw.rect(screen, WHITE, console_rect, 1)
            
            # Draw collapse button
            button_rect = pygame.Rect(
                console_rect.right - self.button_size - 5,
                console_rect.top + 5,
                self.button_size,
                self.button_size
            )
            pygame.draw.rect(screen, WHITE, button_rect)
            pygame.draw.rect(screen, BLACK, button_rect, 1)
            
            # Draw button text
            button_text = "−"
            text_surface = self.font.render(button_text, True, BLACK)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)
            
            # Draw messages with word wrapping
            padding = 10
            available_width = width - (padding * 2) - self.button_size - 10  # Account for button
            y_offset = padding
            
            for message in reversed(self.messages):
                # Wrap the message text
                wrapped_lines = self.wrap_text(message, available_width)
                
                # Draw each line of the wrapped text
                for line in reversed(wrapped_lines):
                    if y_offset + self.line_spacing > height - padding:  # Stop if we've reached the bottom
                        break
                    text_surface = self.font.render(line, True, WHITE)
                    screen.blit(text_surface, (x + padding, y + y_offset))
                    y_offset += self.line_spacing
                
                # Add a small gap between messages
                y_offset += 2 