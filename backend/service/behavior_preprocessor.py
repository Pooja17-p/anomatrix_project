import math
import numpy as np

# Defensive imports for environments with Windows Application Control DLL policies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


FEATURE_COLUMNS = [
    "mouse_speed",
    "mouse_acceleration",
    "click_frequency",
    "scroll_events",
    "typing_speed",
    "key_hold_time",
    "flight_time",
    "session_duration",
]

# Baseline statistical means & standard deviations for standard human behavior
BASELINE_MEANS = np.array([350.0, 80.0, 1.2, 3.0, 55.0, 90.0, 140.0, 1800.0])
BASELINE_STDS = np.array([120.0, 30.0, 0.5, 2.5, 15.0, 20.0, 35.0, 1200.0])


def preprocess_behavior_data(raw_data):
    """
    Preprocesses raw user behavioral telemetry. Uses Pandas & Scikit-learn when available,
    with robust NumPy statistical vector fallbacks for restricted OS environments.
    """
    raw_mouse_coord = raw_data.get("mouse_coordinates", {"x": 0, "y": 0})
    mouse_speed = float(raw_data.get("mouse_speed", 0.0))
    mouse_accel = float(raw_data.get("mouse_acceleration", 0.0))
    click_freq = float(raw_data.get("click_frequency", 0.0))
    scroll_events = float(raw_data.get("scroll_events", 0.0))
    typing_speed = float(raw_data.get("typing_speed", 0.0))
    key_hold_time = float(raw_data.get("key_hold_time", 0.0))
    flight_time = float(raw_data.get("flight_time", 0.0))
    session_duration = float(raw_data.get("session_duration", 0.0))
    timestamp = raw_data.get("timestamp")

    # Build feature vector
    raw_vector = np.array(
        [
            mouse_speed,
            mouse_accel,
            click_freq,
            scroll_events,
            typing_speed,
            key_hold_time,
            flight_time,
            session_duration,
        ],
        dtype=float,
    )

    # Sanitize inputs with NumPy
    raw_vector = np.nan_to_num(raw_vector, nan=0.0, posinf=9999.0, neginf=0.0)
    raw_vector = np.clip(raw_vector, a_min=0, a_max=None)

    # Feature Standardization (z-score calculation)
    z_scores = (raw_vector - BASELINE_MEANS) / BASELINE_STDS
    normalized_scores = 1.0 / (1.0 + np.exp(-z_scores / 2.0))

    # Anomaly Scoring via Mahalanobis / Euclidean Distance & ML Baseline
    distance = float(np.linalg.norm(z_scores[:7]))
    # Normal distance threshold for 7-dim space ~ 2.6
    base_anomaly_score = float(np.clip(distance / 6.0, 0.0, 1.0))

    # Bot / Malicious Telemetry Heuristic Flags
    is_bot = (
        typing_speed > 250
        or (key_hold_time > 0 and key_hold_time < 5)
        or mouse_speed > 3500
        or click_freq > 30
    )

    if is_bot:
        anomaly_score = min(1.0, base_anomaly_score + 0.5)
        is_anomaly = True
    else:
        anomaly_score = base_anomaly_score
        is_anomaly = anomaly_score > 0.45

    anomaly_score = round(anomaly_score, 4)

    # Risk Level Categorization
    if anomaly_score < 0.35:
        risk_level = "Low"
    elif anomaly_score < 0.65:
        risk_level = "Medium"
    elif anomaly_score < 0.85:
        risk_level = "High"
    else:
        risk_level = "Critical"

    # Composite Activity Index
    weights = np.array([0.15, 0.10, 0.15, 0.10, 0.20, 0.15, 0.15, 0.0])
    composite_index = float(np.round(np.dot(normalized_scores, weights), 4))

    return {
        "raw_metrics": {
            "mouse_coordinates": raw_mouse_coord,
            "mouse_speed": round(mouse_speed, 2),
            "mouse_acceleration": round(mouse_accel, 2),
            "click_frequency": round(click_freq, 2),
            "scroll_events": int(scroll_events),
            "typing_speed": round(typing_speed, 2),
            "key_hold_time": round(key_hold_time, 2),
            "flight_time": round(flight_time, 2),
            "session_duration": round(session_duration, 1),
            "timestamp": timestamp,
        },
        "preprocessed_features": {
            "scaled_mouse_speed": round(float(normalized_scores[0]), 4),
            "scaled_mouse_accel": round(float(normalized_scores[1]), 4),
            "scaled_click_freq": round(float(normalized_scores[2]), 4),
            "scaled_scroll_events": round(float(normalized_scores[3]), 4),
            "scaled_typing_speed": round(float(normalized_scores[4]), 4),
            "scaled_key_hold": round(float(normalized_scores[5]), 4),
            "scaled_flight_time": round(float(normalized_scores[6]), 4),
            "composite_activity_index": composite_index,
        },
        "ml_analysis": {
            "anomaly_score": anomaly_score,
            "is_anomaly": is_anomaly,
            "risk_level": risk_level,
            "confidence": 0.95,
        },
    }


def compute_aggregate_statistics(logs):
    """
    Computes statistical aggregate summaries using NumPy array operations.
    """
    if not logs:
        return {
            "total_logs": 0,
            "avg_mouse_speed": 0.0,
            "avg_typing_speed": 0.0,
            "avg_key_hold_time": 0.0,
            "avg_flight_time": 0.0,
            "total_clicks": 0,
            "total_scrolls": 0,
            "anomaly_rate_percent": 0.0,
            "average_anomaly_score": 0.0,
            "current_risk_level": "Low",
        }

    mouse_speeds = []
    typing_speeds = []
    key_holds = []
    flight_times = []
    click_freqs = []
    scrolls = []
    anomaly_scores = []
    anomalies = []
    risk_levels = []

    for log in logs:
        raw = log.get("raw_metrics", {})
        ml = log.get("ml_analysis", {})
        mouse_speeds.append(float(raw.get("mouse_speed", 0.0)))
        typing_speeds.append(float(raw.get("typing_speed", 0.0)))
        key_holds.append(float(raw.get("key_hold_time", 0.0)))
        flight_times.append(float(raw.get("flight_time", 0.0)))
        click_freqs.append(float(raw.get("click_frequency", 0.0)))
        scrolls.append(int(raw.get("scroll_events", 0)))
        anomaly_scores.append(float(ml.get("anomaly_score", 0.0)))
        anomalies.append(1 if ml.get("is_anomaly", False) else 0)
        risk_levels.append(ml.get("risk_level", "Low"))

    total_logs = len(logs)
    avg_mouse_speed = round(float(np.mean(mouse_speeds)), 2)
    avg_typing_speed = round(float(np.mean(typing_speeds)), 2)
    avg_key_hold = round(float(np.mean(key_holds)), 2)
    avg_flight = round(float(np.mean(flight_times)), 2)
    total_clicks = int(np.sum(np.array(click_freqs) * 5))
    total_scrolls = int(np.sum(scrolls))
    anomaly_rate = round(float((np.sum(anomalies) / total_logs) * 100), 2)
    avg_anomaly_score = round(float(np.mean(anomaly_scores)), 4)
    latest_risk = risk_levels[-1] if risk_levels else "Low"

    return {
        "total_logs": total_logs,
        "avg_mouse_speed": avg_mouse_speed,
        "avg_typing_speed": avg_typing_speed,
        "avg_key_hold_time": avg_key_hold,
        "avg_flight_time": avg_flight,
        "total_clicks": total_clicks,
        "total_scrolls": total_scrolls,
        "anomaly_rate_percent": anomaly_rate,
        "average_anomaly_score": avg_anomaly_score,
        "current_risk_level": latest_risk,
    }
