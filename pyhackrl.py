import libtcodpy as libtcod
import math
import textwrap

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50

HEAL_AMOUNT = 4

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
    global stagemap, player

    # fill map with unblocked tiles
    stagemap = [[ Tile(True)
        for y in range(MAP_HEIGHT)]
            for x in range(MAP_WIDTH)]

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

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
        #add to inv and remove from map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.pink)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)
    
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

def player_death(player):
    global game_state
    message('You died!', libtcod.white)
    game_state = 'dead'
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster):
    message(monster.name.capitalize() + ' is dead!', libtcod.cyan)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()

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

def place_objects(room):
    # random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        if not is_blocked(x, y):
            monster_ai = BaseMonster()
            if libtcod.random_get_int(0, 0, 100) < 80:  #80% chance of getting an orc
                #create an orc
                orc_fighter = Fighter(hp=10, defense=0, power=2, death_function=monster_death)
                monster = Object(con, x, y, 'O', 'Orc', libtcod.desaturated_green, blocks=True, fighter=orc_fighter, ai=monster_ai)
            else:
                #create a troll
                troll_fighter = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
                monster = Object(con, x, y, 'T', 'Troll', libtcod.darker_purple, blocks=True, fighter=troll_fighter, ai=monster_ai)

            objects.append(monster)

    num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)
    for i in range(num_items):
        #place an item randomly
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y1-1)

        if not is_blocked(x, y):
            item_component = Item(use_function = cast_heal)
            item = Object(con, x, y, '!', 'healing potion', libtcod.cyan, item=item_component)
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
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute

    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        #go through all tiles, and set their background color
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = stagemap[x][y].block_sight
                if not visible:
                    if stagemap[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                else:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                    stagemap[x][y].explored = True

    #draw all objects in the list
    for obj in objects:
        if obj != player:
            obj.draw()
    player.draw()

    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    # helath bar
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)
    # mouse look
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

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
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

def menu(header, options, width):
	
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options!')
    
    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
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
    
    # convert ascii to index
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None

def inventory_menu(header):
    # inventory
    if len(inventory) == 0:
        options = ['Inventory is empty']
    else:
        options = [item.name for item in inventory]
    index = menu(header, options, INVENTORY_WIDTH)
    #return selected item
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

def message(new_msg, color=libtcod.white):
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
        game_msgs.append((line, color))

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
        return('exit')  #exit game

    # movement
    if key.vk == libtcod.KEY_UP:
        player_move_or_attack(0, -1)
        fov_recompute = True
    elif key.vk == libtcod.KEY_DOWN:
        player_move_or_attack(0, 1)
        fov_recompute = True
    elif key.vk == libtcod.KEY_LEFT:
        player_move_or_attack(-1, 0)
        fov_recompute = True
    elif key.vk == libtcod.KEY_RIGHT:
        player_move_or_attack(1, 0)
        fov_recompute = True
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
        	chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
        	if chosen_item is not None:
        	    chosen_item.use()
        	
        return('no turn')

    return('playing')

# initialization
libtcod.console_set_custom_font('data/fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'pyHack', False)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)

libtcod.sys_set_fps(LIMIT_FPS)

# controls
mouse = libtcod.Mouse()
key = libtcod.Key()

# player
fighter_component = Fighter(hp=30, defense=1, power=5, death_function=player_death)
player = Object(con, 25, 23, '@', 'Hero', libtcod.white, blocks=True, fighter=fighter_component)
objects = [player]
inventory = []
game_msgs = []
make_map()

#gui
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

game_state = 'playing'
player_action = None

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not stagemap[x][y].block_sight, not stagemap[x][y].blocked)
fov_recompute = True

#a warm welcoming message!
message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)

while not libtcod.console_is_window_closed():

    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
    render_all()
    libtcod.console_flush()

    for obj in objects:
        obj.clear()

    if game_state == 'playing':
        player_action = handle_keys()
    if game_state == 'playing' and player_action != 'no turn':
        for obj in objects:
            if obj.ai:
                obj.ai.take_turn()
    if game_state == 'exit' or game_state == 'dead':
        break
