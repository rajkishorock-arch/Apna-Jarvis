import os
import sys
import json
import re
import datetime
import urllib.request
import urllib.error

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from database.db_manager import DatabaseManager

class AIBrain:
    def __init__(self):
        self.openai_key = config.OPENAI_API_KEY
        self.ollama_host = config.OLLAMA_HOST
        self.ollama_model = config.OLLAMA_MODEL
        self.db = DatabaseManager()

    def process_command(self, query):
        """Intelligent natural language parser supporting English & Hinglish commands."""
        query_raw = query
        q = query.lower().strip()
        
        # Log incoming query
        self.db.log_conversation("user", query_raw)
        
        intent = "general_chat"
        params = {}
        reply = ""

        # 1. YouTube Play / Video Search
        if "play" in q and "youtube" in q:
            song = re.sub(r"(play|on youtube|youtube|bajao)", "", q, flags=re.IGNORECASE).strip()
            if song:
                intent = "open_website"
                encoded_song = urllib.parse.quote(song)
                params = {"url": f"https://www.youtube.com/results?search_query={encoded_song}"}
                reply = f"Searching and playing '{song}' on YouTube."
            else:
                intent = "open_website"
                params = {"url": "https://www.youtube.com"}
                reply = "Opening YouTube."
        elif any(k in q for k in ["open youtube", "youtube kholo", "youtube chalo", "youtube"]):
            intent = "open_website"
            params = {"url": "https://www.youtube.com"}
            reply = "Opening YouTube."

        # 2. Chrome / Browser
        elif any(k in q for k in ["open chrome", "chrome kholo", "launch chrome", "browser kholo", "open browser", "chrome"]):
            intent = "launch_app"
            params = {"app": "chrome"}
            reply = "Opening Google Chrome."

        # 3. VS Code
        elif any(k in q for k in ["open vs code", "open vscode", "code kholo", "open code", "vs code", "vscode"]):
            intent = "launch_app"
            params = {"app": "vscode"}
            reply = "Launching Visual Studio Code."

        # 4. Notepad & Calculator
        elif any(k in q for k in ["open notepad", "notepad kholo", "notepad"]):
            intent = "launch_app"
            params = {"app": "notepad"}
            reply = "Opening Notepad."
        elif any(k in q for k in ["open calculator", "calculator kholo", "calculator", "calc"]):
            intent = "launch_app"
            params = {"app": "calculator"}
            reply = "Opening Calculator."

        # 5. Volume Controls
        elif any(k in q for k in ["volume up", "aawaz badhao", "increase volume"]):
            intent = "volume_control"
            params = {"action": "up"}
            reply = "Increasing volume."
        elif any(k in q for k in ["volume down", "aawaz kam karo", "decrease volume"]):
            intent = "volume_control"
            params = {"action": "down"}
            reply = "Decreasing volume."
        elif any(k in q for k in ["mute", "unmute", "aawaz band karo"]):
            intent = "volume_control"
            params = {"action": "mute"}
            reply = "Muting system audio."

        # 6. Close App
        elif "close" in q or "band karo" in q:
            if "chrome" in q or "browser" in q:
                intent = "close_app"
                params = {"app": "chrome"}
                reply = "Closing Chrome."
            elif "notepad" in q:
                intent = "close_app"
                params = {"app": "notepad"}
                reply = "Closing Notepad."
            elif "code" in q or "vscode" in q:
                intent = "close_app"
                params = {"app": "code"}
                reply = "Closing VS Code."
            else:
                reply = "Which application would you like me to close?"

        # 7. Screenshot
        elif any(k in q for k in ["screenshot", "take screenshot", "photo lo", "screen capture", "snapshot"]):
            intent = "take_screenshot"
            params = {}
            reply = "Taking a screenshot now!"

        # 8. System Usage / Stats / CPU / RAM / Battery
        elif any(k in q for k in ["cpu", "ram", "system stats", "system usage", "battery", "performance"]):
            intent = "system_stats"
            params = {}
            reply = "Displaying system performance metrics on dashboard."

        # 9. Time & Date
        elif any(k in q for k in ["time", "samay", "wakt"]):
            now = datetime.datetime.now().strftime("%I:%M %p")
            intent = "general_chat"
            reply = f"The current time is {now}."
        elif any(k in q for k in ["date", "tarikh", "aaj konsa din"]):
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            intent = "general_chat"
            reply = f"Today is {today}."

        # 10. Weather
        elif any(k in q for k in ["weather", "mausam"]):
            intent = "web_search"
            params = {"query": "current weather forecast"}
            reply = "Checking current weather forecast for your location."

        # 11. Math Calculation (Voice Calculator)
        elif any(k in q for k in ["plus", "minus", "times", "multiplied by", "divided by", "calculate"]):
            try:
                expr = q.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("multiplied by", "*").replace("divided by", "/")
                expr = re.sub(r"[^0-9\+\-\*\/\.\(\)\s]", "", expr).strip()
                if expr:
                    res = eval(expr)
                    intent = "general_chat"
                    reply = f"The answer is {res}."
                else:
                    reply = "I couldn't parse the math calculation."
            except Exception:
                reply = "Sorry, I couldn't calculate that math expression."

        # 12. Memory & Preferences
        elif "my name is" in q or "call me" in q:
            match = re.search(r"(my name is|call me)\s+([a-zA-Z]+)", q)
            name = match.group(2).capitalize() if match else "User"
            self.db.set_preference("user_name", name)
            intent = "general_chat"
            reply = f"Pleasure to meet you, {name}! I have saved your name."
        elif "what is my name" in q or "mera naam kya hai" in q:
            name = self.db.get_preference("user_name")
            reply = f"Your name is {name}." if name else "I don't know your name yet. Tell me by saying 'my name is [your name]'!"
            intent = "general_chat"
        elif "note" in q or "remember" in q or "yaad rakho" in q:
            note_text = re.sub(r"^(save note|add note|take note|note|remember|yaad rakho)\s*:?\s*", "", q_raw, flags=re.IGNORECASE).strip()
            if note_text:
                title = self.db.add_note(note_text)
                reply = f"Note saved: '{title}'"
            else:
                reply = "What note would you like me to save?"
            intent = "general_chat"

        # 13. Web Search
        elif q.startswith("search ") or q.startswith("google ") or "search" in q:
            search_query = re.sub(r"^(search|google|search for)\s+", "", q, flags=re.IGNORECASE).strip()
            intent = "web_search"
            params = {"query": search_query}
            reply = f"Searching Google for '{search_query}'."

        # 14. Greetings & General Chat
        elif any(k in q for k in ["hi", "hello", "hey", "namaste", "kaise ho", "how are you"]):
            user_name = self.db.get_preference("user_name") or "there"
            intent = "general_chat"
            reply = f"Hello {user_name}! I am active and ready. How can I help you with your computer?"
        elif any(k in q for k in ["who are you", "tum kaun ho", "what is your name"]):
            intent = "general_chat"
            reply = "I am Jarvis, your AI Desktop Assistant. I can open apps, search YouTube/Google, take screenshots, calculate math, and manage your PC!"

        # 15. Fallback for general questions
        else:
            intent = "web_search"
            params = {"query": q_raw}
            reply = f"Searching Google for '{q_raw}'."

        # Log Jarvis reply
        self.db.log_conversation("jarvis", reply)

        return {
            "intent": intent,
            "params": params,
            "reply": reply
        }

    def process_query(self, query):
        """Backwards compatibility alias for process_command."""
        res = self.process_command(query)
        return {
            "intent": res["intent"],
            "argument": res["params"].get("app") or res["params"].get("query") or res["params"].get("url"),
            "reply": res["reply"],
            "source": "smart_brain"
        }

if __name__ == "__main__":
    brain = AIBrain()
    print(brain.process_command("play Arijit Singh songs on youtube"))
    print(brain.process_command("what is 25 times 4"))
