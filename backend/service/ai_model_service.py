import os
import joblib
from datetime import datetime
import numpy as np
from sklearn.ensemble import IsolationForest
from utils.geo_helper import calculate_distance

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)

def extract_features_from_history(history, registered_country, registered_device):
    """
    Extracts numerical features from a user's login history for ML modeling.
    Features: [login_hour, is_known_device, country_match, travel_speed]
    """
    features = []
    
    # Sort history by timestamp ascending
    sorted_history = sorted(history, key=lambda x: x.get("timestamp") or "")
    
    for i, item in enumerate(sorted_history):
        ts = item.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now()
        elif not isinstance(ts, datetime):
            ts = datetime.now()
            
        login_hour = float(ts.hour)
        
        # Device match (1.0 if registered device, else 0.0)
        is_known_device = 1.0 if item.get("device_id") == registered_device else 0.0
        
        # Country match (1.0 if matches registered country, else 0.0)
        country_match = 1.0 if item.get("country") == registered_country else 0.0
        
        # Travel speed (km/h) from previous login
        travel_speed = 0.0
        if i > 0:
            prev_item = sorted_history[i - 1]
            prev_lat = prev_item.get("latitude")
            prev_lon = prev_item.get("longitude")
            prev_ts = prev_item.get("timestamp")
            
            if isinstance(prev_ts, str):
                try:
                    prev_ts = datetime.fromisoformat(prev_ts.replace("Z", "+00:00"))
                except ValueError:
                    prev_ts = ts
                    
            lat = item.get("latitude")
            lon = item.get("longitude")
            
            if None not in (prev_lat, prev_lon, lat, lon, prev_ts, ts):
                dist = calculate_distance(prev_lat, prev_lon, lat, lon)
                time_diff = (ts - prev_ts).total_seconds() / 3600.0
                if time_diff > 0:
                    travel_speed = dist / time_diff
                    
        features.append([login_hour, is_known_device, country_match, travel_speed])
        
    return np.array(features)

def calculate_ai_anomaly_score(username, current_login_features, user_history, registered_country, registered_device):
    """
    Trains an Isolation Forest on the user's login history,
    then predicts the anomaly score for the current login attempt.
    Returns: anomaly_score (int, 0 to 100)
    """
    # If history is too small (e.g. less than 4 entries), we don't have enough data to train a reliable model
    if len(user_history) < 4:
        return 0
        
    try:
        # Extract features for training
        X_train = extract_features_from_history(user_history, registered_country, registered_device)
        
        # Train Isolation Forest
        clf = IsolationForest(
            n_estimators=50,
            contamination='auto',
            random_state=42,
            bootstrap=False
        )

        clf.fit(X_train)
        
        # Save model for audit/archival
        model_path = os.path.join(MODEL_DIR, f"{username}_isolation_forest.joblib")
        joblib.dump(clf, model_path)
        
        # Score current login
        # current_login_features should be shaped: [login_hour, is_known_device, country_match, travel_speed]
        x_new = np.array([current_login_features])
        
        # score_samples returns raw scores in range [-1.0, 0.0] (more negative means more anomalous)
        raw_score = clf.score_samples(x_new)[0]
        
        # Map raw score to percentage: -0.4 (or above) -> 0% anomaly, -0.7 (or below) -> 100% anomaly
        if raw_score >= -0.42:
            anomaly_score = 0
        elif raw_score <= -0.70:
            anomaly_score = 100
        else:
            anomaly_score = int(((-0.42 - raw_score) / 0.28) * 100)
            
        return max(0, min(100, anomaly_score))
        
    except Exception as e:
        print(f"Error running AI anomaly model: {e}")
        return 0
