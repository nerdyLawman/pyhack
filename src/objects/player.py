import gameconfig
import libtcodpy as libtcod
from Objects import Object, Fighter

_fighter_component = Fighter(hp=30, defense=1, power=5, death_function=_player_death)

player = Object(con, 25, 23, '@', 'Hero', libtcod.white, blocks=True, fighter=_fighter_component)
gameconfig.ACTIVE_OBJECTS.append(player)

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
        # level up
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('Your skills increase. LEVEL UP! Now at level: ' + str(player.level) + '.', libtcod.yellow)

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
