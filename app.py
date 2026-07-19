import math
import random
import time

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

try:
    import power
    HAS_POWER = True
except ImportError:
    HAS_POWER = False

try:
    import imu
    HAS_IMU = True
except ImportError:
    HAS_IMU = False

try:
    import settings
    HAS_SETTINGS = True
except ImportError:
    HAS_SETTINGS = False

try:
    from system.scheduler.events import RequestForegroundPushEvent
    HAS_SUMMON = True
except ImportError:
    HAS_SUMMON = False

# Touch pads (2026 frontboard): TOUCH01..TOUCH12 arrive as button events
try:
    from system.eventbus import eventbus as touch_eventbus
    from events.input import ButtonDownEvent
    HAS_TOUCH = True
except ImportError:
    HAS_TOUCH = False

# --- Timings (all in milliseconds) ---
HUNGRY_AFTER_MIN = 2 * 60 * 60 * 1000   # gets hungry after 2...
HUNGRY_AFTER_MAX = 3 * 60 * 60 * 1000   # ...to 3 hours
PET_HAPPY_TIME = 2500                   # reaction time after a pet
EAT_TIME = 3000                         # munching time
SLEEPY_TIME = 20000                     # nap after too much petting
PETS_UNTIL_SLEEPY = 5                   # pets in quick succession before nap
PET_MEMORY = 15000                      # how long "quick succession" lasts
PALETTE_FLASH_TIME = 1500               # how long the palette name shows
IDLE_FLOP_TIME = 4000                   # how long the content flop lasts
IDLE_LOOK_TIME = 5000                   # glances hold longer
IDLE_CONTENT = 0                        # idle moments: content smile...
IDLE_LOOK_L = 1                         # ...glance left...
IDLE_LOOK_UR = 2                        # ...glance up-right
NAP_AFTER_MIN = 120000                  # spontaneous nap after 2...
NAP_AFTER_MAX = 240000                  # ...to 4 quiet minutes
NAP_MIN = 30000                         # spontaneous naps last 30-60s
NAP_MAX = 60000
BATTERY_FLASH_TIME = 4000               # how long the battery peek shows
BATT_SAMPLE_MS = 60000                  # battery sampled once a minute
STROKE_WINDOW = 900                     # two touch pads within this = a stroke

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

# The same flop mirrored to the right ear (for strokes on the right)
EARS_FLOP_R = ["".join(reversed(row)) for row in EARS_FLOP]

# Touch pads follow the LED clock layout: 12/1 top, 2-5 right side,
# 6/7 bottom, 8-11 left side
RIGHT_PADS = (1, 2, 3, 4, 5)
LEFT_PADS = (8, 9, 10, 11, 12)

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
EYE_LOOK = ["X", "X"]          # narrow glancing eyes (look left / up-right)
EYE_SLEEPY = ["XX"]            # nap lines, drawn low and wide
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
        self.pet_ear = None             # which ear flops during a stroke pet

        self.palette_index = 0
        self.palette_flash = 0          # shows the palette name briefly
        self._apply_palette()

        # Blinking, and the occasional lazy ear flop while idle
        self.blink_timer = self._new_blink_timer()
        self.blinking = 0
        self.idle_flop = 0
        self.idle_flop_timer = self._new_flop_timer()
        self.idle_kind = IDLE_CONTENT
        self.idle_queue = []
        self.nap_timer = self._new_nap_timer()

        self.last_leds = None

        # Battery peek + learned drain rate (persisted across restarts)
        self.battery_flash = 0
        self.batt_level = None
        self.batt_charging = False
        self.batt_sample_timer = 1000   # first sample shortly after launch
        self._batt_anchor = None        # (time, level) drain measurement anchor
        self.drain_rate = 0.0           # % per hour
        self.drain_n = 0
        if HAS_SETTINGS:
            self.drain_rate = settings.get("bunbun_drain_pph", 0.0) or 0.0
            self.drain_n = settings.get("bunbun_drain_n", 0) or 0

        # Flip the screen when the badge is lifted up to face the wearer
        self.flipped = False
        self.imu_timer = 0

        # Stroke-to-pet via the 2026 board touch pads
        self._last_beat = 0
        self._touch_last = None
        self._touch_last_t = -STROKE_WINDOW
        if HAS_TOUCH:
            touch_eventbus.on(ButtonDownEvent, self._on_button_down, self)

    def _new_hunger_timer(self):
        return random.randint(HUNGRY_AFTER_MIN, HUNGRY_AFTER_MAX)

    def _new_blink_timer(self):
        return random.randint(1500, 4000)

    def _new_flop_timer(self):
        return random.randint(8000, 18000)

    def _new_nap_timer(self):
        return random.randint(NAP_AFTER_MIN, NAP_AFTER_MAX)

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
        self._last_beat = self._ticks()

        # Battery: sample once a minute, learn the drain rate
        self.batt_sample_timer -= delta
        if self.batt_sample_timer <= 0:
            self.batt_sample_timer = BATT_SAMPLE_MS
            self._sample_battery()
        if self.battery_flash > 0:
            self.battery_flash -= delta

        # Lifted-to-look detection: when the badge tips past vertical the
        # gravity reading along its top-bottom axis flips sign
        if HAS_IMU:
            self.imu_timer -= delta
            if self.imu_timer <= 0:
                self.imu_timer = 250
                try:
                    ax = imu.acc_read()[0]
                    if not self.flipped and ax < -3:
                        self.flipped = True
                    elif self.flipped and ax > 3:
                        self.flipped = False
                except Exception:
                    pass

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

        # Occasional lazy idle moments while chilling, and after a few
        # quiet minutes it drifts off for a little nap on its own
        if self.state == CHILL and self.happy_timer <= 0:
            if self.idle_flop > 0:
                self.idle_flop -= delta
                if self.idle_flop <= 0 and self.idle_queue:
                    self.idle_kind = self.idle_queue.pop(0)
                    self.idle_flop = IDLE_LOOK_TIME
            else:
                self.idle_flop_timer -= delta
                if self.idle_flop_timer <= 0:
                    self.idle_flop_timer = self._new_flop_timer()
                    if random.randint(0, 1) == 0:
                        self.idle_kind = IDLE_CONTENT
                        self.idle_queue = []
                        self.idle_flop = IDLE_FLOP_TIME
                    else:
                        self.idle_kind = IDLE_LOOK_L
                        self.idle_queue = [IDLE_LOOK_UR]
                        self.idle_flop = IDLE_LOOK_TIME
            self.nap_timer -= delta
            if self.nap_timer <= 0:
                self.state = SLEEPY
                self.state_timer = random.randint(NAP_MIN, NAP_MAX)
                self.idle_flop = 0
                self.nap_timer = self._new_nap_timer()
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
            elif self.button_states.get(BUTTON_TYPES["UP"]):
                # A = battery peek (small overlay, bunny stays visible)
                self.button_states.clear()
                self._sample_battery()
                self.battery_flash = BATTERY_FLASH_TIME
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

    def _pet(self, ear=None):
        # One pet at a time: while a reaction is playing, extra strokes
        # and presses are part of the same pet, not a new one
        if self.happy_timer > 0:
            return
        self.pet_ear = ear
        self.happy_timer = PET_HAPPY_TIME
        self.idle_flop = 0
        self.nap_timer = self._new_nap_timer()

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
        self.nap_timer = self._new_nap_timer()

    # -------------------------------------------------------------- touch

    def _ticks(self):
        if hasattr(time, "ticks_ms"):
            return time.ticks_ms()
        return int(time.time() * 1000)

    def _is_foreground(self):
        # Foreground apps get update() every frame; if the heartbeat is
        # stale, another app (or the menu) has the screen
        now = self._ticks()
        if hasattr(time, "ticks_diff"):
            return time.ticks_diff(now, self._last_beat) < 500
        return now - self._last_beat < 500

    def _on_button_down(self, event):
        name = getattr(event.button, "name", "")
        foreground = self._is_foreground()

        # Keyboard hexpansion: press B anywhere to summon BunBun
        if name == "B" and not foreground and HAS_SUMMON:
            touch_eventbus.emit(RequestForegroundPushEvent(self))
            return

        # Stroking two different touch pads in quick succession = a pet
        if not name.startswith("TOUCH") or not foreground:
            return
        if self.state == SLEEPY:
            self.state = CHILL
            self.recent_pets = 0
            return
        if self.state not in (CHILL, HUNGRY):
            return
        if (
            self._touch_last is not None
            and name != self._touch_last
            and self.time - self._touch_last_t < STROKE_WINDOW
        ):
            # Stroked along one side? That ear flops toward your hand
            try:
                a = int(self._touch_last[5:])
                b = int(name[5:])
            except ValueError:
                a = b = 0
            on_right = a in RIGHT_PADS or b in RIGHT_PADS
            on_left = a in LEFT_PADS or b in LEFT_PADS
            ear = None
            if on_right and not on_left:
                ear = "R"
            elif on_left and not on_right:
                ear = "L"
            # When the screen is flipped the drawing rotates 180 but the
            # pads don't move — swap sides so the ear follows the hand
            if ear and self.flipped:
                ear = "L" if ear == "R" else "R"

            self._touch_last = None
            self._pet(ear)
        else:
            self._touch_last = name
            self._touch_last_t = self.time

    # ------------------------------------------------------------ battery

    def _sample_battery(self):
        if not HAS_POWER:
            return
        try:
            level = power.BatteryLevel()
            state = power.BatteryChargeState()
        except Exception:
            return
        self.batt_level = level
        self.batt_charging = state != "Not Charging"

        # Learn the drain rate: measure % lost between two points in time.
        # Charging invalidates the measurement window.
        if self.batt_charging:
            self._batt_anchor = None
            return
        if self._batt_anchor is None:
            self._batt_anchor = (self.time, level)
            return
        t0, l0 = self._batt_anchor
        if level > l0 + 0.5:
            # Level went up: got charged in between, restart measurement
            self._batt_anchor = (self.time, level)
        elif level < l0 - 0.4:
            hours = (self.time - t0) / 3600000
            if hours > 0:
                rate = (l0 - level) / hours
                if 0 < rate < 60:
                    if self.drain_rate > 0:
                        self.drain_rate = self.drain_rate * 0.8 + rate * 0.2
                    else:
                        self.drain_rate = rate
                    self.drain_n += 1
                    if HAS_SETTINGS and self.drain_n % 3 == 0:
                        settings.set("bunbun_drain_pph", self.drain_rate)
                        settings.set("bunbun_drain_n", self.drain_n)
                        settings.save()
            self._batt_anchor = (self.time, level)

    def _battery_text(self):
        if self.batt_level is None:
            return "battery ?"
        text = "{}%".format(int(self.batt_level))
        if self.batt_charging:
            return text + " charging"
        if self.drain_rate > 0.3 and self.drain_n >= 3:
            mins = int(self.batt_level / self.drain_rate * 60)
            if mins >= 60:
                return "{} ~{}h{:02d}m".format(text, mins // 60, mins % 60)
            return "{} ~{}m".format(text, mins)
        return text + " learning..."

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
        ctx.save()
        if self.flipped:
            ctx.rotate(math.pi)

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

        # Hungry = crying with both ears down; a stroke pet flops the ear
        # on the stroked side; relaxing/napping = one lazy flopped ear.
        # Never floppy while jumping.
        stroke_ear = (
            self.pet_ear
            if self.happy_timer > 0 and self.reaction != REACT_BOUNCE
            else None
        )
        if hungry:
            ears = EARS_SAD
        elif stroke_ear == "L":
            ears = EARS_FLOP
        elif stroke_ear == "R":
            ears = EARS_FLOP_R
        elif (flopping and self.idle_kind == IDLE_CONTENT) or sleepy:
            ears = EARS_FLOP
        else:
            ears = EARS_UP
        self._blit_grid(ctx, ears, 0, 0)
        self._blit_grid(ctx, LOWER, 0, 10)

        # Eyes (cols 8/17, row 13)
        idle_kind = self.idle_kind if flopping else None
        if sleepy:
            self._blit_grid(ctx, EYE_SLEEPY, 6, 14)
            self._blit_grid(ctx, EYE_SLEEPY, 19, 14)
        elif idle_kind == IDLE_LOOK_L:
            # Glances hold uninterrupted - no blinking mid-sequence
            self._blit_grid(ctx, EYE_LOOK, 7, 12)
            self._blit_grid(ctx, EYE_LOOK, 16, 12)
        elif idle_kind == IDLE_LOOK_UR:
            self._blit_grid(ctx, EYE_LOOK, 9, 11)
            self._blit_grid(ctx, EYE_LOOK, 18, 11)
        elif (
            self.blinking > 0 or hungry or idle_kind == IDLE_CONTENT
            or (self.happy_timer > 0 and self.reaction == REACT_STARS)
        ):
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
        elif self.happy_timer > 0 and self.reaction == REACT_STARS:
            self._blit_grid(ctx, W_SMILE, 11, 15)    # content face
        elif happy:
            self._blit_grid(ctx, NOSE_PATCH, 12, 15)
            self._blit_grid(ctx, SMILE_ARC, 11, 15)  # happy face
        elif flopping and self.idle_kind == IDLE_CONTENT:
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
        if self.battery_flash > 0:
            ctx.font_size = 15
            batt = self._battery_text()
            ctx.rgb(*self.colors["X"]).move_to(0, -102).text(batt)
            ctx.move_to(0.9, -102.5).text(batt)
            ctx.move_to(0.5, -101.5).text(batt)
        elif self.palette_flash > 0:
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

        ctx.restore()

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
