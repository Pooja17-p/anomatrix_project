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
  FaCompass,
  FaTachometerAlt,
  FaHeartbeat,
} from "react-icons/fa";

export default function LiveStatusTray() {
  const [isMainExpanded, setIsMainExpanded] = useState(false);
  const [openSections, setOpenSections] = useState({
    mouse: true,
    keyboard: true,
    telemetry: true,
  });

  // Access telemetry tracking hooks
  const {
    mouseScore,
    status: mouseStatus,
    isTracking: isMouseTracking,
    isStepUpRequired,
    resetTrustScore,
  } = useMouseTracker({ intervalMs: 3500 });

  const {
    typingScore,
    status: typingStatus,
    isTracking: isKeystrokeTracking,
    metrics: keyMetrics,
  } = useKeystrokeTracker({ intervalMs: 4000 });

  const toggleSection = (section) => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const getStatusBadge = (statusText) => {
    switch (statusText) {
      case "Trusted":
      case "Low":
        return {
          bg: "bg-emerald-500/20",
          text: "text-emerald-400",
          border: "border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400 text-xs" />,
        };
      case "Suspicious":
      case "Medium":
        return {
          bg: "bg-yellow-500/20",
          text: "text-yellow-400",
          border: "border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400 text-xs" />,
        };
      default:
        return {
          bg: "bg-red-500/20",
          text: "text-red-400",
          border: "border-red-500/40",
          icon: <FaTimesCircle className="text-red-400 text-xs" />,
        };
    }
  };

  const mouseBadge = getStatusBadge(mouseStatus);
  const typingBadge = getStatusBadge(typingStatus);

  return (
    <>
      {/* Global Step-Up Authentication Challenge Modal */}
      <StepUpAuthModal
        isOpen={isStepUpRequired}
        trustScore={mouseScore}
        onVerificationSuccess={resetTrustScore}
      />

      {/* Floating Collapsible Live Status Tray */}
      <div className="fixed bottom-4 right-4 z-50 transition-all duration-300 max-w-sm w-80 font-sans">
        <div className="bg-slate-900/95 backdrop-blur-xl text-white border border-cyan-500/40 rounded-2xl shadow-2xl overflow-hidden shadow-cyan-950/50">
          
          {/* Header Bar (Exactly 40px Height when Collapsed) */}
          <div
            onClick={() => setIsMainExpanded(!isMainExpanded)}
            className="h-10 px-4 flex items-center justify-between cursor-pointer select-none bg-slate-900 hover:bg-slate-800/80 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
              </span>
              <span className="font-bold text-xs tracking-wide text-slate-100 flex items-center gap-1.5">
                <span>Live Status</span>
                <span className="text-[10px] text-cyan-400 font-mono font-medium">
                  ({mouseScore}/100)
                </span>
              </span>
            </div>

            <div className="flex items-center space-x-2 text-xs text-cyan-400 font-semibold">
              <span className="text-[11px] text-slate-400">
                {isMainExpanded ? "Collapse" : "Expand"}
              </span>
              {isMainExpanded ? (
                <FaChevronDown className="text-xs transition-transform" />
              ) : (
                <FaChevronUp className="text-xs transition-transform" />
              )}
            </div>
          </div>

          {/* Expanded Notification Drawer Content */}
          {isMainExpanded && (
            <div className="p-3 space-y-2 border-t border-slate-800/80 bg-slate-950/70 max-h-96 overflow-y-auto">
              
              {/* Section 1: Mouse Motion Auth */}
              <div className="bg-slate-900/90 rounded-xl border border-indigo-500/30 overflow-hidden text-xs">
                <div
                  onClick={() => toggleSection("mouse")}
                  className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-800/50 transition"
                >
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400 relative">
                      <FaMousePointer className="text-xs" />
                      {isMouseTracking && (
                        <span className="absolute -top-0.5 -right-0.5 flex h-1.5 w-1.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                        </span>
                      )}
                    </div>
                    <span className="font-bold text-slate-200">Mouse Motion Auth</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center gap-1 font-bold ${mouseBadge.bg} ${mouseBadge.text} ${mouseBadge.border}`}
                    >
                      {mouseBadge.icon}
                      {mouseStatus}
                    </span>
                    {openSections.mouse ? (
                      <FaChevronDown className="text-[10px] text-slate-500" />
                    ) : (
                      <FaChevronUp className="text-[10px] text-slate-500" />
                    )}
                  </div>
                </div>

                {openSections.mouse && (
                  <div className="px-3 pb-2.5 pt-1 text-[11px] text-slate-400 border-t border-slate-800/60 flex items-center justify-between">
                    <span>
                      Score: <strong className="text-indigo-300 font-mono">{mouseScore}/100</strong>
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <FaCompass className="text-indigo-400 text-[10px]" /> Angle Telemetry Active
                    </span>
                  </div>
                )}
              </div>

              {/* Section 2: Keystroke Biometrics */}
              <div className="bg-slate-900/90 rounded-xl border border-purple-500/30 overflow-hidden text-xs">
                <div
                  onClick={() => toggleSection("keyboard")}
                  className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-800/50 transition"
                >
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 bg-purple-500/10 rounded-lg text-purple-400 relative">
                      <FaKeyboard className="text-xs" />
                      {isKeystrokeTracking && (
                        <span className="absolute -top-0.5 -right-0.5 flex h-1.5 w-1.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-purple-500"></span>
                        </span>
                      )}
                    </div>
                    <span className="font-bold text-slate-200">Keystroke Biometrics</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center gap-1 font-bold ${typingBadge.bg} ${typingBadge.text} ${typingBadge.border}`}
                    >
                      {typingBadge.icon}
                      {typingStatus}
                    </span>
                    {openSections.keyboard ? (
                      <FaChevronDown className="text-[10px] text-slate-500" />
                    ) : (
                      <FaChevronUp className="text-[10px] text-slate-500" />
                    )}
                  </div>
                </div>

                {openSections.keyboard && (
                  <div className="px-3 pb-2.5 pt-1 text-[11px] text-slate-400 border-t border-slate-800/60 flex items-center justify-between">
                    <span>
                      Typing Score: <strong className="text-purple-300 font-mono">{typingScore}/100</strong>
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <FaTachometerAlt className="text-purple-400 text-[10px]" /> {keyMetrics.typingSpeed} WPM ({keyMetrics.avgHoldTime}ms hold)
                    </span>
                  </div>
                )}
              </div>

              {/* Section 3: AI Behavioural Telemetry */}
              <div className="bg-slate-900/90 rounded-xl border border-cyan-500/30 overflow-hidden text-xs">
                <div
                  onClick={() => toggleSection("telemetry")}
                  className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-800/50 transition"
                >
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 bg-cyan-500/10 rounded-lg text-cyan-400 relative">
                      <FaBrain className="text-xs animate-pulse" />
                    </div>
                    <span className="font-bold text-slate-200">AI Behavioural Telemetry</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/30 font-bold">
                      5s Loop
                    </span>
                    {openSections.telemetry ? (
                      <FaChevronDown className="text-[10px] text-slate-500" />
                    ) : (
                      <FaChevronUp className="text-[10px] text-slate-500" />
                    )}
                  </div>
                </div>

                {openSections.telemetry && (
                  <div className="px-3 pb-2.5 pt-1 text-[11px] text-slate-400 border-t border-slate-800/60 flex items-center justify-between">
                    <span>
                      Risk: <strong className="text-emerald-400 font-mono">Low</strong>
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <FaHeartbeat className="text-cyan-400 text-[10px]" /> Anomaly Score: 0.05
                    </span>
                  </div>
                )}
              </div>

            </div>
          )}

        </div>
      </div>
    </>
  );
}
