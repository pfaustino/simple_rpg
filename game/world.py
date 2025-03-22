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
        # Initialize basic attributes first
        self.kill_count = 0  # Initialize kill counter first
        self.player = player
        self.game = None  # Will be set by Game class
        self.player_x = 0
        self.player_y = 0
        self.world_map = {}
        self.overlay_map = {}  # Initialize overlay map
        self.CELL_SIZE = 32
        self.viewport_cells_x = WINDOW_SIZE // self.CELL_SIZE
        self.viewport_cells_y = WINDOW_SIZE // self.CELL_SIZE
        # Make both dimensions odd for proper centering
        if self.viewport_cells_x % 2 == 0:
            self.viewport_cells_x -= 1
        if self.viewport_cells_y % 2 == 0:
            self.viewport_cells_y -= 1
        self.WORLD_SIZE = 100  # 100x100 world size
        self.screen = None
        self.window_width = WINDOW_SIZE
        self.window_height = WINDOW_SIZE
        
        # Initialize Pygame display
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE), pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Create sprite debug window
        self.sprite_debug_window = SpriteDebugWindow()
        
        # Initialize sprite manager first
        sprite_manager.initialize()
        
        # Load sprite mappings if they exist
        load_sprite_mappings()
        
        print("Loading terrain sprites...")
        # Initialize terrain sprites with proper error handling
        self.terrain_sprites = {}
        for terrain in ['water', 'grass', 'sand', 'dirt']:
            sprite = sprite_manager.get_base_tile(terrain)
            if sprite and sprite.image:
                print(f"Loaded {terrain} sprite successfully")
                self.terrain_sprites[terrain] = sprite
            else:
                print(f"Failed to load {terrain} sprite")
        
        # Define terrain colors as fallback
        self.terrain_colors = {
            'water': (0, 0, 255),    # Blue
            'grass': (0, 255, 0),    # Green
            'sand': (255, 223, 128),  # Sandy yellow
            'dirt': (139, 69, 19)     # Brown
        }
        
        # Generate initial world
        self.generate_world()
        
        print("World initialized successfully")

    def handle_resize(self, size):
        """Handle window resize events"""
        self.window_width, self.window_height = size
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        
        # Calculate viewport size in cells for both dimensions
        self.viewport_cells_x = self.window_width // self.CELL_SIZE
        self.viewport_cells_y = (self.window_height - 190) // self.CELL_SIZE  # Account for UI elements
        
        # Make both dimensions odd for proper centering
        if self.viewport_cells_x % 2 == 0:
            self.viewport_cells_x -= 1
        if self.viewport_cells_y % 2 == 0:
            self.viewport_cells_y -= 1
            
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

    def display_viewport(self, screen, player_x, player_y, status_height=0):
        """Display the visible portion of the world centered on the player"""
        self.screen = screen
        
        # Calculate the visible area, ensuring player is centered
        half_viewport_x = self.viewport_cells_x // 2
        half_viewport_y = self.viewport_cells_y // 2
        start_x = player_x - half_viewport_x
        start_y = player_y - half_viewport_y
        end_x = player_x + half_viewport_x + 1
        end_y = player_y + half_viewport_y + 1
        
        # Calculate the offset to center the viewport
        viewport_pixel_width = self.viewport_cells_x * self.CELL_SIZE
        viewport_pixel_height = self.viewport_cells_y * self.CELL_SIZE
        offset_x = (self.window_width - viewport_pixel_width) // 2
        offset_y = status_height + (self.window_height - status_height - 150 - viewport_pixel_height) // 2
        
        # Draw visible terrain
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Convert world coordinates to screen coordinates
                screen_x = (x - start_x) * self.CELL_SIZE + offset_x
                screen_y = (y - start_y) * self.CELL_SIZE + offset_y
                
                # Get terrain and overlay at this position
                terrain_type = self.get_terrain(x, y)
                overlay = self.get_overlay(x, y)
                
                # Draw terrain sprite
                if terrain_type in self.terrain_sprites:
                    sprite = self.terrain_sprites[terrain_type]
                    if sprite and sprite.image:
                        screen.blit(sprite.image, (screen_x, screen_y))
                
                # Draw overlay sprite if it exists
                if overlay:
                    # Get the overlay sprite from sprite manager
                    overlay_sprite = None
                    if isinstance(overlay, str):
                        if 'tree' in overlay.lower():
                            overlay_sprite = sprite_manager.get_overlay_sprite('Trees', overlay)
                        elif 'rock' in overlay.lower() or 'boulder' in overlay.lower() or 'stone' in overlay.lower():
                            overlay_sprite = sprite_manager.get_overlay_sprite('Rocks', overlay)
                        elif 'bush' in overlay.lower() or 'berry' in overlay.lower() or 'flower' in overlay.lower():
                            overlay_sprite = sprite_manager.get_overlay_sprite('Bushes', overlay)
                    
                    if overlay_sprite and overlay_sprite.image:
                        screen.blit(overlay_sprite.image, (screen_x, screen_y))
        
        # Store these for player drawing
        self.viewport_offset_x = offset_x
        self.viewport_offset_y = offset_y
        self.half_viewport_x = half_viewport_x
        self.half_viewport_y = half_viewport_y

    def get_terrain(self, x, y):
        """Get the terrain type at the given coordinates"""
        # Ensure coordinates are within world bounds
        x = max(-50, min(49, x))  # World is 100x100, centered at 0,0
        y = max(-50, min(49, y))
        
        if (x, y) in self.world_map:
            sprite = self.world_map[(x, y)]
            if hasattr(sprite, 'name'):
                sprite_name = sprite.name.lower()
                # Check terrain types
                if 'water' in sprite_name:
                    return 'water'
                elif 'grass' in sprite_name:
                    return 'grass'
                elif 'sand' in sprite_name:
                    return 'sand'
                elif 'dirt' in sprite_name:
                    return 'dirt'
        
        return 'grass'  # Default to grass for unknown terrain

    def get_overlay(self, x, y):
        """Get the overlay type at the given coordinates"""
        # Ensure coordinates are within world bounds
        x = max(-50, min(49, x))  # World is 100x100, centered at 0,0
        y = max(-50, min(49, y))
        
        if hasattr(self, 'overlay_map') and (x, y) in self.overlay_map:
            sprite = self.overlay_map[(x, y)]
            if hasattr(sprite, 'name'):
                return sprite.name
        return None

    def resize(self, width, height):
        """Update viewport size when window is resized"""
        self.window_width = width
        self.window_height = height
        
        # Calculate viewport size to ensure player is centered on a single tile
        # Subtract margins and ensure odd number of tiles
        self.viewport_cells_x = (self.window_width - 40) // self.CELL_SIZE
        self.viewport_cells_y = (self.window_height - 190) // self.CELL_SIZE  # Account for UI elements
        
        # Make sure both dimensions are odd for perfect centering
        if self.viewport_cells_x % 2 == 0:
            self.viewport_cells_x -= 1
        if self.viewport_cells_y % 2 == 0:
            self.viewport_cells_y -= 1
        
        # Update the screen surface with new dimensions
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        
        # Force a redraw of the viewport
        if self.screen:
            self.display_viewport(self.screen, self.player_x, self.player_y)

    def update(self):
        """Update world state"""
        # Update any world-specific timers or effects
        pass  # For now, we don't have any world state that needs updating

    def draw(self, screen):
        """Draw the world"""
        # Draw the viewport
        self.display_viewport(screen, self.player_x, self.player_y)
        
        # Calculate exact player position
        # The player should be exactly half_viewport tiles from the start of the viewport
        player_screen_x = self.half_viewport_x * self.CELL_SIZE + self.viewport_offset_x
        player_screen_y = self.half_viewport_y * self.CELL_SIZE + self.viewport_offset_y
        
        # Draw the player
        self.player.draw(screen, player_screen_x, player_screen_y)

    def get_path_to(self, target_x, target_y):
        """Get a path to the target position"""
        # If the target is not valid, return empty path
        if not self.is_valid_move(target_x, target_y):
            return []
            
        path = []
        current_x = self.player_x
        current_y = self.player_y
        
        # Prevent infinite loops by limiting path length
        max_attempts = 100
        attempts = 0
        
        while (current_x != target_x or current_y != target_y) and attempts < max_attempts:
            attempts += 1
            # Move in x direction first
            if current_x < target_x:
                next_x = current_x + 1
                next_y = current_y
            elif current_x > target_x:
                next_x = current_x - 1
                next_y = current_y
            # Then move in y direction
            elif current_y < target_y:
                next_x = current_x
                next_y = current_y + 1
            elif current_y > target_y:
                next_x = current_x
                next_y = current_y - 1
            else:
                break
                
            # Check if the next move is valid (without showing messages)
            if self.is_valid_move(next_x, next_y):
                path.append((next_x, next_y))
                current_x = next_x
                current_y = next_y
            else:
                # If we hit an invalid move, try to find an alternative path
                # Try moving in y direction first if we were moving in x
                if next_x != current_x:
                    if self.is_valid_move(current_x, next_y):
                        path.append((current_x, next_y))
                        current_y = next_y
                        continue
                # Try moving in x direction first if we were moving in y
                elif next_y != current_y:
                    if self.is_valid_move(next_x, current_y):
                        path.append((next_x, current_y))
                        current_x = next_x
                        continue
                # If no alternative path is found, stop pathfinding
                break
        
        return path

    def is_valid_move(self, x, y, show_messages=False):
        """Check if a move to the given coordinates is valid"""
        # Check world bounds
        if x < -50 or x >= 50 or y < -50 or y >= 50:  # World is 100x100, centered at 0,0
            if show_messages and hasattr(self, 'game') and self.game and hasattr(self.game, 'message_console'):
                self.game.message_console.add_message("You cannot leave the world!")
            return False
            
        # Check terrain
        terrain = self.get_terrain(x, y)
        if terrain == 'water':  # Water is not walkable
            if show_messages and hasattr(self, 'game') and self.game and hasattr(self.game, 'message_console'):
                self.game.message_console.add_message("You cannot walk on water!")
            return False
            
        # Check overlays (trees, rocks, etc.)
        overlay = self.get_overlay(x, y)
        if overlay:  # Only check if overlay exists
            if isinstance(overlay, str):  # Make sure overlay is a string
                overlay_lower = overlay.lower()
                blocking_types = ['tree', 'rock', 'boulder', 'stone']
                if any(block_type in overlay_lower for block_type in blocking_types):
                    if show_messages and hasattr(self, 'game') and self.game and hasattr(self.game, 'message_console'):
                        self.game.message_console.add_message(f"You cannot walk through {overlay}!")
                    return False
            
        return True

    def move_player(self, new_x, new_y):
        """Move the player to a new position and return True if there's an encounter"""
        # Check if the move is valid with messages enabled
        if self.is_valid_move(new_x, new_y, show_messages=True):
            self.player_x = new_x
            self.player_y = new_y
            return False  # Encounters disabled temporarily
        return False

    def teleport_home(self):
        """Teleport the player back to the home position (center of map)"""
        # Store old position for animation
        old_x, old_y = self.player_x, self.player_y
        
        # Set new position to center of map
        self.player_x = 0
        self.player_y = 0
        
        # Add teleport message
        if hasattr(self, 'game') and self.game and hasattr(self.game, 'message_console'):
            self.game.message_console.add_message("You have been teleported home!")
            
        # Force a redraw of the viewport
        if self.screen:
            self.display_viewport(self.screen, self.player_x, self.player_y)
            pygame.display.flip()

    def handle_input(self, event):
        """Handle keyboard input for the world"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:  # Press 'H' to teleport home
                self.teleport_home()
                return True
        return False