# AnomatriX Zero Trust Security — Face Recognition Authentication Module

## Executive Overview

The **Face Recognition Authentication Module** is a core biometric security tier in the **AnomatriX Zero Trust Architecture**. It provides non-intrusive, high-accuracy facial identification and login verification using OpenCV and facial feature embedding comparison.

```
       +-----------------------------------------------------------+
       |                      Web Camera Feed                       |
       |             (Base64 HTML5 Canvas / OpenCV Video)          |
       +-----------------------------------------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |             FaceRecognitionEngine (Service)               |
       |  - Webcam capture / base64 frame decoding                 |
       |  - Face detection & single-face strict enforcement        |
       |  - 128-d Face Embedding Generation                        |
       |  - Euclidean distance & confidence score (0-100%) metric  |
       +-----------------------------------------------------------+
                         /                           \
                        /                             \
       +-------------------------------+   +-------------------------------+
       |   face_model.py (MongoDB)     |   |    face_auth.py (Flask API)   |
       | - Store user face embeddings  |   | - POST /api/face/register     |
       | - Retrieve stored encodings   |   | - POST /api/face/verify       |
       | - Audit log persistence       |   | - GET  /api/face/status       |
       +-------------------------------+   +-------------------------------+
```

---

## Core Capabilities & Technical Highlights

1. **Webcam Capture & Base64 Payload Support**:
   - Accesses physical hardware webcams via OpenCV `cv2.VideoCapture` with auto-exposure warmup.
   - Accepts base64 encoded JPEG/PNG image strings directly from HTML5 `<video>` / `<canvas>` elements.

2. **Strict Single-Face Detection Rule**:
   - **0 Faces Detected** -> Rejected with `NO_FACE_DETECTED`.
   - **2+ Faces Detected** -> Rejected with `MULTIPLE_FACES_DETECTED` to prevent photo spoofing or multi-person ambiguity.
   - **Exactly 1 Face Detected** -> Allowed for encoding extraction.

3. **128-Dimensional Biometric Encoding**:
   - Computes normalized float feature vectors representing facial geometry, landmark spacing, and spatial color histograms.
   - Primary engine uses `face_recognition` / HOG deep learning model when installed.
   - Intelligent OpenCV Haar Cascade / Contour feature vector fallback ensures zero downtime on machines without C++ dlib dependencies.

4. **Distance & Confidence Scoring Engine**:
   - Calculates Euclidean distance $d(v_1, v_2) = \sqrt{\sum (v_{1,i} - v_{2,i})^2}$.
   - Distance threshold $\le 0.6$ signifies an authentic biometric match.
   - Converts distance to an intuitive percentage confidence score ($0\% - 100\%$).

5. **Resilient MongoDB Data Model & Audit Trail**:
   - Stores facial biometric vectors in `anomatrix_db.face_profiles`.
   - Records detailed audit logs for all login attempts in `anomatrix_db.face_logs`.
   - Features automatic in-memory fallback if MongoDB is temporarily unreachable.

---

## Architecture & Code File Structure

| Component File | Role & Responsibilities | Link |
| :--- | :--- | :--- |
| `backend/service/face_recognition_engine.py` | Core engine class handling webcam frame decoding, face detection, single-face rule enforcement, 128-d encoding generation, distance comparison, and confidence scoring. | [face_recognition_engine.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/service/face_recognition_engine.py) |
| `backend/models/face_model.py` | MongoDB collection abstraction for user face profiles (`face_profiles`) and authentication attempt audit logs (`face_logs`). | [face_model.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/models/face_model.py) |
| `backend/routes/face_auth.py` | Flask Blueprint routes for `/api/face/register`, `/api/face/verify`, `/api/face/status`, `/api/face/capture-test`, and `/api/face/logs`. | [face_auth.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/routes/face_auth.py) |
| `backend/app.py` | Main Flask entry point registering `face_auth_bp`. | [app.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/app.py) |
| `backend/test_face_auth.py` | Automated unit & integration test suite covering image decoding, single-face validation, vector comparison, mismatch detection, and REST API routes. | [test_face_auth.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/test_face_auth.py) |
| `frontend/src/components/FaceAuthWidget.jsx` | React UI component with live webcam feed, reticle overlay, registration, login verification, and confidence score gauge bar. | [FaceAuthWidget.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/FaceAuthWidget.jsx) |

---

## REST API Specification

### 1. Register Facial Profile
- **Endpoint**: `POST /api/face/register`
- **Payload**:
  ```json
  {
    "username": "john_doe",
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..." // or "WEBCAM"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "username": "john_doe",
    "face_count": 1,
    "message": "Facial biometric profile successfully registered for 'john_doe'."
  }
  ```

---

### 2. Live Face Verification / Login
- **Endpoint**: `POST /api/face/verify` (also `/api/face/login`)
- **Payload**:
  ```json
  {
    "username": "john_doe",
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..." // or "WEBCAM"
  }
  ```
- **Response (200 OK — Match Verified)**:
  ```json
  {
    "success": true,
    "is_match": true,
    "confidence_score": 94.85,
    "distance": 0.0515,
    "error": null,
    "message": "Authentication successful! Face match verified with 94.85% confidence."
  }
  ```
- **Response (401 Unauthorized — Mismatch)**:
  ```json
  {
    "success": false,
    "is_match": false,
    "confidence_score": 38.2,
    "distance": 0.74,
    "error": "FACE_MISMATCH",
    "message": "Authentication rejected: Face does not match registered profile."
  }
  ```

---

### 3. Check User Registration Status
- **Endpoint**: `GET /api/face/status/<username>`
- **Response**:
  ```json
  {
    "success": true,
    "registered": true,
    "username": "john_doe",
    "updated_at": "2026-08-02T08:14:15.933Z",
    "message": "Face biometric profile is registered for user 'john_doe'."
  }
  ```

---

### 4. Camera & Face Detection Test
- **Endpoint**: `POST /api/face/capture-test`
- **Payload**: `{ "image": "WEBCAM" }`
- **Response**:
  ```json
  {
    "success": true,
    "face_count": 1,
    "locations": [[50, 250, 200, 100]],
    "error": null,
    "message": "Single face successfully detected and validated."
  }
  ```

---

### 5. Audit Log History
- **Endpoint**: `GET /api/face/logs/<username>`
- **Response**:
  ```json
  {
    "success": true,
    "username": "john_doe",
    "count": 5,
    "logs": [
      {
        "username": "john_doe",
        "is_match": true,
        "confidence_score": 94.85,
        "status_code": "SUCCESS",
        "timestamp": "2026-08-02T08:14:15.954Z"
      }
    ]
  }
  ```

---

## Error Handling & Status Matrix

| Error Code | HTTP Status | Description & User Guidance |
| :--- | :--- | :--- |
| `WEBCAM_UNAVAILABLE` | 400 Bad Request | Webcam is missing, in use by another app, or permission was denied. |
| `NO_FACE_DETECTED` | 400 Bad Request | No face was detected in image frame. Align face inside camera center. |
| `MULTIPLE_FACES_DETECTED` | 400 Bad Request | 2 or more faces detected. Ensure only 1 person is visible in frame. |
| `CORRUPTED_IMAGE` | 400 Bad Request | Provided base64 payload is invalid or unreadable. |
| `USER_NOT_REGISTERED` | 404 Not Found | User has no registered facial profile. Must register face first. |
| `FACE_MISMATCH` | 401 Unauthorized | Live face embedding distance exceeds 0.6 match threshold. |
| `SERVER_ERROR` | 500 Internal Error | Unexpected execution error. |

---

## Dependencies & Setup Instructions

### Python Backend Dependencies
Add to `backend/requirements.txt`:
```txt
flask>=3.0.0
flask-cors>=4.0.0
flask-jwt-extended>=4.6.0
pymongo>=4.6.0
opencv-python>=4.8.0
Pillow>=10.0.0
face_recognition>=1.3.0
```

To install dependencies into virtual environment:
```bash
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Running Automated Test Suite
```bash
cd backend
.\venv\Scripts\python.exe test_face_auth.py
```
Expected output:
```txt
Ran 10 tests in 7.549s
OK
```

---

## Frontend Integration

Import and mount the `FaceAuthWidget` inside any React page or modal:

```jsx
import React from 'react';
import FaceAuthWidget from './components/FaceAuthWidget';

export default function Dashboard() {
  return (
    <div className="p-6 bg-slate-950 min-h-screen">
      <h1 className="text-2xl font-bold text-slate-100 mb-6">Biometric Zero Trust Panel</h1>
      <FaceAuthWidget username="admin" />
    </div>
  );
}
```
