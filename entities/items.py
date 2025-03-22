class Item:
    def __init__(self, name, item_type, value=0, stats=None, rarity="common", stackable=False, max_stack=1):
        self.name = name
        self.item_type = item_type.lower()  # Convert to lowercase for consistent comparison
        self.rarity = rarity
        self.value = value
        self.stats = stats or {}  # Dictionary of stat bonuses (attack, defense, etc.)
        self.bonus = self.get_bonus()  # Calculate bonus based on stats
        self.stackable = stackable
        self.max_stack = max_stack
        self.quantity = 1
    
    def get_bonus(self, stat_type=None, default=0):
        """Get the item's bonus for a specific stat type"""
        if not self.stats:
            return self.value if stat_type is None else default
            
        if stat_type:
            return self.stats.get(stat_type, default)
            
        # For backward compatibility
        if self.item_type == "weapon" and "attack" in self.stats:
            return self.stats["attack"]
        elif self.item_type == "armor" and "defense" in self.stats:
            return self.stats["defense"]
        elif "bonus" in self.stats:
            return self.stats["bonus"]
        return default
    
    def to_dict(self):
        """Convert item to dictionary for saving"""
        return {
            "name": self.name,
            "item_type": self.item_type,
            "rarity": self.rarity,
            "value": self.value,
            "stats": self.stats,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "quantity": self.quantity
        }
    
    @staticmethod
    def from_dict(data):
        """Create item from dictionary data"""
        item = Item(
            data["name"],
            data["item_type"],
            data["value"],
            data.get("stats", {}),
            data.get("rarity", "common"),
            data.get("stackable", False),
            data.get("max_stack", 1)
        )
        item.quantity = data.get("quantity", 1)
        return item

class Inventory:
    def __init__(self):
        self.items = []
        self.gold = 0
        self.max_items = 20  # Maximum number of items the inventory can hold
    
    def add_item(self, item):
        """Add an item to the inventory"""
        if item.item_type == "gold":
            self.gold += item.value
            return True
            
        # Try to stack with existing items if stackable
        if item.stackable:
            for existing_item in self.items:
                if (existing_item.name == item.name and 
                    existing_item.quantity < existing_item.max_stack):
                    # Calculate how many can be added to this stack
                    space_in_stack = existing_item.max_stack - existing_item.quantity
                    amount_to_add = min(item.quantity, space_in_stack)
                    
                    existing_item.quantity += amount_to_add
                    item.quantity -= amount_to_add
                    
                    if item.quantity <= 0:
                        return True
                    
        # If we still have items to add and inventory isn't full
        if len(self.items) < self.max_items:
            self.items.append(item)
            return True
        return False
    
    def remove_item(self, item, amount=1):
        """Remove an item from the inventory"""
        if item.item_type == "gold":
            if self.gold >= amount:
                self.gold -= amount
                return True
            return False
            
        if item.stackable:
            for existing_item in self.items:
                if existing_item.name == item.name:
                    if existing_item.quantity > amount:
                        existing_item.quantity -= amount
                        return True
                    elif existing_item.quantity == amount:
                        self.items.remove(existing_item)
                        return True
        else:
            if item in self.items:
                self.items.remove(item)
                return True
        return False
    
    def has_item(self, item_name):
        """Check if an item exists in the inventory by name"""
        return any(item.name == item_name for item in self.items)
    
    def get_item(self, item_name):
        """Get an item from the inventory by name"""
        for item in self.items:
            if item.name == item_name:
                return item
        return None
    
    def get_item_count(self, item_name):
        """Get the total quantity of an item in the inventory"""
        total = 0
        for item in self.items:
            if item.name == item_name:
                total += item.quantity
        return total
    
    def to_dict(self):
        """Convert inventory to dictionary for saving"""
        return {
            'items': [item.to_dict() for item in self.items],
            'gold': self.gold,
            'max_items': self.max_items
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create inventory from dictionary when loading"""
        inventory = cls()
        inventory.items = [Item.from_dict(item_data) for item_data in data['items']]
        inventory.gold = data['gold']
        inventory.max_items = data.get('max_items', 20)  # Default to 20 if not present
        return inventory 