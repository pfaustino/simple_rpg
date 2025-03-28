import pygame
import random
import time
from utils.constants import WINDOW_SIZE, WHITE, BLACK, WINDOW_TITLE
from game.sprites import sprite_manager, GameSprite
from utils.helpers import load_sprite_mappings

class World:
    def __init__(self, player):
        """Initialize the world"""
        # Initialize Pygame display
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE), pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Initialize sprite debug variables
        self.show_sprite_debug = False
        self.selected_sprite = None
        self.sprite_debug_scroll = 0
        self.max_scroll = 0  # Will be calculated based on content
        self._sprite_cache_initialized = False
        self._cached_tiles = []
        self._cached_overlays = {}
        self.window_width = WINDOW_SIZE
        self.window_height = WINDOW_SIZE
        
        # Initialize sprite manager
        sprite_manager.initialize()
        
        # Load sprite mappings if they exist
        load_sprite_mappings()
        
        # Create player character
        self.player = player
        
        # Initialize world state
        self.player_x = 0
        self.player_y = 0
        self.world_map = {}
        self.CELL_SIZE = 32
        self.VIEWPORT_SIZE = self.window_width // self.CELL_SIZE
        
        # Initialize debug flags
        self.show_debug = False
        
        # Generate initial world
        self.generate_world()
        
        # Calculate initial max scroll
        self._calculate_max_scroll()
        
        print("World initialized")  # Debug print

    def handle_resize(self, size):
        """Handle window resize events"""
        self.window_width, self.window_height = size
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        self.VIEWPORT_SIZE = self.window_width // self.CELL_SIZE
        self._calculate_max_scroll()

    def draw_sprite_debug(self):
        """Draw the sprite debug view"""
        # Clear the screen
        self.screen.fill((255, 255, 255))
        
        # Get available sprites
        base_tiles = sprite_manager.get_available_tiles()
        overlays = sprite_manager.get_available_overlays()
        
        # Set up font
        font = pygame.font.Font(None, 24)
        
        # Draw header (fixed position)
        header = font.render("Sprite Debug View", True, (0, 0, 0))
        subheader = font.render("Click a sprite to select it", True, (0, 0, 0))
        self.screen.blit(header, (10, 10))
        self.screen.blit(subheader, (10, 35))
        
        # Start position for drawing sprites (adjusted for scroll)
        x = 10
        y = 70 - self.sprite_debug_scroll
        row_height = 40
        
        # Calculate sprites per row based on window width
        sprites_per_row = max(1, (self.window_width - 40) // 40)
        
        # Draw base terrain tiles section
        terrain_label = font.render("Base Terrain:", True, (0, 0, 0))
        if y + 30 > 60 and y < self.window_height:  # Only draw if visible
            self.screen.blit(terrain_label, (x, y))
        y += 30
        
        # Draw terrain tiles
        row_x = x
        for sprite in base_tiles:
            if y > -40 and y < self.window_height:  # Only draw if in view
                if sprite.image:
                    self.screen.blit(sprite.image, (row_x, y))
            row_x += 40
            if row_x > self.window_width - 40:
                row_x = x
                y += row_height
        
        if row_x != x:  # If the last row wasn't full
            y += row_height
        
        # Draw overlay sections
        for category, sprites in overlays.items():
            # Draw category label
            category_label = font.render(f"{category}:", True, (0, 0, 0))
            if y + 30 > 60 and y < self.window_height:  # Only draw if visible
                self.screen.blit(category_label, (x, y))
            y += 30
            
            # Draw sprites in this category
            row_x = x
            for sprite in sprites:
                if y > -40 and y < self.window_height:  # Only draw if in view
                    if sprite.image:
                        self.screen.blit(sprite.image, (row_x, y))
                row_x += 40
                if row_x > self.window_width - 40:
                    row_x = x
                    y += row_height
            
            if row_x != x:  # If the last row wasn't full
                y += row_height
            y += 20  # Add spacing between categories
        
        # Draw scroll bar if needed
        total_height = y + self.sprite_debug_scroll
        if total_height > self.window_height:
            bar_height = max(40, self.window_height * self.window_height / total_height)
            bar_pos = (self.sprite_debug_scroll / (total_height - self.window_height)) * (self.window_height - bar_height)
            pygame.draw.rect(self.screen, (200, 200, 200), 
                           (self.window_width - 20, 60, 20, self.window_height - 80))
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (self.window_width - 18, 60 + bar_pos, 16, bar_height))
        
        # Update the max scroll value
        self.max_scroll = max(0, total_height - self.window_height + 60)
        
        # Update the display
        pygame.display.flip()

    def handle_sprite_debug_click(self, pos, event):
        """Handle clicks and keyboard events in sprite debug view"""
        # Rate limit debug prints to once per second
        current_time = time.time()
        if not hasattr(self, '_last_debug_print'):
            self._last_debug_print = 0
        
        def debug_print(message):
            if current_time - self._last_debug_print >= 1.0:
                print(message)
                self._last_debug_print = current_time
        
        # Handle keyboard events for scrolling
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                debug_print("Scrolling up")
                self.sprite_debug_scroll = max(0, self.sprite_debug_scroll - 50)
                return True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                debug_print("Scrolling down")
                self.sprite_debug_scroll = min(self.max_scroll, self.sprite_debug_scroll + 50)
                return True
            elif event.key == pygame.K_PAGEUP:
                debug_print("Page up")
                self.sprite_debug_scroll = max(0, self.sprite_debug_scroll - 200)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                debug_print("Page down")
                self.sprite_debug_scroll = min(self.max_scroll, self.sprite_debug_scroll + 200)
                return True
            elif event.key == pygame.K_HOME:
                debug_print("Jump to top")
                self.sprite_debug_scroll = 0
                return True
            elif event.key == pygame.K_END:
                debug_print("Jump to bottom")
                self.sprite_debug_scroll = self.max_scroll
                return True
        
        # Handle mouse wheel scrolling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Mouse wheel up
                debug_print("Mouse wheel up")
                self.sprite_debug_scroll = max(0, self.sprite_debug_scroll - 50)
                return True
            elif event.button == 5:  # Mouse wheel down
                debug_print("Mouse wheel down")
                self.sprite_debug_scroll = min(self.max_scroll, self.sprite_debug_scroll + 50)
                return True
            elif event.button == 1:  # Left click
                # Check if click is on scroll bar
                if self.window_width - 20 <= pos[0] <= self.window_width:
                    if 60 <= pos[1] <= self.window_height - 80:
                        debug_print("Click on scroll bar")
                        scroll_height = self.window_height - 140
                        click_ratio = (pos[1] - 60) / scroll_height
                        self.sprite_debug_scroll = int(click_ratio * self.max_scroll)
                        return True
        
        return False

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

    def display_viewport(self):
        """Display the current viewport of the world"""
        # Clear screen with white background
        self.screen.fill(WHITE)
        
        # Calculate viewport boundaries
        viewport_start_x = self.player_x - self.VIEWPORT_SIZE // 2
        viewport_start_y = self.player_y - self.VIEWPORT_SIZE // 2
        viewport_end_x = viewport_start_x + self.VIEWPORT_SIZE
        viewport_end_y = viewport_start_y + self.VIEWPORT_SIZE
        
        world_size = 50  # Half of our 100x100 world
        grass_sprite = None  # Cache grass sprite for edge filling
        
        # Calculate actual viewport size in pixels
        viewport_width_pixels = self.window_width
        viewport_height_pixels = self.window_height
        
        # First draw terrain
        for y in range(viewport_start_y, viewport_end_y + 1):  # +1 to handle partial tiles
            for x in range(viewport_start_x, viewport_end_x + 1):  # +1 to handle partial tiles
                screen_x = (x - viewport_start_x) * self.CELL_SIZE
                screen_y = (y - viewport_start_y) * self.CELL_SIZE
                
                # Check if position is outside world bounds
                if abs(x) > world_size or abs(y) > world_size:
                    # Get or create grass sprite for edges
                    if grass_sprite is None:
                        grass_sprite = sprite_manager.get_base_tile("grass")
                    if grass_sprite and grass_sprite.image:
                        # Scale grass sprite if needed
                        current_size = grass_sprite.image.get_size()
                        if current_size != (self.CELL_SIZE, self.CELL_SIZE):
                            scaled_image = pygame.transform.scale(grass_sprite.image, 
                                                               (self.CELL_SIZE, self.CELL_SIZE))
                            # Calculate the portion of the tile that should be visible
                            visible_width = min(self.CELL_SIZE, viewport_width_pixels - screen_x)
                            visible_height = min(self.CELL_SIZE, viewport_height_pixels - screen_y)
                            if visible_width > 0 and visible_height > 0:
                                # Only draw the visible portion of the tile
                                visible_rect = pygame.Rect(0, 0, visible_width, visible_height)
                                self.screen.blit(scaled_image, (screen_x, screen_y), visible_rect)
                        else:
                            visible_width = min(self.CELL_SIZE, viewport_width_pixels - screen_x)
                            visible_height = min(self.CELL_SIZE, viewport_height_pixels - screen_y)
                            if visible_width > 0 and visible_height > 0:
                                visible_rect = pygame.Rect(0, 0, visible_width, visible_height)
                                self.screen.blit(grass_sprite.image, (screen_x, screen_y), visible_rect)
                    continue
                
                # Get terrain at this position
                terrain_sprite = self.world_map.get((x, y))
                if terrain_sprite is None:
                    # If no terrain exists at this position, create grass
                    if grass_sprite is None:
                        grass_sprite = sprite_manager.get_base_tile("grass")
                    if grass_sprite:
                        # Create a new sprite instance using the copy method
                        terrain_sprite = grass_sprite.copy()
                        terrain_sprite.rect.x = x * self.CELL_SIZE
                        terrain_sprite.rect.y = y * self.CELL_SIZE
                        self.world_map[(x, y)] = terrain_sprite
                
                if terrain_sprite and terrain_sprite.image:
                    # Scale sprite to match cell size if needed
                    current_size = terrain_sprite.image.get_size()
                    if current_size != (self.CELL_SIZE, self.CELL_SIZE):
                        scaled_image = pygame.transform.scale(terrain_sprite.image, 
                                                           (self.CELL_SIZE, self.CELL_SIZE))
                        # Calculate the portion of the tile that should be visible
                        visible_width = min(self.CELL_SIZE, viewport_width_pixels - screen_x)
                        visible_height = min(self.CELL_SIZE, viewport_height_pixels - screen_y)
                        if visible_width > 0 and visible_height > 0:
                            visible_rect = pygame.Rect(0, 0, visible_width, visible_height)
                            self.screen.blit(scaled_image, (screen_x, screen_y), visible_rect)
                    else:
                        visible_width = min(self.CELL_SIZE, viewport_width_pixels - screen_x)
                        visible_height = min(self.CELL_SIZE, viewport_height_pixels - screen_y)
                        if visible_width > 0 and visible_height > 0:
                            visible_rect = pygame.Rect(0, 0, visible_width, visible_height)
                            self.screen.blit(terrain_sprite.image, (screen_x, screen_y), visible_rect)
        
        # Then draw overlays
        if hasattr(self, 'overlay_map'):
            for y in range(viewport_start_y, viewport_end_y + 1):  # +1 to handle partial tiles
                for x in range(viewport_start_x, viewport_end_x + 1):  # +1 to handle partial tiles
                    # Skip if outside world bounds
                    if abs(x) > world_size or abs(y) > world_size:
                        continue
                        
                    screen_x = (x - viewport_start_x) * self.CELL_SIZE
                    screen_y = (y - viewport_start_y) * self.CELL_SIZE
                    
                    # Get overlay at this position
                    overlay_sprite = self.overlay_map.get((x, y))
                    if overlay_sprite and overlay_sprite.image:
                        # Scale overlay to match cell size if needed
                        current_size = overlay_sprite.image.get_size()
                        if current_size != (self.CELL_SIZE, self.CELL_SIZE):
                            scaled_image = pygame.transform.scale(overlay_sprite.image, 
                                                               (self.CELL_SIZE, self.CELL_SIZE))
                            # Calculate the portion of the tile that should be visible
                            visible_width = min(self.CELL_SIZE, viewport_width_pixels - screen_x)
                            visible_height = min(self.CELL_SIZE, viewport_height_pixels - screen_y)
                            if visible_width > 0 and visible_height > 0:
                                visible_rect = pygame.Rect(0, 0, visible_width, visible_height)
                                self.screen.blit(scaled_image, (screen_x, screen_y), visible_rect)
                        else:
                            visible_width = min(self.CELL_SIZE, viewport_width_pixels - screen_x)
                            visible_height = min(self.CELL_SIZE, viewport_height_pixels - screen_y)
                            if visible_width > 0 and visible_height > 0:
                                visible_rect = pygame.Rect(0, 0, visible_width, visible_height)
                                self.screen.blit(overlay_sprite.image, (screen_x, screen_y), visible_rect)
        
        # Draw player at center
        player_screen_x = (self.VIEWPORT_SIZE // 2) * self.CELL_SIZE
        player_screen_y = (self.VIEWPORT_SIZE // 2) * self.CELL_SIZE
        pygame.draw.rect(self.screen, self.player.color, 
                        (player_screen_x, player_screen_y, self.CELL_SIZE, self.CELL_SIZE))
        
        # Update the display
        pygame.display.flip()

    def get_path_to(self, target_x, target_y):
        """Get a path to the target position"""
        # For now, just return a direct path
        path = []
        current_x = self.player_x
        current_y = self.player_y
        
        while current_x != target_x or current_y != target_y:
            if current_x < target_x:
                current_x += 1
            elif current_x > target_x:
                current_x -= 1
            
            if current_y < target_y:
                current_y += 1
            elif current_y > target_y:
                current_y -= 1
            
            path.append((current_x, current_y))
        
        return path

    def move_player(self, new_x, new_y):
        """Move the player to a new position and return True if there's an encounter"""
        self.player_x = new_x
        self.player_y = new_y
        
        # Random encounter chance (20%)
        return random.random() < 0.2 

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