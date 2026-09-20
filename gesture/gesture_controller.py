import cv2
import numpy as np
import pyautogui
import time
import os
import sys

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

# PyAutoGUI Safety Settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01  # Add slight delay to prevent OS event queue backup

class GestureController:
    def __init__(self):
        self.w_screen, self.h_screen = pyautogui.size()
        
        # Frame reduction for bounding box
        self.frame_reduction_x = 100
        self.frame_reduction_y = 80
        
        # Cursor smoothing variables
        self.ploc_x, self.ploc_y = 0, 0
        self.cloc_x, self.cloc_y = 0, 0
        self.smoothing = config.MOUSE_SENSITIVITY
        
        # Cool-down tracker to prevent rapid multi-clicks
        self.last_action_time = 0
        self.click_cooldown = 0.3  # seconds
        
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
        
        # 1. MOUSE MOVE MODE: Only Index Finger is Up
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            # Map coordinates inside frame reduction bounding box
            # Frame reduction bounds
            x_min = self.frame_reduction_x
            x_max = config.FRAME_WIDTH - self.frame_reduction_x
            y_min = self.frame_reduction_y
            y_max = config.FRAME_HEIGHT - self.frame_reduction_y
            
            # Draw bounding box
            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            
            # Interpolate coordinates
            x_scaled = np.interp(x_index, (x_min, x_max), (0, self.w_screen))
            y_scaled = np.interp(y_index, (y_min, y_max), (0, self.h_screen))
            
            # Smooth coordinates (moving average)
            self.cloc_x = self.ploc_x + (x_scaled - self.ploc_x) / self.smoothing
            self.cloc_y = self.ploc_y + (y_scaled - self.ploc_y) / self.smoothing
            
            # Move cursor (invert X to act like a mirror)
            # Webcams are mirrored, so we subtract scaled X from screen width to match physical hand movement
            target_x = self.w_screen - self.cloc_x
            
            try:
                pyautogui.moveTo(target_x, self.cloc_y)
            except pyautogui.FailSafeException:
                pass  # Ignore if it hits screen corners
                
            cv2.circle(img, (x_index, y_index), 12, (0, 255, 0), cv2.FILLED)
            self.ploc_x, self.ploc_y = self.cloc_x, self.cloc_y

        # 2. LEFT CLICK: Index and Middle fingers up and close to each other
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            # Find distance between index tip and middle tip
            dist, info, img = tracker.find_distance(8, 12, lm_list, img)
            
            if dist < config.CLICK_DISTANCE_THRESHOLD:
                if current_time - self.last_action_time > self.click_cooldown:
                    cv2.circle(img, (info[4], info[5]), 15, (0, 255, 255), cv2.FILLED)
                    try:
                        pyautogui.click()
                    except pyautogui.FailSafeException:
                        pass
                    self.last_action_time = current_time
                    print("[Gesture] Left Click executed")

        # 3. RIGHT CLICK: Thumb and Index finger pinch
        elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            dist, info, img = tracker.find_distance(4, 8, lm_list, img)
            if dist < config.CLICK_DISTANCE_THRESHOLD:
                if current_time - self.last_action_time > self.click_cooldown:
                    cv2.circle(img, (info[4], info[5]), 15, (255, 255, 0), cv2.FILLED)
                    try:
                        pyautogui.rightClick()
                    except pyautogui.FailSafeException:
                        pass
                    self.last_action_time = current_time
                    print("[Gesture] Right Click executed")

        # 4. VOLUME UP / DOWN: Thumb Up (Volume Up) / Thumb Down (Volume Down)
        # Check for thumbs up / thumbs down or specific pinch distance for slider
        # Let's map Pinky & Index distance (horizontal/vertical) or volume commands
        # A simpler option is: Index, Middle, Ring up + Thumb relative position
        # Let's map middle/ring/pinky up, thumb out -> Volume control using Index/Thumb distance
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
            # All fingers up (Palm/Open Hand) - Check if Thumb is closed
            # Let's use distance between Thumb (4) and Index (5) MCP joint
            # If thumb is close to index, adjust volume by moving hand vertically
            dist, info, img = tracker.find_distance(4, 5, lm_list, img)
            
            # Simple volume control: if thumb and index are pinched but middle, ring, pinky are up
            # Let's do: Thumb (4) and Middle (12) distance pinch for scroll
            pass

        # 5. SCROLLING: Index, Middle and Ring up
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
            # Use Index tip vertical movement for scrolling
            if self.last_scroll_y is not None:
                diff = y_index - self.last_scroll_y
                if abs(diff) > 10:
                    # Positive diff = hand moved down = scroll down
                    # Negative diff = hand moved up = scroll up
                    scroll_amount = -int(diff * 1.5)
                    try:
                        pyautogui.scroll(scroll_amount)
                    except pyautogui.FailSafeException:
                        pass
            self.last_scroll_y = y_index
        else:
            self.last_scroll_y = None

        return img
