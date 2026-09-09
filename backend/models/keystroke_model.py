import logging
from datetime import datetime
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import uuid

from config import (
    keystroke_logs_collection,
    keystroke_sessions_collection,
    keystroke_profiles_collection,
    db,
)

logger = logging.getLogger(__name__)

# Collection for saving trained AI keystroke model metadata
keystroke_models_meta_collection = db["keystroke_models_metadata"]

# In-memory storage fallback for when MongoDB is offline during testing/local run
_in_memory_logs = []
_in_memory_sessions = {}
_in_memory_profiles = {}
_in_memory_metadata = {}


def save_keystroke_log(log_data):
    """
    Saves a keystroke dynamics telemetry snapshot into MongoDB keystroke_logs collection.
    Falls back to in-memory store if MongoDB is offline.
    """
    if "created_at" not in log_data:
        log_data["created_at"] = datetime.utcnow().isoformat() + "Z"

    try:
        res = keystroke_logs_collection.insert_one(log_data)
        log_data["_id"] = str(res.inserted_id)
        return log_data
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for save_keystroke_log, using in-memory fallback: %s", str(e))
        doc = dict(log_data)
        doc["_id"] = str(uuid.uuid4())
        _in_memory_logs.append(doc)
        return doc


def save_or_update_keystroke_session(
    session_id, username, typing_score, status, summary=None
):
    """
    Creates a new keystroke authentication session or updates an existing session entry in MongoDB.
    Falls back to in-memory store if MongoDB is offline.
    """
    now_iso = datetime.utcnow().isoformat() + "Z"
    try:
        existing = keystroke_sessions_collection.find_one({"session_id": session_id})

        if existing:
            update_fields = {
                "last_updated": now_iso,
                "typing_score": typing_score,
                "status": status,
                "total_packets": existing.get("total_packets", 0) + 1,
            }
            if summary:
                update_fields["latest_summary"] = summary

            keystroke_sessions_collection.update_one(
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
                "typing_score": typing_score,
                "status": status,
                "total_packets": 1,
                "latest_summary": summary or {},
            }
            res = keystroke_sessions_collection.insert_one(session_doc)
            session_doc["_id"] = str(res.inserted_id)
            return session_doc
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for save_or_update_keystroke_session, using in-memory fallback: %s", str(e))
        session_doc = _in_memory_sessions.get(session_id, {
            "session_id": session_id,
            "username": username,
            "created_at": now_iso,
            "total_packets": 0,
            "_id": str(uuid.uuid4())
        })
        session_doc["last_updated"] = now_iso
        session_doc["typing_score"] = typing_score
        session_doc["status"] = status
        session_doc["total_packets"] += 1
        if summary:
            session_doc["latest_summary"] = summary
        _in_memory_sessions[session_id] = session_doc
        return session_doc


def get_keystroke_profile(username):
    """
    Retrieves the user's historical typing dynamics baseline profile from MongoDB.
    """
    try:
        doc = keystroke_profiles_collection.find_one({"username": username})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_keystroke_profile: %s", str(e))
        if username in _in_memory_profiles:
            return _in_memory_profiles[username]

    # Standard human default baseline profile for new user accounts
    return {
        "username": username,
        "avg_hold_time": 90.0,
        "avg_flight_time": 140.0,
        "avg_typing_speed": 55.0,
        "rhythm_variance": 35.0,
        "error_rate": 0.04,
        "total_samples": 0,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


def update_keystroke_profile(username, feature_vector):
    """
    Updates the user's historical typing dynamics profile using Exponential Moving Average (EMA).
    """
    alpha = 0.2  # EMA smoothing weight factor
    try:
        existing = keystroke_profiles_collection.find_one({"username": username})

        if existing:
            new_profile = {
                "avg_hold_time": round(
                    (1 - alpha) * existing.get("avg_hold_time", 90.0)
                    + alpha * feature_vector.get("hold_time", 90.0),
                    2,
                ),
                "avg_flight_time": round(
                    (1 - alpha) * existing.get("avg_flight_time", 140.0)
                    + alpha * feature_vector.get("flight_time", 140.0),
                    2,
                ),
                "avg_typing_speed": round(
                    (1 - alpha) * existing.get("avg_typing_speed", 55.0)
                    + alpha * feature_vector.get("typing_speed", 55.0),
                    2,
                ),
                "rhythm_variance": round(
                    (1 - alpha) * existing.get("rhythm_variance", 35.0)
                    + alpha * feature_vector.get("rhythm_variance", 35.0),
                    2,
                ),
                "error_rate": round(
                    (1 - alpha) * existing.get("error_rate", 0.04)
                    + alpha * feature_vector.get("error_rate", 0.04),
                    4,
                ),
                "total_samples": existing.get("total_samples", 0) + 1,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }
            keystroke_profiles_collection.update_one(
                {"username": username}, {"$set": new_profile}
            )
        else:
            new_profile = {
                "username": username,
                "avg_hold_time": round(feature_vector.get("hold_time", 90.0), 2),
                "avg_flight_time": round(feature_vector.get("flight_time", 140.0), 2),
                "avg_typing_speed": round(feature_vector.get("typing_speed", 55.0), 2),
                "rhythm_variance": round(feature_vector.get("rhythm_variance", 35.0), 2),
                "error_rate": round(feature_vector.get("error_rate", 0.04), 4),
                "total_samples": 1,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            keystroke_profiles_collection.insert_one(new_profile)
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for update_keystroke_profile: %s", str(e))
        prof = _in_memory_profiles.get(username, get_keystroke_profile(username))
        prof["avg_hold_time"] = round((1 - alpha) * prof.get("avg_hold_time", 90.0) + alpha * feature_vector.get("hold_time", 90.0), 2)
        prof["total_samples"] = prof.get("total_samples", 0) + 1
        _in_memory_profiles[username] = prof


def get_latest_keystroke_score(username):
    """
    Fetches the most recent typing similarity score and status for a user.
    """
    try:
        doc = keystroke_sessions_collection.find_one(
            {"username": username}, sort=[("last_updated", -1)]
        )
        if doc:
            return {
                "typing_score": doc.get("typing_score", 91),
                "status": doc.get("status", "Trusted"),
            }
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_latest_keystroke_score: %s", str(e))
        for sess in reversed(list(_in_memory_sessions.values())):
            if sess.get("username") == username:
                return {
                    "typing_score": sess.get("typing_score", 91),
                    "status": sess.get("status", "Trusted"),
                }

    return {
        "typing_score": 91,
        "status": "Trusted",
    }


def get_keystroke_history(username=None, limit=50):
    """
    Retrieves historical keystroke dynamics logs for a user sorted by newest first.
    """
    query = {}
    if username:
        query = {"$or": [{"username": username}, {"user_id": username}]}

    try:
        cursor = (
            keystroke_logs_collection.find(query)
            .sort("created_at", -1)
            .limit(limit)
        )
        logs = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        if logs:
            return logs
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_keystroke_history: %s", str(e))

    mem_logs = [log for log in _in_memory_logs if not username or log.get("username") == username or log.get("user_id") == username]
    return list(reversed(mem_logs))[:limit]


def get_all_keystroke_logs_for_training(username=None):
    """
    Retrieves all historical keystroke telemetry logs for training AI ML models.
    """
    query = {}
    if username:
        query = {"$or": [{"username": username}, {"user_id": username}]}

    try:
        cursor = keystroke_logs_collection.find(query)
        logs = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        if logs:
            return logs
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for get_all_keystroke_logs_for_training: %s", str(e))

    return [log for log in _in_memory_logs if not username or log.get("username") == username or log.get("user_id") == username]


def save_keystroke_model_metadata(username, metadata):
    """
    Persists AI keystroke model training metadata into MongoDB.
    """
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    try:
        keystroke_models_meta_collection.update_one(
            {"username": username},
            {"$set": metadata},
            upsert=True
        )
    except (PyMongoError, ServerSelectionTimeoutError) as e:
        logger.warning("MongoDB unavailable for save_keystroke_model_metadata: %s", str(e))
        _in_memory_metadata[username] = metadata
