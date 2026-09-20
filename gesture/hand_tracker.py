import cv2
import mediapipe as mp
import numpy as np
import math

class HandTracker:
    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.7):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        
        # Initialize mediapipe hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]
        self.results = None

    def find_hands(self, img, draw=True):
        """Processes the image frame and draws hand landmarks if found."""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img, hand_lms, self.mp_hands.HAND_CONNECTIONS
                )
        return img

    def find_positions(self, img, hand_no=0):
        """Returns a list of landmarks with id, x, and y coordinates."""
        lm_list = []
        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                my_hand = self.results.multi_hand_landmarks[hand_no]
                h, w, c = img.shape
                for id, lm in enumerate(my_hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
        return lm_list

    def fingers_up(self, lm_list):
        """Returns a list of 1s and 0s representing which fingers are open/closed.
        Order: [Thumb, Index, Middle, Ring, Pinky]
        """
        fingers = []
        if len(lm_list) < 21:
            return [0, 0, 0, 0, 0]

        # Thumb (Check horizontal movement relative to MCP join of index finger)
        # We need to check hand orientation. Generally, if thumb tip x is greater/lesser than CMC
        # depending on left/right hand. We'll simplify for now: thumb tip x vs thumb IP x
        if lm_list[self.tip_ids[0]][1] > lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers (Tip y is less than PIP y for open fingers because y is 0 at top of image)
        for id in range(1, 5):
            if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def find_distance(self, p1, p2, lm_list, img=None, draw=True, r=8, t=3):
        """Calculates distance between two landmarks p1 and p2."""
        if len(lm_list) < 21:
            return 0, [0, 0, 0, 0, 0, 0], img
            
        x1, y1 = lm_list[p1][1], lm_list[p1][2]
        x2, y2 = lm_list[p2][1], lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)
        
        info = [x1, y1, x2, y2, cx, cy]

        if img is not None and draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
            
        return length, info, img

# Self-test block
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    print("Starting hand tracking test loop. Press 'q' to quit.")
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image from camera.")
            break
            
        img = tracker.find_hands(img)
        lm_list = tracker.find_positions(img)
        
        if len(lm_list) > 0:
            fingers = tracker.fingers_up(lm_list)
            print(f"Fingers open: {fingers}")
            
        cv2.imshow("Hand Tracker Test", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
