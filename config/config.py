import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent

# Camera & Vision Configurations
CAMERA_INDEX = 0          # Default webcam
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Hand Tracking Settings
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7
MAX_NUM_HANDS = 1

# Speech recognition & synthesis Configurations
TTS_RATE = 175            # Words per minute
TTS_VOLUME = 1.0          # 0.0 to 1.0
TTS_VOICE_ID = 0          # Default system voice index

# Wake word definition
WAKE_WORD = "jarvis"

# LLM Configurations
LLM_PROVIDER = "ollama"   # "ollama" or "openai"
OLLAMA_MODEL = "llama3"   # Or "mistral", "gemma", etc.
OLLAMA_HOST = "http://localhost:11434"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Gesture Control Settings
MOUSE_SENSITIVITY = 1.5
CLICK_DISTANCE_THRESHOLD = 30  # Pixels between fingers to trigger click
DRAG_DISTANCE_THRESHOLD = 25
