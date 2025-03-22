import pygame
import random 
from utils.helpers import play_sound, play_wave_sound
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, BLUE,
    SOUND_ATTACK, SOUND_HIT, SOUND_MISS, SOUND_DEATH,
    SOUND_VICTORY, SOUND_COMBAT_START, SOUND_COMBAT_END,
    WINDOW_SIZE, YELLOW, SOUND_HEAL
)
from entities.character import Character
from ui.bar import Bar
from ui.console import MessageConsole

class CombatSystem:
    def __init__(self, game):
        self.game = game
        self.world = game.world  # Add world reference
        self.in_combat = False
        self.current_enemy = None
        self.turn_order = []
        self.selected_option = 0
        self.combat_options = ["Attack", "Strong Attack", "Heal", "Flee"]
        self.special_moves = []  # Will be populated with player's special moves
        self.combat_animation_frame = 0

    def start_combat(self, enemy):
        """Start a new combat encounter"""
        self.in_combat = True
        self.current_enemy = enemy
        self.turn_order = self.determine_turn_order()
        self.selected_option = 0
        self.combat_options = ["Attack", "Strong Attack", "Heal", "Flee"]
        self.special_moves = self.game.player.get_special_moves()
        
        # Add initial combat message
        self.game.message_console.add_message(f"Combat started with {enemy.name}!")
        
        # Stop any currently playing sounds and play combat start sound
        try:
            pygame.mixer.stop()  # Stop all currently playing sounds
            pygame.mixer.music.stop()  # Stop any playing music
            pygame.mixer.music.unload()  # Unload any loaded music
            play_wave_sound(SOUND_COMBAT_START)
        except Exception as e:
            print(f"Failed to play combat sound: {e}")

    def end_combat(self):
        """End the current combat encounter"""
        self.in_combat = False
        self.current_enemy = None
        self.turn_order = []
        self.selected_option = 0
        
        # Stop combat music
        try:
            pygame.mixer.stop()
        except Exception as e:
            print(f"Failed to stop combat sound: {e}")

    def determine_turn_order(self):
        """Determine the order of turns based on speed"""
        characters = [self.game.player, self.current_enemy]
        return sorted(characters, key=lambda x: x.speed, reverse=True)

    def handle_combat(self, enemy):
        """Handle combat with an enemy"""
        # Initialize combat state
        combat_active = True
        current_turn = "player"  # Start with player's turn
        
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
                        self.game.message_console.add_message("You fled from combat!")
                        return False
                    
                    if current_turn == "player" and event.key == pygame.K_SPACE:
                        # Player attacks
                        damage = random.randint(5, 15)
                        enemy.health -= damage
                        self.game.message_console.add_message(f"You deal {damage} damage to {enemy.name}")
                        
                        # Check if enemy is defeated
                        if enemy.health <= 0:
                            self.game.message_console.add_message(f"{enemy.name} is defeated!")
                            combat_active = False
                            return True
                        
                        current_turn = "enemy"
            
            # Enemy's turn
            if current_turn == "enemy":
                # Enemy attacks
                enemy_damage = random.randint(3, 10)
                self.world.player.health -= enemy_damage
                self.game.message_console.add_message(f"{enemy.name} deals {enemy_damage} damage to you")
                
                # Check if player is defeated
                if self.world.player.health <= 0:
                    self.game.message_console.add_message("You are defeated!")
                    combat_active = False
                    return False
                
                current_turn = "player"
            
            # Draw combat scene
            self.world.screen.blit(combat_surface, (0, 0))
            
            # Draw combatants
            self.world.draw_sprite(self.world.screen, self.world.player.x, self.world.player.y, "player")
            self.world.draw_sprite(self.world.screen, enemy.x, enemy.y, enemy.name)
            
            # Draw health bars
            self.game.bar_renderer.draw_health_bar(self.screen, self.world.player, 10, 10)
            self.game.bar_renderer.draw_health_bar(self.screen, enemy, SCREEN_HEIGHT - 210, 10)
            
            # Draw XP bar for player
            self.game.bar_renderer.draw_xp_bar(self.screen, self.world.player, 10, 35)
            
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
            
            # Draw message console
            console_height = 150
            self.game.message_console.draw(self.screen, 0, SCREEN_HEIGHT - console_height, SCREEN_WIDTH, console_height)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return False

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
                # Handle number keys (1-4)
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    self.selected_option = event.key - pygame.K_1  # Convert key to 0-based index
                    return self.handle_player_action()
                # Handle arrow keys and enter
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.combat_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.combat_options)
                elif event.key == pygame.K_RETURN:
                    return self.handle_player_action()
        else:
            # Enemy's turn
            return self.handle_enemy_turn()

        return "continue"

    def handle_player_action(self):
        """Handle the player's chosen action"""
        action = self.combat_options[self.selected_option]
        
        if action == "Attack":
            damage = self.game.player.attack
            actual_damage = self.current_enemy.take_damage(damage)
            self.game.message_console.add_message(f"You deal {actual_damage} damage to {self.current_enemy.name}!")
            play_wave_sound(SOUND_ATTACK)
        
        elif action == "Strong Attack":
            if self.game.player.mp >= 10:  # Check if player has enough MP
                self.game.player.mp -= 10  # Consume MP
                damage = self.game.player.attack * 2  # Double damage
                actual_damage = self.current_enemy.take_damage(damage)
                self.game.message_console.add_message(f"You perform a strong attack for {actual_damage} damage!")
                play_wave_sound(SOUND_HIT)
            else:
                self.game.message_console.add_message("Not enough MP for strong attack!")
                play_wave_sound(SOUND_MISS)
                return "continue"
        
        elif action == "Heal":
            if self.game.player.mp >= 20:  # Check if player has enough MP
                self.game.player.mp -= 20  # Consume MP
                heal_amount = 50
                self.game.player.heal(heal_amount)
                self.game.message_console.add_message(f"You heal for {heal_amount} HP!")
                play_wave_sound(SOUND_HEAL)
            else:
                self.game.message_console.add_message("Not enough MP to heal!")
                play_wave_sound(SOUND_MISS)
                return "continue"
        
        elif action == "Flee":
            if random.random() < 0.5:  # 50% chance to flee
                self.game.message_console.add_message("You successfully flee!")
                play_wave_sound(SOUND_COMBAT_END)
                self.end_combat()
                return "continue"
            else:
                self.game.message_console.add_message("Failed to flee!")
                play_wave_sound(SOUND_MISS)

        # Regenerate 2 MP per turn
        self.game.player.mp = min(self.game.player.max_mp, self.game.player.mp + 2)
        if self.game.player.mp < self.game.player.max_mp:
            self.game.message_console.add_message("You recover 2 MP!")

        # Rotate turn order
        self.turn_order = self.turn_order[1:] + [self.turn_order[0]]
        return "continue"

    def handle_enemy_turn(self):
        """Handle the enemy's turn"""
        if not self.current_enemy:
            return False
            
        # Check if enemy can use a special move
        if random.random() < 0.2 and self.current_enemy.special_moves:
            # Randomly select a special move
            move = random.choice(self.current_enemy.special_moves)
            if self.current_enemy.can_use_special_move(move):
                # Use the special move
                self.current_enemy.use_special_move(move, self.game.player)
                play_wave_sound(SOUND_HIT)
                self.game.message_console.add_message(f"{self.current_enemy.name} used {move['name']}!")
            else:
                # Fall back to normal attack if can't use special move
                damage = self.current_enemy.attack
                self.game.player.take_damage(damage)
                play_wave_sound(SOUND_ATTACK)
                self.game.message_console.add_message(f"{self.current_enemy.name} attacks for {damage} damage!")
        else:
            # Normal attack
            damage = self.current_enemy.attack
            self.game.player.take_damage(damage)
            play_wave_sound(SOUND_ATTACK)
            self.game.message_console.add_message(f"{self.current_enemy.name} attacks for {damage} damage!")
            
        # Regenerate enemy MP
        self.current_enemy.mp = min(self.current_enemy.max_mp, self.current_enemy.mp + 2)
        
        # Rotate turn order
        self.turn_order = self.turn_order[1:] + [self.turn_order[0]]
        return True

    def handle_enemy_defeat(self):
        """Handle enemy defeat"""
        if self.current_enemy:
            self.game.handle_enemy_defeat(self.current_enemy)
            self.current_enemy = None
            self.in_combat = False

    def draw_combat_screen(self):
        """Draw the combat screen"""
        # Draw the world viewport
        self.game.world.display_viewport(self.game.world.screen, self.game.world.player_x, self.game.world.player_y)
        
        # Draw the player character
        player_screen_x = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        player_screen_y = (self.world.VIEWPORT_SIZE // 2) * self.world.CELL_SIZE
        self.game.player.draw(self.game.screen, player_screen_x, player_screen_y)
        
        # Draw the enemy if it exists
        if self.current_enemy:
            # Position enemy on the right side of the player
            enemy_screen_x = player_screen_x + 100  # 100 pixels to the right of player
            enemy_screen_y = player_screen_y
            self.current_enemy.draw(self.game.screen, enemy_screen_x, enemy_screen_y)
        
        # Draw combat UI elements
        # Draw player status bar at the top
        self.game.bar_renderer.draw_health_bar(self.game.screen, self.game.player, 10, 10)
        self.game.bar_renderer.draw_mp_bar(self.game.screen, self.game.player, 10, 35)
        self.game.bar_renderer.draw_xp_bar(self.game.screen, self.game.player, 10, 60)
        
        # Draw enemy health bar if enemy exists
        if self.current_enemy:
            self.game.bar_renderer.draw_health_bar(self.game.screen, self.current_enemy, 10, 85)
        
        # Draw combat options with number key shortcuts
        for i, option in enumerate(self.combat_options):
            color = WHITE if i == self.selected_option else (200, 200, 200)
            # Add number key shortcut to each option
            option_text = f"{i+1} - {option}"
            text = self.game.font.render(option_text, True, color)
            self.game.screen.blit(text, (20, 120 + i * 30))
        
        # Draw turn order text
        turn_text = f"Turn: {'Player' if self.turn_order and self.turn_order[0] == self.game.player else self.current_enemy.name if self.current_enemy else 'Unknown'}"
        text = self.game.font.render(turn_text, True, WHITE)
        self.game.screen.blit(text, (20, 180))
        
        # Draw message console at the bottom
        console_height = 150
        self.game.message_console.draw(self.game.screen, 0, SCREEN_HEIGHT - console_height, SCREEN_WIDTH, console_height)

    def draw_combat_message(self):
        """Draw the current combat message"""
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.message_time < self.message_duration:
            self.game.draw_text(self.message, 10, 420)

    def update(self):
        """Update combat system state"""
        # Update any ongoing animations or effects
        self.update_animations()

    def update_animations(self):
        """Update combat animations"""
        # Update combat animation frame
        self.combat_animation_frame = (self.combat_animation_frame + 1) % 60  # 60 frames per second