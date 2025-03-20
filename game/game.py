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
from entities.items import Item, Inventory
from ui.console import MessageConsole
from game.world import World
from game.sprites import sprite_manager

class Game:
    def __init__(self):
        # Initialize Pygame display first
        pygame.init()
        pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Initialize sprite manager
        sprite_manager.initialize()
        
        # Load sprite mappings if they exist
        load_sprite_mappings()
        
        # Debug view flags
        self.show_debug = False
        self.show_sprite_debug = False
        
        # Create player character
        self.player = Character(
            name="Hero",
            health=100,
            attack=10,
            character_type='player'
        )
        
        # Create world with player
        self.world = World(self.player)
        self.world.show_debug = self.show_debug
        self.world.show_sprite_debug = self.show_sprite_debug
        
        # Create message console
        self.console = MessageConsole()
        
        # Game state
        self.running = True
        self.in_combat = False
        self.current_enemy = None
        self.combat_options = [
            "Attack",
            "Strong Attack",
            "Heal",
            "Flee"
        ]
        self.selected_option = 0
        
        # Add message console
        self.message_console = MessageConsole(max_messages=6)
        
        # Try to load saved game
        save_data = load_game()
        if save_data:
            # Create player with saved stats
            self.player = Character(
                save_data["player"]["name"],
                health=save_data["player"]["max_health"],
                attack=save_data["player"]["attack"]
            )
            # Restore player stats
            self.player.health = save_data["player"]["health"]
            self.player.level = save_data["player"]["level"]
            self.player.exp = save_data["player"]["exp"]
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
            self.player = Character("Hero")
        
        self.enemies = ["Goblin", "Orc", "Troll", "Dragon"]
        self.game_running = True
        self.show_inventory = False
        
        # Initialize world with player
        self.world = World(self.player)
        
        # Restore player position if save exists
        if save_data and "world" in save_data:
            self.world.player_x = save_data["world"].get("player_x", 0)
            self.world.player_y = save_data["world"].get("player_y", 0)
        
        # Initialize game state
        self.in_combat = False
        self.current_enemy = None
        self.combat_animation_frame = 0
        self.combat_animation_speed = 0.2
        self.message = "Click to move, Q to quit"
        self.message_time = 0
        self.message_duration = 3  # seconds
        
        # Display initial viewport
        self.world.display_viewport()
        print("Game initialized")  # Debug print

    def create_enemy(self):
        enemy_name = random.choice(self.enemies)
        if enemy_name == "Dragon":
            return Character(enemy_name, health=150, attack=20)
        elif enemy_name == "Troll":
            return Character(enemy_name, health=100, attack=15)
        elif enemy_name == "Orc":
            return Character(enemy_name, health=80, attack=12)
        else:  # Goblin
            return Character(enemy_name, health=50, attack=8)

    def handle_inventory_input(self, event):
        """Handle input while inventory is open"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:  # Close inventory
                self.show_inventory = False
            elif event.key == pygame.K_u:  # Unequip menu
                self.message = "Press 1 for weapon, 2 for armor"
                self.message_console.add_message("Press 1 for weapon, 2 for armor")
                self.message_time = time.time()
            elif event.key in [pygame.K_1, pygame.K_2] and self.message.startswith("Press 1 for"):
                # Handle unequipping
                slot = "weapon" if event.key == pygame.K_1 else "armor"
                if self.player.unequip_item(slot):
                    self.message = f"Unequipped {slot}"
                    self.message_console.add_message(f"Unequipped {slot}")
                else:
                    self.message = f"No {slot} to unequip"
                    self.message_console.add_message(f"No {slot} to unequip")
                self.message_time = time.time()
            elif pygame.K_1 <= event.key <= pygame.K_9:
                # Try to equip/use item
                item_index = event.key - pygame.K_1
                if item_index < len(self.player.inventory.items):
                    item = self.player.inventory.items[item_index]
                    if self.player.equip_item(item_index):
                        self.message = f"Equipped {item.name}"
                        self.message_console.add_message(f"Equipped {item.name}")
                    else:
                        self.message = f"Cannot equip {item.name}"
                        self.message_console.add_message(f"Cannot equip {item.name}")
                    self.message_time = time.time()

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
        
        # Forward only relevant events to sprite debug window if it's open
        if self.show_sprite_debug:
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if self.world.handle_sprite_debug_click(event.pos if hasattr(event, 'pos') else None, event):
                    return "continue"
            return "continue"
        
        # Handle regular game controls when not in sprite debug
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if self.world.move_player(self.world.player_x - 1, self.world.player_y):
                    enemy = self.create_enemy()
                    self.battle(enemy)
            elif event.key == pygame.K_RIGHT:
                if self.world.move_player(self.world.player_x + 1, self.world.player_y):
                    enemy = self.create_enemy()
                    self.battle(enemy)
            elif event.key == pygame.K_UP:
                if self.world.move_player(self.world.player_x, self.world.player_y - 1):
                    enemy = self.create_enemy()
                    self.battle(enemy)
            elif event.key == pygame.K_DOWN:
                if self.world.move_player(self.world.player_x, self.world.player_y + 1):
                    enemy = self.create_enemy()
                    self.battle(enemy)
            elif event.key == pygame.K_ESCAPE:
                return "quit"
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
            if path:
                # Move along the path
                for next_x, next_y in path:
                    if self.world.move_player(next_x, next_y):
                        enemy = self.create_enemy()
                        self.battle(enemy)
                        if not self.player.is_alive():
                            self.show_game_over()
                            self.game_running = False
                            return "quit"
                    # Update display after each step
                    self.world.display_viewport()
                    self.player.draw(self.world.screen, player_screen_x, player_screen_y)
                    pygame.display.flip()
                    pygame.time.delay(100)  # Small delay between steps
        
        return "continue"

    def battle(self, enemy):
        self.current_enemy = enemy
        self.in_combat = True
        self.message = f"A {enemy.name} appears!"
        self.message_console.add_message(f"A {enemy.name} appears!")
        self.message_time = time.time()
        
        while enemy.is_alive() and self.player.is_alive():
            self.draw_combat_screen()
            
            # Handle input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # Check if console button was clicked
                        padding = 10
                        console_width = WINDOW_SIZE // 3
                        console_height = WINDOW_SIZE // 4
                        console_x = WINDOW_SIZE - console_width - padding
                        console_y = WINDOW_SIZE - console_height - padding
                        console_rect = pygame.Rect(console_x, console_y, console_width, console_height)
                        
                        if self.message_console.toggle_collapse(event.pos, console_rect):
                            continue  # Skip combat handling if console was clicked
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        choice = event.key - pygame.K_1 + 1
                        # Process combat choice
                        if choice == 1:  # Regular attack
                            damage = self.player.attack_target(enemy)
                            self.last_player_damage = damage
                            self.message = f"You deal {damage} damage to {enemy.name}"
                            self.message_console.add_message(f"You deal {damage} damage to {enemy.name}")
                            self.combat_animation_frame = 1
                        elif choice == 2:  # Strong attack
                            damage = self.player.strong_attack(enemy)
                            self.last_player_damage = damage
                            self.message = f"Strong attack! {damage} damage to {enemy.name}"
                            self.message_console.add_message(f"Strong attack! {damage} damage to {enemy.name}")
                            self.combat_animation_frame = 1
                        elif choice == 3:  # Heal
                            heal_amount = self.player.heal()
                            self.message = f"You heal for {heal_amount} HP"
                            self.message_console.add_message(f"You heal for {heal_amount} HP")
                        else:  # Flee
                            play_sound(SOUND_FLEE)
                            if random.random() < 0.5:
                                self.message = "You successfully fled!"
                                self.message_console.add_message("You successfully fled!")
                                self.in_combat = False
                                return
                            else:
                                self.message = "Failed to flee!"
                                self.message_console.add_message("Failed to flee!")
                        
                        self.message_time = time.time()
                        
                        if not enemy.is_alive():
                            self.handle_enemy_defeat(enemy)
                            break
                        
                        # Enemy's turn
                        damage = enemy.attack_target(self.player)
                        self.last_enemy_damage = damage
                        self.message = f"{enemy.name} deals {damage} damage to you"
                        self.message_console.add_message(f"{enemy.name} deals {damage} damage to you")
                        self.combat_animation_frame = 11
                        
                        if not self.player.is_alive():
                            self.message = "You have been defeated!"
                            self.message_console.add_message("You have been defeated!")
                            play_sound(SOUND_PLAYER_DEFEAT)
                            self.game_running = False
                            break
            
            # Draw message at the bottom
            if time.time() - self.message_time < self.message_duration:
                self.world.draw_text(self.message, (10, WINDOW_SIZE - 30), WHITE)
            pygame.display.flip()
            time.sleep(0.1)
        
        self.in_combat = False
        self.world.display_viewport()

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
                    self.message = "Inventory full! Some items were lost!"
                    self.message_console.add_message("Inventory full! Some items were lost!")
                    self.message_time = time.time()
        
        # Determine XP reward based on enemy type
        xp_reward = {
            "Dragon": 100,
            "Troll": 75,
            "Orc": 50,
            "Goblin": 25
        }.get(enemy.name, 50)  # Default to 50 if enemy type not found
        
        # Display victory message with loot
        if loot_message:
            self.message = f"Defeated! Found: {', '.join(loot_message)}! +{xp_reward} XP!"
            self.message_console.add_message(f"Defeated! Found: {', '.join(loot_message)}! +{xp_reward} XP!")
        else:
            self.message = f"Defeated! No loot found. +{xp_reward} XP!"
            self.message_console.add_message(f"Defeated! No loot found. +{xp_reward} XP!")
        
        play_sound(SOUND_ENEMY_DEFEAT)
        self.player.gain_exp(xp_reward)
        self.message_time = time.time()
        
        # Autosave after successful fight
        if save_game(self.player, self.world):
            time.sleep(1)  # Wait a bit so player can read loot message
            self.message = "Game autosaved!"
            self.message_console.add_message("Game autosaved!")
            self.message_time = time.time()

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
            if not self.show_inventory:
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

    def draw_combat_screen(self):
        """Draw the combat screen with enemy and player stats"""
        # Draw HP bars at the top
        hp_bar_width = 300
        hp_bar_height = 25
        padding = 10
        
        # Draw player HP bar first (on top)
        player_hp_percent = self.player.health / self.player.max_health
        player_hp_color = (0, 255, 0) if player_hp_percent > 0.5 else (255, 255, 0) if player_hp_percent > 0.2 else (255, 0, 0)
        
        # Draw player HP bar background
        pygame.draw.rect(self.world.screen, (200, 200, 200), 
                        (padding, padding, hp_bar_width, hp_bar_height))
        # Draw player HP bar fill
        pygame.draw.rect(self.world.screen, player_hp_color,
                        (padding, padding, hp_bar_width * player_hp_percent, hp_bar_height))
        # Draw player HP bar border
        pygame.draw.rect(self.world.screen, (255, 255, 255),
                        (padding, padding, hp_bar_width, hp_bar_height), 1)
        
        # Draw player name
        player_name = self.player.name
        name_surface = pygame.font.Font(None, 24).render(player_name, True, (0, 0, 0))
        name_rect = name_surface.get_rect()
        name_rect.x = padding + 5
        name_rect.centery = padding + hp_bar_height // 2
        self.world.screen.blit(name_surface, name_rect)
        
        # Draw player HP text
        player_hp_text = f"{self.player.health}/{self.player.max_health}"
        hp_surface = pygame.font.Font(None, 24).render(player_hp_text, True, (0, 0, 0))
        hp_rect = hp_surface.get_rect()
        hp_rect.right = padding + hp_bar_width - 5
        hp_rect.centery = padding + hp_bar_height // 2
        self.world.screen.blit(hp_surface, hp_rect)
        
        # Draw enemy HP bar second (below player)
        enemy_hp_percent = self.current_enemy.health / self.current_enemy.max_health
        enemy_hp_color = (0, 255, 0) if enemy_hp_percent > 0.5 else (255, 255, 0) if enemy_hp_percent > 0.2 else (255, 0, 0)
        
        # Draw enemy HP bar background
        pygame.draw.rect(self.world.screen, (200, 200, 200), 
                        (padding, padding + hp_bar_height + 5, hp_bar_width, hp_bar_height))
        # Draw enemy HP bar fill
        pygame.draw.rect(self.world.screen, enemy_hp_color,
                        (padding, padding + hp_bar_height + 5, hp_bar_width * enemy_hp_percent, hp_bar_height))
        # Draw enemy HP bar border
        pygame.draw.rect(self.world.screen, (255, 255, 255),
                        (padding, padding + hp_bar_height + 5, hp_bar_width, hp_bar_height), 1)
        
        # Draw enemy name
        enemy_name = self.current_enemy.name
        name_surface = pygame.font.Font(None, 24).render(enemy_name, True, (0, 0, 0))
        name_rect = name_surface.get_rect()
        name_rect.x = padding + 5
        name_rect.centery = padding + hp_bar_height + 5 + hp_bar_height // 2
        self.world.screen.blit(name_surface, name_rect)
        
        # Draw enemy HP text
        enemy_hp_text = f"{self.current_enemy.health}/{self.current_enemy.max_health}"
        hp_surface = pygame.font.Font(None, 24).render(enemy_hp_text, True, (0, 0, 0))
        hp_rect = hp_surface.get_rect()
        hp_rect.right = padding + hp_bar_width - 5
        hp_rect.centery = padding + hp_bar_height + 5 + hp_bar_height // 2
        self.world.screen.blit(hp_surface, hp_rect)
        
        # Draw combat options
        options = ["[1] Attack", "[2] Strong Attack", "[3] Heal", "[4] Flee"]
        x = 20
        y = WINDOW_SIZE - 100  # Position above the console
        spacing = 150  # Space between options
        
        for option in options:
            text_surface = pygame.font.Font(None, 24).render(option, True, (255, 255, 255))
            self.world.screen.blit(text_surface, (x, y))
            x += spacing
        
        # Draw message console at the bottom
        console_height = 150
        console_y = WINDOW_SIZE - console_height - 10
        self.message_console.draw(self.world.screen, 10, console_y, WINDOW_SIZE - 20, console_height)

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
            self.draw_health_bar(self.world.screen, self.world.player.health, 100, 50, 50, 10)
            self.draw_health_bar(self.world.screen, enemy.health, 100, 50, 150, 10)
            
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

    def draw_health_bar(self, screen, current, maximum, x, y, width, height):
        """Draw a health bar"""
        # Background
        pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height))
        
        # Health bar
        health_width = int((current / maximum) * width)
        health_color = (0, 255, 0) if current > maximum * 0.5 else (255, 165, 0) if current > maximum * 0.25 else (255, 0, 0)
        pygame.draw.rect(screen, health_color, (x, y, health_width, height))
        
        # Border
        pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 1)
        
        # Health text
        health_text = f"{current}/{maximum}"
        text_surface = self.font.render(health_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x + width/2, y + height/2))
        screen.blit(text_surface, text_rect)

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