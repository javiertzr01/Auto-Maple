"""The central program that ties all the modules together."""

import time

from dotenv import load_dotenv

from src.modules.bot import Bot
from src.modules.capture import Capture
from src.modules.notifier import Notifier
from src.modules.listener import Listener
from src.modules.gui import GUI
from src.modules.telegram_bot import TelegramBot

load_dotenv()

bot = Bot()
capture = Capture()
notifier = Notifier()
listener = Listener()
telegram = TelegramBot()

bot.start()
while not bot.ready:
    time.sleep(0.01)

telegram.start()
while not telegram.ready:
    time.sleep(0.01)

capture.start()
while not capture.ready:
    time.sleep(0.01)

notifier.start()
while not notifier.ready:
    time.sleep(0.01)

listener.start()
while not listener.ready:
    time.sleep(0.01)

print('\n[~] Successfully initialized Auto Maple')

gui = GUI()
gui.start()


#pylint: disable=W0105
"""
Capture

config.capture = capture
capture.frame = None
capture.minimap = {}
capture.minimap_ratio = 1
capture.minimap_sample = None
capture.sct = None
capture.window = {
    'left': 0,
    'top': 0,
    'width': 1366,
    'height': 768
}
capture.ready = False
capture.calibrated = False
capture.thread = threading.Thread(target=capture._main)
capture.thread.daemon = True
"""

"""
Notifier

    notifier.mixer = pygame.mixer.music

    notifier.ready = False
    notifier.thread = threading.Thread(target=notifier._main)
    notifier.thread.daemon = True

    notifier.room_change_threshold = 0.9
    notifier.rune_alert_delay = 270
"""

"""
Listener
    config.listener = listener

    listener.enabled = True
    listener.ready = False
    listener.block_time = 0
    listener.thread = threading.Thread(target=listener._main)
    listener.thread.daemon = True
"""
#pylint: enable=W0105
