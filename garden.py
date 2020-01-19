import random
from widget import *
import tako
from pygame import sprite

class Garden:

    def __init__(self, size, num_tako, pop_max, genetic_type, rand_net, seed,
                 display_off, garden_mode):
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
        self.display_off = display_off
        self.garden_mode = garden_mode
        self.reset()
 
    def reset(self):
        self.garden_map = [[Dirt(self.display_off) for x in range(self.size)]
                           for x in range(self.size)]
        self.tako_list = []
        rock = 0
        while rock < (0.02 * (self.size**2)):
            self.add_item(Rock(self.display_off))
            rock += 1
        ball = 0
        while ball < (0.04 * (self.size**2)):
            self.add_item(Ball(self.display_off))
            ball += 1
        gras = 0
        while (gras <= (.25 * (self.size**2))):
            #two types of grass
            if (self.garden_mode == "Diverse Static" or
                self.garden_mode == "Nutrition"):
                l = random.randint(0, 1)
                if l == 1:
                    self.add_item(Grass(self.display_off))
                else:
                    if self.garden_mode == "Nutrition":
                        self.add_item(Grass2(self.display_off, poison=True))
                    else:
                        self.add_item(Grass2(self.display_off, poison=False))
                gras += 1
            #one type of grass
            else:
                self.add_item(Grass(self.display_off))
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
        Tak = tako.Tako.default_tako(direction, self.display_off, x, y,
                                self.genetic_type, self.rand_net)
        self.garden_map[y][x].kill()
        self.garden_map[y][x] = Tak
        self.tako_list.append(Tak)

    def switch_nutrition(self):
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

    def switch_grasses(self):
        for y in range(self.size):
            for x in range(self.size):
                if isinstance(self.garden_map[y][x], Grass):
                    self.garden_map[y][x].kill()
                    g = Grass2(self.display_off, x, y, poison=False)
                    self.garden_map[y][x] = g
                    self.new_sprites.add(g)
                elif isinstance(self.garden_map[y][x], Grass2):
                    self.garden_map[y][x].kill()
                    g = Grass(self.display_off, x, y)
                    self.garden_map[y][x] = g
                    self.new_sprites.add(g)
        
    def get_sensors(self, tak):
        target = self.get_target(tak)
        obj = self.garden_map[target[1]][target[0]]
        return obj.node
    
    def perform_action(self, index, tak):
        result = function_array[index](self, tak, tak.last_obj)
        return result

    def forward(self, tak, obj=None):
        #get target square
        target = self.get_target(tak)
        targ = self.garden_map[target[1]][target[0]]
        result = targ.intersected()
        #check if it's dirt
        if result is None:
            new = Dirt(self.display_off, tak.x, tak.y)
            self.garden_map[tak.y][tak.x] = new
            self.new_sprites.add(new)
            self.garden_map[target[1]][target[0]].kill()
            self.garden_map[target[1]][target[0]] = tak
            tak.move_rect((target[0] - tak.x), (target[1] - tak.y))
            tak.y = target[1]
            tak.x = target[0]
        return result
    
    def turn_left(self, tak, obj):
        newdir = tak.direction
        newdir -= 1
        if newdir < 0:
            newdir = 3
        tak.direction = newdir
        return None

    def turn_right(self, tak, obj):
        newdir = tak.direction
        newdir += 1
        if newdir > 3:
            newdir = 0
        tak.direction = newdir
        return None

    #for now take eaten object out if grass
    #TODO; changed for now
    def eat(self, tak, obj):
        target = self.get_target(tak)
        tak.last_obj = self.garden_map[target[1]][target[0]]
        x = tak.last_obj
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

    def mate(self, tak, obj):
        target = self.get_target(tak)
        tak.last_obj = self.garden_map[target[1]][target[0]]
        v = tak.last_obj
        result = v.mated(tak)
        if len(result)>2:
            tak.mating_attempts += 1
            if len(self.tako_list) < self.pop_max:
                while True:
                    x = random.randrange(0, (self.size))
                    y = random.randrange(0, (self.size))
                    if isinstance(self.garden_map[y][x], Dirt):
                        if x > tak.x - 3 or x < tak.x + 3:
                            if y > tak.y - 3 or y < tak.y + 3:
                                break
                direction = random.randrange(0,3)
                new_genome = tak.genome.recombine(v.genome)
                if (tako.family_detection != None or
                    tako.record_inbreeding == True or
                    tako.inbreed_lim < 1.1):
                    new_tak = tako.Tako(direction, self.display_off, x, y,
                                        new_genome, None, None, [tak, v],
                                        (max(tak.gen, v.gen) + 1),
                                        tak.degree_detection(v),
                                        tak.genoverlap(v))
                else:
                    new_tak = tako.Tako(direction, self.display_off, x, y,
                                        new_genome, None, None, [tak, v],
                                        (max(tak.gen, v.gen) + 1), None, None)
                self.garden_map[y][x].kill()
                self.garden_map[y][x] = new_tak
                self.tako_list.append(new_tak)
                self.new_sprites.add(new_tak)
                if new_tak.gen > self.highest_gen:
                    self.highest_gen = new_tak.gen
        return result

    def get_target(self, tak):
        target = [tak.x, tak.y]
        # looking north
        if tak.direction == 0:
            # if on extreme north edge
            if tak.y == 0:
                target[1] = self.size - 1
            else:
                target[1] = tak.y - 1
        #east
        elif tak.direction == 1:
            if tak.x == self.size - 1:
                target[0] = 0
            else:
                target[0] = tak.x + 1
        #south
        elif tak.direction == 2:
            if tak.y == self.size - 1:
                target[1] = 0
            else:
                target[1] = tak.y + 1
        #west
        elif tak.direction == 3:
            if tak.x == 0:
                target[0] = self.size - 1
            else:
                target[0] = tak.x - 1
        return target


function_array = [Garden.forward, Garden.turn_left, Garden.turn_right,
                  Garden.eat, Garden.play, Garden.mate]
