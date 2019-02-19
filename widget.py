from pygame import sprite, Color, image, Rect
from pygame.constants import RLEACCEL
import os
## A widget is a kind of object in a Garden
## It can be interactable or not
## It holds responses to different actions

class Widget(sprite.Sprite):
    #a widget has a position
    def __init__(self, display_off, x=None, y=None):
        sprite.Sprite.__init__(self)
        if not display_off:
            self.image, self.rect = self.load_image(self.display, display_off,
                                                    Color('#FF00FF'))
        self.x = x
        self.y = y
        if not display_off:
            if self.x is not None:
                if self.y is not None:
                    self.rect = Rect(x*50, y*50, 50, 50)

    # functions should be implemented in subclasses
    # if they are relevant to that widget type
    def eaten(self):
        return ("amuse", -1)

    def played(self):
        return ("amuse", -1)

    # if creature tries to walk into widget,
    def intersected(self):
        return ("amuse", -1)

    def mated(self, tako):
        return ("amuse", -1)

    #display_off (bool): whether images are being displayed
    def load_image(self, name, display_off, colorkey=None):
        fullname = os.path.join('img', name)
        img = image.load(fullname)
        img = img.convert()
        if colorkey is not None:
            if colorkey is -1:
                colorkey = img.get_at((0,0))
            img.set_colorkey(colorkey, RLEACCEL)
        return img, img.get_rect()

    def update_rect(self):
        self.rect = Rect(self.x*50, self.y*50, 50, 50)

    def move_rect(self, x, y):
        self.rect = self.rect.move(x*50, y*50)

class Dirt(Widget):
    node = 0
    display = "dirt.png"
                
    #things can grow here eventually
    #creatures can walk on it
    def intersected(self):
        return None


class Grass(Widget):
    node = 1
    display = "grass.png"

    def __init__(self, display_off, x=0, y=0, poison=False):
        super().__init__(display_off, x, y)
        self.poison = poison
        
    def eaten(self):
        if self.poison:
            return ("fullness", 10)
        else:
            return ("fullness", 30)


class Rock(Widget):
    node = 3
    display = "rock.png"
    def played(self):
        return ("amuse", -10)

    def eaten(self):
        return ("pain", 30)
    

class Ball(Widget):
    node = 2
    display = "toy.png"
    #should move eventually
    def played(self):
        return ("amuse", 30)

class Grass2(Widget):
    node = 5
    display = "grass2.png"

    def __init__(self, display_off, x=0, y=0, poison=True):
        super().__init__(display_off, x, y)
        self.poison = poison

    def eaten(self):
        if self.poison:
            return ("fullness", 10)
        else:
            return ("fullness", 30)
