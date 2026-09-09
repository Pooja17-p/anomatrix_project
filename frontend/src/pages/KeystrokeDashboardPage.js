import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import useKeystrokeTracker from "../hooks/useKeystrokeTracker";
import KeystrokeMetricsGrid from "../components/KeystrokeMetricsGrid";
import KeystrokeTrustGauge from "../components/KeystrokeTrustGauge";
import KeystrokeRhythmChart from "../components/KeystrokeRhythmChart";
import KeystrokeActivityTable from "../components/KeystrokeActivityTable";

import {
  FaKeyboard,
  FaSync,
  FaClock,
  FaPlug,
  FaCheckCircle,
  FaPen,
  FaUndo,
} from "react-icons/fa";

export default function KeystrokeDashboardPage() {
  const { typingScore, status, metrics } = useKeystrokeTracker({ intervalMs: 3500 });
  const [testText, setTestText] = useState("");
  const [sessionUptime, setSessionUptime] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [history, setHistory] = useState([
    {
      id: 1,
      timestamp: new Date().toLocaleTimeString(),
      typingSpeed: metrics.typingSpeed || 55,
      holdTime: metrics.avgHoldTime || 90,
      flightTime: metrics.avgFlightTime || 140,
      keypresses: 24,
      errors: 1,
      trustScore: typingScore || 91,
      riskLevel: "LOW",
      status: "Trusted",
    },
  ]);

  // Session Uptime Timer
  React.useEffect(() => {
    const timer = setInterval(() => setSessionUptime((prev) => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatUptime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleManualSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      const newSnapshot = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        typingSpeed: metrics.typingSpeed || 58,
        holdTime: metrics.avgHoldTime || 88,
        flightTime: metrics.avgFlightTime || 135,
        keypresses: testText.length || 32,
        errors: (testText.match(/\b/g) || []).length,
        trustScore: typingScore || 94,
        riskLevel: typingScore < 50 ? "CRITICAL" : typingScore < 70 ? "HIGH" : typingScore < 85 ? "MEDIUM" : "LOW",
        status: status || "Trusted",
      };
      setHistory((prev) => [newSnapshot, ...prev]);
      setIsSyncing(false);
    }, 600);
  };

  return (
    <div className="flex bg-slate-950 min-h-screen text-slate-100 font-sans">
      {/* Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 pl-[260px] p-6 overflow-y-auto min-h-screen space-y-6">
        {/* Top Session Status Banner */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-6 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 relative overflow-hidden">
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center space-x-4">
            <div className="p-4 bg-indigo-500/10 rounded-2xl border border-indigo-500/30 text-indigo-400">
              <FaKeyboard className="text-3xl animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-extrabold tracking-tight text-white">
                  Keystroke Dynamics Dashboard
                </h1>
                <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
                  Live Zero-Trust Typing Biometrics
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Real-time typing cadence evaluation, key hold/flight time analysis, Isolation Forest AI scoring, and rhythm profiling.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Session Uptime */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold flex items-center gap-1">
                <FaClock className="text-indigo-400" /> Session Uptime
              </span>
              <span className="text-indigo-300 font-bold">{formatUptime(sessionUptime)}</span>
            </div>

            {/* AI Engine Status */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold flex items-center gap-1">
                <FaPlug className="text-emerald-400" /> AI Engine
              </span>
              <span className="font-bold flex items-center gap-1 text-emerald-400">
                <FaCheckCircle className="text-[10px]" />
                Isolation Forest Active
              </span>
            </div>

            {/* Manual Sync Button */}
            <button
              onClick={handleManualSync}
              disabled={isSyncing}
              className="flex items-center space-x-2 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 px-4 py-2.5 rounded-xl transition text-xs font-bold shadow-lg"
            >
              <FaSync className={isSyncing ? "animate-spin" : ""} />
              <span>{isSyncing ? "Evaluating..." : "Sync AI"}</span>
            </button>
          </div>
        </div>

        {/* 1. Live Typing Metrics Grid */}
        <KeystrokeMetricsGrid
          typingSpeed={metrics.typingSpeed}
          avgHoldTime={metrics.avgHoldTime}
          avgFlightTime={metrics.avgFlightTime}
          rhythmVariance={metrics.rhythmVariance}
          errorRate={metrics.errorRate}
          keypressCount={testText.length}
        />

        {/* 2. Interactive Typing Test Box & Biometrics Visualizer */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FaPen className="text-cyan-400" />
              <span>Live Typing Practice & Biometric Sampler</span>
            </h3>
            <button
              onClick={() => setTestText("")}
              className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200 transition"
            >
              <FaUndo className="text-[10px]" />
              <span>Clear Field</span>
            </button>
          </div>

          <textarea
            rows={3}
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            placeholder="Type anything here (e.g. 'The quick brown fox jumps over the lazy dog') to observe your live key press, hold time, and typing rhythm biometrics..."
            className="w-full bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-600 rounded-xl p-4 text-sm focus:outline-none focus:border-indigo-500/60 font-mono resize-none"
          />

          <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 font-mono bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 gap-2">
            <span>Characters Typed: <strong className="text-cyan-300">{testText.length}</strong></span>
            <span>Est. Words: <strong className="text-indigo-300">{Math.round(testText.length / 5)}</strong></span>
            <span>Live Cadence Status: <strong className="text-emerald-400">{status || "Trusted"}</strong></span>
          </div>
        </div>

        {/* 3. AI Trust Score Gauge & Rhythm Trend Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <KeystrokeTrustGauge
              trustScore={typingScore}
              riskLevel={typingScore < 50 ? "CRITICAL" : typingScore < 70 ? "HIGH" : typingScore < 85 ? "MEDIUM" : "LOW"}
              aiVerdict={status === "Trusted" ? "Genuine Typing Dynamics" : "Suspicious Typing Pattern"}
              modelUsed="IsolationForest"
            />
          </div>

          <div className="lg:col-span-2">
            <KeystrokeRhythmChart history={history} />
          </div>
        </div>

        {/* 4. Keystroke Activity Logs Table */}
        <KeystrokeActivityTable
          history={history}
          isSyncing={isSyncing}
          onRefresh={handleManualSync}
        />
      </div>
    </div>
  );
}
