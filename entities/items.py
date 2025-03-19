class Item:
    def __init__(self, name, item_type, value=0, stats=None, rarity="common"):
        self.name = name
        self.item_type = item_type  # "gold", "resource", "weapon", "armor"
        self.rarity = rarity
        self.value = value
        self.stats = stats or {}  # Dictionary of stat bonuses (attack, defense, etc.)
        self.bonus = value  # For backward compatibility
    
    def to_dict(self):
        """Convert item to dictionary for saving"""
        return {
            "name": self.name,
            "item_type": self.item_type,
            "rarity": self.rarity,
            "value": self.value,
            "stats": self.stats
        }
    
    @staticmethod
    def from_dict(data):
        """Create item from dictionary data"""
        return Item(
            data["name"],
            data["item_type"],
            data["value"],
            data["stats"],
            data["rarity"]
        )

class Inventory:
    def __init__(self):
        self.items = []
        self.gold = 0
        self.capacity = 20  # Maximum number of items
    
    def add_item(self, item):
        """Add an item to inventory if there's space"""
        if item.item_type == "gold":
            self.gold += item.value
            return True
        if len(self.items) < self.capacity:
            self.items.append(item)
            return True
        return False
    
    def remove_item(self, index):
        """Remove item at given index"""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def to_dict(self):
        """Convert inventory to dictionary for saving"""
        return {
            "items": [item.to_dict() for item in self.items],
            "gold": self.gold,
            "capacity": self.capacity
        }
    
    @staticmethod
    def from_dict(data):
        """Create inventory from dictionary data"""
        inventory = Inventory()
        inventory.gold = data["gold"]
        inventory.capacity = data["capacity"]
        inventory.items = [Item.from_dict(item_data) for item_data in data["items"]]
        return inventory 