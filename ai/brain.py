import os
import sys
import json
import re
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
        
        # Initialize Database Manager
        self.db = DatabaseManager()
        
        # Predefined patterns for instantaneous execution fallback & memory management
        self.intent_patterns = {
            r"open\s+(chrome|browser)": {"intent": "open_app", "argument": "chrome"},
            r"open\s+notepad": {"intent": "open_app", "argument": "notepad"},
            r"open\s+calculator": {"intent": "open_app", "argument": "calculator"},
            r"open\s+code|open\s+vs\s*code": {"intent": "open_app", "argument": "vscode"},
            r"open\s+explorer": {"intent": "open_app", "argument": "explorer"},
            r"close\s+chrome|close\s+browser": {"intent": "close_app", "argument": "chrome"},
            r"close\s+notepad": {"intent": "close_app", "argument": "notepad"},
            r"close\s+calculator": {"intent": "close_app", "argument": "calc"},
            r"close\s+code|close\s+vs\s*code": {"intent": "close_app", "argument": "code"},
            r"screenshot|take\s+a\s+screenshot": {"intent": "screenshot", "argument": None},
            r"system\s+(status|stats|usage)|cpu|ram": {"intent": "system_stats", "argument": None},
            
            # Memory & Preference Rules
            r"(my name is|call me)\s+([a-zA-Z]+)": {"intent": "save_name", "argument": "group_2"},
            r"what is my name": {"intent": "get_name", "argument": None},
            r"(write|take|add)\s+(a\s+)?note\s*(:)?\s*(.+)": {"intent": "add_note", "argument": "group_4"},
            r"(show|read|list)\s+notes": {"intent": "get_notes", "argument": None},
            r"delete\s+note\s+(\d+)": {"intent": "delete_note", "argument": "group_1"},
            
            # General Actions
            r"search\s+(for\s+)?(.+)": {"intent": "search_web", "argument": "group_2"},
            r"shutdown": {"intent": "shutdown", "argument": None},
            r"abort\s+shutdown": {"intent": "abort_shutdown", "argument": None}
        }

    def process_query(self, query):
        """Processes the query, logs it in chat history, and routes it to rules or LLMs."""
        query = query.lower().strip()
        
        # 1. Log the user's incoming query in database conversation history
        self.db.log_conversation("user", query)
        
        # 2. Check regex-based rule matching
        for pattern, action in self.intent_patterns.items():
            match = re.match(pattern, query)
            if match:
                intent = action["intent"]
                argument = action["argument"]
                
                if argument == "group_1":
                    argument = match.group(1)
                elif argument == "group_2":
                    argument = match.group(2)
                elif argument == "group_4":
                    argument = match.group(4)
                
                reply = ""
                # Handle database preference / note queries directly
                if intent == "save_name" and argument:
                    self.db.set_preference("user_name", argument)
                    reply = f"Alright, I will remember that your name is {argument}."
                elif intent == "get_name":
                    name = self.db.get_preference("user_name")
                    reply = f"Your name is {name}." if name else "I don't know your name yet. You can tell me by saying: my name is..."
                elif intent == "add_note" and argument:
                    title = self.db.add_note(argument)
                    reply = f"I've saved that note under the title: {title}"
                elif intent == "get_notes":
                    notes = self.db.get_notes(5)
                    if notes:
                        notes_text = ", and ".join([f"ID {n[0]} is '{n[2]}'" for n in notes])
                        reply = f"Here are your recent notes: {notes_text}."
                    else:
                        reply = "You don't have any notes saved yet."
                elif intent == "delete_note" and argument:
                    note_id = int(argument)
                    success = self.db.delete_note(note_id)
                    reply = f"Deleted note with ID {note_id}." if success else f"Could not find a note with ID {note_id}."
                else:
                    # General OS Automation intent matched
                    reply = f"Executing command for {intent}"
                    if argument:
                        reply += f" with arguments: {argument}"
                
                # Log Jarvis's responding voice reply
                self.db.log_conversation("jarvis", reply)
                
                return {
                    "intent": intent,
                    "argument": argument,
                    "reply": reply,
                    "source": "regex_rule"
                }
        
        # 3. If no rules matched, query LLM
        if self.openai_key:
            return self._query_openai(query)
        else:
            return self._query_ollama(query)

    def _query_openai(self, query):
        """Queries OpenAI API with conversation history context."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}"
        }
        
        system_prompt = (
            "You are the brain of JarvisX, an AI desktop assistant. "
            "Map the user input to a system action. You must respond ONLY with a JSON object containing: "
            '{"intent": "<intent>", "argument": "<argument or null>", "reply": "<friendly speaking response>"}. '
            "Supported intents: open_app, close_app, open_url, search_web, screenshot, system_stats, general_chat, shutdown. "
            "If it's just a general question/greeting, set intent to 'general_chat' and write a friendly response in 'reply'."
        )
        
        # Build chat history messages array (including the current query which is already saved)
        history = self.db.get_recent_conversations(6)
        messages = [{"role": "system", "content": system_prompt}]
        for sender, msg, _ in history:
            role = "user" if sender == "user" else "assistant"
            messages.append({"role": role, "content": msg})
            
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.2
        }
        
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                content = res_body['choices'][0]['message']['content'].strip()
                res_json = json.loads(content)
                # Log Jarvis's response to database
                self.db.log_conversation("jarvis", res_json.get("reply", ""))
                return res_json
        except Exception as e:
            print(f"[Brain Error] OpenAI API query failed: {e}. Falling back to Ollama or local rules.")
            return self._query_ollama(query)

    def _query_ollama(self, query):
        """Queries a local Ollama instance with conversation history context."""
        url = f"{self.ollama_host}/api/chat"
        
        system_prompt = (
            "You are the brain of JarvisX, an AI desktop assistant. "
            "Map the user input to a system action. Respond ONLY with a valid JSON object containing: "
            '{"intent": "intent_name", "argument": "arg_or_null", "reply": "speaking_response"}. '
            "Supported intents: open_app, close_app, open_url, search_web, screenshot, system_stats, general_chat, shutdown. "
            "If it is a general query, set intent to 'general_chat' and reply."
        )
        
        # Build chat history messages array (including the current query which is already saved)
        history = self.db.get_recent_conversations(6)
        messages = [{"role": "system", "content": system_prompt}]
        for sender, msg, _ in history:
            role = "user" if sender == "user" else "assistant"
            messages.append({"role": role, "content": msg})
            
        data = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json"
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                content = res_body['message']['content'].strip()
                res_json = json.loads(content)
                # Log Jarvis's response to database
                self.db.log_conversation("jarvis", res_json.get("reply", ""))
                return res_json
        except Exception as e:
            # Fallback when LLM is unavailable
            reply = f"I heard you say '{query}', but my AI brain is currently offline. Let's try matching this to standard command features."
            self.db.log_conversation("jarvis", reply)
            return {
                "intent": "general_chat",
                "argument": None,
                "reply": reply,
                "source": "fallback"
            }

if __name__ == "__main__":
    brain = AIBrain()
    print("Testing rule matching:")
    print(brain.process_query("my name is raj"))
    print(brain.process_query("what is my name"))
    print(brain.process_query("write a note: purchase coding monitor tonight"))
    print(brain.process_query("show notes"))
