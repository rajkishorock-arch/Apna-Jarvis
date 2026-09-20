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
        self.gesture_enabled = True
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
        
        # Face Recognizer (lazy import to prevent dependency issues)
        from vision.face_recognizer import FaceRecognizer
        self.face_recognizer = FaceRecognizer()
        
        self.auth_consecutive_frames = 0
        self.auth_required_frames = 5
        
    def run(self):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(3, config.FRAME_WIDTH)
        cap.set(4, config.FRAME_HEIGHT)
        
        while self.active:
            try:
                success, img = cap.read()
                if not success:
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
                    # Look for registered user faces
                    name, confidence, rect = self.face_recognizer.predict(img)
                    if rect is not None:
                        x, y, w, h = rect
                        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        
                        # LBPH distance (lower is better, < 80 represents strong confidence)
                        if name and name != "Unknown" and confidence < 80:
                            self.auth_consecutive_frames += 1
                            cv2.putText(
                                img, f"Verifying... {self.auth_consecutive_frames}/{self.auth_required_frames}", 
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                            )
                            
                            if self.auth_consecutive_frames >= self.auth_required_frames:
                                self.mode = "GESTURE"
                                self.access_granted.emit(name)
                                self.auth_consecutive_frames = 0
                        else:
                            self.auth_consecutive_frames = 0
                            cv2.putText(
                                img, "Access Denied / Unknown Face", (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
                            )
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
                
                # Convert frame to QImage for Qt UI update
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = img_rgb.shape
                bytes_per_line = ch * w
                q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                self.frame_processed.emit(q_img)
                time.sleep(0.01)
            except Exception as e:
                print(f"[Camera Thread Loop Error]: {e}")
                time.sleep(0.1)
            
        cap.release()

    def start_face_capture(self, user_name):
        self.capture_user_name = user_name
        self.capture_count = 0
        self.mode = "CAPTURE"

    def activate_lock(self):
        self.mode = "LOCK"
        self.auth_consecutive_frames = 0

    def stop(self):
        self.active = False
        self.wait()


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
        self.status_changed.emit("Online (Listening for 'Jarvis')")
        
        while self.active:
            if not self.voice_enabled:
                self.status_changed.emit("Microphone Disabled")
                time.sleep(0.5)
                continue
                
            # Passive listening for wake word
            query = self.listener.listen(timeout=3, phrase_time_limit=4)
            if query and config.WAKE_WORD in query:
                print(f"[GUI Voice Worker] Wake word detected: {query}")
                
                # Check security lock state first
                if self.locked:
                    self.status_changed.emit("Locked Mode (Mic Blocked)")
                    self.tts.speak("System access is locked. Please look at the camera to authenticate.")
                    continue
                
                self.status_changed.emit("Listening for command...")
                self.tts.speak("Yes, how can I help you?")
                
                # Active listening for system command
                command = self.listener.listen(timeout=5, phrase_time_limit=6)
                if command:
                    print(f"[GUI Voice Worker] Command: {command}")
                    self.status_changed.emit("Processing query...")
                    
                    if "stop voice" in command or "disable voice" in command:
                        self.tts.speak("Disabling voice assistant.")
                        self.voice_enabled = False
                        continue
                        
                    response = self.brain.process_query(command)
                    reply = response.get("reply", "I am on it.")
                    self.tts.speak(reply)
                    
                    self.command_received.emit(command, reply)
                    
                    # Execute automation
                    intent = response.get("intent")
                    arg = response.get("argument")
                    
                    if intent == "open_app" and arg:
                        self.automation.open_app(arg)
                        self.brain.db.log_app_launch(arg)
                        self.app_opened.emit(arg)
                    elif intent == "close_app" and arg:
                        self.automation.close_app(arg)
                    elif intent == "open_url" and arg:
                        self.automation.open_url(arg)
                    elif intent == "search_web" and arg:
                        self.automation.search_web(arg)
                    elif intent == "screenshot":
                        self.automation.take_screenshot()
                    elif intent == "system_stats":
                        stats = self.automation.get_system_stats()
                        stat_reply = f"CPU is at {stats['cpu_percent']} percent, and RAM usage is {stats['ram_percent']} percent."
                        self.tts.speak(stat_reply)
                    elif intent == "shutdown":
                        self.automation.shutdown()
                    elif intent == "abort_shutdown":
                        self.automation.abort_shutdown()
                
                self.status_changed.emit("Online (Listening for 'Jarvis')")
            else:
                time.sleep(0.01)

    def stop(self):
        self.active = False
        self.wait()
