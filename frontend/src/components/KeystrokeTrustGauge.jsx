import React from "react";
import {
  FaKeyboard,
  FaRobot,
  FaUserCheck,
  FaExclamationTriangle,
  FaCheckCircle,
  FaTimesCircle,
  FaBrain,
} from "react-icons/fa";

export default function KeystrokeTrustGauge({
  trustScore = 91,
  riskLevel = "LOW",
  aiVerdict = "Genuine Typing Dynamics",
  modelUsed = "IsolationForest",
}) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (trustScore / 100) * circumference;

  const getRiskStyle = (risk) => {
    switch ((risk || "").toUpperCase()) {
      case "CRITICAL":
        return {
          color: "#ef4444",
          badgeBg: "bg-red-500/20 text-red-400 border-red-500/40",
          icon: <FaTimesCircle className="text-red-400" />,
          verdictIcon: <FaRobot className="text-red-400 text-xl" />,
        };
      case "HIGH":
        return {
          color: "#f97316",
          badgeBg: "bg-orange-500/20 text-orange-400 border-orange-500/40",
          icon: <FaExclamationTriangle className="text-orange-400" />,
          verdictIcon: <FaRobot className="text-orange-400 text-xl" />,
        };
      case "MEDIUM":
        return {
          color: "#eab308",
          badgeBg: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400" />,
          verdictIcon: <FaExclamationTriangle className="text-yellow-400 text-xl" />,
        };
      default:
        return {
          color: "#10b981",
          badgeBg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400" />,
          verdictIcon: <FaUserCheck className="text-emerald-400 text-xl" />,
        };
    }
  };

  const style = getRiskStyle(riskLevel);

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between h-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-cyan-500/10 rounded-xl border border-cyan-500/30 text-cyan-400">
            <FaKeyboard className="text-xl" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Keystroke AI Evaluation</span>
            </h3>
            <p className="text-xs text-slate-400">Continuous Typing Biometrics</p>
          </div>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-extrabold tracking-wide uppercase border flex items-center gap-1.5 ${style.badgeBg}`}
        >
          {style.icon}
          {riskLevel} RISK
        </span>
      </div>

      {/* Gauge and AI Verdict Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
        {/* SVG Circular Gauge */}
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
              {trustScore}
            </span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-widest">
              Trust Score
            </span>
          </div>
        </div>

        {/* AI Details */}
        <div className="space-y-3">
          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>AI Verdict</span>
              <FaBrain className="text-cyan-400" />
            </div>
            <div className="flex items-center space-x-2">
              {style.verdictIcon}
              <span className="text-sm font-bold text-white truncate">{aiVerdict}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                Classifier
              </span>
              <span className="text-xs font-extrabold text-cyan-300 truncate block">
                {modelUsed}
              </span>
            </div>

            <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                Confidence
              </span>
              <span className="text-xs font-extrabold text-emerald-400 font-mono">
                {(trustScore * 0.98).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
