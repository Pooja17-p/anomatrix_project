import sys
import os
import json
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from service.keystroke_engine import (
    extract_typing_features,
    evaluate_typing_similarity,
    train_keystroke_model,
    predict_keystroke_trust_score,
)

print("=" * 60)
print("TESTING FLASK KEYSTROKE DYNAMICS AUTHENTICATION APIs")
print("=" * 60)

client = app.test_client()
sample_user = "test_user_key_001"

# 1. Test Feature Extraction & Similarity Evaluation
print("\n--- 1. Testing Biometric Feature Extraction & Similarity Engine ---")
sample_events = {
    "hold_times": [85.0, 92.0, 78.0, 95.0, 88.0],
    "flight_times": [120.0, 145.0, 130.0, 155.0, 125.0],
    "keypress_count": 25,
    "error_count": 1,
}

features = extract_typing_features(sample_events, window_duration=4.0)
print("Extracted Features:", json.dumps(features, indent=2))
assert features["hold_time"] > 0
assert features["flight_time"] > 0
assert features["typing_speed"] == 75.0

# 2. Test POST /keystroke-data Endpoint
print("\n--- 2. Testing POST /keystroke-data ---")
telemetry_payload = {
    "user_id": sample_user,
    "session_id": "key_sess_100",
    "hold_times": [85.0, 92.0, 78.0, 95.0, 88.0],
    "flight_times": [120.0, 145.0, 130.0, 155.0, 125.0],
    "keypress_count": 25,
    "error_count": 1,
    "window_duration": 4.0,
    "timestamp": datetime.utcnow().isoformat() + "Z",
}

resp_collect = client.post("/keystroke-data", data=json.dumps(telemetry_payload), content_type="application/json")
print("POST /keystroke-data Response Code:", resp_collect.status_code)
res_collect_data = resp_collect.get_json()
print("POST /keystroke-data Response:", json.dumps(res_collect_data, indent=2))

assert resp_collect.status_code == 201
assert res_collect_data["status"] == "success"
assert "typing_score" in res_collect_data
assert res_collect_data["user_id"] == sample_user

# 3. Test POST /keystroke/train Endpoint
print("\n--- 3. Testing POST /keystroke/train ---")
resp_train = client.post("/keystroke/train", data=json.dumps({"user_id": sample_user}), content_type="application/json")
print("POST /keystroke/train Response Code:", resp_train.status_code)
res_train_data = resp_train.get_json()
print("POST /keystroke/train Response:", json.dumps(res_train_data, indent=2))

assert resp_train.status_code == 200
assert res_train_data["status"] == "success"
assert res_train_data["model_type"] == "IsolationForest"

# 4. Test POST /keystroke/predict Endpoint
print("\n--- 4. Testing POST /keystroke/predict ---")
predict_payload = {
    "user_id": sample_user,
    "session_id": "key_sess_100",
    "hold_times": [90.0, 91.0, 89.0, 92.0],
    "flight_times": [135.0, 140.0, 138.0, 142.0],
    "keypress_count": 20,
    "error_count": 0,
    "window_duration": 4.0,
}

resp_predict = client.post("/keystroke/predict", data=json.dumps(predict_payload), content_type="application/json")
print("POST /keystroke/predict Response Code:", resp_predict.status_code)
res_predict_data = resp_predict.get_json()
print("POST /keystroke/predict Response:", json.dumps(res_predict_data, indent=2))

assert resp_predict.status_code == 200
assert "trust_score" in res_predict_data
assert 0 <= res_predict_data["trust_score"] <= 100

# Test Bot Macro Script Injection via POST /keystroke/predict
print("\n--- 4b. Testing Bot Macro Injection Detection ---")
bot_payload = {
    "user_id": sample_user,
    "session_id": "bot_key_sess",
    "hold_times": [1.0, 1.0, 1.0],
    "flight_times": [0.0, 0.0, 0.0],
    "keypress_count": 300,
    "error_count": 0,
    "window_duration": 4.0,
}

resp_bot = client.post("/keystroke/predict", data=json.dumps(bot_payload), content_type="application/json")
res_bot_data = resp_bot.get_json()
print("Bot Predict Response:", json.dumps(res_bot_data, indent=2))

assert resp_bot.status_code == 200
assert res_bot_data["trust_score"] <= 50

# 5. Test GET /keystroke/history Endpoint
print("\n--- 5. Testing GET /keystroke/history ---")
resp_hist = client.get(f"/keystroke/history?user_id={sample_user}&limit=10")
print("GET /keystroke/history Response Code:", resp_hist.status_code)
res_hist_data = resp_hist.get_json()
print("Total Records Fetched:", res_hist_data.get("total_records"))

assert resp_hist.status_code == 200
assert res_hist_data["status"] == "success"
assert len(res_hist_data["history"]) >= 1

print("\n" + "=" * 60)
print("[SUCCESS] ALL KEYSTROKE DYNAMICS API TESTS PASSED PERFECTLY!")
print("=" * 60)
