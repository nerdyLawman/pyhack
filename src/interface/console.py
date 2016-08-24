import libtcodpy as libtcod
import gameconfig


libtcod.console_set_custom_font('data/fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(gameconfig.SCREEN_WIDTH, gameconfig.SCREEN_HEIGHT, 'pyHack', False)
con = libtcod.console_new(gameconfig.MAP_WIDTH, gameconfig.MAP_HEIGHT)
