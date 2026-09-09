import sys
import os
import json
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from service.mouse_engine import compute_mouse_kinematics, evaluate_mouse_similarity, predict_trust_score, train_mouse_model

print("=" * 60)
print("TESTING FLASK MOUSE MOTION AUTHENTICATION APIs")
print("=" * 60)

client = app.test_client()

sample_user = "test_user_mouse_001"

# 1. Test POST /mouse-data Endpoint
print("\n--- 1. Testing POST /mouse-data ---")
valid_mouse_data_payload = {
    "user_id": sample_user,
    "session_id": "sess_test_100",
    "points": [
        {"x": 100, "y": 100, "timestamp": 1000.0},
        {"x": 150, "y": 120, "timestamp": 1100.0},
        {"x": 220, "y": 180, "timestamp": 1200.0},
        {"x": 300, "y": 250, "timestamp": 1300.0},
    ],
    "click_events": 2,
    "scroll_behaviour": 3,
    "window_duration": 4.0,
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

resp = client.post("/mouse-data", data=json.dumps(valid_mouse_data_payload), content_type="application/json")
print("POST /mouse-data Response Status Code:", resp.status_code)
res_data = resp.get_json()
print("POST /mouse-data Response:", json.dumps(res_data, indent=2))

assert resp.status_code == 201
assert res_data["status"] == "success"
assert "record_id" in res_data
assert "kinematics" in res_data
assert res_data["user_id"] == sample_user


# Test POST /mouse-data Input Validation Error (Invalid payload)
print("\n--- 1b. Testing POST /mouse-data Input Validation (Bad Payload) ---")
invalid_payload = {
    "user_id": sample_user,
    "points": "not_a_list_of_points"
}
resp_bad = client.post("/mouse-data", data=json.dumps(invalid_payload), content_type="application/json")
print("Invalid POST /mouse-data Response Status Code:", resp_bad.status_code)
res_bad_data = resp_bad.get_json()
print("Invalid POST /mouse-data Response:", json.dumps(res_bad_data, indent=2))

assert resp_bad.status_code == 400
assert res_bad_data["status"] == "error"


# 2. Test POST /mouse/train Endpoint
print("\n--- 2. Testing POST /mouse/train ---")
train_payload = {
    "user_id": sample_user
}

resp_train = client.post("/mouse/train", data=json.dumps(train_payload), content_type="application/json")
print("POST /mouse/train Response Status Code:", resp_train.status_code)
res_train_data = resp_train.get_json()
print("POST /mouse/train Response:", json.dumps(res_train_data, indent=2))

assert resp_train.status_code == 200
assert res_train_data["status"] == "success"
assert res_train_data["model_type"] == "IsolationForest"
assert res_train_data["samples_trained"] >= 5


# 3. Test POST /mouse/predict Endpoint
print("\n--- 3. Testing POST /mouse/predict ---")
predict_payload = {
    "user_id": sample_user,
    "session_id": "sess_test_100",
    "points": [
        {"x": 105, "y": 105, "timestamp": 1000.0},
        {"x": 155, "y": 125, "timestamp": 1100.0},
        {"x": 225, "y": 185, "timestamp": 1200.0},
        {"x": 305, "y": 255, "timestamp": 1300.0},
    ],
    "click_events": 1,
    "scroll_behaviour": 2,
    "window_duration": 4.0
}

resp_predict = client.post("/mouse/predict", data=json.dumps(predict_payload), content_type="application/json")
print("POST /mouse/predict Response Status Code:", resp_predict.status_code)
res_predict_data = resp_predict.get_json()
print("POST /mouse/predict Response:", json.dumps(res_predict_data, indent=2))

assert resp_predict.status_code == 200
assert res_predict_data["status"] in ["Trusted", "Suspicious", "Anomalous"]
assert "trust_score" in res_predict_data
assert "mouse_score" in res_predict_data
assert "security_status" in res_predict_data
assert 0 <= res_predict_data["trust_score"] <= 100


# Test Bot Detection via POST /mouse/predict
print("\n--- 3b. Testing POST /mouse/predict with Bot/Macro Trajectory ---")
bot_predict_payload = {
    "user_id": sample_user,
    "session_id": "bot_sess_999",
    "points": [
        {"x": 0, "y": 0, "timestamp": 1000.0},
        {"x": 1000, "y": 0, "timestamp": 1001.0},
    ]
}

resp_bot = client.post("/mouse/predict", data=json.dumps(bot_predict_payload), content_type="application/json")
res_bot_data = resp_bot.get_json()
print("Bot Predict Response:", json.dumps(res_bot_data, indent=2))

assert resp_bot.status_code == 200
assert res_bot_data["status"] in ["Suspicious", "Anomalous"]
assert res_bot_data["trust_score"] <= 50


# 4. Test GET /mouse/history Endpoint
print("\n--- 4. Testing GET /mouse/history ---")
resp_hist = client.get(f"/mouse/history?user_id={sample_user}&limit=10")
print("GET /mouse/history Response Status Code:", resp_hist.status_code)
res_hist_data = resp_hist.get_json()
print("GET /mouse/history Summary:")
print("Status:", res_hist_data.get("status"))
print("Total Records Fetched:", res_hist_data.get("total_records"))

assert resp_hist.status_code == 200
assert res_hist_data["status"] == "success"
assert "history" in res_hist_data
assert len(res_hist_data["history"]) >= 1

print("\n" + "=" * 60)
print("[SUCCESS] ALL FLASK MOUSE AUTHENTICATION API TESTS PASSED!")
print("=" * 60)
