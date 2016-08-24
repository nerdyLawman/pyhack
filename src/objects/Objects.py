import libtcodpy as libtcod
from map import mapconfig
from interface import helpers as interface_helpers
import math
import gameconfig

def is_blocked(x, y):
    #first test the map tile
    if mapconfig.stagemap[x][y].blocked:
        return True

    #now check for any blocking objects
    for object in  gameconfig.ACTIVE_OBJECTS:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

class Object:
    # generic object
    def __init__(self, con, x, y, char, name, color, blocks=False, fighter=None,
                 ai=None, item=None):
      self.con = con
      self.x = x
      self.y = y
      self.char = char
      self.name = name
      self.color = color
      self.blocks = blocks

      self.fighter = fighter
      if self.fighter:
          self.fighter.owner = self

      self.ai = ai
      if self.ai:
          self.ai.owner = self

      self.item = item
      if self.item:
          self.item.owner = self

    def move(self, dx, dy):
      if not is_blocked(self.x + dx, self.y + dy):
          self.x += dx
          self.y += dy

    def move_towards(self, target_x, target_y):
      dx = target_x - self.x
      dy = target_y - self.y
      distance = math.sqrt(dx ** 2 + dy ** 2)

      dx = int(round(dx / distance))
      dy = int(round(dx / distance))
      self.move(dx, dy)

    def distance_to(self, other):
      dx = other.x - self.x
      dy = other.y - self.y
      return math.sqrt(dx ** 2 + dy ** 2)

    def send_to_back(self):
        gameconfig.ACTIVE_OBJECTS.remove(self)
        gameconfig.ACTIVE_OBJECTS.insert(0, self)

    def draw(self):
        if libtcod.map_is_in_fov(gameconfig.FOV_MAP, self.x, self.y):
            libtcod.console_set_default_foreground(self.con, self.color)
            libtcod.console_set_char_background(self.con, self.x, self.y,
                                                self.color, libtcod.BKGND_SET)
            libtcod.console_put_char(self.con, self.x, self.y, self.char,
                                     libtcod.BKGND_NONE)

    def clear(self):
        libtcod.console_put_char(self.con, self.x, self.y, ' ',
                                 libtcod.BKGND_NONE)


class Item:
    # an item that can be picked up and used
    def __init__(self, use_function=None):
        self.use_function = use_function

    def pick_up(self):
        #add to inv and remove from map
        if len(inventory) >= 26:
            interface_helpers.message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.pink)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            interface_helpers.message('You picked up a ' + self.owner.name + '!', libtcod.green)

    def use(self):
        if self.use_function is None:
            interface_helpers.message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)



