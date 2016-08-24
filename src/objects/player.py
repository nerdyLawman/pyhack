import gameconfig
import libtcodpy as libtcod
from Objects import Object
from CharacterClasses import Fighter
from interface import helpers as interface_helpers
from interface.console import con
import gameconfig

def _player_death(player):
    interface_helpers.message('You died!', libtcod.white)
    gameconfig.GAME_STATE = 'dead'
    player.char = '%'
    player.color = libtcod.dark_red

_fighter_component = Fighter(hp=30, defense=1, power=5, death_function=_player_death)

player = Object(con, 25, 23, '@', 'Hero', libtcod.white, blocks=True, fighter=_fighter_component)
gameconfig.ACTIVE_OBJECTS.append(player)

