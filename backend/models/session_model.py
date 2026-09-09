from config import sessions_collection
from datetime import datetime


def create_or_update_session(
    username, session_id, duration, latest_risk="Low", summary=None
):
    """
    Creates a new session or updates an existing session entry in the sessions collection.
    """
    now_iso = datetime.utcnow().isoformat() + "Z"

    existing_session = sessions_collection.find_one({"session_id": session_id})

    if existing_session:
        update_fields = {
            "last_active": now_iso,
            "session_duration": max(duration, existing_session.get("session_duration", 0)),
            "latest_risk_level": latest_risk,
            "total_logs_collected": existing_session.get("total_logs_collected", 0) + 1,
        }
        if summary:
            update_fields["summary"] = summary

        sessions_collection.update_one(
            {"session_id": session_id}, {"$set": update_fields}
        )
        existing_session.update(update_fields)
        existing_session["_id"] = str(existing_session["_id"])
        return existing_session
    else:
        session_data = {
            "session_id": session_id,
            "username": username,
            "start_time": now_iso,
            "last_active": now_iso,
            "session_duration": duration,
            "total_logs_collected": 1,
            "latest_risk_level": latest_risk,
            "status": "active",
            "summary": summary or {},
        }
        res = sessions_collection.insert_one(session_data)
        session_data["_id"] = str(res.inserted_id)
        return session_data


def get_session(session_id):
    """
    Retrieves a session document by session_id.
    """
    doc = sessions_collection.find_one({"session_id": session_id})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def get_user_sessions(username, limit=20):
    """
    Retrieves recent sessions for a user.
    """
    cursor = (
        sessions_collection.find({"username": username})
        .sort("last_active", -1)
        .limit(limit)
    )
    sessions = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        sessions.append(doc)
    return sessions
