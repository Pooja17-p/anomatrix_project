from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models.behavior_model import (
    save_behavior_log,
    get_behavior_history,
    get_behavior_stats,
)
from models.session_model import create_or_update_session
from models.user_model import find_user, update_trust
from service.behavior_preprocessor import (
    preprocess_behavior_data,
    compute_aggregate_statistics,
)

behavior_bp = Blueprint("behavior", __name__)


# -------------------------------------------------------------
# POST /api/behavior/collect
# Continuously receives user behavioral data every 5 seconds
# -------------------------------------------------------------
@behavior_bp.route("/collect", methods=["POST"])
@jwt_required()
def collect_behavior():
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}

        session_id = data.get("session_id", f"sess_{current_user}_default")
        timestamp = data.get("timestamp") or datetime.utcnow().isoformat() + "Z"

        # 1. Preprocess raw data using Pandas, NumPy & Scikit-learn
        processed_data = preprocess_behavior_data(data)

        # 2. Build behavior log document for MongoDB persistence
        log_entry = {
            "username": current_user,
            "session_id": session_id,
            "timestamp": timestamp,
            "raw_metrics": processed_data["raw_metrics"],
            "preprocessed_features": processed_data["preprocessed_features"],
            "ml_analysis": processed_data["ml_analysis"],
        }

        # 3. Save log into MongoDB behavior_logs collection
        saved_log = save_behavior_log(log_entry)

        # 4. Update session metadata in sessions collection
        duration = processed_data["raw_metrics"]["session_duration"]
        risk_level = processed_data["ml_analysis"]["risk_level"]
        anomaly_score = processed_data["ml_analysis"]["anomaly_score"]

        session_summary = {
            "latest_mouse_speed": processed_data["raw_metrics"]["mouse_speed"],
            "latest_typing_speed": processed_data["raw_metrics"]["typing_speed"],
            "latest_anomaly_score": anomaly_score,
        }

        create_or_update_session(
            username=current_user,
            session_id=session_id,
            duration=duration,
            latest_risk=risk_level,
            summary=session_summary,
        )

        # 5. Dynamic trust score update based on behavioral anomaly risk
        user_info = find_user(current_user)
        if user_info:
            current_trust = user_info.get("trust_score", 100)
            if risk_level == "Critical":
                new_trust = max(0, current_trust - 15)
            elif risk_level == "High":
                new_trust = max(0, current_trust - 8)
            elif risk_level == "Medium":
                new_trust = max(0, current_trust - 2)
            else:
                new_trust = min(100, current_trust + 1)

            update_trust(current_user, new_trust, risk_level)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Behavior data collected and preprocessed successfully",
                    "data": {
                        "log_id": saved_log.get("_id"),
                        "session_id": session_id,
                        "anomaly_score": anomaly_score,
                        "is_anomaly": processed_data["ml_analysis"]["is_anomaly"],
                        "risk_level": risk_level,
                        "timestamp": timestamp,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to process behavior data: {str(e)}",
                }
            ),
            500,
        )


# -------------------------------------------------------------
# GET /api/behavior/history
# Retrieves historical behavior logs for the authenticated user
# -------------------------------------------------------------
@behavior_bp.route("/history", methods=["GET"])
@jwt_required()
def behavior_history():
    try:
        current_user = get_jwt_identity()

        limit = int(request.args.get("limit", 50))
        skip = int(request.args.get("skip", 0))
        session_id = request.args.get("session_id")

        history = get_behavior_history(
            username=current_user,
            session_id=session_id,
            limit=limit,
            skip=skip,
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "count": len(history),
                    "username": current_user,
                    "history": history,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to fetch behavior history: {str(e)}",
                }
            ),
            500,
        )


# -------------------------------------------------------------
# GET /api/behavior/statistics
# Computes aggregate behavioral analytics (typing speed, mouse speed, etc.)
# -------------------------------------------------------------
@behavior_bp.route("/statistics", methods=["GET"])
@jwt_required()
def behavior_statistics():
    try:
        current_user = get_jwt_identity()

        raw_logs = get_behavior_stats(current_user)
        stats = compute_aggregate_statistics(raw_logs)

        return (
            jsonify(
                {
                    "status": "success",
                    "username": current_user,
                    "statistics": stats,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to compute behavior statistics: {str(e)}",
                }
            ),
            500,
        )
