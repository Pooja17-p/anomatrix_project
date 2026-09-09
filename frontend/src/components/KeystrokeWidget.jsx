import React from "react";
import useKeystrokeTracker from "../hooks/useKeystrokeTracker";
import { FaKeyboard, FaShieldAlt, FaTachometerAlt, FaCheckCircle, FaExclamationTriangle, FaTimesCircle } from "react-icons/fa";

export default function KeystrokeWidget() {
  const { typingScore, status, isTracking, metrics } = useKeystrokeTracker({ intervalMs: 4000 });

  const getStatusColor = (statusText) => {
    switch (statusText) {
      case "Trusted":
        return {
          bg: "bg-emerald-500/20",
          text: "text-emerald-400",
          border: "border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400" />,
        };
      case "Suspicious":
        return {
          bg: "bg-yellow-500/20",
          text: "text-yellow-400",
          border: "border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400" />,
        };
      default:
        return {
          bg: "bg-red-500/20",
          text: "text-red-400",
          border: "border-red-500/40",
          icon: <FaTimesCircle className="text-red-400" />,
        };
    }
  };

  const style = getStatusColor(status);

  return (
    <div className="fixed bottom-4 left-64 z-50 transition-all duration-300">
      <div className="bg-slate-900/90 backdrop-blur-md text-white border border-purple-500/30 rounded-xl p-3 shadow-2xl shadow-purple-950/40 flex items-center space-x-3 text-xs">
        <div className="p-2.5 bg-purple-500/10 rounded-lg border border-purple-500/30 text-purple-400 relative">
          <FaKeyboard className="text-base" />
          {isTracking && (
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
            </span>
          )}
        </div>

        <div>
          <div className="font-semibold flex items-center gap-1.5 text-slate-200">
            <span>Keystroke Biometrics</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center gap-1 font-bold ${style.bg} ${style.text} ${style.border}`}>
              {style.icon}
              {status}
            </span>
          </div>

          <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-1">
            <span>Typing Score: <strong className="text-purple-300 font-mono text-xs">{typingScore}/100</strong></span>
            <span>•</span>
            <span className="text-slate-400 flex items-center gap-1">
              <FaTachometerAlt className="text-purple-400 text-[10px]" /> {metrics.typingSpeed} WPM ({metrics.avgHoldTime}ms hold)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
