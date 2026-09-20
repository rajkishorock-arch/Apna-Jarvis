import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QTextEdit, QListWidget, QListWidgetItem, QFrame, QMessageBox, QInputDialog
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage, QFont

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from gui.workers import CameraWorker, VoiceWorker
from database.db_manager import DatabaseManager
from automation.system_control import SystemAutomation
from voice.tts import TTSManager
from voice.asr import VoiceListener
from ai.brain import AIBrain

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JarvisX - AI Desktop Assistant Dashboard")
        self.resize(1100, 750)
        
        # Subsystem instances for thread sharing
        self.tts = TTSManager()
        self.listener = VoiceListener()
        self.brain = AIBrain()
        self.automation = SystemAutomation()
        
        self.system_locked = False
        
        # Load stylesheet for professional look
        self.apply_dark_theme()
        
        # Initialize UI Components
        self.init_ui()
        
        # Start Workers
        self.start_workers()
        
        # Telemetry Timer (updates CPU/RAM every 1.5 seconds)
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(1500)
        
        # Initial notes refresh
        self.refresh_notes()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0E0E10;
            }
            QWidget {
                color: #E2E2E6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#card {
                background-color: #18181C;
                border: 1px solid #2C2C35;
                border-radius: 12px;
                padding: 10px;
            }
            QLabel#header {
                font-size: 20px;
                font-weight: bold;
                color: #5F5FC4;
                margin-bottom: 5px;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
                padding: 10px;
            }
            QPushButton {
                background-color: #5F5FC4;
                border: none;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 13px;
                margin-bottom: 4px;
            }
            QPushButton:hover {
                background-color: #7373D8;
            }
            QPushButton#toggle-btn-active {
                background-color: #2ECC71;
            }
            QPushButton#toggle-btn-active:hover {
                background-color: #27AE60;
            }
            QPushButton#toggle-btn-inactive {
                background-color: #E74C3C;
            }
            QPushButton#toggle-btn-inactive:hover {
                background-color: #C0392B;
            }
            QProgressBar {
                border: 1px solid #2C2C35;
                border-radius: 5px;
                text-align: center;
                height: 18px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #5F5FC4;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #121214;
                border: 1px solid #2C2C35;
                border-radius: 8px;
                color: #00FFCC;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QListWidget {
                background-color: #121214;
                border: 1px solid #2C2C35;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #2C2C35;
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #5F5FC4;
                color: white;
            }
        """)

    def init_ui(self):
        # Main widget & layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header bar
        header_layout = QHBoxLayout()
        title_label = QLabel("JarvisX - Operations Command Center")
        title_label.setObjectName("title")
        header_layout.addWidget(title_label)
        
        # User name greeting label
        self.greeting_label = QLabel("Loading memory...")
        self.greeting_label.setStyleSheet("font-size: 14px; font-style: italic; color: #8F8FA0;")
        header_layout.addWidget(self.greeting_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        
        main_layout.addLayout(header_layout)
        
        # Middle row containing Left Widgets, Camera Feed, and Right notes
        self.middle_layout = QHBoxLayout()
        self.middle_layout.setSpacing(15)
        
        # COLUMN 1: System Telemetry & Control Buttons
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # Card 1: System Health
        telemetry_card = QFrame()
        telemetry_card.setObjectName("card")
        telemetry_layout = QVBoxLayout(telemetry_card)
        
        telemetry_title = QLabel("System Resource Telemetry")
        telemetry_title.setObjectName("header")
        telemetry_layout.addWidget(telemetry_title)
        
        telemetry_layout.addWidget(QLabel("CPU Utilization:"))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setValue(0)
        telemetry_layout.addWidget(self.cpu_bar)
        
        telemetry_layout.addWidget(QLabel("RAM Memory Utilization:"))
        self.ram_bar = QProgressBar()
        self.ram_bar.setValue(0)
        telemetry_layout.addWidget(self.ram_bar)
        
        telemetry_layout.addWidget(QLabel("Battery Status:"))
        self.battery_bar = QProgressBar()
        self.battery_bar.setValue(0)
        telemetry_layout.addWidget(self.battery_bar)
        
        self.battery_label = QLabel("Battery: Unknown")
        self.battery_label.setStyleSheet("font-size: 11px; color: #8F8FA0;")
        telemetry_layout.addWidget(self.battery_label)
        
        left_layout.addWidget(telemetry_card)
        
        # Card 2: Modules Controls Toggles & Security
        self.control_card = QFrame()
        self.control_card.setObjectName("card")
        control_layout = QVBoxLayout(self.control_card)
        
        control_title = QLabel("Subsystem Control")
        control_title.setObjectName("header")
        control_layout.addWidget(control_title)
        
        self.gesture_toggle = QPushButton("Camera Gesture: ENABLED")
        self.gesture_toggle.setObjectName("toggle-btn-active")
        self.gesture_toggle.clicked.connect(self.toggle_gesture_mode)
        control_layout.addWidget(self.gesture_toggle)
        
        self.voice_toggle = QPushButton("Voice Recognition: ENABLED")
        self.voice_toggle.setObjectName("toggle-btn-active")
        self.voice_toggle.clicked.connect(self.toggle_voice_mode)
        control_layout.addWidget(self.voice_toggle)
        
        # Security additions
        self.register_face_btn = QPushButton("Security: REGISTER FACE")
        self.register_face_btn.clicked.connect(self.register_face_action)
        control_layout.addWidget(self.register_face_btn)
        
        self.lock_app_btn = QPushButton("Security: LOCK SYSTEM")
        self.lock_app_btn.setStyleSheet("background-color: #E67E22;")
        self.lock_app_btn.clicked.connect(self.lock_app_action)
        control_layout.addWidget(self.lock_app_btn)
        
        left_layout.addWidget(self.control_card)
        self.middle_layout.addLayout(left_layout, stretch=1)
        
        # COLUMN 2: Camera Feed Preview Panel
        camera_card = QFrame()
        camera_card.setObjectName("card")
        camera_layout = QVBoxLayout(camera_card)
        
        camera_title = QLabel("Real-Time Processing Stream")
        camera_title.setObjectName("header")
        camera_layout.addWidget(camera_title)
        
        self.camera_label = QLabel("Camera Feed Loading...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(500, 375)
        self.camera_label.setStyleSheet("background-color: #121214; border-radius: 8px; border: 1px dashed #2C2C35;")
        camera_layout.addWidget(self.camera_label)
        
        self.middle_layout.addWidget(camera_card, stretch=2)
        
        # COLUMN 3: Memory Notes Panel
        self.notes_card = QFrame()
        self.notes_card.setObjectName("card")
        notes_layout = QVBoxLayout(self.notes_card)
        
        notes_title = QLabel("Memory Notes")
        notes_title.setObjectName("header")
        notes_layout.addWidget(notes_title)
        
        self.notes_list = QListWidget()
        notes_layout.addWidget(self.notes_list)
        
        notes_btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_notes)
        notes_btn_layout.addWidget(self.refresh_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #C0392B;")
        self.delete_btn.clicked.connect(self.delete_selected_note)
        notes_btn_layout.addWidget(self.delete_btn)
        
        notes_layout.addLayout(notes_btn_layout)
        
        self.middle_layout.addWidget(self.notes_card, stretch=1)
        
        main_layout.addLayout(self.middle_layout, stretch=3)
        
        # Bottom row: System logs
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        
        log_title = QHBoxLayout()
        log_hdr = QLabel("Activity Terminal Logs")
        log_hdr.setObjectName("header")
        log_title.addWidget(log_hdr)
        
        self.voice_status_label = QLabel("Status: Calibrating mic...")
        self.voice_status_label.setStyleSheet("color: #00FFCC; font-weight: bold;")
        log_title.addWidget(self.voice_status_label, alignment=Qt.AlignRight)
        log_layout.addLayout(log_title)
        
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.append("System Command Logger online.\n")
        log_layout.addWidget(self.log_terminal)
        
        main_layout.addWidget(log_card, stretch=2)

    def start_workers(self):
        # 1. Camera Gesture Worker QThread
        self.camera_worker = CameraWorker()
        self.camera_worker.frame_processed.connect(self.update_camera_frame)
        self.camera_worker.capture_progress.connect(self.face_capture_progress)
        self.camera_worker.capture_finished.connect(self.face_capture_finished)
        self.camera_worker.access_granted.connect(self.face_unlock_success)
        self.camera_worker.start()
        
        # 2. Voice Recognition Worker QThread
        self.voice_worker = VoiceWorker(
            self.brain, self.tts, self.listener, self.automation
        )
        self.voice_worker.status_changed.connect(self.update_voice_status)
        self.voice_worker.command_received.connect(self.log_voice_command)
        self.voice_worker.app_opened.connect(self.log_app_launch)
        self.voice_worker.start()

    # --- Slots / Handlers ---
    def update_camera_frame(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.width(), 
            self.camera_label.height(), 
            Qt.KeepAspectRatio
        ))

    def update_voice_status(self, status):
        self.voice_status_label.setText(f"Status: {status}")
        self.log_terminal.append(f"[System Status] {status}")

    def log_voice_command(self, cmd, reply):
        self.log_terminal.append(f"\n[User Query]: {cmd}")
        self.log_terminal.append(f"[Jarvis Voice Response]: {reply}")
        
        if "note" in cmd:
            self.refresh_notes()
        if "my name is" in cmd or "call me" in cmd:
            self.update_greeting()

    def log_app_launch(self, app_name):
        self.log_terminal.append(f"[Automation] Launched application: {app_name}")

    def update_telemetry(self):
        stats = self.automation.get_system_stats()
        self.cpu_bar.setValue(int(stats["cpu_percent"]))
        self.ram_bar.setValue(int(stats["ram_percent"]))
        
        battery = stats["battery_percent"]
        if battery is not None:
            self.battery_bar.setValue(int(battery))
            plugged = "Charging" if stats["battery_plugged"] else "On Battery"
            self.battery_label.setText(f"Battery: {int(battery)}% ({plugged})")
        else:
            self.battery_bar.setValue(0)
            self.battery_label.setText("Battery status: No battery detected")
            
        self.update_greeting()

    def update_greeting(self):
        user_name = self.brain.db.get_preference("user_name")
        if user_name:
            self.greeting_label.setText(f"User Profile: {user_name.capitalize()} ")
        else:
            self.greeting_label.setText("User Profile: Guest Profile ")

    def refresh_notes(self):
        self.notes_list.clear()
        notes = self.brain.db.get_notes(15)
        for nid, title, content, timestamp in notes:
            display_text = f"{title}\n-> {content}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, nid)
            self.notes_list.addItem(item)

    def delete_selected_note(self):
        selected = self.notes_list.currentItem()
        if selected:
            nid = selected.data(Qt.UserRole)
            self.brain.db.delete_note(nid)
            self.log_terminal.append(f"[DB Action] Deleted note ID: {nid}")
            self.refresh_notes()

    def toggle_gesture_mode(self):
        active = self.camera_worker.gesture_enabled
        self.camera_worker.gesture_enabled = not active
        if active:
            self.gesture_toggle.setText("Camera Gesture: DISABLED")
            self.gesture_toggle.setObjectName("toggle-btn-inactive")
            self.camera_label.clear()
            self.camera_label.setText("Webcam Gesture Control Off")
            self.log_terminal.append("[Control Panel] Camera Gesture recognition deactivated.")
        else:
            self.gesture_toggle.setText("Camera Gesture: ENABLED")
            self.gesture_toggle.setObjectName("toggle-btn-active")
            self.log_terminal.append("[Control Panel] Camera Gesture recognition activated.")
            
        self.gesture_toggle.style().unpolish(self.gesture_toggle)
        self.gesture_toggle.style().polish(self.gesture_toggle)

    def toggle_voice_mode(self):
        active = self.voice_worker.voice_enabled
        self.voice_worker.voice_enabled = not active
        if active:
            self.voice_toggle.setText("Voice Recognition: DISABLED")
            self.voice_toggle.setObjectName("toggle-btn-inactive")
            self.log_terminal.append("[Control Panel] Voice Assistant mic deactivated.")
        else:
            self.voice_toggle.setText("Voice Recognition: ENABLED")
            self.voice_toggle.setObjectName("toggle-btn-active")
            self.log_terminal.append("[Control Panel] Voice Assistant mic activated.")
            
        self.voice_toggle.style().unpolish(self.voice_toggle)
        self.voice_toggle.style().polish(self.voice_toggle)

    # --- Security Features (Phase 9) ---
    def register_face_action(self):
        # Fetch current user name from SQLite or ask
        user_name = self.brain.db.get_preference("user_name")
        if not user_name:
            user_name, ok = QInputDialog.getText(self, "Face Registration", "Please enter your name first:")
            if not ok or not user_name.strip():
                return
            self.brain.db.set_preference("user_name", user_name)
            
        self.log_terminal.append(f"\n[Security] Initializing Face Capture for: {user_name.capitalize()}")
        self.tts.speak("Please look directly at the webcam for face capture.", block=False)
        
        # Disable panels to prevent interaction during capture
        self.register_face_btn.setEnabled(False)
        self.lock_app_btn.setEnabled(False)
        
        self.camera_worker.start_face_capture(user_name)

    def face_capture_progress(self, current, total):
        self.log_terminal.append(f"[Security] Capturing face sample: {current}/{total}")

    def face_capture_finished(self, success):
        self.register_face_btn.setEnabled(True)
        self.lock_app_btn.setEnabled(True)
        
        if success:
            self.log_terminal.append("[Security] Face samples trained. Classifier model weights updated.")
            self.tts.speak("Face database registration completed successfully.")
        else:
            self.log_terminal.append("[Security Error] Face training failed. Please check camera alignment.")
            self.tts.speak("Face training failed. Please try again.")

    def lock_app_action(self):
        # Check if model is trained before locking
        if not self.camera_worker.face_recognizer.model_loaded:
            QMessageBox.warning(
                self, "Lock Error", 
                "You must register your face first before locking the system."
            )
            return
            
        self.system_locked = True
        self.voice_worker.locked = True
        self.log_terminal.append("\n[Security] COMMAND CENTER SECURED. SYSTEM LOCKED.")
        self.tts.speak("System locked. Facial authentication required to restore access.")
        
        # Disable all UI widgets
        self.notes_card.setEnabled(False)
        self.control_card.setEnabled(False)
        self.voice_status_label.setText("Status: LOCKED")
        self.voice_status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        
        # Active camera lock detection
        self.camera_worker.activate_lock()

    def face_unlock_success(self, name):
        self.system_locked = False
        self.voice_worker.locked = False
        
        # Restore GUI panel interactions
        self.notes_card.setEnabled(True)
        self.control_card.setEnabled(True)
        self.voice_status_label.setText("Status: Online (Listening)")
        self.voice_status_label.setStyleSheet("color: #00FFCC; font-weight: bold;")
        
        self.log_terminal.append(f"\n[Security] Face matched: {name.capitalize()}. Access Granted.")
        self.tts.speak(f"Welcome back {name}. Command Center unlocked.")

    def closeEvent(self, event):
        # Stop telemetry timer to prevent database operations during shutdown
        self.telemetry_timer.stop()
        # Properly terminate threads on exit to prevent locking processes
        self.camera_worker.stop()
        self.voice_worker.stop()
        self.brain.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())
