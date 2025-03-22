import json
import random
from utils.constants import SOUND_SPELL_CAST, SOUND_SPELL_HIT, SOUND_HEAL

class SpellSystem:
    def __init__(self, game):
        self.game = game
        self.spell_database = self.load_spell_database()
        
    def load_spell_database(self):
        """Load spells from JSON file"""
        try:
            with open('data/spells.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading spell database: {e}")
            return {}
    
    def get_available_spells(self, character):
        """Get list of spells available to the character"""
        available_spells = []
        for spell_id, spell_data in self.spell_database.items():
            if character.level >= spell_data['level_requirement']:
                available_spells.append({
                    'id': spell_id,
                    **spell_data
                })
        return available_spells
    
    def can_cast_spell(self, character, spell_id):
        """Check if character can cast a spell"""
        if spell_id not in self.spell_database:
            return False, "Spell not found"
            
        spell = self.spell_database[spell_id]
        if character.level < spell['level_requirement']:
            return False, "Level too low"
            
        if character.mp < spell['mp_cost']:
            return False, "Not enough MP"
            
        return True, "Can cast"
    
    def cast_spell(self, caster, target, spell_id):
        """Cast a spell from caster to target"""
        if spell_id not in self.spell_database:
            return False, "Spell not found"
            
        spell = self.spell_database[spell_id]
        can_cast, message = self.can_cast_spell(caster, spell_id)
        
        if not can_cast:
            return False, message
            
        # Consume MP
        caster.mp -= spell['mp_cost']
        
        # Play spell cast sound
        self.game.play_sound(SOUND_SPELL_CAST)
        
        # Handle different spell types
        if spell['type'] == 'damage':
            damage = spell['damage']
            actual_damage = target.take_damage(damage)
            self.game.message_console.add_message(f"{caster.name} casts {spell['name']} for {actual_damage} damage!")
            self.game.play_sound(SOUND_SPELL_HIT)
            
            # Apply effects if any
            if 'effects' in spell:
                self.apply_spell_effects(target, spell['effects'])
                
        elif spell['type'] == 'heal':
            heal_amount = spell['heal_amount']
            target.heal(heal_amount)
            self.game.message_console.add_message(f"{caster.name} casts {spell['name']} and heals {target.name} for {heal_amount} HP!")
            self.game.play_sound(SOUND_HEAL)
            
        elif spell['type'] == 'buff':
            if 'effects' in spell:
                self.apply_spell_effects(target, spell['effects'])
            self.game.message_console.add_message(f"{caster.name} casts {spell['name']} on {target.name}!")
            
        return True, f"Cast {spell['name']}"
    
    def apply_spell_effects(self, target, effects):
        """Apply spell effects to target"""
        for effect_name, effect_data in effects.items():
            if effect_name == 'freeze':
                if random.random() < effect_data['chance']:
                    target.add_status_effect('frozen', effect_data['duration'])
                    self.game.message_console.add_message(f"{target.name} is frozen!")
                    
            elif effect_name == 'defense_up':
                target.add_status_effect('defense_up', effect_data['duration'], effect_data['amount'])
                self.game.message_console.add_message(f"{target.name}'s defense increased by {effect_data['amount']}!")
                
            elif effect_name == 'speed_up':
                target.add_status_effect('speed_up', effect_data['duration'], effect_data['amount'])
                self.game.message_console.add_message(f"{target.name}'s speed increased by {effect_data['amount']}!") 