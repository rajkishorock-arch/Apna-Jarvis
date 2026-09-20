import speech_recognition as sr
import sys
import os

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

class VoiceListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.microphone_available = False
        
        try:
            self.microphone = sr.Microphone()
            print("[Voice] Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
            self.microphone_available = True
            print("[Voice] Calibration complete.")
        except Exception as e:
            print(f"[Voice] Microphone setup notice: {e}. Voice input fallback to Text Chat.")

    def listen(self, timeout=4, phrase_time_limit=6):
        """Listens to the microphone and returns the transcribed string (lowercase)."""
        if not self.microphone_available:
            return None

        try:
            with self.microphone as source:
                print("[Voice] Listening...")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
                print("[Voice] Processing speech...")
                query = self.recognizer.recognize_google(audio)
                print(f"[User]: {query}")
                return query.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("[Voice] Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"[Voice] Google Speech Recognition service error: {e}")
            return None
        except Exception as e:
            print(f"[Voice] Speech recognition notice: {e}")
            return None

if __name__ == "__main__":
    listener = VoiceListener()
    while True:
        command = listener.listen()
        if command:
            if "exit" in command or "quit" in command:
                print("Exiting test listener.")
                break
