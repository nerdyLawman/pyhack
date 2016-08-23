import libtcodpy as libtcod

class Object:
  # generic object
  def __init__(self, con, x, y, char, color):
    self.con = con
    self.x = x
    self.y = y
    self.char = char
    self.color = color

  def move(self, dx, dy):
    self.x += dx
    self.y += dy

  def draw(self):
    libtcod.console_set_default_foreground(con, self.color)
    libtcod.console_put_char(self.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

  def clear(self):
    libtcod.console_put_char(self.con, self.x, self.y, ' ', libtcod.BKGND_NONE)
