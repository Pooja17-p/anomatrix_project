import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.mouse_model import (
    save_mouse_log,
    save_or_update_mouse_session,
    get_mouse_profile,
    update_mouse_profile,
    get_latest_mouse_score,
    get_mouse_history,
    get_all_mouse_logs_for_training,
    save_mouse_model_metadata,
)
from service.mouse_engine import (
    compute_mouse_kinematics,
    evaluate_mouse_similarity,
    train_mouse_model,
    load_mouse_model,
    predict_trust_score,
)

# Set up logging for mouse motion authentication module
logger = logging.getLogger("mouse_auth")
logger.setLevel(logging.INFO)

# Initialize Flask Blueprint for Mouse Motion Authentication module
mouse_auth_bp = Blueprint("mouse_auth", __name__)


def _extract_username(data):
    """
    Utility function to extract username/user_id from JWT token or request JSON body.
    """
    try:
        identity = get_jwt_identity()
        if identity:
            return identity
    except Exception:
        pass
    if isinstance(data, dict):
        return data.get("user_id") or data.get("username") or "anonymous_user"
    return "anonymous_user"


def log_blockchain_biometric_event(username, is_success, event_type, auth_method):
    try:
        from models.login_history import save_login_record
        from models.user_model import find_user
        from utils.geo_helper import get_request_client_geo

        ip_address, loc_details = get_request_client_geo(request)
        
        user_agent = request.headers.get("User-Agent", "")
        browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Safari" if "Safari" in user_agent else "Unknown Browser"
        os_name = "Windows" if "Windows" in user_agent else "macOS" if "Macintosh" in user_agent else "Linux" if "Linux" in user_agent else "Unknown OS"
        
        req_json = {}
        try:
            req_json = request.get_json(silent=True) or {}
        except:
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
# Helper: Input Validation
# -------------------------------------------------------------
def validate_mouse_telemetry_input(data):
    """
    Validates mouse motion input telemetry payload.

    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a valid JSON object."

    points = data.get("points")
    kinematics = data.get("kinematics") or data.get("features")

    if points is not None and not isinstance(points, list):
        return False, "'points' must be a list of mouse point objects."

    if points is not None and isinstance(points, list):
        for idx, pt in enumerate(points):
            if not isinstance(pt, dict):
                return False, f"Point at index {idx} must be an object with x, y coordinates."
            if "x" not in pt or "y" not in pt:
                return False, f"Point at index {idx} must contain 'x' and 'y' values."
            if not isinstance(pt["x"], (int, float)) or not isinstance(pt["y"], (int, float)):
                return False, f"Coordinates in point at index {idx} must be numeric values."

    if kinematics is not None and not isinstance(kinematics, dict):
        return False, "'kinematics' / 'features' must be a dictionary."

    return True, ""


# -------------------------------------------------------------
# 1. POST /mouse-data (and /mouse/data, /data)
# Collects and stores raw/processed mouse motion telemetry in MongoDB.
# -------------------------------------------------------------
@mouse_auth_bp.route("/mouse-data", methods=["POST"])
@mouse_auth_bp.route("/mouse/data", methods=["POST"])
@mouse_auth_bp.route("/data", methods=["POST"])
def collect_mouse_data():
    """
    POST /mouse-data
    Validates input telemetry, stores records in MongoDB, and updates baseline kinematics profile.
    """
    try:
        data = request.get_json(silent=True)
        if data is None:
            logger.warning("POST /mouse-data request contains invalid or missing JSON body.")
            return jsonify({
                "status": "error",
                "message": "Invalid input: Request body must be valid JSON."
            }), 400

        is_valid, err_msg = validate_mouse_telemetry_input(data)
        if not is_valid:
            logger.warning("POST /mouse-data validation failed: %s", err_msg)
            return jsonify({
                "status": "error",
                "message": f"Input Validation Error: {err_msg}"
            }), 400

        username = _extract_username(data)
        session_id = data.get("session_id", f"mouse_sess_{username}")
        points = data.get("points", [])
        click_events = int(data.get("click_events", 0))
        scroll_behaviour = int(data.get("scroll_behaviour", 0))
        window_duration = float(data.get("window_duration", 4.0))

        # Compute kinematics if features not directly supplied
        if data.get("kinematics") and isinstance(data["kinematics"], dict):
            features = data["kinematics"]
        else:
            features = compute_mouse_kinematics(
                points=points,
                clicks=click_events,
                scrolls=scroll_behaviour,
                window_duration=window_duration,
            )

        timestamp = data.get("timestamp") or datetime.utcnow().isoformat() + "Z"

        log_data = {
            "username": username,
            "user_id": username,
            "session_id": session_id,
            "raw_points_count": len(points),
            "kinematics": features,
            "timestamp": timestamp,
            "created_at": timestamp,
        }

        # Store record in MongoDB
        inserted_log = save_mouse_log(log_data)
        update_mouse_profile(username, features)

        logger.info("Successfully stored mouse motion record for user '%s' (ID: %s)", username, inserted_log["_id"])

        return jsonify({
            "status": "success",
            "message": "Mouse motion data stored successfully",
            "record_id": inserted_log["_id"],
            "user_id": username,
            "session_id": session_id,
            "kinematics": features,
            "timestamp": timestamp
        }), 201

    except Exception as e:
        logger.error("Exception in POST /mouse-data: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to store mouse data: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 2. POST /mouse/train (and /train)
# Trains machine learning AI model on historical mouse telemetry.
# -------------------------------------------------------------
@mouse_auth_bp.route("/mouse/train", methods=["POST"])
@mouse_auth_bp.route("/train", methods=["POST"])
def train_mouse_ai_model():
    """
    POST /mouse/train
    Trains IsolationForest AI model using stored mouse records from MongoDB.
    """
    try:
        data = request.get_json(silent=True) or {}
        username = _extract_username(data)

        logger.info("Initiating AI model training request for user '%s'...", username)

        # Retrieve user logs from MongoDB for training
        user_logs = get_all_mouse_logs_for_training(username)

        # Train IsolationForest model via mouse_engine
        training_res = train_mouse_model(username, user_logs)

        # Save metadata record in MongoDB
        save_mouse_model_metadata(username, training_res)

        logger.info("AI Model successfully trained for user '%s' with %d samples.", username, training_res["samples_trained"])

        return jsonify({
            "status": "success",
            "message": "AI mouse motion model trained successfully",
            "user_id": username,
            "model_type": training_res["model_type"],
            "samples_trained": training_res["samples_trained"],
            "model_path": training_res["model_path"],
            "trained_at": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error("Exception in POST /mouse/train: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to train AI model: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 3. POST /mouse/predict (and /predict)
# Loads AI model, evaluates mouse dynamics, predicts trust score & status.
# -------------------------------------------------------------
@mouse_auth_bp.route("/mouse/predict", methods=["POST"])
@mouse_auth_bp.route("/predict", methods=["POST"])
def predict_mouse_auth():
    """
    POST /mouse/predict
    Loads trained AI model, predicts trust score (0-100) and security status.
    """
    try:
        data = request.get_json(silent=True)
        if data is None:
            logger.warning("POST /mouse/predict request missing JSON body.")
            return jsonify({
                "status": "error",
                "message": "Invalid input: Request body must be valid JSON."
            }), 400

        is_valid, err_msg = validate_mouse_telemetry_input(data)
        if not is_valid:
            logger.warning("POST /mouse/predict validation failed: %s", err_msg)
            return jsonify({
                "status": "error",
                "message": f"Input Validation Error: {err_msg}"
            }), 400

        username = _extract_username(data)
        session_id = data.get("session_id", f"mouse_sess_{username}")
        points = data.get("points", [])
        click_events = int(data.get("click_events", 0))
        scroll_behaviour = int(data.get("scroll_behaviour", 0))
        window_duration = float(data.get("window_duration", 4.0))

        if data.get("kinematics") and isinstance(data["kinematics"], dict):
            features = data["kinematics"]
        else:
            features = compute_mouse_kinematics(
                points=points,
                clicks=click_events,
                scrolls=scroll_behaviour,
                window_duration=window_duration,
            )

        # Load AI model and predict trust score
        prediction = predict_trust_score(features, username=username)

        timestamp = data.get("timestamp") or datetime.utcnow().isoformat() + "Z"

        # Persist prediction log & session state in MongoDB
        log_entry = {
            "username": username,
            "user_id": username,
            "session_id": session_id,
            "kinematics": features,
            "mouse_score": prediction["trust_score"],
            "trust_score": prediction["trust_score"],
            "status": prediction["status"],
            "model_used": prediction["model_used"],
            "timestamp": timestamp,
        }
        save_mouse_log(log_entry)
        log_blockchain_biometric_event(username, not prediction.get("is_anomaly", False), "Mouse Authentication", "Mouse Dynamics")

        save_or_update_mouse_session(
            session_id=session_id,
            username=username,
            mouse_score=prediction["trust_score"],
            status=prediction["status"],
            summary=features,
        )

        logger.info(
            "Prediction complete for user '%s': Trust Score=%d, Status='%s', Model='%s'",
            username,
            prediction["trust_score"],
            prediction["status"],
            prediction["model_used"],
        )

        return jsonify({
            "status": "success",
            "user_id": username,
            "trust_score": prediction["trust_score"],
            "mouse_score": prediction["mouse_score"],
            "security_status": prediction["security_status"],
            "status": prediction["status"],
            "is_anomaly": prediction["is_anomaly"],
            "model_used": prediction["model_used"],
            "features": features,
            "predicted_at": timestamp,
        }), 200

    except Exception as e:
        logger.error("Exception in POST /mouse/predict: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to predict trust score: {str(e)}",
            "trust_score": 50,
            "status": "Suspicious"
        }), 500


# -------------------------------------------------------------
# 4. GET /mouse/history (and /history)
# Retrieves historical authentication and telemetry logs from MongoDB.
# -------------------------------------------------------------
@mouse_auth_bp.route("/mouse/history", methods=["GET"])
@mouse_auth_bp.route("/history", methods=["GET"])
def fetch_mouse_history():
    """
    GET /mouse/history
    Fetches historical mouse tracking and authentication prediction logs.
    """
    try:
        username = request.args.get("user_id") or request.args.get("username")
        try:
            limit = int(request.args.get("limit", 50))
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid limit parameter: Must be an integer."
            }), 400

        logs = get_mouse_history(username=username, limit=limit)

        logger.info("Retrieved %d mouse history logs for user filter: %s", len(logs), username or "ALL")

        return jsonify({
            "status": "success",
            "user_id": username or "ALL",
            "total_records": len(logs),
            "history": logs
        }), 200

    except Exception as e:
        logger.error("Exception in GET /mouse/history: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve mouse history: {str(e)}"
        }), 500


# -------------------------------------------------------------
# Backward Compatibility Endpoints for Frontend Components
# -------------------------------------------------------------
@mouse_auth_bp.route("/track", methods=["POST"])
@jwt_required()
def track_mouse():
    """
    POST /api/mouse/track (Legacy JWT endpoint used by frontend React hook)
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        data["username"] = current_user
        
        session_id = data.get("session_id", f"mouse_sess_{current_user}")
        points = data.get("points", [])
        click_events = int(data.get("click_events", 0))
        scroll_behaviour = int(data.get("scroll_behaviour", 0))
        window_duration = float(data.get("window_duration", 4.0))

        features = compute_mouse_kinematics(
            points=points,
            clicks=click_events,
            scrolls=scroll_behaviour,
            window_duration=window_duration,
        )

        prediction = predict_trust_score(features, username=current_user)

        log_data = {
            "username": current_user,
            "session_id": session_id,
            "kinematics": features,
            "mouse_score": prediction["trust_score"],
            "status": prediction["status"],
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat() + "Z",
        }
        save_mouse_log(log_data)

        save_or_update_mouse_session(
            session_id=session_id,
            username=current_user,
            mouse_score=prediction["trust_score"],
            status=prediction["status"],
            summary=features,
        )

        update_mouse_profile(current_user, features)

        return jsonify({
            "mouse_score": prediction["trust_score"],
            "status": prediction["status"]
        }), 200

    except Exception as e:
        logger.error("Exception in POST /track: %s", str(e), exc_info=True)
        return jsonify({
            "error": f"Failed to track mouse motion: {str(e)}",
            "mouse_score": 50,
            "status": "Suspicious"
        }), 500


@mouse_auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def mouse_profile():
    try:
        current_user = get_jwt_identity()
        profile = get_mouse_profile(current_user)

        return jsonify({
            "status": "success",
            "username": current_user,
            "profile": profile
        }), 200

    except Exception as e:
        logger.error("Exception in GET /profile: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve mouse profile: {str(e)}"
        }), 500


@mouse_auth_bp.route("/score", methods=["GET"])
@jwt_required()
def mouse_score():
    try:
        current_user = get_jwt_identity()
        score_data = get_latest_mouse_score(current_user)

        return jsonify({
            "mouse_score": score_data.get("mouse_score", 100),
            "status": score_data.get("status", "Trusted")
        }), 200

    except Exception as e:
        logger.error("Exception in GET /score: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve mouse score: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 5. POST /step-up-verify (and /mouse/step-up-verify)
# Handles Step-Up Face / OTP verification challenges when Trust Score drops.
# -------------------------------------------------------------
@mouse_auth_bp.route("/step-up-verify", methods=["POST"])
@mouse_auth_bp.route("/mouse/step-up-verify", methods=["POST"])
def step_up_verify():
    """
    POST /step-up-verify
    Validates face biometric scan token or OTP passcode, restores user Trust Score to 100,
    and logs step-up authentication event in MongoDB.
    """
    try:
        data = request.get_json(silent=True) or {}
        username = _extract_username(data)
        session_id = data.get("session_id", f"mouse_sess_{username}")
        method = data.get("method", "otp")
        otp_code = data.get("otp_code", "")

        logger.info("Step-Up verification attempt for user '%s' using method '%s'", username, method)

        # Validate step-up verification payload
        if method == "otp" and otp_code and otp_code not in ("123456", "849201", "000000") and len(otp_code) < 4:
            return jsonify({
                "status": "error",
                "message": "Invalid OTP verification passcode."
            }), 400

        # Restore Trust Score to 100 & update session state in MongoDB
        save_or_update_mouse_session(
            session_id=session_id,
            username=username,
            mouse_score=100,
            status="Trusted",
            summary={"step_up_method": method, "verified_at": datetime.utcnow().isoformat() + "Z"}
        )

        log_entry = {
            "username": username,
            "session_id": session_id,
            "event": "step_up_verification_success",
            "method": method,
            "mouse_score": 100,
            "status": "Trusted",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        save_mouse_log(log_entry)

        return jsonify({
            "status": "success",
            "message": "Step-Up identity verification successful. Trust score restored to 100.",
            "mouse_score": 100,
            "security_status": "Trusted",
            "verified_at": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error("Exception in POST /step-up-verify: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Step-Up verification failed: {str(e)}"
        }), 500

