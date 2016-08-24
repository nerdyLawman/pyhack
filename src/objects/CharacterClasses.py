import libtcodpy as libtcod
from interface import helpers as interface_helpers

class Fighter:
    #combat-related properties and methods
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def heal(self, amount):
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            interface_helpers.message(self.owner.name.capitalize() + ' attacks ' + target.name +
                    ' for ' + str(damage) + ' hit points.', libtcod.orange)
            target.fighter.take_damage(damage)
        else:
            interface_helpers.message(self.owner.name.capitalize() + ' attacks ' + target.name +
                    ' but it has no effect!', libtcod.cyan)
