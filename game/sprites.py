import pygame
import os
import time
import zipfile
import shutil
import glob
import random
import math

class SpriteSheet:
    def __init__(self, image_path, sprite_width=32, sprite_height=32, grid_width=16, grid_height=20):
        """Load and manage a sprite sheet"""
        self.sheet = pygame.image.load(image_path).convert_alpha()
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sprites = {}
        self._load_sprites()
    
    def _load_sprites(self):
        """Load all sprites from the sheet into a dictionary"""
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                sprite_index = row * self.grid_width + col
                x = col * self.sprite_width
                y = row * self.sprite_height
                sprite = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                sprite.blit(self.sheet, (0, 0), (x, y, self.sprite_width, self.sprite_height))
                self.sprites[sprite_index] = sprite
    
    def get_sprite(self, index):
        """Get a sprite by its index in the sheet"""
        return self.sprites.get(index)
    
    def get_sprite_at(self, row, col):
        """Get a sprite by its grid position"""
        index = row * self.grid_width + col
        return self.get_sprite(index)

class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sprite_sheet, animation_frames, animation_speed=0.1, x=0, y=0):
        """Create an animated sprite from a sprite sheet"""
        super().__init__()
        self.sprite_sheet = sprite_sheet
        self.animation_frames = animation_frames
        self.current_frame = 0
        self.animation_speed = animation_speed
        self.last_update = time.time()
        self.image = sprite_sheet.get_sprite(animation_frames[0])
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.playing = True
        self.direction = 0  # 0: right, 1: left, 2: up, 3: down
    
    def update(self):
        """Update the animation frame"""
        if not self.playing:
            return
            
        now = time.time()
        if now - self.last_update > self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            self.image = self.sprite_sheet.get_sprite(self.animation_frames[self.current_frame])
            self.last_update = now
    
    def set_direction(self, direction):
        """Set the sprite's direction (0: right, 1: left, 2: up, 3: down)"""
        if direction != self.direction:
            self.direction = direction
            # Flip the sprite horizontally if facing left
            if direction == 1:
                self.image = pygame.transform.flip(self.image, True, False)
            else:
                self.image = self.sprite_sheet.get_sprite(self.animation_frames[self.current_frame])

class GameSprite(pygame.sprite.Sprite):
    def __init__(self, sprite_sheet=None, sprite_index=None, x=0, y=0):
        """Create a game sprite from a sprite sheet or individual sprite"""
        super().__init__()
        self.sprite_sheet = sprite_sheet
        self.sprite_index = sprite_index
        self.image = None
        self.rect = None
        self.name = None
        if sprite_sheet and sprite_index is not None:
            self.image = sprite_sheet.get_sprite(sprite_index)
            if self.image:
                self.rect = self.image.get_rect()
                self.rect.x = x
                self.rect.y = y
    
    def copy(self):
        """Create a deep copy of the sprite"""
        new_sprite = GameSprite()
        if self.image:
            new_sprite.image = self.image.copy()
        if self.rect:
            new_sprite.rect = self.rect.copy()
        new_sprite.name = self.name
        return new_sprite

class SingleSprite:
    """Class to handle individual PNG files from a directory"""
    def __init__(self, directory):
        self.directory = directory
        self.sprites = {}
        self.load_sprites()
    
    def load_sprites(self):
        """Load all PNG files from the directory"""
        try:
            for root, _, files in os.walk(self.directory):
                for file in files:
                    if file.endswith('.png'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.directory)
                        rel_path = rel_path.replace('\\', '/')  # Normalize path separators
                        sprite_path = os.path.join(root, file)
                        try:
                            sprite = pygame.image.load(sprite_path).convert_alpha()
                            self.sprites[rel_path] = sprite
                        except pygame.error as e:
                            print(f"Error loading sprite {rel_path}: {str(e)}")
        except Exception as e:
            print(f"Error walking directory {self.directory}: {str(e)}")
    
    def get_sprite(self, name):
        """Get a sprite by its name (relative path)"""
        # Normalize the path separator
        name = name.replace('\\', '/')
        return self.sprites.get(name)  # Simply return None if not found

class SpriteManager:
    def __init__(self):
        """Initialize the sprite manager"""
        self.initialized = False
        self.sprite_sheets = {}
        self.single_sprites = {}
        self.sprite_mappings = {}
        self.overlay_categories = ["Trees", "Rocks", "Bushes"]
        self._cached_base_tiles = {}  # Cache for base tiles
        self._cached_overlays = {}  # Cache for overlay sprites
    
    def initialize(self):
        """Initialize sprite sheets and single sprites after Pygame display is initialized"""
        if not self.initialized:
            self.load_sprite_sheets()
            self.load_single_sprites()
            self.initialized = True
    
    def load_sprite_sheets(self):
        """Load all sprite sheets from the assets directory"""
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        
        # Look for sprite sheets and individual sprites in zip files
        for root, _, files in os.walk(assets_dir):
            for file in files:
                if file.endswith('.zip'):
                    zip_path = os.path.join(root, file)
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            # Create a temporary directory for extraction
                            temp_dir = os.path.join(assets_dir, 'temp_extract')
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # Extract all PNG files
                            png_files = [f for f in zip_ref.namelist() if f.lower().endswith('.png')]
                            for png_file in png_files:
                                zip_ref.extract(png_file, temp_dir)
                                
                                # Determine if this is a sprite sheet or individual sprite
                                img_path = os.path.join(temp_dir, png_file)
                                try:
                                    img = pygame.image.load(img_path).convert_alpha()
                                    width, height = img.get_size()
                                    
                                    # If the image is large and seems to be a grid, treat as sprite sheet
                                    if width >= 256 and height >= 256 and ('sheet' in png_file.lower() or 'icon' in png_file.lower()):
                                        if 'character' in png_file.lower() or 'icon' in png_file.lower():
                                            shutil.copy(img_path, os.path.join(assets_dir, 'character_icons.png'))
                                        elif 'item' in png_file.lower():
                                            shutil.copy(img_path, os.path.join(assets_dir, 'items.png'))
                                    else:
                                        # Individual sprite - move to appropriate category directory
                                        target_dir = None
                                        if 'character' in png_file.lower():
                                            target_dir = os.path.join(assets_dir, 'characters_png')
                                        elif 'item' in png_file.lower():
                                            target_dir = os.path.join(assets_dir, 'items_png')
                                        elif any(terrain in png_file.lower() for terrain in ['tree', 'rock', 'grass', 'water', 'terrain']):
                                            target_dir = os.path.join(assets_dir, 'terrain_png')
                                        
                                        if target_dir:
                                            os.makedirs(target_dir, exist_ok=True)
                                            # Preserve subdirectory structure from zip
                                            rel_path = os.path.dirname(png_file)
                                            if rel_path:
                                                os.makedirs(os.path.join(target_dir, rel_path), exist_ok=True)
                                            shutil.copy(img_path, os.path.join(target_dir, png_file))
                                except Exception as e:
                                    print(f"Error loading {png_file}: {str(e)}")
                            
                            # Clean up temporary directory
                            shutil.rmtree(temp_dir, ignore_errors=True)
                    except Exception as e:
                        print(f"Error with zip file {zip_path}: {str(e)}")
        
        # Create placeholder sprite sheets if needed
        self._create_placeholder_sheets(assets_dir)
        
        # Define sprite sheet paths using existing files
        sprite_paths = {
            'characters': os.path.join(assets_dir, 'character_icons.png'),
            'items': os.path.join(assets_dir, '#2 - Transparent Icons & Drop Shadow.png'),
            'terrain': os.path.join(assets_dir, 'Background 2a.png')  # Using this for terrain tiles
        }
        
        # Load all sprite sheets with appropriate grid sizes
        for sheet_name, path in sprite_paths.items():
            if os.path.exists(path):
                if sheet_name == 'characters':
                    self.sprite_sheets[sheet_name] = SpriteSheet(path, sprite_width=32, sprite_height=32,
                                                               grid_width=16, grid_height=20)
                elif sheet_name == 'items':
                    self.sprite_sheets[sheet_name] = SpriteSheet(path, sprite_width=32, sprite_height=32,
                                                               grid_width=16, grid_height=20)
                else:  # terrain
                    self.sprite_sheets[sheet_name] = SpriteSheet(path, sprite_width=64, sprite_height=64,
                                                               grid_width=8, grid_height=8)
            else:
                print(f"Missing sprite sheet: {path}")
    
    def _create_placeholder_sheets(self, assets_dir):
        """Create placeholder sprite sheets if they don't exist"""
        # Create character sprite sheet
        character_path = os.path.join(assets_dir, 'character_icons.png')
        if not os.path.exists(character_path):
            print("Creating placeholder character sheet...")
            # Create a 16x20 grid of sprites (32x32 pixels each)
            sheet = pygame.Surface((32 * 16, 32 * 20), pygame.SRCALPHA)
            
            # Character types and their base colors
            character_types = {
                'player': (0, 255, 255),    # Cyan
                'goblin': (0, 255, 0),      # Green
                'orc': (255, 165, 0),       # Orange
                'troll': (128, 0, 128),     # Purple
                'dragon': (255, 0, 0)       # Red
            }
            
            # Create sprites for each character type
            for row, (char_type, base_color) in enumerate(character_types.items()):
                # Each character type gets 4 rows of sprites
                base_y = row * 4 * 32
                
                # Create variations for different states (idle, walk, attack, hurt)
                states = ['idle', 'walk', 'attack', 'hurt']
                for state_row, state in enumerate(states):
                    y = base_y + state_row * 32
                    for col in range(16):
                        x = col * 32
                        # Slightly vary the color for each frame
                        color = (
                            min(255, base_color[0] + col * 10),
                            min(255, base_color[1] + col * 10),
                            min(255, base_color[2] + col * 10)
                        )
                        # Draw the sprite
                        pygame.draw.rect(sheet, color, (x, y, 32, 32))
                        pygame.draw.rect(sheet, (255, 255, 255), (x, y, 32, 32), 1)
                        # Add frame number
                        font = pygame.font.Font(None, 20)
                        text = font.render(f"{col}", True, (255, 255, 255))
                        sheet.blit(text, (x + 12, y + 12))
            
            pygame.image.save(sheet, character_path)
            print(f"Created placeholder character sheet at: {character_path}")
        
        # Create item sprite sheet if needed
        item_path = os.path.join(assets_dir, 'items.png')
        if not os.path.exists(item_path):
            print("Creating placeholder item sheet...")
            sheet = pygame.Surface((32 * 16, 32 * 20), pygame.SRCALPHA)
            for row in range(20):
                for col in range(16):
                    x = col * 32
                    y = row * 32
                    color = (
                        (row * 10) % 255,
                        (col * 10) % 255,
                        ((row + col) * 10) % 255
                    )
                    pygame.draw.rect(sheet, color, (x, y, 32, 32))
                    pygame.draw.rect(sheet, (255, 255, 255), (x, y, 32, 32), 1)
            pygame.image.save(sheet, item_path)
            print(f"Created placeholder item sheet at: {item_path}")
    
    def load_single_sprites(self):
        """Load individual PNG files from the assets directory"""
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        
        # Create terrain_png directory if it doesn't exist
        terrain_dir = os.path.join(assets_dir, 'terrain_png')
        if not os.path.exists(terrain_dir):
            os.makedirs(terrain_dir, exist_ok=True)
        
        # Create Tiles directory if it doesn't exist
        tiles_dir = os.path.join(terrain_dir, 'Tiles')
        if not os.path.exists(tiles_dir):
            os.makedirs(tiles_dir, exist_ok=True)
        
        # Define base terrain tiles with textures
        terrain_tiles = {
            'grass': {
                'base': (34, 139, 34),  # Forest green
                'details': [
                    {'color': (50, 205, 50), 'count': 15,  # Grass blades
                     'draw': lambda s, x, y: pygame.draw.line(s, (50, 205, 50), (x, y+12), (x+random.randint(-4, 4), y), 2)},
                    {'color': (144, 238, 144), 'count': 8,  # Highlights
                     'draw': lambda s, x, y: pygame.draw.circle(s, (144, 238, 144), (x, y), 1)}
                ]
            },
            'dirt': {
                'base': (139, 69, 19),  # Saddle brown
                'details': [
                    {'color': (101, 67, 33), 'count': 20,  # Dark spots
                     'draw': lambda s, x, y: pygame.draw.circle(s, (101, 67, 33), (x, y), random.randint(1, 3))},
                    {'color': (160, 82, 45), 'count': 15,  # Light spots
                     'draw': lambda s, x, y: pygame.draw.circle(s, (160, 82, 45), (x, y), 1)}
                ]
            },
            'sand': {
                'base': (238, 214, 175),  # Tan
                'details': [
                    {'color': (210, 180, 140), 'count': 25,  # Dark speckles
                     'draw': lambda s, x, y: pygame.draw.circle(s, (210, 180, 140), (x, y), 1)},
                    {'color': (245, 222, 179), 'count': 20,  # Light speckles
                     'draw': lambda s, x, y: pygame.draw.circle(s, (245, 222, 179), (x, y), 1)}
                ]
            },
            'water': {
                'base': (30, 144, 255),  # Dodger blue
                'details': [
                    {'color': (135, 206, 235), 'count': 4,  # Wave lines
                     'draw': lambda s, x, y: pygame.draw.arc(s, (135, 206, 235), (x, y, 16, 8), 0, 3.14, 2)},
                    {'color': (173, 216, 230), 'count': 8,  # Highlights
                     'draw': lambda s, x, y: pygame.draw.circle(s, (173, 216, 230), (x, y), 1)}
                ]
            }
        }
        
        # Create base terrain tiles
        for tile_name, tile_data in terrain_tiles.items():
            sprite_path = os.path.join(tiles_dir, f"{tile_name}.png")
            try:
                # Always recreate the tiles to ensure they have textures
                surface = pygame.Surface((32, 32), pygame.SRCALPHA)
                
                # Draw base color (fill entire surface)
                pygame.draw.rect(surface, tile_data['base'], (0, 0, 32, 32))
                
                # Add texture details
                for detail in tile_data['details']:
                    for _ in range(detail['count']):
                        x = random.randint(1, 31)
                        y = random.randint(1, 31)
                        detail['draw'](surface, x, y)
                
                # Save the textured tile without border
                pygame.image.save(surface, sprite_path)
            except Exception as e:
                print(f"Error creating tile {tile_name}: {str(e)}")
        
        # Look for directories containing individual sprites
        for category in ['characters_png', 'items_png', 'terrain_png']:
            category_dir = os.path.join(assets_dir, category)
            if os.path.exists(category_dir) and os.path.isdir(category_dir):
                try:
                    self.single_sprites[category] = SingleSprite(category_dir)
                except Exception as e:
                    print(f"Error loading category {category}: {str(e)}")
    
    def get_sprite(self, sheet_name, sprite_index, x=0, y=0):
        """Create a game sprite from a specific sheet and index"""
        if not self.initialized:
            self.initialize()
        if sheet_name in self.sprite_sheets:
            sheet = self.sprite_sheets[sheet_name]
            sprite = sheet.get_sprite(sprite_index)
            if sprite:
                game_sprite = GameSprite(sheet, sprite_index, x, y)
                game_sprite.image = sprite
                game_sprite.rect = sprite.get_rect()
                game_sprite.rect.x = x
                game_sprite.rect.y = y
                return game_sprite
        return None
    
    def get_animated_sprite(self, sheet_name, character_type, animation_type, x=0, y=0):
        """Create an animated sprite for a character"""
        if not self.initialized:
            self.initialize()
        if (sheet_name in self.sprite_sheets and 
            character_type in self.sprite_mappings[sheet_name] and 
            animation_type in self.sprite_mappings[sheet_name][character_type]):
            
            frames = self.sprite_mappings[sheet_name][character_type][animation_type]
            return AnimatedSprite(self.sprite_sheets[sheet_name], frames, x=x, y=y)
        return None
    
    def get_item_sprite(self, item_type, item_name, x=0, y=0):
        """Create a sprite for an item"""
        if not self.initialized:
            self.initialize()
        if item_type in self.sprite_mappings['items']:
            sprite_index = self.sprite_mappings['items'][item_type].get(item_name)
            if sprite_index is not None:
                return self.get_sprite('items', sprite_index, x, y)
        return None
    
    def get_base_tile(self, tile_name, x=0, y=0):
        """Get a base terrain tile by name"""
        if not self.initialized:
            self.initialize()
        
        # Check cache first
        if tile_name in self._cached_base_tiles:
            sprite = self._cached_base_tiles[tile_name].copy()
            sprite.rect.x = x
            sprite.rect.y = y
            return sprite
        
        # Try to get the tile from the Tiles directory
        if 'terrain_png' in self.single_sprites:
            sprite_sheet = self.single_sprites['terrain_png']
            surface = None
            
            # Try different path variations
            variations = [
                tile_name,
                f"{tile_name}.png",
                f"Tiles/{tile_name}",
                f"Tiles/{tile_name}.png",
            ]
            
            # Try each variation
            for path in variations:
                surface = sprite_sheet.get_sprite(path)
                if surface:
                    break
            
            if not surface:
                # Create a textured tile using the unified system
                sprite = self._create_textured_sprite('terrain', tile_name)
            else:
                # Create a GameSprite from the surface
                sprite = GameSprite()
                sprite.image = surface
                sprite.rect = surface.get_rect()
                sprite.name = tile_name
            
            if sprite:
                sprite.rect.x = x
                sprite.rect.y = y
                # Cache the sprite
                self._cached_base_tiles[tile_name] = sprite.copy()
                return sprite  # Return the sprite
            else:
                print(f"Failed to create tile: {tile_name}")  # Debug print
        else:
            print("terrain_png category not found!")  # Debug print
        return None
    
    def _create_textured_sprite(self, sprite_type, sprite_name):
        """Create a textured sprite using the unified texture system"""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Define all textures
        textures = {
            # Tree textures
            'pine': {
                'base': (101, 67, 33),  # Dark brown trunk
                'details': [
                    {'color': (1, 68, 33), 'count': 3,  # Tree triangles
                     'draw': lambda s, x, y: [
                         pygame.draw.polygon(s, (1, 68, 33), [(16, 2), (8, 12), (24, 12)]),  # Top
                         pygame.draw.polygon(s, (34, 139, 34), [(15, 1), (7, 11), (23, 11)]),  # Top highlight
                         pygame.draw.polygon(s, (1, 68, 33), [(16, 8), (6, 20), (26, 20)]),  # Middle
                         pygame.draw.polygon(s, (34, 139, 34), [(15, 7), (5, 19), (25, 19)]),  # Middle highlight
                         pygame.draw.polygon(s, (1, 68, 33), [(16, 14), (4, 28), (28, 28)]),  # Bottom
                         pygame.draw.polygon(s, (34, 139, 34), [(15, 13), (3, 27), (27, 27)])  # Bottom highlight
                     ]},
                    {'color': (101, 67, 33), 'count': 1,  # Trunk
                     'draw': lambda s, x, y: pygame.draw.rect(s, (101, 67, 33), (14, 16, 4, 16))}
                ]
            },
            'oak': {
                'base': (101, 67, 33),  # Dark brown trunk
                'details': [
                    {'color': (1, 68, 33), 'count': 5,  # Foliage circles
                     'draw': lambda s, x, y: [
                         pygame.draw.circle(s, (1, 68, 33), (16 + dx, 12 + dy), 8) for dx, dy in [(0,0), (-2,-2), (2,-2), (-2,2), (2,2)]
                     ]},
                    {'color': (34, 139, 34), 'count': 5,  # Foliage highlights
                     'draw': lambda s, x, y: [
                         pygame.draw.circle(s, (34, 139, 34), (16 + dx - 1, 12 + dy - 1), 7) for dx, dy in [(0,0), (-2,-2), (2,-2), (-2,2), (2,2)]
                     ]},
                    {'color': (101, 67, 33), 'count': 1,  # Trunk
                     'draw': lambda s, x, y: pygame.draw.rect(s, (101, 67, 33), (14, 16, 4, 16))}
                ]
            },
            'dead': {
                'base': (101, 67, 33),  # Dark brown trunk
                'details': [
                    {'color': (101, 67, 33), 'count': 1,  # Main trunk
                     'draw': lambda s, x, y: pygame.draw.rect(s, (101, 67, 33), (14, 0, 4, 32))},
                    {'color': (139, 69, 19), 'count': 1,  # Trunk highlight
                     'draw': lambda s, x, y: pygame.draw.rect(s, (139, 69, 19), (15, 0, 2, 32))},
                    {'color': (101, 67, 33), 'count': 3,  # Branches
                     'draw': lambda s, x, y: [
                         pygame.draw.line(s, (101, 67, 33), (branch[0], branch[1]), (branch[2], branch[3]), 3) for branch in [(8,8,20,4), (20,12,8,16), (24,20,12,24)]
                     ]},
                    {'color': (139, 69, 19), 'count': 3,  # Branch highlights
                     'draw': lambda s, x, y: [
                         pygame.draw.line(s, (139, 69, 19), (branch[0], branch[1]), (branch[2], branch[3]), 1) for branch in [(8,8,20,4), (20,12,8,16), (24,20,12,24)]
                     ]}
                ]
            },
            # Rock textures
            'boulder': {
                'base': (128, 128, 128),  # Base gray
                'details': [
                    {'color': (128, 128, 128), 'count': 1,  # Main shape
                     'draw': lambda s, x, y: pygame.draw.ellipse(s, (128, 128, 128), (4, 8, 24, 20))},
                    {'color': (169, 169, 169), 'count': 1,  # Highlight
                     'draw': lambda s, x, y: pygame.draw.ellipse(s, (169, 169, 169), (6, 10, 20, 16))},
                    {'color': (105, 105, 105), 'count': 1,  # Shadow
                     'draw': lambda s, x, y: pygame.draw.ellipse(s, (105, 105, 105), (8, 12, 16, 12))},
                    {'color': (90, 90, 90), 'count': 5,  # Texture spots
                     'draw': lambda s, x, y: pygame.draw.circle(s, (90, 90, 90), (random.randint(8, 24), random.randint(12, 24)), 1)}
                ]
            },
            'stone': {
                'base': (128, 128, 128),  # Base gray
                'details': [
                    {'color': (128, 128, 128), 'count': 1,  # Base shape
                     'draw': lambda s, x, y: pygame.draw.polygon(s, (128, 128, 128), [(8, 16), (16, 8), (24, 16), (24, 24), (16, 28), (8, 24)])},
                    {'color': (169, 169, 169), 'count': 1,  # Highlights
                     'draw': lambda s, x, y: pygame.draw.polygon(s, (169, 169, 169), [(7, 15), (15, 7), (23, 15)])},
                    {'color': (90, 90, 90), 'count': 1,  # Shadows
                     'draw': lambda s, x, y: pygame.draw.polygon(s, (90, 90, 90), [(25, 25), (17, 29), (9, 25)])}
                ]
            },
            'crystal': {
                'base': (200, 200, 255),  # Base crystal color
                'details': [
                    {'color': (200, 200, 255), 'count': 1,  # Base shape
                     'draw': lambda s, x, y: pygame.draw.polygon(s, (200, 200, 255), [(16, 4), (24, 12), (24, 24), (16, 28), (8, 24), (8, 12)])},
                    {'color': (220, 220, 255), 'count': 1,  # Inner glow
                     'draw': lambda s, x, y: pygame.draw.polygon(s, (220, 220, 255), [(p[0]*0.8 + 16*0.2, p[1]*0.8 + 16*0.2) for p in [(16, 4), (24, 12), (24, 24), (16, 28), (8, 24), (8, 12)]])},
                    {'color': (255, 255, 255), 'count': 1,  # Highlight
                     'draw': lambda s, x, y: pygame.draw.line(s, (255, 255, 255), (16, 4), (24, 12), 2)}
                ]
            },
            # Bush textures
            'small': {
                'base': (0, 100, 0),  # Dark green
                'details': [
                    {'color': (0, 100, 0), 'count': 4,  # Base circles
                     'draw': lambda s, x, y: [pygame.draw.circle(s, (0, 100, 0), (pos[0], pos[1]), r) for pos, r in [(16, 16, 12), (12, 18, 10), (20, 18, 10), (16, 20, 10)]]},
                    {'color': (34, 139, 34), 'count': 4,  # Highlight circles
                     'draw': lambda s, x, y: [pygame.draw.circle(s, (34, 139, 34), (pos[0]-1, pos[1]-1), r-1) for pos, r in [(16, 16, 12), (12, 18, 10), (20, 18, 10), (16, 20, 10)]]}
                ]
            },
            'berry': {
                'base': (0, 120, 0),  # Dark green
                'details': [
                    {'color': (0, 120, 0), 'count': 4,  # Base circles
                     'draw': lambda s, x, y: [pygame.draw.circle(s, (0, 120, 0), (pos[0], pos[1]), r) for pos, r in [(16, 16, 12), (12, 18, 10), (20, 18, 10), (16, 20, 10)]]},
                    {'color': (34, 139, 34), 'count': 4,  # Highlight circles
                     'draw': lambda s, x, y: [pygame.draw.circle(s, (34, 139, 34), (pos[0]-1, pos[1]-1), r-1) for pos, r in [(16, 16, 12), (12, 18, 10), (20, 18, 10), (16, 20, 10)]]},
                    {'color': (139, 0, 0), 'count': 5,  # Berries
                     'draw': lambda s, x, y: [
                         pygame.draw.circle(s, (139, 0, 0), (random.randint(8, 24), random.randint(8, 24)), 2) and  # Dark red base
                         pygame.draw.circle(s, (255, 0, 0), (x-1, y-1), 1)  # Bright red highlight
                         for _ in range(5)
                     ]}
                ]
            },
            'flower': {
                'base': (0, 120, 0),  # Dark green
                'details': [
                    {'color': (0, 120, 0), 'count': 4,  # Base circles
                     'draw': lambda s, x, y: [pygame.draw.circle(s, (0, 120, 0), (pos[0], pos[1]), r) for pos, r in [(16, 16, 12), (12, 18, 10), (20, 18, 10), (16, 20, 10)]]},
                    {'color': (34, 139, 34), 'count': 4,  # Highlight circles
                     'draw': lambda s, x, y: [pygame.draw.circle(s, (34, 139, 34), (pos[0]-1, pos[1]-1), r-1) for pos, r in [(16, 16, 12), (12, 18, 10), (20, 18, 10), (16, 20, 10)]]},
                    {'color': (255, 255, 0), 'count': 4,  # Flowers
                     'draw': lambda s, x, y: [
                         (pygame.draw.circle(s, (255, 255, 0), (x, y), 2),  # Yellow center
                          [pygame.draw.circle(s, (255, 192, 203),  # Pink petals
                                           (x + int(3 * math.cos(math.radians(i * 90))),
                                            y + int(3 * math.sin(math.radians(i * 90)))), 2)
                           for i in range(4)])
                         for x, y in [(random.randint(8, 24), random.randint(8, 24)) for _ in range(4)]
                     ]}
                ]
            }
        }
        
        # Map sprite types to their texture names
        type_mapping = {
            'tree': sprite_name,  # Use the sprite name directly (pine, oak, dead)
            'rock': sprite_name,  # Use the sprite name directly (boulder, stone, crystal)
            'bush': sprite_name,  # Use the sprite name directly (small, berry, flower)
            'terrain': sprite_name  # For base terrain tiles
        }
        
        # Get the actual texture name to use
        texture_name = type_mapping.get(sprite_type, sprite_name)
        
        # Get the texture data
        texture_data = textures.get(texture_name)
        if not texture_data:
            return None
            
        # Draw base color if specified
        if 'base' in texture_data:
            pygame.draw.rect(surface, texture_data['base'], (0, 0, 32, 32))
            
        # Add all details
        if 'details' in texture_data:
            for detail in texture_data['details']:
                for _ in range(detail['count']):
                    x = random.randint(1, 31)
                    y = random.randint(1, 31)
                    detail['draw'](surface, x, y)
        
        # Create a GameSprite with the textured surface
        game_sprite = GameSprite()
        game_sprite.image = surface
        game_sprite.rect = surface.get_rect()
        game_sprite.name = sprite_name
        
        return game_sprite
    
    def get_overlay_sprite(self, category, sprite_name, x=0, y=0):
        """Get an overlay sprite (trees, rocks, etc.)"""
        if not self.initialized:
            self.initialize()
        
        # Create cache key
        cache_key = f"{category}/{sprite_name}"
        
        # Check cache first
        if cache_key in self._cached_overlays:
            sprite = self._cached_overlays[cache_key].copy()
            sprite.rect.x = x
            sprite.rect.y = y
            return sprite
        
        # Try to get the sprite from the terrain_png category
        if 'terrain_png' in self.single_sprites:
            sprite_sheet = self.single_sprites['terrain_png']
            surface = None
            
            # Try different path variations
            variations = [
                f"{category}/{sprite_name}",
                f"{category}/{sprite_name}.png",
                f"{category.lower()}/{sprite_name}",
                f"{category.lower()}/{sprite_name}.png"
            ]
            
            # Try each variation
            for path in variations:
                surface = sprite_sheet.get_sprite(path)
                if surface:
                    break
            
            if not surface:
                # Map category names to texture types
                category_map = {
                    "Trees": "tree",
                    "Rocks": "rock",
                    "Bushes": "bush"
                }
                # Get the base category type
                base_category = category_map.get(category, category.lower())
                # Create a textured sprite using the unified system
                sprite = self._create_textured_sprite(base_category, sprite_name)
            else:
                # Create a GameSprite from the surface
                sprite = GameSprite()
                sprite.image = surface
                sprite.rect = surface.get_rect()
                sprite.name = sprite_name
            
            if sprite:
                sprite.rect.x = x
                sprite.rect.y = y
                # Cache the sprite
                self._cached_overlays[cache_key] = sprite.copy()
                return sprite
        
        return None
    
    def get_available_tiles(self):
        """Get a list of all available base terrain tiles"""
        if not self.initialized:
            self.initialize()
        
        tiles = []
        
        # First add the base terrain tiles
        base_tiles = ['grass', 'dirt', 'sand', 'water']
        for tile_name in base_tiles:
            sprite = self.get_base_tile(tile_name)
            if sprite:
                tiles.append(sprite)
        
        # Then add any map tiles
        if 'terrain_png' in self.single_sprites:
            for sprite_name in self.single_sprites['terrain_png'].sprites:
                if sprite_name.startswith('Tiles/Map_tile_'):
                    # Remove .png extension if present
                    tile_name = sprite_name[:-4] if sprite_name.endswith('.png') else sprite_name
                    sprite = self.get_base_tile(tile_name)
                    if sprite:
                        tiles.append(sprite)
        
        return tiles

    def get_available_overlays(self):
        """Get a dictionary of available overlay sprites by category"""
        if not self.initialized:
            self.initialize()
        
        overlays = {}
        categories = {
            "Trees": ["pine", "oak", "dead"],
            "Rocks": ["boulder", "stone", "crystal"],
            "Bushes": ["small", "berry", "flower"]
        }
        
        for category, sprites in categories.items():
            category_sprites = []
            for sprite_name in sprites:
                sprite = self.get_overlay_sprite(category, sprite_name)
                if sprite:
                    category_sprites.append(sprite)
            if category_sprites:
                overlays[category] = category_sprites
        
        return overlays
    
    def get_terrain_sprite(self, terrain_type, x=0, y=0):
        """Create a sprite for terrain (base tile or overlay)"""
        if not self.initialized:
            self.initialize()
        
        # Check if this is a base tile (grass, dirt, sand, water)
        if terrain_type in ['grass', 'dirt', 'sand', 'water']:
            sprite = self.get_base_tile(terrain_type, x, y)
            if sprite:
                return sprite
        
        # Check if this is a map tile
        if terrain_type.startswith('Map_tile_'):
            sprite = self.get_base_tile(terrain_type, x, y)
            if sprite:
                return sprite
        
        # Then check each overlay category
        for category in self.overlay_categories:
            sprite = self.get_overlay_sprite(category, terrain_type, x, y)
            if sprite:
                return sprite
        
        # If no sprite found, return grass as default
        print(f"No sprite found for {terrain_type}, using grass as default")
        return self.get_base_tile('grass', x, y)

    def get_single_sprite(self, category, sprite_name, x=0, y=0):
        """Create a game sprite from an individual PNG file"""
        if not self.initialized:
            self.initialize()
        
        print(f"Getting single sprite: {category}/{sprite_name}")  # Debug print
        
        category_key = f"{category}_png"
        if category_key in self.single_sprites:
            sprite_sheet = self.single_sprites[category_key]
            sprite = sprite_sheet.get_sprite(sprite_name)
            if sprite:
                print(f"Found sprite: {sprite_name}")  # Debug print
                game_sprite = GameSprite(None, None, x, y)
                game_sprite.image = sprite
                game_sprite.rect = sprite.get_rect()
                game_sprite.rect.x = x
                game_sprite.rect.y = y
                game_sprite.name = sprite_name  # Add name for debugging
                return game_sprite
            else:
                print(f"Sprite not found: {sprite_name}")  # Debug print
                print(f"Available sprites: {sorted(sprite_sheet.sprites.keys())}")  # Debug print
        else:
            print(f"Category not found: {category_key}")  # Debug print
            print(f"Available categories: {sorted(self.single_sprites.keys())}")  # Debug print
        return None

# Create a global sprite manager instance
sprite_manager = SpriteManager() 