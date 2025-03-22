import pygame
from game.sprites import sprite_manager

class SpriteDebugWindow:
    def __init__(self):
        """Initialize the sprite debug window"""
        self.window_width = 800
        self.window_height = 600
        self.sprite_debug_scroll = 0
        self.max_scroll = 0
        self._sprite_cache_initialized = False
        self._cached_tiles = []
        self._cached_overlays = {}
        self._last_debug_print = 0
        self.is_open = False
    
    def open(self):
        """Open the sprite debug view"""
        if not self.is_open:
            self.is_open = True
            self._calculate_max_scroll()
    
    def close(self):
        """Close the sprite debug view"""
        self.is_open = False
    
    def handle_event(self, event):
        """Handle events for the sprite debug view"""
        if not self.is_open:
            return False
        
        # Handle keyboard events for scrolling
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_w]:
                self.sprite_debug_scroll = max(0, self.sprite_debug_scroll - 50)
                return True
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.sprite_debug_scroll = min(self.max_scroll, self.sprite_debug_scroll + 50)
                return True
            elif event.key == pygame.K_PAGEUP:
                self.sprite_debug_scroll = max(0, self.sprite_debug_scroll - 200)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.sprite_debug_scroll = min(self.max_scroll, self.sprite_debug_scroll + 200)
                return True
            elif event.key == pygame.K_HOME:
                self.sprite_debug_scroll = 0
                return True
            elif event.key == pygame.K_END:
                self.sprite_debug_scroll = self.max_scroll
                return True
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                self.close()
                return True
        
        # Handle mouse wheel scrolling
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Mouse wheel up
                self.sprite_debug_scroll = max(0, self.sprite_debug_scroll - 50)
                return True
            elif event.button == 5:  # Mouse wheel down
                self.sprite_debug_scroll = min(self.max_scroll, self.sprite_debug_scroll + 50)
                return True
            elif event.button == 1:  # Left click
                # Check if click is on scroll bar area
                if self.window_width - 20 <= event.pos[0] <= self.window_width:
                    # Calculate scroll bar metrics
                    scroll_bar_height = int((self.window_height / (self.total_content_height + self.sprite_debug_scroll)) * self.window_height)
                    scroll_bar_height = max(30, min(scroll_bar_height, self.window_height))  # Ensure minimum and maximum size
                    
                    # Calculate scroll position based on click
                    click_ratio = event.pos[1] / self.window_height
                    self.sprite_debug_scroll = int(click_ratio * self.max_scroll)
                    self.sprite_debug_scroll = max(0, min(self.sprite_debug_scroll, self.max_scroll))
                    return True
        
        return False
    
    def draw(self, screen):
        """Draw the sprite debug view contents"""
        if not self.is_open:
            return
        
        # Store current window dimensions
        self.window_width = screen.get_width()
        self.window_height = screen.get_height()
        
        # Clear the screen first
        screen.fill((0, 0, 0))
        
        # Draw header
        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)
        text = font.render("Sprite Debug View (ESC/SPACE to close)", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        # Start position for drawing sprites
        x = 10
        y = 40 - self.sprite_debug_scroll
        
        # Draw base terrain tiles
        text = font.render("Base Terrain:", True, (255, 255, 255))
        if y + 30 > 0 and y < self.window_height:
            screen.blit(text, (x, y))
        y += 30
        
        # Get base terrain tiles
        base_tiles = sprite_manager._cached_base_tiles
        row_start_y = y
        
        for sprite_name, sprite in base_tiles.items():
            if y + 64 + 20 > 0 and y < self.window_height:
                # Clean up sprite name - remove directory path and extension
                clean_name = sprite_name.split('/')[-1].split('.')[0]
                
                # Draw sprite name
                text = small_font.render(clean_name, True, (255, 255, 255))
                text_rect = text.get_rect()
                text_rect.centerx = x + 32
                text_rect.bottom = y + 15
                screen.blit(text, text_rect)
                
                # Draw sprite at 64x64
                sprite_copy = sprite.copy()
                if sprite_copy.image.get_size() != (64, 64):
                    scaled_image = pygame.transform.scale(sprite_copy.image, (64, 64))
                else:
                    scaled_image = sprite_copy.image
                screen.blit(scaled_image, (x, y + 20))
            
            x += 64 + 30
            if x + 64 > self.window_width - 15:
                x = 10
                y = row_start_y + 64 + 40
                row_start_y = y
        
        y = row_start_y + 64 + 40
        
        # Draw overlay sections
        overlay_categories = {
            "Trees": ["pine", "oak", "dead"],
            "Rocks": ["boulder", "stone", "crystal"],
            "Bushes": ["small", "berry", "flower"]
        }
        
        for category, sprite_types in overlay_categories.items():
            if y + 30 > 0 and y < self.window_height:
                x = 10
                text = font.render(f"{category}:", True, (255, 255, 255))
                screen.blit(text, (x, y))
            y += 30
            row_start_y = y
            
            for sprite_type in sprite_types:
                sprite = sprite_manager.get_overlay_sprite(category, sprite_type)
                if sprite and sprite.image and y + 64 + 20 > 0 and y < self.window_height:
                    # Clean up sprite name - remove directory path and extension
                    clean_name = sprite_type.split('/')[-1].split('.')[0]
                    
                    # Draw sprite name
                    text = small_font.render(clean_name, True, (255, 255, 255))
                    text_rect = text.get_rect()
                    text_rect.centerx = x + 32
                    text_rect.bottom = y + 15
                    screen.blit(text, text_rect)
                    
                    # Draw sprite at 64x64
                    sprite_copy = sprite.copy()
                    if sprite_copy.image.get_size() != (64, 64):
                        scaled_image = pygame.transform.scale(sprite_copy.image, (64, 64))
                    else:
                        scaled_image = sprite_copy.image
                    screen.blit(scaled_image, (x, y + 20))
                
                x += 64 + 30
                if x + 64 > self.window_width - 15:
                    x = 10
                    y = row_start_y + 64 + 40
                    row_start_y = y
            
            y = row_start_y + 64 + 40
        
        # Store total content height for scroll calculations
        self.total_content_height = y
        
        # Draw scroll bar if content exceeds window height
        if self.total_content_height > self.window_height:
            # Calculate scroll bar metrics
            content_ratio = min(1.0, self.window_height / self.total_content_height)
            scroll_bar_height = max(30, int(content_ratio * self.window_height))
            
            # Calculate scroll bar position
            available_scroll_space = self.window_height - scroll_bar_height
            scroll_progress = self.sprite_debug_scroll / self.max_scroll if self.max_scroll > 0 else 0
            scroll_bar_pos = int(scroll_progress * available_scroll_space)
            
            # Draw scroll bar background
            pygame.draw.rect(screen, (50, 50, 50), 
                           (self.window_width - 15, 0, 15, self.window_height))
            
            # Draw scroll bar
            pygame.draw.rect(screen, (150, 150, 150), 
                           (self.window_width - 15, scroll_bar_pos, 15, scroll_bar_height))
        
        # Update the display
        pygame.display.flip()
    
    def _calculate_max_scroll(self):
        """Calculate the maximum scroll distance based on content height"""
        # Initialize sprite cache if needed
        if not self._sprite_cache_initialized:
            self._sprite_cache_initialized = True
            self._cached_tiles = sprite_manager.get_available_tiles()
            self._cached_overlays = {
                "Trees": ["pine", "oak", "dead"],
                "Rocks": ["boulder", "stone", "crystal"],
                "Bushes": ["small", "berry", "flower"]
            }
        
        # Calculate base terrain height
        base_tiles = sprite_manager._cached_base_tiles
        sprite_size = 64  # 2x original size (32 * 2)
        spacing = 30  # Increased spacing for larger sprites
        sprites_per_row = max(1, (self.window_width - 40) // (sprite_size + spacing))
        row_height = sprite_size + 40  # Include space for text and padding
        
        # Calculate height needed for base terrain
        num_base_tiles = len(base_tiles)
        base_terrain_rows = (num_base_tiles + sprites_per_row - 1) // sprites_per_row
        total_height = 40  # Initial header space
        total_height += 30  # "Base Terrain:" text
        total_height += base_terrain_rows * row_height
        total_height += 40  # Space after base terrain section
        
        # Calculate height needed for overlay sections
        for category in self._cached_overlays:
            total_height += 30  # Category header
            num_sprites = len(self._cached_overlays[category])
            category_rows = (num_sprites + sprites_per_row - 1) // sprites_per_row
            total_height += category_rows * row_height
            total_height += 40  # Space after category
        
        # Add extra padding at the bottom
        total_height += 40
        
        # Calculate max scroll value
        visible_height = self.window_height
        self.max_scroll = max(0, total_height - visible_height)
        self.total_content_height = total_height 