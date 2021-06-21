from pygame import sprite, Color, image, Rect
from pygame.constants import RLEACCEL
import os
## A widget is a kind of object in a Garden
## It can be interactable or not
## It holds responses to different actions

class Widget(sprite.Sprite):
    #a widget has a position
    def __init__(self, display_on, x=None, y=None):
        sprite.Sprite.__init__(self)
        if display_on:
            self.image, self.rect = self.load_image(self.display,
                                                    Color('#FF00FF'))
        self.x = x
        self.y = y
        if display_on:
            if self.x is not None:
                if self.y is not None:
                    self.rect = Rect(x*50, y*50, 50, 50)

    # functions should be implemented in subclasses
    # if they are relevant to that widget type
    def eaten(self):
        """Return result of object being eaten.
        """
        return ("amuse", -1)

    def played(self):
        """Return result of object being played with.
        """
        return ("amuse", -1)

    def intersected(self):
        """Return result of object being intersected.
        """
        return ("amuse", -1)

    def mated(self, tak):
        """Return result of object being mated with.
        """
        return ("amuse", -1)

    def load_image(self, name, colorkey=None):
        """Return object's image and rect.
        """
        fullname = os.path.join('img', name)
        img = image.load(fullname)
        img = img.convert()
        if colorkey is not None:
            if colorkey != -1:
                colorkey = img.get_at((0,0))
            img.set_colorkey(colorkey, RLEACCEL)
        return img, img.get_rect()

    def update_rect(self):
        """Reset rect to object's location.
        """
        self.rect = Rect(self.x*50, self.y*50, 50, 50)

    def move_rect(self, x, y):
        """Move rect by x, y.
        """
        self.rect = self.rect.move(x*50, y*50)

class Dirt(Widget):
    node = 0
    display = "dirt.png"
                
    #things can grow here eventually
    #creatures can walk on it
    def intersected(self):
        """Return result of Dirt being intersected (None, walkable).
        """
        return None


class Grass(Widget):
    node = 1
    display = "grass.png"

    def __init__(self, display_on, x=0, y=0, poison=False):
        super().__init__(display_on, x, y)
        self.poison = poison
        
    def eaten(self):
        """Return result of Grass being eaten (fills fullness).
        """
        if self.poison:
            return ("fullness", 10)
        else:
            return ("fullness", 30)


class Rock(Widget):
    node = 3
    display = "rock.png"
    def played(self):
        """Return result of Rock being played with (not amusing).
        """
        return ("amuse", -10)

    def eaten(self):
        """Return result of Rock being eaten (painful).
        """
        return ("pain", 30)
    

class Ball(Widget):
    node = 2
    display = "toy.png"
    #should move eventually
    def played(self):
        """Return result of Ball being played with (amusing).
        """
        return ("amuse", 30)

class Grass2(Widget):
    node = 5
    display = "grass2.png"

    def __init__(self, display_on, x=0, y=0, poison=True):
        super().__init__(display_on, x, y)
        self.poison = poison

    def eaten(self):
        """Return result of Grass2 being eaten (fills fullness).
        """       
        if self.poison:
            return ("fullness", 10)
        else:
            return ("fullness", 30)
