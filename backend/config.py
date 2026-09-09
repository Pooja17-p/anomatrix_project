from pymongo import MongoClient

# Initialize MongoClient with a fast server selection timeout to prevent blocking if Mongo is offline
client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)

db = client["anomatrix_db"]

def is_db_connected():
    """
    Utility function checking if MongoDB server is responsive.
    """
    try:
        client.admin.command('ping')
        return True
    except Exception:
        return False

users_collection = db["users"]

devices_collection = db["devices"]

login_history_collection = db["login_history"]

behavior_logs_collection = db["behavior_logs"]

sessions_collection = db["sessions"]

mouse_logs_collection = db["mouse_logs"]

mouse_sessions_collection = db["mouse_sessions"]

mouse_profiles_collection = db["mouse_profiles"]

keystroke_logs_collection = db["keystroke_logs"]

keystroke_sessions_collection = db["keystroke_sessions"]

keystroke_profiles_collection = db["keystroke_profiles"]

# Face Security Configuration Constants
FACE_MATCH_THRESHOLD = 0.58
FACE_MAX_FAILED_ATTEMPTS = 3
FACE_LOCKOUT_MINUTES = 15