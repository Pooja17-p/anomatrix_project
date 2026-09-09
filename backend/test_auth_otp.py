"""
Automated Test Suite for Authentication & OTP Verification Module
Verifies user registration, password hashing, JWT creation, MFA triggering, OTP generation, OTP resend, invalid OTP rejection, and successful OTP verification.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from config import db, users_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_auth_otp_flow():
    print("\n" + "=" * 60)
    print("TESTING AUTHENTICATION & OTP VERIFICATION MODULE")
    print("=" * 60)

    client = app.test_client()
    test_user = "otp_test_user_2026"
    test_pass = "SecurePass123!"

    # Clean up test user if exists
    users_collection.delete_one({"username": test_user})

    # 1. Test Registration API
    print("\n--- 1. Testing User Registration (POST /register) ---")
    reg_payload = {
        "name": "OTP Test User",
        "email": "otptest@anomatrix.io",
        "department": "Cybersecurity",
        "employee_id": "EMP-9090",
        "username": test_user,
        "password": test_pass,
        "device_id": "test_device_otp_001",
        "browser": "Chrome",
        "os": "Windows 11"
    }

    resp_reg = client.post("/register", json=reg_payload)
    print(f"POST /register Status Code: {resp_reg.status_code}")
    assert resp_reg.status_code == 201
    assert resp_reg.get_json()["message"] == "Registration Successful"

    # 2. Test Normal Login API
    print("\n--- 2. Testing Standard Login (POST /login) ---")
    resp_login = client.post("/login", json={
        "username": test_user,
        "password": test_pass,
        "device_id": "test_device_otp_001"
    })
    print(f"POST /login Status Code: {resp_login.status_code}")
    assert resp_login.status_code == 200
    login_data = resp_login.get_json()
    assert "access_token" in login_data
    assert login_data["mfa_enabled"] == False
    print(f"Issued JWT Access Token: {login_data['access_token'][:25]}...")

    # 3. Enable MFA in User Profile Settings
    print("\n--- 3. Enabling MFA for User (POST /update-settings) ---")
    resp_settings = client.post("/update-settings", json={
        "username": test_user,
        "mfa_enabled": True,
        "trust_devices": False,
        "email_alerts": True
    })
    assert resp_settings.status_code == 200
    print("MFA Flag set to True successfully.")

    # 4. Test MFA Triggered Login
    print("\n--- 4. Testing MFA-Triggered Login (POST /login) ---")
    resp_mfa_login = client.post("/login", json={
        "username": test_user,
        "password": test_pass,
        "device_id": "test_device_otp_001"
    })
    assert resp_mfa_login.status_code == 200
    mfa_data = resp_mfa_login.get_json()
    assert mfa_data.get("mfa_required") == True
    assert mfa_data.get("username") == test_user
    assert "dev_otp_preview" not in mfa_data
    assert "otp_code" not in mfa_data
    print("Login correctly halted. mfa_required = True response received (OTP strictly protected from API response).")

    # Retrieve generated temp_otp from database
    db_user = users_collection.find_one({"username": test_user})
    otp_code = db_user.get("temp_otp")
    assert otp_code is not None and len(otp_code) == 6
    print(f"Generated DB OTP Code: {otp_code}")

    # 5. Test Resend OTP Endpoint
    print("\n--- 5. Testing Resend OTP Endpoint (POST /resend-otp) ---")
    resp_resend = client.post("/resend-otp", json={"username": test_user})
    assert resp_resend.status_code == 200
    new_db_user = users_collection.find_one({"username": test_user})
    new_otp_code = new_db_user.get("temp_otp")
    assert new_otp_code is not None and len(new_otp_code) == 6
    print(f"Resent New DB OTP Code: {new_otp_code}")

    # 6. Test Invalid OTP Rejection
    print("\n--- 6. Testing Invalid OTP Rejection (POST /verify-otp) ---")
    resp_invalid = client.post("/verify-otp", json={
        "username": test_user,
        "otp": "000000",
        "device_id": "test_device_otp_001"
    })
    assert resp_invalid.status_code == 401
    assert resp_invalid.get_json()["message"] == "Invalid OTP code"
    print("Invalid OTP code correctly rejected with HTTP 401.")

    # 7. Test Expired OTP Rejection
    print("\n--- 7. Testing Expired OTP Rejection (POST /verify-otp) ---")
    users_collection.update_one(
        {"username": test_user},
        {"$set": {"otp_expiry": datetime.now() - timedelta(minutes=1)}}
    )
    resp_expired = client.post("/verify-otp", json={
        "username": test_user,
        "otp": new_otp_code,
        "device_id": "test_device_otp_001"
    })
    assert resp_expired.status_code == 401
    assert resp_expired.get_json()["message"] == "OTP code has expired"
    print("Expired OTP code correctly rejected with HTTP 401.")

    # Regenerate valid OTP code
    client.post("/resend-otp", json={"username": test_user})
    valid_db_user = users_collection.find_one({"username": test_user})
    valid_otp = valid_db_user.get("temp_otp")

    # 8. Test Valid OTP Verification & Final Token Issuance
    print("\n--- 8. Testing Valid OTP Verification (POST /verify-otp) ---")
    resp_valid = client.post("/verify-otp", json={
        "username": test_user,
        "otp": valid_otp,
        "device_id": "test_device_otp_001"
    })
    assert resp_valid.status_code == 200
    valid_data = resp_valid.get_json()
    assert valid_data["message"] == "Login successful"
    assert "access_token" in valid_data
    assert valid_data["trust_score"] >= 0
    print("OTP verification successful! JWT token issued & OTP cleared from DB.")

    # Verify temp_otp cleared
    final_user = users_collection.find_one({"username": test_user})
    assert "temp_otp" not in final_user or final_user.get("temp_otp") is None

    # Clean up test user
    users_collection.delete_one({"username": test_user})

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL AUTHENTICATION & OTP VERIFICATION TESTS PASSED PERFECTLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_auth_otp_flow()
