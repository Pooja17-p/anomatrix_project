# ANOMATRIX Zero-Trust Keystroke Dynamics Authentication

Complete technical specification and documentation for the **Keystroke Dynamics Authentication Module** in the **ANOMATRIX Zero-Trust Security System**.

---

## 1. Executive Summary & Architecture Overview

The **ANOMATRIX Keystroke Dynamics Authentication** engine establishes continuous user authenticity verification by capturing high-frequency keyboard biometrics (Key Press Time, Key Release Time, Key Hold Time, Inter-Key Flight Time, Typing Speed WPM, Rhythm Consistency Variance, and Backspace Error Rate).

Using an **Isolation Forest Unsupervised Machine Learning Model** combined with Exponential Moving Average (EMA) baseline user profiling, the system evaluates typing dynamics every 3–4 seconds, generating a dynamic **Trust Score (0–100)** and classifying session state as **Trusted**, **Suspicious**, or **Anomalous**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ANOMATRIX FRONTEND                                     │
│  - Continuous Keyboard Event Capture (keydown / keyup)                                 │
│  - Hold Time (Release - Press), Flight Time (Inter-Press Latency), WPM                 │
│  - Keystroke Dynamics Security Dashboard & Live Biometric Sampler                      │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │ 3-4s Window Telemetry Payload
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FLASK BACKEND SERVICES                                 │
│  - POST /keystroke-data       (Ingestion & Profile EMA Updating)                       │
│  - POST /keystroke/train      (Isolation Forest Model Training)                        │
│  - POST /keystroke/predict    (Isolation Forest Inference & Macro Bot Filtering)       │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │ Persist Telemetry & Session State
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MONGODB DATA ENGINE                                    │
│  - keystroke_logs     : Full historical telemetry & AI decision logs                   │
│  - keystroke_sessions : Live session state, trust score & packet counters              │
│  - keystroke_profiles : Moving average baseline features for every user                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Folder Structure

```
anomatrix-zero-trust-security/
├── backend/
│   ├── app.py                         # Flask Server Entrypoint & Blueprint Registration
│   ├── config.py                      # MongoDB Connection & Collections Configuration
│   ├── models/
│   │   └── keystroke_model.py         # MongoDB Operations & In-Memory Fallback Store
│   ├── routes/
│   │   └── keystroke_auth.py          # Flask REST Blueprints (/keystroke-data, /train, /predict, /history)
│   ├── service/
│   │   └── keystroke_engine.py        # Isolation Forest ML Model, StandardScaler & Feature Extraction
│   ├── test_keystroke_auth.py         # Automated Test Suite for Keystroke APIs & ML Engine
│   └── ml_models/                     # Trained Joblib Model Pipelines (.joblib)
└── frontend/
    └── src/
        ├── components/
        │   ├── KeystrokeMetricsGrid.jsx # Stat Cards Grid (WPM, Hold, Flight, Rhythm, Error Rate)
        │   ├── KeystrokeTrustGauge.jsx  # SVG Circular Trust Score Meter & AI Verdict Card
        │   ├── KeystrokeRhythmChart.jsx # Chart.js Latency Trends Line Chart
        │   ├── KeystrokeActivityTable.jsx# Log History Table with Search & Filter
        │   └── KeystrokeWidget.jsx      # Floating Zero-Trust Status Pill Widget
        ├── hooks/
        │   └── useKeystrokeTracker.js   # Background Keystroke Dynamics Capture Hook
        └── pages/
            └── KeystrokeDashboardPage.js # Main Responsive Keystroke Security Dashboard Page
```

---

## 3. Behavioral Feature Extraction & Machine Learning Flow

### Feature Vector Composition
The system extracts 6 behavioral feature indicators from raw keyboard events:

1. **`hold_time`**: Mean key press duration ($\text{Release Time} - \text{Press Time}$) in milliseconds ($\text{ms}$).
2. **`flight_time`**: Mean time between consecutive keypresses ($\text{Press}_i - \text{Release}_{i-1}$) in milliseconds ($\text{ms}$).
3. **`typing_speed`**: Typing velocity in Words Per Minute ($\text{WPM}$):
   $$\text{WPM} = \left(\frac{N_{\text{keypresses}}}{5}\right) \times \left(\frac{60}{T_{\text{window}}}\right)$$
4. **`rhythm_variance`**: Standard deviation of flight and hold latencies ($\text{std}(\text{flight\_times})$).
5. **`error_rate`**: Backspace and Delete usage ratio ($\frac{N_{\text{backspace}}}{N_{\text{total}}}$).
6. **`total_keypresses`**: Total keys pressed in the interval window.

### Isolation Forest Model Inference
- **Scaling**: Standardized using `sklearn.preprocessing.StandardScaler`.
- **Inference**: Evaluated using `IsolationForest` ($N=100$ decision trees, contamination $= 0.08$).
- **Score Mapping**: Raw anomaly decision function score mapped to a normalized **Trust Score** $(0 - 100)$:
  $$\text{Trust Score} = \text{clip}\left(50 + (\text{decision\_function}(X) \times 100), 10, 100\right)$$
- **Bot Macro Filter**: Script paste / automated injection override ($v > 250\text{WPM}$, or $N>10$, $\text{rhythm}<1\text{ms}$, $\text{hold}<5\text{ms}$) forces trust score to $\le 15$.

---

## 4. MongoDB Database Schemas

### 1. `keystroke_logs` Collection
```json
{
  "_id": "ObjectId('66a13a...')",
  "username": "john_doe",
  "session_id": "key_sess_8f3a12_1721832000000",
  "biometrics": {
    "hold_time": 87.6,
    "flight_time": 135.0,
    "typing_speed": 75.0,
    "rhythm_variance": 13.04,
    "error_rate": 0.04,
    "total_keypresses": 25,
    "total_errors": 1
  },
  "trust_score": 96,
  "status": "Trusted",
  "model_used": "IsolationForest",
  "timestamp": "2026-07-24T19:30:00.000Z",
  "created_at": "2026-07-24T19:30:00.000Z"
}
```

### 2. `keystroke_sessions` Collection
```json
{
  "_id": "ObjectId('66a13b...')",
  "session_id": "key_sess_8f3a12_1721832000000",
  "username": "john_doe",
  "created_at": "2026-07-24T19:00:00.000Z",
  "last_updated": "2026-07-24T19:30:00.000Z",
  "typing_score": 96,
  "status": "Trusted",
  "total_packets": 85
}
```

### 3. `keystroke_profiles` Collection
Maintains user baseline typing profiles updated via Exponential Moving Average (EMA, $\alpha=0.2$):
```json
{
  "_id": "ObjectId('66a13c...')",
  "username": "john_doe",
  "avg_hold_time": 89.2,
  "avg_flight_time": 138.4,
  "avg_typing_speed": 72.5,
  "rhythm_variance": 15.1,
  "error_rate": 0.035,
  "total_samples": 320,
  "last_updated": "2026-07-24T19:30:00.000Z"
}
```

---

## 5. REST APIs

```
POST /keystroke-data        - Store telemetry & update baseline EMA profile
POST /keystroke/train       - Train user-specific Isolation Forest model
POST /keystroke/predict     - Execute Isolation Forest inference & return Trust Score
GET  /keystroke/history     - Retrieve historical typing telemetry logs
GET  /keystroke/profile     - Fetch historical baseline typing profile
GET  /keystroke/score       - Retrieve latest typing similarity score & status
```
