import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QTextEdit, QListWidget, QListWidgetItem, QFrame, QMessageBox, QInputDialog, QLineEdit
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
        self.setWindowTitle("Jarvis AI Desktop Assistant")
        self.resize(1150, 800)
        
        # Subsystem instances for thread sharing
        self.tts = TTSManager()
        self.listener = VoiceListener()
        self.brain = AIBrain()
        self.automation = SystemAutomation()
        
        self.system_locked = False
        
        # Load stylesheet for professional light look
        self.apply_light_theme()
        
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

    def apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC;
            }
            QWidget {
                color: #1E293B;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
                font-size: 13px;
            }
            QFrame#card {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 14px;
            }
            QLabel#header {
                font-size: 15px;
                font-weight: 700;
                color: #0F172A;
                margin-bottom: 8px;
            }
            QLabel#title {
                font-size: 20px;
                font-weight: 700;
                color: #0F172A;
            }
            QPushButton {
                background-color: #2563EB;
                border: none;
                color: #FFFFFF;
                padding: 9px 16px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton#toggle-btn-active {
                background-color: #ECFDF5;
                color: #065F46;
                border: 1px solid #A7F3D0;
            }
            QPushButton#toggle-btn-active:hover {
                background-color: #D1FAE5;
            }
            QPushButton#toggle-btn-inactive {
                background-color: #FEF2F2;
                color: #991B1B;
                border: 1px solid #FECACA;
            }
            QPushButton#toggle-btn-inactive:hover {
                background-color: #FEE2E2;
            }
            QPushButton#btn-danger {
                background-color: #EF4444;
                color: #FFFFFF;
            }
            QPushButton#btn-danger:hover {
                background-color: #DC2626;
            }
            QPushButton#btn-secondary {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
            }
            QPushButton#btn-secondary:hover {
                background-color: #E2E8F0;
            }
            QPushButton#btn-shortcut {
                background-color: #FFFFFF;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#btn-shortcut:hover {
                background-color: #EFF6FF;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB;
            }
            QProgressBar {
                border: 1px solid #E2E8F0;
                background-color: #F1F5F9;
                border-radius: 6px;
                text-align: center;
                height: 20px;
                color: #334155;
                font-weight: 600;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 5px;
            }
            QTextEdit {
                background-color: #FAFAFA;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #334155;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 8px;
            }
            QListWidget {
                background-color: #FAFAFA;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                border-bottom: 1px solid #F1F5F9;
                padding: 8px;
                border-radius: 6px;
                color: #334155;
            }
            QListWidget::item:hover {
                background-color: #F1F5F9;
            }
            QListWidget::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
                font-weight: 600;
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
        title_label = QLabel("Jarvis AI Assistant")
        title_label.setObjectName("title")
        header_layout.addWidget(title_label)
        
        # User name greeting label
        self.greeting_label = QLabel("Welcome, User")
        self.greeting_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background-color: #F1F5F9; padding: 6px 14px; border-radius: 20px;")
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
        
        telemetry_title = QLabel("System Performance")
        telemetry_title.setObjectName("header")
        telemetry_layout.addWidget(telemetry_title)
        
        telemetry_layout.addWidget(QLabel("CPU Usage:"))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setValue(0)
        telemetry_layout.addWidget(self.cpu_bar)
        
        telemetry_layout.addWidget(QLabel("RAM Usage:"))
        self.ram_bar = QProgressBar()
        self.ram_bar.setValue(0)
        telemetry_layout.addWidget(self.ram_bar)
        
        telemetry_layout.addWidget(QLabel("Battery Status:"))
        self.battery_bar = QProgressBar()
        self.battery_bar.setValue(0)
        telemetry_layout.addWidget(self.battery_bar)
        
        self.battery_label = QLabel("Battery: Checking...")
        self.battery_label.setStyleSheet("font-size: 11px; color: #64748B; margin-top: 2px;")
        telemetry_layout.addWidget(self.battery_label)
        
        left_layout.addWidget(telemetry_card)
        
        # Card 2: Modules Controls Toggles & Security
        self.control_card = QFrame()
        self.control_card.setObjectName("card")
        control_layout = QVBoxLayout(self.control_card)
        
        control_title = QLabel("Controls & Security")
        control_title.setObjectName("header")
        control_layout.addWidget(control_title)
        
        self.gesture_toggle = QPushButton("Camera Gesture: ENABLED")
        self.gesture_toggle.setObjectName("toggle-btn-active")
        self.gesture_toggle.clicked.connect(self.toggle_gesture_mode)
        control_layout.addWidget(self.gesture_toggle)
        
        self.voice_toggle = QPushButton("Voice Assistant: ENABLED")
        self.voice_toggle.setObjectName("toggle-btn-active")
        self.voice_toggle.clicked.connect(self.toggle_voice_mode)
        control_layout.addWidget(self.voice_toggle)
        
        # Security additions
        self.register_face_btn = QPushButton("Register Face ID")
        self.register_face_btn.clicked.connect(self.register_face_action)
        control_layout.addWidget(self.register_face_btn)
        
        self.lock_app_btn = QPushButton("Lock Assistant")
        self.lock_app_btn.setObjectName("btn-danger")
        self.lock_app_btn.clicked.connect(self.lock_app_action)
        control_layout.addWidget(self.lock_app_btn)
        
        left_layout.addWidget(self.control_card)
        self.middle_layout.addLayout(left_layout, stretch=1)
        
        # COLUMN 2: Camera Feed Preview Panel
        camera_card = QFrame()
        camera_card.setObjectName("card")
        camera_layout = QVBoxLayout(camera_card)
        
        camera_title = QLabel("Live Camera Feed")
        camera_title.setObjectName("header")
        camera_layout.addWidget(camera_title)
        
        self.camera_label = QLabel("Initializing Camera...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(500, 375)
        self.camera_label.setStyleSheet("background-color: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0; color: #64748B; font-weight: 500;")
        camera_layout.addWidget(self.camera_label)
        
        self.middle_layout.addWidget(camera_card, stretch=2)
        
        # COLUMN 3: Memory Notes Panel
        self.notes_card = QFrame()
        self.notes_card.setObjectName("card")
        notes_layout = QVBoxLayout(self.notes_card)
        
        notes_title = QLabel("Saved Notes")
        notes_title.setObjectName("header")
        notes_layout.addWidget(notes_title)
        
        self.notes_list = QListWidget()
        notes_layout.addWidget(self.notes_list)
        
        notes_btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("btn-secondary")
        self.refresh_btn.clicked.connect(self.refresh_notes)
        notes_btn_layout.addWidget(self.refresh_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("btn-danger")
        self.delete_btn.clicked.connect(self.delete_selected_note)
        notes_btn_layout.addWidget(self.delete_btn)
        
        notes_layout.addLayout(notes_btn_layout)
        
        self.middle_layout.addWidget(self.notes_card, stretch=1)
        
        main_layout.addLayout(self.middle_layout, stretch=3)
        
        # Bottom row: Interactive AI Assistant Chat & Command Bar
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        
        log_title = QHBoxLayout()
        log_hdr = QLabel("AI Assistant Stream")
        log_hdr.setObjectName("header")
        log_title.addWidget(log_hdr)
        
        # Help / User Guide Button
        self.help_btn = QPushButton("❓ How to Use (Guide)")
        self.help_btn.setObjectName("btn-shortcut")
        self.help_btn.clicked.connect(self.show_help_dialog)
        log_title.addWidget(self.help_btn)
        
        self.voice_status_label = QLabel("Status: Online (Listening)")
        self.voice_status_label.setStyleSheet("color: #059669; font-weight: 600; background-color: #ECFDF5; padding: 4px 10px; border-radius: 12px; font-size: 12px;")
        log_title.addWidget(self.voice_status_label, alignment=Qt.AlignRight)
        log_layout.addLayout(log_title)
        
        # Quick Action Shortcuts Bar
        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(8)
        
        btn_chrome = QPushButton("🌐 Open Chrome")
        btn_chrome.setObjectName("btn-shortcut")
        btn_chrome.clicked.connect(lambda: self.execute_quick_command("open chrome"))
        shortcuts_layout.addWidget(btn_chrome)
        
        btn_yt = QPushButton("🎵 Open YouTube")
        btn_yt.setObjectName("btn-shortcut")
        btn_yt.clicked.connect(lambda: self.execute_quick_command("open youtube"))
        shortcuts_layout.addWidget(btn_yt)
        
        btn_vscode = QPushButton("💻 Open VS Code")
        btn_vscode.setObjectName("btn-shortcut")
        btn_vscode.clicked.connect(lambda: self.execute_quick_command("open vs code"))
        shortcuts_layout.addWidget(btn_vscode)
        
        btn_shot = QPushButton("📸 Screenshot")
        btn_shot.setObjectName("btn-shortcut")
        btn_shot.clicked.connect(lambda: self.execute_quick_command("take screenshot"))
        shortcuts_layout.addWidget(btn_shot)
        
        btn_stats = QPushButton("📊 System Usage")
        btn_stats.setObjectName("btn-shortcut")
        btn_stats.clicked.connect(lambda: self.execute_quick_command("what is my cpu usage"))
        shortcuts_layout.addWidget(btn_stats)
        
        log_layout.addLayout(shortcuts_layout)
        
        # Chat Stream Area
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.append("👋 <b>Jarvis AI:</b> Welcome Rajkishor! Type any command below or use Voice/Gestures to control your PC.\n")
        log_layout.addWidget(self.log_terminal)
        
        # Text Command Input Bar
        input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type a command or ask a question (e.g., 'Open Chrome', 'Search machine learning on google')...")
        self.cmd_input.returnPressed.connect(self.send_text_command)
        input_layout.addWidget(self.cmd_input, stretch=4)
        
        self.send_cmd_btn = QPushButton("Send Command")
        self.send_cmd_btn.clicked.connect(self.send_text_command)
        input_layout.addWidget(self.send_cmd_btn, stretch=1)
        
        log_layout.addLayout(input_layout)
        
        main_layout.addWidget(log_card, stretch=3)

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
        if self.camera_worker.gesture_enabled:
            pixmap = QPixmap.fromImage(q_img)
            self.camera_label.setPixmap(pixmap.scaled(
                self.camera_label.width(), 
                self.camera_label.height(), 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    def update_voice_status(self, status):
        self.voice_status_label.setText(f"Status: {status}")
        self.log_terminal.append(f"[System Status] {status}")

    def execute_quick_command(self, cmd_text):
        self.cmd_input.setText(cmd_text)
        self.send_text_command()

    def send_text_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        
        self.cmd_input.clear()
        self.log_terminal.append(f"<b>🧑 You:</b> {cmd}")
        
        # Process command using AI Brain
        result = self.brain.process_command(cmd)
        intent = result["intent"]
        params = result["params"]
        reply = result["reply"]
        
        # Execute Desktop Automation based on intent
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
        
        # Display response & speak out
        self.log_terminal.append(f"<b>🤖 Jarvis:</b> {reply}\n")
        self.tts.speak(reply, block=False)
        
        if "note" in cmd.lower():
            self.refresh_notes()
        if "my name is" in cmd.lower() or "call me" in cmd.lower():
            self.update_greeting()

    def show_help_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Jarvis AI - User Guide & Commands")
        msg.setTextFormat(Qt.RichText)
        msg.setText("""
        <h3>🤖 Welcome to Jarvis AI Assistant User Guide</h3>
        <p>Aap Jarvis ko <b>Voice</b>, <b>Text Commands</b>, ya <b>Hand Gestures</b> se control kar sakte hain:</p>

        <h4>1. 💬 Voice & Text Commands (Boliye ya Type Karein):</h4>
        <ul>
            <li><b>Apps Open/Close:</b> <i>"Open Chrome"</i>, <i>"Open YouTube"</i>, <i>"Open VS Code"</i>, <i>"Close Notepad"</i></li>
            <li><b>System Actions:</b> <i>"Take screenshot"</i>, <i>"What is my CPU usage?"</i>, <i>"Volume up"</i>, <i>"Mute"</i></li>
            <li><b>Web Search:</b> <i>"Search Python tutorials on Google"</i></li>
            <li><b>Notes & Memory:</b> <i>"Remember buy milk"</i>, <i>"Save note project deadline tomorrow"</i></li>
            <li><b>General Questions:</b> <i>"What is artificial intelligence?"</i>, <i>"Tell me a joke"</i></li>
        </ul>

        <h4>2. ✋ Hand Gestures (Webcam se Control):</h4>
        <ul>
            <li><b>👆 Index Finger Up:</b> Mouse Cursor screen par move hoga</li>
            <li><b>✌️ Index + Middle Pinch:</b> Left Click karega</li>
            <li><b>👌 Thumb + Index Pinch:</b> Right Click karega</li>
            <li><b>🖐️ 3 Ungliyan Up/Down:</b> Screen Scroll karega</li>
        </ul>

        <h4>3. 👤 Face ID Security:</h4>
        <ul>
            <li>Click <b>'Register Face ID'</b> -> Look at camera to save face model.</li>
            <li>Click <b>'Lock Assistant'</b> -> App will lock until authorized face is detected.</li>
        </ul>
        """)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def log_voice_command(self, cmd, reply):
        self.log_terminal.append(f"<b>🎙️ User (Voice):</b> {cmd}")
        self.log_terminal.append(f"<b>🤖 Jarvis:</b> {reply}\n")
        
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
        self.voice_status_label.setText("Status: Locked")
        self.voice_status_label.setStyleSheet("color: #DC2626; font-weight: 600; background-color: #FEF2F2; padding: 4px 10px; border-radius: 12px; font-size: 12px;")
        
        # Active camera lock detection
        self.camera_worker.activate_lock()

    def face_unlock_success(self, name):
        self.system_locked = False
        self.voice_worker.locked = False
        
        # Restore GUI panel interactions
        self.notes_card.setEnabled(True)
        self.control_card.setEnabled(True)
        self.voice_status_label.setText("Status: Online (Listening)")
        self.voice_status_label.setStyleSheet("color: #059669; font-weight: 600; background-color: #ECFDF5; padding: 4px 10px; border-radius: 12px; font-size: 12px;")
        
        self.log_terminal.append(f"\n[Security] Face matched: {name.capitalize()}. Access Granted.")
        self.tts.speak(f"Welcome back {name}. Command Center unlocked.")

    def closeEvent(self, event):
        try:
            self.telemetry_timer.stop()
            self.camera_worker.active = False
            self.voice_worker.active = False
            if hasattr(self.camera_worker, 'cap') and self.camera_worker.cap:
                self.camera_worker.cap.release()
            self.brain.db.close()
        except Exception:
            pass
        event.accept()
        os._exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())
