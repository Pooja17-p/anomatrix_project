"""
Automated Test Suite for Device Fingerprinting Authentication Engine
Verifies SHA-256 hash generation, weighted fuzzy similarity algorithm, and Flask REST APIs.
"""

import logging
from app import app
from service.device_fingerprint_engine import generate_fingerprint_hash, calculate_device_similarity, evaluate_device_trust

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_device_fingerprint_engine():
    print("\n" + "=" * 60)
    print("TESTING DEVICE FINGERPRINTING ENGINE & SIMILARITY MATCHING")
    print("=" * 60)

    # Sample Device Biometrics A (Original trusted baseline)
    device_a = {
        "canvas_hash": "a4f8901bce23991209ffae7812",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "hardware_concurrency": 16,
        "device_memory": 16,
        "screen_resolution": "1920x1080",
        "color_depth": 24,
        "pixel_ratio": 1.25,
        "platform": "Win32",
        "os": "Windows 10/11",
        "browser_name": "Chrome",
        "browser_version": "124.0.0.0",
        "language": "en-US",
        "timezone": "Asia/Kolkata",
    }

    # Sample Device B (Same physical PC, but updated browser version Chrome 124 -> 125)
    device_b = {
        **device_a,
        "browser_version": "125.0.0.0",
    }

    # Sample Device C (Unknown untrusted device / Linux Headless Bot)
    device_c = {
        "canvas_hash": "99999999999999999999999999",
        "webgl_vendor": "Mesa",
        "webgl_renderer": "llvmpipe (LLVM 12.0.0, 256 bits)",
        "hardware_concurrency": 2,
        "device_memory": 2,
        "screen_resolution": "800x600",
        "color_depth": 16,
        "pixel_ratio": 1.0,
        "platform": "Linux x86_64",
        "os": "Linux",
        "browser_name": "HeadlessChrome",
        "browser_version": "99.0.0.0",
        "language": "en-US",
        "timezone": "UTC",
    }

    # 1. Test SHA-256 Hash Generation
    hash_a = generate_fingerprint_hash(device_a)
    hash_a_dup = generate_fingerprint_hash(device_a)
    assert hash_a == hash_a_dup, "SHA-256 hash must be deterministic!"
    assert len(hash_a) == 64, f"SHA-256 hash length must be 64 chars, got {len(hash_a)}"
    print(f"\n--- 1. SHA-256 Fingerprint ID Generation ---")
    print(f"Generated SHA-256 Hash ID: {hash_a}")

    # 2. Test Similarity Algorithm
    match_a_a, _ = calculate_device_similarity(device_a, device_a)
    print(f"Device A vs Device A Match Percentage: {match_a_a}% (Expected: 100.0%)")
    assert match_a_a == 100.0

    match_a_b, bd_b = calculate_device_similarity(device_b, device_a)
    print(f"Device B (Browser Shift) vs Device A Match: {match_a_b}% (Expected: ~100.0%)")
    assert match_a_b >= 85.0

    match_a_c, bd_c = calculate_device_similarity(device_c, device_a)
    print(f"Device C (Spoofed Headless) vs Device A Match: {match_a_c}% (Expected: <30%)")
    assert match_a_c < 30.0

    # 3. Test Flask REST APIs via test client
    print(f"\n--- 3. Testing Flask REST Endpoints ---")
    client = app.test_client()

    # Test POST /api/device/fingerprint
    resp_reg = client.post("/api/device/fingerprint", json={
        "username": "test_device_user",
        "attributes": device_a,
    })
    print(f"POST /api/device/fingerprint Status: {resp_reg.status_code}")
    assert resp_reg.status_code == 201
    reg_json = resp_reg.get_json()
    assert reg_json["status"] == "success"

    # Test POST /api/device/verify (Same device)
    resp_ver_same = client.post("/api/device/verify", json={
        "username": "test_device_user",
        "attributes": device_a,
    })
    print(f"POST /api/device/verify (Same Device) Status: {resp_ver_same.status_code}")
    assert resp_ver_same.status_code == 200
    ver_same_json = resp_ver_same.get_json()
    assert ver_same_json["verification"]["risk_level"] == "Trusted"
    assert ver_same_json["verification"]["match_percentage"] == 100.0

    # Test POST /api/device/verify (Spoofed Bot Device C)
    resp_ver_bot = client.post("/api/device/verify", json={
        "username": "test_device_user",
        "attributes": device_c,
    })
    print(f"POST /api/device/verify (Spoofed Bot) Status: {resp_ver_bot.status_code}")
    assert resp_ver_bot.status_code == 200
    ver_bot_json = resp_ver_bot.get_json()
    assert ver_bot_json["verification"]["risk_level"] == "High Risk"
    assert ver_bot_json["verification"]["match_percentage"] < 50.0

    # Test GET /api/device/trusted-list
    resp_list = client.get("/api/device/trusted-list?username=test_device_user")
    print(f"GET /api/device/trusted-list Status: {resp_list.status_code}")
    assert resp_list.status_code == 200
    assert resp_list.get_json()["count"] >= 1

    # Test GET /api/device/history
    resp_hist = client.get("/api/device/history?username=test_device_user")
    print(f"GET /api/device/history Status: {resp_hist.status_code}")
    assert resp_hist.status_code == 200
    assert resp_hist.get_json()["count"] >= 2

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL DEVICE FINGERPRINTING ENGINE & API TESTS PASSED PERFECTLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_device_fingerprint_engine()
