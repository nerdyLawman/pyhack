import config
import libtcodpy as libtcod
import math
import textwrap
import shelve

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

#exp and level
LEVEL_UP_BASE = 100
LEVEL_UP_FACTOR = 50

INVENTORY_WIDTH = 50
LIGHTNING_RANGE = 5
LIGHTNING_DAMAGE = 10

FIREBALL_RADIUS = 4
FIREBALL_DAMAGE = 11

CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8

HEAL_AMOUNT = 6

MAP_WIDTH = 80
MAP_HEIGHT = 43

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

FOV_ALGO = 2
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 8

selected = 0

color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 100)
color_light_ground = libtcod.Color(200, 180, 50)


class Tile:
    # map tile and properties
    def __init__(self, blocked, block_sight = None):
        self.explored = False
        self.blocked = blocked
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class Rect:
    # rectangular room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        return (self.x1 < other.x2 and self.x2 >= other.x1 and
            self.y1 <= other.y2 and self.y2 >= other.y1)

def create_room(room):
    global stagemap
    for x in range(room.x1+1, room.x2):
        for y in range(room.y1+1, room.y2):
            stagemap[x][y].blocked = False
            stagemap[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global stagemap
    # horizontal tunnel
    for x in range(min(x1, x2), max(x1, x2) + 1):
        stagemap[x][y].blocked = False
        stagemap[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global stagemap
    # vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        stagemap[x][y].blocked = False
        stagemap[x][y].block_sight = False

def make_map():
    global stagemap, objects, stairs
    objects = [player]

    # fill map with unblocked tiles
    stagemap = [[ Tile(True)
        for y in range(config.MAP_HEIGHT)]
            for x in range(config.MAP_WIDTH)]

    rooms = []
    num_rooms = 0

    for r in range(config.MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, config.MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, config.MAP_HEIGHT - h - 1)

        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            #this means there are no intersections, so this room is valid

            #"paint" it to the map's tiles
            create_room(new_room)

            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel

                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            #finally, append the new room to the list
            place_objects(new_room)
            rooms.append(new_room)
            num_rooms += 1

    #create stairs
    stairs = Object(con, new_x, new_y, '<', 'stairs', libtcod.black)
    objects.append(stairs)
    stairs.send_to_back()

class Object:
  # generic object
  def __init__(self, con, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None):
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

  def distance(self, x, y):
      return math.sqrt((x - self.x) **  2 + (y - self.y) ** 2)

  def send_to_back(self):
      global objects
      objects.remove(self)
      objects.insert(0, self)

  def draw(self):
      if libtcod.map_is_in_fov(fov_map, self.x, self.y):
          libtcod.console_set_default_foreground(self.con, self.color)
          libtcod.console_set_char_background(self.con, self.x, self.y, self.color, libtcod.BKGND_SET)
          libtcod.console_put_char(self.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

  def clear(self):
      libtcod.console_put_char(self.con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Item:
    # an item that can be picked up and used
    def __init__(self, use_function=None):
        self.use_function = use_function

    def pick_up(self):
        global item_count
        #add to inv and remove from map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.pink)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)
            item_count -= 1

    def drop(self):
        global item_count
        #drop objects
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped ' + self.owner.name + '.', libtcod.yellow)
        item_count += 1

    def use(self):
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)

def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
	    message('You are already at full health.', libtcod.red)
	    return('cancelled')
    message('your wounds feel better.', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
    #find nearest enemy and shock them with your deviant behaviour
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:
        message('No enemy is close enough to be shocked by you.', libtcod.red)
        return 'cancelled'
    message('A lightning bold strikes the ' + monster.name + ', ZAP! For ' + str(LIGHTNING_DAMAGE) + ' damage.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_fireball():
    message('Left-click a target tile, right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The fireball explodes burning everything in range.', libtcod.orange)

    for obj in objects:
        #damage everything in radius
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hp.', libtcod.orange)
            obj.fighter.take_damage(FIREBALL_DAMAGE)

def cast_confusion():
    message('left-click an enemy to confuse. Right-click to cancel.', libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'cancelled'
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster
    message('The monster feels very confused', libtcod.light_green)

class Fighter:
    #combat-related properties and methods
    def __init__(self, hp, defense, power, xp, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.xp = xp
        self.death_function = death_function

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            # gain exp
            if self.owner != player:
                player.fighter.xp += self.xp
                check_level_up()
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
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.', libtcod.orange)
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!', libtcod.cyan)

class BaseMonster:
    #basic monster ai
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

class ConfusedMonster:
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
        else:
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confuse', libtcod.red)

def player_death(player):
    global game_state
    message('You died!', libtcod.white)
    game_state = 'dead'
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster):
    global monster_count
    message(monster.name.capitalize() + ' is dead! You gain ' + str(monster.fighter.xp) + 'XP!', libtcod.cyan)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster_count -= 1
    monster.send_to_back()

def closest_monster(max_range):
    #find closest enemy to max range and in FOV
    closest_enemy = None
    closest_dist = max_range + 1

    for obj in objects:
        if obj.fighter and not obj == player and libtcod.map_is_in_fov(fov_map, obj.x, obj.y):
            dist = player.distance_to(obj)
            if dist < closest_dist:
                closest_enemy = obj
                closest_dist = dist
    return closest_enemy

def target_tile(max_range=None):
    global key, mouse
    while True:
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
        render_all()

        (x, y) = (mouse.cx, mouse.cy)
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
            (max_range is None or player.distance(x, y) <= max_range)):
            return(x, y)
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return(None, None)

def target_monster(max_range=None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None:
            return None

        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj

def player_move_or_attack(dx, dy):
    global fov_recompute

    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    #try to find an attackable object there
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    #attack if target found, move otherwise
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True

def check_level_up():
    level_up_xp = LEVEL_UP_BASE + player.level + LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        #level up
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('Your skills increas. LEVEL UP! Now at level: ' + str(player.level) + '.', libtcod.yellow)

        choice = 'no selection'
        while choice == 'no selection':
            choice = menu('Level up! Chose a stat to raise!\n',
                ['Constitution: +10 HP', 'Stregnth: +1 STR', 'Agility: +1 DEX'], 24)
        if choice == 0:
            player.fighter.max_hp += 10
            player.fighter.hp += 10
        elif choice == 1:
            player.fighter.power += 1
        elif choice == 2:
            player.fighter.defense += 1

def place_objects(room):
    # random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, config.MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        if not is_blocked(x, y):
            monster_ai = BaseMonster()
            if libtcod.random_get_int(0, 0, 100) < 80:  #80% chance of getting an orc
                #create an orc
                orc_fighter = Fighter(hp=6, defense=0, power=2, xp=10, death_function=monster_death)
                monster = Object(con, x, y, 'O', 'Orc', libtcod.desaturated_green, blocks=True, fighter=orc_fighter, ai=monster_ai)
            else:
                #create a troll
                troll_fighter = Fighter(hp=10, defense=0, power=3, xp=30, death_function=monster_death)
                monster = Object(con, x, y, 'T', 'Troll', libtcod.darker_purple, blocks=True, fighter=troll_fighter, ai=monster_ai)

            objects.append(monster)

    num_items = libtcod.random_get_int(0, 0, config.MAX_ROOM_ITEMS)
    for i in range(num_items):
        #place an item randomly
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y1-1)

        if not is_blocked(x, y):
            dice = libtcod.random_get_int(0, 0, 100)
            if dice < 70:
                item_component = Item(use_function = cast_heal)
                item = Object(con, x, y, '!', 'healing potion', libtcod.cyan, item=item_component)
            elif dice < 70+10:
                item_component = Item(use_function = cast_lightning)
                item = Object(con, x, y, 'Z', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
            elif dice < 70+10+10:
                item_component = Item(use_function=cast_fireball)
                item = Object(con, x, y, '#', 'scroll of fireball', libtcod.light_red, item=item_component)
            else:
                item_component = Item(use_function = cast_confusion)
                item = Object(con, x, y, '*', 'scroll of confusion', libtcod.light_orange, item=item_component)
            objects.append(item)
            item.send_to_back()

def is_blocked(x, y):
    #first test the map tile
    if stagemap[x][y].blocked:
        return True

    #now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

def render_all():
    global fov_map
    global fov_recompute

    color_dark_wall = config.color_dark_wall
    color_light_wall = config.color_light_wall
    color_dark_ground = config.color_dark_ground
    color_light_ground = config.color_light_ground

    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, config.TORCH_RADIUS, config.FOV_LIGHT_WALLS, config.FOV_ALGO)
        #go through all tiles, and set their background color
        for y in range(config.MAP_HEIGHT):
            for x in range(config.MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = stagemap[x][y].block_sight
                if not visible:
                    if stagemap[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, config.color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, config.color_dark_ground, libtcod.BKGND_SET)
                else:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, config.color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, config.color_light_ground, libtcod.BKGND_SET)
                    stagemap[x][y].explored = True

    #draw all objects in the list
    for obj in objects:
        if obj != player:
            obj.draw()
    player.draw()

    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    # dungeon level
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level: ' + str(dungeon_level))
    # health bar
    render_bar(1, 1, config.BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)
    # monsters bar
    render_bar(1, 3, config.BAR_WIDTH, 'MONSTERS', monster_count, start_monster_count, libtcod.light_blue, libtcod.darker_blue)
    # items bar
    render_bar(1, 5, config.BAR_WIDTH, 'ITEMS', item_count, start_item_count, libtcod.light_violet, libtcod.darker_violet)
    # mouse look
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, SCREEN_WIDTH/4, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
    libtcod.console_blit(panel, 0, 0, config.SCREEN_WIDTH, config.PANEL_HEIGHT, 0, 0, config.PANEL_Y)

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a status bar
    bar_width = int(float(value) / maximum * total_width)
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))

    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, config.MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

def menu(header, options, width):
    global selected
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options!')

    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    #create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    #blit window contents
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    #present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_DOWN:
        if selected < len(options):
            selected += 1
        else:
            selected = 1
    elif key.vk == libtcod.KEY_UP:
        if selected > 1:
            selected -= 1
        else:
            selected = len(options)
    elif key.vk == libtcod.KEY_ENTER:
        return(selected-1)
    elif key.vk == libtcod.KEY_ESCAPE:
        return None
    libtcod.console_set_default_background(window, libtcod.light_yellow)
    libtcod.console_rect(window, 0, selected-1+header_height, 100, 1, True, libtcod.BKGND_SET)
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    # convert ascii to index
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return 'no selection'

def inventory_menu(header):
    # inventory
    if len(inventory) == 0:
        options = ['Inventory is empty']
    else:
        options = [item.name for item in inventory]
    index = 'no selection'
    #return selected item
    while index == 'no selection':
        index = menu(header, options, INVENTORY_WIDTH)
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

def message(new_msg, color=libtcod.white):
    new_msg_lines = textwrap.wrap(new_msg, config.MSG_WIDTH)

    for line in new_msg_lines:
        if len(game_msgs) == config.MSG_HEIGHT:
            del game_msgs[0]
        game_msgs.append((line, color))

def message_box(text, width=50):
    menu(text, [], width)

def get_names_under_mouse():
    global mouse
    (x, y) = (mouse.cx, mouse.cy)
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
    names = ', '.join(names)
    return names.capitalize()

def handle_keys():
    global playerx, playery, fov_recompute, key

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        selected = 0
        return('exit')  #exit game

    # movement
    if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
        player_move_or_attack(0, -1)
    elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
        player_move_or_attack(0, 1)
    elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
        player_move_or_attack(-1, 0)
    elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
        player_move_or_attack(1, 0)
    elif key.vk == libtcod.KEY_KP7:
        player_move_or_attack(-1, -1)
    elif key.vk == libtcod.KEY_KP9:
        player_move_or_attack(1, -1)
    elif key.vk == libtcod.KEY_KP1:
        player_move_or_attack(-1, 1)
    elif key.vk == libtcod.KEY_KP3:
        player_move_or_attack(1, 1)
    elif key.vk == libtcod.KEY_KP5:
        message('You wait a turn for the darkness to close in on you.', libtcod.white)
        pass
    else:
        #other keys
        key_char = chr(key.c)
        if key_char == 'g':
            #pick up an item
            for obj in objects:
                if obj.x == player.x and obj.y == player.y and obj.item:
                    obj.item.pick_up()
                    break
        if key_char == 'i':
            #display inventory
            selection = -1
            chosen_item = inventory_menu('Press the key next to an item to use it, or ESC to cancel\n')
            if chosen_item is not None:
                chosen_item.use()
        if key_char == 'd':
            chosen_item = inventory_menu('Press the key next to an item to drop it.\n')
            if chosen_item is not None:
                chosen_item.drop()
        if key_char == 'c':
            # show character info
            level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
            message_box('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
                '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
                '\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense), 24)
        if key_char == 'f':
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        if key_char == ',' or key_char == '.':
            #go down stairs if player is on them
            if stairs.x == player.x and stairs.y == player.y:
                next_level()

        return('no turn')

    return('playing')

def main_menu():
    #img = libtcod.image_load('bgk.png')
    while not libtcod.console_is_window_closed():
        choice = menu('', ['New Game', 'Continue', 'Quit'], 24)
        if choice == 0:
            new_game()
            play_game()
        if choice == 1:
            try:
                load_game()
            except:
                message_box('\n No saved gamedata to load.\n', 24)
                continue
            play_game()
        elif choice == 2:
            break

def new_game():
    global player, panel, inventory, game_msgs, game_state, dungeon_level, player_level
    # player
    fighter_component = Fighter(hp=30, defense=1, power=5, xp=0, death_function=player_death)
    player = Object(con, 0, 0, '@', 'Hero', libtcod.white, blocks=True, fighter=fighter_component)
    dungeon_level = 1
    player.level = 1
    make_map()

    #gui
    panel = libtcod.console_new(config.SCREEN_WIDTH, config.PANEL_HEIGHT)

    game_state = 'playing'
    inventory = []
    game_msgs = []
    initialize_fov()
    initialize_gamedata()
    #a warm welcoming message!
    message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)

def initialize_fov():
    global fov_recompute, fov_map
    libtcod.console_clear(con)
    fov_recompute = True
    fov_map = libtcod.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
    for y in range(config.MAP_HEIGHT):
        for x in range(config.MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not stagemap[x][y].block_sight, not stagemap[x][y].blocked)

def initialize_gamedata():
    global start_monster_count, monster_count, start_item_count, item_count
    start_monster_count = 0
    start_item_count = 0
    for obj in objects:
        if obj.ai:
            start_monster_count += 1
        if obj.item:
            start_item_count += 1
    monster_count = start_monster_count
    item_count = start_item_count

def save_game():
    #open new empty shelve - overwrites old
    file = shelve.open('savegame', 'n')
    file['map'] = stagemap
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['stairs_index'] = objects.index(stairs)
    file['dungron_level'] = dungeon_level
    file.close()

def load_game():
    #open previously saved shelve
    global stagemap, objects, player, inventory, game_msgs, game_state, stairs, dungeon_level
    file = shelve.open('savegame', 'r')
    stagemap = file['map']
    objects = file['objects']
    player = objects[file['player_index']]
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    stairs = objects[file['stairs_index']]
    dungeon_level = file['dungeon_level']
    file.close()

    initialize_fov()

def play_game():
    global key, mouse
    player_action = None
    # controls
    mouse = libtcod.Mouse()
    key = libtcod.Key()

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
        render_all()
        libtcod.console_flush()
        for obj in objects:
            obj.clear()

        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break
        if game_state == 'playing' and player_action != 'no turn':
            for obj in objects:
                if obj.ai:
                    obj.ai.take_turn()

def next_level():
    global dungeon_level
    # got to next level
    message('You take a moment to rest and recover your strength.', libtcod.light_cyan)
    player.fighter.heal(player.fighter.max_hp / 2)
    message('After a moment of peace, you descend deeper into the depths of horror.', libtcod.dark_red)
    dungeon_level += 1
    make_map()
    initialize_fov()

# initialization
libtcod.console_set_custom_font('data/fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 'pyHack', False)
con = libtcod.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)

libtcod.sys_set_fps(config.LIMIT_FPS)

libtcod.console_set_default_foreground(0, libtcod.light_yellow)
libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
    'PYHACKRL')
libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-3, libtcod.BKGND_NONE, libtcod.CENTER,
    'by Norf Launmen')

main_menu()
