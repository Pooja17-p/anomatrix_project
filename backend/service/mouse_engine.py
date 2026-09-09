import os
import math
import logging
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Directory where trained AI models are saved
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Feature keys used for machine learning models
FEATURE_KEYS = [
    "speed",
    "acceleration",
    "direction",
    "direction_variance",
    "straightness_ratio",
    "click_rate",
    "scroll_speed",
]


def compute_mouse_kinematics(points, clicks=0, scrolls=0, window_duration=4.0):
    """
    Computes mathematical kinematics metrics (speed, acceleration, direction, curvature)
    from raw mouse movement points and event counters.

    Parameters:
        points (list of dict): Mouse point samples [{'x': int, 'y': int, 'timestamp': float}]
        clicks (int): Count of click events in the interval window.
        scrolls (int): Count of scroll events in the interval window.
        window_duration (float): Time window duration in seconds (default: 4.0s).

    Returns:
        dict: Calculated kinematics features dictionary.
    """
    if not points or len(points) < 2:
        return {
            "speed": 0.0,
            "acceleration": 0.0,
            "direction": 0.0,
            "direction_variance": 0.0,
            "straightness_ratio": 1.0,
            "click_rate": round(clicks / max(window_duration, 1.0), 2),
            "scroll_speed": round(scrolls / max(window_duration, 1.0), 2),
        }

    speeds = []
    accelerations = []
    directions = []
    total_path_length = 0.0

    last_speed = 0.0

    for i in range(1, len(points)):
        p1 = points[i - 1]
        p2 = points[i]

        dx = p2.get("x", 0) - p1.get("x", 0)
        dy = p2.get("y", 0) - p1.get("y", 0)
        dt = (p2.get("timestamp", 0) - p1.get("timestamp", 0)) / 1000.0  # seconds

        if dt <= 0:
            dt = 0.016  # fallback frame delta

        dist = math.sqrt(dx * dx + dy * dy)
        total_path_length += dist

        current_speed = dist / dt  # px/s
        speeds.append(current_speed)

        dv = current_speed - last_speed
        accel = abs(dv / dt)  # px/s^2
        accelerations.append(accel)
        last_speed = current_speed

        # Movement direction angle in degrees [0, 360)
        angle_rad = math.atan2(dy, dx)
        angle_deg = (math.degrees(angle_rad) + 360.0) % 360.0
        directions.append(angle_deg)

    avg_speed = float(np.mean(speeds)) if speeds else 0.0
    avg_accel = float(np.mean(accelerations)) if accelerations else 0.0
    avg_direction = float(np.mean(directions)) if directions else 0.0
    dir_variance = float(np.var(directions)) if directions else 0.0

    start_p = points[0]
    end_p = points[-1]
    euclidean_dist = math.sqrt(
        (end_p.get("x", 0) - start_p.get("x", 0)) ** 2
        + (end_p.get("y", 0) - start_p.get("y", 0)) ** 2
    )

    straightness = (
        euclidean_dist / total_path_length if total_path_length > 0 else 1.0
    )
    straightness = min(1.0, max(0.0, straightness))

    click_rate = clicks / max(window_duration, 1.0)
    scroll_speed = scrolls / max(window_duration, 1.0)

    return {
        "speed": round(avg_speed, 2),
        "acceleration": round(avg_accel, 2),
        "direction": round(avg_direction, 2),
        "direction_variance": round(dir_variance, 2),
        "straightness_ratio": round(straightness, 4),
        "click_rate": round(click_rate, 2),
        "scroll_speed": round(scroll_speed, 2),
    }


def _features_to_vector(features):
    """Convert features dict into numerical vector."""
    return [float(features.get(k, 0.0)) for k in FEATURE_KEYS]


def get_model_path(username):
    """Returns absolute file path for a user's trained model."""
    safe_user = "".join(c for c in (username or "global") if c.isalnum() or c in ("_", "-"))
    return os.path.join(MODEL_DIR, f"mouse_model_{safe_user}.joblib")


def train_mouse_model(username, feature_records):
    """
    Trains an IsolationForest ML model on user's historical mouse features.

    Parameters:
        username (str): Target user identifier.
        feature_records (list of dict): List of feature dicts or log dicts.

    Returns:
        dict: Training metadata (samples_count, model_path, algorithm).
    """
    logger.info("Starting AI model training for mouse authentication (user: %s)...", username)
    X = []

    for item in feature_records:
        if isinstance(item, dict):
            if "kinematics" in item and isinstance(item["kinematics"], dict):
                vec = _features_to_vector(item["kinematics"])
            elif "features" in item and isinstance(item["features"], dict):
                vec = _features_to_vector(item["features"])
            elif "speed" in item:
                vec = _features_to_vector(item)
            else:
                continue
            X.append(vec)

    # If insufficient real training samples, generate baseline distribution samples around normal human movement
    if len(X) < 5:
        logger.info("Insufficient samples (%d) for user %s. Supplementing with human baseline profile samples.", len(X), username)
        base_samples = [
            [350.0, 90.0, 180.0, 45.0, 0.85, 0.5, 2.0],
            [400.0, 110.0, 195.0, 50.0, 0.88, 0.6, 2.2],
            [320.0, 80.0, 160.0, 40.0, 0.80, 0.4, 1.8],
            [380.0, 100.0, 175.0, 48.0, 0.84, 0.5, 2.1],
            [360.0, 95.0, 185.0, 42.0, 0.86, 0.5, 2.0],
            [420.0, 120.0, 200.0, 55.0, 0.82, 0.7, 2.4],
        ]
        X.extend(base_samples)

    X_arr = np.array(X, dtype=np.float64)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_arr)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.08,
        random_state=42
    )
    model.fit(X_scaled)

    model_pipeline = {
        "scaler": scaler,
        "model": model,
        "username": username,
        "feature_keys": FEATURE_KEYS,
        "samples_count": len(X_arr),
    }

    filepath = get_model_path(username)
    joblib.dump(model_pipeline, filepath)
    logger.info("Successfully trained and saved AI mouse model to %s (samples: %d)", filepath, len(X_arr))

    return {
        "status": "success",
        "username": username,
        "model_type": "IsolationForest",
        "samples_trained": len(X_arr),
        "model_path": filepath,
    }


def load_mouse_model(username):
    """
    Loads trained AI model pipeline for user from disk.

    Parameters:
        username (str): User account name.

    Returns:
        dict or None: Model pipeline dict if found, else None.
    """
    filepath = get_model_path(username)
    if os.path.exists(filepath):
        try:
            logger.info("Loading AI mouse model from %s", filepath)
            return joblib.load(filepath)
        except Exception as e:
            logger.error("Failed to load model file %s: %s", filepath, str(e))
            return None
    return None


def predict_trust_score(features, username=None):
    """
    Predicts trust score (0-100) and security status for mouse motion features
    using loaded AI model or fallback heuristic engine.

    Parameters:
        features (dict): Extracted mouse kinematics features.
        username (str): Optional user identifier.

    Returns:
        dict: Prediction result object containing trust_score, status, and details.
    """
    logger.info("Predicting mouse trust score for user: %s", username)

    # 1. Check for extreme robotic / bot patterns first
    c_speed = features.get("speed", 0.0)
    c_accel = features.get("acceleration", 0.0)
    straightness = features.get("straightness_ratio", 1.0)

    is_bot = (c_speed > 4000.0) or (c_speed > 20.0 and c_accel < 0.1 and straightness > 0.99)

    # 2. Try loading user AI model
    model_pipeline = load_mouse_model(username) if username else None

    if model_pipeline and not is_bot:
        try:
            scaler = model_pipeline["scaler"]
            model = model_pipeline["model"]
            vec = np.array([_features_to_vector(features)], dtype=np.float64)
            vec_scaled = scaler.transform(vec)

            # decision_function yields positive for inliers, negative for outliers
            raw_score = model.decision_function(vec_scaled)[0]
            # Normalize decision_function (-0.5 to +0.5 range typical) to (0 to 100)
            trust_score = int(round(np.clip(50 + (raw_score * 100), 10, 100)))
            model_used = "IsolationForest"
        except Exception as e:
            logger.warning("Error running AI model prediction, falling back to heuristic: %s", str(e))
            trust_score, _ = evaluate_mouse_similarity(features, {})
            model_used = "HeuristicEngine"
    else:
        # Fallback to similarity evaluator
        trust_score, _ = evaluate_mouse_similarity(features, {})
        model_used = "HeuristicEngine"

    if is_bot:
        trust_score = min(trust_score, 15)
        model_used += "+BotFilter"

    # Status mapping based on trust score threshold
    if trust_score >= 80:
        status = "Trusted"
        is_anomaly = False
    elif trust_score >= 50:
        status = "Suspicious"
        is_anomaly = True
    else:
        status = "Anomalous"
        is_anomaly = True

    return {
        "trust_score": trust_score,
        "mouse_score": trust_score,
        "status": status,
        "security_status": status,
        "is_anomaly": is_anomaly,
        "features": features,
        "model_used": model_used,
    }


def evaluate_mouse_similarity(current_features, baseline_profile):
    """
    Compares current mouse movement kinematics against user's historical baseline profile.
    Generates a mouse similarity score (0 - 100) and security status ('Trusted', 'Suspicious', 'Anomalous').

    Parameters:
        current_features (dict): Current calculated mouse kinematics.
        baseline_profile (dict): User's historical baseline profile stored in MongoDB.

    Returns:
        tuple: (mouse_score: int, status: str)
    """
    b_speed = baseline_profile.get("avg_speed", 350.0)
    b_accel = baseline_profile.get("avg_acceleration", 90.0)
    b_dir_var = baseline_profile.get("direction_variance", 45.0)

    c_speed = current_features.get("speed", 0.0)
    c_accel = current_features.get("acceleration", 0.0)
    c_dir_var = current_features.get("direction_variance", 0.0)

    # Calculate relative deviations
    speed_diff = abs(c_speed - b_speed) / max(b_speed, 100.0)
    accel_diff = abs(c_accel - b_accel) / max(b_accel, 50.0)
    dir_diff = abs(c_dir_var - b_dir_var) / max(b_dir_var, 20.0)

    composite_diff = (0.4 * speed_diff) + (0.35 * accel_diff) + (0.25 * dir_diff)

    raw_score = 100.0 - (composite_diff * 15.0)

    # Robotic / Macro penalization
    if c_speed > 4000 or (c_speed > 20 and c_accel < 0.1 and current_features.get("straightness_ratio", 0) > 0.99):
        raw_score -= 55.0

    mouse_score = int(round(np.clip(raw_score, 10.0, 100.0)))

    # Status Mapping
    if mouse_score >= 80:
        status = "Trusted"
    elif mouse_score >= 50:
        status = "Suspicious"
    else:
        status = "Anomalous"

    return mouse_score, status
