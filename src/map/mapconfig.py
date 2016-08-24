import gameconfig
import components

stagemap = [[ components.Tile(True)
    for y in range(gameconfig.MAP_HEIGHT)]
        for x in range(gameconfig.MAP_WIDTH)]