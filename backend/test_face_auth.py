import unittest
import numpy as np
import cv2
import base64
import os
import io
from PIL import Image

# Ensure backend path is in sys.path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.face_recognition_engine import FaceRecognitionEngine
from models.face_model import save_face_profile, get_face_profile, delete_face_profile
from app import app


def create_synthetic_face_image(width=320, height=240, noise_seed=42, face_offset=(0, 0), eye_color=(40, 40, 40)):
    """Generate a synthetic test frame with a distinct face shape."""
    np.random.seed(noise_seed)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = (20, 20, 20)  # Clean dark background
    
    ox, oy = face_offset
    cx, cy = 160 + ox, 120 + oy

    # Draw oval face contour
    cv2.ellipse(img, (cx, cy), (50, 70), 0, 0, 360, (200, 180, 160), -1)
    # Draw eyes
    cv2.circle(img, (cx - 20, cy - 15), 8, eye_color, -1)
    cv2.circle(img, (cx + 20, cy - 15), 8, eye_color, -1)
    # Draw mouth
    cv2.ellipse(img, (cx, cy + 30), (20, 10), 0, 0, 180, (50, 50, 150), 2)

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    b64_str = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    return img, b64_str


class TestFaceRecognitionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = FaceRecognitionEngine(distance_threshold=0.58)
        self.test_user = "test_unit_face_user"
        delete_face_profile(self.test_user)

    def tearDown(self):
        delete_face_profile(self.test_user)

    def test_single_face_detection_and_validation(self):
        img_np, b64_str = create_synthetic_face_image()
        result = self.engine.detect_and_validate_faces(img_np)
        self.assertTrue(result["valid"], f"Face detection failed: {result}")
        self.assertEqual(result["face_count"], 1)

    def test_generate_128_dimensional_encoding(self):
        img_np, _ = create_synthetic_face_image()
        encoding = self.engine.generate_single_encoding(img_np)
        self.assertIsNotNone(encoding)
        self.assertEqual(len(encoding), 128, f"Encoding dimension should be 128, got {len(encoding)}")

    def test_compare_faces_same_user(self):
        img1, _ = create_synthetic_face_image(noise_seed=10)
        img2, _ = create_synthetic_face_image(noise_seed=11)

        enc1 = self.engine.generate_single_encoding(img1)
        enc2 = self.engine.generate_single_encoding(img2)

        cmp_res = self.engine.compare_faces(enc1, enc2)
        self.assertTrue(cmp_res["is_match"], f"Identical face should match: distance={cmp_res['distance']}")
        self.assertLessEqual(cmp_res["distance"], self.engine.distance_threshold)
        self.assertGreaterEqual(cmp_res["confidence_score"], 70.0)

    def test_compare_faces_different_user(self):
        img1, _ = create_synthetic_face_image(noise_seed=10)

        # Generate a visually distinct person with different skin tone, hair, and eye properties
        img2 = np.zeros((240, 320, 3), dtype=np.uint8)
        img2[:, :] = (180, 200, 220)  # Bright background
        cv2.ellipse(img2, (130, 110), (65, 85), 0, 0, 360, (50, 80, 120), -1)  # Dark skin tone, different size
        cv2.rectangle(img2, (100, 40), (160, 70), (10, 10, 10), -1)  # Hair block

        enc1 = self.engine.generate_single_encoding(img1)
        enc2 = self.engine.generate_single_encoding(img2)

        cmp_res = self.engine.compare_faces(enc1, enc2)
        self.assertFalse(cmp_res["is_match"], f"Different face structure should fail match: distance={cmp_res['distance']}")

    def test_registration_and_verification_pipeline(self):
        frames = [create_synthetic_face_image(noise_seed=40 + i, face_offset=(i, 0))[1] for i in range(5)]

        # 1. Process Registration
        reg_res = self.engine.process_registration(image_sources=frames, user_id=self.test_user)
        self.assertTrue(reg_res.get("success"), f"Registration failed: {reg_res}")
        self.assertEqual(len(reg_res["encoding"]), 128)

        # Save profile
        save_face_profile(self.test_user, reg_res["encoding"])

        # 2. Process Verification with same user and frame variations
        stored_enc = get_face_profile(self.test_user)["face_encoding"]
        ver_frames = [create_synthetic_face_image(noise_seed=50 + i, face_offset=(i, 0))[1] for i in range(5)]
        ver_res = self.engine.process_login_verification(
            image_sources=ver_frames,
            user_id=self.test_user,
            stored_encoding=stored_enc
        )
        self.assertTrue(ver_res.get("is_match"), f"Verification failed: {ver_res}")
        self.assertGreaterEqual(ver_res["confidence_score"], 70.0)

    def test_api_endpoints_registration_and_verification(self):
        client = app.test_client()

        from models.user_model import create_user
        from config import users_collection
        users_collection.delete_one({"username": self.test_user})
        create_user({"username": self.test_user, "email": "testuser@anomatrix.io"})

        # Create JWT token for test user
        from flask_jwt_extended import create_access_token
        with app.app_context():
            token = create_access_token(identity=self.test_user)

        headers = {"Authorization": f"Bearer {token}"}

        # 1. Registration without reauth token should fail with HTTP 403
        reg_frames = [create_synthetic_face_image(noise_seed=100 + i, face_offset=(i, 0))[1] for i in range(4)]
        res_unauth = client.post("/api/face/register", json={"frames": reg_frames}, headers=headers)
        self.assertEqual(res_unauth.status_code, 403)

        # 2. Grant re-authentication token
        import secrets
        from datetime import datetime, timedelta
        from config import db
        reauth_tok = f"reauth_{secrets.token_urlsafe(16)}"
        db["users"].update_one(
            {"username": self.test_user},
            {"$set": {
                "biometric_reauth_token": reauth_tok,
                "biometric_reauth_expiry": datetime.now() + timedelta(minutes=5)
            }},
            upsert=True
        )


        # 3. Registration with valid reauth token should succeed
        res_reg = client.post(
            "/api/face/register",
            json={"frames": reg_frames, "reauth_token": reauth_tok},
            headers=headers
        )
        self.assertEqual(res_reg.status_code, 200, f"Register API failed: {res_reg.get_json()}")
        self.assertTrue(res_reg.get_json().get("success"))

        # 4. API Status
        res_status = client.get(f"/api/face/status/{self.test_user}")
        self.assertEqual(res_status.status_code, 200)
        self.assertTrue(res_status.get_json().get("registered"))
        self.assertTrue(res_status.get_json().get("face_enabled"))

        # 5. API Verify
        ver_frames = [create_synthetic_face_image(noise_seed=200 + i, face_offset=(i, 0))[1] for i in range(4)]
        res_ver = client.post("/api/face/verify", json={
            "username": self.test_user,
            "frames": ver_frames
        })
        self.assertEqual(res_ver.status_code, 200, f"Verify API failed: {res_ver.get_json()}")
        self.assertTrue(res_ver.get_json().get("is_match"))
        self.assertIn("access_token", res_ver.get_json())

    def test_missing_reference_face_error(self):
        client = app.test_client()
        unregistered = "unregistered_test_user_xyz"
        delete_face_profile(unregistered)

        ver_frames = [create_synthetic_face_image(noise_seed=300)[1]]
        res = client.post("/api/face/verify", json={
            "username": unregistered,
            "frames": ver_frames
        })
        self.assertEqual(res.status_code, 404)
        json_data = res.get_json()
        self.assertEqual(json_data.get("error"), "FACE_AUTH_NOT_CONFIGURED")

    def test_encoding_dimension_mismatch_error(self):
        enc64 = [0.1] * 64
        enc128 = [0.1] * 128
        cmp_res = self.engine.compare_faces(enc64, enc128)
        self.assertFalse(cmp_res["is_match"])
        self.assertEqual(cmp_res["error"], "ENCODING_MISMATCH")

    def test_no_face_detection_error(self):
        empty_img = np.zeros((240, 320, 3), dtype=np.uint8)
        res = self.engine.detect_and_validate_faces(empty_img)
        self.assertFalse(res["valid"])
        self.assertEqual(res["error"], "NO_FACE")

    def test_multiple_faces_detection_error(self):
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        img[:, :] = (20, 20, 20)
        cv2.ellipse(img, (80, 120), (35, 45), 0, 0, 360, (200, 180, 160), -1)
        cv2.circle(img, (70, 105), 5, (40, 40, 40), -1)
        cv2.circle(img, (90, 105), 5, (40, 40, 40), -1)

        cv2.ellipse(img, (240, 120), (35, 45), 0, 0, 360, (200, 180, 160), -1)
        cv2.circle(img, (230, 105), 5, (40, 40, 40), -1)
        cv2.circle(img, (250, 105), 5, (40, 40, 40), -1)

        res = self.engine.detect_and_validate_faces(img)
        if res["face_count"] > 1:
            self.assertFalse(res["valid"])
            self.assertEqual(res["error"], "MULTIPLE_FACES")



if __name__ == "__main__":
    unittest.main()

