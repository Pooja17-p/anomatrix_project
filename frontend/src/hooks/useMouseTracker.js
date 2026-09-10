import { useEffect, useRef, useState } from "react";
import axios from "axios";
import API_BASE_URL from "../config/api";

const API_MOUSE_URL = `${API_BASE_URL}/api/mouse`;

export function useMouseTracker({ intervalMs = 4000, enabled = true } = {}) {
  const [mouseScore, setMouseScore] = useState(100);
  const [status, setStatus] = useState("Trusted");
  const [isTracking, setIsTracking] = useState(enabled);
  const [lastResult, setLastResult] = useState(null);
  const [isStepUpRequired, setIsStepUpRequired] = useState(false);

  const telemetryRef = useRef({
    points: [],
    clickEvents: 0,
    scrollBehaviour: 0,
    lastX: null,
    lastY: null,
    lastTime: null,
    lastSpeed: 0,
    sessionId: null,
  });

  const resetTrustScore = (newScore = 100) => {
    setMouseScore(newScore);
    setStatus("Trusted");
    setIsStepUpRequired(false);
  };

  useEffect(() => {
    if (!enabled) {
      setIsTracking(false);
      return;
    }
    setIsTracking(true);

    let currentSessionId = sessionStorage.getItem("anomatrix_mouse_session_id");
    if (!currentSessionId) {
      currentSessionId = "mouse_sess_" + Math.random().toString(36).substring(2, 9) + "_" + Date.now();
      sessionStorage.setItem("anomatrix_mouse_session_id", currentSessionId);
    }
    telemetryRef.current.sessionId = currentSessionId;

    const handleMouseMove = (e) => {
      const now = performance.now();
      const ref = telemetryRef.current;
      const currentX = e.clientX;
      const currentY = e.clientY;

      if (ref.lastX !== null && ref.lastY !== null && ref.lastTime !== null) {
        const dt = (now - ref.lastTime) / 1000;
        if (dt >= 0.01) {
          const dx = currentX - ref.lastX;
          const dy = currentY - ref.lastY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const currentSpeed = dist / dt;
          const dv = currentSpeed - ref.lastSpeed;
          const acceleration = Math.abs(dv / dt);
          const angleRad = Math.atan2(dy, dx);
          const directionDeg = Math.round(((angleRad * 180 / Math.PI) + 360) % 360);

          ref.points.push({
            x: currentX,
            y: currentY,
            speed: Math.round(currentSpeed),
            acceleration: Math.round(acceleration),
            direction: directionDeg,
            timestamp: Date.now(),
          });

          ref.lastSpeed = currentSpeed;
        }
      }

      ref.lastX = currentX;
      ref.lastY = currentY;
      ref.lastTime = now;
    };

    const handleClick = () => {
      telemetryRef.current.clickEvents += 1;
    };

    const handleScroll = () => {
      telemetryRef.current.scrollBehaviour += 1;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    window.addEventListener("click", handleClick, { passive: true });
    window.addEventListener("scroll", handleScroll, { passive: true });

    const timerId = setInterval(async () => {
      const token = localStorage.getItem("token");
      if (!token) return;

      const ref = telemetryRef.current;
      const pointsSample = ref.points.slice(-50);

      const payload = {
        session_id: ref.sessionId,
        points: pointsSample,
        click_events: ref.clickEvents,
        scroll_behaviour: ref.scrollBehaviour,
        window_duration: intervalMs / 1000.0,
        timestamp: new Date().toISOString(),
      };

      try {
        const response = await axios.post(`${API_MOUSE_URL}/track`, payload, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.data) {
          const { mouse_score, status: newStatus } = response.data;
          setMouseScore(mouse_score);
          setStatus(newStatus);
          setLastResult(response.data);
          // Never trigger continuous periodic step-up popups during normal usage
          setIsStepUpRequired(false);
        }
      } catch (err) {
        // Silent background telemetry
      }

      ref.points = [];
      ref.clickEvents = 0;
      ref.scrollBehaviour = 0;
    }, intervalMs);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("click", handleClick);
      window.removeEventListener("scroll", handleScroll);
      clearInterval(timerId);
    };
  }, [intervalMs, enabled]);

  return {
    mouseScore,
    status,
    isTracking,
    isStepUpRequired: false,
    resetTrustScore,
    lastResult,
  };
}
export default useMouseTracker;
