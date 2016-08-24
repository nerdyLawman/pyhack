import libtcodpy as libtcod
import gameconfig
from interface import helpers as interface_helpers
from interface import interfaceconfig
from player import player


def monster_death(monster):
    interface_helpers.message(monster.name.capitalize() + ' is dead!', libtcod.cyan)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
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

def cast_heal():
    # heal the player
    if player.fighter.hp == player.fighter.max_hp:
        interface_helpers.message('You are already at full health.', libtcod.red)
        return('cancelled')
    interface_helpers.message('your wounds feel better.', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
    #find nearest enemy and shock them with your deviant behaviour
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:
        message('No enemy is close enough to be shocked by you.', libtcod.red)
        return 'cancelled'
    message('A lightning bold strikes the ' + monster.name + ', ZAP! For ' + str(LIGHTNING_DAMAGE) + ' damage.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)


def player_move_or_attack(dx, dy):
    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    #try to find an attackable object there
    target = None
    for object in gameconfig.ACTIVE_OBJECTS:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    #attack if target found, move otherwise
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        gameconfig.FOV_RECOMPUTE = True

def handle_keys():
    global playerx, playery

    if interfaceconfig.KEY.vk == libtcod.KEY_ENTER and interfaceconfig.KEY.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif interfaceconfig.KEY.vk == libtcod.KEY_ESCAPE:
        return('exit')  #exit game

    # movement
    if interfaceconfig.KEY.vk == libtcod.KEY_UP:
        player_move_or_attack(0, -1)
        gameconfig.FOV_RECOMPUTE = True
    elif interfaceconfig.KEY.vk == libtcod.KEY_DOWN:
        player_move_or_attack(0, 1)
        gameconfig.FOV_RECOMPUTE = True
    elif interfaceconfig.KEY.vk == libtcod.KEY_LEFT:
        player_move_or_attack(-1, 0)
        gameconfig.FOV_RECOMPUTE = True
    elif interfaceconfig.KEY.vk == libtcod.KEY_RIGHT:
        player_move_or_attack(1, 0)
        gameconfig.FOV_RECOMPUTE = True
    else:
        #other keys
        key_char = chr(interfaceconfig.KEY.c)
        if key_char == 'g':
            #pick up an item
            for obj in gameconfig.ACTIVE_OBJECTS:
                if obj.x == player.x and obj.y == player.y and obj.item:
                    obj.item.pick_up()
                    break
        if key_char == 'i':
        	#display inventory
        	chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
        	if chosen_item is not None:
        	    chosen_item.use()
        if key_char == 'f':
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        return('no turn')

    return('playing')
