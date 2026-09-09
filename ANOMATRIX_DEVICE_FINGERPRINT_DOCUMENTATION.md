# ANOMATRIX Zero-Trust Device Fingerprinting Framework

Complete technical specification and documentation for the **Device Fingerprinting Module** in the **ANOMATRIX Zero-Trust Security Platform**.

---

## 1. Executive Summary & Architecture Overview

The **ANOMATRIX Device Fingerprinting Framework** implements continuous hardware and browser biometric verification. It captures 15+ browser attributes (HTML5 Canvas Signature, WebGL GPU Vendor & Renderer, Hardware Concurrency, Device Memory, Screen Resolution, Color Depth, Timezone, Language, Operating System, and Network Info).

The framework generates a deterministic **SHA-256 Fingerprint ID** and evaluates incoming biometrics against known user baseline profiles using a **weighted fuzzy similarity matching algorithm**. Instead of rigid binary exact matching, the system classifies devices as **Trusted** ($\ge 85\%$), **Medium Risk** ($55\% - 84\%$), or **High Risk** ($< 55\%$), accommodating legitimate browser updates without false positives.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ANOMATRIX FRONTEND                                     │
│  - deviceFingerprint.js   (HTML5 Canvas Hash, WebGL GPU Renderer, CPU, RAM, Screen)    │
│  - useDeviceFingerprint.js (Continuous Biometric Extraction & Verification Hook)       │
│  - devices.js             (Device Fingerprinting Dashboard & Similarity Gauge)         │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │ 
                                  ▼ POST /api/device/verify
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FLASK BACKEND SERVICES                                 │
│  - device_fingerprint_engine.py (SHA-256 Hashing, Weighted Fuzzy Similarity Matcher)    │
│  - device_fingerprint.py        (REST Blueprint: /fingerprint, /verify, /trusted-list) │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │ Persist Fingerprints & Audit History
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MONGODB DATA ENGINE                                    │
│  - device_fingerprints  : Known baseline fingerprints per user (SHA-256 ID, WebGL, etc)  │
│  - device_trust_history : Historical verification events & match percentages           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Folder Structure

```
anomatrix-zero-trust-security/
├── backend/
│   ├── app.py                            # Blueprint Registration (/api/device)
│   ├── config.py                         # MongoDB Client Connection & is_db_connected Helper
│   ├── models/
│   │   └── device_model.py               # MongoDB Persistence (device_fingerprints, device_trust_history)
│   ├── service/
│   │   └── device_fingerprint_engine.py   # SHA-256 Hashing & Weighted Similarity Engine
│   ├── routes/
│   │   └── device_fingerprint.py         # Flask REST Blueprint (/fingerprint, /verify, /revoke)
│   └── test_device_fingerprint.py        # Automated Test Suite for Device Fingerprinting
└── frontend/
    └── src/
        ├── utils/
        │   └── deviceFingerprint.js      # Client Biometrics Extractor (Canvas, WebGL, Hardware)
        ├── hooks/
        │   └── useDeviceFingerprint.js    # React Custom Verification Hook
        ├── components/
        │   ├── DeviceMetricsGrid.jsx     # Metric Cards (SHA-256 ID, Browser/OS, Hardware, Canvas)
        │   ├── DeviceSimilarityGauge.jsx # SVG Circular Match Score Gauge & Breakdown Grid
        │   └── DeviceHistoryTable.jsx    # Trusted Devices Manager & Revocation Audit Logs
        └── pages/
            └── devices.js                # Main Device Fingerprinting Dashboard Page
```

---

## 3. Weighted Fuzzy Similarity Algorithm

The similarity engine computes a match score between incoming attributes ($X_{\text{inc}}$) and user baseline attributes ($X_{\text{base}}$):

$$\text{Similarity Score} = \sum_{i=1}^{n} w_i \cdot S_i(X_{\text{inc}}, X_{\text{base}})$$

### Category Weights & Attribute Breakdown
1. **HTML5 Canvas Signature Hash ($25\%$)**: Hash of invisible canvas rendering containing text, gradients, and geometric curves.
2. **WebGL GPU Vendor & Renderer ($25\%$)**: Unmasked graphics card renderer string from `WEBGL_debug_renderer_info`.
3. **Hardware Specs ($20\%$)**: Combined evaluation of CPU cores (`hardwareConcurrency`), RAM memory (`deviceMemory`), and Screen Resolution.
4. **Operating System & Platform ($15\%$)**: OS family and platform architecture (`Win32`, `MacIntel`, `Linux`).
5. **Timezone & Language ($10\%$)**: Resolved IANA timezone (`Asia/Kolkata`) and language locale (`en-US`).
6. **User Agent Browser Family ($5\%$)**: Browser name (`Chrome`, `Firefox`, `Safari`, `Edge`).

### Risk Level Classification
- **$\ge 85.0\%$**: `Trusted` (Low Risk) - Legitimate user device.
- **$55.0\% - 84.9\%$**: `Medium Risk` - Partial shift detected (e.g. browser updated or new display attached).
- **$< 55.0\%$**: `High Risk` / `Anomalous` - Untrusted device, headless browser, or proxy spoofing.

---

## 4. MongoDB Database Schemas

### 1. `device_fingerprints` Collection
```json
{
  "_id": "ObjectId('66a210...')",
  "username": "john_doe",
  "fingerprint_id": "c4e74daea34e685a6773c778185b7b47bd571a8a660ac3e29832a1e8c72124ef",
  "device_name": "Chrome on Windows 10/11",
  "status": "Trusted",
  "trust_score": 100,
  "attributes": {
    "browser_name": "Chrome",
    "browser_version": "124.0.0.0",
    "os": "Windows 10/11",
    "platform": "Win32",
    "screen_resolution": "1920x1080",
    "color_depth": 24,
    "hardware_concurrency": 16,
    "device_memory": 16,
    "webgl_vendor": "Google Inc. (NVIDIA)",
    "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070...)",
    "canvas_hash": "cv_1a89f30_2481",
    "timezone": "Asia/Kolkata",
    "language": "en-US"
  },
  "first_seen": "2026-07-24T19:00:00.000Z",
  "last_verified": "2026-07-24T21:00:00.000Z"
}
```

### 2. `device_trust_history` Collection
```json
{
  "_id": "ObjectId('66a211...')",
  "username": "john_doe",
  "fingerprint_id": "c4e74daea34e685a6773c778185b7b47bd571a8a660ac3e29832a1e8c72124ef",
  "match_percentage": 100.0,
  "risk_level": "Trusted",
  "status": "Trusted Device Match",
  "attribute_breakdown": {
    "canvas_match": 100.0,
    "webgl_match": 100.0,
    "hardware_match": 100.0,
    "os_match": 100.0,
    "locale_match": 100.0,
    "browser_match": 100.0
  },
  "timestamp": "2026-07-24T21:00:00.000Z"
}
```

---

## 5. REST APIs

```
POST /api/device/fingerprint  - Register/update trusted device fingerprint
POST /api/device/verify       - Verify live biometrics & compute similarity score
GET  /api/device/history      - Fetch device verification log history
GET  /api/device/trusted-list - Retrieve registered trusted devices
POST /api/device/revoke       - Revoke trust for a device fingerprint ID
```
