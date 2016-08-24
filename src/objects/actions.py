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


def cast_heal():
    # heal the player
    if player.fighter.hp == player.fighter.max_hp:
        interface_helpers.message('You are already at full health.', libtcod.red)
        return('cancelled')
    interface_helpers.message('your wounds feel better.', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)


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

        return('no turn')

    return('playing')