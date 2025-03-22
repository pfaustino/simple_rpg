import pygame
import time
import random
import sys
import json
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    STATE_MENU, STATE_PLAYING, STATE_COMBAT,
    STATE_INVENTORY, STATE_SAVE, STATE_LOAD,
    STATE_QUIT, SOUND_BUTTON_CLICK, SOUND_LEVEL_UP,
    SOUND_ITEM_PICKUP, SOUND_COMBAT_START, SOUND_COMBAT_END,
    SOUND_ATTACK, SOUND_HIT, SOUND_MISS, SOUND_DEATH,
    SOUND_VICTORY, WHITE, BLACK, GREEN, WINDOW_TITLE, YELLOW
)
from utils.helpers import play_sound, save_game, load_game, load_sprite_mappings, play_wave_sound
from entities.character import Character
from game.combat import CombatSystem
from entities.items import Item, Inventory
from ui.console import MessageConsole
from ui.systemmenu import SystemMenu
from game.world import World
from game.sprites import sprite_manager
from ui.bar import Bar

class Game:
    def __init__(self):
        """Initialize the game"""
        # Initialize Pygame and set up display first
        pygame.init()
        pygame.mixer.init()  # Initialize the sound mixer
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simple RPG")
        
        # Initialize window dimensions
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        
        # Initialize font
        self.font = pygame.font.Font(None, 24)
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
        # Initialize message console
        self.message_console = MessageConsole()
        
        # Initialize system menu
        self.system_menu = SystemMenu(self.width, self.height)
        
        print("Game initialized")
        
        # Game state
        self.running = True
        self.in_combat = False
        self.current_enemy = None
        self.sprite_debug_active = False
        self.show_inventory = False
        self.unequip_mode = False  # Initialize unequip_mode
               
        # Debug view flags
        self.show_debug = False
        self.show_sprite_debug = False
        
        # Initialize sprite manager (after display is set up)
        sprite_manager.initialize()
        
        # Load sprite mappings if they exist
        load_sprite_mappings()
        
        # Load item databases
        self.load_item_databases()
        
        # Initialize spell system
        from game.spells import SpellSystem
        self.spell_system = SpellSystem(self)
        
        # Try to load saved game
        save_data = load_game()
        if save_data:
            # Create player with saved stats
            self.player = Character(
                save_data["player"]["name"],
                health=save_data["player"]["max_health"],
                attack=save_data["player"]["attack"],
                character_type='player'
            )
            # Restore player stats
            self.player.health = save_data["player"]["health"]
            self.player.level = save_data["player"]["level"]
            self.player.exp = save_data["player"]["exp"]
            self.player.exp_to_next_level = save_data["player"].get("exp_to_next_level", 100)
            self.player.max_health = save_data["player"]["max_health"]
            self.player.attack = save_data["player"]["attack"]
            self.player.mp = save_data["player"].get("mp", 50)  # Restore MP
            self.player.max_mp = save_data["player"].get("max_mp", 50)  # Restore max MP
            # Restore kill stats
            self.player.kills = save_data["player"].get("kills", {})
            # Restore inventory if it exists
            if "inventory" in save_data["player"]:
                self.player.inventory = Inventory.from_dict(save_data["player"]["inventory"])
            # Restore equipment if it exists
            if "equipment" in save_data["player"]:
                for slot, item_data in save_data["player"]["equipment"].items():
                    if item_data:
                        self.player.equipment[slot] = Item.from_dict(item_data)
        else:
            # Create new player character
            self.player = self.create_player()
        
        # Initialize world with player
        self.world = World(self.player)
        self.world.game = self  # Set the game reference
        self.world.show_debug = self.show_debug
        self.world.show_sprite_debug = self.show_sprite_debug
        self.world.screen = self.screen  # Share the screen surface
        
        # Restore player position if save exists
        if save_data and "world" in save_data:
            self.world.player_x = save_data["world"].get("player_x", 0)
            self.world.player_y = save_data["world"].get("player_y", 0)
        
        # Combat options
        self.combat_options = [
            "Attack",
            "Strong Attack",
            "Heal",
            "Flee"
        ]
        self.selected_option = 0
        
        # Enemy types
        self.enemies = ["Goblin", "Orc", "Troll", "Dragon"]
        
        print("Game initialization complete")
        
        # Load monster database
        self.monster_database = self.load_monster_database()
        
        # Initialize combat system
        self.combat_system = CombatSystem(self)
        
        self.bar_renderer = Bar()
        
    def load_monster_database(self):
        """Load the monster database from JSON file"""
        try:
            with open('data/monsters.json', 'r') as f:
                data = json.load(f)
                return data['monsters']
        except Exception as e:
            print(f"Error loading monster database: {e}")
            return []

    def create_enemy(self):
        """Create a random enemy from the monster database"""
        # Get player's current level (default to 1 if not set)
        player_level = getattr(self.player, 'level', 1)
        
        # Filter monsters that are appropriate for the player's level
        appropriate_monsters = [
            monster for monster in self.monster_database
            if monster['level_range'][0] <= player_level <= monster['level_range'][1]
        ]
        
        if not appropriate_monsters:
            # If no appropriate monsters found, use the closest level range
            appropriate_monsters = sorted(
                self.monster_database,
                key=lambda m: abs(m['level_range'][0] - player_level)
            )[:5]  # Take top 5 closest level ranges
        
        # Select a random monster from the appropriate ones
        monster_data = random.choice(appropriate_monsters)
        
        # Create the enemy character with the monster's stats
        enemy = Character(
            monster_data['name'],
            health=monster_data['base_stats']['hp'],
            attack=monster_data['base_stats']['attack'],
            defense=monster_data['base_stats']['defense'],
            speed=monster_data['base_stats']['speed'],
            mp=monster_data['base_stats']['mp'],
            character_type='enemy'
        )
        
        # Store the monster data for loot generation
        enemy.monster_data = monster_data
        
        # Position the enemy one tile away from the player
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        enemy.x = self.world.player_x + direction[0]
        enemy.y = self.world.player_y + direction[1]
        
        return enemy

    def handle_inventory_input(self, event):
        """Handle input while inventory is open"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:  # Close inventory
                self.show_inventory = False
            elif event.key == pygame.K_u:  # Unequip menu
                self.message_console.add_message("Press 1 for weapon, 2 for armor, 3 for accessory to unequip")
                self.unequip_mode = True
            elif self.unequip_mode and event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:  # Unequip items
                if event.key == pygame.K_1:
                    slot = "weapon"
                elif event.key == pygame.K_2:
                    slot = "armor"
                else:
                    slot = "accessory"
                
                # Check if there's an item equipped in the slot
                if self.player.equipment[slot]:
                    # Try to unequip the item
                    unequipped_item = self.player.unequip_item(slot)
                    if unequipped_item:
                        if self.player.inventory.add_item(unequipped_item):
                            self.message_console.add_message(f"Unequipped {unequipped_item.name}")
                            play_sound(SOUND_ITEM_PICKUP)
                        else:
                            # If inventory is full, re-equip the item
                            self.player.equipment[slot] = unequipped_item
                            self.message_console.add_message("Inventory full! Cannot unequip.")
                else:
                    self.message_console.add_message(f"No {slot} equipped")
                self.unequip_mode = False  # Exit unequip mode after attempt
            
            elif pygame.K_1 <= event.key <= pygame.K_9:  # Equip/use items (when not in unequip mode)
                if not hasattr(self, 'unequip_mode') or not self.unequip_mode:
                    item_index = event.key - pygame.K_1
                    if item_index < len(self.player.inventory.items):
                        item = self.player.inventory.items[item_index]
                        
                        # Determine item type and handle accordingly
                        if item.item_type == "weapon":
                            # Try to equip the weapon
                            old_item = self.player.equip_item(item)
                            if old_item is not None:
                                # Successfully equipped, remove from inventory
                                self.player.inventory.remove_item(item)
                                # Add the old item to inventory if there was one
                                if old_item:
                                    self.player.inventory.add_item(old_item)
                                self.message_console.add_message(f"Equipped {item.name}")
                                play_sound(SOUND_ITEM_PICKUP)
                            else:
                                self.message_console.add_message(f"Cannot equip {item.name}")
                        elif item.item_type == "armor":
                            # Try to equip the armor
                            old_item = self.player.equip_item(item)
                            if old_item is not None:
                                # Successfully equipped, remove from inventory
                                self.player.inventory.remove_item(item)
                                # Add the old item to inventory if there was one
                                if old_item:
                                    self.player.inventory.add_item(old_item)
                                self.message_console.add_message(f"Equipped {item.name}")
                                play_sound(SOUND_ITEM_PICKUP)
                            else:
                                self.message_console.add_message(f"Cannot equip {item.name}")
                        elif item.item_type == "accessory":
                            # Try to equip the accessory
                            old_item = self.player.equip_item(item)
                            if old_item is not None:
                                # Successfully equipped, remove from inventory
                                self.player.inventory.remove_item(item)
                                # Add the old item to inventory if there was one
                                if old_item:
                                    self.player.inventory.add_item(old_item)
                                self.message_console.add_message(f"Equipped {item.name}")
                                play_sound(SOUND_ITEM_PICKUP)
                            else:
                                self.message_console.add_message(f"Cannot equip {item.name}")
                        else:
                            # For non-equipment items (potions, food, etc.)
                            if self.player.use_item(item):
                                self.player.inventory.remove_item(item)
                                self.message_console.add_message(f"Used {item.name}")
                                play_sound(SOUND_ITEM_PICKUP)
                            else:
                                self.message_console.add_message(f"Cannot use {item.name} right now")

    def animate_movement(self, start_x, start_y, end_x, end_y):
        """Animate movement from start position to end position"""
        ANIMATION_SPEED = 4  # pixels per frame
        
        # Convert tile positions to pixel positions
        start_pixel_x = start_x * self.world.CELL_SIZE
        start_pixel_y = start_y * self.world.CELL_SIZE
        end_pixel_x = end_x * self.world.CELL_SIZE
        end_pixel_y = end_y * self.world.CELL_SIZE
        
        # Current pixel position
        current_pixel_x = start_pixel_x
        current_pixel_y = start_pixel_y
        
        # Calculate direction and distance
        dx = end_pixel_x - start_pixel_x
        dy = end_pixel_y - start_pixel_y
        distance = max(abs(dx), abs(dy))
        
        if distance == 0:
            return
            
        # Normalize movement vector
        move_x = (dx / distance) * ANIMATION_SPEED
        move_y = (dy / distance) * ANIMATION_SPEED
        
        # Animation loop
        clock = pygame.time.Clock()
        while abs(current_pixel_x - end_pixel_x) > ANIMATION_SPEED or abs(current_pixel_y - end_pixel_y) > ANIMATION_SPEED:
            # Update position
            if abs(current_pixel_x - end_pixel_x) > ANIMATION_SPEED:
                current_pixel_x += move_x
            else:
                current_pixel_x = end_pixel_x
                
            if abs(current_pixel_y - end_pixel_y) > ANIMATION_SPEED:
                current_pixel_y += move_y
            else:
                current_pixel_y = end_pixel_y
            
            # Update world display
            self.world.display_viewport(self.world.screen, end_x, end_y)
            
            # Calculate screen position relative to viewport
            screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE + (current_pixel_x - end_pixel_x)
            screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE + (current_pixel_y - end_pixel_y)
            
            # Draw player at current position
            self.player.draw(self.world.screen, int(screen_x), int(screen_y))
            
            # Update display
            pygame.display.flip()
            clock.tick(60)  # Cap at 60 FPS
        
        # Ensure final position is exact
        self.world.display_viewport(self.world.screen, end_x, end_y)
        screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        self.player.draw(self.world.screen, screen_x, screen_y)
        pygame.display.flip()

    def handle_movement(self, event):
        """Handle movement input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.show_sprite_debug:
            # Get click position
            click_x, click_y = event.pos
            
            # Calculate viewport area
            status_height = 40  # Height of the status bar
            console_height = 150  # Height of the console
            viewport_height = self.height - status_height - console_height
            
            # Calculate the viewport size to be a multiple of cell size
            viewport_cells = min(
                (self.width // self.world.CELL_SIZE),
                (viewport_height // self.world.CELL_SIZE)
            )
            if viewport_cells % 2 == 0:  # Ensure odd number of cells for proper centering
                viewport_cells -= 1
            
            # Calculate the total viewport size in pixels
            viewport_pixel_size = viewport_cells * self.world.CELL_SIZE
            
            # Calculate viewport position to center it
            viewport_x = (self.width - viewport_pixel_size) // 2
            viewport_y = status_height + (viewport_height - viewport_pixel_size) // 2
            
            # Calculate viewport boundaries
            viewport_right = viewport_x + viewport_pixel_size
            viewport_bottom = viewport_y + viewport_pixel_size
            
            # Check if click is within viewport bounds
            if (viewport_x <= click_x <= viewport_right and 
                viewport_y <= click_y <= viewport_bottom):
                
                # Convert click to viewport coordinates
                viewport_tile_x = (click_x - viewport_x) // self.world.CELL_SIZE
                viewport_tile_y = (click_y - viewport_y) // self.world.CELL_SIZE
                
                # Convert viewport coordinates to world coordinates
                half_viewport = viewport_cells // 2
                world_x = self.world.player_x + (viewport_tile_x - half_viewport)
                world_y = self.world.player_y + (viewport_tile_y - half_viewport)
                
                # Debug output
                print(f"Click at screen: ({click_x}, {click_y})")
                print(f"Viewport bounds: ({viewport_x}, {viewport_y}) to ({viewport_right}, {viewport_bottom})")
                print(f"Viewport tile pos: ({viewport_tile_x}, {viewport_tile_y})")
                print(f"World target: ({world_x}, {world_y})")
                print(f"Current player pos: ({self.world.player_x}, {self.world.player_y})")
                
                # Get path to clicked location
                path = self.world.get_path_to(world_x, world_y)
                if path and not self.in_combat:
                    # Move along the path
                    for next_x, next_y in path:
                        if self.world.is_valid_move(next_x, next_y):
                            if self.world.move_player(next_x, next_y):
                                # If we get a combat encounter, stop moving
                                return "continue"
                            
                            # Update the display after each step
                            self.world.display_viewport(self.screen, next_x, next_y, viewport_y)
                            pygame.display.flip()
                            
                            # Small delay between moves for smooth animation
                            pygame.time.delay(50)
        
        return "continue"

    def handle_enemy_defeat(self, enemy):
        """Handle enemy defeat, including loot generation and experience rewards"""
        # Record the kill
        self.world.kill_count += 1
        
        # Generate loot based on monster data if available
        loot = []
        if enemy.monster_data:
            loot = self.generate_loot(enemy.monster_data)
        
        # Calculate total gold from gold items
        gold_items = [item for item in loot if item.name == "Gold"]
        total_gold = sum(item.value for item in gold_items)
        
        # Add gold to inventory
        self.player.inventory.gold += total_gold
        
        # Add non-gold items to inventory
        non_gold_items = [item for item in loot if item.name != "Gold"]
        for item in non_gold_items:
            self.player.inventory.add_item(item)
        
        # Add experience if monster data is available
        exp_gained = enemy.monster_data.get("exp_reward", 0) if enemy.monster_data else 0
        self.player.gain_exp(exp_gained)
        
        # Regenerate some MP after combat
        self.player.mp = min(self.player.max_mp, self.player.mp + 10)
        
        # Display victory message with loot
        loot_message = f"Defeated {enemy.name}!"
        if total_gold > 0:
            loot_message += f"\nFound {total_gold} gold!"
        if non_gold_items:
            loot_message += "\nLoot:"
            for item in non_gold_items:
                if item.quantity > 1:
                    loot_message += f"\n- {item.name} (x{item.quantity})"
                else:
                    loot_message += f"\n- {item.name}"
        
        self.message_console.add_message(loot_message)
        if exp_gained > 0:
            self.message_console.add_message(f"Gained {exp_gained} XP!")
        
        # Autosave after successful fight
        save_game(self.player, self.world)
        self.message_console.add_message("Game autosaved!")
        
        # Force console to update and display the autosave message
        self.message_console.draw(self.screen, 0, SCREEN_HEIGHT - 150, SCREEN_WIDTH, 150)
        pygame.display.flip()

    def run(self):
        """Main game loop"""
        running = True
        clock = pygame.time.Clock()
        
        # Show system menu at start
        self.system_menu.show()
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.width, self.height = event.w, event.h
                    self.message_console.scroll_to_bottom()
                    self.system_menu.resize(event.w, event.h)
                    self.world.resize(event.w, event.h)
                
                # Debug keyboard events - add this before any other keyboard handling
                if event.type == pygame.KEYDOWN:
                    print(f"Key pressed: {pygame.key.name(event.key)} (key code: {event.key})")
                    # Handle teleport home (H key) - only when not in combat or inventory
                    if event.key == pygame.K_h:
                        print("H key detected!")
                        if not self.in_combat and not self.show_inventory and not self.system_menu.is_visible:
                            print("Attempting teleport...")
                            # Teleport player home
                            self.world.player_x = 0
                            self.world.player_y = 0
                            self.message_console.add_message("You have been teleported home!")
                            # Force a redraw
                            self.world.display_viewport(self.screen, self.world.player_x, self.world.player_y)
                            pygame.display.flip()
                            print("Teleport complete!")
                            continue
                
                # Handle system menu first if it's visible
                if self.system_menu.is_visible:
                    menu_action = self.system_menu.handle_event(event)
                    if menu_action:
                        if menu_action == "Continue":
                            self.system_menu.hide()
                        elif menu_action == "New Game":
                            self.player = self.create_player()
                            self.world = World(self.player)
                            self.world.game = self
                            self.system_menu.hide()
                        elif menu_action == "Tools":
                            self.show_sprite_debug = not self.show_sprite_debug
                            if self.show_sprite_debug:
                                self.world.sprite_debug_window.open()
                            else:
                                self.world.sprite_debug_window.close()
                            self.system_menu.hide()
                        elif menu_action == "Quit Game":
                            running = False
                    continue
                
                # Handle console scrolling
                console_rect = pygame.Rect(0, self.height - 150, self.width, 150)
                if self.message_console.handle_scroll(event, console_rect):
                    continue
                
                # Handle other events based on game state
                if self.show_inventory:
                    self.handle_inventory_input(event)
                elif self.show_sprite_debug:
                    self.handle_sprite_debug_input(event)
                else:
                    result = self.handle_movement(event)
                    if result == "quit":
                        self.system_menu.show()
            
            # Clear the screen
            self.screen.fill(WHITE)
            
            # Calculate viewport area
            status_height = 40  # Height of the status bar
            console_height = 150  # Height of the console
            viewport_height = self.height - status_height - console_height
            
            # Calculate the viewport size to be a multiple of cell size
            viewport_cells = min(
                (self.width // self.world.CELL_SIZE),
                (viewport_height // self.world.CELL_SIZE)
            )
            if viewport_cells % 2 == 0:  # Ensure odd number of cells for proper centering
                viewport_cells -= 1
            
            # Update the world's viewport size
            self.world.VIEWPORT_SIZE = viewport_cells
            
            # Calculate the total viewport size in pixels
            viewport_pixel_size = viewport_cells * self.world.CELL_SIZE
            
            # Calculate viewport position to center it
            viewport_x = (self.width - viewport_pixel_size) // 2
            viewport_y = status_height + (viewport_height - viewport_pixel_size) // 2
            
            # Draw the world with the player at the center
            self.world.display_viewport(self.screen, self.world.player_x, self.world.player_y, viewport_y)
            
            # Calculate the exact pixel position for the player to be centered on a tile
            player_screen_x = viewport_x + (viewport_pixel_size // 2)
            player_screen_y = viewport_y + (viewport_pixel_size // 2)
            
            # Draw the player centered on the tile
            self.player.draw(self.screen, player_screen_x - (self.world.CELL_SIZE // 2), player_screen_y - (self.world.CELL_SIZE // 2))
            
            # Draw UI overlays based on game state
            if self.show_inventory:
                self.draw_inventory_screen()
            elif self.show_sprite_debug:
                self.draw_sprite_debug()
            
            # Always draw persistent UI elements last
            self.draw_player_status()  # Draw status bar at the top
            self.message_console.draw(self.screen, 0, self.height - 150, self.width, 150)
            
            # Draw system menu if visible
            self.system_menu.draw(self.screen)
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)
        
        # Clean up
        pygame.quit()

    def show_game_over(self):
        """Show the game over screen and handle resurrection"""
        self.world.screen.fill(BLACK)
        self.world.draw_text("Game Over!", (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 - 50), WHITE)
        self.world.draw_text(f"Final level: {self.player.level}", 
                           (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2), WHITE)
        self.world.draw_text(f"Final location: ({self.world.player_x}, {self.world.player_y})", 
                           (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50), WHITE)
        self.world.draw_text("Press SPACE to resurrect at the nearest town", 
                           (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 100), WHITE)
        pygame.display.flip()

        # Wait for player input
        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Resurrect player
                        self.player.health = self.player.max_health // 2  # Resurrect with half health
                        self.player.mp = self.player.max_mp // 2      # Resurrect with half mp
                        
                        # Find nearest town coordinates (for now just starting position)
                        self.world.player_x = SCREEN_WIDTH // (2 * TILE_SIZE)
                        self.world.player_y = SCREEN_HEIGHT // (2 * TILE_SIZE)
                        
                        # End combat and clear any status effects
                        self.in_combat = False
                        self.current_enemy = None
                        self.player.status_effects.clear()
                        
                        # Add resurrection message
                        self.message_console.add_message("You have been resurrected in town.")
                        return "continue"
                    elif event.key == pygame.K_ESCAPE:
                        return "quit"
            
            # Small delay to prevent high CPU usage
            time.sleep(0.1)

    def draw_inventory_screen(self):
        """Draw the inventory screen overlay"""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)  # 70% opacity
        self.world.screen.blit(overlay, (0, 0))
        
        # Draw inventory title and gold amount on the same line
        self.world.draw_text("Inventory", (20, 20), WHITE)
        self.world.draw_text(f"Gold: {self.player.inventory.gold}", (200, 20), WHITE)
        
        # Draw equipped items
        y_pos = 60  # Moved down to prevent overlap
        self.world.draw_text("Equipped:", (20, y_pos), WHITE)
        y_pos += 30
        for slot, item in self.player.equipment.items():
            if item:
                self.world.draw_text(f"{slot.title()}: {item.name} (+{item.bonus})", 
                                   (40, y_pos), WHITE)
            else:
                self.world.draw_text(f"{slot.title()}: None", (40, y_pos), WHITE)
            y_pos += 30
        
        # Draw inventory items
        y_pos += 20
        self.world.draw_text("Items:", (20, y_pos), WHITE)
        y_pos += 30
        
        # Filter out gold items from the display
        displayed_items = [item for item in self.player.inventory.items if item.item_type != "gold"]
        
        for i, item in enumerate(displayed_items):
            if y_pos < SCREEN_HEIGHT - 80:  # Leave space for controls
                # Display item name with quantity if stackable
                if item.stackable and item.quantity > 1:
                    self.world.draw_text(f"[{i+1}] {item.name} x{item.quantity}", (40, y_pos), WHITE)
                else:
                    self.world.draw_text(f"[{i+1}] {item.name}", (40, y_pos), WHITE)
                y_pos += 30
        
        # Draw controls at the bottom
        self.world.draw_text("Controls: [1-9] Equip/Use Item | [U] Unequip | [I] Close", 
                           (20, SCREEN_HEIGHT - 30), WHITE)

    def generate_loot(self, monster_data):
        """Generate loot based on monster data"""
        loot = []
        
        # Add gold based on monster level
        min_gold = monster_data.get("min_gold", 0)
        max_gold = monster_data.get("max_gold", 0)
        gold_amount = random.randint(min_gold, max_gold)
        if gold_amount > 0:
            gold_item = Item("Gold", "gold", gold_amount, value=gold_amount)
            loot.append(gold_item)
        
        # Add equipment based on monster level and rarity
        monster_level = monster_data.get("level", 1)
        rarity_roll = random.random()
        
        # Determine rarity based on roll
        if rarity_roll < 0.05:  # 5% chance for rare
            rarity = "rare"
            item_level = monster_level + random.randint(1, 2)
        elif rarity_roll < 0.15:  # 10% chance for uncommon
            rarity = "uncommon"
            item_level = monster_level
        else:  # 85% chance for common
            rarity = "common"
            item_level = max(1, monster_level - 1)
        
        # Generate equipment based on monster type
        monster_type = monster_data.get("type", "unknown")
        if monster_type == "humanoid":
            # Humanoid monsters can drop weapons and armor
            if random.random() < 0.3:  # 30% chance for weapon
                weapon = self.generate_weapon(item_level, rarity)
                if weapon:
                    loot.append(weapon)
            if random.random() < 0.3:  # 30% chance for armor
                armor = self.generate_armor(item_level, rarity)
                if armor:
                    loot.append(armor)
        else:
            # Non-humanoid monsters have a lower chance of dropping equipment
            if random.random() < 0.15:  # 15% chance for weapon
                weapon = self.generate_weapon(item_level, rarity)
                if weapon:
                    loot.append(weapon)
            if random.random() < 0.15:  # 15% chance for armor
                armor = self.generate_armor(item_level, rarity)
                if armor:
                    loot.append(armor)
        
        return loot

    def generate_weapon(self, item_level, rarity):
        """Generate a weapon based on level and rarity"""
        try:
            # Filter weapons by level requirement
            available_weapons = [
                weapon for weapon in self.weapon_database.values()
                if weapon.get('level_req', 1) <= item_level
            ]
            
            if not available_weapons:
                return None
                
            # Select a random weapon from available ones
            weapon_data = random.choice(available_weapons)
            
            # Create weapon item with stats
            weapon = Item(
                name=weapon_data.get('name', 'Unknown Weapon'),
                item_type="weapon",
                value=weapon_data.get('value', 0),
                stats={"attack": weapon_data.get('attack', 1)},
                rarity=rarity
            )
            
            return weapon
        except Exception as e:
            print(f"Error generating weapon: {e}")
            return None

    def generate_armor(self, item_level, rarity):
        """Generate a random armor piece"""
        try:
            # Filter available armor based on level requirement
            available_armor = [
                armor for armor in self.armor_database.values()
                if armor.get('level_requirement', 1) <= item_level
            ]
            
            if not available_armor:
                return None
                
            # Select random armor from filtered list
            armor_data = random.choice(available_armor)
            
            # Create armor item
            armor = Item(
                name=armor_data.get('name', 'Unknown Armor'),
                item_type='armor',
                value=armor_data.get('value', 0),
                stats={'defense': armor_data.get('defense', 1)},
                rarity=rarity
            )
            
            return armor
        except Exception as e:
            print(f"Error generating armor: {e}")
            return None

    def draw_text(self, text, x, y, color=WHITE):
        """Draw text on the screen"""
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_player_status(self):
        """Draw player status information"""
        # Draw health bar
        self.bar_renderer.draw_health_bar(self.screen, self.player, 10, 10)
        
        # Draw MP bar
        self.bar_renderer.draw_mp_bar(self.screen, self.player, 10, 35)
        
        # Draw XP bar with level label inside
        self.bar_renderer.draw_xp_bar(self.screen, self.player, 10, 60)
        
        # Draw gold counter
        gold_text = f"Gold: {self.player.inventory.gold}"
        text = self.font.render(gold_text, True, YELLOW)
        self.screen.blit(text, (10, 85))

    def draw_combat_screen(self):
        """Draw the combat screen with all UI elements"""
        # Draw the base game world first
        self.world.display_viewport(self.world.screen, self.world.player_x, self.world.player_y)
        
        # Draw the player character
        player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        self.player.draw(self.world.screen, player_screen_x, player_screen_y)
        
        # Draw the enemy if it exists
        if self.current_enemy:
            # Position enemy on the right side of the player
            enemy_screen_x = player_screen_x + 100  # 100 pixels to the right of player
            enemy_screen_y = player_screen_y
            self.current_enemy.draw(self.world.screen, enemy_screen_x, enemy_screen_y)
        
        # Draw combat UI elements
        # Draw player status bar at the top
        self.bar_renderer.draw_health_bar(self.world.screen, self.player, 10, 10)
        self.bar_renderer.draw_xp_bar(self.world.screen, self.player, 10, 35)
        
        # Draw enemy health bar if enemy exists
        if self.current_enemy:
            self.bar_renderer.draw_health_bar(self.world.screen, self.current_enemy, 10, 60)
        
        # Draw combat options
        options = ["Attack", "Defend", "Use Item", "Flee"]
        for i, option in enumerate(options):
            text = self.font.render(option, True, WHITE)
            self.world.screen.blit(text, (10, 200 + i * 30))
        
        # Draw message console at the bottom
        # Calculate console dimensions (20% of screen height, full width)
        console_height = int(self.world.window_height * 0.2)  # 20% of screen height
        console_y = self.world.window_height - console_height
        self.message_console.draw(self.world.screen, 0, console_y, self.world.window_width, console_height)
        
        # Update the display
        pygame.display.flip()

    def handle_combat(self, enemy):
        """Handle combat with an enemy"""
        # Initialize combat state
        combat_active = True
        current_turn = "player"  # Start with player's turn
        combat_messages = []
        
        # Store original positions
        original_player_pos = (self.world.player.x, self.world.player.y)
        original_enemy_pos = (enemy.x, enemy.y)
        
        # Create combat surface
        combat_surface = pygame.Surface((self.world.screen.get_width(), self.world.screen.get_height()))
        combat_surface.fill((0, 0, 0))  # Black background
        
        # Combat loop
        while combat_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Allow fleeing from combat
                        combat_active = False
                        self.world.player.x, self.world.player.y = original_player_pos
                        enemy.x, enemy.y = original_enemy_pos
                        return False
                    
                    if current_turn == "player" and event.key == pygame.K_SPACE:
                        # Player attacks
                        damage = random.randint(5, 15)
                        enemy.health -= damage
                        combat_messages.append(f"You deal {damage} damage to {enemy.name}")
                        
                        # Check if enemy is defeated
                        if enemy.health <= 0:
                            combat_messages.append(f"{enemy.name} is defeated!")
                            combat_active = False
                            return True
                        
                        current_turn = "enemy"
            
            # Enemy's turn
            if current_turn == "enemy":
                # Enemy attacks
                enemy_damage = random.randint(3, 10)
                self.world.player.health -= enemy_damage
                combat_messages.append(f"{enemy.name} deals {enemy_damage} damage to you")
                
                # Check if player is defeated
                if self.world.player.health <= 0:
                    combat_messages.append("You are defeated!")
                    combat_active = False
                    return False
                
                current_turn = "player"
            
            # Draw combat scene
            self.world.screen.blit(combat_surface, (0, 0))
            
            # Draw combatants
            self.world.draw_sprite(self.world.screen, self.world.player.x, self.world.player.y, "player")
            self.world.draw_sprite(self.world.screen, enemy.x, enemy.y, enemy.name)
            
            # Draw health bars
            self.bar_renderer.draw_health_bar(self.screen, self.world.player, 10, 10)
            self.bar_renderer.draw_health_bar(self.screen, enemy, SCREEN_HEIGHT - 210, 10)
            
            # Draw XP bar for player
            self.bar_renderer.draw_xp_bar(self.screen, self.world.player, 10, 35)
            
            # Draw combat messages
            self.draw_combat_messages(combat_messages)
            
            # Draw turn indicator
            turn_text = f"Current Turn: {'Player' if current_turn == 'player' else enemy.name}"
            text_surface = self.font.render(turn_text, True, (255, 255, 255))
            self.world.screen.blit(text_surface, (50, 200))
            
            # Draw instructions
            instructions = [
                "Press SPACE to attack",
                "Press ESC to flee"
            ]
            for i, text in enumerate(instructions):
                text_surface = self.font.render(text, True, (200, 200, 200))
                self.world.screen.blit(text_surface, (50, 250 + i * 30))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return False

    def draw_combat_messages(self, messages):
        """Draw combat messages"""
        # Show last 5 messages
        for i, message in enumerate(messages[-5:]):
            text_surface = self.font.render(message, True, (255, 255, 255))
            self.world.screen.blit(text_surface, (50, 350 + i * 30))

    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            # Debug keyboard events
            if event.type == pygame.KEYDOWN:
                print(f"Key pressed: {pygame.key.name(event.key)} (key code: {event.key})")
                if event.key == pygame.K_h:
                    print("H key detected!")
                    if not self.in_combat and not self.show_inventory:
                        print("Attempting teleport...")
                        # Teleport player home
                        self.world.player_x = 0
                        self.world.player_y = 0
                        self.message_console.add_message("You have been teleported home!")
                        # Force a redraw
                        self.world.display_viewport(self.screen, self.world.player_x, self.world.player_y)
                        pygame.display.flip()
                        print("Teleport complete!")
                        continue
            
            if event.type == pygame.VIDEORESIZE:
                self.world.resize(event.w, event.h)
                continue
            
            # Handle console scrolling
            console_rect = pygame.Rect(
                0,
                self.height - 150,  # Console height
                self.width,
                150
            )
            if self.message_console.handle_scroll(event, console_rect):
                continue  # Skip other event processing if console handled the event
            
            # Handle other events based on game state
            if self.in_combat:
                result = self.combat_system.handle_combat_turn(event)
                if result == "game_over":
                    self.show_game_over()
                    return "quit"
            elif self.show_inventory:
                self.handle_inventory_input(event)
            elif self.show_sprite_debug:
                self.handle_sprite_debug_input(event)
            else:
                result = self.handle_movement(event)
                if result == "quit":
                    self.system_menu.show()
        
        return "continue"

    def battle(self, enemy):
        """Start a battle with an enemy"""
        if enemy is None:
            return
            
        # Initialize combat system
        self.combat_system = CombatSystem(self)
        self.combat_system.start_combat(enemy)
        
        # Main combat loop
        while self.combat_system.in_combat:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        # End combat
        self.combat_system.end_combat() 

    def update(self):
        """Update game state"""
        if self.in_combat:
            # Update combat system
            self.combat_system.update()
        else:
            # Update world state
            self.world.update()
            
        # Update message console
        self.message_console.update()
        
        # Update any active animations
        if hasattr(self, 'combat_system'):
            self.combat_system.update_animations() 

    def draw(self):
        """Draw the current game state"""
        # Clear the screen
        self.screen.fill(BLACK)
        
        if self.in_combat:
            # Draw combat screen
            self.combat_system.draw_combat_screen()
        else:
            # Draw world
            self.world.draw(self.screen)
            
            # Draw player status
            self.draw_player_status()
            
            # Draw message console
            self.message_console.draw(self.screen, 10, SCREEN_HEIGHT - 160, 400, 150)
            
        # Update the display
        pygame.display.flip() 

    def load_item_databases(self):
        """Load all item databases from JSON files"""
        try:
            # Load weapon database
            with open('data/weapons.json', 'r') as f:
                weapons_data = json.load(f)
                self.weapon_database = {weapon['name']: weapon for weapon in weapons_data['weapons']}
        except Exception as e:
            print(f"Error loading weapon database: {e}")
            self.weapon_database = {}
            
        try:
            # Load armor database
            with open('data/armor.json', 'r') as f:
                armor_data = json.load(f)
                self.armor_database = {armor['name']: armor for armor in armor_data['armor']}
        except Exception as e:
            print(f"Error loading armor database: {e}")
            self.armor_database = {}
            
        try:
            # Load resource database
            with open('data/resources.json', 'r') as f:
                self.resource_database = json.load(f)
        except Exception as e:
            print(f"Error loading resource database: {e}")
            self.resource_database = {}
            
        try:
            # Load food database
            with open('data/food.json', 'r') as f:
                self.food_database = json.load(f)
        except Exception as e:
            print(f"Error loading food database: {e}")
            self.food_database = {}
            
        try:
            # Load potion database
            with open('data/potions.json', 'r') as f:
                self.potion_database = json.load(f)
        except Exception as e:
            print(f"Error loading potion database: {e}")
            self.potion_database = {} 

    def create_player(self):
        """Create a new player character"""
        # Create player with initial stats
        player = Character(
            name="Player",
            level=1,
            health=100,
            max_health=100,
            attack=15,
            defense=10,
            speed=10,
            mp=50,
            max_mp=50
        )
        
        # Add starting items
        player.inventory.add_item("Health Potion", 3)
        player.inventory.add_item("Mana Potion", 2)
        
        # Add starting spells
        player.known_spells = ['fireball', 'lesser_heal']
        
        # Set initial position to center of world
        self.world = World(player)
        world_size = self.world.WORLD_SIZE
        self.world.player_x = world_size // 2
        self.world.player_y = world_size // 2
        
        return player

    def handle_combat_turn(self, event):
        """Handle a single turn of combat"""
        if not self.in_combat:
            return "continue"

        # Update status effects
        for character in self.turn_order:
            character.update_status_effects()

        # Check if combat is over
        if not self.game.player.is_alive():
            return "game_over"
        if not self.current_enemy.is_alive():
            self.handle_enemy_defeat()
            return "continue"

        # Handle input for player's turn
        if self.turn_order[0] == self.game.player:
            if event.type == pygame.KEYDOWN:
                # Number key shortcuts for combat actions
                if event.key == pygame.K_1:
                    self.combat_system.selected_option = 0  # Attack
                    return self.combat_system.handle_player_action()
                elif event.key == pygame.K_2:
                    self.combat_system.selected_option = 1  # Strong Attack
                    return self.combat_system.handle_player_action()
                elif event.key == pygame.K_3:
                    self.combat_system.selected_option = 2  # Heal
                    return self.combat_system.handle_player_action()
                elif event.key == pygame.K_4:
                    self.combat_system.selected_option = 3  # Flee
                    return self.combat_system.handle_player_action()
                
                # Arrow key navigation
                if event.key == pygame.K_UP:
                    self.combat_system.selected_option = (self.combat_system.selected_option - 1) % len(self.combat_system.combat_options)
                elif event.key == pygame.K_DOWN:
                    self.combat_system.selected_option = (self.combat_system.selected_option + 1) % len(self.combat_system.combat_options)
                elif event.key == pygame.K_RETURN:
                    return self.combat_system.handle_player_action()
        else:
            # Enemy's turn
            return self.combat_system.handle_enemy_turn()

        return "continue" 

    def load_game_state(self, save_data):
        """Load game state from save data"""
        # Create player with saved stats
        self.player = Character(
            save_data["player"]["name"],
            health=save_data["player"]["max_health"],
            attack=save_data["player"]["attack"],
            character_type='player'
        )
        # Restore player stats
        self.player.health = save_data["player"]["health"]
        self.player.level = save_data["player"]["level"]
        self.player.exp = save_data["player"]["exp"]
        self.player.exp_to_next_level = save_data["player"].get("exp_to_next_level", 100)
        self.player.max_health = save_data["player"]["max_health"]
        self.player.attack = save_data["player"]["attack"]
        self.player.mp = save_data["player"].get("mp", 50)  # Restore MP
        self.player.max_mp = save_data["player"].get("max_mp", 50)  # Restore max MP
        # Restore kill stats
        self.player.kills = save_data["player"].get("kills", {})
        # Restore inventory if it exists
        if "inventory" in save_data["player"]:
            self.player.inventory = Inventory.from_dict(save_data["player"]["inventory"])
        # Restore equipment if it exists
        if "equipment" in save_data["player"]:
            for slot, item_data in save_data["player"]["equipment"].items():
                if item_data:
                    self.player.equipment[slot] = Item.from_dict(item_data)
        else:
            # Create new player character
            self.player = self.create_player()
        
        # Initialize world with player
        self.world = World(self.player)
        self.world.show_debug = self.show_debug
        self.world.show_sprite_debug = self.show_sprite_debug
        self.world.screen = self.screen  # Share the screen surface
        
        # Restore player position if save exists
        if save_data and "world" in save_data:
            self.world.player_x = save_data["world"].get("player_x", 0)
            self.world.player_y = save_data["world"].get("player_y", 0)
        
        # Combat options
        self.combat_options = [
            "Attack",
            "Strong Attack",
            "Heal",
            "Flee"
        ]
        self.selected_option = 0
        
        # Enemy types
        self.enemies = ["Goblin", "Orc", "Troll", "Dragon"]
        
        print("Game initialization complete")
        
        # Load monster database
        self.monster_database = self.load_monster_database()
        
        # Initialize combat system
        self.combat_system = CombatSystem(self)
        
        self.bar_renderer = Bar() 