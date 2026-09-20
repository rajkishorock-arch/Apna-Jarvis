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
        self.recognizer.energy_threshold = 300  # Default microphone sensitivity threshold
        self.microphone = sr.Microphone()
        
        # Calibrate microphone noise levels
        print("[Voice] Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Voice] Calibration complete.")

    def listen(self, timeout=5, phrase_time_limit=8):
        """Listens to the microphone and returns the transcribed string (lowercase)."""
        with self.microphone as source:
            try:
                print("[Voice] Listening...")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
                print("[Voice] Processing speech...")
                query = self.recognizer.recognize_google(audio)
                print(f"[User]: {query}")
                return query.lower()
            except sr.WaitTimeoutError:
                # No speech detected within the timeout
                return None
            except sr.UnknownValueError:
                # Speech was detected but could not be understood
                print("[Voice] Could not understand audio.")
                return None
            except sr.RequestError as e:
                # Connection or API issues
                print(f"[Voice] Google Speech Recognition service error: {e}")
                return None
            except Exception as e:
                print(f"[Voice] Error occurred during recognition: {e}")
                return None

if __name__ == "__main__":
    listener = VoiceListener()
    while True:
        command = listener.listen()
        if command:
            if "exit" in command or "quit" in command:
                print("Exiting test listener.")
                break
