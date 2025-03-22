import pygame
from utils.constants import FONT_SIZE, BLACK, WHITE, MAX_CONSOLE_MESSAGES, SCREEN_WIDTH, SCREEN_HEIGHT

class MessageConsole:
    def __init__(self):
        self.messages = []
        self.is_collapsed = False
        self.button_size = 20
        self.font = pygame.font.Font(None, int(FONT_SIZE * 0.75))  # 75% of original font size
        self.line_spacing = 18  # Reduced from 25 to 18 for tighter spacing
        self.scroll_offset = 0  # Current scroll position
        self.scroll_bar_width = 10
        self.is_scrolling = False
        self.scroll_start_y = 0
        self.visible_lines = 0  # Will be calculated in draw method
        
    def add_message(self, message):
        """Add a new message to the console"""
        self.messages.append(message)
        if len(self.messages) > MAX_CONSOLE_MESSAGES:
            self.messages.pop(0)
        # Auto-scroll to bottom when new message arrives
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the message history"""
        if self.visible_lines > 0:
            self.scroll_offset = max(0, len(self.messages) - self.visible_lines)
        else:
            self.scroll_offset = 0
    
    def handle_scroll(self, event, console_rect):
        """Handle scrolling events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Mouse wheel up
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return True
            elif event.button == 5:  # Mouse wheel down
                self.scroll_offset = min(len(self.messages) - self.visible_lines, self.scroll_offset + 1)
                return True
            elif event.button == 1:  # Left click
                # Check if click is on scroll bar
                scroll_bar_rect = self.get_scroll_bar_rect(console_rect)
                if scroll_bar_rect.collidepoint(event.pos):
                    self.is_scrolling = True
                    self.scroll_start_y = event.pos[1]
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                self.is_scrolling = False
        elif event.type == pygame.MOUSEMOTION and self.is_scrolling:
            # Update scroll position based on mouse movement
            delta_y = event.pos[1] - self.scroll_start_y
            scroll_range = self.get_scroll_range(console_rect.height)
            if scroll_range > 0:
                move_ratio = delta_y / scroll_range
                self.scroll_offset = int(max(0, min(len(self.messages) - self.visible_lines,
                                               self.scroll_offset + move_ratio * len(self.messages))))
                self.scroll_start_y = event.pos[1]
                return True
        return False
    
    def get_scroll_bar_rect(self, console_rect):
        """Get the rectangle for the scroll bar"""
        scroll_range = self.get_scroll_range(console_rect.height)
        if scroll_range <= 0 or len(self.messages) == 0:
            return pygame.Rect(0, 0, 0, 0)
        
        bar_height = max(20, console_rect.height * (self.visible_lines / max(1, len(self.messages))))
        bar_y = console_rect.y + (self.scroll_offset / max(1, len(self.messages))) * scroll_range
        return pygame.Rect(
            console_rect.right - self.scroll_bar_width - 2,
            bar_y,
            self.scroll_bar_width,
            bar_height
        )
    
    def get_scroll_range(self, console_height):
        """Get the available scrolling range"""
        return max(0, console_height - 20)  # 20 is minimum scroll bar height
    
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
            
            # Calculate visible area
            padding = 10
            available_width = width - (padding * 2) - self.button_size - self.scroll_bar_width - 10
            self.visible_lines = (height - 2 * padding) // self.line_spacing
            
            # Create a clipping rect for the messages
            clip_rect = pygame.Rect(x + padding, y + padding,
                                  available_width, height - 2 * padding)
            old_clip = screen.get_clip()
            screen.set_clip(clip_rect)
            
            # Draw visible messages
            y_offset = padding
            visible_messages = self.messages[self.scroll_offset:self.scroll_offset + self.visible_lines]
            
            for message in visible_messages:
                # Wrap the message text
                wrapped_lines = self.wrap_text(message, available_width)
                
                # Draw each line of the wrapped text
                for line in wrapped_lines:
                    if y_offset + self.line_spacing <= height - padding:
                        text_surface = self.font.render(line, True, WHITE)
                        screen.blit(text_surface, (x + padding, y + y_offset))
                        y_offset += self.line_spacing
                
                # Add a small gap between messages
                y_offset += 2
            
            # Restore the original clipping rect
            screen.set_clip(old_clip)
            
            # Draw scroll bar if needed
            if len(self.messages) > self.visible_lines:
                scroll_bar_rect = self.get_scroll_bar_rect(console_rect)
                pygame.draw.rect(screen, WHITE, scroll_bar_rect)
                
                # Draw scroll bar background
                scroll_bg_rect = pygame.Rect(
                    console_rect.right - self.scroll_bar_width - 2,
                    console_rect.y + 2,
                    self.scroll_bar_width,
                    console_rect.height - 4
                )
                pygame.draw.rect(screen, (50, 50, 50), scroll_bg_rect)
    
    def update(self):
        """Update message console state"""
        # Update any message-specific timers or effects
        pass  # For now, we don't have any message state that needs updating 