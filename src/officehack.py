import libtcodpy as libtcod
import math
import textwrap
import shelve
import gameconfig
from objects.Objects import Object, Fighter
from interface.helpers import main_menu, message_box

def render_all():
    # main fucntion which draws all objects on the screen every cycle
    global fov_map
    global fov_recompute

    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, gameconfig.TORCH_RADIUS, gameconfig.FOV_LIGHT_WALLS, gameconfig.FOV_ALGO)
        #go through all tiles, and set their background color
        for y in range(gameconfig.MAP_HEIGHT):
            for x in range(gameconfig.MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = stagemap[x][y].block_sight
                if not visible:
                    if stagemap[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, gameconfig.color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, gameconfig.color_dark_ground, libtcod.BKGND_SET)
                else:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, gameconfig.color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, gameconfig.color_light_ground, libtcod.BKGND_SET)
                    stagemap[x][y].explored = True

    # draw all objects in the list
    for obj in objects:
        if obj != player:
            obj.draw()
    # draw player last
    player.draw()

    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, gameconfig.SCREEN_WIDTH, gameconfig.SCREEN_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # interface shit maybe cleanup later as render_interface()
    # dungeon level
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level: ' + str(dungeon_level))
    # health bar
    render_bar(1, 1, gameconfig.BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)
    # NPCs bar
    render_bar(1, 3, gameconfig.BAR_WIDTH, 'NPCS', npc_count, start_npc_count, libtcod.light_blue, libtcod.darker_blue)
    # items bar
    render_bar(1, 5, gameconfig.BAR_WIDTH, 'ITEMS', item_count, start_item_count, libtcod.light_violet, libtcod.darker_violet)
    # mouse look
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, SCREEN_WIDTH/4, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
    libtcod.console_blit(panel, 0, 0, gameconfig.SCREEN_WIDTH, gameconfig.PANEL_HEIGHT, 0, 0, gameconfig.PANEL_Y)


def new_game():
    global player, panel, inventory, game_msgs, game_state, dungeon_level, player_level
    # player
    fighter_component = Fighter(hp=30, defense=1, power=5, xp=0, death_function=player_death)
    player = Object(con, 0, 0, '@', 'Hero', libtcod.white, blocks=True, fighter=fighter_component)
    dungeon_level = 1
    player.level = 1
    make_map()

    #gui
    panel = libtcod.console_new(gameconfig.SCREEN_WIDTH, gameconfig.PANEL_HEIGHT)

    game_state = 'playing'
    inventory = []
    game_msgs = []

    initialize_leveldata()
    initialize_fov()

    #a warm welcoming message!
    message(gameconfig.WELCOME_MESSAGE, libtcod.red)

def save_game():
    # open new empty shelve - overwrites old
    file = shelve.open('savegame', 'n')
    file['map'] = stagemap
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['stairs_index'] = objects.index(stairs)
    file['dungron_level'] = dungeon_level
    file.close()

def load_game():
    global stagemap, objects, player, inventory, game_msgs, game_state, stairs, dungeon_level
    # open previously saved shelve
    file = shelve.open('savegame', 'r')
    stagemap = file['map']
    objects = file['objects']
    player = objects[file['player_index']]
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    stairs = objects[file['stairs_index']]
    dungeon_level = file['dungeon_level']
    file.close()
    # render FOV
    initialize_fov()

def play_game():
    global key, mouse

    player_action = None
    # control assignment
    mouse = libtcod.Mouse()
    key = libtcod.Key()

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
        render_all()
        libtcod.console_flush()
        for obj in objects:
            obj.clear()

        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break
        if game_state == 'playing' and player_action != 'no turn':
            for obj in objects:
                if obj.ai:
                    obj.ai.take_turn()

def next_level():
    global dungeon_level

    # go to next level
    message('You take a moment to rest and recover your strength.', libtcod.light_cyan)
    player.fighter.heal(player.fighter.max_hp / 2)
    message('After a moment of peace, you descend deeper into the depths of horror.', libtcod.dark_red)
    dungeon_level += 1

    # create new level
    make_map()
    initialize_leveldata()
    initialize_fov()

# here we go!
libtcod.console_set_custom_font('data/fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(gameconfig.SCREEN_WIDTH, gameconfig.SCREEN_HEIGHT, 'Office_Hack', False)
con = libtcod.console_new(gameconfig.MAP_WIDTH, gameconfig.MAP_HEIGHT)

libtcod.sys_set_fps(gameconfig.LIMIT_FPS)

libtcod.console_set_default_foreground(0, libtcod.light_yellow)
libtcod.console_print_ex(0, gameconfig.SCREEN_WIDTH/2, gameconfig.SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
    'OFFICE_HACK')
libtcod.console_print_ex(0, gameconfig.SCREEN_WIDTH/2, gameconfig.SCREEN_HEIGHT/2-3, libtcod.BKGND_NONE, libtcod.CENTER,
    'by Norf Launmen')

main_menu(con)
