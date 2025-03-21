import pygame
import time
import random
import sys
import json
from utils.constants import (
    WINDOW_SIZE, WHITE, BLACK, GREEN, SOUND_ENEMY_DEFEAT,
    SOUND_PLAYER_DEFEAT, SOUND_FLEE, WINDOW_TITLE
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
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Simple RPG")
        
        # Initialize window dimensions
        self.width = WINDOW_SIZE
        self.height = WINDOW_SIZE
        
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
               
        # Debug view flags
        self.show_debug = False
        self.show_sprite_debug = False
        
        # Initialize sprite manager (after display is set up)
        sprite_manager.initialize()
        
        # Load sprite mappings if they exist
        load_sprite_mappings()
        
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
            self.player = Character(
                name="Hero",
                health=100,
                attack=10,
                character_type='player'
            )
            # Initialize XP system (these should be set in Character.__init__ but let's make sure)
            self.player.level = 1
            self.player.exp = 0
            self.player.exp_to_next_level = 100
        
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
        
        # Load sounds
        self.encounter_sound = pygame.mixer.Sound("sounds/CivilWarDrummer.wav")

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
                self.message_console.add_message("Press 1 for weapon, 2 for armor")
            elif event.key in [pygame.K_1, pygame.K_2]:  # Changed condition to remove message.startswith check
                slot = "weapon" if event.key == pygame.K_1 else "armor"
                if self.player.unequip_item(slot):
                    self.message_console.add_message(f"Unequipped {slot}")
                else:
                    self.message_console.add_message(f"No {slot} to unequip")
            elif pygame.K_1 <= event.key <= pygame.K_9:
                item_index = event.key - pygame.K_1
                if item_index < len(self.player.inventory.items):
                    item = self.player.inventory.items[item_index]
                    if self.player.equip_item(item_index):
                        self.message_console.add_message(f"Equipped {item.name}")
                    else:
                        self.message_console.add_message(f"Cannot equip {item.name}")

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
        """Handle player movement and game state updates"""
        # Calculate player screen position (needed for all drawing operations)
        player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        
        # Handle sprite debug view first
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.show_sprite_debug = not self.show_sprite_debug
                if self.show_sprite_debug:
                    self.world.sprite_debug_window.open()
                else:
                    self.world.sprite_debug_window.close()
            elif event.key == pygame.K_i:  # Open inventory
                self.show_inventory = True
                return
            elif event.key == pygame.K_ESCAPE:
                self.system_menu.show()
                return "menu"
        
        # Don't handle movement if in combat
        if self.in_combat:
            return "continue"
        
        # Forward only relevant events to sprite debug window if it's open
        if self.show_sprite_debug:
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if self.world.handle_sprite_debug_click(event.pos if hasattr(event, 'pos') else None, event):
                    return "continue"
            return "continue"
        
        # Handle regular game controls when not in sprite debug
        if event.type == pygame.KEYDOWN:
            moved = False
            new_x, new_y = self.world.player_x, self.world.player_y
            
            if event.key == pygame.K_LEFT:
                new_x -= 1
            elif event.key == pygame.K_RIGHT:
                new_x += 1
            elif event.key == pygame.K_UP:
                new_y -= 1
            elif event.key == pygame.K_DOWN:
                new_y += 1
            
            # Check if movement is valid and animate if it is
            if (new_x, new_y) != (self.world.player_x, self.world.player_y):
                if self.world.is_valid_move(new_x, new_y):
                    # Store old position for animation
                    old_x, old_y = self.world.player_x, self.world.player_y
                    
                    # Update position in world
                    moved = self.world.move_player(new_x, new_y)
                    
                    if moved:
                        # Animate the movement
                        self.animate_movement(old_x, old_y, new_x, new_y)
                        
                        # Check for enemy encounter after movement
                        if random.random() < 0.3:
                            enemy = self.create_enemy()
                            self.battle(enemy)
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.show_sprite_debug:
            # Get click position relative to viewport
            click_x, click_y = event.pos
            viewport_x = click_x // self.world.CELL_SIZE
            viewport_y = click_y // self.world.CELL_SIZE
            
            # Convert viewport coordinates to world coordinates
            world_x = self.world.player_x - (self.world.VIEWPORT_SIZE // 2) + viewport_x
            world_y = self.world.player_y - (self.world.VIEWPORT_SIZE // 2) + viewport_y
            
            # Get path to clicked location
            path = self.world.get_path_to(world_x, world_y)
            if path and not self.in_combat:
                # Move along the path
                for next_x, next_y in path:
                    if self.world.is_valid_move(next_x, next_y):
                        old_x, old_y = self.world.player_x, self.world.player_y
                        if self.world.move_player(next_x, next_y):
                            # Animate the movement
                            self.animate_movement(old_x, old_y, next_x, next_y)
                            
                            # Check for enemy encounter
                            if random.random() < 0.3:
                                enemy = self.create_enemy()
                                self.battle(enemy)
                                if not self.player.is_alive():
                                    self.show_game_over()
                                    self.game_running = False
                                    return "quit"
                                break
        
        return "continue"

    def handle_enemy_defeat(self, enemy):
        """Handle enemy defeat, including loot and experience"""
        # Record the kill
        self.player.record_kill(enemy.name)
        
        # Generate and display loot
        loot = self.generate_loot(enemy.monster_data)
        loot_message = []
        for item in loot:
            if item.item_type == "gold":
                self.player.inventory.gold += item.value
                loot_message.append(f"{item.value} gold")
            else:
                if self.player.inventory.add_item(item):
                    loot_message.append(item.name)
                else:
                    self.message_console.add_message("Inventory full! Some items were lost!")
        
        # Get XP reward from monster data
        xp_reward = enemy.monster_data['exp_reward']
        
        # Display victory message with loot
        if loot_message:
            self.message_console.add_message(f"Defeated! Found: {', '.join(loot_message)}! +{xp_reward} XP!")
        else:
            self.message_console.add_message(f"Defeated! No loot found. +{xp_reward} XP!")
        
        play_sound(SOUND_ENEMY_DEFEAT)
        self.player.gain_exp(xp_reward)
        
        # Autosave after successful fight
        if save_game(self.player, self.world):
            time.sleep(1)  # Wait a bit so player can read loot message
            self.message_console.add_message("Game autosaved!")

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
                    self.message_console.scroll_to_bottom()  # Reset scroll position on resize
                    self.system_menu.resize(event.w, event.h)  # Update menu positions
                    self.world.resize(event.w, event.h)  # Update world viewport size
                
                # Handle system menu first if it's visible
                if self.system_menu.is_visible:
                    menu_action = self.system_menu.handle_event(event)
                    if menu_action:
                        if menu_action == "Continue":
                            self.system_menu.hide()
                        elif menu_action == "New Game":
                            # Reset player and world
                            self.player = Character(
                                name="Hero",
                                health=100,
                                attack=10,
                                character_type='player'
                            )
                            self.player.level = 1
                            self.player.exp = 0
                            self.player.exp_to_next_level = 100
                            self.world = World(self.player)
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
                console_rect = pygame.Rect(
                    0,
                    self.height - 150,  # Console height
                    self.width,
                    150
                )
                if self.message_console.handle_scroll(event, console_rect):
                    continue  # Skip other event processing if console handled the event
                
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
            
            # Draw the game world in the middle area (between status bar and console)
            status_height = 40  # Height of the status bar
            console_height = 150  # Height of the console
            viewport_height = self.height - status_height - console_height
            self.world.display_viewport(self.screen, self.world.player_x, self.world.player_y, status_height)
            
            # Draw the player
            player_screen_x = self.width // 2
            player_screen_y = status_height + (viewport_height // 2)
            self.player.draw(self.screen, player_screen_x, player_screen_y)
            
            # Draw UI overlays based on game state
            if self.show_inventory:
                self.draw_inventory_screen()
            elif self.show_sprite_debug:
                self.draw_sprite_debug()
            
            # Always draw persistent UI elements last
            self.draw_player_status()  # Draw status bar at the top
            self.message_console.draw(self.screen, 0, self.height - 150, self.width, 150)  # Draw console at the bottom
            
            # Draw system menu if visible
            self.system_menu.draw(self.screen)
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)
        
        # Clean up
        pygame.quit()

    def show_game_over(self):
        """Show the game over screen"""
        self.world.screen.fill(BLACK)
        self.world.draw_text("Game Over!", (WINDOW_SIZE//2 - 50, WINDOW_SIZE//2 - 50), WHITE)
        self.world.draw_text(f"Final level: {self.player.level}", 
                           (WINDOW_SIZE//2 - 50, WINDOW_SIZE//2), WHITE)
        self.world.draw_text(f"Final location: ({self.world.player_x}, {self.world.player_y})", 
                           (WINDOW_SIZE//2 - 100, WINDOW_SIZE//2 + 50), WHITE)
        pygame.display.flip()
        time.sleep(3)

    def draw_inventory_screen(self):
        """Draw the inventory screen overlay"""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)  # 70% opacity
        self.world.screen.blit(overlay, (0, 0))
        
        # Draw inventory title
        self.world.draw_text("Inventory", (20, 20), WHITE)
        
        # Draw gold amount
        self.world.draw_text(f"Gold: {self.player.inventory.gold}", (20, 50), WHITE)
        
        # Draw equipped items
        y_pos = 80
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
        
        for i, item in enumerate(self.player.inventory.items):
            if y_pos < WINDOW_SIZE - 80:  # Leave space for controls
                self.world.draw_text(f"[{i+1}] {item.name}", (40, y_pos), WHITE)
                y_pos += 30
        
        # Draw controls at the bottom
        self.world.draw_text("Controls: [1-9] Equip/Use Item | [U] Unequip | [I] Close", 
                           (20, WINDOW_SIZE - 30), WHITE)

    def generate_loot(self, enemy_name):
        """Generate loot based on enemy type"""
        loot = []
        
        # Base gold values for each enemy type
        gold_values = {
            "Dragon": (80, 120),
            "Troll": (40, 80),
            "Orc": (20, 40),
            "Goblin": (5, 15)
        }
        
        # Add gold
        min_gold, max_gold = gold_values.get(enemy_name, (10, 30))
        gold_amount = random.randint(min_gold, max_gold)
        loot.append(Item("Gold Coins", "gold", gold_amount))
        
        # Chance to drop equipment
        drop_chance = {
            "Dragon": 0.8,
            "Troll": 0.5,
            "Orc": 0.3,
            "Goblin": 0.1
        }.get(enemy_name, 0.2)
        
        if random.random() < drop_chance:
            # Possible equipment drops
            weapons = [
                ("Rusty Dagger", 1),
                ("Iron Sword", 2),
                ("Steel Blade", 3),
                ("Magic Sword", 4),
                ("Dragon Slayer", 5)
            ]
            armor = [
                ("Leather Armor", 1),
                ("Chain Mail", 2),
                ("Steel Plate", 3),
                ("Magic Armor", 4),
                ("Dragon Scale", 5)
            ]
            
            # Better enemies drop better loot
            quality = {
                "Dragon": (3, 5),
                "Troll": (2, 4),
                "Orc": (1, 3),
                "Goblin": (0, 2)
            }.get(enemy_name, (0, 2))
            
            # Maybe drop a weapon
            if random.random() < 0.5:
                name, bonus = random.choice(weapons[quality[0]:quality[1]])
                loot.append(Item(name, "weapon", bonus))
            # Maybe drop armor
            if random.random() < 0.5:
                name, bonus = random.choice(armor[quality[0]:quality[1]])
                loot.append(Item(name, "armor", bonus))
        
        return loot

    def draw_text(self, text, x, y, color=WHITE):
        """Draw text on the screen"""
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_player_status(self):
        """Draw the player's status bar at the top of the screen"""
        # Draw health bar
        health_width = 200
        health_height = 20
        health_x = 10
        health_y = 10
        
        # Draw health bar background
        pygame.draw.rect(self.world.screen, (100, 0, 0), 
                        (health_x, health_y, health_width, health_height))
        
        # Draw health bar fill
        health_percent = self.player.health / self.player.max_health
        pygame.draw.rect(self.world.screen, (0, 255, 0),
                        (health_x, health_y, health_width * health_percent, health_height))
        
        # Draw health text
        health_text = f"HP: {self.player.health}/{self.player.max_health}"
        text_surface = self.font.render(health_text, True, WHITE)
        self.world.screen.blit(text_surface, (health_x + 5, health_y + 2))
        
        # Draw XP bar
        xp_width = 200
        xp_height = 15
        xp_x = 10
        xp_y = 35
        
        # Draw XP bar background
        pygame.draw.rect(self.world.screen, (50, 50, 50),
                        (xp_x, xp_y, xp_width, xp_height))
        
        # Draw XP bar fill
        xp_percent = self.player.exp / self.player.exp_to_next_level
        pygame.draw.rect(self.world.screen, (0, 0, 255),
                        (xp_x, xp_y, xp_width * xp_percent, xp_height))
        
        # Draw XP text
        xp_text = f"XP: {self.player.exp}/{self.player.exp_to_next_level} (Level {self.player.level})"
        text_surface = self.font.render(xp_text, True, WHITE)
        self.world.screen.blit(text_surface, (xp_x + 5, xp_y + 2))
        
        # Draw gold amount
        gold_text = f"Gold: {self.player.inventory.gold}"
        text_surface = self.font.render(gold_text, True, WHITE)
        self.world.screen.blit(text_surface, (xp_x + xp_width + 20, xp_y + 2))

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
        Bar.draw_health_bar(self.world.screen, self.player, 10, 10)
        Bar.draw_xp_bar(self.world.screen, self.player, 10, 35)
        
        # Draw enemy health bar if enemy exists
        if self.current_enemy:
            Bar.draw_health_bar(self.world.screen, self.current_enemy, 10, 60)
        
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
            Bar.draw_health_bar(self.screen, self.world.player, 10, 10)
            Bar.draw_health_bar(self.screen, enemy, WINDOW_SIZE - 210, 10)
            
            # Draw XP bar for player
            Bar.draw_xp_bar(self.screen, self.world.player, 10, 35)
            
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
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_d:
                    # Toggle terrain debug view
                    self.show_debug = not self.show_debug
                    self.show_sprite_debug = False
                    self.world.show_debug = self.show_debug
                elif event.key == pygame.K_s:
                    # Toggle sprite debug view
                    self.show_sprite_debug = not self.show_sprite_debug
                    self.show_debug = False
                    self.world.show_debug = False
                elif event.key == pygame.K_g:
                    # Return to game view
                    self.show_debug = False
                    self.show_sprite_debug = False
                    self.world.show_debug = False
                else:
                    self.handle_movement(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks in sprite debug view
                if event.button == 1 and self.show_sprite_debug:  # Left click
                    if self.world.handle_sprite_debug_click(event.pos):
                        continue
        return True 

    def battle(self, enemy):
        """Start a battle with an enemy"""
        self.current_enemy = enemy
        self.in_combat = True
        
        # Play first 1.5 seconds of encounter sound
        play_wave_sound(self.encounter_sound, starttime=0, maxtime=1500)
        
        if self.combat_system.handle_battle(enemy):
            self.combat_system.enemy_turn(enemy)
            return True
        return False 