import cv2
import numpy as np
import pyautogui
import time
import os
import sys

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

# PyAutoGUI Safety Settings (Disable corner fail-safe crash)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.001

class GestureController:
    def __init__(self):
        self.w_screen, self.h_screen = pyautogui.size()
        
        # Frame reduction for bounding box
        self.frame_reduction_x = 60
        self.frame_reduction_y = 50
        
        # Cursor smoothing variables
        self.ploc_x, self.ploc_y = 0, 0
        self.cloc_x, self.cloc_y = 0, 0
        self.smoothing = max(1.5, config.MOUSE_SENSITIVITY)
        
        # Cool-down tracker to prevent rapid multi-clicks
        self.last_action_time = 0
        self.click_cooldown = 0.35  # seconds
        
        # Scroll tracker
        self.last_scroll_y = None

    def execute_gestures(self, lm_list, fingers, tracker, img):
        """Map hand gestures to OS automation commands."""
        if len(lm_list) < 21:
            return img

        # Get index and middle finger tip coordinates
        x_index, y_index = lm_list[8][1], lm_list[8][2]
        x_middle, y_middle = lm_list[12][1], lm_list[12][2]
        x_thumb, y_thumb = lm_list[4][1], lm_list[4][2]
        
        current_time = time.time()
        
        # Bounding box bounds
        x_min = self.frame_reduction_x
        x_max = config.FRAME_WIDTH - self.frame_reduction_x
        y_min = self.frame_reduction_y
        y_max = config.FRAME_HEIGHT - self.frame_reduction_y
        
        # Draw bounding box
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (255, 180, 0), 2)
        
        # 1. MOUSE MOVE MODE: Index Finger Up (or Index + Middle Up)
        if fingers[1] == 1:
            # Interpolate coordinates to screen size
            x_scaled = np.interp(x_index, (x_min, x_max), (0, self.w_screen))
            y_scaled = np.interp(y_index, (y_min, y_max), (0, self.h_screen))
            
            # Clip bounds
            x_scaled = np.clip(x_scaled, 0, self.w_screen - 1)
            y_scaled = np.clip(y_scaled, 0, self.h_screen - 1)
            
            # Smooth coordinates
            self.cloc_x = self.ploc_x + (x_scaled - self.ploc_x) / self.smoothing
            self.cloc_y = self.ploc_y + (y_scaled - self.ploc_y) / self.smoothing
            
            # Direct movement (image is already flipped in worker thread)
            try:
                pyautogui.moveTo(int(self.cloc_x), int(self.cloc_y))
            except Exception:
                pass
                
            cv2.circle(img, (x_index, y_index), 10, (0, 255, 0), cv2.FILLED)
            self.ploc_x, self.ploc_y = self.cloc_x, self.cloc_y

        # 2. LEFT CLICK: Index and Middle fingers pinch (distance < threshold)
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
            dist, info, img = tracker.find_distance(8, 12, lm_list, img)
            if dist < 35:
                if current_time - self.last_action_time > self.click_cooldown:
                    cv2.circle(img, (info[4], info[5]), 15, (0, 255, 255), cv2.FILLED)
                    try:
                        pyautogui.click()
                    except Exception:
                        pass
                    self.last_action_time = current_time
                    print("[Gesture] Left Click executed")

        # 3. RIGHT CLICK: Thumb and Index finger pinch
        elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0:
            dist, info, img = tracker.find_distance(4, 8, lm_list, img)
            if dist < 35:
                if current_time - self.last_action_time > self.click_cooldown:
                    cv2.circle(img, (info[4], info[5]), 15, (255, 255, 0), cv2.FILLED)
                    try:
                        pyautogui.rightClick()
                    except Exception:
                        pass
                    self.last_action_time = current_time
                    print("[Gesture] Right Click executed")

        # 4. SCROLLING: Index, Middle and Ring up
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
            if self.last_scroll_y is not None:
                diff = y_index - self.last_scroll_y
                if abs(diff) > 8:
                    scroll_amount = -int(diff * 2.0)
                    try:
                        pyautogui.scroll(scroll_amount)
                    except Exception:
                        pass
            self.last_scroll_y = y_index
        else:
            self.last_scroll_y = None

        return img
