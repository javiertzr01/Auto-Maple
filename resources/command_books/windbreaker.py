"""A collection of all commands that Adele can use to interact with the game. 	"""
import time
import math

# pylint: disable=import-error
from src.common import config, settings, utils
from src.routine.components import Command, Walk
from src.common.vkeys import press, key_down, key_up
# pylint: enable=import-error

# List of key mappings
class Key:
    # Movement
    JUMP = 'space'
    GUST_SHIFT = 'space'
    WIND_WALK = 'shift'

    # Buffs
    CYGNUS_KNIGHTS = '0'
    SHARP_EYES = '-'
    STORM_BRINGER = '='
    STORM_WINDS = '9'
    GLORY_OF_GUARDIANS = '8'

    # Buffs Toggle
    ELEMENT_INFUSION = 'home'
    TRIFLING_WINDS = 'insert'

    # Attacks
    WIND_FLOURISH = 'x'
    CYCLONE = 'c'  #Hold#
    CYGNUS_KNIGHTS_WILL = 'ctrl'

    # Debuff
    PINPOINT_MARK = 'd'

    # Decoy
    EMERALD_FLOWER = "\\"

#########################
#       Commands        #
#########################
def walk(direction):
    key_down(direction)
    time.sleep(0.5)
    key_up(direction)
    time.sleep(0.05)

def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Auto Maple.
    """

    num_presses = 2
    if direction == 'up' or direction == 'down':
        num_presses = 1
    if config.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_x = target[0] - config.player_pos[0]
    d_y = target[1] - config.player_pos[1]
    if abs(d_y) > settings.move_tolerance * 1.5:
        if direction == 'down':
            press(Key.JUMP, 3)
            press(Key.GUST_SHIFT, num_presses)
        elif direction == 'up':
            press(Key.JUMP, 1)
            press(Key.GUST_SHIFT, num_presses)
    if abs(d_x) > 0.1:
        press(Key.GUST_SHIFT, num_presses)
    else:
        walk(direction)


class Adjust(Command):
    """Fine-tunes player position using small movements."""

    def __init__(self, x, y, max_steps=5):
        super().__init__(locals())
        self.target = (float(x), float(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        counter = self.max_steps    # counter = 5
        toggle = True
        error = utils.distance(config.player_pos, self.target)
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            """
            error = distance between player and target
            config.enabled - if the main bot loop is running
            counter - max steps
            adjust_tolerance - The allowed error from a specific location while adjusting to that location
            """
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                threshold = settings.adjust_tolerance / math.sqrt(2)
                if abs(d_x) > threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('right')
                    counter -= 1
            else:
                d_y = self.target[1] - config.player_pos[1]
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):
                    if d_y < 0:
                        GustShift('up').main()
                    else:
                        key_down('down')
                        time.sleep(0.05)
                        press(Key.JUMP, 3, down_time=0.1)
                        key_up('down')
                        time.sleep(0.05)
                    counter -= 1
            error = utils.distance(config.player_pos, self.target)
            toggle = not toggle

class Buff(Command):
    """Uses each of Wind Breaker's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.cd120_buff_time = 0
        self.cd180_buff_time = 0
        self.cd200_buff_time = 0
        self.cd240_buff_time = 0
        self.cd300_buff_time = 0
        self.cd900_buff_time = 0
        self.decent_buff_time = 0

    def main(self):
        now = time.time()

        if self.cd120_buff_time == 0 or now - self.cd120_buff_time > 120:
            time.sleep(0.2)
            press(Key.STORM_WINDS, 2)
            time.sleep(0.5)
            press(Key.GLORY_OF_GUARDIANS, 2)
            self.cd120_buff_time = now
            time.sleep(0.5)
        # if self.cd180_buff_time == 0 or now - self.cd180_buff_time > 180:
	    #     press(Key.WEAPON_AURA, 2)
	    #     press(Key.LEGACY_RESTORATION, 2)
	    #     self.cd180_buff_time = now
        # if self.cd200_buff_time == 0 or now - self.cd200_buff_time > 200:
        #     press(Key.STORM_BRINGER, 2)
        #     time.sleep(0.5)
        #     self.cd200_buff_time = now
        # if self.cd240_buff_time == 0 or now - self.cd240_buff_time > 240:
	    #     press(Key.GRANDIS_GODDESS, 2)
	    #     self.cd240_buff_time = now
        # if self.cd300_buff_time == 0 or now - self.cd300_buff_time > 300:
        #     press(Key.SHARP_EYES, 2)
        #     time.sleep(0.5)
        #     press(Key.CYGNUS_KNIGHTS, 2)
        #     time.sleep(0.5)
        #     self.cd300_buff_time = now
        if self.cd900_buff_time == 0 or now - self.cd900_buff_time > 900:
            press(Key.CYGNUS_KNIGHTS, 2)
            self.cd900_buff_time = now
        # if self.decent_buff_time == 0 or now - self.decent_buff_time > settings.buff_cooldown:
	    #     for key in buffs:
		#         press(key, 3, up_time=0.3)
	    #     self.decent_buff_time = now

class GustShift(Command):
    """Performs a flash jump in the given direction."""

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)

    def main(self):
        key_down(self.direction)
        time.sleep(0.1)
        press(Key.GUST_SHIFT, 1)
        press(Key.GUST_SHIFT, 1)
        key_up(self.direction)
        time.sleep(1)

class WindFlourish(Command):
    """ Wind Breaker's Main Mobbing skill"""

    def __init__(self, direction, attacks=2, repetitions=1):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.attacks = int(attacks)
        self.repetitions = int(repetitions)

    def main(self):
        time.sleep(0.05)
        key_down(self.direction)
        time.sleep(0.05)
        if config.stage_fright and utils.bernoulli(0.7):
            time.sleep(utils.rand_float(0.1, 0.3))
        for _ in range(self.repetitions):
            press(Key.WIND_FLOURISH, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.4)
        else:
            time.sleep(0.3)