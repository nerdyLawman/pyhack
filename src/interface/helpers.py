import libtcodpy as libtcod
import gameconfig
import textwrap
from interface import interfaceconfig

#gui
panel = libtcod.console_new(gameconfig.SCREEN_WIDTH, gameconfig.PANEL_HEIGHT)

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a status bar
    bar_width = int(float(value) / maximum * total_width)
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))

    y = 1
    for (line, color) in gameconfig.GAME_MSGS:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, gameconfig.MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

def menu(header, options, width):

    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options!')

    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    height = len(options) + header_height

    #create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    #blit window contents
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    #present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)

    # convert ascii to index
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None

def inventory_menu(header):
    # inventory
    if len(inventory) == 0:
        options = ['Inventory is empty']
    else:
        options = [item.name for item in inventory]
    index = menu(header, options, INVENTORY_WIDTH)
    #return selected item
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

def message(new_msg, color=libtcod.white):
    new_msg_lines = textwrap.wrap(new_msg, gameconfig.MSG_WIDTH)

    for line in new_msg_lines:
        if len(gameconfig.GAME_MSGS) == gameconfig.MSG_HEIGHT:
            del gameconfig.GAME_MSGS[0]
        gameconfig.GAME_MSGS.append((line, color))

def get_names_under_mouse():
    (x, y) = (interfaceconfig.MOUSE.cx, interfaceconfig.MOUSE.cy)
    names = [obj.name for obj in gameconfig.ACTIVE_OBJECTS
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(gameconfig.FOV_MAP, obj.x, obj.y)]
    names = ', '.join(names)
    return names.capitalize()

