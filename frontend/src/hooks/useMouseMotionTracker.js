import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import API_BASE_URL from "../config/api";

const API_MOUSE_URL = `${API_BASE_URL}/api/mouse`;

/**
 * Custom React Hook for live mouse motion tracking and telemetry evaluation.
 * Captures coordinates, speed, acceleration, path points, distance, clicks, scrolls,
 * and handles periodic backend AI evaluation sync.
 */
export function useMouseMotionTracker({
  refreshIntervalMs = 3500,
  maxPathPoints = 120,
  enabled = true,
} = {}) {
  // Live Position
  const [livePosition, setLivePosition] = useState({ x: 0, y: 0 });

  // Kinematic Metrics
  const [currentSpeed, setCurrentSpeed] = useState(0); // px/sec
  const [avgSpeed, setAvgSpeed] = useState(0); // px/sec
  const [peakSpeed, setPeakSpeed] = useState(0); // px/sec
  const [acceleration, setAcceleration] = useState(0); // px/sec²
  const [totalDistance, setTotalDistance] = useState(0); // total px moved
  const [clickCount, setClickCount] = useState(0);
  const [scrollCount, setScrollCount] = useState(0);
  const [curvatureIndex, setCurvatureIndex] = useState(0.0);

  // Security Evaluation & AI Prediction
  const [trustScore, setTrustScore] = useState(98);
  const [riskLevel, setRiskLevel] = useState("LOW"); // LOW, MEDIUM, HIGH, CRITICAL
  const [aiPrediction, setAiPrediction] = useState({
    verdict: "Human Behavior",
    confidence: 96.5,
    isAnomaly: false,
    modelUsed: "IsolationForest + XGBoost Ensemble",
    riskFactors: [],
    predictedAt: new Date().toISOString(),
  });

  // Session & Telemetry Status
  const [sessionId, setSessionId] = useState("");
  const [sessionStatus, setSessionStatus] = useState("Active"); // Active, Idle, Suspicious, Monitored
  const [sessionUptime, setSessionUptime] = useState(0); // seconds
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [pathPoints, setPathPoints] = useState([]);
  const [clickMarkers, setClickMarkers] = useState([]);
  const [nextSyncCountdown, setNextSyncCountdown] = useState(Math.round(refreshIntervalMs / 1000));
  const [isSyncing, setIsSyncing] = useState(false);
  const [backendConnected, setBackendConnected] = useState(true);

  // Internal references to avoid unnecessary state triggers during 60fps mouse movements
  const internalRef = useRef({
    lastX: null,
    lastY: null,
    lastTime: null,
    lastSpeed: 0,
    speedHistory: [],
    pointsBuffer: [],
    clicksBuffer: 0,
    scrollsBuffer: 0,
    totalDistAccumulator: 0,
    peakSpeedAccumulator: 0,
    activeTimeMs: 0,
    idleTimeMs: 0,
    windowStartMs: Date.now(),
  });

  // Initialize or retrieve Session ID
  useEffect(() => {
    let sessId = sessionStorage.getItem("anomatrix_mouse_dashboard_sess");
    if (!sessId) {
      sessId = "sess_" + Math.random().toString(36).substring(2, 8) + "_" + Date.now();
      sessionStorage.setItem("anomatrix_mouse_dashboard_sess", sessId);
    }
    setSessionId(sessId);
  }, []);

  // Session Uptime Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setSessionUptime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Next Sync Countdown Timer
  useEffect(() => {
    const countdownTimer = setInterval(() => {
      setNextSyncCountdown((prev) => (prev <= 1 ? Math.round(refreshIntervalMs / 1000) : prev - 1));
    }, 1000);
    return () => clearInterval(countdownTimer);
  }, [refreshIntervalMs]);

  // Main Event Listeners for Mouse Motion
  useEffect(() => {
    if (!enabled) return;

    const handleMouseMove = (e) => {
      const x = e.clientX;
      const y = e.clientY;
      const now = performance.now();
      const ref = internalRef.current;

      setLivePosition({ x, y });

      if (ref.lastX !== null && ref.lastY !== null && ref.lastTime !== null) {
        const dt = (now - ref.lastTime) / 1000; // seconds

        if (dt >= 0.008) { // Throttle point recording to >8ms intervals (~120Hz)
          const dx = x - ref.lastX;
          const dy = y - ref.lastY;
          const dist = Math.sqrt(dx * dx + dy * dy);

          const instSpeed = Math.round(dist / dt); // px/sec
          const dv = instSpeed - ref.lastSpeed;
          const instAccel = Math.round(Math.abs(dv / dt)); // px/sec²
          const angle = Math.round(((Math.atan2(dy, dx) * 180 / Math.PI) + 360) % 360);

          ref.totalDistAccumulator += dist;
          if (instSpeed > ref.peakSpeedAccumulator) {
            ref.peakSpeedAccumulator = instSpeed;
          }

          ref.speedHistory.push(instSpeed);
          if (ref.speedHistory.length > 50) ref.speedHistory.shift();

          const currentAvgSpeed = Math.round(
            ref.speedHistory.reduce((a, b) => a + b, 0) / ref.speedHistory.length
          );

          setCurrentSpeed(instSpeed);
          setAcceleration(instAccel);
          setAvgSpeed(currentAvgSpeed);
          setPeakSpeed(ref.peakSpeedAccumulator);
          setTotalDistance(Math.round(ref.totalDistAccumulator));

          const pointData = {
            x,
            y,
            speed: instSpeed,
            accel: instAccel,
            angle,
            timestamp: Date.now(),
          };

          ref.pointsBuffer.push(pointData);

          // Update path points state for canvas drawing
          setPathPoints((prev) => {
            const updated = [...prev, pointData];
            return updated.length > maxPathPoints ? updated.slice(-maxPathPoints) : updated;
          });

          ref.lastSpeed = instSpeed;
          ref.activeTimeMs += dt * 1000;
        }
      } else {
        ref.idleTimeMs += 10;
      }

      ref.lastX = x;
      ref.lastY = y;
      ref.lastTime = now;
    };

    const handleClick = (e) => {
      internalRef.current.clicksBuffer += 1;
      setClickCount((prev) => prev + 1);

      const clickData = {
        x: e.clientX,
        y: e.clientY,
        timestamp: Date.now(),
      };

      setClickMarkers((prev) => [...prev.slice(-20), clickData]);
    };

    const handleScroll = () => {
      internalRef.current.scrollsBuffer += 1;
      setScrollCount((prev) => prev + 1);
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    window.addEventListener("click", handleClick, { passive: true });
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("click", handleClick);
      window.removeEventListener("scroll", handleScroll);
    };
  }, [enabled, maxPathPoints]);

  // Compute Curvature Index periodically
  useEffect(() => {
    const curvatureCalcTimer = setInterval(() => {
      const pts = internalRef.current.pointsBuffer;
      if (pts.length < 5) return;

      let directDistSum = 0;
      let actualPathSum = 0;

      for (let i = 2; i < pts.length; i++) {
        const dx = pts[i].x - pts[i - 1].x;
        const dy = pts[i].y - pts[i - 1].y;
        actualPathSum += Math.sqrt(dx * dx + dy * dy);
      }

      const dxTotal = pts[pts.length - 1].x - pts[0].x;
      const dyTotal = pts[pts.length - 1].y - pts[0].y;
      directDistSum = Math.sqrt(dxTotal * dxTotal + dyTotal * dyTotal);

      if (directDistSum > 10) {
        const curvatureRatio = actualPathSum / (directDistSum || 1);
        setCurvatureIndex(parseFloat(curvatureRatio.toFixed(2)));
      }
    }, 1000);

    return () => clearInterval(curvatureCalcTimer);
  }, []);

  // Client Heuristic Safety Evaluation (Fallback if backend unreachable)
  const computeClientHeuristicScore = useCallback((pts, clicks, scrolls, speed, peakSpd) => {
    let score = 98;
    let risk = "LOW";
    let verdict = "Human Behavior";
    let isAnomaly = false;
    const riskFactors = [];

    if (peakSpd > 4500) {
      score -= 25;
      riskFactors.push("Unnatural Instantaneous Velocity (>4500 px/s)");
    }

    if (pts.length > 20) {
      // Check for perfectly straight synthetic lines
      let totalAngleDiff = 0;
      for (let i = 1; i < pts.length - 1; i++) {
        const diff = Math.abs(pts[i].angle - pts[i - 1].angle);
        totalAngleDiff += diff;
      }
      const avgAngleVar = totalAngleDiff / (pts.length - 1);
      if (avgAngleVar < 0.5) {
        score -= 30;
        riskFactors.push("Zero Angular Variation (Synthetic Straight Line)");
      }
    }

    if (score >= 85) {
      risk = "LOW";
      verdict = "Genuine Human User";
    } else if (score >= 65) {
      risk = "MEDIUM";
      verdict = "Suspicious Motion Pattern";
    } else if (score >= 40) {
      risk = "HIGH";
      verdict = "Potential Bot / Automated Script";
      isAnomaly = true;
    } else {
      risk = "CRITICAL";
      verdict = "High Confidence Automated Attack";
      isAnomaly = true;
    }

    return { score: Math.max(0, Math.min(100, score)), risk, verdict, isAnomaly, riskFactors };
  }, []);

  // Sync Telemetry with Backend Flask API & Update Dashboard Auto-refresh
  const syncTelemetryWithBackend = useCallback(async () => {
    if (!enabled) return;

    setIsSyncing(true);
    const ref = internalRef.current;
    const token = localStorage.getItem("token");

    const latestPoints = [...ref.pointsBuffer].slice(-60);
    const currentClicks = ref.clicksBuffer;
    const currentScrolls = ref.scrollsBuffer;

    // Reset buffer window counts
    ref.pointsBuffer = [];
    ref.clicksBuffer = 0;
    ref.scrollsBuffer = 0;

    const payload = {
      session_id: sessionId || "sess_default",
      points: latestPoints,
      click_events: currentClicks,
      scroll_behaviour: currentScrolls,
      window_duration: refreshIntervalMs / 1000.0,
      timestamp: new Date().toISOString(),
    };

    let backendSuccess = false;

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await axios.post(`${API_MOUSE_URL}/predict`, payload, {
        headers,
        timeout: 4000,
      });

      if (res.data && res.data.status === "success") {
        backendSuccess = true;
        setBackendConnected(true);

        const backendScore = res.data.trust_score ?? res.data.mouse_score ?? 95;
        const backendStatus = res.data.status ?? res.data.security_status ?? "Trusted";
        const isAnomaly = res.data.is_anomaly ?? false;
        const modelUsed = res.data.model_used ?? "IsolationForest Ensemble";

        let risk = "LOW";
        if (backendScore < 40) risk = "CRITICAL";
        else if (backendScore < 60) risk = "HIGH";
        else if (backendScore < 80) risk = "MEDIUM";

        setTrustScore(backendScore);
        setRiskLevel(risk);
        setSessionStatus(backendStatus === "Trusted" ? "Active" : backendStatus);

        const newPrediction = {
          verdict: isAnomaly ? "Automated Anomaly Detected" : "Genuine Human Behavior",
          confidence: parseFloat((backendScore * 0.98).toFixed(1)),
          isAnomaly,
          modelUsed,
          riskFactors: isAnomaly ? ["Backend Anomaly Classifier Flagged Window"] : ["Normal Kinematic Trajectory"],
          predictedAt: new Date().toLocaleTimeString(),
        };

        setAiPrediction(newPrediction);

        const newSnapshot = {
          id: Date.now(),
          timestamp: new Date().toLocaleTimeString(),
          pointsCaptured: latestPoints.length,
          avgSpeed: currentSpeed,
          peakSpeed: peakSpeed,
          clicks: currentClicks,
          scrolls: currentScrolls,
          trustScore: backendScore,
          riskLevel: risk,
          status: backendStatus,
        };

        setTelemetryHistory((prev) => [newSnapshot, ...prev.slice(0, 24)]);
      }
    } catch (err) {
      console.warn("Backend mouse sync unavailable, resorting to client heuristic evaluator:", err.message);
      setBackendConnected(false);
    }

    // Fallback if backend call was unsuccessful
    if (!backendSuccess) {
      const clientEval = computeClientHeuristicScore(
        latestPoints,
        currentClicks,
        currentScrolls,
        currentSpeed,
        peakSpeed
      );

      setTrustScore(clientEval.score);
      setRiskLevel(clientEval.risk);
      setSessionStatus(clientEval.risk === "LOW" ? "Active" : clientEval.risk);

      const clientPrediction = {
        verdict: clientEval.verdict,
        confidence: 94.2,
        isAnomaly: clientEval.isAnomaly,
        modelUsed: "Client Kinematic Engine (Fallback)",
        riskFactors: clientEval.riskFactors.length ? clientEval.riskFactors : ["Kinematics Within Normal Bounds"],
        predictedAt: new Date().toLocaleTimeString(),
      };

      setAiPrediction(clientPrediction);

      const newSnapshot = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        pointsCaptured: latestPoints.length,
        avgSpeed: currentSpeed,
        peakSpeed: peakSpeed,
        clicks: currentClicks,
        scrolls: currentScrolls,
        trustScore: clientEval.score,
        riskLevel: clientEval.risk,
        status: clientEval.risk === "LOW" ? "Trusted" : "Suspicious",
      };

      setTelemetryHistory((prev) => [newSnapshot, ...prev.slice(0, 24)]);
    }

    setIsSyncing(false);
  }, [enabled, sessionId, refreshIntervalMs, currentSpeed, peakSpeed, computeClientHeuristicScore]);

  // Periodic Telemetry Auto-refresh Loop
  useEffect(() => {
    const autoRefreshTimer = setInterval(() => {
      syncTelemetryWithBackend();
    }, refreshIntervalMs);

    return () => clearInterval(autoRefreshTimer);
  }, [refreshIntervalMs, syncTelemetryWithBackend]);

  // Clear Path Visualization
  const clearPath = useCallback(() => {
    setPathPoints([]);
    setClickMarkers([]);
  }, []);

  return {
    livePosition,
    currentSpeed,
    avgSpeed,
    peakSpeed,
    acceleration,
    totalDistance,
    clickCount,
    scrollCount,
    curvatureIndex,
    trustScore,
    riskLevel,
    aiPrediction,
    sessionId,
    sessionStatus,
    sessionUptime,
    telemetryHistory,
    pathPoints,
    clickMarkers,
    nextSyncCountdown,
    isSyncing,
    backendConnected,
    syncTelemetryWithBackend,
    clearPath,
  };
}

export default useMouseMotionTracker;
