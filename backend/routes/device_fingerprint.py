"""
Flask REST Blueprint for Device Fingerprinting Authentication Engine
Endpoints:
- POST /api/device/fingerprint  (Register/update trusted device)
- POST /api/device/verify       (Verify incoming biometrics & compute similarity score)
- GET  /api/device/history      (Get verification audit log history)
- GET  /api/device/trusted-list (Get registered trusted devices)
- POST /api/device/revoke       (Revoke trust for a device ID)
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from service.device_fingerprint_engine import (
    evaluate_device_trust,
    generate_fingerprint_hash,
)
from models.device_model import (
    save_device_fingerprint,
    get_trusted_devices,
    get_device_history,
    revoke_device_trust,
)

logger = logging.getLogger(__name__)

device_fingerprint_bp = Blueprint("device_fingerprint", __name__)


@device_fingerprint_bp.route("/fingerprint", methods=["POST"])
def register_fingerprint():
    """
    Registers or updates a device fingerprint profile for a user.
    """
    data = request.get_json() or {}
    username = data.get("username", "anonymous")
    attributes = data.get("attributes", {})

    if not attributes:
        return jsonify({"status": "error", "message": "Missing device attributes payload"}), 400

    fingerprint_id = generate_fingerprint_hash(attributes)
    device_name = data.get("device_name") or f"{attributes.get('browser_name', 'Browser')} on {attributes.get('os', 'Device')}"

    result = save_device_fingerprint({
        "username": username,
        "fingerprint_id": fingerprint_id,
        "attributes": attributes,
        "device_name": device_name,
        "status": "Trusted",
        "trust_score": 100,
    })

    return jsonify({
        "status": "success",
        "message": "Device fingerprint registered successfully",
        "fingerprint_id": fingerprint_id,
        "device_name": device_name,
        "username": username,
        "result": result,
    }), 201


@device_fingerprint_bp.route("/verify", methods=["POST"])
def verify_device():
    """
    Verifies incoming device biometrics against user baseline profiles.
    Returns match percentage, risk level (Trusted, Medium Risk, High Risk),
    fingerprint ID, and breakdown.
    """
    data = request.get_json() or {}
    username = data.get("username", "anonymous")
    attributes = data.get("attributes") or data.get("fingerprint", {})

    if not attributes:
        return jsonify({"status": "error", "message": "Missing device attributes payload for verification"}), 400

    verification_result = evaluate_device_trust(attributes, username=username)

    return jsonify({
        "status": "success",
        "verification": verification_result,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), 200


@device_fingerprint_bp.route("/history", methods=["GET"])
def device_history():
    """
    Retrieves device verification audit logs.
    """
    username = request.args.get("username")
    limit = int(request.args.get("limit", 30))

    history = get_device_history(username=username, limit=limit)
    return jsonify({
        "status": "success",
        "count": len(history),
        "history": history,
    }), 200


@device_fingerprint_bp.route("/trusted-list", methods=["GET"])
def trusted_devices_list():
    """
    Retrieves registered trusted device profiles for a user.
    """
    username = request.args.get("username", "anonymous")
    devices = get_trusted_devices(username)

    return jsonify({
        "status": "success",
        "username": username,
        "count": len(devices),
        "devices": devices,
    }), 200


@device_fingerprint_bp.route("/revoke", methods=["POST"])
def revoke_device():
    """
    Revokes trust for a registered device fingerprint.
    """
    data = request.get_json() or {}
    username = data.get("username", "anonymous")
    fingerprint_id = data.get("fingerprint_id")

    if not fingerprint_id:
        return jsonify({"status": "error", "message": "Missing fingerprint_id parameter"}), 400

    success = revoke_device_trust(username, fingerprint_id)
    if success:
        return jsonify({
            "status": "success",
            "message": f"Trust revoked for device fingerprint {fingerprint_id}",
            "fingerprint_id": fingerprint_id,
        }), 200

    return jsonify({
        "status": "error",
        "message": f"Device fingerprint {fingerprint_id} not found or already revoked",
    }), 444
