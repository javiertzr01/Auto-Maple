"""A module for tracking useful in-game information."""
import threading
import time
from os.path import join, splitext
import keyboard as kb

import cv2
import win32gui
import win32ui
import win32con
import numpy as np

from src.common import config, utils # pylint: disable=import-error

# The distance between the top of the minimap and the top of the screen
MINIMAP_TOP_BORDER = 5

# The thickness of the other three borders of the minimap
MINIMAP_BOTTOM_BORDER = 9

# Offset in pixels to adjust for windowed mode
WINDOWED_OFFSET_TOP = 36
WINDOWED_OFFSET_LEFT = 10

# Offset to accurately screenshot game only
BORDER_PIXELS = 8
TITLEBAR_PIXELS = 30

# Start point(Offset) of screenshot
X_0 = BORDER_PIXELS
Y_0 = TITLEBAR_PIXELS

# The top-left and bottom-right corners of the minimap
MM_TL_TEMPLATE = cv2.imread('assets/minimap_tl_template.png', 0)
MM_BR_TEMPLATE = cv2.imread('assets/minimap_br_template.png', 0)

MMT_HEIGHT = max(MM_TL_TEMPLATE.shape[0], MM_BR_TEMPLATE.shape[0]) #22
MMT_WIDTH = max(MM_TL_TEMPLATE.shape[1], MM_BR_TEMPLATE.shape[1]) #37

# The player's symbol on the minimap
PLAYER_TEMPLATE = cv2.imread('assets/player_template.png', 0)
PT_HEIGHT, PT_WIDTH = PLAYER_TEMPLATE.shape


class Capture:
    """
    A class that tracks player position and various in-game events. It constantly updates
    the config module with information regarding these events. It also annotates and
    displays the minimap in a pop-up window.
    """

    def __init__(self):
        """Initializes this Capture object's main thread."""

        config.capture = self

        self.frame = None
        self.minimap = {}
        self.minimap_ratio = 1
        self.minimap_sample = None
        self.sct = None
        self.window = {
            'left': 0,
            'top': 0,
            'width': 1366,
            'height': 768
        }

        self.fourcc = cv2.VideoWriter_fourcc(*'avc1')

        self.ready = False
        self.calibrated = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Capture's thread."""

        print('\n[~] Started video capture')
        self.thread.start()

    def _main(self):
        """Constantly monitors the player's position and in-game events."""
        while True:
            # Calibrate by finding the top-left and bottom-right corners of the minimap
            self.frame = self.screenshot()
            if self.frame is None:
                continue
            top_left, _ = utils.single_match(self.frame, MM_TL_TEMPLATE)
            _, bottom_right = utils.single_match(self.frame, MM_BR_TEMPLATE)
            mm_tl = (
                top_left[0] + MINIMAP_BOTTOM_BORDER,
                top_left[1] + MINIMAP_TOP_BORDER
            )
            mm_br = (
                max(mm_tl[0] + PT_WIDTH, bottom_right[0] - MINIMAP_BOTTOM_BORDER),
                max(mm_tl[1] + PT_HEIGHT, bottom_right[1] - MINIMAP_BOTTOM_BORDER) #487vs476
            )
            self.minimap_ratio = (mm_br[0] - mm_tl[0]) / (mm_br[1] - mm_tl[1])
            self.minimap_sample = self.frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]
            # cv2.imshow("calibrate", self.minimap_sample)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows() 
            self.calibrated = True
            while True:
                if not self.calibrated:
                    break

                # Take screenshot 
                self.frame = self.screenshot()
                if self.frame is None:
                    continue

                # Crop the frame to only show the minimap
                minimap = self.frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]

                # Determine the player's position
                player = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
                if player: 
                    config.player_pos = utils.convert_to_relative(player[0], minimap)

                # Package display information to be polled by GUI 
                self.minimap = {
                     'minimap': minimap,
                     'rune_active': config.bot.rune_active,
                     'rune_pos': config.bot.rune_pos,
                    'path': config.path,
                    'player_pos': config.player_pos
                }

                if not self.ready:
                    self.ready = True
                time.sleep(0.001)

    def screenshot(self):
        """
        Takes a screenshot of the game
        Returns:
            image : a cv2 accessible numpy array
        """
        hwnd = win32gui.FindWindow(None, 'MapleStory')
        wDC = win32gui.GetWindowDC(hwnd)

        # Calibrate screen capture
        rect = win32gui.GetWindowRect(hwnd)
        self.window['left'] = rect[0]
        self.window['top'] = rect[1]
        self.window['width'] = max(rect[2] - rect[0], MMT_WIDTH)
        self.window['height'] = max(rect[3] - rect[1], MMT_HEIGHT)

        # Calibrate to remove extra space from width and height
        self.window['width'] = self.window['width'] - (BORDER_PIXELS * 2)
        self.window['height'] = self.window['height'] - TITLEBAR_PIXELS - BORDER_PIXELS
        dcObj=win32ui.CreateDCFromHandle(wDC)
        cDC=dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.window['width'], self.window['height'])
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0,0),(self.window['width'], self.window['height']) , dcObj, (X_0, Y_0), win32con.SRCCOPY)

        # Conversion to cv2-compaitible
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        image = np.fromstring(signedIntsArray, dtype='uint8')
        image.shape = (self.window['height'], self.window['width'], 4)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        return image
    
    def re_encode(self, path, frames, duration):
        """
        Re-encode the video for accurate fps on video
        NOTE: Unused for now. Causes too much overhead
        Args:
            path : path to save the file to
            frame_rate : accurate frame rate
        """
        # Input Video
        input_video = path
        
        # Output Video
        filename, file_extension = splitext(path)
        output_video = join(filename, "_re-encoded", file_extension)
        
        # Open input video
        cap = cv2.VideoCapture(input_video)
        
        # Dimensions of video frame
        width = int(cap.get(3))
        height = int(cap.get(4))
        
        # Create VideoWriter object to re-encode video
        fps = frames//duration
        out = cv2.VideoWriter(output_video, self.fourcc, fps, (width, height))
        
        # Read frames from input video
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Write frames to output video
            out.write(frame)
        
        # Release resources
        cap.release()
        out.release()
        
        
    
    def record(self, path, frame_rate=28, duration=0, x0=X_0, x1=None, y0=Y_0, y1=None):
        """
        Records the game
        Args:
            path : path to save the file to
            fourcc : fourcc object (Look at __init__)
            frame_rate (int, optional): fps of the video saved. Defaults to 28.
            duration (int, optional): duration of recording. Defaults to 0.
            x0 : width start. Defaults to X_0.
            x1 : width end. Defaults to None.
            y0 : height start. Defaults to Y_0.
            y1 : height end. Defaults to None.
        """
        def convert_cv2_obj(image):
            """Convert image to cv2 object instead of nparray"""
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image

        if x1 is None:
            x1 = self.window['width']
        if y1 is None:
            y1 = self.window['height']
        frame_width = x1 - x0
        frame_height = y1 - y0
        
        # DEBUG
        print(f"Frame Width: {frame_width}")
        print(f"Frame Height: {frame_height}")
        
        out = cv2.VideoWriter(path, self.fourcc, frame_rate, (frame_width, frame_height))
        
        time_diff = 0
        start = time.time()
        # Test FPS
        frames = 0
        
        while True:
            if duration == 0:
                if kb.is_pressed(config.listener.config['Record Video']):
                    config.listener.recording = False
                    print("Stopped Recording (capture.py)")
                    duration = time.time() - start
                    break
            elif time_diff >= duration:
                break
            cropped = self.frame[y0:y1, x0:x1]
            # DEBUG
            cv2.imshow("crop", cropped)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            cropped = convert_cv2_obj(cropped)
            
            # cv2.imshow('test_record', cropped)
            # Pass image to VideoWriter
            out.write(cropped)
            time_diff = time.time() - start
            
            #Test FPS
            frames += 1
        print(f"Frames collected: {frames}")
        
        out.release()

        # if need to re-encode for smooth picture
        self.re_encode(path, frames, duration)
        cv2.destroyAllWindows()
            
    def record_rune(self, path, duration):
        """
        Crops image to rune area and records focal area
        Args:
            path : path to save file
            duration : number of seconds to record
        """
        height = self.window['height']
        width = self.window['width']
        preset_height = 1080
        preset_width = 1920
        height_ratio = height/preset_height
        width_ratio = width/preset_width
        frame_rate = 322.0
        y0 = 110
        y1 = (height//3) - 30
        x0 = (width//3) + 20
        x1 = (4 * width//6) - 30
        
        # DEBUG:
        print (f"y0:{y0}, y1:{y1}, x0:{x0}, x1{x1}")
        self.record(path, frame_rate, duration=duration, x0=x0, x1=x1, y0=y0, y1=y1)
