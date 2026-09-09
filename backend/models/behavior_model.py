from config import behavior_logs_collection
from datetime import datetime


def save_behavior_log(log_data):
    """
    Inserts a preprocessed behavior log into the behavior_logs collection.
    """
    if "created_at" not in log_data:
        log_data["created_at"] = datetime.utcnow().isoformat() + "Z"

    result = behavior_logs_collection.insert_one(log_data)
    log_data["_id"] = str(result.inserted_id)
    return log_data


def get_behavior_history(username, session_id=None, limit=50, skip=0):
    """
    Retrieves behavior logs for a specific user, sorted by newest first.
    """
    query = {"username": username}
    if session_id:
        query["session_id"] = session_id

    cursor = (
        behavior_logs_collection.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )

    logs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)

    return logs


def get_behavior_stats(username):
    """
    Retrieves raw behavior logs for aggregation metrics computation.
    """
    cursor = behavior_logs_collection.find({"username": username})
    logs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)
    return logs


def get_latest_behavior_log(username):
    """
    Returns the most recent behavior log entry for a user.
    """
    doc = behavior_logs_collection.find_one(
        {"username": username}, sort=[("timestamp", -1)]
    )
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc
