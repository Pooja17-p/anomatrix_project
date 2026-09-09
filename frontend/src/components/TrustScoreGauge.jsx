import React from "react";
import {
  FaShieldAlt,
  FaRobot,
  FaUserCheck,
  FaExclamationTriangle,
  FaCheckCircle,
  FaTimesCircle,
  FaBrain,
  FaSlidersH,
} from "react-icons/fa";

export default function TrustScoreGauge({
  trustScore = 95,
  riskLevel = "LOW",
  aiPrediction = {},
  backendConnected = true,
}) {
  // SVG Circular Gauge Calculations
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (trustScore / 100) * circumference;

  // Determine styles according to Risk Level
  const getRiskDetails = (risk) => {
    switch (risk.toUpperCase()) {
      case "CRITICAL":
        return {
          bg: "bg-red-500/10",
          border: "border-red-500/30",
          text: "text-red-400",
          gaugeColor: "#ef4444",
          badgeBg: "bg-red-500/20 text-red-400 border-red-500/40",
          icon: <FaTimesCircle className="text-red-400 text-lg" />,
          verdictIcon: <FaRobot className="text-red-400 text-xl" />,
        };
      case "HIGH":
        return {
          bg: "bg-orange-500/10",
          border: "border-orange-500/30",
          text: "text-orange-400",
          gaugeColor: "#f97316",
          badgeBg: "bg-orange-500/20 text-orange-400 border-orange-500/40",
          icon: <FaExclamationTriangle className="text-orange-400 text-lg" />,
          verdictIcon: <FaRobot className="text-orange-400 text-xl" />,
        };
      case "MEDIUM":
        return {
          bg: "bg-yellow-500/10",
          border: "border-yellow-500/30",
          text: "text-yellow-400",
          gaugeColor: "#eab308",
          badgeBg: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400 text-lg" />,
          verdictIcon: <FaExclamationTriangle className="text-yellow-400 text-xl" />,
        };
      default:
        return {
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/30",
          text: "text-emerald-400",
          gaugeColor: "#10b981",
          badgeBg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400 text-lg" />,
          verdictIcon: <FaUserCheck className="text-emerald-400 text-xl" />,
        };
    }
  };

  const style = getRiskDetails(riskLevel);

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between h-full space-y-6">
      {/* Header title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/30 text-indigo-400">
            <FaShieldAlt className="text-xl" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Security & AI Assessment</span>
            </h3>
            <p className="text-xs text-slate-400">
              Zero-Trust Continuous Biometric Evaluation
            </p>
          </div>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-extrabold tracking-wide uppercase border flex items-center gap-1.5 ${style.badgeBg}`}
        >
          {style.icon}
          {riskLevel} RISK
        </span>
      </div>

      {/* Trust Score Gauge & Prediction Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
        {/* SVG Circular Gauge */}
        <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 relative">
          <svg className="w-36 h-36 transform -rotate-90">
            {/* Background Track */}
            <circle
              cx="72"
              cy="72"
              r={radius}
              className="stroke-slate-800"
              strokeWidth="10"
              fill="transparent"
            />
            {/* Progress Fill */}
            <circle
              cx="72"
              cy="72"
              r={radius}
              stroke={style.gaugeColor}
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

        {/* AI Prediction Details */}
        <div className="space-y-3">
          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>AI Verdict</span>
              <FaBrain className="text-cyan-400" />
            </div>
            <div className="flex items-center space-x-2">
              {style.verdictIcon}
              <span className="text-sm font-bold text-white">
                {aiPrediction.verdict || "Evaluating..."}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                Confidence
              </span>
              <span className="text-sm font-extrabold text-cyan-300 font-mono">
                {aiPrediction.confidence ?? 95.0}%
              </span>
            </div>

            <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                Engine
              </span>
              <span className="text-[11px] font-bold text-slate-300 truncate block">
                {backendConnected ? "Flask ML" : "Client Heuristic"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Factors Checklist */}
      <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 space-y-2">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
          <span>Active Risk Signals</span>
          <FaSlidersH className="text-slate-500" />
        </div>

        {aiPrediction.riskFactors && aiPrediction.riskFactors.length > 0 ? (
          <ul className="space-y-1.5">
            {aiPrediction.riskFactors.map((factor, idx) => (
              <li key={idx} className="flex items-center space-x-2 text-xs">
                {aiPrediction.isAnomaly ? (
                  <FaExclamationTriangle className="text-amber-400 text-xs flex-shrink-0" />
                ) : (
                  <FaCheckCircle className="text-emerald-400 text-xs flex-shrink-0" />
                )}
                <span className="text-slate-300 truncate">{factor}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="flex items-center space-x-2 text-xs text-emerald-400">
            <FaCheckCircle />
            <span>Kinematic trajectory conforms to human baseline</span>
          </div>
        )}
      </div>
    </div>
  );
}
