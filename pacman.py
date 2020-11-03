"""
pac man

authors: Horst JENS, Simon HEPPNER, Max KOBER
email: horstjens@gmail.com, simon@heppner.at
contact: see http://spielend-programmieren.at/de:kontakt
license: gpl, see http://www.gnu.org/licenses/gpl-3.0.de.html
part of http://ThePythonGamebook.com
"""

import pygame
# import pygame.locals
import pygame.freetype  # not automatically loaded when importing pygame!
import pygame.gfxdraw
import random
import os


class VectorSprite(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygame sprite class
    """

    number = 0  # unique number for each sprite
    images = []

    # numbers = {} # { number, Sprite }

    def __init__(self,
                 pos=None,
                 move=None,
                 acceleration=1.0,
                 _layer=0,
                 angle=0,
                 radius=0,
                 color=(
                               random.randint(0, 255),
                               random.randint(0, 255),
                               random.randint(0, 255),
                       ),
                 hitpoints=100,
                 hitpointsfull=100,
                 stop_on_edge = False,
                 kill_on_edge = False,
                 bounce_on_edge = False,
                 warp_on_edge = False,
                 age = 0,
                 max_age = None,
                 max_distance = None,
                 picture = None,
                 boss = None,
                 #kill_with_boss = False,
                 move_with_boss = False,
                 area = None, # pygame.Rect,
                 animations_per_second = None,
                 animation_index = 0,
                 **kwargs):
        #self._default_parameters(**kwargs)
        _locals = locals().copy() # copy locals() so that it does not updates itself
        for key in _locals:
            if key != "self" and key != "kwargs":  # iterate over all named arguments, including default values
                setattr(self, key, _locals[key])
        for key, arg in kwargs.items(): # iterate over all **kwargs arguments
            setattr(self, key, arg)
        if pos is None:
            self.pos = pygame.math.Vector2(200,200)
        if move is None:
            self.move = pygame.math.Vector2(0,0)
        self.animation_time_passed = 0
        self._overwrite_parameters()
        pygame.sprite.Sprite.__init__(
            self, self.groups
        )  # call parent class. NEVER FORGET !
        self.number = VectorSprite.number  # unique number for each sprite
        VectorSprite.number += 1
        # VectorSprite.numbers[self.number] = self
        # self.visible = False
        self.create_image()
        self.distance_traveled = 0  # in pixel
        # self.rect.center = (-300,-300) # avoid blinking image in topleft corner
        if self.angle != 0:
            self.set_angle(self.angle)

    def _overwrite_parameters(self):
        """change parameters before create_image is called"""
        pass


    def kill(self):
        # check if this is a boss and kill all his underlings as well
        tokill = [s for s in Viewer.allgroup if "boss" in s.__dict__ and s.boss == self]
        for s in tokill:
            s.kill()
        # if self.number in self.numbers:
        #   del VectorSprite.numbers[self.number] # remove Sprite from numbers dict
        pygame.sprite.Sprite.kill(self)

    def create_image(self):
        if self.picture is not None:
            self.image = self.picture.copy()
        elif self.animations_per_second is not None:
            self.image = self.images[self.animation_index]
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(self.color)
        self.image = self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos[0], 0), round(self.pos[1], 0))
        # self.width = self.rect.width
        # self.height = self.rect.height

    def rotate(self, by_degree):
        """rotates a sprite and changes it's angle by by_degree"""
        self.angle += by_degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def get_angle(self):
        if self.angle > 180:
            return self.angle - 360
        return self.angle

    def set_angle(self, degree):
        """rotates a sprite and changes it's angle to degree"""
        self.angle = degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def update(self, seconds):
        """calculate movement, position and bouncing on edge"""
        self.age += seconds
        if self.age < 0:
            return
        if self.animations_per_second is not None:
            self.animation_time_passed += seconds
            if self.animation_time_passed > 1 / self.animations_per_second:
                self.animation_time_passed = 0
                self.animation_index += 1
                if self.animation_index == len(self.images):
                    self.animation_index = 0
                self.image = self.images[self.animation_index]

        # self.visible = True
        self.distance_traveled += self.move.length() * seconds
        # ----- kill because... ------
        if self.hitpoints <= 0:
            self.kill()
        if self.max_age is not None and self.age > self.max_age:
            self.kill()
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        # acceleration
        self.move *= self.acceleration
        # ---- movement with/without boss ----
        if self.boss and self.move_with_boss:
            self.pos = self.boss.pos
            self.move = self.boss.move
        else:
            # move independent of boss
            self.pos += self.move * seconds
            self.wallcheck()
        # print("rect:", self.pos.x, self.pos.y)
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def wallcheck(self):
        # ---- bounce / kill on screen edge ----
        if self.area is None:
            self.area = Viewer.screenrect
            #print(self.area)
        # ------- left edge ----
        if self.pos.x < self.area.left:
            if self.stop_on_edge:
                self.pos.x = self.area.left
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = self.area.left
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = self.area.right
        # -------- upper edge -----
        if self.pos.y < self.area.top:
            if self.stop_on_edge:
                self.pos.y = self.area.top
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = self.area.top
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = self.area.bottom
        # -------- right edge -----
        if self.pos.x > self.area.right:
            if self.stop_on_edge:
                self.pos.x = self.area.right
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = self.area.right
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = self.area.left
        # --------- lower edge ------------
        if self.pos.y > self.area.bottom:
            if self.stop_on_edge:
                self.pos.y = self.area.bottom
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = self.area.bottom
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = self.area.top


class Flytext(VectorSprite):
    def __init__(
            self,
            pos=pygame.math.Vector2(50, 50),
            move=pygame.math.Vector2(0, -50),
            text="hallo",
            color=(255, 0, 0),
            bgcolor=None,
            max_age=0.5,
            age=0,
            acceleration_factor=1.0,
            fontsize=48,
            textrotation=0,
            style=pygame.freetype.STYLE_STRONG,
            alpha_start=255,
            alpha_end=255,
            width_start=None,
            width_end=None,
            height_start=None,
            height_end=None,
            rotate_start=0,
            rotate_end=0,
            picture=None,
    ):
        """Create a flying VectorSprite with text or picture that disappears after a while

        :param pygame.math.Vector2 pos:     startposition in Pixel. To attach the text to another Sprite, use an existing Vector.
        :param pygame.math.Vector2 move:    movevector in Pixel per second
        :param text:                        the text to render. accept unicode chars. Will be overwritten when picture is given
        :param (int,int,int) color:         foregroundcolor for text
        :param (int,int,int) bgcolor:       backgroundcolor for text. If set to None, black is the transparent color
        :param float max_age:               lifetime of Flytext in seconds. Delete itself when age > max_age
        :param float age:                   start age in seconds. If negative, Flytext stay invisible until age >= 0
        :param float acceleration_factor:   1.0 for no acceleration. > 1 for acceleration of move Vector, < 1 for negative acceleration
        :param int fontsize:                fontsize for text
        :param float textrotation:          static textrotation in degree for rendering text.
        :param int style:                   effect for text rendering, see pygame.freetype constants
        :param int alpha_start:             alpha value for age =0. 255 is no transparency, 0 is full transparent
        :param int alpha_end:               alpha value for age = max_age.
        :param int width_start:             start value for dynamic zooming of width in pixel
        :param int width_end:               end value for dynamic zooming of width in pixel
        :param int height_start:            start value for dynamic zooming of height in pixel
        :param int height_end:              end value for dynamic zooming of height in pixel
        :param float rotate_start:          start angle for dynamic rotation of the whole Flytext Sprite
        :param float rotate_end:            end angle for dynamic rotation
        :param picture:                     a picture object. If not None, it overwrites any given text
        :return: None
        """

        self.recalc_each_frame = False
        self.text = text
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.alpha_diff_per_second = (alpha_start - alpha_end) / max_age
        if alpha_end != alpha_start:
            self.recalc_each_frame = True
        self.style = style
        self.acceleration_factor = acceleration_factor
        self.fontsize = fontsize
        self.textrotation = textrotation
        self.color = color
        self.bgcolor = bgcolor
        self.width_start = width_start
        self.width_end = width_end
        self.height_start = height_start
        self.height_end = height_end
        self.picture = picture
        # print( "my picture is:", self.picture)
        if width_start is not None:
            self.width_diff_per_second = (width_end - width_start) / max_age
            self.recalc_each_frame = True
        else:
            self.width_diff_per_second = 0
        if height_start is not None:
            self.height_diff_per_second = (height_end - height_start) / max_age
            self.recalc_each_frame = True
        else:
            self.height_diff_per_second = 0
        self.rotate_start = rotate_start
        self.rotate_end = rotate_end
        if (rotate_start != 0 or rotate_end != 0) and rotate_start != rotate_end:
            self.rotate_diff_per_second = (rotate_end - rotate_start) / max_age
            self.recalc_each_frame = True
        else:
            self.rotate_diff_per_second = 0
        # self.visible = False
        VectorSprite.__init__(
            self,
            color=color,
            pos=pos,
            move=move,
            max_age=max_age,
            age=age,
            picture=picture,
        )
        self._layer = 27  # order of sprite layers (before / behind other sprites)
        # acceleration_factor  # if < 1, Text moves slower. if > 1, text moves faster.

    def create_image(self):
        if self.picture is not None:
            # print("picture", self)
            self.image = self.picture
        else:
            # print("no picture", self)
            myfont = Viewer.font
            # text, textrect = myfont.render(
            # fgcolor=self.color,
            # bgcolor=self.bgcolor,
            # get_rect(text, style=STYLE_DEFAULT, rotation=0, size=0) -> rect
            textrect = myfont.get_rect(
                text=self.text,
                size=self.fontsize,
                rotation=self.textrotation,
                style=self.style,
            )  # font 22
            self.image = pygame.Surface((textrect.width, textrect.height))
            # render_to(surf, dest, text, fgcolor=None, bgcolor=None, style=STYLE_DEFAULT, rotation=0, size=0) -> Rect
            textrect = myfont.render_to(
                surf=self.image,
                dest=(0, 0),
                text=self.text,
                fgcolor=self.color,
                bgcolor=self.bgcolor,
                style=self.style,
                rotation=self.textrotation,
                size=self.fontsize,
            )
            if self.bgcolor is None:
                self.image.set_colorkey((0, 0, 0))

            self.rect = textrect
            # picture ? overwrites text

        # transparent ?
        if self.alpha_start == self.alpha_end == 255:
            pass
        elif self.alpha_start == self.alpha_end:
            self.image.set_alpha(self.alpha_start)
            # print("fix alpha", self.alpha_start)
        else:
            self.image.set_alpha(
                self.alpha_start - self.age * self.alpha_diff_per_second
            )
            # print("alpha:", self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        # save the rect center for zooming and rotating
        oldcenter = self.image.get_rect().center
        # dynamic zooming ?
        if self.width_start is not None or self.height_start is not None:
            if self.width_start is None:
                self.width_start = textrect.width
            if self.height_start is None:
                self.height_start = textrect.height
            w = self.width_start + self.age * self.width_diff_per_second
            h = self.height_start + self.age * self.height_diff_per_second
            self.image = pygame.transform.scale(self.image, (int(w), int(h)))
        # rotation?
        if self.rotate_start != 0 or self.rotate_end != 0:
            if self.rotate_diff_per_second == 0:
                self.image = pygame.transform.rotate(self.image, self.rotate_start)
            else:
                self.image = pygame.transform.rotate(
                    self.image,
                    self.rotate_start + self.age * self.rotate_diff_per_second,
                )
        # restore the old center after zooming and rotating
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def update(self, seconds):
        VectorSprite.update(self, seconds)
        if self.age < 0:
            return
        self.move *= self.acceleration_factor
        if self.recalc_each_frame:
            self.create_image()


class Hitpointbar(VectorSprite):
    height = 5

    def _overwrite_parameters(self):
        self.kill_with_boss = True
        self.move_with_boss = True

    def create_image(self):
        self.image = pygame.Surface((self.boss.width, self.height))
        # self.image.fill((0,255,0))
        percent = self.boss.width * (self.boss.hitpoints / self.boss.hitpointsfull)
        pygame.draw.rect(self.image, (0, 255, 0), (0, 0, int(round(percent, 0)), self.height))
        pygame.draw.rect(self.image, (0, 64, 0), (0, 0, self.boss.width, self.height), 1)
        self.image.set_colorkey((0, 0, 0,))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()

        # self.rect.center = self.pos.x, self.pos.y

    def update(self, seconds):
        self.create_image()
        # super().update(seconds)
        self.rect.center = self.boss.rect.centerx, self.boss.rect.centery - self.boss.height



class Spark(VectorSprite):

    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True
        self.color = randomize_colors(self.color, 50)

    def create_image(self):
        self.image = pygame.Surface((10, 10))
        pygame.draw.line(self.image, self.color,
                         (10, 5), (5, 5), 3)
        pygame.draw.line(self.image, self.color,
                         (5, 5), (2, 5), 1)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.image0 = self.image.copy()


class Smoke(VectorSprite):
    """a round fragment or bubble particle, fading out"""

    def _overwrite_parameters(self):
        # self.speed = random.randint(10, 50)
        self.start_radius = 1

        self.radius = 1
        self.end_radius = 10  # random.randint(15,20)
        # if self.max_age is None:
        #self.max_age = 7.5  # + random.random() * 2.5
        self.kill_on_edge = True
        self.kill_with_boss = False  # VERY IMPORTANT!!!
        # if self.move == pygame.math.Vector2(0, 0):
        #    self.move = pygame.math.Vector2(1, 0)
        #    self.move *= self.speed
        #    a, b = 0, 360
        #    self.move.rotate_ip(random.randint(a, b))
        self.alpha_start = 64
        self.alpha_end = 0
        self.alpha_diff_per_second = (self.alpha_start - self.alpha_end) / self.max_age
        self.color = (10, 10, 10)
        # self.color = randomize_colors(color=self.color, by=35)

    def create_image(self):
        # self.radius = self.start_radius +
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius))
        pygame.draw.circle(
            self.image, self.color, (self.radius, self.radius), self.radius
        )
        self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = int(round(self.pos.x, 0)), int(round(self.pos.y, 0))
        # self.rect.center=(int(round(self.pos[0],0)), int(round(self.pos[1],0)))

    def update(self, seconds):
        # self.create_image()
        self.radius = (self.end_radius / self.max_age) * self.age
        self.radius = int(round(self.radius, 0))
        self.create_image()
        #self.move = Viewer.windvector * seconds
        super().update(seconds)
        self.image.set_alpha(self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()


class Monster(VectorSprite):

    def _overwrite_parameters(self):
        self._layer=7
        self.pos = pygame.math.Vector2(self.x * Viewer.cell_width + Viewer.cell_width//2, self.y * Viewer.cell_height+Viewer.cell_height//2)
        self._layer = 2

class Pill(VectorSprite):

    def _overwrite_parameters(self):
        self.pos = pygame.math.Vector2(self.x * Viewer.cell_width + Viewer.cell_width // 2,
                                       self.y * Viewer.cell_height + Viewer.cell_height // 2)
        self._layer=30

class SuperPill(VectorSprite):

    def _overwrite_parameters(self):
        self.pos = pygame.math.Vector2(self.x * Viewer.cell_width + Viewer.cell_width // 2,
                                       self.y * Viewer.cell_height + Viewer.cell_height // 2)
        self._layer=1


class Player(Monster):
    def _overwrite_parameters(self):
        self.pos = pygame.math.Vector2(self.x * Viewer.cell_width + Viewer.cell_width//2, self.y * Viewer.cell_height+Viewer.cell_height//2)
        self._layer = 2
        self.animations_per_second = 5
        self.xx = 0
        self.yy = 0


class Ghost(Monster):

    nesw = {"north": (0,-1),
            "east": (1,0),
            "south": (0,1),
            "west": (-1,0)
            }
    inverse = {"north":"south",
               "east":"west",
               "south":"north",
               "west":"east"}

    def _overwrite_parameters(self):
        #self.nesw = [False, False, False, False] # direction to go: north, east, south, west
        self.direction = random.choice(tuple(self.nesw.keys()))
        self.animations_per_second = 4
        self.pos = pygame.math.Vector2(self.x * Viewer.cell_width + Viewer.cell_width // 2,
                                       self.y * Viewer.cell_height + Viewer.cell_height // 2)

    def move_nesw(self):
        # get possible directions
        self.options = []
        for direction in self.nesw.keys():
            dx, dy = self.nesw[direction][0], self.nesw[direction][1]
            if Game.cells[self.y+dy][self.x+dx] != 1 : # not a wall
                for other in [m for m in Viewer.ghostgroup if m.number != self.number]:
                    if other.x == self.x +dx and other.y == self.y + dy:
                        break
                else: # no break at all
                    self.options.append(direction)

        # just one option
        if len(self.options) == 0:
            return
        if len(self.options) ==1:
            self.direction = self.options[0]
        # no crossing, just continue old direction
        elif self.options in ([self.direction, self.inverse[self.direction]],
                            [self.inverse[self.direction], self.direction]):
            pass  # keep old direction
        # corner, T crossing, curve or full crossing
        else:
            self.direction = random.choice(self.options)
        # ---- teleport -----
        self.x += self.nesw[self.direction][0]
        self.y += self.nesw[self.direction][1]
        self.pos = pygame.math.Vector2(self.x * Viewer.cell_width + Viewer.cell_width // 2,
                                       self.y * Viewer.cell_height + Viewer.cell_height // 2)



class Game:
    lives = 3
    ghosts = 4
    points = 0
    # legend: 1: wall, 0: pill, 3: nothing, 2: player, 4,5,6,7: ghost
    cells = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 1, 0, 1, 1, 3, 3, 1, 1, 0, 1, 1, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1, 4, 5, 6, 7, 1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]


class Viewer:
    width = 0
    height = 0
    screenrect = None
    font = None
    cell_width = 0
    cell_height = 0
    max_idle = 0.22 # how many seconds idletime is allowed before computer makes automatic turn
    images = {}
    # --- player images ---
    images_east = []
    images_west = []
    images_south = []
    images_north = []
    # --- ghost images ---
    images_blue = []
    images_green = []
    images_neon = []
    images_orange = []
    images_pink = []
    images_red = []


    def __init__(
            self,
            width=800,
            height=600,
    ):

        Viewer.width = width
        Viewer.height = height
        Viewer.screenrect = pygame.Rect(0, 0, width, height)
        tiles_x = len(Game.cells[0])
        tiles_y = len(Game.cells)
        Viewer.cell_width = width // tiles_x
        Viewer.cell_height = height // tiles_y

        # ---- pygame init
        pygame.init()
        # pygame.mixer.init(11025) # raises exception on fail
        # Viewer.font = pygame.font.Font(os.path.join("data", "FreeMonoBold.otf"),26)
        # fontfile = os.path.join("data", "fonts", "DejaVuSans.ttf")
        # --- font ----
        # if you have your own font:
        # Viewer.font = pygame.freetype.Font(os.path.join("data","fonts","INSERT_YOUR_FONTFILENAME.ttf"))
        # otherwise:
        fontname = pygame.freetype.get_default_font()
        Viewer.font = pygame.freetype.SysFont(fontname, 64)

        # ------ joysticks init ----
        pygame.joystick.init()
        self.joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        for j in self.joysticks:
            j.init()
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.playtime = 0.0
        self.idle = 0 # how many seconds user did not gave a command

        # ------ background images ------
        # self.backgroundfilenames = []  # every .jpg or .jpeg file in the folder 'data'
        # self.make_background()
        self.load_images()
        self.setup() # this includes prepare_sprites()
        self.run()

    def load_images(self):
        # --- pacman ----
        # ----- PACMAN -----
        # 5 pacman-pictures, heading east
        for number in range(1,6):
            pic = pygame.image.load(os.path.join("data", f"pacman{number}.png"))
            pic = pygame.transform.scale(pic, (Viewer.cell_width, Viewer.cell_height))
            pic.convert_alpha()
            Viewer.images_east.append(pic)
        # copy for 3 other cardinal directions
        Player.images = Viewer.images_east[:]
        angles = (-90,-180,-270)
        containers = (Viewer.images_south, Viewer.images_west, Viewer.images_north)
        for i in (0,1,2):
            for pic in Viewer.images_east:
                containers[i].append(pygame.transform.rotate(pic, angles[i]))
        # ----ghost----
        colors = ("blue", "green", "neon", "orange", "pink", "red")
        for i in range(len(colors)):
            for number in range(1,5):
                pic = pygame.image.load(os.path.join("data", f"{colors[i]}_ghost{number}.png"))
                pic = pygame.transform.scale(pic, (Viewer.cell_width, Viewer.cell_height))
                pic.convert_alpha()
                Viewer.__dict__[f"images_{colors[i]}"].append(pic)

        # --- pill ---
        pic = pygame.image.load(os.path.join("data", "point_small.png"))
        pic = pygame.transform.scale(pic, (Viewer.cell_width, Viewer.cell_height))
        pic.convert_alpha()
        Viewer.images["pill"] = pic  # east


    def setup(self):
        """call this to restart a game"""
        # ------ game variables -----

        self.background = pygame.Surface((Viewer.width, Viewer.height))
        self.background.fill((15, 15, 15))
        # draw start and finish text in topleft / lowerright corners

        # create labyrinth
        for y, line in enumerate(Game.cells):
            for x, char in enumerate(line):
                if char == 1:
                    pygame.draw.rect(self.background, (0,0,128), (x * Viewer.cell_width, y * Viewer.cell_height, Viewer.cell_width, Viewer.cell_height) )
        self.prepare_sprites()
        self.idle = 0


    def prepare_sprites(self):
        """painting on the surface and create sprites"""
        Viewer.allgroup = pygame.sprite.LayeredUpdates()  # for drawing with layers
        Viewer.playergroup = pygame.sprite.Group()
        Viewer.ghostgroup = pygame.sprite.Group()
        Viewer.pillgroup = pygame.sprite.Group()  # GroupSingle
        Viewer.supergroup = pygame.sprite.Group()
        # assign classes to groups
        VectorSprite.groups = self.allgroup

        Player.groups = self.allgroup, self.playergroup
        Pill.groups = self.allgroup, self.pillgroup
        Ghost.groups = self.allgroup, self.ghostgroup

        #self.player1 = Player(x=10, y=9, picture = Viewer.images["player1"])
        for y, line in enumerate(Game.cells):
            for x, char in enumerate(line):
                if char == 0:
                    Pill(x=x, y=y, picture=Viewer.images["pill"])
                elif char == 2:
                    self.player1 = Player(x=x, y=x, xx=x, yy=y )
                    self.player1.startx = x
                    self.player1.starty = y
                elif char == 3:
                    pass # nothing
                # --- ghosts ---
                elif char == 4:
                    Ghost(x=x, y=y, animation_index = 0, images=Viewer.images_red,
                          startx = x, starty = y)
                elif char == 5:
                    Ghost(x=x, y=y, animation_index = 1, images=Viewer.images_green,
                          startx = x, starty = y)
                elif char == 6:
                    Ghost(x=x, y=y, animation_index = 2, images=Viewer.images_orange,
                          startx = x, starty = y)
                elif char == 7:
                    Ghost(x=x, y=y, animation_index = 3, images=Viewer.images_pink,
                          startx = x, starty = y)


    def check_player_ghost_collision(self):
        # ----- player vs. ghost:
        for player in self.playergroup:
            #crashgroup = pygame.sprite.spritecollide(player, self.ghostgroup, False, pygame.sprite.collide_rect)
            for ghost in self.ghostgroup:
                if player.x == ghost.x and player.y == ghost.y:
                    Game.lives -= 1
                    Flytext(pos=pygame.math.Vector2(player.pos.x, player.pos.y),
                            text="you lost a life! -- press Space key",
                            color=(200, 0, 0),
                            max_age=10,
                            fontsize=22)
                    self.wait_for_space = True
                    self.reset_monsters_and_player()
                    if Game.lives == 0:
                        Flytext(pos=pygame.math.Vector2(self.width // 2, self.height // 2),
                                text="Game over  - press space to restart",
                                color=(200, 0, 0),
                                max_age=10,
                                fontsize=44)
                        Game.lives = 3
                        Game.points = 0
                        self.reset_monsters_and_player()
                        # --- kill old pills ----
                        for p in self.pillgroup:
                            p.kill()
                        # create new pills
                        for y, line in enumerate(Game.cells):
                            for x, char in enumerate(line):
                                if char == 0:
                                    Pill(x=x, y=y, picture=Viewer.images["pill"])



                        # self.setup()
                    # break
                    return # only substract one life at max.

    def debug_positions(self):
        print("player:", self.player1.x, self.player1.y)
        for monster in self.ghostgroup:
            print("ghost ", monster.number, "x", monster.x, "y", monster.y)

    def move_monsters(self):
        #print("---before first check ----")
        #self.debug_positions()
        self.check_player_ghost_collision()
        #print("---move monsters ---")
        for monster in self.ghostgroup:
            monster.move_nesw()
        self.check_player_ghost_collision()
        #self.debug_positions()

    def move_player(self, dx, dy):
        #print("cell to go:", Game.cells[self.player1.y + dy][self.player1.x+dx])
        
        self.player1.xx += dx // 4
        self.player1.yy += dy // 4
        self.player1.pos.x += Viewer.cell_width * dx // 4
        self.player1.pos.y += Viewer.cell_height * dy // 4
        
        if self.player1.xx % 4 == 0:
            self.player1.x = self.player1.xx
        if self.player1.yy % 4 == 0:
            self.player1.y = self.player1.yy
            
        
        if Game.cells[self.player1.y][self.player1.x] in (0,2):
        # Player images
            if dx == 0 and dy == -1:
                Player.images = Viewer.images_north[:]
            elif dx == 0 and dy == 1:
                Player.images = Viewer.images_south[:]
            elif dx == 1 and dy == 0:
                Player.images = Viewer.images_east[:]
            elif dx == -1 and dy == 0:
                Player.images = Viewer.images_west[:]
            # move monsters
            self.move_monsters()

    def play(self):
        # ------- pressed and released key ------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False # running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                #if event.key == pygame.K_SPACE:
                #    self.move_monsters()  # player does nothing, but monsters move
                #    self.idle = 0
                #if event.key == pygame.K_UP:
                #    # check if north of player is free
                #    self.move_player(0, -1)
                #    self.idle = 0
                #if event.key == pygame.K_DOWN:
                #    self.move_player(0, 1)
                #    self.idle = 0
                #if event.key == pygame.K_LEFT:
                #    self.move_player(-1, 0)
                #    self.idle = 0
                #if event.key == pygame.K_RIGHT:
                #    self.move_player(1, 0)
                #    self.idle = 0

        if self.idle > Viewer.max_idle:
            # automatic turn because player did nothing for too long
            pressed_keys = pygame.key.get_pressed()
            if pressed_keys[pygame.K_UP]:
                self.move_player(0, -1)
            if pressed_keys[pygame.K_DOWN]:
                self.move_player(0, 1)
            if pressed_keys[pygame.K_LEFT]:
                self.move_player(-1, 0)
            if pressed_keys[pygame.K_RIGHT]:
                self.move_player(1, 0)
            self.move_monsters()
            self.idle = 0
        # ------------ pressed keys ------
        # pressed_keys = pygame.key.get_pressed()
        # ------ mouse handler ------
        # click_left, click_middle, click_right = pygame.mouse.get_pressed()
        # click_oldleft, click_oldmiddle, click_oldright = click_left, click_middle, click_right
        # ----------- collision detection ------------
        # ----- player vs pill ------
        for player in self.playergroup:
            crashgroup = pygame.sprite.spritecollide(player, self.pillgroup, True, pygame.sprite.collide_rect)
            # crashgroup_m = pygame.sprite.spritecollide(ship, crashgroup_r, True,  pygame.sprite.collide_mask)
            for pill in crashgroup:
                Game.points += 1
                for _ in range(5):
                    m = pygame.math.Vector2()
                    a = random.randint(0, 360)
                    w = random.randint(100, 150)
                    m.from_polar((w, a))
                    Spark(pos=pygame.math.Vector2(pill.pos.x, pill.pos.y),
                          move=m,
                          _layer=10,
                          color=(200, 200, 200),
                          max_age=0.8,
                          angle=a,
                          acceleration=0.95,
                          )
        # ---------------------------
        return True # running = True


    def reset_monsters_and_player(self):
        """teleport monsters and players back at start position"""
        self.player1.x = self.player1.startx
        self.player1.y = self.player1.starty
        self.player1.pos = pygame.math.Vector2(self.player1.x * Viewer.cell_width + Viewer.cell_width // 2,
                                               self.player1.y * Viewer.cell_height + Viewer.cell_height // 2)
        for m in self.ghostgroup:
            m.x = m.startx
            m.y = m.starty
            m.pos = pygame.math.Vector2(m.x * Viewer.cell_width + Viewer.cell_width // 2,
                                        m.y * Viewer.cell_height + Viewer.cell_height // 2)



    def run(self):
        """The mainloop"""

        running = True
        # pygame.mouse.set_visible(False)
        click_oldleft, click_oldmiddle, click_oldright = False, False, False
        # --------------------------- main loop --------------------------
        self.wait_for_space = True
        Flytext(text="press space to start",
                pos=pygame.math.Vector2(Viewer.width//2, Viewer.height * 0.8),
                fontsize=48,
                color = (0,222,0),
                max_age = 4,
                )
        while running:
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            self.playtime += seconds
            self.idle += seconds

            # ---------- clear all --------------
            # pygame.display.set_caption(f"player 1: {self.player1.deaths}   vs. player 2: {self.player2.deaths}")     #str(nesw))
            self.screen.blit(self.background, (0, 0))

            # -------- events ------
            #for event in pygame.event.get():
            #    if event.type == pygame.QUIT:
            #        running = False
            #    if event.type == pygame.KEYDOWN:
            #        if event.key == pygame.K_SPACE:
            #            print("Space!!!!!!")

            if not self.wait_for_space:
                running = self.play()
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                         running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.wait_for_space = False
                            #print("yeahhhhhh")
                            Flytext(text="let's go!")
            # ----------- writing on screen ----------

            # -------- write points ------------
            surf, rect = Viewer.font.render(
                text = f"lives: {Game.lives} points: {Game.points}  pills left: {len(self.pillgroup)}",
                fgcolor = (215,215,215),
                size=22
            )
            self.screen.blit(surf, (15, 15))
            # -------- fps -----------
            surf, rect = Viewer.font.render(
                text="fps: {:5.2f}".format(self.clock.get_fps()),
                fgcolor=(215, 215, 215),
                size=12,
            )
            self.screen.blit(surf, (15, Viewer.height - rect.height))
            # write angle of ship, angle to mouse
            # diff = pygame.math.Vector2(pygame.mouse.get_pos()-self.ship1.pos)
            # m = diff.as_polar()[1]
            pygame.display.set_caption("pac man")

            # --------- update all sprites ----------------
            self.allgroup.update(seconds)

            # ---------- blit all sprites --------------
            self.allgroup.draw(self.screen)
            pygame.display.flip()
            # -----------------------------------------------------
        pygame.mouse.set_visible(True)
        pygame.quit()
        # try:
        #    sys.exit()
        # finally:
        #    pygame.quit()


## -------------------- functions --------------------------------

def between(value, lower_limit=0, upper_limit=255):
    """makes sure a (color) value stays between a lower and a upper limit ( 0 and 255 )

    :param float value: the value that should stay between min and max
    :param float lower_limit:  the minimum value (lower limit)
    :param float upper_limit:  the maximum value (upper limit)
    :return: new_value"""
    return lower_limit if value < lower_limit else upper_limit if value > upper_limit else value


def cmp(a, b):
    """compares a with b, returns 1 if a > b, returns 0 if a==b and returns -1 if a < b"""
    return (a > b) - (a < b)


def randomize_colors(color, by=30):
    """randomize each color of a r,g,b tuple by the amount of +- by
    while staying between 0 and 255
    returns a color tuple"""
    r, g, b = color
    r += random.randint(-by, by)
    g += random.randint(-by, by)
    b += random.randint(-by, by)
    r = between(r)  # 0<-->255
    g = between(g)
    b = between(b)
    return r, g, b


def write(background, text, x=50, y=150, color=(0, 0, 0),
          font_size=None, font_name="mono", bold=True, origin="topleft"):
    """blit text on a given pygame surface (given as 'background')
       the origin is the alignment of the text surface
       origin can be 'center', 'centercenter', 'topleft', 'topcenter', 'topright', 'centerleft', 'centerright',
       'bottomleft', 'bottomcenter', 'bottomright'
    """
    if font_size is None:
        font_size = 24
    font = pygame.font.SysFont(font_name, font_size, bold)
    width, height = font.size(text)
    surface = font.render(text, True, color)

    if origin == "center" or origin == "centercenter":
        background.blit(surface, (x - width // 2, y - height // 2))
    elif origin == "topleft":
        background.blit(surface, (x, y))
    elif origin == "topcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "topright":
        background.blit(surface, (x - width, y))
    elif origin == "centerleft":
        background.blit(surface, (x, y - height // 2))
    elif origin == "centerright":
        background.blit(surface, (x - width, y - height // 2))
    elif origin == "bottomleft":
        background.blit(surface, (x, y - height))
    elif origin == "bottomcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "bottomright":
        background.blit(surface, (x - width, y - height))


if __name__ == "__main__":
    # g = Game()
    Viewer(
        width=1200,
        height=800,
    )
