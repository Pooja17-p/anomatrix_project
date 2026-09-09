# ANOMATRIX Zero-Trust Continuous Mouse Authentication

This document provides complete technical documentation for the **Continuous Mouse Motion Authentication System** in ANOMATRIX.

---

## 1. Executive Summary & Architecture Overview

The **ANOMATRIX Continuous Mouse Motion Authentication** engine establishes a continuous, zero-trust security perimeter by continuously analyzing user mouse kinematics (coordinates, speed, acceleration, straightness ratio, angular variations, clicks, and scroll behavior). 

Using an **Isolation Forest Unsupervised Machine Learning Model** combined with Exponential Moving Average (EMA) baseline user profiling, the system predicts user authenticity every 3–4 seconds. If a user's **Trust Score** drops below the security threshold (< 55), the system automatically triggers a **Step-Up Authentication Challenge** (Face Biometrics or OTP), requiring verification before granting continued session access.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ANOMATRIX FRONTEND                                     │
│  - Continuous Capture (>120Hz)                                                         │
│  - Trajectory Buffer & Kinematic Feature Extraction                                   │
│  - Live HTML5 Canvas Motion Trajectory & Real-Time Dashboard                           │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │ 3-4s Window Telemetry Payload
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FLASK BACKEND SERVICES                                 │
│  - POST /api/mouse/predict  (Isolation Forest Inference)                               │
│  - POST /api/mouse/step-up-verify (Biometric / OTP Verification)                      │
│  - EMA Baseline Profile Update & Kinematics Calculator                                 │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │ Persist Telemetry & Session State
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MONGODB DATA ENGINE                                    │
│  - mouse_logs      : Full historical telemetry & AI decision logs                      │
│  - mouse_sessions  : Live session state, trust score & packet counters                 │
│  - mouse_profiles  : Moving average baseline features for every user                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Folder Structure

```
anomatrix-zero-trust-security/
├── backend/
│   ├── app.py                         # Flask Server Entrypoint & Blueprint Registration
│   ├── config.py                      # MongoDB Database Connection & PyMongo Collections
│   ├── models/
│   │   └── mouse_model.py             # MongoDB Operations & In-Memory Resilience Fallback
│   ├── routes/
│   │   └── mouse_auth.py              # Flask REST Blueprints (/predict, /track, /step-up-verify, /history)
│   ├── service/
│   │   └── mouse_engine.py            # Isolation Forest ML Engine, StandardScaler & Kinematics Math
│   └── ml_models/                     # Trained Joblib Model Pipelines (.joblib)
└── frontend/
    ├── public/                        # Public index.html template with Tailwind CSS CDN
    └── src/
        ├── components/
        │   ├── StepUpAuthModal.jsx    # Step-Up Verification Challenge Modal (Face / OTP)
        │   ├── MouseTrackerWidget.jsx # Floating Zero-Trust Status Widget
        │   ├── MousePathCanvas.jsx    # HTML5 Canvas Real-Time Motion Trajectory
        │   ├── TrustScoreGauge.jsx    # SVG Circular Trust Gauge & AI Prediction Card
        │   ├── MovementStatsGrid.jsx    # Stat Cards Grid (Speed, Accel, Distance, Curvature)
        │   ├── TelemetryCharts.jsx    # Chart.js Velocity Trends & Risk Distribution
        │   └── RecentActivityTable.jsx# Log History Table with Search & Filter
        ├── hooks/
        │   ├── useMouseTracker.js     # Background Mouse Tracking & Step-Up Trigger Hook
        │   └── useMouseMotionTracker.js # Dashboard Specific Telemetry Hook
        └── pages/
            └── MouseDashboardPage.js  # Main Mouse Motion Security Dashboard Page
```

---

## 3. Kinematic Feature Extraction & Machine Learning Flow

### Feature Vector Composition
The system extracts 7 kinematic feature indicators from mouse sampling points:

1. **`speed`**: Mean instantaneous velocity ($\text{px}/\text{s}$) defined as:
   $$\text{speed} = \frac{\sqrt{\Delta x^2 + \Delta y^2}}{\Delta t}$$
2. **`acceleration`**: Rate of velocity change ($\text{px}/\text{s}^2$):
   $$\text{accel} = \frac{|\text{speed}_i - \text{speed}_{i-1}|}{\Delta t}$$
3. **`direction`**: Mean movement direction angle in degrees $[0^\circ, 360^\circ)$.
4. **`direction_variance`**: Angular deviation variance ($\text{var}(\theta)$).
5. **`straightness_ratio`**: Ratio of Euclidean end-to-end distance to total path distance:
   $$\text{straightness} = \frac{D_{\text{euclidean}}}{D_{\text{path}}} \in (0, 1]$$
6. **`click_rate`**: Frequency of mouse clicks per second ($\text{clicks}/\text{s}$).
7. **`scroll_speed`**: Frequency of scroll wheel events per second ($\text{scrolls}/\text{s}$).

### Isolation Forest Model Inference
- **Scaling**: Standardized using `sklearn.preprocessing.StandardScaler`.
- **Inference**: Evaluated using `IsolationForest` ($N=100$ estimators, contamination rate $= 0.08$).
- **Score Mapping**: The raw `decision_function` score is mapped to a normalized **Trust Score** $(0 - 100)$:
  $$\text{Trust Score} = \text{clip}\left(50 + (\text{decision\_score} \times 100), 10, 100\right)$$

---

## 4. MongoDB Database Schemas

### 1. `mouse_logs` Collection
Stores every raw telemetry packet and prediction result:
```json
{
  "_id": "ObjectId('66a12b...')",
  "username": "user123",
  "session_id": "mouse_sess_8f3a12_1721832000000",
  "kinematics": {
    "speed": 380.45,
    "acceleration": 95.12,
    "direction": 178.5,
    "direction_variance": 42.1,
    "straightness_ratio": 0.8542,
    "click_rate": 0.5,
    "scroll_speed": 1.2
  },
  "mouse_score": 94,
  "status": "Trusted",
  "model_used": "IsolationForest",
  "timestamp": "2026-07-24T19:15:00.000Z",
  "created_at": "2026-07-24T19:15:00.000Z"
}
```

### 2. `mouse_sessions` Collection
Tracks active zero-trust session states:
```json
{
  "_id": "ObjectId('66a12c...')",
  "session_id": "mouse_sess_8f3a12_1721832000000",
  "username": "user123",
  "created_at": "2026-07-24T19:00:00.000Z",
  "last_updated": "2026-07-24T19:15:00.000Z",
  "mouse_score": 94,
  "status": "Trusted",
  "total_packets": 140
}
```

### 3. `mouse_profiles` Collection
Maintains user baseline motion profiles updated via Exponential Moving Average (EMA, $\alpha=0.2$):
```json
{
  "_id": "ObjectId('66a12d...')",
  "username": "user123",
  "avg_speed": 365.2,
  "avg_acceleration": 92.4,
  "avg_direction": 182.1,
  "direction_variance": 44.0,
  "click_rate": 0.48,
  "scroll_speed": 1.8,
  "total_samples": 450,
  "last_updated": "2026-07-24T19:15:00.000Z"
}
```

---

## 5. Step-Up Authentication Workflow

When `mouse_score < 55`:
1. `useMouseTracker.js` sets `isStepUpRequired = true`.
2. `StepUpAuthModal.jsx` opens over the UI blocking unauthorized user actions.
3. User selects either **OTP Verification** (6-digit passcode) or **Face Verification** (Webcam scan simulation).
4. On submission, frontend calls `POST /api/mouse/step-up-verify`.
5. Backend verifies payload, restores session Trust Score to `100`, updates status to `Trusted`, logs security event in MongoDB, and closes modal.

---

## 6. Best Practices & Low-Latency Optimization

1. **Passive Telemetry Listener**: Event listeners use `{ passive: true }` for non-blocking 60fps/120fps mouse movement capture.
2. **Buffer References (`useRef`)**: Coordinates and points are accumulated in `useRef` buffers to prevent React re-renders during high frequency cursor movements.
3. **Resilient MongoDB Fallback**: In-memory database fallback (`_in_memory_logs`) ensures seamless execution even if MongoDB is restarting or offline during local dev.
4. **Optimized Model Caching**: `joblib.load()` caches trained Isolation Forest pipelines in memory for sub-millisecond inference times.
