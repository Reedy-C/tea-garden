import random
from widget import *
from tako import Tako
from pygame import sprite

class Garden:
    """ simulates a small environment containing
    objects and a creature which can
    go forward
    turn left/right
    eat
    play
    as well as seeing what is directly in front of it
    """


    def __init__(self, size, num_tako, pop_max, genetic_type, rand_net, seed):
        #create the map and add toy, grass, rock, creature
        if size < 3:
            raise ValueError
        self.size = size
        self.num_tako = num_tako
        self.pop_max = pop_max
        self.new_sprites = sprite.Group()
        self.highest_gen = 0
        self.genetic_type = genetic_type
        self.rand_net = rand_net
        if seed is not None:
            random.seed(seed)
        self.reset()
 
    def reset(self):
        self.garden_map = [[Dirt() for x in range(self.size)]
                           for x in range(self.size)]
        self.tako_list = []
        rock = 0
        while rock < (0.02 * (self.size**2)):
            self.add_item(Rock())
            rock += 1
        ball = 0
        while ball < (0.04 * (self.size**2)):
            self.add_item(Ball())
            ball += 1
        gras = 0
        while (gras <= (.25 * (self.size**2))):
            l = random.randint(0, 1)
            if l == 1:
                self.add_item(Grass())
            else:
                self.add_item(Grass2(poison=False))
            gras += 1
        while (len(self.tako_list)) < self.num_tako:
            self.add_creature()
        for y in range(self.size):
            for x in range(self.size):
                if isinstance(self.garden_map[y][x], Dirt):
                    Dirt.y = y
                    Dirt.x = x
        
    def add_item(self, item):
        while True:
            x = random.randrange(0, self.size)
            y = random.randrange(0, self.size)
            if isinstance(self.garden_map[y][x], Dirt):
                break
        self.garden_map[y][x].kill()
        self.garden_map[y][x] = item
        item.x = x
        item.y = y
        item.update_rect()
        self.new_sprites.add(item)

    def add_creature(self):
        while True:
            x = random.randrange(0, (self.size))
            y = random.randrange(0, (self.size))
            if isinstance(self.garden_map[y][x], Dirt):
                break
        direction = random.randrange(0,3)
        Tak = Tako.default_tako(direction, x, y, self.genetic_type,
                                self.rand_net)
        self.garden_map[y][x].kill()
        self.garden_map[y][x] = Tak
        self.tako_list.append(Tak)

    def switch_grass(self):
        for y in range(self.size):
            for x in range(self.size):
                if isinstance(self.garden_map[y][x], Grass):
                    if self.garden_map[y][x].poison == True:
                        self.garden_map[y][x].poison = False
                    else:
                        self.garden_map[y][x].poison = True
                elif isinstance(self.garden_map[y][x], Grass2):
                    if self.garden_map[y][x].poison == True:
                        self.garden_map[y][x].poison = False
                    else:
                        self.garden_map[y][x].poison = True
        
    def getSensors(self, tako):
        target = self.get_target(tako)
        obj = self.garden_map[target[1]][target[0]]
        return obj.node
    
    def performAction(self, index, tako):
        result = function_array[index](self, tako, tako.last_obj)
        return result

    def forward(self, tako, obj=None):
        #get target square
        target = self.get_target(tako)
        targ = self.garden_map[target[1]][target[0]]
        result = targ.intersected()
        #check if it's dirt
        if result is None:
            new = Dirt(tako.x, tako.y)
            self.garden_map[tako.y][tako.x] = new
            self.new_sprites.add(new)
            self.garden_map[target[1]][target[0]].kill()
            self.garden_map[target[1]][target[0]] = tako
            tako.move_rect((target[0] - tako.x), (target[1] - tako.y))
            tako.y = target[1]
            tako.x = target[0]
        return result
    
    def turn_left(self, tako, obj):
        newdir = tako.direction
        newdir -= 1
        if newdir < 0:
            newdir = 3
        tako.direction = newdir
        return None

    def turn_right(self, tako, obj):
        newdir = tako.direction
        newdir += 1
        if newdir > 3:
            newdir = 0
        tako.direction = newdir
        return None

    #for now take eaten object out if grass
    #TODO; changed for now
    def eat(self, tako, obj):
        target = self.get_target(tako)
        tako.last_obj = self.garden_map[target[1]][target[0]]
        x = tako.last_obj
        result = x.eaten()
        #if isinstance(tako.last_obj, Grass):
        #    self.add_item(Grass())
        #    tako.last_obj.kill()
        #    new = Dirt(target[0], target[1])
        #    self.new_sprites.add(new)
        #    self.garden_map[target[1]][target[0]] = new
        return result

    #for now take played-with object out
    #TODO; changed for now
    def play(self, tako, obj):
        target = self.get_target(tako)
        tako.last_obj = self.garden_map[target[1]][target[0]]
        x = tako.last_obj
        result = x.played()
##        if isinstance(tako.last_obj, Ball):
##            tako.last_obj.kill()
##            new = Dirt(target[0], target[1])
##            self.garden_map[target[1]][target[0]] = new
##            self.new_sprites.add(new)
##            self.add_item(Ball())
        return result

    def mate(self, tako, obj):
        target = self.get_target(tako)
        tako.last_obj = self.garden_map[target[1]][target[0]]
        v = tako.last_obj
        result = v.mated(tako)
        if result != ("boredom", -1):
            tako.mating_attempts += 1
            #then result[3] is a genome
            #result[4] is its parents
            #result[5] is its generation
            if len(self.tako_list) < self.pop_max:
                #chance = random.randint(0, 1)
                chance = 0
                if chance == 0:
                    while True:
                        x = random.randrange(0, (self.size))
                        y = random.randrange(0, (self.size))
                        if isinstance(self.garden_map[y][x], Dirt):
                            if x > tako.x - 3 or x < tako.x + 3:
                                if y > tako.y - 3 or y < tako.y + 3:
                                    break
                    direction = random.randrange(0,3)
                    new_tak = Tako(direction, x, y, result[3], None,
                                        parents=result[4], gen=result[5])
                    tako.children.append(new_tak.ident)
                    v.children.append(new_tak.ident)
                    self.garden_map[y][x].kill()
                    self.garden_map[y][x] = new_tak
                    self.tako_list.append(new_tak)
                    self.new_sprites.add(new_tak)
                    if result[5] > self.highest_gen:
                        self.highest_gen = result[5]
            result = (result[0], result[1], result[2])
        return result

    def get_target(self, tako):
        target = [tako.x, tako.y]
        # looking north
        if tako.direction == 0:
            # if on extreme north edge
            if tako.y == 0:
                target[1] = self.size - 1
            else:
                target[1] = tako.y - 1
        #east
        elif tako.direction == 1:
            if tako.x == self.size - 1:
                target[0] = 0
            else:
                target[0] = tako.x + 1
        #south
        elif tako.direction == 2:
            if tako.y == self.size - 1:
                target[1] = 0
            else:
                target[1] = tako.y + 1
        #west
        elif tako.direction == 3:
            if tako.x == 0:
                target[0] = self.size - 1
            else:
                target[0] = tako.x - 1
        return target


function_array = [Garden.forward, Garden.turn_left, Garden.turn_right,
                  Garden.eat, Garden.play, Garden.mate]
