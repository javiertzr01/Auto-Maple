import time
import win32gui
import win32ui
import win32con
import ctypes
from ctypes import wintypes

import cv2
import mss
import numpy as np

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

def mss_screenshot(delay=1):
    with mss.mss() as sct:
        handle = user32.FindWindowW(None, 'MapleStory')
        rect = wintypes.RECT()
        user32.GetWindowRect(handle, ctypes.pointer(rect))
        rect = (rect.left, rect.top, rect.right, rect.bottom)
        rect = tuple(max(0, x) for x in rect)
        
        window['left'] = rect[0]
        window['top'] = rect[1]
        window['width'] = rect[2] - rect[0]
        window['height'] = rect[3] - rect[1]
        try:
            return np.array(sct.grab(window))
        except mss.exception.ScreenShotError:
            print(f'\n[!] Error while taking screenshot, retrying in {delay} second'
                  + ('s' if delay != 1 else ''))
            time.sleep(delay)

def win32_screenshot():
    hwnd = win32gui.FindWindow(None, 'MapleStory')
    wDC = win32gui.GetWindowDC(hwnd)
    
    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    
    border_pixels = 8
    titlebar_pixels = 30
    width = width - (border_pixels * 2)
    height = height - titlebar_pixels - border_pixels
    cropped_x = border_pixels
    cropped_y = titlebar_pixels
    
    dcObj=win32ui.CreateDCFromHandle(wDC)
    cDC=dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0,0),(width, height) , dcObj, (cropped_x,cropped_y), win32con.SRCCOPY)
    
    # Conversion to cv2-compaitible
    signedIntsArray = dataBitMap.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height, width, 4)
    
    # Free Resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    
    return img
            
if __name__ == "__main__":
    
    window = {}
    fps_ls = []
    loop_time = time.time()
    
    MM_TL_TEMPLATE = cv2.imread('assets/minimap_tl_template.png', 0)
    MM_BR_TEMPLATE = cv2.imread('assets/minimap_br_template.png', 0)
    
    while(True):
        # ss = mss_screenshot()
        ss = win32_screenshot()
        cv2.imshow('FPS Checker', ss)
        fps = 1 / (time.time() - loop_time)
        fps_ls.append(fps)
        print('FPS {}'.format(fps))
        loop_time = time.time()
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            print(sum(fps_ls)/len(fps_ls))
            break
        

    