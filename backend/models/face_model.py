import logging
from datetime import datetime
from config import db, is_db_connected

logger = logging.getLogger("face_model")

# MongoDB collections
face_profiles_collection = db["face_profiles"]
face_logs_collection = db["face_logs"]

# In-memory fallback dictionary if MongoDB is not active
_IN_MEMORY_FACE_PROFILES = {}
_IN_MEMORY_FACE_LOGS = []


def save_face_profile(username, face_encoding, metadata=None):
    """
    Save or update a user's face embedding vector in MongoDB (with in-memory fallback).

    :param username: User identifier (str).
    :param face_encoding: 128-dimensional list of float numbers.
    :param metadata: Optional dict with camera metadata, registration timestamp, etc.
    """
    record = {
        "username": username,
        "face_encoding": face_encoding,
        "metadata": metadata or {},
        "updated_at": datetime.utcnow().isoformat()
    }

    # Store in memory cache
    _IN_MEMORY_FACE_PROFILES[username] = record

    if is_db_connected():
        try:
            face_profiles_collection.update_one(
                {"username": username},
                {"$set": record},
                upsert=True
            )
            logger.info(f"[FACE MODEL] Successfully persisted face profile in MongoDB for user: {username}")
            return True
        except Exception as e:
            logger.error(f"[FACE MODEL] Failed to save face profile in MongoDB: {str(e)}")
            return True
    else:
        logger.info(f"[FACE MODEL] MongoDB offline. Saved face profile in-memory for user: {username}")
        return True


def get_face_profile(username):
    """
    Retrieve registered face profile for a user.

    :param username: User identifier.
    :return: dict with 'username', 'face_encoding', 'updated_at', or None.
    """
    doc = None
    if is_db_connected():
        try:
            doc = face_profiles_collection.find_one({"username": username}, {"_id": 0})
        except Exception as e:
            logger.error(f"[FACE MODEL] Error querying face profile from MongoDB: {str(e)}")

    if not doc:
        doc = _IN_MEMORY_FACE_PROFILES.get(username)

    if doc and doc.get("face_encoding"):
        enc = doc["face_encoding"]
        if isinstance(enc, list):
            try:
                doc["face_encoding"] = [float(x) for x in enc]
            except Exception:
                pass
    return doc


def delete_face_profile(username):
    """
    Delete registered face profile for a user.

    :param username: User identifier.
    :return: True if deleted.
    """
    if username in _IN_MEMORY_FACE_PROFILES:
        del _IN_MEMORY_FACE_PROFILES[username]

    if is_db_connected():
        try:
            face_profiles_collection.delete_one({"username": username})
        except Exception as e:
            logger.error(f"[FACE MODEL] Failed to delete face profile from MongoDB: {str(e)}")

    return True


def save_face_auth_log(username, is_match, confidence_score, status_code, details=None):
    """
    Record an audit log entry for a face authentication attempt.

    :param username: User identifier.
    :param is_match: Boolean flag indicating if authentication succeeded.
    :param confidence_score: Float confidence score (0-100%).
    :param status_code: Status string code (e.g. 'SUCCESS', 'FACE_MISMATCH', 'NO_FACE_DETECTED').
    :param details: Additional error details or image metadata.
    """
    log_entry = {
        "username": username,
        "is_match": is_match,
        "confidence_score": confidence_score,
        "status_code": status_code,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }

    _IN_MEMORY_FACE_LOGS.append(log_entry)

    if is_db_connected():
        try:
            face_logs_collection.insert_one(log_entry.copy())
            logger.info(f"[FACE MODEL] Logged face auth attempt for user '{username}': status={status_code}")
        except Exception as e:
            logger.error(f"[FACE MODEL] Failed to insert face auth log in MongoDB: {str(e)}")

    return log_entry


def get_face_auth_logs(username=None, limit=50):
    """
    Retrieve face authentication audit logs.

    :param username: Optional filter by user ID.
    :param limit: Maximum logs to return.
    :return: List of log records.
    """
    if is_db_connected():
        try:
            query = {"username": username} if username else {}
            cursor = face_logs_collection.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"[FACE MODEL] Failed to query logs from MongoDB: {str(e)}")

    # Fallback to in-memory logs
    logs = _IN_MEMORY_FACE_LOGS
    if username:
        logs = [l for l in logs if l.get("username") == username]
    return sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
