import gameconfig
import components
import libtcodpy as libtcod
from interface.console import con
from objects import actions as object_actions
from objects.Objects import Object, Item
from objects.CharacterClasses import Fighter
from objects.Monsters import BaseMonster
from objects.player import player
from objects.actions import cast_heal
from interface import helpers as interface_helpers
from objects.player import player
import mapconfig

def _create_room(room):
    for x in range(room.x1+1, room.x2):
        for y in range(room.y1+1, room.y2):
            mapconfig.stagemap[x][y].blocked = False
            mapconfig.stagemap[x][y].block_sight = False

def _create_h_tunnel(x1, x2, y):
    # horizontal tunnel
    for x in range(min(x1, x2), max(x1, x2) + 1):
        mapconfig.stagemap[x][y].blocked = False
        mapconfig.stagemap[x][y].block_sight = False

def _create_v_tunnel(y1, y2, x):
    # vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        mapconfig.stagemap[x][y].blocked = False
        mapconfig.stagemap[x][y].block_sight = False

def is_blocked(x, y):
    #first test the map tile
    if mapconfig.stagemap[x][y].blocked:
        return True

    #now check for any blocking objects
    for object in  gameconfig.ACTIVE_OBJECTS:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

def _place_objects(room):
    # random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, gameconfig.MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        if not is_blocked(x, y):
            monster_ai = BaseMonster()
            if libtcod.random_get_int(0, 0, 100) < 80:  #80% chance of getting an orc
                #create an orc
                orc_fighter = Fighter(hp=10, defense=0, power=2, death_function=object_actions.monster_death)
                monster = Object(con, x, y, 'O', 'Orc', libtcod.desaturated_green, blocks=True, fighter=orc_fighter, ai=monster_ai)
            else:
                #create a troll
                troll_fighter = Fighter(hp=10, defense=0, power=3, death_function=object_actions.monster_death)
                monster = Object(con, x, y, 'T', 'Troll', libtcod.darker_purple, blocks=True, fighter=troll_fighter, ai=monster_ai)

            gameconfig.ACTIVE_OBJECTS.append(monster)

    num_items = libtcod.random_get_int(0, 0, gameconfig.MAX_ROOM_ITEMS)
    for i in range(num_items):
        #place an item randomly
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y1-1)

        if not is_blocked(x, y):
            item_component = Item(use_function = cast_heal())
            item = Object(con, x, y, '!', 'healing potion', libtcod.cyan, item=item_component)
            gameconfig.ACTIVE_OBJECTS.append(item)
            item.send_to_back()


def render_all():
    color_dark_wall = gameconfig.color_dark_wall
    color_light_wall = gameconfig.color_light_wall
    color_dark_ground = gameconfig.color_dark_ground
    color_light_ground = gameconfig.color_light_ground

    if gameconfig.FOV_RECOMPUTE:
        gameconfig.FOV_RECOMPUTE = False
        libtcod.map_compute_fov(gameconfig.FOV_MAP, player.x, player.y, gameconfig.TORCH_RADIUS, gameconfig.FOV_LIGHT_WALLS, gameconfig.FOV_ALGO)
        #go through all tiles, and set their background color
        for y in range(gameconfig.MAP_HEIGHT):
            for x in range(gameconfig.MAP_WIDTH):
                visible = libtcod.map_is_in_fov(gameconfig.FOV_MAP, x, y)
                wall = mapconfig.stagemap[x][y].block_sight
                if not visible:
                    if mapconfig.stagemap[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, gameconfig.color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, gameconfig.color_dark_ground, libtcod.BKGND_SET)
                else:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, gameconfig.color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, gameconfig.color_light_ground, libtcod.BKGND_SET)
                    mapconfig.stagemap[x][y].explored = True

    #draw all objects in the list
    for obj in gameconfig.ACTIVE_OBJECTS:
        if obj != player:
            obj.draw()
    player.draw()

    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, gameconfig.SCREEN_WIDTH, gameconfig.SCREEN_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_background(interface_helpers.panel, libtcod.black)
    libtcod.console_clear(interface_helpers.panel)
    # health bar
    interface_helpers.render_bar(1, 1, gameconfig.BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)
    # mouse look
    libtcod.console_set_default_foreground(interface_helpers.panel, libtcod.light_gray)
    libtcod.console_print_ex(interface_helpers.panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, interface_helpers.get_names_under_mouse())
    libtcod.console_blit(interface_helpers.panel, 0, 0, gameconfig.SCREEN_WIDTH, gameconfig.PANEL_HEIGHT, 0, 0, gameconfig.PANEL_Y)


def make_map():
    rooms = []
    num_rooms = 0

    for r in range(gameconfig.MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, gameconfig.ROOM_MIN_SIZE, gameconfig.ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, gameconfig.ROOM_MIN_SIZE, gameconfig.ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, gameconfig.MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, gameconfig.MAP_HEIGHT - h - 1)

        #"Rect" class makes rectangles easier to work with
        new_room = components.Rect(x, y, w, h)

        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            #this means there are no intersections, so this room is valid

            #"paint" it to the map's tiles
            _create_room(new_room)

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
                    _create_h_tunnel(prev_x, new_x, prev_y)
                    _create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    _create_v_tunnel(prev_y, new_y, prev_x)
                    _create_h_tunnel(prev_x, new_x, new_y)

            #finally, append the new room to the list
            _place_objects(new_room)
            rooms.append(new_room)
            num_rooms += 1
