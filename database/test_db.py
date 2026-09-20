import os
import sys

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

def test_database():
    print("[Test] Initializing Database Manager...")
    db = DatabaseManager()
    
    # 1. Test Preferences
    print("[Test] Writing preference...")
    db.set_preference("test_pref", "hello_world")
    val = db.get_preference("test_pref")
    assert val == "hello_world", f"Expected 'hello_world', got '{val}'"
    print("[Test] Preferences working.")

    # 2. Test Conversations
    print("[Test] Writing conversation history...")
    db.log_conversation("user", "Hello this is a test")
    db.log_conversation("jarvis", "Acknowledged")
    chats = db.get_recent_conversations(2)
    assert len(chats) == 2, "Expected 2 chat turns"
    assert chats[0][0] == "user"
    assert chats[1][0] == "jarvis"
    print("[Test] Conversation logging working.")

    # 3. Test App Usage Tracker
    print("[Test] Incrementing app launch logs...")
    db.log_app_launch("chrome")
    db.log_app_launch("chrome")
    top_apps = db.get_top_apps(1)
    assert len(top_apps) == 1, "Expected 1 tracked app"
    assert top_apps[0][0] == "chrome"
    assert top_apps[0][1] >= 2, f"Expected usage count >= 2, got {top_apps[0][1]}"
    print("[Test] App usage tracking working.")

    # 4. Test Notes
    print("[Test] Adding note...")
    note_content = "This is a secret note test"
    title = db.add_note(note_content, "Test Note")
    notes = db.get_notes(1)
    assert len(notes) == 1, "Expected 1 note in list"
    assert notes[0][1] == "Test Note"
    assert notes[0][2] == note_content
    
    # Test delete note
    print("[Test] Deleting note...")
    note_id = notes[0][0]
    success = db.delete_note(note_id)
    assert success is True, "Expected delete_note to return True"
    assert len(db.get_notes(1)) == 0, "Expected notes list to be empty"
    print("[Test] Notes features working.")

    db.close()
    print("[Test] ALL DATABASE TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_database()
