import sqlite3
import os
import datetime
from pathlib import Path

# Locate database path
DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "jarvis.db"

class DatabaseManager:
    def __init__(self):
        # Create directory if it doesn't exist
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Creates the initial database schema if tables do not exist."""
        cursor = self.conn.cursor()
        
        # 1. Preferences Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                pref_key TEXT PRIMARY KEY,
                pref_value TEXT
            )
        """)
        
        # 2. Conversation History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sender TEXT,
                message TEXT
            )
        """)
        
        # 3. Notes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                content TEXT
            )
        """)
        
        # 4. App Usage Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_usage (
                app_name TEXT PRIMARY KEY,
                use_count INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

    # --- Preferences Mappings ---
    def get_preference(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute("SELECT pref_value FROM preferences WHERE pref_key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_preference(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO preferences (pref_key, pref_value) 
            VALUES (?, ?)
            ON CONFLICT(pref_key) DO UPDATE SET pref_value = excluded.pref_value
        """, (key, str(value)))
        self.conn.commit()

    # --- Conversation History Mappings ---
    def log_conversation(self, sender, message):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conversation_history (sender, message, timestamp) 
            VALUES (?, ?, datetime('now', 'localtime'))
        """, (sender, message))
        self.conn.commit()

    def get_recent_conversations(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT sender, message, timestamp 
            FROM conversation_history 
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        # Return in chronological order
        return cursor.fetchall()[::-1]

    # --- Notes Mappings ---
    def add_note(self, content, title=None):
        if not title:
            # Auto-generate title using first 5 words or current date
            words = content.split()
            title = " ".join(words[:4]) if words else "Untitled Note"
            title += "..."
            
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notes (title, content, timestamp) 
            VALUES (?, ?, datetime('now', 'localtime'))
        """, (title, content))
        self.conn.commit()
        return title

    def get_notes(self, limit=20):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, content, timestamp 
            FROM notes 
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        return cursor.fetchall()

    def delete_note(self, note_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # --- App Usage Tracking ---
    def log_app_launch(self, app_name):
        app_name = app_name.lower().strip()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO app_usage (app_name, use_count, last_used) 
            VALUES (?, 1, datetime('now', 'localtime'))
            ON CONFLICT(app_name) DO UPDATE SET 
                use_count = use_count + 1,
                last_used = datetime('now', 'localtime')
        """, (app_name,))
        self.conn.commit()

    def get_top_apps(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT app_name, use_count, last_used 
            FROM app_usage 
            ORDER BY use_count DESC LIMIT ?
        """, (limit,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = DatabaseManager()
    print("Testing DB operations...")
    db.set_preference("user_name", "Raj")
    print("User Name Preference:", db.get_preference("user_name"))
    
    db.log_conversation("user", "Hello Jarvis")
    db.log_conversation("jarvis", "Hello Raj, how can I assist you?")
    print("Recent Chats:", db.get_recent_conversations(2))
    
    db.log_app_launch("chrome")
    db.log_app_launch("chrome")
    db.log_app_launch("notepad")
    print("Top Apps:", db.get_top_apps())
    
    title = db.add_note("Buy groceries and milk tonight", "Groceries")
    print(f"Added Note: {title}")
    print("Notes List:", db.get_notes(1))
    db.close()
