import gameconfig
import libtcodpy as libtcod

# initialization
libtcod.console_set_custom_font('data/fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(gameconfig.SCREEN_WIDTH, gameconfig.SCREEN_HEIGHT, 'Office_Hack', False)
con = libtcod.console_new(gameconfig.MAP_WIDTH, gameconfig.MAP_HEIGHT)

libtcod.sys_set_fps(gameconfig.LIMIT_FPS)

libtcod.console_set_default_foreground(0, libtcod.light_yellow)
libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
    'OFFICE_HACK')
libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-3, libtcod.BKGND_NONE, libtcod.CENTER,
    'by Norf Launmen')
