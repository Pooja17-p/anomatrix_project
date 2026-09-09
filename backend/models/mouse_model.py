import logging
from datetime import datetime
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import uuid

from config import (
    mouse_logs_collection,
    mouse_sessions_collection,
    mouse_profiles_collection,
    db,
)

logger = logging.getLogger(__name__)

# Collection for saving trained AI model metadata
mouse_models_meta_collection = db["mouse_models_metadata"]

# In-memory storage fallback for when MongoDB is offline during testing/local run
_in_memory_logs = []
_in_memory_sessions = {}
_in_memory_profiles = {}
_in_memory_metadata = {}


def save_mouse_log(log_data):
    """
    Saves a mouse trajectory and kinematics telemetry entry into MongoDB mouse_logs collection.
    Falls back to in-memory store if MongoDB is offline.
    """
    if "created_at" not in log_data:
        log_data["created_at"] = datetime.utcnow().isoformat() + "Z"

    try:
        res = mouse_logs_collection.insert_one(log_data)
        log_data["_id"] = str(res.inserted_id)
        return log_data
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for save_mouse_log, using in-memory fallback: %s", str(e))
        doc = dict(log_data)
        doc["_id"] = str(uuid.uuid4())
        _in_memory_logs.append(doc)
        return doc


def save_or_update_mouse_session(session_id, username, mouse_score, status, summary=None):
    """
    Creates a new mouse authentication session or updates an existing session document in MongoDB.
    Falls back to in-memory store if MongoDB is offline.
    """
    now_iso = datetime.utcnow().isoformat() + "Z"
    try:
        existing = mouse_sessions_collection.find_one({"session_id": session_id})
        if existing:
            update_fields = {
                "last_updated": now_iso,
                "mouse_score": mouse_score,
                "status": status,
                "total_packets": existing.get("total_packets", 0) + 1,
            }
            if summary:
                update_fields["latest_summary"] = summary

            mouse_sessions_collection.update_one(
                {"session_id": session_id}, {"$set": update_fields}
            )
            existing.update(update_fields)
            existing["_id"] = str(existing["_id"])
            return existing
        else:
            session_doc = {
                "session_id": session_id,
                "username": username,
                "created_at": now_iso,
                "last_updated": now_iso,
                "mouse_score": mouse_score,
                "status": status,
                "total_packets": 1,
                "latest_summary": summary or {},
            }
            res = mouse_sessions_collection.insert_one(session_doc)
            session_doc["_id"] = str(res.inserted_id)
            return session_doc
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for save_or_update_mouse_session, using in-memory fallback: %s", str(e))
        session_doc = _in_memory_sessions.get(session_id, {
            "session_id": session_id,
            "username": username,
            "created_at": now_iso,
            "total_packets": 0,
            "_id": str(uuid.uuid4())
        })
        session_doc["last_updated"] = now_iso
        session_doc["mouse_score"] = mouse_score
        session_doc["status"] = status
        session_doc["total_packets"] += 1
        if summary:
            session_doc["latest_summary"] = summary
        _in_memory_sessions[session_id] = session_doc
        return session_doc


def get_mouse_profile(username):
    """
    Retrieves the user's historical mouse motion baseline profile from MongoDB.
    """
    try:
        doc = mouse_profiles_collection.find_one({"username": username})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_mouse_profile: %s", str(e))
        if username in _in_memory_profiles:
            return _in_memory_profiles[username]

    return {
        "username": username,
        "avg_speed": 350.0,
        "avg_acceleration": 90.0,
        "avg_direction": 180.0,
        "direction_variance": 45.0,
        "click_rate": 0.5,
        "scroll_speed": 2.0,
        "total_samples": 0,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


def update_mouse_profile(username, feature_vector):
    """
    Updates user's historical mouse baseline profile using Exponential Moving Average (EMA).
    """
    alpha = 0.2
    try:
        existing = mouse_profiles_collection.find_one({"username": username})
        if existing:
            new_profile = {
                "avg_speed": round((1 - alpha) * existing.get("avg_speed", 350.0) + alpha * feature_vector.get("speed", 350.0), 2),
                "avg_acceleration": round((1 - alpha) * existing.get("avg_acceleration", 90.0) + alpha * feature_vector.get("acceleration", 90.0), 2),
                "avg_direction": round((1 - alpha) * existing.get("avg_direction", 180.0) + alpha * feature_vector.get("direction", 180.0), 2),
                "direction_variance": round((1 - alpha) * existing.get("direction_variance", 45.0) + alpha * feature_vector.get("direction_variance", 45.0), 2),
                "click_rate": round((1 - alpha) * existing.get("click_rate", 0.5) + alpha * feature_vector.get("click_rate", 0.5), 2),
                "scroll_speed": round((1 - alpha) * existing.get("scroll_speed", 2.0) + alpha * feature_vector.get("scroll_speed", 2.0), 2),
                "total_samples": existing.get("total_samples", 0) + 1,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }
            mouse_profiles_collection.update_one({"username": username}, {"$set": new_profile})
        else:
            new_profile = {
                "username": username,
                "avg_speed": round(feature_vector.get("speed", 350.0), 2),
                "avg_acceleration": round(feature_vector.get("acceleration", 90.0), 2),
                "avg_direction": round(feature_vector.get("direction", 180.0), 2),
                "direction_variance": round(feature_vector.get("direction_variance", 45.0), 2),
                "click_rate": round(feature_vector.get("click_rate", 0.5), 2),
                "scroll_speed": round(feature_vector.get("scroll_speed", 2.0), 2),
                "total_samples": 1,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            mouse_profiles_collection.insert_one(new_profile)
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for update_mouse_profile: %s", str(e))
        prof = _in_memory_profiles.get(username, get_mouse_profile(username))
        prof["avg_speed"] = round((1 - alpha) * prof.get("avg_speed", 350.0) + alpha * feature_vector.get("speed", 350.0), 2)
        prof["total_samples"] = prof.get("total_samples", 0) + 1
        _in_memory_profiles[username] = prof


def get_latest_mouse_score(username):
    """
    Fetches the most recent mouse similarity score and status for a given user.
    """
    try:
        doc = mouse_sessions_collection.find_one({"username": username}, sort=[("last_updated", -1)])
        if doc:
            return {
                "mouse_score": doc.get("mouse_score", 100),
                "status": doc.get("status", "Trusted"),
            }
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_latest_mouse_score: %s", str(e))
        for sess in reversed(list(_in_memory_sessions.values())):
            if sess.get("username") == username:
                return {
                    "mouse_score": sess.get("mouse_score", 100),
                    "status": sess.get("status", "Trusted"),
                }
    return {
        "mouse_score": 100,
        "status": "Trusted",
    }


def get_mouse_history(username=None, limit=50):
    """
    Retrieves historical mouse tracking logs for a user (or all users) sorted by newest first.
    """
    query = {}
    if username:
        query = {"$or": [{"username": username}, {"user_id": username}]}

    try:
        cursor = mouse_logs_collection.find(query).sort("created_at", -1).limit(limit)
        logs = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        if logs:
            return logs
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_mouse_history: %s", str(e))

    mem_logs = [log for log in _in_memory_logs if not username or log.get("username") == username or log.get("user_id") == username]
    return list(reversed(mem_logs))[:limit]


def get_all_mouse_logs_for_training(username=None):
    """
    Retrieves all historical mouse telemetry logs for training machine learning models.
    """
    query = {}
    if username:
        query = {"$or": [{"username": username}, {"user_id": username}]}

    try:
        cursor = mouse_logs_collection.find(query)
        logs = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        if logs:
            return logs
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_all_mouse_logs_for_training: %s", str(e))

    return [log for log in _in_memory_logs if not username or log.get("username") == username or log.get("user_id") == username]


def save_mouse_model_metadata(username, metadata):
    """
    Persists AI model training metadata into MongoDB.
    """
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    try:
        mouse_models_meta_collection.update_one(
            {"username": username},
            {"$set": metadata},
            upsert=True
        )
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for save_mouse_model_metadata: %s", str(e))
        _in_memory_metadata[username] = metadata
