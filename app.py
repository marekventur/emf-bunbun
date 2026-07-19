import math
import random

from app import App
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES

# LEDs: not available in every simulator build, so we fall back gracefully.
try:
    from tildagonos import tildagonos
    from system.eventbus import eventbus
    from system.patterndisplay.events import PatternDisable, PatternEnable
    HAS_LEDS = True
except ImportError:
    HAS_LEDS = False

# --- Timings (all in milliseconds) ---
HUNGRY_AFTER_MIN = 2 * 60 * 60 * 1000   # gets hungry after 2...
HUNGRY_AFTER_MAX = 3 * 60 * 60 * 1000   # ...to 3 hours
PET_HAPPY_TIME = 2500                   # reaction time after a pet
EAT_TIME = 3000                         # munching time
SLEEPY_TIME = 20000                     # nap after too much petting
PETS_UNTIL_SLEEPY = 6                   # pets in quick succession before nap
PET_MEMORY = 10000                      # how long "quick succession" lasts
PALETTE_FLASH_TIME = 1500               # how long the palette name shows
IDLE_FLOP_TIME = 4000                   # how long a lazy ear-flop moment lasts

# Pet states
CHILL = 0
HUNGRY = 1
EATING = 2
SLEEPY = 3

# Pet reactions (rotated so petting stays fun)
REACT_HEARTS = 0
REACT_STARS = 1
REACT_BOUNCE = 2

# --- Pixel art ---
# All art is Marek's drawings (BunnyRabbitcarol*.png), converted to
# 27-wide grids of chunky "art pixels", PX screen pixels each. The face
# intentionally bleeds off the bottom of the round screen.
PX = 8
ORIGIN_X = -108  # grid col 0 in screen coords (screen center is 0,0)
ORIGIN_Y = -88   # grid row 0 (leaves breathing room above the ears)

# Fixed colors, shared by all palettes
FIXED_COLORS = {
    "o": (1.0, 1.0, 1.0),       # fur
    "g": (0.30, 0.65, 0.30),    # carrot greens
    "O": (0.90, 0.50, 0.10),    # carrot
    "b": (0.01, 0.64, 1.0),     # tear
}

# Curated color combos: (name, outline "X", accent "p", bg top, bg bottom).
# Cycled with the down button — hand-picked, no random ugly pairings.
# Light-outlined bunnies get dark night backgrounds for contrast;
# dark-outlined bunnies keep the light background for the same reason.
LIGHT_BG = ((1.0, 0.80, 0.87), (0.75, 0.69, 0.93))         # pink -> lilac
PLUM_BG = ((0.24, 0.13, 0.26), (0.10, 0.06, 0.16))         # dusk plum
NAVY_BG = ((0.10, 0.13, 0.27), (0.04, 0.06, 0.15))         # midnight navy
PALETTES = [
    ("carol", (1.0, 0.447, 0.361), (1.0, 0.957, 0.69)) + PLUM_BG,
    ("choco", (0.40, 0.26, 0.18), (1.0, 0.447, 0.361)) + LIGHT_BG,
    ("sky", (0.55, 0.65, 0.90), (0.97, 0.62, 0.72)) + NAVY_BG,
    ("berry", (0.75, 0.30, 0.45), (1.0, 0.80, 0.85)) + LIGHT_BG,
]

HEART_COLOR = {"X": (0.90, 0.20, 0.40)}
STAR_COLOR = {"X": (1.0, 0.72, 0.15)}
ZZZ_COLOR = {"X": (0.48, 0.40, 0.62)}

# Background gradient bands
BG_BANDS = 12

# Ears, rows 0-9 of the grid: both up, or left one lazily flopped over
# (from BunnyRabbitcarol2_eardrop.png)
EARS_UP = [
    "........XXX.....XXX........",
    ".......XoooX...XoooX.......",
    "......XoooooX.XoooooX......",
    "......XppoooX.XoooppX......",
    "......XpppooX.XoopppX......",
    "......XpppooX.XoopppX......",
    "......XpppooX.XoopppX......",
    "......XpppooX.XoopppX......",
    "......XpppoooXooopppX......",
    "......XppooooXooooppX......",
]
EARS_FLOP = [
    "................XXX........",
    "...............XoooX.......",
    ".....XXXXXX...XoooooX......",
    "....XooooooX..XoooppX......",
    "...XooooooooX.XoopppX......",
    "...XoppppoooX.XoopppX......",
    "....XXppppooX.XoopppX......",
    "......XpppooX.XoopppX......",
    "......XpppoooXooopppX......",
    "......XppooooXooooppX......",
]
# Both ears down (hungry/crying): the flopped ear mirrored to both sides
EARS_SAD = [
    "...........................",
    "...........................",
    ".....XXXXXX.....XXXXXX.....",
    "....XooooooX...XooooooX....",
    "...XooooooooX.XooooooooX...",
    "...XoppppoooX.XoooppppoX...",
    "....XXppppooX.XooppppXX....",
    "......XpppooX.XoopppX......",
    "......XpppoooXooopppX......",
    "......XppooooXooooppX......",
]

# Head and face, rows 10+ (eyes blanked out so expressions can swap in;
# the ∴ nose/mouth and cheeks stay as drawn).
LOWER = [
    "......XoooooooooooooX......",
    ".....XXoooooooooooooXX.....",
    "....XXoooooooooooooooXX....",
    "...XXoooooooooooooooooXX...",
    "...XoooooooooooooooooooX...",
    "..XXoooooooooXoooooooooXX..",
    "..XopppppoooXoXooopppppoX..",
    "..XopppppooooooooopppppoX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
    "..XoooooooooooooooooooooX..",
]

# Faces, all from Marek's expression drawings. Eyes go at cols 8/17,
# row 13. Mouths sit under the nose, centered on col 13.
EYE_OPEN = ["XX", "XX"]        # base drawing
EYE_FLAT = ["XX"]              # chill/content line eyes
TEAR = ["b", "b"]

NOSE_PATCH = ["ooo"]                      # hides the nose dot at (12,15)
SMILE_ARC = ["X...X", ".XXX."]            # happy: big open smile (11,15)
W_SMILE = ["X.X.X", "XXXXX"]              # content: little w smile (11,15)
MOUTH_FLAT = ["XXX"]                      # chill/hungry flat mouth (12,16)
CRY_MOUTH = ["X...X"]                     # crying wail row (11,17)
EAT_MOUTH = ["XXX", "XoX", "XoX", "XXX", "XXX"]  # big open O, from the
                                          # eat drawing, at (12,13)

HEART_SPRITE = [".X.X.", "XXXXX", "XXXXX", ".XXX.", "..X.."]
STAR_SPRITE = ["..X..", ".XXX.", "XXXXX", ".XXX.", "..X.."]
Z_SPRITE = ["XXX", "..X", ".X.", "X..", "XXX"]
CARROT = [".g.g.", "..g..", "OOOOO", ".OOO.", ".OOO.", "..O.."]


class Bunny(App):
    def __init__(self):
        super().__init__()
        self.button_states = Buttons(self)

        # Take over the LED ring from the OS default rainbow spinner.
        if HAS_LEDS:
            eventbus.emit(PatternDisable())

        self.state = CHILL
        self.time = 0                   # total ms since app start
        self.hunger_timer = self._new_hunger_timer()
        self.happy_timer = 0            # >0 means a pet reaction is playing
        self.reaction = REACT_HEARTS
        self.state_timer = 0            # countdown for EATING / SLEEPY
        self.recent_pets = 0
        self.pet_memory = 0
        self.particles = []             # floating hearts/stars: [x, y, age, kind, px]
        self.hop = 0                    # vertical offset for the bounce reaction

        self.palette_index = 0
        self.palette_flash = 0          # shows the palette name briefly
        self._apply_palette()

        # Blinking, and the occasional lazy ear flop while idle
        self.blink_timer = self._new_blink_timer()
        self.blinking = 0
        self.idle_flop = 0
        self.idle_flop_timer = self._new_flop_timer()

        self.last_leds = None

    def _new_hunger_timer(self):
        return random.randint(HUNGRY_AFTER_MIN, HUNGRY_AFTER_MAX)

    def _new_blink_timer(self):
        return random.randint(2500, 6000)

    def _new_flop_timer(self):
        return random.randint(15000, 40000)

    def _apply_palette(self):
        name, outline, accent, bg_top, bg_bottom = PALETTES[self.palette_index]
        self.palette_name = name
        self.colors = dict(FIXED_COLORS)
        self.colors["X"] = outline
        self.colors["p"] = accent
        self.bg_top = bg_top
        self.bg_bottom = bg_bottom

    # ------------------------------------------------------------- update

    def update(self, delta):
        self.time += delta

        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self._leds_off()
            if HAS_LEDS:
                eventbus.emit(PatternEnable())  # give LEDs back to the OS
            self.minimise()
            return

        # Blinking (not while asleep, lids are closed anyway)
        self.blink_timer -= delta
        if self.blink_timer <= 0:
            self.blinking = 180
            self.blink_timer = self._new_blink_timer()
        if self.blinking > 0:
            self.blinking -= delta

        # Occasional lazy ear-flop moment while idle
        if self.state == CHILL and self.happy_timer <= 0:
            if self.idle_flop > 0:
                self.idle_flop -= delta
            else:
                self.idle_flop_timer -= delta
                if self.idle_flop_timer <= 0:
                    self.idle_flop = IDLE_FLOP_TIME
                    self.idle_flop_timer = self._new_flop_timer()
        else:
            self.idle_flop = 0

        # Getting hungry over time
        if self.state == CHILL:
            self.hunger_timer -= delta
            if self.hunger_timer <= 0:
                self.state = HUNGRY

        # Forget rapid petting after a while
        if self.pet_memory > 0:
            self.pet_memory -= delta
            if self.pet_memory <= 0:
                self.recent_pets = 0

        # Buttons
        if self.state == SLEEPY:
            # Any button wakes it instantly
            for name in ("CONFIRM", "UP", "DOWN", "LEFT", "RIGHT"):
                if self.button_states.get(BUTTON_TYPES[name]):
                    self.button_states.clear()
                    self.state = CHILL
                    self.recent_pets = 0
                    break
        elif self.state in (CHILL, HUNGRY):
            if self.button_states.get(BUTTON_TYPES["CONFIRM"]):
                # C = pet
                self.button_states.clear()
                self._pet()
            elif self.button_states.get(BUTTON_TYPES["LEFT"]):
                # E = feed
                self.button_states.clear()
                self._feed()
            elif self.button_states.get(BUTTON_TYPES["DOWN"]):
                # D = colour
                self.button_states.clear()
                self.palette_index = (self.palette_index + 1) % len(PALETTES)
                self._apply_palette()
                self.palette_flash = PALETTE_FLASH_TIME
            elif self.button_states.get(BUTTON_TYPES["RIGHT"]):
                # Dev shortcut (B): fast-forward straight to hungry
                self.button_states.clear()
                self.state = HUNGRY

        if self.palette_flash > 0:
            self.palette_flash -= delta

        # Timed states
        if self.state == EATING:
            self.state_timer -= delta
            if self.state_timer <= 0:
                self.state = CHILL
                self.hunger_timer = self._new_hunger_timer()
                self.happy_timer = PET_HAPPY_TIME  # happy after a meal
                self.reaction = REACT_HEARTS
        elif self.state == SLEEPY:
            self.state_timer -= delta
            if self.state_timer <= 0:
                self.state = CHILL
                self.recent_pets = 0

        # Pet reaction plays out
        if self.happy_timer > 0:
            self.happy_timer -= delta
        if self.happy_timer > 0 and self.reaction == REACT_BOUNCE:
            # Snappy square-wave hops: instantly up, hold, instantly down
            t = PET_HAPPY_TIME - self.happy_timer
            in_air = t < 220 or 380 <= t < 600 or 760 <= t < 980
            self.hop = -16 if in_air else 0
        else:
            self.hop = 0

        # Particles float up, each twinkling to its own rhythm
        alive = []
        for part in self.particles:
            part[1] -= delta * 0.03   # float upwards
            part[2] += delta          # age
            if part[2] < part[6]:     # own lifetime
                alive.append(part)
        self.particles = alive

        self._update_leds()

    def _pet(self):
        self.happy_timer = PET_HAPPY_TIME
        self.idle_flop = 0

        # Pick a different reaction than last time
        choices = [REACT_HEARTS, REACT_STARS, REACT_BOUNCE]
        choices.remove(self.reaction)
        self.reaction = random.choice(choices)

        if self.reaction == REACT_HEARTS:
            self._spawn_particles("heart", 6)
        elif self.reaction == REACT_STARS:
            self._spawn_particles("star", 7)
        else:  # bounce: one big heart above the hop
            self.particles.append([-14, -95, 0, "heart", 7, 350, 2200])

        self.recent_pets += 1
        self.pet_memory = PET_MEMORY
        if self.recent_pets >= PETS_UNTIL_SLEEPY:
            self.state = SLEEPY
            self.state_timer = SLEEPY_TIME
            self.happy_timer = 0
            self.particles = []

    def _spawn_particles(self, kind, count):
        # Scattered across the whole screen, each with its own size,
        # twinkle rhythm, and lifespan so they never move in lockstep.
        # New spawns keep their distance from each other to avoid clumps.
        for _ in range(count):
            for _attempt in range(12):
                x = random.randint(-105, 70)
                y = random.randint(-95, 45)
                clear = True
                for p in self.particles:
                    dx = p[0] - x
                    dy = p[1] - y
                    if dx * dx + dy * dy < 55 * 55:
                        clear = False
                        break
                if clear:
                    break
            self.particles.append([
                x,
                y,
                0,
                kind,
                random.randint(4, 8),        # chunky pixel size
                random.randint(160, 420),    # twinkle period
                random.randint(1400, 2600),  # lifetime
            ])

    def _feed(self):
        self.state = EATING
        self.state_timer = EAT_TIME
        self.idle_flop = 0

    # --------------------------------------------------------------- LEDs

    def _update_leds(self):
        if not HAS_LEDS:
            return
        if self.happy_timer > 0:
            # Glow fading out as the happy moment passes
            level = self.happy_timer / PET_HAPPY_TIME
            if self.reaction == REACT_STARS:
                color = (int(255 * level), int(180 * level), int(30 * level))
            else:
                color = (int(255 * level), int(60 * level), int(120 * level))
        elif self.state == HUNGRY:
            # Slow orange "breathing" pulse so passers-by can alert you
            level = (math.sin(self.time / 700) + 1) / 2  # 0..1
            level = 0.08 + 0.35 * level                  # keep it battery-kind
            color = (int(255 * level), int(90 * level), 0)
        else:
            color = (0, 0, 0)

        if color != self.last_leds:
            for i in range(1, 13):
                tildagonos.leds[i] = color
            tildagonos.leds.write()
            self.last_leds = color

    def _leds_off(self):
        if not HAS_LEDS:
            return
        for i in range(1, 13):
            tildagonos.leds[i] = (0, 0, 0)
        tildagonos.leds.write()
        self.last_leds = (0, 0, 0)

    # ------------------------------------------------------ pixel drawing

    def _blit(self, ctx, rows, ox, oy, px, colors):
        # Draw a sprite. Runs of the same colour become one rectangle,
        # which keeps the draw call count low for the badge.
        for ry, row in enumerate(rows):
            x = 0
            while x < len(row):
                c = row[x]
                if c == ".":
                    x += 1
                    continue
                x2 = x
                while x2 < len(row) and row[x2] == c:
                    x2 += 1
                ctx.rgb(*colors[c]).rectangle(
                    ox + x * px, oy + ry * px, (x2 - x) * px, px
                ).fill()
                x = x2

    def _blit_grid(self, ctx, rows, gx, gy, colors=None):
        self._blit(
            ctx, rows,
            ORIGIN_X + gx * PX, ORIGIN_Y + gy * PX + self.hop, PX,
            colors or self.colors,
        )

    # --------------------------------------------------------------- draw

    def draw(self, ctx):
        clear_background(ctx)

        # Palette background gradient in chunky horizontal bands
        top, bottom = self.bg_top, self.bg_bottom
        band_h = 240 / BG_BANDS
        for i in range(BG_BANDS):
            t = i / (BG_BANDS - 1)
            ctx.rgb(
                top[0] + (bottom[0] - top[0]) * t,
                top[1] + (bottom[1] - top[1]) * t,
                top[2] + (bottom[2] - top[2]) * t,
            ).rectangle(-120, -120 + i * band_h, 240, band_h + 1).fill()

        hungry = self.state == HUNGRY
        sleepy = self.state == SLEEPY
        happy = self.happy_timer > 0 or self.state == EATING
        flopping = self.idle_flop > 0

        # Hungry = crying with both ears down; relaxing/napping = one
        # lazy flopped ear. Never floppy while jumping.
        if hungry:
            ears = EARS_SAD
        elif flopping or sleepy:
            ears = EARS_FLOP
        else:
            ears = EARS_UP
        self._blit_grid(ctx, ears, 0, 0)
        self._blit_grid(ctx, LOWER, 0, 10)

        # Eyes (cols 8/17, row 13)
        line_eyes = (
            sleepy or self.blinking > 0 or hungry or flopping
            or (self.happy_timer > 0 and self.reaction == REACT_STARS)
        )
        if line_eyes:
            self._blit_grid(ctx, EYE_FLAT, 8, 13)
            self._blit_grid(ctx, EYE_FLAT, 17, 13)
        else:
            self._blit_grid(ctx, EYE_OPEN, 8, 13)
            self._blit_grid(ctx, EYE_OPEN, 17, 13)

        if hungry:
            self._blit_grid(ctx, TEAR, 8, 14)

        # Mouths (all from Marek's expression drawings)
        if self.state == EATING:
            # Chew: alternate Marek's big open O-mouth with a closed flat
            # mouth (the O covers the nose; closed frames show it again)
            if (self.time // 250) % 2 == 0:
                self._blit_grid(ctx, EAT_MOUTH, 12, 13)
            else:
                self._blit_grid(ctx, MOUTH_FLAT, 12, 16)
            self._draw_carrot(ctx)
        elif hungry:
            self._blit_grid(ctx, CRY_MOUTH, 11, 17)
        elif sleepy:
            self._blit_grid(ctx, MOUTH_FLAT, 12, 16)
        elif self.happy_timer > 0 and self.reaction == REACT_STARS:
            self._blit_grid(ctx, W_SMILE, 11, 15)    # content face
        elif happy:
            self._blit_grid(ctx, NOSE_PATCH, 12, 15)
            self._blit_grid(ctx, SMILE_ARC, 11, 15)  # happy face
        elif flopping:
            self._blit_grid(ctx, W_SMILE, 11, 15)    # lazy content flop
        # plain chill: face stays exactly as drawn

        if sleepy:
            self._draw_zzz(ctx)
        for part in self.particles:
            # Twinkle: each particle flashes on/off to its own rhythm
            if (part[2] // part[5]) % 2 == 1:
                continue
            sprite = STAR_SPRITE if part[3] == "star" else HEART_SPRITE
            color = STAR_COLOR if part[3] == "star" else HEART_COLOR
            self._blit(ctx, sprite, part[0], part[1], part[4], color)

        # Text overlays
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        if self.palette_flash > 0:
            ctx.font_size = 14
            ctx.rgb(*self.colors["X"]).move_to(0, -102).text(self.palette_name)
        ctx.font_size = 13
        if hungry:
            ctx.rgb(0.80, 0.30, 0.10).move_to(0, 88).text("I'm hungry!")
            ctx.rgb(0.80, 0.30, 0.10).move_to(0, 104).text("E = feed")
        elif sleepy:
            ctx.rgb(0.48, 0.40, 0.62).move_to(0, 100).text("shhh... napping")
        elif self.state == CHILL:
            # Rotate through the instructions so all buttons get explained
            hints = ("C = pet", "D = colour", "E = feed")
            hint = hints[(self.time // 3000) % 3]
            ctx.rgb(0.80, 0.60, 0.55).move_to(0, 100).text(hint)

    def _draw_carrot(self, ctx):
        # Big carrot right in front of the mouth, shrinking as it's eaten
        size = max(0.2, self.state_timer / EAT_TIME)
        px = 13 * size
        self._blit(ctx, CARROT, -2.5 * px, 58, px, self.colors)

    def _draw_zzz(self, ctx):
        wob = math.sin(self.time / 400) * 3
        self._blit(ctx, Z_SPRITE, 52, -50 + wob, 3, ZZZ_COLOR)
        self._blit(ctx, Z_SPRITE, 68, -70 - wob, 4, ZZZ_COLOR)


__app_export__ = Bunny
