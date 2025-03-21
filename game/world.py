import pygame
import random
import time
import os
from utils.constants import WINDOW_SIZE, WHITE, BLACK, WINDOW_TITLE
from game.sprites import sprite_manager, GameSprite
from utils.helpers import load_sprite_mappings

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
                # Check if click is on scroll bar
                if self.window_width - 20 <= event.pos[0] <= self.window_width:
                    if 60 <= event.pos[1] <= self.window_height - 80:
                        scroll_height = self.window_height - 140
                        click_ratio = (event.pos[1] - 60) / scroll_height
                        self.sprite_debug_scroll = int(click_ratio * self.max_scroll)
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
            if y + sprite.rect.height + 20 > 0 and y < self.window_height:
                # Draw sprite name
                text = small_font.render(sprite_name, True, (255, 255, 255))
                text_rect = text.get_rect()
                text_rect.centerx = x + sprite.rect.width // 2
                text_rect.bottom = y + 15
                screen.blit(text, text_rect)
                
                # Draw sprite
                sprite_copy = sprite.copy()
                sprite_copy.rect.x = x
                sprite_copy.rect.y = y + 20
                screen.blit(sprite_copy.image, sprite_copy.rect)
            
            x += sprite.rect.width + 15
            if x + sprite.rect.width > self.window_width - 15:
                x = 10
                y = row_start_y + sprite.rect.height + 40
                row_start_y = y
        
        y = row_start_y + sprite.rect.height + 40
        
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
                if sprite and y + sprite.rect.height + 20 > 0 and y < self.window_height:
                    # Draw sprite name
                    text = small_font.render(sprite_type, True, (255, 255, 255))
                    text_rect = text.get_rect()
                    text_rect.centerx = x + sprite.rect.width // 2
                    text_rect.bottom = y + 15
                    screen.blit(text, text_rect)
                    
                    # Draw sprite
                    sprite.rect.x = x
                    sprite.rect.y = y + 20
                    screen.blit(sprite.image, sprite.rect)
                
                x += sprite.rect.width + 15
                if x + sprite.rect.width > self.window_width - 15:
                    x = 10
                    y = row_start_y + sprite.rect.height + 40
                    row_start_y = y
            
            y = row_start_y + sprite.rect.height + 40
        
        # Draw scroll bar if needed
        if y + self.sprite_debug_scroll > self.window_height:
            scroll_bar_height = int((self.window_height / (y + self.sprite_debug_scroll)) * self.window_height)
            scroll_bar_pos = int((self.sprite_debug_scroll / (y - self.window_height)) * (self.window_height - scroll_bar_height))
            pygame.draw.rect(screen, (200, 200, 200), 
                           (self.window_width - 15, 0, 15, self.window_height))
            pygame.draw.rect(screen, (100, 100, 100), 
                           (self.window_width - 15, scroll_bar_pos, 15, scroll_bar_height))
        
        # Update the display
        pygame.display.flip()
    
    def _calculate_max_scroll(self):
        """Calculate the maximum scroll distance based on content height"""
        if not self._sprite_cache_initialized:
            self._sprite_cache_initialized = True
            self._cached_tiles = sprite_manager.get_available_tiles()
            self._cached_overlays = {}
        
        sprite_size = 32
        sprites_per_row = max(1, (self.window_width - 40) // (sprite_size + 10))
        row_height = sprite_size + 20
        visible_height = self.window_height - 40
        
        terrain_rows = (len(self._cached_tiles) + sprites_per_row - 1) // sprites_per_row
        terrain_height = terrain_rows * row_height + 90
        
        overlay_height = 0
        for category, sprites in self._cached_overlays.items():
            if not sprites:
                continue
            rows = (len(sprites) + sprites_per_row - 1) // sprites_per_row
            overlay_height += rows * row_height + 70
        
        total_height = terrain_height + overlay_height
        self.max_scroll = max(0, total_height - visible_height)

class World:
    def __init__(self, player):
        """Initialize the world"""
        # Initialize Pygame display
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE), pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Create sprite debug window
        self.sprite_debug_window = SpriteDebugWindow()
        
        # Initialize sprite manager
        sprite_manager.initialize()
        
        # Load sprite mappings if they exist
        load_sprite_mappings()
        
        # Initialize world state
        self.player = player
        self.player_x = 0
        self.player_y = 0
        self.world_map = {}
        self.CELL_SIZE = 32
        self.VIEWPORT_SIZE = WINDOW_SIZE // self.CELL_SIZE
        self.WORLD_SIZE = 100  # 100x100 world size
        self.window_width = WINDOW_SIZE
        self.window_height = WINDOW_SIZE
        
        # Initialize sprite dictionaries
        self.terrain_sprites = {
            'water': sprite_manager.get_base_tile('water'),
            'grass': sprite_manager.get_base_tile('grass'),
            'sand': sprite_manager.get_base_tile('sand'),
            'dirt': sprite_manager.get_base_tile('dirt')
        }
        self.overlay_sprites = {}
        
        # Generate initial world
        self.generate_world()
        
        # Display the initial viewport after world generation
        self.display_viewport()
        
        print("World initialized")

    def handle_resize(self, size):
        """Handle window resize events"""
        self.window_width, self.window_height = size
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        self.VIEWPORT_SIZE = self.window_width // self.CELL_SIZE
        self._calculate_max_scroll()

    def handle_sprite_debug_click(self, pos, event):
        """Forward sprite debug events to the debug window"""
        if self.sprite_debug_window.is_open:
            return self.sprite_debug_window.handle_event(event)
        return False

    def draw_sprite_debug(self, screen):
        """Draw the sprite debug window"""
        if not self.sprite_debug_window.is_open:
            self.sprite_debug_window.open()
        self.sprite_debug_window.draw(screen)

    def draw_text(self, text, position, color, font_size=24):
        """Helper method to draw text on the screen with custom font size"""
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def generate_world(self):
        """Generate the initial world state with varied terrain"""
        # Initialize terrain types
        terrain_types = ["grass", "dirt", "sand", "water"]
        overlay_types = {
            "Trees": ["pine", "oak", "dead"],
            "Rocks": ["boulder", "stone", "crystal"],
            "Bushes": ["small", "berry", "flower"]
        }
        
        print("\nGenerating world...")
        print("Loading terrain sprites...")
        
        # Pre-load terrain sprites to avoid repeated loading
        terrain_sprites = {}
        for terrain in terrain_types:
            sprite = sprite_manager.get_base_tile(terrain)
            if sprite:
                print(f"Loaded terrain sprite: {terrain}")
                terrain_sprites[terrain] = sprite
            else:
                print(f"Failed to load terrain sprite: {terrain}")
        
        # Pre-load overlay sprites
        overlay_sprites = {}
        for category, types in overlay_types.items():
            overlay_sprites[category] = {}
            for overlay_type in types:
                sprite = sprite_manager.get_overlay_sprite(category, overlay_type)
                if sprite:
                    print(f"Loaded overlay sprite: {category}/{overlay_type}")
                    overlay_sprites[category][overlay_type] = sprite
        
        print("\nGenerating terrain...")
        # Generate base terrain with some patterns
        for y in range(-50, 50):  # 100x100 world
            for x in range(-50, 50):
                # Create some terrain patterns
                distance = ((x/2)**2 + (y/2)**2)**0.5  # Distance from center
                noise = random.uniform(-2, 2)  # Add some randomness
                adjusted_distance = distance + noise
                
                # Determine terrain type based on distance from center with noise
                if adjusted_distance < 5:  # Center area
                    terrain = "grass"
                    # High chance of trees and bushes in grass areas
                    if random.random() < 0.2:
                        self.add_overlay(x, y, overlay_sprites, "Trees", ["pine", "oak"])
                    elif random.random() < 0.15:
                        self.add_overlay(x, y, overlay_sprites, "Bushes", ["small", "berry", "flower"])
                elif adjusted_distance < 10:  # Ring around center
                    # Transition zone between grass and dirt
                    terrain = "dirt" if random.random() < 0.7 else "grass"
                    # Some rocks and dead trees in dirt areas
                    if random.random() < 0.15:
                        self.add_overlay(x, y, overlay_sprites, "Rocks", ["boulder", "stone"])
                    elif random.random() < 0.1:
                        self.add_overlay(x, y, overlay_sprites, "Trees", ["dead"])
                elif adjusted_distance < 15:  # Outer ring
                    # Transition zone between dirt and sand
                    terrain = "sand" if random.random() < 0.7 else "dirt"
                    # Few rocks in sand areas
                    if random.random() < 0.1:
                        self.add_overlay(x, y, overlay_sprites, "Rocks", ["stone"])
                elif adjusted_distance < 20:  # Water border
                    # Transition zone between sand and water
                    terrain = "water" if random.random() < 0.7 else "sand"
                else:  # Random terrain for outer areas
                    weights = [0.4, 0.3, 0.2, 0.1]  # Weights for [grass, dirt, sand, water]
                    terrain = random.choices(terrain_types, weights=weights)[0]
                    # Add random overlays based on terrain
                    if terrain == "grass" and random.random() < 0.15:
                        self.add_overlay(x, y, overlay_sprites, "Trees", ["pine", "oak"])
                    elif terrain == "dirt" and random.random() < 0.1:
                        self.add_overlay(x, y, overlay_sprites, "Rocks", ["boulder", "stone"])
                
                # Get the pre-loaded sprite or create a new one
                base_sprite = terrain_sprites.get(terrain)
                if base_sprite:
                    # Create a new sprite instance using the copy method
                    sprite = base_sprite.copy()
                    sprite.rect.x = x * self.CELL_SIZE
                    sprite.rect.y = y * self.CELL_SIZE
                    self.world_map[(x, y)] = sprite
                else:
                    print(f"Warning: Could not create sprite for {terrain} at ({x}, {y})")
        
        print("World generation complete!")
    
    def add_overlay(self, x, y, overlay_sprites, category, types):
        """Add an overlay sprite to the world"""
        if category in overlay_sprites:
            overlay_type = random.choice(types)
            if overlay_type in overlay_sprites[category]:
                # Get a fresh overlay sprite from sprite manager instead of using cached one
                sprite = sprite_manager.get_overlay_sprite(category, overlay_type)
                if sprite and sprite.image:
                    sprite.rect.x = x * self.CELL_SIZE
                    sprite.rect.y = y * self.CELL_SIZE
                    # Store overlay in a separate layer
                    if not hasattr(self, 'overlay_map'):
                        self.overlay_map = {}
                    self.overlay_map[(x, y)] = sprite

    def display_viewport(self, screen=None, player_x=None, player_y=None, offset_y=0):
        """Display the current viewport centered on the player"""
        if screen is None:
            screen = self.screen
        if player_x is None:
            player_x = self.player_x
        if player_y is None:
            player_y = self.player_y
            
        # Clear the screen
        screen.fill(WHITE)
        
        # Calculate viewport boundaries
        viewport_start_x = max(0, player_x - (self.VIEWPORT_SIZE // 2))
        viewport_start_y = max(0, player_y - (self.VIEWPORT_SIZE // 2))
        viewport_end_x = min(self.WORLD_SIZE, viewport_start_x + self.VIEWPORT_SIZE)
        viewport_end_y = min(self.WORLD_SIZE, viewport_start_y + self.VIEWPORT_SIZE)
        
        # Draw terrain
        for y in range(viewport_start_y, viewport_end_y):
            for x in range(viewport_start_x, viewport_end_x):
                screen_x = (x - viewport_start_x) * self.CELL_SIZE
                screen_y = (y - viewport_start_y) * self.CELL_SIZE + offset_y
                terrain_type = self.get_terrain(x, y)
                if terrain_type in self.terrain_sprites:
                    sprite = self.terrain_sprites[terrain_type]
                    screen.blit(sprite.image, (screen_x, screen_y))
        
        # Draw overlay features
        for y in range(viewport_start_y, viewport_end_y):
            for x in range(viewport_start_x, viewport_end_x):
                screen_x = (x - viewport_start_x) * self.CELL_SIZE
                screen_y = (y - viewport_start_y) * self.CELL_SIZE + offset_y
                overlay_type = self.get_overlay(x, y)
                if overlay_type in self.overlay_sprites:
                    sprite = self.overlay_sprites[overlay_type]
                    screen.blit(sprite.image, (screen_x, screen_y))

    def get_path_to(self, target_x, target_y):
        """Get a path to the target position"""
        path = []
        current_x = self.player_x
        current_y = self.player_y
        
        while current_x != target_x or current_y != target_y:
            # Move in x direction first
            if current_x < target_x:
                current_x += 1
            elif current_x > target_x:
                current_x -= 1
            # Then move in y direction
            elif current_y < target_y:
                current_y += 1
            elif current_y > target_y:
                current_y -= 1
            # Add the new position to the path
            if self.is_valid_move(current_x, current_y):
                path.append((current_x, current_y))
            else:
                # If we hit an invalid move, stop pathfinding
                break
        
        return path

    def is_valid_move(self, x, y):
        """Check if a move to the given coordinates is valid"""
        # Check if the position is within world bounds (-50 to 50 for 100x100 world)
        if not (-50 <= x <= 50 and -50 <= y <= 50):
            return False
            
        # Check if the terrain at this position is walkable
        terrain = self.get_terrain(x, y)
        if terrain == 'water':  # Water is not walkable
            return False
            
        return True

    def move_player(self, new_x, new_y):
        """Move the player to a new position and return True if there's an encounter"""
        # Only update position if the move is valid
        if self.is_valid_move(new_x, new_y):
            self.player_x = new_x
            self.player_y = new_y
            return True
        return False

    def _calculate_max_scroll(self):
        """Calculate the maximum scroll distance based on content height"""
        # Initialize sprite cache if not already done
        if not self._sprite_cache_initialized:
            self._sprite_cache_initialized = True
            self._cached_tiles = sprite_manager.get_available_tiles()
            self._cached_overlays = {}
        
        # Calculate dimensions
        sprite_size = 32
        sprites_per_row = max(1, (self.window_width - 40) // (sprite_size + 10))
        row_height = sprite_size + 20
        visible_height = self.window_height - 40
        
        # Calculate total height needed for terrain tiles
        terrain_rows = (len(self._cached_tiles) + sprites_per_row - 1) // sprites_per_row
        terrain_height = terrain_rows * row_height + 90  # 90 is initial offset
        
        # Calculate total height needed for overlay sections
        overlay_height = 0
        for category, sprites in self._cached_overlays.items():
            if not sprites:
                continue
            rows = (len(sprites) + sprites_per_row - 1) // sprites_per_row
            overlay_height += rows * row_height + 70  # 70 is space for category header and padding
        
        # Total content height
        total_height = terrain_height + overlay_height
        
        # Calculate maximum scroll
        self.max_scroll = max(0, total_height - visible_height)
        print(f"Max scroll calculated: {self.max_scroll}")  # Debug print 

    def get_terrain(self, x, y):
        """Get the terrain type at the given coordinates"""
        if (x, y) in self.world_map:
            sprite = self.world_map[(x, y)]
            # Extract terrain type from sprite name
            sprite_name = sprite.name if hasattr(sprite, 'name') else ''
            if 'water' in sprite_name.lower():
                return 'water'
            elif 'grass' in sprite_name.lower():
                return 'grass'
            elif 'sand' in sprite_name.lower():
                return 'sand'
            elif 'dirt' in sprite_name.lower():
                return 'dirt'
        return 'grass'  # Default to grass for unknown terrain

    def get_overlay(self, x, y):
        """Get the overlay type at the given coordinates"""
        if hasattr(self, 'overlay_map') and (x, y) in self.overlay_map:
            sprite = self.overlay_map[(x, y)]
            return sprite.name if hasattr(sprite, 'name') else None
        return None 