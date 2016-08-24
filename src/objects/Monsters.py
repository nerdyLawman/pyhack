import libtcodpy as libtcod
import gameconfig
from player import player

class BaseMonster:
    #basic monster ai
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(gameconfig.FOV_MAP, monster.x, monster.y):
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)