import React from "react";
import Sidebar from "../components/Sidebar";
import useMouseMotionTracker from "../hooks/useMouseMotionTracker";
import MousePathCanvas from "../components/MousePathCanvas";
import TrustScoreGauge from "../components/TrustScoreGauge";
import MovementStatsGrid from "../components/MovementStatsGrid";
import TelemetryCharts from "../components/TelemetryCharts";
import RecentActivityTable from "../components/RecentActivityTable";

import {
  FaMousePointer,
  FaSync,
  FaClock,
  FaPlug,
  FaCheckCircle,
  FaExclamationCircle,
} from "react-icons/fa";

export default function MouseDashboardPage() {
  const {
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
    sessionUptime,
    telemetryHistory,
    pathPoints,
    clickMarkers,
    nextSyncCountdown,
    isSyncing,
    backendConnected,
    syncTelemetryWithBackend,
    clearPath,
  } = useMouseMotionTracker({ refreshIntervalMs: 3500, maxPathPoints: 120 });

  // Format uptime HH:MM:SS
  const formatUptime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex bg-slate-950 min-h-screen text-slate-100 font-sans">
      {/* Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 pl-[260px] p-6 overflow-y-auto min-h-screen space-y-6">
        {/* Top Session Status Banner */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-6 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 relative overflow-hidden">
          {/* Subtle Glow Background Effect */}
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center space-x-4">
            <div className="p-4 bg-cyan-500/10 rounded-2xl border border-cyan-500/30 text-cyan-400">
              <FaMousePointer className="text-3xl animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-extrabold tracking-tight text-white">
                  Mouse Motion Dashboard
                </h1>
                <span className="text-xs px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                  Live Zero-Trust Tracking
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Real-time mouse dynamics evaluation, AI trajectory classification, kinematic metrics, and security profiling.
              </p>
            </div>
          </div>

          {/* Session Information Badges & Manual Refresh */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Session ID */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold">Session ID</span>
              <span className="text-cyan-400 font-bold">{sessionId || "sess_initializing"}</span>
            </div>

            {/* Session Uptime */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold flex items-center gap-1">
                <FaClock className="text-indigo-400" /> Uptime
              </span>
              <span className="text-indigo-300 font-bold">{formatUptime(sessionUptime)}</span>
            </div>

            {/* Backend Connectivity Status */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold flex items-center gap-1">
                <FaPlug className={backendConnected ? "text-emerald-400" : "text-amber-400"} /> AI Engine
              </span>
              <span className={`font-bold flex items-center gap-1 ${backendConnected ? "text-emerald-400" : "text-amber-400"}`}>
                {backendConnected ? <FaCheckCircle className="text-[10px]" /> : <FaExclamationCircle className="text-[10px]" />}
                {backendConnected ? "Flask ML Active" : "Client Fallback"}
              </span>
            </div>

            {/* Auto-refresh Timer Pill */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold">Auto-Sync</span>
              <span className="text-emerald-400 font-mono font-bold flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                in {nextSyncCountdown}s
              </span>
            </div>

            {/* Manual Sync Button */}
            <button
              onClick={syncTelemetryWithBackend}
              disabled={isSyncing}
              className="flex items-center space-x-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 px-4 py-2.5 rounded-xl transition text-xs font-bold shadow-lg"
            >
              <FaSync className={isSyncing ? "animate-spin" : ""} />
              <span>{isSyncing ? "Evaluating..." : "Sync AI"}</span>
            </button>
          </div>
        </div>

        {/* 1. Live Movement Statistics Grid */}
        <MovementStatsGrid
          livePosition={livePosition}
          currentSpeed={currentSpeed}
          avgSpeed={avgSpeed}
          peakSpeed={peakSpeed}
          acceleration={acceleration}
          totalDistance={totalDistance}
          curvatureIndex={curvatureIndex}
          clickCount={clickCount}
          scrollCount={scrollCount}
        />

        {/* 2. Primary Visualization Row: Mouse Path Canvas & AI Trust Score Gauge */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <MousePathCanvas
              pathPoints={pathPoints}
              clickMarkers={clickMarkers}
              livePosition={livePosition}
              currentSpeed={currentSpeed}
              onClear={clearPath}
            />
          </div>

          <div className="lg:col-span-1">
            <TrustScoreGauge
              trustScore={trustScore}
              riskLevel={riskLevel}
              aiPrediction={aiPrediction}
              backendConnected={backendConnected}
            />
          </div>
        </div>

        {/* 3. Real-time Telemetry Analytics & Velocity Trend Line Charts */}
        <TelemetryCharts history={telemetryHistory} />

        {/* 4. Historical Telemetry Logs & Activity Table */}
        <RecentActivityTable
          history={telemetryHistory}
          isSyncing={isSyncing}
          onRefresh={syncTelemetryWithBackend}
        />
      </div>
    </div>
  );
}
