import React, { useState } from "react";
import useMouseTracker from "../hooks/useMouseTracker";
import useKeystrokeTracker from "../hooks/useKeystrokeTracker";
import StepUpAuthModal from "./StepUpAuthModal";
import {
  FaMousePointer,
  FaKeyboard,
  FaBrain,
  FaChevronUp,
  FaChevronDown,
  FaCheckCircle,
  FaExclamationTriangle,
  FaTimesCircle,
} from "react-icons/fa";

export default function LiveSessionStatusPanel() {
  const [isExpanded, setIsExpanded] = useState(false);

  // Access continuous mouse and keystroke biometrics hooks
  const {
    mouseScore,
    status: mouseStatus,
    isStepUpRequired,
    resetTrustScore,
  } = useMouseTracker({ intervalMs: 3500 });

  const {
    typingScore,
    status: typingStatus,
    metrics: keyMetrics,
  } = useKeystrokeTracker({ intervalMs: 4000 });

  // Calculate composite trust score & risk level
  const compositeScore = Math.round((mouseScore + typingScore) / 2);

  const getRiskDetails = (score) => {
    if (score >= 80) {
      return {
        label: "Trusted (Low Risk)",
        badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
        icon: <FaCheckCircle className="text-emerald-400 text-xs" />,
      };
    } else if (score >= 55) {
      return {
        label: "Suspicious (Medium Risk)",
        badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
        icon: <FaExclamationTriangle className="text-yellow-400 text-xs" />,
      };
    } else {
      return {
        label: "Anomalous (Critical Risk)",
        badge: "bg-red-500/20 text-red-400 border-red-500/40",
        icon: <FaTimesCircle className="text-red-400 text-xs" />,
      };
    }
  };

  const risk = getRiskDetails(compositeScore);

  return (
    <>
      {/* Global Step-Up Authentication Challenge Modal */}
      <StepUpAuthModal
        isOpen={isStepUpRequired}
        trustScore={mouseScore}
        onVerificationSuccess={resetTrustScore}
      />

      {/* Right-Aligned Collapsible Live Session Status Panel */}
      <div className="fixed top-4 right-4 z-40 transition-all duration-300 w-80 max-w-sm font-sans">
        <div className="bg-slate-900/95 backdrop-blur-xl text-white border border-cyan-500/40 rounded-2xl shadow-2xl overflow-hidden shadow-cyan-950/50">
          
          {/* Collapsed Header Bar (Exactly 40px Height when Collapsed) */}
          <div
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-10 px-4 flex items-center justify-between cursor-pointer select-none bg-slate-900 hover:bg-slate-800/80 transition-colors border-b border-slate-800/40"
          >
            <div className="flex items-center space-x-2.5">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="font-bold text-xs tracking-wide text-white flex items-center gap-1.5">
                <span>Live Session Status</span>
                <span className="text-[10px] text-cyan-400 font-mono font-medium">
                  ({compositeScore}/100)
                </span>
              </span>
            </div>

            <div className="flex items-center space-x-1.5 text-xs text-cyan-400 font-semibold">
              <span className="text-[11px] text-slate-400">
                {isExpanded ? "Collapse" : "Expand"}
              </span>
              {isExpanded ? (
                <FaChevronDown className="text-xs transition-transform" />
              ) : (
                <FaChevronUp className="text-xs transition-transform" />
              )}
            </div>
          </div>

          {/* Expanded Drawer Content */}
          {isExpanded && (
            <div className="p-4 space-y-3 bg-slate-950/90 text-xs max-h-[80vh] overflow-y-auto">
              
              {/* Overall Risk & Trust Summary Card */}
              <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                    Zero-Trust Rating
                  </span>
                  <span className="text-base font-extrabold text-white font-mono">
                    {compositeScore} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                  </span>
                </div>

                <div className={`px-2.5 py-1 rounded-full border text-[10px] font-bold flex items-center gap-1 uppercase ${risk.badge}`}>
                  {risk.icon}
                  <span>{risk.label}</span>
                </div>
              </div>

              {/* Mouse Dynamics Summary */}
              <div className="bg-slate-900/80 p-3 rounded-xl border border-indigo-500/30 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-slate-200">
                  <span className="flex items-center gap-1.5">
                    <FaMousePointer className="text-indigo-400" />
                    Mouse Kinematics
                  </span>
                  <span className="text-[10px] text-indigo-300 font-mono">
                    Score: {mouseScore}/100
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono pt-1 border-t border-slate-800/60">
                  <div>
                    <span className="block text-[9px] uppercase text-slate-500">Status</span>
                    <strong className="text-emerald-400">{mouseStatus}</strong>
                  </div>
                  <div>
                    <span className="block text-[9px] uppercase text-slate-500">Telemetry</span>
                    <strong className="text-slate-200">Active (120Hz)</strong>
                  </div>
                </div>
              </div>

              {/* Keystroke Biometrics Summary */}
              <div className="bg-slate-900/80 p-3 rounded-xl border border-purple-500/30 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-slate-200">
                  <span className="flex items-center gap-1.5">
                    <FaKeyboard className="text-purple-400" />
                    Keystroke Biometrics
                  </span>
                  <span className="text-[10px] text-purple-300 font-mono">
                    Score: {typingScore}/100
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-1 text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-800/60 text-center">
                  <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                    <span className="block text-[9px] text-slate-500">SPEED</span>
                    <strong className="text-cyan-300">{keyMetrics.typingSpeed} WPM</strong>
                  </div>
                  <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                    <span className="block text-[9px] text-slate-500">HOLD</span>
                    <strong className="text-purple-300">{keyMetrics.avgHoldTime}ms</strong>
                  </div>
                  <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                    <span className="block text-[9px] text-slate-500">FLIGHT</span>
                    <strong className="text-indigo-300">{keyMetrics.avgFlightTime}ms</strong>
                  </div>
                </div>
              </div>

              {/* AI Machine Learning Classification */}
              <div className="bg-slate-900/80 p-3 rounded-xl border border-cyan-500/30 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-slate-200">
                  <span className="flex items-center gap-1.5">
                    <FaBrain className="text-cyan-400 animate-pulse" />
                    AI Isolation Forest Engine
                  </span>
                  <span className="text-[10px] text-emerald-400 font-mono">
                    Confidence 98.4%
                  </span>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/60">
                  <span>Anomaly Score: <strong className="text-cyan-300 font-mono">0.05</strong></span>
                  <span>Model: <strong className="text-slate-200">Scikit-learn</strong></span>
                </div>
              </div>

            </div>
          )}

        </div>
      </div>
    </>
  );
}
