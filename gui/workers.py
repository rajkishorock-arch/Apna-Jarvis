import cv2
import time
import sys
import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from gesture.hand_tracker import HandTracker
from gesture.gesture_controller import GestureController
from voice.tts import TTSManager
from voice.asr import VoiceListener
from automation.system_control import SystemAutomation
from ai.brain import AIBrain

class CameraWorker(QThread):
    """QThread to handle webcam capturing, hand gesture processing, and face security."""
    frame_processed = Signal(QImage)
    capture_progress = Signal(int, int)  # (current, total)
    capture_finished = Signal(bool)
    access_granted = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.active = True
        self.gesture_enabled = False  # Disabled by default on startup!
        self.mode = "GESTURE"  # "GESTURE", "CAPTURE", "LOCK"
        self.capture_user_name = "User"
        self.capture_count = 0
        self.capture_max = 30
        
        # Subsystems
        self.tracker = HandTracker(
            detection_con=config.MIN_DETECTION_CONFIDENCE,
            track_con=config.MIN_TRACKING_CONFIDENCE,
            max_hands=config.MAX_NUM_HANDS
        )
        self.controller = GestureController()
        self.cap = None
        
        # Face Recognizer (lazy import to prevent dependency issues)
        from vision.face_recognizer import FaceRecognizer
        self.face_recognizer = FaceRecognizer()
        
        self.auth_consecutive_frames = 0
        self.auth_required_frames = 5
        
    def run(self):
        while self.active:
            # If gesture mode is disabled and not capturing/locking, keep camera closed!
            if not self.gesture_enabled and self.mode == "GESTURE":
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None
                time.sleep(0.2)
                continue

            # Open camera hardware ONLY when enabled or capturing/locking
            if self.cap is None or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                for _ in range(5):
                    if self.cap.isOpened():
                        self.cap.read()
                        time.sleep(0.04)

            try:
                success, img = self.cap.read()
                if not success or img is None or img.size == 0:
                    time.sleep(0.03)
                    continue
                
                # Mode Routing
                if self.mode == "CAPTURE":
                    # Grayscale conversion for Haar cascades
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    rect = self.face_recognizer.detect_face(gray)
                    if rect is not None:
                        x, y, w, h = rect
                        # Draw face frame
                        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 2)
                        cv2.putText(
                            img, f"Capturing {self.capture_count}/{self.capture_max}", 
                            (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
                        )
                        
                        self.capture_count += 1
                        self.face_recognizer.save_sample(
                            gray, rect, self.capture_user_name, self.capture_count
                        )
                        self.capture_progress.emit(self.capture_count, self.capture_max)
                        
                        # Space out images slightly to get different angles
                        time.sleep(0.12)
                        
                        if self.capture_count >= self.capture_max:
                            # Captured all, start training
                            cv2.putText(
                                img, "Training AI...", (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                            )
                            self.mode = "GESTURE"
                            train_success = self.face_recognizer.train_classifier()
                            self.capture_finished.emit(train_success)
                    else:
                        cv2.putText(
                            img, "Align face inside camera...", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                        )
                        
                elif self.mode == "LOCK":
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    name, confidence = self.face_recognizer.recognize_face(gray)
                    
                    if name is not None:
                        cv2.putText(
                            img, f"Verifying: {name} ({int(confidence)}%)", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                        )
                        self.auth_consecutive_frames += 1
                        if self.auth_consecutive_frames >= self.auth_required_frames:
                            self.mode = "GESTURE"
                            self.access_granted.emit(name)
                    else:
                        self.auth_consecutive_frames = 0
                        cv2.putText(
                            img, "Locked - Scan Face to Unlock", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                        )
                        
                elif self.mode == "GESTURE":
                    if self.gesture_enabled:
                        # Capture gestures
                        img = self.tracker.find_hands(img, draw=True)
                        lm_list = self.tracker.find_positions(img)
                        
                        if len(lm_list) > 0:
                            fingers = self.tracker.fingers_up(lm_list)
                            img = self.controller.execute_gestures(lm_list, fingers, self.tracker, img)
                    else:
                        cv2.putText(
                            img, "Gestures Offline", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                        )
                
                # Convert frame to QImage safely with .copy() to prevent memory buffer corruption
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = img_rgb.shape
                bytes_per_line = ch * w
                q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                
                self.frame_processed.emit(q_img)
                time.sleep(0.01)
            except Exception as e:
                print(f"[Camera Thread Loop Error]: {e}")
                time.sleep(0.1)
            
        if self.cap:
            self.cap.release()

    def start_face_capture(self, user_name):
        self.capture_user_name = user_name
        self.capture_count = 0
        self.mode = "CAPTURE"

    def activate_lock(self):
        self.mode = "LOCK"
        self.auth_consecutive_frames = 0

    def stop(self):
        self.active = False
        if hasattr(self, 'cap') and self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        self.quit()


class VoiceWorker(QThread):
    """QThread to handle voice input capturing and system commands routing."""
    status_changed = Signal(str)
    command_received = Signal(str, str)
    app_opened = Signal(str)
    
    def __init__(self, brain, tts, listener, automation):
        super().__init__()
        self.active = True
        self.voice_enabled = True
        self.locked = False  # Lock indicator block
        
        self.brain = brain
        self.tts = tts
        self.listener = listener
        self.automation = automation

    def run(self):
        self.status_changed.emit("Online (Listening for voice commands)")
        
        while self.active:
            if not self.voice_enabled:
                self.status_changed.emit("Microphone Disabled")
                time.sleep(0.5)
                continue
                
            if self.locked:
                self.status_changed.emit("Locked Mode (Mic Blocked)")
                time.sleep(0.5)
                continue

            query = self.listener.listen(timeout=3, phrase_time_limit=5)
            if query:
                # Remove wake word if prefixed
                clean_cmd = re.sub(r"^(jarvis|hey jarvis|hello jarvis)\s*", "", query, flags=re.IGNORECASE).strip()
                if not clean_cmd:
                    clean_cmd = query
                    
                print(f"[GUI Voice Worker] Processing voice query: {clean_cmd}")
                self.status_changed.emit("Processing voice command...")
                
                if "disable voice" in clean_cmd or "stop voice" in clean_cmd:
                    self.tts.speak("Disabling voice assistant.", block=False)
                    self.voice_enabled = False
                    self.status_changed.emit("Microphone Disabled")
                    continue
                    
                res = self.brain.process_command(clean_cmd)
                intent = res["intent"]
                params = res["params"]
                reply = res["reply"]
                
                # Execute automation
                if intent == "launch_app":
                    self.automation.launch_app(params["app"])
                elif intent == "close_app":
                    self.automation.close_app(params["app"])
                elif intent == "open_website":
                    self.automation.open_website(params["url"])
                elif intent == "web_search":
                    self.automation.search_web(params["query"])
                elif intent == "take_screenshot":
                    self.automation.take_screenshot()
                elif intent == "volume_control":
                    self.automation.control_volume(params["action"])

                # Speak & emit signal for UI update
                self.command_received.emit(clean_cmd, reply)
                self.tts.speak(reply, block=False)
                self.status_changed.emit("Online (Listening for voice commands)")
            else:
                time.sleep(0.01)

    def stop(self):
        self.active = False
        self.wait()
