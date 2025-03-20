import pygame
import time
import random
import sys
from utils.constants import (
    WINDOW_SIZE, WHITE, BLACK, GREEN, SOUND_ENEMY_DEFEAT,
    SOUND_PLAYER_DEFEAT, SOUND_FLEE, WINDOW_TITLE
)
from utils.helpers import play_sound, save_game, load_game, load_sprite_mappings
from entities.character import Character
from game.combat import CombatSystem
from entities.items import Item, Inventory
from ui.console import MessageConsole
from game.world import World
from game.sprites import sprite_manager

class Game:
    def __init__(self):
        """Initialize the game"""
        # Initialize Pygame and set up display first
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Simple RPG")
        
        # Initialize font
        self.font = pygame.font.Font(None, 24)
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
        # Initialize message console
        self.message_console = MessageConsole(max_messages=6)
        
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
        
        # Display initial viewport
        self.world.display_viewport()
        print("Game initialization complete")
        
        # Initialize combat system
        self.combat_system = CombatSystem(self)

    def create_enemy(self):
        """Create a random enemy with appropriate stats"""
        enemy_name = random.choice(self.enemies)
        if enemy_name == "Dragon":
            return Character(enemy_name, health=150, attack=20, character_type='enemy')
        elif enemy_name == "Troll":
            return Character(enemy_name, health=100, attack=15, character_type='enemy')
        elif enemy_name == "Orc":
            return Character(enemy_name, health=80, attack=12, character_type='enemy')
        else:  # Goblin
            return Character(enemy_name, health=50, attack=8, character_type='enemy')

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

    def handle_movement(self, event):
        """Handle player movement and game state updates"""
        # Calculate player screen position (needed for all drawing operations)
        player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        
        # Handle sprite debug view first
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.show_sprite_debug = not self.show_sprite_debug
            if self.show_sprite_debug:
                self.world.sprite_debug_window.open()
            else:
                self.world.sprite_debug_window.close()
            return "continue"
        
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
            if event.key == pygame.K_LEFT:
                moved = self.world.move_player(self.world.player_x - 1, self.world.player_y)
            elif event.key == pygame.K_RIGHT:
                moved = self.world.move_player(self.world.player_x + 1, self.world.player_y)
            elif event.key == pygame.K_UP:
                moved = self.world.move_player(self.world.player_x, self.world.player_y - 1)
            elif event.key == pygame.K_DOWN:
                moved = self.world.move_player(self.world.player_x, self.world.player_y + 1)
            elif event.key == pygame.K_ESCAPE:
                return "quit"
                
            # Only create enemy if we successfully moved and aren't in combat
            if moved and not self.in_combat:
                # 30% chance to encounter an enemy when moving
                if random.random() < 0.3:
                    enemy = self.create_enemy()
                    self.battle(enemy)
                    
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.show_sprite_debug:  # Left click
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
                    if self.world.move_player(next_x, next_y):
                        # 30% chance to encounter an enemy when moving
                        if random.random() < 0.3:
                            enemy = self.create_enemy()
                            self.battle(enemy)
                            if not self.player.is_alive():
                                self.show_game_over()
                                self.game_running = False
                                return "quit"
                            break  # Stop moving if we encounter an enemy
                    # Update display after each step
                    self.world.display_viewport()
                    self.player.draw(self.world.screen, player_screen_x, player_screen_y)
                    pygame.display.flip()
                    pygame.time.delay(100)  # Small delay between steps
        
        return "continue"

    def handle_enemy_defeat(self, enemy):
        """Handle enemy defeat, including loot and experience"""
        # Record the kill
        self.player.record_kill(enemy.name)
        
        # Generate and display loot
        loot = self.generate_loot(enemy.name)
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
        
        # Determine XP reward based on enemy type
        xp_reward = {
            "Dragon": 100,
            "Troll": 75,
            "Orc": 50,
            "Goblin": 25
        }.get(enemy.name, 50)  # Default to 50 if enemy type not found
        
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
        self.game_running = True
        clock = pygame.time.Clock()
        
        while self.game_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    break
                elif event.type == pygame.VIDEORESIZE:
                    self.world.handle_resize((event.w, event.h))
                else:
                    result = self.handle_movement(event)
                    if result == "quit":
                        self.game_running = False
                        break
            
            # Update game state
            if self.show_inventory:
                self.draw_inventory_screen()
            else:
                if self.show_sprite_debug:
                    # Only draw sprite debug view when in debug mode
                    self.world.sprite_debug_window.draw(self.world.screen)
                else:
                    # Only draw game world when not in debug mode
                    self.world.display_viewport()
                    
                    # Calculate player screen position
                    player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
                    player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
                    
                    # Draw player at center of viewport
                    self.player.draw(self.world.screen, player_screen_x, player_screen_y)
            
            # Update display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)
        
        # Clean up
        if self.world.sprite_debug_window.is_open:
            self.world.sprite_debug_window.close()
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

    def draw_combat_screen(self):
        """Draw the combat screen"""
        # Draw the game world in the background
        self.world.display_viewport()
        
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)  # 50% opacity
        self.screen.blit(overlay, (0, 0))
        
        # Calculate player screen position
        player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        
        # Draw player and enemy
        self.player.draw(self.screen, player_screen_x - 100, player_screen_y)  # Player on left
        if self.current_enemy:
            self.current_enemy.draw(self.screen, player_screen_x + 100, player_screen_y)  # Enemy on right
            
        # Draw health bars
        self.draw_health_bar(self.player, 10, 10)  # Player health bar on left
        if self.current_enemy:
            self.draw_health_bar(self.current_enemy, WINDOW_SIZE - 210, 10)  # Enemy health bar on right
            
        # Draw combat options
        option_text = "Combat Options:"
        self.draw_text(option_text, 10, 400, WHITE)
        self.draw_text("1: Attack  2: Strong Attack  3: Heal  4: Flee", 10, 430, WHITE)
        
        # Draw message console at the bottom of the screen
        console_height = 100
        self.message_console.draw(self.screen, 10, WINDOW_SIZE - console_height - 10, WINDOW_SIZE - 20, console_height)
        
        # Update display
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
            
            # Draw health bars with proper width and height
            hp_bar_width = 300
            hp_bar_height = 25
            padding = 10
            
            # Draw player health bar
            self.draw_health_bar(self.world.screen, self.world.player.health, self.world.player.max_health,
                               padding, padding, hp_bar_width, hp_bar_height)
            
            # Draw enemy health bar
            self.draw_health_bar(self.world.screen, enemy.health, enemy.max_health,
                               padding, padding + hp_bar_height + 5, hp_bar_width, hp_bar_height)
            
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

    def draw_health_bar(self, character, x, y):
        """Draw a health bar for a character"""
        bar_width = 200
        bar_height = 20
        fill = (character.health / character.max_health) * bar_width
        
        # Draw the background
        pygame.draw.rect(self.screen, (255, 0, 0), (x, y, bar_width, bar_height))
        # Draw the fill
        pygame.draw.rect(self.screen, (0, 255, 0), (x, y, fill, bar_height))
        # Draw the border
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)
        
        # Draw the text
        health_text = f"{character.name}: {character.health}/{character.max_health} HP"
        self.draw_text(health_text, x, y - 20)
        
        # Draw XP bar for player character
        if character == self.world.player:
            xp_y = y + bar_height + 5
            xp_fill = (character.exp / (character.level * 100)) * bar_width
            
            # Draw the background
            pygame.draw.rect(self.screen, (100, 100, 100), (x, xp_y, bar_width, bar_height))
            # Draw the fill
            pygame.draw.rect(self.screen, (0, 0, 255), (x, xp_y, xp_fill, bar_height))
            # Draw the border
            pygame.draw.rect(self.screen, (255, 255, 255), (x, xp_y, bar_width, bar_height), 2)
            
            # Draw the text
            xp_text = f"Level {character.level} - XP: {character.exp}/{character.level * 100}"
            self.draw_text(xp_text, x, xp_y + bar_height + 5)

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
        """Handle battle with an enemy"""
        self.current_enemy = enemy
        self.in_combat = True
        
        if self.combat_system.handle_battle(enemy):
            self.combat_system.enemy_turn(enemy)
            return True
        return False 