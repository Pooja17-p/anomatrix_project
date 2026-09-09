"""
ANOMATRIX Device Fingerprint Engine
Generates SHA-256 fingerprint signatures and executes weighted fuzzy similarity matching
against user trusted device baseline profiles.
"""

import hashlib
import json
import logging
from models.device_model import get_trusted_devices, save_device_fingerprint, log_device_verification

logger = logging.getLogger(__name__)


def generate_fingerprint_hash(attributes):
    """
    Generates a deterministic SHA-256 hex fingerprint ID from key browser biometrics.
    """
    if not isinstance(attributes, dict):
        attributes = {}

    canonical_payload = [
        str(attributes.get("canvas_hash", "")),
        str(attributes.get("webgl_vendor", "")),
        str(attributes.get("webgl_renderer", "")),
        str(attributes.get("platform", "")),
        str(attributes.get("os", "")),
        str(attributes.get("hardware_concurrency", "")),
        str(attributes.get("device_memory", "")),
        str(attributes.get("screen_resolution", "")),
        str(attributes.get("timezone", "")),
        str(attributes.get("language", "")),
    ]

    raw_str = "||".join(canonical_payload)
    fingerprint_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
    return fingerprint_hash


def calculate_device_similarity(incoming, baseline):
    """
    Computes a weighted similarity percentage (0-100%) between incoming device biometrics
    and a known baseline profile.
    
    Weights:
    - Canvas Signature Hash: 25%
    - WebGL GPU Vendor & Renderer: 25%
    - Hardware Specs (CPU, RAM, Screen): 20%
    - Platform & Operating System: 15%
    - Language & Timezone: 10%
    - User Agent Family: 5%
    """
    if not isinstance(incoming, dict):
        incoming = {}
    if not isinstance(baseline, dict):
        baseline = {}

    scores = {}

    # 1. Canvas Signature Hash (25%)
    inc_canvas = str(incoming.get("canvas_hash", ""))
    base_canvas = str(baseline.get("canvas_hash", ""))
    scores["canvas"] = 1.0 if (inc_canvas and inc_canvas == base_canvas) else 0.0

    # 2. WebGL GPU Vendor & Renderer (25%)
    inc_gpu = f"{incoming.get('webgl_vendor', '')}|{incoming.get('webgl_renderer', '')}"
    base_gpu = f"{baseline.get('webgl_vendor', '')}|{baseline.get('webgl_renderer', '')}"
    scores["webgl"] = 1.0 if (inc_gpu and inc_gpu == base_gpu) else 0.0

    # 3. Hardware Specs: CPU cores, RAM, Screen Resolution (20%)
    hw_matches = 0
    hw_total = 3
    if str(incoming.get("hardware_concurrency", "")) == str(baseline.get("hardware_concurrency", "")):
        hw_matches += 1
    if str(incoming.get("device_memory", "")) == str(baseline.get("device_memory", "")):
        hw_matches += 1
    if str(incoming.get("screen_resolution", "")) == str(baseline.get("screen_resolution", "")):
        hw_matches += 1
    scores["hardware"] = hw_matches / hw_total

    # 4. Platform & Operating System (15%)
    inc_os = f"{incoming.get('platform', '')}|{incoming.get('os', '')}"
    base_os = f"{baseline.get('platform', '')}|{baseline.get('os', '')}"
    scores["os_platform"] = 1.0 if (inc_os and inc_os == base_os) else 0.0

    # 5. Language & Timezone (10%)
    loc_matches = 0
    if str(incoming.get("timezone", "")) == str(baseline.get("timezone", "")):
        loc_matches += 1
    if str(incoming.get("language", "")).split("-")[0] == str(baseline.get("language", "")).split("-")[0]:
        loc_matches += 1
    scores["locale"] = loc_matches / 2.0

    # 6. User Agent Family (5%)
    inc_browser = str(incoming.get("browser_name", ""))
    base_browser = str(baseline.get("browser_name", ""))
    scores["browser"] = 1.0 if (inc_browser and inc_browser == base_browser) else 0.0

    # Weighted Sum Calculation
    weighted_score = (
        scores["canvas"] * 0.25 +
        scores["webgl"] * 0.25 +
        scores["hardware"] * 0.20 +
        scores["os_platform"] * 0.15 +
        scores["locale"] * 0.10 +
        scores["browser"] * 0.05
    )

    match_percentage = round(weighted_score * 100, 1)

    breakdown = {
        "canvas_match": round(scores["canvas"] * 100, 1),
        "webgl_match": round(scores["webgl"] * 100, 1),
        "hardware_match": round(scores["hardware"] * 100, 1),
        "os_match": round(scores["os_platform"] * 100, 1),
        "locale_match": round(scores["locale"] * 100, 1),
        "browser_match": round(scores["browser"] * 100, 1),
    }

    return match_percentage, breakdown


def evaluate_device_trust(incoming_attributes, username="anonymous"):
    """
    Main device verification engine. Compares incoming biometrics against all known
    trusted profiles for a user and calculates risk level.
    """
    fingerprint_id = generate_fingerprint_hash(incoming_attributes)
    trusted_devices = get_trusted_devices(username)

    # First-time device registration for new users
    if not trusted_devices:
        device_name = f"{incoming_attributes.get('browser_name', 'Browser')} on {incoming_attributes.get('os', 'Device')}"
        save_device_fingerprint({
            "username": username,
            "fingerprint_id": fingerprint_id,
            "attributes": incoming_attributes,
            "device_name": device_name,
            "status": "Trusted",
            "trust_score": 100,
        })
        
        result = {
            "fingerprint_id": fingerprint_id,
            "match_percentage": 100.0,
            "risk_level": "Trusted",
            "status": "Trusted (New Baseline Saved)",
            "trust_score": 100,
            "attribute_breakdown": {
                "canvas_match": 100.0,
                "webgl_match": 100.0,
                "hardware_match": 100.0,
                "os_match": 100.0,
                "locale_match": 100.0,
                "browser_match": 100.0,
            },
            "is_new_device": True,
        }

        log_device_verification({
            "username": username,
            "fingerprint_id": fingerprint_id,
            "match_percentage": 100.0,
            "risk_level": "Trusted",
            "attributes": incoming_attributes,
            "attribute_breakdown": result["attribute_breakdown"],
            "status": "New Device Registered",
        })
        return result

    # Find highest similarity match across all registered user devices
    best_match_percentage = 0.0
    best_breakdown = {}
    matched_device = None

    for dev in trusted_devices:
        # Ignore revoked devices
        if dev.get("status") == "Revoked":
            continue

        baseline_attrs = dev.get("attributes", {})
        match_pct, breakdown = calculate_device_similarity(incoming_attributes, baseline_attrs)

        if match_pct > best_match_percentage:
            best_match_percentage = match_pct
            best_breakdown = breakdown
            matched_device = dev

    # Classify Risk Level based on best match percentage
    if best_match_percentage >= 85.0:
        risk_level = "Trusted"
        status_text = "Trusted Device Match"
    elif best_match_percentage >= 55.0:
        risk_level = "Medium Risk"
        status_text = "Partial Device Match (Browser/OS Shift)"
    else:
        risk_level = "High Risk"
        status_text = "Untrusted / Unknown Device (Potential Spoofing)"

    # Compute overall trust score (0-100)
    trust_score = int(best_match_percentage)

    verification_result = {
        "fingerprint_id": fingerprint_id,
        "match_percentage": best_match_percentage,
        "risk_level": risk_level,
        "status": status_text,
        "trust_score": trust_score,
        "attribute_breakdown": best_breakdown,
        "matched_device_id": matched_device.get("fingerprint_id") if matched_device else None,
        "is_new_device": False,
    }

    # Log verification event
    log_device_verification({
        "username": username,
        "fingerprint_id": fingerprint_id,
        "match_percentage": best_match_percentage,
        "risk_level": risk_level,
        "attributes": incoming_attributes,
        "attribute_breakdown": best_breakdown,
        "status": status_text,
    })

    return verification_result
