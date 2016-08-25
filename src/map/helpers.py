import gameconfig
import components
import libtcodpy as libtcod
from objects.Objects import Object, Item, BaseNPC

def random_choice_index(chances):
    # returns a random index
    dice = libtcod.random_get_int(0, 1, sum(chances))
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
        if dice <= running_sum:
            return choice
        choice += 1

def random_choice(chances_dict):
    # returns a string of a random selection
    chances = chances_dict.values()
    strings = chances_dict.keys()
    return strings[random_choice_index(chances)]

def is_blocked(x, y):
    # test if tile is blocked
    if level_map[x][y].blocked:
        return True
    # now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True
    return False

def create_room(room):
    global level_map
    # basic room
    for x in range(room.x1+1, room.x2):
        for y in range(room.y1+1, room.y2):
            level_map[x][y].blocked = False
            level_map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global level_map
    # horizontal tunnel
    for x in range(min(x1, x2), max(x1, x2) + 1):
        level_map[x][y].blocked = False
        level_map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global level_map
    # vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        level_map[x][y].blocked = False
        level_map[x][y].block_sight = False

def initialize_fov():
    global fov_recompute, fov_map
    # set initial FOV condition
    libtcod.console_clear(con)
    fov_recompute = True
    fov_map = libtcod.map_new(gameconfig.MAP_WIDTH, gameconfig.MAP_HEIGHT)
    for y in range(gameconfig.MAP_HEIGHT):
        for x in range(gameconfig.MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not level_map[x][y].block_sight, not level_map[x][y].blocked)

def get_leveldata():
    global start_npc_count, npc_count, start_item_count, item_count
    # returns counts of NPCs and Items --todo return instead of assignment
    start_npc_count = 0
    start_item_count = 0
    for obj in objects:
        if obj.ai:
            start_npc_count += 1
        if obj.item:
            start_item_count += 1
    npc_count = start_npc_count
    item_count = start_item_count

def place_objects(room):
    # random number of NPCS per room
    num_npcs = libtcod.random_get_int(0, 0, gameconfig.MAX_ROOM_NPCS)
    num_items = libtcod.random_get_int(0, 0, gameconfig.MAX_ROOM_ITEMS)

    # add NPCS
    for i in range(num_npcs):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        if not is_blocked(x, y):
            npc_ai = BaseNPC()
            npc_chances = {'dave': 80, 'deb': 20}
            dice = random_choice(npc_chances)
            if dice == 'dave':  #80% chance of getting a Dave
                #create a Dave
                npc_fighter = Fighter(hp=6, defense=0, power=2, xp=10, death_function=npc_death)
                npc = Object(x, y, 'O', 'Dave', libtcod.desaturated_green, blocks=True, fighter=npc_fighter, ai=npc_ai)
            elif dice == 'deb':
                #create a Deb
                npc_fighter = Fighter(hp=10, defense=0, power=3, xp=30, death_function=npc_death)
                npc = Object(x, y, 'T', 'Troll', libtcod.darker_purple, blocks=True, fighter=npc_fighter, ai=npc_ai)
            objects.append(npc)

    # add Items
    for i in range(num_items):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y1-1)

        if not is_blocked(x, y):
            item_chances = {'heal': 70, 'lightning': 10, 'fireball': 10, 'confuse': 10}
            dice = random_choice(item_chances)
            if dice == 'heal':
                item_component = Item(use_function = cast_heal)
                item = Object(x, y, '!', 'healing potion', libtcod.cyan, item=item_component)
            elif dice == 'lightning':
                item_component = Item(use_function = cast_lightning)
                item = Object(x, y, 'Z', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
            elif dice == 'fireball':
                item_component = Item(use_function=cast_fireball)
                item = Object(x, y, '#', 'scroll of fireball', libtcod.light_red, item=item_component)
            elif dice == 'confuse':
                item_component = Item(use_function = cast_confusion)
                item = Object(x, y, '*', 'scroll of confusion', libtcod.light_orange, item=item_component)
            objects.append(item)
            item.send_to_back()

def make_map():
    global level_map, objects, stairs
    # generate the level map

    objects = [player]
    rooms = []
    num_rooms = 0

    # fill map with unblocked tiles
    level_map = [[ Tile(True)
        for y in range(gameconfig.MAP_HEIGHT)]
            for x in range(gameconfig.MAP_WIDTH)]

    for r in range(gameconfig.MAX_ROOMS):

        # random width and height
        w = libtcod.random_get_int(0, gameconfig.ROOM_MIN_SIZE, gameconfig.ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, gameconfig.ROOM_MIN_SIZE, gameconfig.ROOM_MAX_SIZE)
        # random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, gameconfig.MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, gameconfig.MAP_HEIGHT - h - 1)

        # basic room
        new_room = RectRoom(x, y, w, h)
        failed = False

        #run through the other rooms and see if they intersect with this one
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            create_room(new_room)
            (new_x, new_y) = new_room.center() #center coordinates of new room
            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                (prev_x, prev_y) = rooms[num_rooms-1].center() #center coordinates of previous room
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            place_objects(new_room)
            rooms.append(new_room)
            num_rooms += 1

    # create stairs in the last room
    stairs = Object(new_x, new_y, '<', 'stairs', libtcod.black)
    objects.append(stairs)
    stairs.send_to_back()
