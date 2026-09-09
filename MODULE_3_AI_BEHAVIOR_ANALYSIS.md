# Module 3 – AI Behavior Analysis Architecture

Complete implementation reference and technical specification for **Module 3 – AI Behavior Analysis** in the **ANOMATRIX Zero-Trust Security Platform**.

---

```
Module 3 – AI Behavior Analysis
├── 3.1 Mouse Motion Data Collection
├── 3.2 Mouse Feature Extraction
├── 3.3 Isolation Forest AI Model
├── 3.4 Flask REST APIs
├── 3.5 Dashboard Visualization
└── 3.6 Continuous Authentication Engine
```

---

## 3.1 Mouse Motion Data Collection

### Implementation File
- [useMouseMotionTracker.js](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/hooks/useMouseMotionTracker.js)
- [useMouseTracker.js](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/hooks/useMouseTracker.js)

### Technical Details
- **Passive Event Listeners**: High-frequency passive event listeners (`mousemove`, `click`, `scroll`) hooked to `window` with non-blocking `{ passive: true }` execution.
- **Sampling Throttling**: Throttles mouse point sampling to $>10\text{ms}$ steps ($~100\text{Hz}$) to ensure pixel-perfect kinematic precision without frame lag.
- **Trajectory Buffer**: Stores coordinate tuples $(x_i, y_i, t_i, v_i, a_i, \theta_i)$ in a non-rendering `useRef` telemetry buffer to eliminate unnecessary React re-renders.
- **Windowing**: Packages collected samples every 3–5 seconds into window telemetry payloads transmitted to the Flask REST API.

```javascript
// High-Frequency Passive Listener Code
window.addEventListener("mousemove", handleMouseMove, { passive: true });
window.addEventListener("click", handleClick, { passive: true });
window.addEventListener("scroll", handleScroll, { passive: true });
```

---

## 3.2 Mouse Feature Extraction

### Implementation File
- [mouse_engine.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/service/mouse_engine.py) (`compute_mouse_kinematics`)

### Mathematical Formulas & Extracted Features
The system processes raw coordinate arrays to extract 7 core behavioral features:

| Feature Key | Description | Mathematical Expression |
| :--- | :--- | :--- |
| **`speed`** | Mean velocity ($px/s$) | $\bar{v} = \frac{1}{N}\sum \frac{\sqrt{\Delta x^2 + \Delta y^2}}{\Delta t}$ |
| **`acceleration`** | Mean acceleration ($px/s^2$) | $\bar{a} = \frac{1}{N}\sum \frac{|\Delta v|}{\Delta t}$ |
| **`direction`** | Mean movement angle | $\bar{\theta} = \frac{1}{N}\sum \left[\left(\text{atan2}(\Delta y, \Delta x) \times \frac{180}{\pi} + 360\right) \bmod 360\right]$ |
| **`direction_variance`** | Angular entropy / variance | $\text{Var}(\theta) = \frac{1}{N}\sum (\theta_i - \bar{\theta})^2$ |
| **`straightness_ratio`** | Line directness ratio | $S = \frac{\sqrt{(x_N-x_0)^2 + (y_N-y_0)^2}}{\sum \sqrt{\Delta x^2 + \Delta y^2}} \in [0, 1]$ |
| **`click_rate`** | Clicks per second | $C_{\text{rate}} = \frac{N_{\text{clicks}}}{T_{\text{window}}}$ |
| **`scroll_speed`** | Scroll events per second | $S_{\text{speed}} = \frac{N_{\text{scrolls}}}{T_{\text{window}}}$ |

---

## 3.3 Isolation Forest AI Model

### Implementation File
- [mouse_engine.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/service/mouse_engine.py) (`train_mouse_model`, `predict_trust_score`)

### AI Model Architecture
- **Algorithm**: Unsupervised Anomaly Detection using `sklearn.ensemble.IsolationForest`.
- **Hyperparameters**:
  - `n_estimators`: 100 decision trees
  - `contamination`: 0.08 (8% expected anomaly rate)
  - `random_state`: 42
- **Feature Normalization**: Inputs scaled with `sklearn.preprocessing.StandardScaler`.
- **Trust Score Formula**:
  $$\text{Trust Score} = \text{clip}\left(50 + (\text{decision\_function}(X) \times 100), 10, 100\right)$$
- **Bot/Macro Filter**: Heuristic override flags instant line moves ($v > 4000\text{px/s}$, $S > 0.99$, $a < 0.1$) as automated scripts, dropping score to $\le 15$.
- **Model Persistence**: Pipelines saved per user to disk as `backend/ml_models/mouse_model_<username>.joblib`.

---

## 3.4 Flask REST APIs

### Implementation File
- [mouse_auth.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/routes/mouse_auth.py)

### API Endpoint Registry

```
POST /api/mouse/predict           - Isolation Forest Inference & Bot Filter
POST /api/mouse/mouse-data        - Telemetry Ingestion & Kinematic Calculation
POST /api/mouse/train             - Train User-Specific Isolation Forest Model
POST /api/mouse/step-up-verify    - Face / OTP Verification Challenge Handler
GET  /api/mouse/history           - Retrieve Historical Telemetry Logs
GET  /api/mouse/profile           - Fetch Exponential Moving Average Baseline
```

#### Example Response (`POST /api/mouse/predict`)
```json
{
  "status": "success",
  "user_id": "john_doe",
  "trust_score": 94,
  "mouse_score": 94,
  "security_status": "Trusted",
  "is_anomaly": false,
  "model_used": "IsolationForest",
  "features": {
    "speed": 380.45,
    "acceleration": 95.12,
    "direction": 178.5,
    "direction_variance": 42.1,
    "straightness_ratio": 0.8542,
    "click_rate": 0.5,
    "scroll_speed": 1.2
  },
  "predicted_at": "2026-07-24T19:25:00.000Z"
}
```

---

## 3.5 Dashboard Visualization

### Implementation Files
- [MouseDashboardPage.js](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/pages/MouseDashboardPage.js)
- [MousePathCanvas.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/MousePathCanvas.jsx)
- [TrustScoreGauge.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/TrustScoreGauge.jsx)
- [MovementStatsGrid.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/MovementStatsGrid.jsx)
- [TelemetryCharts.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/TelemetryCharts.jsx)
- [RecentActivityTable.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/RecentActivityTable.jsx)

### Visualization Features
1. **Interactive Path Canvas**: Real-time cursor motion path with Bézier curves, velocity heatmaps, click ripples, crosshairs, and canvas controls.
2. **SVG Circular Trust Gauge**: 0–100 Trust Score meter, Risk Level badges (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), AI Verdict, and Risk Factor checklist.
3. **Kinematic Metrics Grid**: Stat cards displaying Live $(X, Y)$ position, Current Speed, Avg Speed, Peak Velocity, Acceleration, Distance, Curvature Index, Clicks, and Scrolls.
4. **Chart.js Analytics**: Multi-line velocity trend chart and trust score distribution bar chart.
5. **Activity Log Table**: Chronological telemetry event history with search, risk filters, auto-refresh countdown, and manual sync.

---

## 3.6 Continuous Authentication Engine

### Implementation Files
- [StepUpAuthModal.jsx](file:///c:/Users/HP/anomatrix-zero-trust-security/frontend/src/components/StepUpAuthModal.jsx)
- [mouse_model.py](file:///c:/Users/HP/anomatrix-zero-trust-security/backend/models/mouse_model.py)

### Zero-Trust Evaluation Loop
1. **Continuous Verification**: Evaluates mouse kinematics in 3.5-second sliding windows.
2. **Threshold Monitoring**:
   - **Score $\ge 80$**: `Trusted` (Low Risk)
   - **$55 \le \text{Score} < 80$**: `Suspicious` (Medium Risk)
   - **Score $< 55$**: `Anomalous` / `Critical` -> **Triggers Step-Up Authentication Modal**.
3. **Step-Up Challenge Execution**: Automatically presents `StepUpAuthModal` blocking user actions until **Face Biometric Scan** or **OTP Verification** is passed.
4. **Baseline EMA Profile Updating**: Dynamically updates the user's historical profile in MongoDB (`mouse_profiles`) using Exponential Moving Average ($\alpha = 0.2$):
   $$\text{Profile}_{\text{new}} = (1 - \alpha)\text{Profile}_{\text{old}} + \alpha \times \text{Feature}_{\text{current}}$$
