import pyttsx3
import threading
import sys
import os

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

class TTSManager:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self._configure_engine()
        except Exception as e:
            print(f"[TTS Error] Failed to initialize speech engine: {e}")
            self.engine = None

    def _configure_engine(self):
        if not self.engine:
            return
            
        # Set words per minute (speed)
        self.engine.setProperty('rate', config.TTS_RATE)
        # Set volume level (0.0 to 1.0)
        self.engine.setProperty('volume', config.TTS_VOLUME)
        
        # Select voice (male/female based on availability)
        voices = self.engine.getProperty('voices')
        if voices:
            # Safely select voice index
            voice_index = min(config.TTS_VOICE_ID, len(voices) - 1)
            self.engine.setProperty('voice', voices[voice_index].id)

    def speak(self, text, block=True):
        """Synthesize text into speech. Can run in blocking or non-blocking mode."""
        if not self.engine:
            print(f"[Jarvis (Console)]: {text}")
            return

        print(f"[Jarvis]: {text}")
        
        if block:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            # Run in a separate thread for non-blocking speaking
            thread = threading.Thread(target=self._speak_thread, args=(text,))
            thread.daemon = True
            thread.start()

    def _speak_thread(self, text):
        # We need a separate pyttsx3 instance in sub-threads as it isn't thread-safe
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', config.TTS_RATE)
            engine.setProperty('volume', config.TTS_VOLUME)
            voices = engine.getProperty('voices')
            if voices:
                voice_index = min(config.TTS_VOICE_ID, len(voices) - 1)
                engine.setProperty('voice', voices[voice_index].id)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS Thread Error] Failed to speak in thread: {e}")

if __name__ == "__main__":
    tts = TTSManager()
    tts.speak("Hello! I am Jarvis, your AI desktop assistant. How can I help you today?")
