"""A keyboard listener to track user inputs."""

import time
import threading
import winsound
from os.path import join
from datetime import datetime

import keyboard as kb
import cv2

# pylint: disable=import-error
from src.common.interfaces import Configurable
from src.common import config, utils
# pylint: enable=import-error


class Listener(Configurable):
    DEFAULT_CONFIG = {
        'Start/stop': 'insert',
        'Reload routine': 'f6',
        'Record position': 'f7',
        'Screenshot': 'f8',
        # 'Record Video': 'f9'
    }
    BLOCK_DELAY = 1         # Delay after blocking restricted button press

    def __init__(self):
        """Initializes this Listener object's main thread."""

        super().__init__('controls')
        config.listener = self

        self.enabled = False
        self.ready = False
        self.block_time = 0
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True
        
        self.recording = False

    def start(self):
        """
        Starts listening to user inputs.
        :return:    None
        """

        print('\n[~] Started keyboard listener')
        self.thread.start()

    def _main(self):
        """
        Constantly listens for user inputs and updates variables in config accordingly.
        :return:    None
        """

        self.ready = True
        while True:
            if self.enabled:
                if kb.is_pressed(self.config['Start/stop']):
                    Listener.toggle_enabled()
                elif kb.is_pressed(self.config['Reload routine']):
                    Listener.reload_routine()
                elif self.restricted_pressed('Record position'):
                    Listener.record_position()
                elif kb.is_pressed(self.config['Screenshot']):
                    Listener.screenshot()
                # Recording feature not used - Inconsistent
                # elif kb.is_pressed(self.config['Record Video']) and self.recording is False:
                #     Listener.record_video()
            time.sleep(0.01)

    def restricted_pressed(self, action):
        """Returns whether the key bound to ACTION is pressed only if the bot is disabled."""

        if kb.is_pressed(self.config[action]):
            if not config.enabled:
                return True
            now = time.time()
            if now - self.block_time > Listener.BLOCK_DELAY:
                print(f"\n[!] Cannot use '{action}' while Auto Maple is enabled")
                self.block_time = now
        return False

    @staticmethod
    def toggle_enabled():
        """Resumes or pauses the current routine. Plays a sound to notify the user."""

        config.bot.rune_active = False

        if not config.enabled:
            Listener.recalibrate_minimap()      # Recalibrate only when being enabled.

        config.enabled = not config.enabled
        utils.print_state()

        if config.enabled:
            winsound.Beep(784, 333)     # G5
        else:
            winsound.Beep(523, 333)     # C5
        time.sleep(0.267)

    @staticmethod
    def reload_routine():
        Listener.recalibrate_minimap()

        config.routine.load(config.routine.path)

        winsound.Beep(523, 200)     # C5
        winsound.Beep(659, 200)     # E5
        winsound.Beep(784, 200)     # G5

    @staticmethod
    def recalibrate_minimap():
        config.capture.calibrated = False
        while not config.capture.calibrated:
            time.sleep(0.01)
        config.gui.edit.minimap.redraw()

    @staticmethod
    def record_position():
        pos = tuple('{:.3f}'.format(round(i, 3)) for i in config.player_pos)
        now = datetime.now().strftime('%I:%M:%S %p')
        config.gui.edit.record.add_entry(now, pos)
        print(f'\n[~] Recorded position ({pos[0]}, {pos[1]}) at {now}')
        time.sleep(0.6)
    
    @staticmethod
    def screenshot():
        # TODO: Make Directory if Screenshots is not available
        
        image = config.capture.frame
        
        now = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3] + '.png'
        path = join('assets', 'Screenshots', now)
        
        cv2.imwrite(path, image)
        
        print(f"Screenshot saved as {path}")
        time.sleep(0.6)
        
    @staticmethod
    def record_video():
        print("Started Recording")
        config.listener.recording = True
        now = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3] + '.mp4'
        path = join('assets', 'Recordings', now)
        time.sleep(0.6)
        
        config.capture.record(path)
        
        print("Stopped Recording (listener.py)")
        
        print(f"Recording saved as {path}")
