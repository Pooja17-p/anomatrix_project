import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { FaBrain } from "react-icons/fa";
import API_BASE_URL from "../config/api";

const API_BEHAVIOR_URL = `${API_BASE_URL}/api/behavior`;

export default function BehaviorTracker() {
  const [trackingActive, setTrackingActive] = useState(true);
  const [latestStats, setLatestStats] = useState({
    anomaly_score: 0.05,
    risk_level: "Low",
    logsCount: 0,
    typingSpeed: 0,
    mouseSpeed: 0,
  });

  // Telemetry buffer references to avoid unnecessary re-renders during high frequency events
  const metricsRef = useRef({
    // Mouse kinematics
    lastMouseX: null,
    lastMouseY: null,
    lastMouseTime: null,
    lastMouseSpeed: 0,
    mouseSpeeds: [],
    mouseAccelerations: [],
    currentMouseCoords: { x: 0, y: 0 },

    // Click & Scroll counts
    clickCount: 0,
    scrollCount: 0,

    // Keystroke dynamics
    keyDownMap: {},
    lastKeyUpTime: null,
    holdTimes: [],
    flightTimes: [],
    keypressCount: 0,

    // Session lifecycle
    sessionStartTime: Date.now(),
    sessionId: null,
  });

  useEffect(() => {
    // Initialize or restore session_id in sessionStorage
    let existingSessionId = sessionStorage.getItem("anomatrix_session_id");
    if (!existingSessionId) {
      existingSessionId = "sess_" + Math.random().toString(36).substring(2, 9) + "_" + Date.now();
      sessionStorage.setItem("anomatrix_session_id", existingSessionId);
    }
    metricsRef.current.sessionId = existingSessionId;

    // -------------------------------------------------------------------
    // 1. Mouse Event Listener (Coordinates, Speed, Acceleration)
    // -------------------------------------------------------------------
    const handleMouseMove = (e) => {
      const now = performance.now();
      const ref = metricsRef.current;
      ref.currentMouseCoords = { x: e.clientX, y: e.clientY };

      if (ref.lastMouseX !== null && ref.lastMouseY !== null && ref.lastMouseTime !== null) {
        const dt = (now - ref.lastMouseTime) / 1000; // in seconds
        if (dt > 0.005) { // Throttle calculations to >5ms steps
          const dx = e.clientX - ref.lastMouseX;
          const dy = e.clientY - ref.lastMouseY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const currentSpeed = dist / dt; // px/sec

          const dv = currentSpeed - ref.lastMouseSpeed;
          const acceleration = Math.abs(dv / dt); // px/sec^2

          ref.mouseSpeeds.push(currentSpeed);
          ref.mouseAccelerations.push(acceleration);
          ref.lastMouseSpeed = currentSpeed;
        }
      }

      ref.lastMouseX = e.clientX;
      ref.lastMouseY = e.clientY;
      ref.lastMouseTime = now;
    };

    // -------------------------------------------------------------------
    // 2. Click Event Listener
    // -------------------------------------------------------------------
    const handleClick = () => {
      metricsRef.current.clickCount += 1;
    };

    // -------------------------------------------------------------------
    // 3. Scroll Event Listener
    // -------------------------------------------------------------------
    const handleScroll = () => {
      metricsRef.current.scrollCount += 1;
    };

    // -------------------------------------------------------------------
    // 4. Keystroke Dynamics Listeners (Hold Time, Flight Time, Typing Speed)
    // -------------------------------------------------------------------
    const handleKeyDown = (e) => {
      const now = performance.now();
      const ref = metricsRef.current;

      if (!ref.keyDownMap[e.code]) {
        ref.keyDownMap[e.code] = now;
        ref.keypressCount += 1;

        // Flight time: duration between previous keyup and current keydown
        if (ref.lastKeyUpTime !== null) {
          const flightTime = now - ref.lastKeyUpTime;
          if (flightTime >= 0 && flightTime < 5000) {
            ref.flightTimes.push(flightTime);
          }
        }
      }
    };

    const handleKeyUp = (e) => {
      const now = performance.now();
      const ref = metricsRef.current;

      const keyDownTime = ref.keyDownMap[e.code];
      if (keyDownTime) {
        const holdTime = now - keyDownTime;
        if (holdTime >= 0 && holdTime < 5000) {
          ref.holdTimes.push(holdTime);
        }
        delete ref.keyDownMap[e.code];
      }

      ref.lastKeyUpTime = now;
    };

    // Attach passive window event listeners
    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    window.addEventListener("click", handleClick, { passive: true });
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("keydown", handleKeyDown, { passive: true });
    window.addEventListener("keyup", handleKeyUp, { passive: true });

    // -------------------------------------------------------------------
    // 5. Send Telemetry to Flask Backend every 5 Seconds via Axios
    // -------------------------------------------------------------------
    const intervalId = setInterval(async () => {
      const token = localStorage.getItem("token");
      if (!token) return; // Wait until authenticated

      const ref = metricsRef.current;
      const sessionDurationSec = Math.floor((Date.now() - ref.sessionStartTime) / 1000);

      // Compute averages for the 5 second window
      const avgMouseSpeed =
        ref.mouseSpeeds.length > 0
          ? ref.mouseSpeeds.reduce((a, b) => a + b, 0) / ref.mouseSpeeds.length
          : 0;

      const avgMouseAccel =
        ref.mouseAccelerations.length > 0
          ? ref.mouseAccelerations.reduce((a, b) => a + b, 0) / ref.mouseAccelerations.length
          : 0;

      const clickFrequency = ref.clickCount / 5; // clicks/sec in 5s window

      const avgHoldTime =
        ref.holdTimes.length > 0
          ? ref.holdTimes.reduce((a, b) => a + b, 0) / ref.holdTimes.length
          : 0;

      const avgFlightTime =
        ref.flightTimes.length > 0
          ? ref.flightTimes.reduce((a, b) => a + b, 0) / ref.flightTimes.length
          : 0;

      // Typing speed: (keypresses in 5s window / 5 chars per word) * (60s / 5s) = keypresses * 2.4 WPM
      const typingSpeedWpm = Math.round((ref.keypressCount / 5) * 12);

      const payload = {
        session_id: ref.sessionId,
        mouse_coordinates: ref.currentMouseCoords,
        mouse_speed: Math.round(avgMouseSpeed * 100) / 100,
        mouse_acceleration: Math.round(avgMouseAccel * 100) / 100,
        click_frequency: Math.round(clickFrequency * 100) / 100,
        scroll_events: ref.scrollCount,
        typing_speed: typingSpeedWpm,
        key_hold_time: Math.round(avgHoldTime * 100) / 100,
        flight_time: Math.round(avgFlightTime * 100) / 100,
        session_duration: sessionDurationSec,
        timestamp: new Date().toISOString(),
      };

      try {
        const response = await axios.post(`${API_BEHAVIOR_URL}/collect`, payload, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.data && response.data.data) {
          const resData = response.data.data;
          setLatestStats((prev) => ({
            anomaly_score: resData.anomaly_score,
            risk_level: resData.risk_level,
            logsCount: prev.logsCount + 1,
            typingSpeed: payload.typing_speed,
            mouseSpeed: payload.mouse_speed,
          }));
        }
      } catch (err) {
        console.error("Error dispatching behavior telemetry to backend:", err?.response?.data || err.message);
      }

      // Flush 5-second interval buffers for next slide window
      ref.mouseSpeeds = [];
      ref.mouseAccelerations = [];
      ref.clickCount = 0;
      ref.scrollCount = 0;
      ref.keypressCount = 0;
      ref.holdTimes = [];
      ref.flightTimes = [];
    }, 5000);

    // Cleanup listeners and interval on unmount
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("click", handleClick);
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-50 transition-all duration-300">
      <div className="bg-slate-900/90 backdrop-blur-md text-white border border-cyan-500/30 rounded-xl p-3 shadow-2xl shadow-cyan-950/40 flex items-center space-x-3 text-xs">
        <div className="relative flex items-center justify-center">
          <FaBrain className="text-cyan-400 text-lg animate-pulse" />
          <span className="absolute -top-1 -right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
          </span>
        </div>

        <div>
          <div className="font-semibold flex items-center gap-1 text-slate-200">
            <span>AI Behavioural Telemetry</span>
            <span className="text-[10px] bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/30">
              5s Loop
            </span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
            <span>
              Risk:{" "}
              <strong
                className={
                  latestStats.risk_level === "Critical"
                    ? "text-red-400"
                    : latestStats.risk_level === "High"
                    ? "text-orange-400"
                    : latestStats.risk_level === "Medium"
                    ? "text-yellow-400"
                    : "text-emerald-400"
                }
              >
                {latestStats.risk_level}
              </strong>
            </span>
            <span>•</span>
            <span>Score: {latestStats.anomaly_score}</span>
            <span>•</span>
            <span>Logs: {latestStats.logsCount}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
