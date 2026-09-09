import time
from config import login_history_collection
from datetime import datetime

def save_login_record(
    user_id,
    email,
    ip_address,
    loc_details,
    client_details,
    risk_level,
    login_status,
    event_type="User Login",
    authentication_method="Password",
    anomaly_score=None,
    trust_score=None,
    impossible_travel=None,
    ai_score=None
):
    """
    Saves a comprehensive login history record to MongoDB and registers it on-chain.
    """
    # Import here to prevent circular import loops
    from blockchain.blockchain_service import add_blockchain_audit_log

    timestamp_sec = int(time.time())
    
    city = loc_details.get("city", "Location unavailable")
    region = loc_details.get("region") or loc_details.get("state") or ""
    state = loc_details.get("state") or loc_details.get("region") or ""
    country = loc_details.get("country", "")
    lat = loc_details.get("latitude") if loc_details.get("latitude") is not None else loc_details.get("lat", 0.0)
    lon = loc_details.get("longitude") if loc_details.get("longitude") is not None else loc_details.get("lon", 0.0)
    isp = loc_details.get("isp", "Unknown ISP")

    # 1. Dispatch log to local Blockchain (Web3.py Ganache provider)
    blockchain_tx = add_blockchain_audit_log(
        user_id=user_id,
        event_type=event_type,
        timestamp=timestamp_sec,
        ip_address=ip_address,
        city=city,
        country=country,
        risk_level=risk_level,
        auth_method=authentication_method,
        login_status=login_status
    )

    record = {
        "username": user_id,  # mapped to user_id requirement
        "user_id": user_id,
        "email": email,
        "login_time": datetime.now(),
        "timestamp": datetime.now(),  # keep for backwards compatibility with test scripts
        "ip_address": ip_address,
        "city": city,
        "region": region,
        "state": state,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "isp": isp,
        "device": client_details.get("device", "Unknown Device"),
        "device_id": client_details.get("device", "Unknown Device"), # keep for compatibility with test scripts
        "browser": client_details.get("browser", "Unknown Browser"),
        "operating_system": client_details.get("operating_system", "Unknown OS"),
        "risk_level": risk_level,
        "login_status": login_status,
        
        # Blockchain audit metrics
        "event_type": event_type,
        "authentication_method": authentication_method,
        "blockchain_transaction_hash": blockchain_tx
    }
    
    if anomaly_score is not None:
        record["anomaly_score"] = anomaly_score
    if trust_score is not None:
        record["trust_score"] = trust_score
    if impossible_travel is not None:
        record["impossible_travel"] = impossible_travel
    if ai_score is not None:
        record["ai_score"] = ai_score
    
    login_history_collection.insert_one(record)
    return record

def get_last_successful_login(user_id):
    """
    Retrieves the most recent successful login history record for a user.
    """
    # Sort by login_time descending, find the first successful record
    record = login_history_collection.find_one(
        {
            "username": user_id,
            "login_status": "Successful"
        },
        sort=[("login_time", -1)]
    )
    return record

def get_user_login_history(user_id):
    """
    Retrieves all login history records for a user.
    """
    records = list(
        login_history_collection.find(
            {"username": user_id},
            {"_id": 0}
        ).sort("login_time", -1)
    )
    return records
