class Character:
    def __init__(self, name, health=100, attack=10, defense=5, speed=10, mp=0, character_type='player'):
        self.name = name
        self.max_health = health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.max_mp = mp
        self.mp = mp
        self.character_type = character_type
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100
        self.kills = {}
        self.equipped_weapon = None
        self.equipped_armor = None
        self.special_moves = []
        self.status_effects = []
        self.monster_data = None  # Store monster data for enemies

    def is_alive(self):
        """Check if the character is alive"""
        return self.health > 0

    def take_damage(self, damage):
        """Apply damage to the character"""
        # Calculate actual damage after defense
        actual_damage = max(1, damage - self.defense)
        self.health = max(0, self.health - actual_damage)
        return actual_damage

    def heal(self, amount):
        """Heal the character"""
        self.health = min(self.max_health, self.health + amount)
        return amount

    def gain_exp(self, amount):
        """Gain experience points and level up if possible"""
        self.exp += amount
        while self.exp >= self.exp_to_next_level:
            self.level_up()

    def level_up(self):
        """Level up the character"""
        self.level += 1
        self.exp -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        
        # Increase stats
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        self.defense += 1
        self.speed += 1
        self.max_mp += 5
        self.mp = self.max_mp

    def record_kill(self, enemy_name):
        """Record a kill for tracking purposes"""
        self.kills[enemy_name] = self.kills.get(enemy_name, 0) + 1

    def get_special_moves(self):
        """Get available special moves"""
        if self.character_type == 'enemy' and self.monster_data:
            return self.monster_data['special_moves']
        return self.special_moves

    def can_use_special_move(self, move):
        """Check if the character can use a special move"""
        return self.mp >= move['mp_cost']

    def use_special_move(self, move):
        """Use a special move and consume MP"""
        if self.can_use_special_move(move):
            self.mp -= move['mp_cost']
            return True
        return False

    def add_status_effect(self, effect):
        """Add a status effect to the character"""
        self.status_effects.append(effect)

    def remove_status_effect(self, effect):
        """Remove a status effect from the character"""
        if effect in self.status_effects:
            self.status_effects.remove(effect)

    def update_status_effects(self):
        """Update and remove expired status effects"""
        self.status_effects = [effect for effect in self.status_effects if not effect.is_expired()]
        for effect in self.status_effects:
            effect.apply(self) 