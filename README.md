# JarvisX – AI Desktop Assistant with Voice & Gesture Control

JarvisX is an industry-level AI Desktop Operating System Assistant that combines **Computer Vision-based Hand Gesture Recognition** and **Voice Commands** into a unified, modular desktop automation controller.

---

## 🚀 Key Features

- **🎙️ Voice Assistant Control**: Uses Speech-to-Text and Text-to-Speech to parse natural commands ("Hey Jarvis, open VS Code").
- **✋ Hand Gesture Control**: MediaPipe-based hand tracking maps camera inputs to OS events (cursor movement, left/right clicks, dragging, scrolling).
- **🧠 Natural Language Understanding (LLM)**: Matches command patterns and routes queries to either local Ollama (Llama/Gemma) or OpenAI GPT models.
- **📁 Desktop Automation**: PyAutoGUI interface triggers screenshots, system stats queries, application launches/closures, and web searches.
- **🔌 Modular Architecture**: Highly separated codebase for easy scaling and customization.

---

## 🛠️ Project Structure

```text
JarvisX/
│
├── config/
│   └── config.py          # Centralized configuration & settings
│
├── gesture/
│   ├── hand_tracker.py    # MediaPipe hand landmarks tracker
│   └── gesture_controller.py # Mappings for cursor, clicks, and scrolling
│
├── voice/
│   ├── tts.py             # PyTTSx3 Text-to-Speech Engine
│   └── asr.py             # SpeechRecognition Audio capturing (Speech-to-Text)
│
├── automation/
│   └── system_control.py  # Automation wrappers (launch apps, screenshots, CPU/RAM stats)
│
├── ai/
│   └── brain.py           # Regex intent parsing & LLM orchestration
│
├── main.py                # Multi-threaded entry point coordinating voice & gestures
├── requirements.txt       # Dependencies manifest
└── README.md              # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10 or 3.11 or 3.12 (Windows recommended)
- A working webcam and microphone.

### Setup Instructions

1. **Clone the repository and open the workspace**:
   ```bash
   cd jar
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Assistant**:
   ```bash
   python main.py
   ```

---

## 🎮 How to Control JarvisX

### Voice Commands (Activate with wake word "Jarvis")

- *"Hey Jarvis, open Chrome"*
- *"Hey Jarvis, what is my CPU usage?"*
- *"Hey Jarvis, search for deep learning on google"*
- *"Hey Jarvis, take a screenshot"*
- *"Hey Jarvis, disable gesture"* (toggles camera feed off)
- *"Hey Jarvis, enable gesture"* (toggles camera feed back on)

### Gesture Controls (Webcam input)

- **👆 Index Finger Up**: Move cursor (scaled to screen with exponential smoothing).
- **✌ Index + Middle Fingers Up**: Pinch tips together to trigger a **Left Click**.
- **👌 Thumb + Index Pinch**: Pinch tips together to trigger a **Right Click**.
- **🖐️ Index + Middle + Ring Fingers Up**: Move index vertically up and down to **Scroll**.
