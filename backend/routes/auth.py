
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from models.user_model import create_user, find_user, update_trust, update_settings, update_user_location

from models.device_model import (
    register_device,
    find_device
)

from models.login_history_model import (
    save_login_history,
    get_user_logins
)

from service.trust_engine import calculate_trust_score
from service.anomaly_engine import detect_anomaly
from service.email_service import send_otp_email_async
from service.ai_model_service import calculate_ai_anomaly_score
from utils.geo_helper import get_ip_geolocation, detect_impossible_travel, calculate_distance, get_request_client_geo

import bcrypt
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def log_failed_login_attempt(username):
    try:
        ip_address, loc_details = get_request_client_geo(request)
        
        user_agent = request.headers.get("User-Agent", "")
        browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
        os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
        
        req_json = {}
        try:
            req_json = request.json or {}
        except:
            pass
            
        client_details = {
            "device": req_json.get("device_id") or "Unknown Device",
            "browser": browser,
            "operating_system": os_name
        }
        
        from models.login_history import save_login_record
        save_login_record(
            user_id=username,
            email="",
            ip_address=ip_address,
            loc_details=loc_details,
            client_details=client_details,
            risk_level="High",
            login_status="Failed",
            event_type="Failed Login",
            authentication_method="Password"
        )
    except Exception as e:
        logger.warning(f"Error logging failed login: {e}")

auth_bp = Blueprint('auth', __name__)



## -----------------------------
# REGISTER ROUTE
# -----------------------------
@auth_bp.route('/register', methods=['POST'])
def register():

    data = request.json

    name = data.get("name")
    email = data.get("email")
    department = data.get("department")
    employee_id = data.get("employee_id")

    username = data.get("username")
    password = data.get("password")

    device_id = data.get("device_id")
    browser = data.get("browser")
    os = data.get("os")

    if not username or not password:

        return {

            "message": "Username and Password Required"

        },400

    existing_user = find_user(username)

    if existing_user:

        return {

            "message":"User Already Exists"

        },400

    hashed_password = bcrypt.hashpw(

        password.encode("utf-8"),

        bcrypt.gensalt()

    )

    # Resolve registration IP & Geolocation
    ip = data.get("mock_ip") or request.headers.get("X-Forwarded-For") or request.remote_addr
    geo = get_ip_geolocation(ip)

    user = {

        "name":name,

        "email":email,

        "department":department,

        "employee_id":employee_id,

        "username":username,

        "password": hashed_password,

        "registered_device": device_id,

        "browser": browser,

        "os": os,

        "trust_score": 100,

        "risk_level": "Low",

        "mfa_enabled": False,

        "trust_devices": False,

        "email_alerts": True,

        "dark_mode": False,

        "auto_logout": True,
        
        "last_ip": ip,
        
        "last_city": geo.get("city"),
        
        "last_country": geo.get("country"),
        
        "last_latitude": geo.get("lat"),
        
        "last_longitude": geo.get("lon"),
        
        "registered_country": geo.get("country")

    }

    create_user(user)

    register_device({

        "device_id":device_id,

        "username":username,

        "trust_level":"trusted"

    })

    return {

        "message":"Registration Successful",

        "trust_score":100,

        "risk_level":"Low"

    },201


# -----------------------------
# LOGIN ROUTE
# -----------------------------
@auth_bp.route('/login', methods=['POST'])
def login():

    data = request.json

    username = data.get("username")
    password = data.get("password")
    device_id = data.get("device_id")

    user = find_user(username)

    if not user:
        log_failed_login_attempt(username)
        return {
            "message": "Invalid username"
        }, 401

    if not bcrypt.checkpw(
        password.encode('utf-8'),
        user['password']
    ):
        log_failed_login_attempt(username)
        return {
            "message": "Invalid password"
        }, 401

    # -----------------------------
    # DEVICE TRUST CHECK
    # -----------------------------
    device = find_device(device_id)
    is_known_device = device is not None

    # -----------------------------
    # GEOLOCATION & IMPOSSIBLE TRAVEL CHECKS
    # -----------------------------
    ip = data.get("mock_ip") or request.headers.get("X-Forwarded-For") or request.remote_addr
    geo = get_ip_geolocation(ip)
    
    current_lat = geo.get("lat")
    current_lon = geo.get("lon")
    current_city = geo.get("city")
    current_country = geo.get("country")

    # Fetch Login History
    login_history = get_user_logins(username)
    login_count = len(login_history)
    
    # Calculate Impossible Travel
    last_login = login_history[-1] if login_history else None
    impossible_travel, travel_speed, travel_distance = detect_impossible_travel(
        last_login,
        current_lat,
        current_lon,
        datetime.now()
    )

    # -----------------------------
    # AI BEHAVIOR MODEL (ISOLATION FOREST)
    # -----------------------------
    login_hour = float(datetime.now().hour)
    registered_country = user.get("registered_country") or current_country
    registered_device = user.get("registered_device") or device_id
    
    country_match = 1.0 if current_country == registered_country else 0.0
    is_known_device_val = 1.0 if is_known_device else 0.0
    
    ai_score = calculate_ai_anomaly_score(
        username,
        [login_hour, is_known_device_val, country_match, travel_speed],
        login_history,
        registered_country,
        registered_device
    )

    # -----------------------------
    # ANOMALY DETECTION (HYBRID)
    # -----------------------------
    anomaly_score = detect_anomaly(
        login_count=login_count,
        is_known_device=is_known_device,
        current_hour=datetime.now().hour,
        impossible_travel=impossible_travel,
        ai_score=ai_score
    )

    # -----------------------------
    # TRUST SCORE
    # -----------------------------
    trust_score = calculate_trust_score(
        is_known_device,
        login_count,
        anomaly_score
    )

    # -----------------------------
    # RISK LEVEL
    # -----------------------------
    if anomaly_score <= 20:
        risk_level = "Low"
    elif anomaly_score <= 50:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # -----------------------------
    # CHECK MFA REQUIREMENT
    # -----------------------------
    mfa_enabled = user.get("mfa_enabled", False)
    if mfa_enabled or risk_level == "High":
        otp_code = f"{random.randint(100000, 999999)}"
        log_msg = f"[MFA EMAIL] OTP generated for user: {username}"
        print(log_msg)
        logger.info(log_msg)

        from config import db
        
        # Save temp OTP & computed security context to avoid drift on validation
        db["users"].update_one(
            {"username": username},
            {"$set": {
                "temp_otp": otp_code,
                "otp_expiry": datetime.now() + timedelta(minutes=5),
                "temp_login_attempt": {
                    "ip": ip,
                    "city": current_city,
                    "country": current_country,
                    "latitude": current_lat,
                    "longitude": current_lon,
                    "anomaly_score": anomaly_score,
                    "trust_score": trust_score,
                    "risk_level": risk_level,
                    "impossible_travel": impossible_travel,
                    "ai_score": ai_score,
                    "is_known_device": is_known_device,
                    "travel_speed": travel_speed,
                    "travel_distance": travel_distance
                }
            }}
        )
        
        # Asynchronously transmit OTP code to user's registered email
        user_email = user.get("email")
        send_otp_email_async(user_email, username, otp_code)

        is_face_enabled = bool(user.get("face_enabled", False) and (user.get("face_registered", False) or user.get("faceRegistered", False)))
        return {
            "mfa_required": True,
            "username": username,
            "email": user_email,
            "face_enabled": is_face_enabled,
            "message": f"Verification code sent to registered email ({user_email})"
        }, 200


    # -----------------------------
    # AUTO TRUST NEW DEVICE
    # -----------------------------
    user_trust_devices = user.get("trust_devices", False)
    if not is_known_device:
        if user_trust_devices:
            register_device({
                "device_id": device_id,
                "username": username,
                "trust_level": "trusted"
            })
            is_known_device = True
        else:
            register_device({
                "device_id": device_id,
                "username": username,
                "trust_level": "new"
            })

    # -----------------------------
    # SAVE LOGIN HISTORY WITH GEOLOCATION
    # -----------------------------
    # Resolve IP & Location details dynamically
    ip_address, loc_details = get_request_client_geo(request)
    
    user_agent = request.headers.get("User-Agent", "")
    browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
    os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
    
    client_details = {
        "device": device_id,
        "browser": browser,
        "operating_system": os_name
    }
    
    from models.login_history import save_login_record
    save_login_record(
        user_id=username,
        email=user.get("email", ""),
        ip_address=ip_address,
        loc_details=loc_details,
        client_details=client_details,
        risk_level=risk_level,
        login_status="Successful",
        event_type="User Login",
        authentication_method="Password",
        anomaly_score=anomaly_score,
        trust_score=trust_score,
        impossible_travel=impossible_travel,
        ai_score=ai_score
    )

    # Update active user location and trust metrics
    update_user_location(username, ip, current_city, current_country, current_lat, current_lon)
    update_trust(username, trust_score, risk_level)

    # Re-fetch logins to reflect the latest login session count
    login_history = get_user_logins(username)
    login_count = len(login_history)

    # -----------------------------
    # DYNAMIC ALERTS
    # -----------------------------
    alerts = []

    # Unknown Device Alert
    if not is_known_device:
        alerts.append({
            "level": "High",
            "title": "Unknown Device Detected",
            "message": f"Login attempted from a new device: {device_id[:12]}..."
        })

    # Impossible Travel Alert
    if impossible_travel:
        alerts.append({
            "level": "High",
            "title": "Impossible Travel Detected",
            "message": f"Rapid physical movement flagged. Distance: {int(travel_distance)} km, Speed: {int(travel_speed)} km/h."
        })

    # Risk Alerts
    if risk_level == "High":
        alerts.append({
            "level": "High",
            "title": "High Risk Login",
            "message": "Zero Trust Engine flagged this login attempt as high risk."
        })
    elif risk_level == "Medium":
        alerts.append({
            "level": "Medium",
            "title": "Medium Risk Login",
            "message": "This session context should be continuously monitored."
        })
    else:
        alerts.append({
            "level": "Low",
            "title": "Trusted Login",
            "message": "Authentication completed successfully."
        })

    # High Login Count Alert
    if login_count >= 5:
        alerts.append({
            "level": "Medium",
            "title": "Frequent Login Activity",
            "message": f"{login_count} sessions have been logged for this user."
        })

    # Behavioral Anomaly Alert
    if ai_score >= 50:
        alerts.append({
            "level": "High",
            "title": "Behavioral Anomaly",
            "message": f"Login behavior deviates {ai_score}% from your established historical baseline."
        })

    # -----------------------------
    # JWT TOKEN
    # -----------------------------
    access_token = create_access_token(
        identity=username
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "trust_score": trust_score,
        "known_device": is_known_device,
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "alerts": alerts,
        "name": user.get("name"),
        "email": user.get("email"),
        "department": user.get("department"),
        "employee_id": user.get("employee_id"),
        "browser": user.get("browser"),
        "os": user.get("os"),
        "mfa_enabled": user.get("mfa_enabled", False),
        "trust_devices": user.get("trust_devices", False),
        "email_alerts": user.get("email_alerts", True),
        "dark_mode": user.get("dark_mode", False),
        "auto_logout": user.get("auto_logout", True)
    }, 200


# -----------------------------
# VERIFY OTP ROUTE
# -----------------------------
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    username = data.get("username")
    otp = data.get("otp")
    device_id = data.get("device_id")

    user = find_user(username)
    if not user:
        return {"message": "User not found"}, 404

    temp_otp = user.get("temp_otp")
    otp_expiry = user.get("otp_expiry")

    if not temp_otp or temp_otp != otp:
        return {"message": "Invalid OTP code"}, 401

    if not otp_expiry or datetime.now() > otp_expiry:
        return {"message": "OTP code has expired"}, 401

    # Clear OTP
    from config import db
    db["users"].update_one(
        {"username": username},
        {"$unset": {"temp_otp": "", "otp_expiry": ""}}
    )

    # Complete normal login flow after successful MFA
    device = find_device(device_id)
    is_known_device = device is not None
    user_trust_devices = user.get("trust_devices", False)

    if not is_known_device:
        if user_trust_devices:
            register_device({
                "device_id": device_id,
                "username": username,
                "trust_level": "trusted"
            })
            is_known_device = True
        else:
            register_device({
                "device_id": device_id,
                "username": username,
                "trust_level": "new"
            })

    temp_attempt = user.get("temp_login_attempt")
    if temp_attempt:
        ip = temp_attempt.get("ip")
        city = temp_attempt.get("city")
        country = temp_attempt.get("country")
        latitude = temp_attempt.get("latitude")
        longitude = temp_attempt.get("longitude")
        anomaly_score = temp_attempt.get("anomaly_score")
        trust_score = temp_attempt.get("trust_score")
        risk_level = temp_attempt.get("risk_level")
        impossible_travel = temp_attempt.get("impossible_travel")
        ai_score = temp_attempt.get("ai_score")
        travel_speed = temp_attempt.get("travel_speed", 0.0)
        travel_distance = temp_attempt.get("travel_distance", 0.0)
    else:
        ip = request.remote_addr
        geo = get_ip_geolocation(ip)
        city = geo.get("city")
        country = geo.get("country")
        latitude = geo.get("lat")
        longitude = geo.get("lon")
        
        login_history = get_user_logins(username)
        anomaly_score = detect_anomaly(len(login_history), is_known_device)
        trust_score = calculate_trust_score(is_known_device, len(login_history), anomaly_score)
        risk_level = "High" if anomaly_score >= 80 else "Medium" if anomaly_score >= 50 else "Low"
        impossible_travel = False
        ai_score = 0
        travel_speed = 0.0
        travel_distance = 0.0

    # Resolve IP & Location details dynamically
    ip_address, loc_details = get_request_client_geo(request)
    
    user_agent = request.headers.get("User-Agent", "")
    browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
    os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
    
    client_details = {
        "device": device_id,
        "browser": browser,
        "operating_system": os_name
    }
    
    from models.login_history import save_login_record
    save_login_record(
        user_id=username,
        email=user.get("email", ""),
        ip_address=ip_address,
        loc_details=loc_details,
        client_details=client_details,
        risk_level=risk_level,
        login_status="Successful",
        event_type="OTP Verification",
        authentication_method="OTP",
        anomaly_score=anomaly_score,
        trust_score=trust_score,
        impossible_travel=impossible_travel,
        ai_score=ai_score
    )

    update_user_location(username, ip, city, country, latitude, longitude)
    update_trust(username, trust_score, risk_level)

    # Clean up temp_login_attempt
    db["users"].update_one(
        {"username": username},
        {"$unset": {"temp_login_attempt": ""}}
    )

    login_history = get_user_logins(username)
    login_count = len(login_history)

    alerts = []
    if not is_known_device:
        alerts.append({
            "level": "High",
            "title": "Unknown Device Detected",
            "message": f"Login attempted from a new device: {device_id[:12]}..."
        })
    if impossible_travel:
        alerts.append({
            "level": "High",
            "title": "Impossible Travel Detected",
            "message": f"Rapid physical movement flagged. Distance: {int(travel_distance)} km, Speed: {int(travel_speed)} km/h."
        })
    if risk_level == "High":
        alerts.append({
            "level": "High",
            "title": "High Risk Login",
            "message": "Zero Trust Engine flagged this login attempt as high risk."
        })
    elif risk_level == "Medium":
        alerts.append({
            "level": "Medium",
            "title": "Medium Risk Login",
            "message": "This session context should be continuously monitored."
        })
    else:
        alerts.append({
            "level": "Low",
            "title": "Trusted Login",
            "message": "Authentication completed successfully."
        })

    if login_count >= 5:
        alerts.append({
            "level": "Medium",
            "title": "Frequent Login Activity",
            "message": f"{login_count} sessions have been logged for this user."
        })

    if ai_score >= 50:
        alerts.append({
            "level": "High",
            "title": "Behavioral Anomaly",
            "message": f"Login behavior deviates {ai_score}% from your established historical baseline."
        })

    access_token = create_access_token(
        identity=username
    )

    is_face_enabled = bool(user.get("face_enabled", False))
    is_face_registered = bool(user.get("face_registered", False) or user.get("faceRegistered", False))
    face_required = is_face_enabled and is_face_registered

    if face_required:
        return {
            "message": "OTP Verified. Face verification required.",
            "face_required": True,
            "username": username,
            "email": user.get("email"),
            "pre_auth_token": access_token
        }, 200

    return {
        "message": "Login successful",
        "access_token": access_token,
        "face_required": False,
        "trust_score": trust_score,
        "known_device": is_known_device,
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "alerts": alerts,
        "name": user.get("name"),
        "email": user.get("email"),
        "department": user.get("department"),
        "employee_id": user.get("employee_id"),
        "browser": user.get("browser"),
        "os": user.get("os"),
        "mfa_enabled": user.get("mfa_enabled", False),
        "trust_devices": user.get("trust_devices", False),
        "email_alerts": user.get("email_alerts", True),
        "dark_mode": user.get("dark_mode", False),
        "auto_logout": user.get("auto_logout", True)
    }, 200


# -----------------------------
# SECURITY RE-AUTHENTICATION ROUTE
# -----------------------------
@auth_bp.route('/api/auth/reauthenticate', methods=['POST'])
@jwt_required()
def reauthenticate_user():
    """
    Validates user password before granting a biometric registration token.
    """
    current_user = get_jwt_identity()
    data = request.json or {}
    password = data.get("password")

    user = find_user(current_user)
    if not user:
        return {"success": False, "message": "User not found"}, 404

    if not password or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return {"success": False, "message": "Invalid password. Re-authentication failed."}, 401

    import secrets
    reauth_token = f"reauth_{secrets.token_urlsafe(24)}"
    expiry = datetime.now() + timedelta(minutes=5)

    from config import db
    db["users"].update_one(
        {"username": current_user},
        {"$set": {
            "biometric_reauth_token": reauth_token,
            "biometric_reauth_expiry": expiry
        }}
    )

    return {
        "success": True,
        "reauth_token": reauth_token,
        "username": current_user,
        "message": "Security re-authentication successful. Biometric registration authorized for 5 minutes."
    }, 200



# -----------------------------
# RESEND OTP ROUTE
# -----------------------------
@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.json
    username = data.get("username")

    if not username:
        return {"message": "Username is required"}, 400

    user = find_user(username)
    if not user:
        return {"message": "User not found"}, 404

    otp_code = f"{random.randint(100000, 999999)}"
    log_msg = f"[MFA EMAIL] OTP generated for user: {username}"
    print(log_msg)
    logger.info(log_msg)

    from config import db
    db["users"].update_one(
        {"username": username},
        {"$set": {
            "temp_otp": otp_code,
            "otp_expiry": datetime.now() + timedelta(minutes=5)
        }}
    )
    
    # Asynchronously transmit OTP code to user's registered email
    user_email = user.get("email")
    send_otp_email_async(user_email, username, otp_code)

    return {
        "message": f"A new verification code has been sent to your email ({user_email})",
        "username": username,
        "email": user_email
    }, 200



# -----------------------------
# UPDATE SETTINGS ROUTE
# -----------------------------
@auth_bp.route('/update-settings', methods=['POST'])
def update_user_settings():
    data = request.json
    username = data.get("username")

    update_settings(username, data)

    return {
        "message": "Settings updated successfully"
    }, 200



# -----------------------------
# LOGIN HISTORY ROUTE
# -----------------------------
@auth_bp.route('/login-history/<username>', methods=['GET'])
def login_history(username):

    history = get_user_logins(username)

    result = []

    for item in history:

        result.append({

            "device_id": item.get("device_id"),

            "timestamp": str(item.get("timestamp"))

        })

    return {

        "history": result

    }, 200


# -----------------------------
# VERIFY SESSION (CONTINUOUS AUTHENTICATION)
# -----------------------------
@auth_bp.route('/verify-session', methods=['POST'])
@jwt_required()
def verify_session():
    username = get_jwt_identity()
    user = find_user(username)
    if not user:
        return {"message": "User not found"}, 404
        
    data = request.json
    device_id = data.get("device_id")
    ip = data.get("mock_ip") or request.headers.get("X-Forwarded-For") or request.remote_addr
    
    geo = get_ip_geolocation(ip)
    
    # Calculate distance from last known user location
    last_latitude = user.get("last_latitude")
    last_longitude = user.get("last_longitude")
    
    impossible_travel = False
    travel_distance = 0.0
    if last_latitude is not None and last_longitude is not None:
        travel_distance = calculate_distance(last_latitude, last_longitude, geo.get("lat"), geo.get("lon"))
        # If location changed dramatically (e.g. > 1000 km) during session verification
        if travel_distance > 1000.0:
            impossible_travel = True
            
    is_known_device = (device_id == user.get("registered_device"))
    
    login_history = get_user_logins(username)
    
    # AI calculation for session threat index
    current_hour = datetime.now().hour
    country_match = 1.0 if geo.get("country") == user.get("registered_country") else 0.0
    
    # Simulate a speed if travel is impossible
    speed = 1500.0 if impossible_travel else 0.0
    
    ai_score = calculate_ai_anomaly_score(
        username,
        [current_hour, 1.0 if is_known_device else 0.0, country_match, speed],
        login_history,
        user.get("registered_country") or geo.get("country"),
        user.get("registered_device")
    )
    
    anomaly_score = detect_anomaly(
        login_count=len(login_history),
        is_known_device=is_known_device,
        current_hour=current_hour,
        impossible_travel=impossible_travel,
        ai_score=ai_score
    )
    
    trust_score = calculate_trust_score(
        is_known_device,
        len(login_history),
        anomaly_score
    )
    
    # Update trust metrics in user model
    risk_level = "High" if anomaly_score >= 80 else "Medium" if anomaly_score >= 50 else "Low"
    update_trust(username, trust_score, risk_level)
    
    if trust_score < 20 or anomaly_score >= 80:
        return {
            "session_valid": False,
            "message": "Security context compromised. Session terminated.",
            "trust_score": trust_score,
            "anomaly_score": anomaly_score,
            "risk_level": "High"
        }, 401
        
    return {
        "session_valid": True,
        "trust_score": trust_score,
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "message": "Session trust verified successfully."
    }, 200


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    try:
        data = request.json or {}
        username = data.get("username")
        if username:
            # Resolve IP & Location details dynamically
            ip_address, loc_details = get_request_client_geo(request)
            
            user_agent = request.headers.get("User-Agent", "")
            browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
            os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
            
            client_details = {
                "device": data.get("device_id") or "Unknown Device",
                "browser": browser,
                "operating_system": os_name
            }
            
            # Log on-chain
            user = find_user(username) or {}
            from models.login_history import save_login_record
            save_login_record(
                user_id=username,
                email=user.get("email", ""),
                ip_address=ip_address,
                loc_details=loc_details,
                client_details=client_details,
                risk_level="Low",
                login_status="Successful",
                event_type="Logout",
                authentication_method="None"
            )
            return {"success": True, "message": "Logout recorded on-chain"}, 200
        return {"message": "Username is required"}, 400
    except Exception as e:
        return {"message": str(e)}, 500


@auth_bp.route('/api/change-password', methods=['POST'])
def change_password():
    try:
        data = request.json or {}
        username = data.get("username")
        new_password = data.get("new_password")
        
        if not username or not new_password:
            return {"message": "Username and new password are required"}, 400
            
        user = find_user(username)
        if not user:
            return {"message": "User not found"}, 404
            
        # Hash new password
        import bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        from config import db
        db["users"].update_one(
            {"username": username},
            {"$set": {"password": hashed_password}}
        )
        
        # Resolve IP & Location details dynamically
        ip_address, loc_details = get_request_client_geo(request)
        
        user_agent = request.headers.get("User-Agent", "")
        browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
        os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
        
        client_details = {
            "device": data.get("device_id") or "Unknown Device",
            "browser": browser,
            "operating_system": os_name
        }
        
        # Log on-chain
        from models.login_history import save_login_record
        save_login_record(
            user_id=username,
            email=user.get("email", ""),
            ip_address=ip_address,
            loc_details=loc_details,
            client_details=client_details,
            risk_level="Low",
            login_status="Successful",
            event_type="Password Change",
            authentication_method="Password"
        )
        return {"success": True, "message": "Password updated and event logged on-chain"}, 200
    except Exception as e:
        return {"message": str(e)}, 500


@auth_bp.route('/api/lock-user', methods=['POST'])
def lock_user():
    try:
        data = request.json or {}
        username = data.get("username")
        
        if not username:
            return {"message": "Username is required"}, 400
            
        user = find_user(username)
        if not user:
            return {"message": "User not found"}, 404
            
        from config import db
        db["users"].update_one(
            {"username": username},
            {"$set": {"locked": True}}
        )
        
        # Resolve IP & Location details dynamically
        ip_address, loc_details = get_request_client_geo(request)
        
        user_agent = request.headers.get("User-Agent", "")
        browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
        os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
        
        client_details = {
            "device": data.get("device_id") or "Unknown Device",
            "browser": browser,
            "operating_system": os_name
        }
        
        # Log on-chain
        from models.login_history import save_login_record
        save_login_record(
            user_id=username,
            email=user.get("email", ""),
            ip_address=ip_address,
            loc_details=loc_details,
            client_details=client_details,
            risk_level="High",
            login_status="Successful",
            event_type="Account Locked",
            authentication_method="None"
        )
        return {"success": True, "message": "Account locked and logged on-chain"}, 200
    except Exception as e:
        return {"message": str(e)}, 500


@auth_bp.route('/api/unlock-user', methods=['POST'])
def unlock_user():
    try:
        data = request.json or {}
        username = data.get("username")
        
        if not username:
            return {"message": "Username is required"}, 400
            
        user = find_user(username)
        if not user:
            return {"message": "User not found"}, 404
            
        from config import db
        db["users"].update_one(
            {"username": username},
            {"$set": {"locked": False}}
        )
        
        # Resolve IP & Location details dynamically
        ip_address, loc_details = get_request_client_geo(request)
        
        user_agent = request.headers.get("User-Agent", "")
        browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
        os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
        
        client_details = {
            "device": data.get("device_id") or "Unknown Device",
            "browser": browser,
            "operating_system": os_name
        }
        
        # Log on-chain
        from models.login_history import save_login_record
        save_login_record(
            user_id=username,
            email=user.get("email", ""),
            ip_address=ip_address,
            loc_details=loc_details,
            client_details=client_details,
            risk_level="Low",
            login_status="Successful",
            event_type="Account Unlocked",
            authentication_method="None"
        )
        return {"success": True, "message": "Account unlocked and logged on-chain"}, 200
    except Exception as e:
        return {"message": str(e)}, 500
