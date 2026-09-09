import React from "react";
import {
  FaCheckCircle,
  FaExclamationTriangle,
  FaTimesCircle,
  FaFingerprint,
} from "react-icons/fa";

export default function DeviceSimilarityGauge({
  matchPercentage = 100.0,
  riskLevel = "Trusted",
  breakdown = {},
}) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (matchPercentage / 100) * circumference;

  const getRiskStyle = (risk) => {
    switch ((risk || "").toUpperCase()) {
      case "HIGH RISK":
      case "CRITICAL":
        return {
          color: "#ef4444",
          badgeBg: "bg-red-500/20 text-red-400 border-red-500/40",
          icon: <FaTimesCircle className="text-red-400" />,
        };
      case "MEDIUM RISK":
      case "SUSPICIOUS":
        return {
          color: "#eab308",
          badgeBg: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400" />,
        };
      default:
        return {
          color: "#10b981",
          badgeBg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400" />,
        };
    }
  };

  const style = getRiskStyle(riskLevel);

  const categoryMatches = [
    { label: "Canvas Hash Signature", pct: breakdown.canvas_match ?? 100, weight: "25%" },
    { label: "WebGL GPU Renderer", pct: breakdown.webgl_match ?? 100, weight: "25%" },
    { label: "Hardware CPU/RAM/Screen", pct: breakdown.hardware_match ?? 100, weight: "20%" },
    { label: "OS & Platform", pct: breakdown.os_match ?? 100, weight: "15%" },
    { label: "Locale & Timezone", pct: breakdown.locale_match ?? 100, weight: "10%" },
    { label: "Browser User Agent", pct: breakdown.browser_match ?? 100, weight: "5%" },
  ];

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between h-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-cyan-500/10 rounded-xl border border-cyan-500/30 text-cyan-400">
            <FaFingerprint className="text-xl" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Device Similarity Match</span>
            </h3>
            <p className="text-xs text-slate-400">Fuzzy Biometric Baseline Comparison</p>
          </div>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-extrabold tracking-wide uppercase border flex items-center gap-1.5 ${style.badgeBg}`}
        >
          {style.icon}
          {riskLevel}
        </span>
      </div>

      {/* SVG Circular Gauge & Breakdown Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
        {/* SVG Circular Meter */}
        <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 relative">
          <svg className="w-36 h-36 transform -rotate-90">
            <circle
              cx="72"
              cy="72"
              r={radius}
              className="stroke-slate-800"
              strokeWidth="10"
              fill="transparent"
            />
            <circle
              cx="72"
              cy="72"
              r={radius}
              stroke={style.color}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-700 ease-out"
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-3xl font-black text-white font-mono tracking-tight">
              {matchPercentage}%
            </span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-widest">
              Match Score
            </span>
          </div>
        </div>

        {/* Category Match Percentages Breakdown */}
        <div className="space-y-2 font-mono text-xs">
          {categoryMatches.map((cat, i) => (
            <div key={i} className="space-y-1">
              <div className="flex justify-between text-[11px] text-slate-400">
                <span className="truncate">{cat.label}</span>
                <span className="text-cyan-300 font-bold">{cat.pct}%</span>
              </div>
              <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${cat.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
