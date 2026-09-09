import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from service.face_recognition_engine import FaceRecognitionEngine
from service.email_service import send_face_security_alert_async
from models.face_model import (
    save_face_profile,
    get_face_profile,
    delete_face_profile,
    save_face_auth_log,
    get_face_auth_logs,
)
from models.user_model import (
    find_user,
    update_face_status,
    update_face_last_verified,
    record_face_failed_attempt,
    reset_face_failed_attempts,
    update_trust,
)
from config import users_collection, db, FACE_MAX_FAILED_ATTEMPTS, FACE_LOCKOUT_MINUTES

logger = logging.getLogger("face_auth")
logger.setLevel(logging.INFO)

# Initialize Flask Blueprint for Face Recognition Authentication
face_auth_bp = Blueprint("face_auth", __name__)

# Instantiate global FaceRecognitionEngine singleton with standard tolerance (distance_threshold=0.58)
face_engine = FaceRecognitionEngine(distance_threshold=0.58, min_confidence=70.0)


def log_blockchain_biometric_event(username, is_success, event_type, auth_method):
    try:
        from models.login_history import save_login_record
        from utils.geo_helper import get_request_client_geo

        ip_address, loc_details = get_request_client_geo(request)
        user_agent = request.headers.get("User-Agent", "")
        browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
        os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"

        req_json = {}
        try:
            req_json = request.get_json(silent=True) or {}
        except Exception:
            pass

        client_details = {
            "device": req_json.get("device_id") or "Unknown Device",
            "browser": browser,
            "operating_system": os_name
        }

        user = find_user(username) or {}
        save_login_record(
            user_id=username,
            email=user.get("email", ""),
            ip_address=ip_address,
            loc_details=loc_details,
            client_details=client_details,
            risk_level="Low" if is_success else "High",
            login_status="Successful" if is_success else "Failed",
            event_type=event_type,
            authentication_method=auth_method
        )
    except Exception as e:
        logger.warning(f"Error logging biometric event to blockchain: {e}")


# -------------------------------------------------------------
# 1. POST /register (and /api/face/register)
# SECURE BIOMETRIC REGISTRATION - ACCESSIBLE ONLY FROM SETTINGS WORKFLOW
# -------------------------------------------------------------
@face_auth_bp.route("/register", methods=["POST"])
@face_auth_bp.route("/api/face/register", methods=["POST"])
@jwt_required()
def register_face():
    """
    POST /api/face/register
    Requires: JWT Authentication + Active Re-Authentication Security Token.
    Identity ISOLATION: Target user is derived strictly from server-side JWT identity (get_jwt_identity()).
    """
    try:
        authenticated_user = get_jwt_identity()
        if not authenticated_user:
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Authentication required for biometric registration."
            }), 401

        data = request.get_json(silent=True) or {}
        reauth_token = data.get("reauth_token") or request.headers.get("X-Biometric-Reauth-Token")

        user = find_user(authenticated_user)
        if not user:
            return jsonify({
                "success": False,
                "error": "USER_NOT_FOUND",
                "message": "Authenticated user profile not found."
            }), 404

        # Validate security re-authentication authorization
        stored_reauth_token = user.get("biometric_reauth_token")
        reauth_expiry = user.get("biometric_reauth_expiry")

        has_valid_reauth = False
        if reauth_token and stored_reauth_token and reauth_token == stored_reauth_token:
            if reauth_expiry and datetime.now() <= reauth_expiry:
                has_valid_reauth = True

        if not has_valid_reauth:
            save_face_auth_log(
                username=authenticated_user,
                is_match=False,
                confidence_score=0.0,
                status_code="UNAUTHORIZED_REGISTRATION_ATTEMPT",
                details={"message": "Biometric registration attempt blocked due to missing or expired re-authentication context."}
            )
            return jsonify({
                "success": False,
                "error": "REAUTHENTICATION_REQUIRED",
                "message": "Biometric registration requires active security-settings re-authentication. Please initiate registration from Settings."
            }), 403

        image_sources = data.get("frames") or data.get("image") or "WEBCAM"
        result = face_engine.process_registration(image_sources=image_sources, user_id=authenticated_user)

        if not result.get("success"):
            save_face_auth_log(
                username=authenticated_user,
                is_match=False,
                confidence_score=0.0,
                status_code=result.get("error", "REGISTRATION_FAILED"),
                details={"message": result.get("message")}
            )
            return jsonify(result), 400

        # Store authorized face profile embedding
        save_face_profile(
            username=authenticated_user,
            face_encoding=result["encoding"],
            metadata={"source_frames": result.get("frames_processed", 1)}
        )

        # Update database state fields: face_enabled = True, face_registered = True
        update_face_status(authenticated_user, enabled=True, registered=True)

        # Consume single-use re-authentication token
        db["users"].update_one(
            {"username": authenticated_user},
            {"$unset": {"biometric_reauth_token": "", "biometric_reauth_expiry": ""}}
        )

        save_face_auth_log(
            username=authenticated_user,
            is_match=True,
            confidence_score=100.0,
            status_code="FACE_REGISTERED",
            details={"message": "Authorized face profile successfully registered from Security Settings."}
        )

        log_blockchain_biometric_event(authenticated_user, True, "FACE_REGISTERED", "Facial Biometrics")

        return jsonify({
            "success": True,
            "username": authenticated_user,
            "face_count": 1,
            "face_enabled": True,
            "face_registered": True,
            "faceRegistered": True,
            "frames_processed": result.get("frames_processed", 1),
            "message": f"Face Recognition Enabled Successfully! Biometric profile stored for user '{authenticated_user}'."
        }), 200

    except Exception as e:
        logger.exception(f"[FACE AUTH ROUTE] Exception during face registration: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": f"An unexpected server error occurred during registration: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 2. POST /verify (and /login, /api/face/verify, /api/face/login)
# FACE AUTHENTICATION / VERIFICATION ONLY - NEVER CREATES A PROFILE
# -------------------------------------------------------------
@face_auth_bp.route("/verify", methods=["POST"])
@face_auth_bp.route("/login", methods=["POST"])
@face_auth_bp.route("/api/face/verify", methods=["POST"])
@face_auth_bp.route("/api/face/login", methods=["POST"])
def verify_face():
    """
    POST /api/face/verify
    Compares submitted face against existing registered profile.
    NEVER creates a new face profile.
    """
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username") or data.get("user_id")

        try:
            jwt_user = get_jwt_identity()
            if jwt_user:
                username = jwt_user
        except Exception:
            pass

        if not username or username == "anonymous_user":
            return jsonify({
                "success": False,
                "is_match": False,
                "confidence_score": 0.0,
                "distance": 1.0,
                "error": "MISSING_USERNAME",
                "message": "Username is required for face verification."
            }), 400

        user_record = find_user(username) or {}
        is_face_enabled = bool(user_record.get("face_enabled", False))
        is_face_registered = bool(user_record.get("face_registered", False) or user_record.get("faceRegistered", False))

        profile = get_face_profile(username)
        if not is_face_enabled or not is_face_registered or not profile or not profile.get("face_encoding"):
            save_face_auth_log(
                username=username,
                is_match=False,
                confidence_score=0.0,
                status_code="FACE_AUTH_NOT_CONFIGURED",
                details={"message": "Face authentication requested but not enabled/registered."}
            )
            return jsonify({
                "success": False,
                "is_match": False,
                "confidence_score": 0.0,
                "distance": 1.0,
                "threshold": face_engine.distance_threshold,
                "error": "FACE_AUTH_NOT_CONFIGURED",
                "message": "Face authentication is not configured for this account. Please enable it from Security Settings."
            }), 404

        # Rate Limiting & Lockout Check
        lock_until = user_record.get("face_locked_until")
        if lock_until:
            try:
                lock_dt = datetime.fromisoformat(lock_until)
                if datetime.utcnow() < lock_dt:
                    rem_sec = int((lock_dt - datetime.utcnow()).total_seconds())
                    return jsonify({
                        "success": False,
                        "is_match": False,
                        "error": "FACE_AUTHENTICATION_LOCKED",
                        "message": f"Face authentication temporarily restricted due to multiple failed attempts. Try again in {rem_sec} seconds."
                    }), 429
            except Exception:
                pass

        stored_encoding = profile["face_encoding"]
        image_sources = data.get("frames") or data.get("image") or "WEBCAM"

        result = face_engine.process_login_verification(
            image_sources=image_sources,
            user_id=username,
            stored_encoding=stored_encoding
        )

        confidence = result.get("confidence_score", 0.0)
        distance = result.get("distance", 1.0)
        is_match = bool(result.get("is_match", False))

        if not result.get("success") or not is_match:
            # Verification Failed
            failed_count, is_locked, lock_time_iso = record_face_failed_attempt(
                username,
                max_attempts=FACE_MAX_FAILED_ATTEMPTS,
                lockout_minutes=FACE_LOCKOUT_MINUTES
            )

            status_code = result.get("error", "FACE_VERIFICATION_FAILED")
            save_face_auth_log(
                username=username,
                is_match=False,
                confidence_score=confidence,
                status_code=status_code,
                details={
                    "message": result.get("message"),
                    "distance": distance,
                    "failed_attempts": failed_count,
                    "locked_out": is_locked
                }
            )

            log_blockchain_biometric_event(username, False, "FACE_VERIFICATION_FAILED", "Facial Biometrics")

            # Lower trust score on verification failure
            curr_trust = user_record.get("trust_score", 100)
            new_trust = max(0, curr_trust - 30)
            update_trust(username, new_trust, "High")

            # Trigger Security Email Alert
            from utils.geo_helper import get_request_client_geo
            ip_addr, loc_det = get_request_client_geo(request)
            event_details = {
                "ip_address": ip_addr,
                "location": f"{loc_det.get('city', 'Unknown')}, {loc_det.get('country', 'Unknown')}",
                "device": request.headers.get("User-Agent", "Unknown Device"),
                "risk_level": "High",
                "reason": result.get("message") or "Face biometric mismatch",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            send_face_security_alert_async(user_record.get("email"), username, event_details)

            response_payload = {
                "success": False,
                "is_match": False,
                "confidence_score": confidence,
                "distance": distance,
                "threshold": face_engine.distance_threshold,
                "failed_attempts": failed_count,
                "locked": is_locked,
                "error": status_code,
                "message": result.get("message") or "Face verification failed. Access denied."
            }
            return jsonify(response_payload), 401

        # Verification Succeeded
        reset_face_failed_attempts(username)
        update_face_last_verified(username)

        # Bolster trust score
        update_trust(username, 100, "Low")

        save_face_auth_log(
            username=username,
            is_match=True,
            confidence_score=confidence,
            status_code="FACE_VERIFICATION_SUCCESS",
            details={
                "message": "Facial verification succeeded.",
                "distance": distance,
                "confidence": confidence
            }
        )

        log_blockchain_biometric_event(username, True, "FACE_VERIFICATION_SUCCESS", "Facial Biometrics")

        access_token = create_access_token(identity=username)
        response_payload = {
            "success": True,
            "is_match": True,
            "confidence_score": confidence,
            "distance": distance,
            "threshold": face_engine.distance_threshold,
            "access_token": access_token,
            "faceVerified": True,
            "authenticated": True,
            "user": {
                "username": username,
                "name": user_record.get("name", username),
                "email": user_record.get("email"),
                "trust_score": 100,
                "risk_level": "Low",
                "mfa_enabled": user_record.get("mfa_enabled", True),
                "face_enabled": True,
                "face_registered": True
            },
            "message": f"Authentication Successful! Face verified with {confidence}% confidence. Redirecting..."
        }
        return jsonify(response_payload), 200

    except Exception as e:
        logger.exception(f"[FACE AUTH ROUTE] Exception during face verification: {str(e)}")
        return jsonify({
            "success": False,
            "is_match": False,
            "confidence_score": 0.0,
            "distance": 1.0,
            "error": "SERVER_ERROR",
            "message": f"An unexpected server error occurred during face verification: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 3. POST /disable (and /api/face/disable)
# DISABLE FACE RECOGNITION FROM SETTINGS WORKFLOW
# -------------------------------------------------------------
@face_auth_bp.route("/disable", methods=["POST"])
@face_auth_bp.route("/api/face/disable", methods=["POST"])
@jwt_required()
def disable_face():
    try:
        username = get_jwt_identity()
        update_face_status(username, enabled=False, registered=True)
        save_face_auth_log(
            username=username,
            is_match=True,
            confidence_score=100.0,
            status_code="FACE_DISABLED",
            details={"message": "Face authentication disabled by user."}
        )
        log_blockchain_biometric_event(username, True, "FACE_DISABLED", "Facial Biometrics")
        return jsonify({
            "success": True,
            "username": username,
            "face_enabled": False,
            "message": "Face authentication has been disabled."
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": "SERVER_ERROR", "message": str(e)}), 500


# -------------------------------------------------------------
# 4. GET /status/<username> (and /api/face/status/<username>)
# -------------------------------------------------------------
@face_auth_bp.route("/status/<username>", methods=["GET"])
@face_auth_bp.route("/api/face/status/<username>", methods=["GET"])
def get_face_status(username):
    try:
        user_record = find_user(username) or {}
        profile = get_face_profile(username)

        is_registered = bool(user_record.get("face_registered", False) or user_record.get("faceRegistered", False) or (profile and profile.get("face_encoding")))
        is_enabled = bool(user_record.get("face_enabled", False)) if is_registered else False

        return jsonify({
            "success": True,
            "registered": is_registered,
            "face_registered": is_registered,
            "faceRegistered": is_registered,
            "face_enabled": is_enabled,
            "username": username,
            "registered_at": user_record.get("face_registered_at"),
            "last_verified_at": user_record.get("face_last_verified_at"),
            "failed_attempts": user_record.get("face_failed_attempts", 0),
            "locked_until": user_record.get("face_locked_until"),
            "message": f"Face status for '{username}': enabled={is_enabled}, registered={is_registered}"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


# -------------------------------------------------------------
# 5. GET /logs/<username> (and /api/face/logs/<username>)
# -------------------------------------------------------------
@face_auth_bp.route("/logs/<username>", methods=["GET"])
@face_auth_bp.route("/api/face/logs/<username>", methods=["GET"])
def get_user_face_logs(username):
    try:
        logs = get_face_auth_logs(username)
        return jsonify({
            "success": True,
            "username": username,
            "count": len(logs),
            "logs": logs
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


# -------------------------------------------------------------
# 6. POST /tolerance (and /api/face/tolerance)
# -------------------------------------------------------------
@face_auth_bp.route("/tolerance", methods=["POST"])
@face_auth_bp.route("/api/face/tolerance", methods=["POST"])
def set_face_tolerance():
    try:
        data = request.get_json(silent=True) or {}
        new_tol = data.get("tolerance") or data.get("threshold") or 0.58
        face_engine.set_tolerance(new_tol)
        return jsonify({
            "success": True,
            "tolerance": face_engine.distance_threshold,
            "message": f"Face distance tolerance updated to {face_engine.distance_threshold}."
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

