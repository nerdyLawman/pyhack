import gameconfig
import libtcodpy as libtcod
import math

import map.helpers as map_helpers
from map import mapconfig
from objects import actions as object_actions
from interface.console import con
from interface import helpers as interface_helpers
from interface import interfaceconfig

libtcod.sys_set_fps(gameconfig.LIMIT_FPS)
map_helpers.make_map()

player_action = None

for y in range(gameconfig.MAP_HEIGHT):
    for x in range(gameconfig.MAP_WIDTH):
        libtcod.map_set_properties(gameconfig.FOV_MAP, x, y, not mapconfig.stagemap[x][y].block_sight, 
                                   not mapconfig.stagemap[x][y].blocked)
#a warm welcoming message!
interface_helpers.message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)

while not libtcod.console_is_window_closed():

    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,interfaceconfig.KEY, interfaceconfig.MOUSE)
    map_helpers.render_all()
    libtcod.console_flush()

    for obj in gameconfig.ACTIVE_OBJECTS:
        obj.clear()

    if gameconfig.GAME_STATE == 'playing':
        player_action = object_actions.handle_keys()
    if gameconfig.GAME_STATE == 'playing' and player_action != 'no turn':
        for obj in gameconfig.ACTIVE_OBJECTS:
            if obj.ai:
                obj.ai.take_turn()
    if gameconfig.GAME_STATE == 'exit' or gameconfig.GAME_STATE == 'dead':
        break
