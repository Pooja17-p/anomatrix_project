from config import users_collection


# -----------------------------
# CREATE USER
# -----------------------------
def create_user(user_data):
    # Ensure default face security fields are set
    user_data.setdefault("face_enabled", False)
    user_data.setdefault("face_registered", False)
    user_data.setdefault("face_registered_at", None)
    user_data.setdefault("face_last_verified_at", None)
    user_data.setdefault("face_failed_attempts", 0)
    user_data.setdefault("face_locked_until", None)
    return users_collection.insert_one(user_data)



# -----------------------------
# FIND USER
# -----------------------------
def find_user(username):
    return users_collection.find_one({
        "username": username
    })


# -----------------------------
# UPDATE TRUST SCORE
# -----------------------------
def update_trust(username, trust_score, risk_level):

    users_collection.update_one(

        {
            "username": username
        },

        {
            "$set": {

                "trust_score": trust_score,

                "risk_level": risk_level

            }
        }

    )


# -----------------------------
# UPDATE TRUSTED DEVICE
# -----------------------------
def update_device(username, device_id):

    users_collection.update_one(

        {
            "username": username
        },

        {
            "$set": {

                "registered_device": device_id

            }
        }

    )


# -----------------------------
# GET ALL USERS
# -----------------------------
def get_all_users():

    return list(

        users_collection.find({}, {

            "password": 0

        })

    )


# -----------------------------
# UPDATE SETTINGS
# -----------------------------
def update_settings(username, settings_data):

    users_collection.update_one(

        {
            "username": username
        },

        {
            "$set": {

                "mfa_enabled": settings_data.get("mfa_enabled", False),

                "trust_devices": settings_data.get("trust_devices", False),

                "email_alerts": settings_data.get("email_alerts", True),

                "dark_mode": settings_data.get("dark_mode", False),

                "auto_logout": settings_data.get("auto_logout", True)

            }
        }

    )


# -----------------------------
# UPDATE USER LOCATION
# -----------------------------
def update_user_location(username, ip, city, country, lat, lon):
    users_collection.update_one(
        {"username": username},
        {
            "$set": {
                "last_ip": ip,
                "last_city": city,
                "last_country": country,
                "last_latitude": lat,
                "last_longitude": lon
            }
        }
    )


# -----------------------------
# FACE SECURITY MANAGEMENT
# -----------------------------
def update_face_status(username, enabled=True, registered=True):
    from datetime import datetime
    now_iso = datetime.utcnow().isoformat()
    update_dict = {
        "face_enabled": enabled,
        "face_registered": registered,
        "faceRegistered": registered
    }
    if registered:
        update_dict["face_registered_at"] = now_iso
    users_collection.update_one(
        {"username": username},
        {"$set": update_dict}
    )


def update_face_last_verified(username):
    from datetime import datetime
    now_iso = datetime.utcnow().isoformat()
    users_collection.update_one(
        {"username": username},
        {
            "$set": {
                "face_last_verified_at": now_iso,
                "face_failed_attempts": 0,
                "face_locked_until": None
            }
        }
    )


def record_face_failed_attempt(username, max_attempts=3, lockout_minutes=15):
    from datetime import datetime, timedelta
    user = find_user(username) or {}
    current_failed = user.get("face_failed_attempts", 0) + 1
    update_data = {"face_failed_attempts": current_failed}
    
    locked = False
    lock_until_iso = None
    if current_failed >= max_attempts:
        lock_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
        lock_until_iso = lock_until.isoformat()
        update_data["face_locked_until"] = lock_until_iso
        locked = True
        
    users_collection.update_one(
        {"username": username},
        {"$set": update_data}
    )
    return current_failed, locked, lock_until_iso


def reset_face_failed_attempts(username):
    users_collection.update_one(
        {"username": username},
        {"$set": {"face_failed_attempts": 0, "face_locked_until": None}}
    )

