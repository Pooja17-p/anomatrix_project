"""
Device Fingerprinting MongoDB Model Layer
Manages persistence for device_fingerprints and device_trust_history collections.
Includes in-memory storage fallback for local development when MongoDB is offline.
"""

import logging
from datetime import datetime
from config import db, is_db_connected

logger = logging.getLogger(__name__)

# In-memory store fallback
_in_memory_fingerprints = []
_in_memory_history = []


def save_device_fingerprint(fingerprint_data):
    """
    Saves or updates a trusted device fingerprint profile for a user.
    """
    if is_db_connected():
        try:
            collection = db["device_fingerprints"]
            query = {
                "username": fingerprint_data["username"],
                "fingerprint_id": fingerprint_data["fingerprint_id"]
            }
            update = {
                "$set": {
                    "fingerprint_id": fingerprint_data["fingerprint_id"],
                    "username": fingerprint_data["username"],
                    "attributes": fingerprint_data.get("attributes", {}),
                    "device_name": fingerprint_data.get("device_name", "Unknown Device"),
                    "last_verified": datetime.utcnow().isoformat() + "Z",
                    "status": fingerprint_data.get("status", "Trusted"),
                    "trust_score": fingerprint_data.get("trust_score", 100),
                },
                "$setOnInsert": {
                    "first_seen": datetime.utcnow().isoformat() + "Z"
                }
            }
            result = collection.update_one(query, update, upsert=True)
            logger.info(f"Saved device fingerprint {fingerprint_data['fingerprint_id']} to MongoDB for user {fingerprint_data['username']}")
            return {"status": "success", "upserted_id": str(result.upserted_id) if result.upserted_id else "updated"}
        except Exception as e:
            logger.error(f"MongoDB Error saving device fingerprint: {e}")

    # Fallback to in-memory store
    for item in _in_memory_fingerprints:
        if item["username"] == fingerprint_data["username"] and item["fingerprint_id"] == fingerprint_data["fingerprint_id"]:
            item.update(fingerprint_data)
            item["last_verified"] = datetime.utcnow().isoformat() + "Z"
            return {"status": "success", "store": "in-memory-updated"}

    new_record = {
        **fingerprint_data,
        "first_seen": datetime.utcnow().isoformat() + "Z",
        "last_verified": datetime.utcnow().isoformat() + "Z",
    }
    _in_memory_fingerprints.append(new_record)
    logger.info(f"Saved device fingerprint {fingerprint_data['fingerprint_id']} to in-memory fallback store")
    return {"status": "success", "store": "in-memory-created"}


def register_device(arg1, *args, **kwargs):
    """
    Flexible wrapper function supporting both dict payload calls:
    register_device({"device_id": ..., "username": ...})
    and positional parameter calls:
    register_device(user_id, device_fingerprint, ip_address, browser, os)
    """
    if isinstance(arg1, dict):
        username = str(arg1.get("username") or arg1.get("user_id") or "anonymous")
        fingerprint_id = str(arg1.get("device_id") or arg1.get("fingerprint_id") or "dev_default")
        browser = arg1.get("browser", "Browser")
        os_sys = arg1.get("os", "OS")
        fp_data = {
            "username": username,
            "fingerprint_id": fingerprint_id,
            "attributes": arg1,
            "device_name": f"{browser} on {os_sys}",
            "status": "Trusted",
            "trust_score": 100,
        }
        return save_device_fingerprint(fp_data)
    else:
        user_id = str(arg1)
        device_fingerprint = str(args[0]) if len(args) > 0 else str(kwargs.get("device_fingerprint", "dev_default"))
        ip_address = args[1] if len(args) > 1 else kwargs.get("ip_address", "127.0.0.1")
        browser = args[2] if len(args) > 2 else kwargs.get("browser", "Browser")
        os_sys = args[3] if len(args) > 3 else kwargs.get("os", "OS")
        fp_data = {
            "username": user_id,
            "fingerprint_id": device_fingerprint,
            "attributes": {
                "browser_name": browser,
                "os": os_sys,
                "ip_address": ip_address,
            },
            "device_name": f"{browser} on {os_sys}",
            "status": "Trusted",
            "trust_score": 100,
        }
        return save_device_fingerprint(fp_data)


def find_device(arg1, *args, **kwargs):
    """
    Flexible search function supporting single parameter calls:
    find_device(device_id)
    and dual parameter calls:
    find_device(user_id, device_fingerprint)
    """
    target_fp = None
    target_user = None

    if len(args) > 0:
        target_user = str(arg1)
        target_fp = str(args[0])
    elif "device_fingerprint" in kwargs:
        target_user = str(arg1)
        target_fp = str(kwargs["device_fingerprint"])
    else:
        target_fp = str(arg1)

    if is_db_connected():
        try:
            collection = db["device_fingerprints"]
            query = {}
            if target_fp:
                query["fingerprint_id"] = target_fp
            if target_user:
                query["username"] = target_user
            doc = collection.find_one(query, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            logger.error(f"MongoDB Error finding device: {e}")

    # Fallback to in-memory store
    for item in _in_memory_fingerprints:
        match_fp = not target_fp or item.get("fingerprint_id") == target_fp
        match_user = not target_user or item.get("username") == target_user
        if match_fp and match_user:
            return item
    return None


def get_trusted_devices(username):
    """
    Retrieves all trusted device fingerprints registered for a given user.
    """
    if is_db_connected():
        try:
            collection = db["device_fingerprints"]
            docs = list(collection.find({"username": username}, {"_id": 0}))
            return docs
        except Exception as e:
            logger.error(f"MongoDB Error fetching trusted devices: {e}")

    # Fallback to in-memory store
    return [d for d in _in_memory_fingerprints if d.get("username") == username]


def log_device_verification(log_data):
    """
    Logs a continuous device verification event.
    """
    log_entry = {
        "username": log_data.get("username", "anonymous"),
        "fingerprint_id": log_data.get("fingerprint_id", "unknown"),
        "match_percentage": log_data.get("match_percentage", 100),
        "risk_level": log_data.get("risk_level", "Trusted"),
        "attributes": log_data.get("attributes", {}),
        "attribute_breakdown": log_data.get("attribute_breakdown", {}),
        "status": log_data.get("status", "Verified"),
        "timestamp": log_data.get("timestamp") or datetime.utcnow().isoformat() + "Z",
    }

    if is_db_connected():
        try:
            collection = db["device_trust_history"]
            res = collection.insert_one(log_entry)
            log_entry["_id"] = str(res.inserted_id)
            return log_entry
        except Exception as e:
            logger.error(f"MongoDB Error logging device verification: {e}")

    log_entry["_id"] = f"mem_log_{len(_in_memory_history) + 1}"
    _in_memory_history.insert(0, log_entry)
    return log_entry


def get_device_history(username=None, limit=30):
    """
    Retrieves historical device verification logs.
    """
    if is_db_connected():
        try:
            collection = db["device_trust_history"]
            query = {"username": username} if username else {}
            docs = list(collection.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit))
            return docs
        except Exception as e:
            logger.error(f"MongoDB Error fetching device history: {e}")

    # Fallback to in-memory store
    filtered = [d for d in _in_memory_history if not username or d.get("username") == username]
    return filtered[:limit]


def revoke_device_trust(username, fingerprint_id):
    """
    Revokes trust status for a specific device fingerprint.
    """
    if is_db_connected():
        try:
            collection = db["device_fingerprints"]
            res = collection.update_one(
                {"username": username, "fingerprint_id": fingerprint_id},
                {"$set": {"status": "Revoked", "trust_score": 0}}
            )
            return res.modified_count > 0
        except Exception as e:
            logger.error(f"MongoDB Error revoking device trust: {e}")

    # Fallback to in-memory store
    for item in _in_memory_fingerprints:
        if item.get("username") == username and item.get("fingerprint_id") == fingerprint_id:
            item["status"] = "Revoked"
            item["trust_score"] = 0
            return True
    return False