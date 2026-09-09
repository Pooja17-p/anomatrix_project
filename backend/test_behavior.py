import sys
import os
import json
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.behavior_preprocessor import (
    preprocess_behavior_data,
    compute_aggregate_statistics,
)

print("--------------------------------------------------")
print("TESTING AI BEHAVIOUR PREPROCESSOR & ML ENGINE")
print("--------------------------------------------------")

sample_raw_payload = {
    "session_id": "test_sess_001",
    "mouse_coordinates": {"x": 640, "y": 480},
    "mouse_speed": 245.5,
    "mouse_acceleration": 22.1,
    "click_frequency": 1.4,
    "scroll_events": 5,
    "typing_speed": 62.0,
    "key_hold_time": 82.5,
    "flight_time": 110.2,
    "session_duration": 45,
    "timestamp": datetime.utcnow().isoformat() + "Z",
}

processed_result = preprocess_behavior_data(sample_raw_payload)

print("Preprocessed Output:")
print(json.dumps(processed_result, indent=2))

assert "raw_metrics" in processed_result
assert "preprocessed_features" in processed_result
assert "ml_analysis" in processed_result
assert processed_result["ml_analysis"]["risk_level"] in ["Low", "Medium", "High", "Critical"]

print("\n--- Testing Anomaly Detection on Extreme Bot Telemetry ---")
extreme_bot_payload = {
    "session_id": "bot_sess_999",
    "mouse_coordinates": {"x": 0, "y": 0},
    "mouse_speed": 4500.0, # Impossible mouse speed
    "mouse_acceleration": 800.0,
    "click_frequency": 50.0,
    "scroll_events": 200,
    "typing_speed": 450.0, # 450 WPM bot typing
    "key_hold_time": 1.2, # 1.2 ms key hold
    "flight_time": 2.0,
    "session_duration": 10,
    "timestamp": datetime.utcnow().isoformat() + "Z",
}

bot_processed = preprocess_behavior_data(extreme_bot_payload)
print(json.dumps(bot_processed["ml_analysis"], indent=2))

assert bot_processed["ml_analysis"]["is_anomaly"] == True
assert bot_processed["ml_analysis"]["risk_level"] in ["High", "Critical"]

print("\n--- Testing Aggregate Statistics Computation ---")
stats = compute_aggregate_statistics([processed_result, bot_processed])
print(json.dumps(stats, indent=2))

assert stats["total_logs"] == 2
print("\n[SUCCESS] ALL BEHAVIOURAL PREPROCESSING & ML TESTS PASSED PERFECTLY!")
