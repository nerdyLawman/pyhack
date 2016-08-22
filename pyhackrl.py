import libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

MAX_ROOM_MONSTERS = 3

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
  def __init__(self, con, x, y, char, name, color, blocks=False, fighter=None, ai=None):
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

  def move(self, dx, dy):
    if not is_blocked(self.x + dx, self.y + dy):
        self.x += dx
        self.y += dy

  def draw(self):
      if libtcod.map_is_in_fov(fov_map, self.x, self.y):
          libtcod.console_set_default_foreground(con, self.color)
          libtcod.console_put_char(self.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

  def clear(self):
      libtcod.console_put_char(self.con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Fighter:
    #combat-related properties and methods
    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power

class BaseMonster:
    #basic monster ai
    def take_turn(self):
        print('The ' + self.owner.name + ' growls!')

def player_move_or_attack(dx, dy):
    global fov_recompute

    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    #try to find an attackable object there
    target = None
    for object in objects:
        if object.x == x and object.y == y:
            target = object
            break

    #attack if target found, move otherwise
    if target is not None:
        print 'The ' + target.name + ' laughs at your puny efforts to attack him!'
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
            if libtcod.random_get_int(0, 0, 100) < 80:  #80% chance of getting an orc
                #create an orc
                monster = Object(con, x, y, 'O', 'Orc', libtcod.desaturated_green, True)
            else:
                #create a troll
                monster = Object(con, x, y, 'T', 'Troll', libtcod.darker_green, True)

            objects.append(monster)

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
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
                    stagemap[x][y].explored = True

    #draw all objects in the list
    for object in objects:
        object.draw()

    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

def handle_keys():
    global playerx, playery, fov_recompute

    key = libtcod.console_wait_for_keypress(True)

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return('exit')  #exit game

    # movement
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player_move_or_attack(0, -1)
        fov_recompute = True
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player_move_or_attack(0, 1)
        fov_recompute = True
    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player_move_or_attack(-1, 0)
        fov_recompute = True
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player_move_or_attack(1, 0)
        fov_recompute = True
    else:
        return('no turn')

    return('playing')

# initialization
libtcod.console_set_custom_font('data/fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'pyHack', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

libtcod.sys_set_fps(LIMIT_FPS)

# player
fighter_component = Fighter(hp=30, defense=2, power=5)
player = Object(con, 25, 23, '@', 'Hero', libtcod.white, blocks=True, fighter=fighter_component)
objects = [player]
make_map()

game_state = 'playing'
player_action = None

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not stagemap[x][y].block_sight, not stagemap[x][y].blocked)
fov_recompute = True

while not libtcod.console_is_window_closed():

    render_all()
    libtcod.console_flush()

    for obj in objects:
        obj.clear()

    if game_state == 'playing':
        player_action = handle_keys()
    if game_state == 'playing' and player_action != 'no turn':
        for obj in objects:
            if obj != player:
                print 'The ' + obj.name + ' growls!'
    if game_state == 'exit':
        break
