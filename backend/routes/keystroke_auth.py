import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.keystroke_model import (
    save_keystroke_log,
    save_or_update_keystroke_session,
    get_keystroke_profile,
    update_keystroke_profile,
    get_latest_keystroke_score,
    get_keystroke_history,
    get_all_keystroke_logs_for_training,
    save_keystroke_model_metadata,
)
from service.keystroke_engine import (
    extract_typing_features,
    evaluate_typing_similarity,
    train_keystroke_model,
    predict_keystroke_trust_score,
)

logger = logging.getLogger("keystroke_auth")
logger.setLevel(logging.INFO)

# Initialize Flask Blueprint for Keystroke Dynamics Authentication module
keystroke_auth_bp = Blueprint("keystroke_auth", __name__)


def _extract_username(data):
    """Utility function to extract username/user_id from JWT token or request JSON body."""
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
# 1. POST /keystroke-data (and /keystroke/data, /data, /collect)
# Collects raw/processed keyboard telemetry in MongoDB and updates profile.
# -------------------------------------------------------------
@keystroke_auth_bp.route("/keystroke-data", methods=["POST"])
@keystroke_auth_bp.route("/keystroke/data", methods=["POST"])
@keystroke_auth_bp.route("/data", methods=["POST"])
@keystroke_auth_bp.route("/collect", methods=["POST"])
def collect_keystroke_data():
    """
    POST /keystroke-data
    Extracts hold time, flight time, WPM, rhythm variance, and error rates,
    stores records in MongoDB, and updates user profile.
    """
    try:
        data = request.get_json(silent=True) or {}
        username = _extract_username(data)
        session_id = data.get("session_id", f"key_sess_{username}")
        window_duration = float(data.get("window_duration", 4.0))

        features = extract_typing_features(data, window_duration=window_duration)
        prediction = predict_keystroke_trust_score(features, username=username)

        log_data = {
            "username": username,
            "user_id": username,
            "session_id": session_id,
            "biometrics": features,
            "kinematics": features,
            "typing_score": prediction["trust_score"],
            "trust_score": prediction["trust_score"],
            "status": prediction["status"],
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat() + "Z",
        }
        saved_doc = save_keystroke_log(log_data)

        save_or_update_keystroke_session(
            session_id=session_id,
            username=username,
            typing_score=prediction["trust_score"],
            status=prediction["status"],
            summary=features,
        )

        update_keystroke_profile(username, features)

        return jsonify({
            "status": "success",
            "message": "Keystroke telemetry stored successfully",
            "record_id": saved_doc.get("_id"),
            "user_id": username,
            "session_id": session_id,
            "typing_score": prediction["trust_score"],
            "trust_score": prediction["trust_score"],
            "security_status": prediction["status"],
            "auth_status": prediction["status"],
            "features": features,
            "timestamp": log_data["timestamp"],
        }), 201

    except Exception as e:
        logger.error("Exception in POST /keystroke-data: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to collect keystroke telemetry: {str(e)}",
            "typing_score": 50,
            "status": "Suspicious"
        }), 500


# -------------------------------------------------------------
# 2. POST /keystroke/train (and /train)
# Trains Isolation Forest AI model on user historical typing logs.
# -------------------------------------------------------------
@keystroke_auth_bp.route("/keystroke/train", methods=["POST"])
@keystroke_auth_bp.route("/train", methods=["POST"])
def train_keystroke_auth():
    """
    POST /keystroke/train
    Trains an Isolation Forest ML model on historical user typing features.
    """
    try:
        data = request.get_json(silent=True) or {}
        username = _extract_username(data)

        logs = get_all_keystroke_logs_for_training(username)
        training_result = train_keystroke_model(username, logs)

        metadata = {
            "model_type": training_result["model_type"],
            "samples_trained": training_result["samples_trained"],
            "model_path": training_result["model_path"],
            "trained_at": datetime.utcnow().isoformat() + "Z",
        }
        save_keystroke_model_metadata(username, metadata)

        return jsonify({
            "status": "success",
            "message": "AI keystroke model trained successfully",
            "user_id": username,
            "model_type": training_result["model_type"],
            "samples_trained": training_result["samples_trained"],
            "model_path": training_result["model_path"],
            "trained_at": metadata["trained_at"],
        }), 200

    except Exception as e:
        logger.error("Exception in POST /keystroke/train: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to train keystroke AI model: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 3. POST /keystroke/predict (and /predict)
# Evaluated typing biometrics and predicts trust score via Isolation Forest.
# -------------------------------------------------------------
@keystroke_auth_bp.route("/keystroke/predict", methods=["POST"])
@keystroke_auth_bp.route("/predict", methods=["POST"])
def predict_keystroke_auth():
    """
    POST /keystroke/predict
    Evaluates typing biometrics using Isolation Forest, returns Trust Score (0-100) and risk level.
    """
    try:
        data = request.get_json(silent=True) or {}
        username = _extract_username(data)
        session_id = data.get("session_id", f"key_sess_{username}")
        window_duration = float(data.get("window_duration", 4.0))

        if data.get("biometrics") and isinstance(data["biometrics"], dict):
            features = data["biometrics"]
        else:
            features = extract_typing_features(data, window_duration=window_duration)

        prediction = predict_keystroke_trust_score(features, username=username)
        timestamp = data.get("timestamp") or datetime.utcnow().isoformat() + "Z"

        log_entry = {
            "username": username,
            "user_id": username,
            "session_id": session_id,
            "biometrics": features,
            "kinematics": features,
            "typing_score": prediction["trust_score"],
            "trust_score": prediction["trust_score"],
            "status": prediction["status"],
            "model_used": prediction["model_used"],
            "timestamp": timestamp,
        }
        save_keystroke_log(log_entry)
        log_blockchain_biometric_event(username, not prediction.get("is_anomaly", False), "Keystroke Authentication", "Keystroke Dynamics")

        save_or_update_keystroke_session(
            session_id=session_id,
            username=username,
            typing_score=prediction["trust_score"],
            status=prediction["status"],
            summary=features,
        )

        return jsonify({
            "status": prediction["status"],
            "user_id": username,
            "trust_score": prediction["trust_score"],
            "typing_score": prediction["trust_score"],
            "security_status": prediction["status"],
            "is_anomaly": prediction["is_anomaly"],
            "model_used": prediction["model_used"],
            "features": features,
            "predicted_at": timestamp,
        }), 200

    except Exception as e:
        logger.error("Exception in POST /keystroke/predict: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to predict keystroke trust score: {str(e)}",
            "typing_score": 50,
            "status": "Suspicious"
        }), 500


# -------------------------------------------------------------
# 4. GET /keystroke/history (and /history)
# Fetches historical keystroke tracking logs from MongoDB.
# -------------------------------------------------------------
@keystroke_auth_bp.route("/keystroke/history", methods=["GET"])
@keystroke_auth_bp.route("/history", methods=["GET"])
def fetch_keystroke_history():
    """
    GET /keystroke/history
    Fetches historical typing telemetry and authentication prediction logs.
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

        logs = get_keystroke_history(username=username, limit=limit)

        return jsonify({
            "status": "success",
            "user_id": username or "ALL",
            "total_records": len(logs),
            "history": logs
        }), 200

    except Exception as e:
        logger.error("Exception in GET /keystroke/history: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve keystroke history: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 5. GET /keystroke/profile (and /profile)
# -------------------------------------------------------------
@keystroke_auth_bp.route("/keystroke/profile", methods=["GET"])
@keystroke_auth_bp.route("/profile", methods=["GET"])
def keystroke_profile():
    try:
        data = request.get_json(silent=True) or {}
        username = request.args.get("user_id") or request.args.get("username") or _extract_username(data)
        profile = get_keystroke_profile(username)

        return jsonify({
            "status": "success",
            "username": username,
            "profile": profile
        }), 200

    except Exception as e:
        logger.error("Exception in GET /profile: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch keystroke profile: {str(e)}"
        }), 500


# -------------------------------------------------------------
# 6. GET /keystroke/score (and /score)
# -------------------------------------------------------------
@keystroke_auth_bp.route("/keystroke/score", methods=["GET"])
@keystroke_auth_bp.route("/score", methods=["GET"])
def keystroke_score():
    try:
        data = request.get_json(silent=True) or {}
        username = request.args.get("user_id") or request.args.get("username") or _extract_username(data)
        score_data = get_latest_keystroke_score(username)

        return jsonify({
            "typing_score": score_data.get("typing_score", 91),
            "status": score_data.get("status", "Trusted")
        }), 200

    except Exception as e:
        logger.error("Exception in GET /score: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch keystroke score: {str(e)}"
        }), 500
