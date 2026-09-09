import React, { useState } from "react";
import {
  FaShieldAlt,
  FaInfoCircle,
  FaCheckCircle,
  FaMousePointer,
  FaKeyboard,
  FaFingerprint,
  FaChevronDown,
  FaChevronUp,
} from "react-icons/fa";

export default function SecurityConditionsBanner({ title = "Zero-Trust Security Conditions" }) {
  const [isExpanded, setIsExpanded] = useState(true);

  const conditions = [
    {
      icon: <FaMousePointer className="text-cyan-400 text-xs" />,
      title: "Mouse Kinematics & Velocity Tracking",
      desc: "Continuous trajectory, cursor acceleration, and curvature index are analyzed in real-time.",
    },
    {
      icon: <FaKeyboard className="text-purple-400 text-xs" />,
      title: "Keystroke Biometric Cadence",
      desc: "Key press hold times, inter-key flight latencies, WPM, and error rate profile typing dynamics.",
    },
    {
      icon: <FaFingerprint className="text-emerald-400 text-xs" />,
      title: "Device Fingerprinting & SHA-256 Baseline",
      desc: "Canvas signature, WebGL renderer, and hardware specs are hashed for fuzzy similarity matching.",
    },
    {
      icon: <FaShieldAlt className="text-yellow-400 text-xs" />,
      title: "Automated Step-Up Authentication",
      desc: "Trust scores below threshold (< 55) trigger mandatory Face Verification or OTP challenge.",
    },
  ];

  return (
    <div className="bg-slate-900/90 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-4 mb-5 shadow-2xl text-slate-200 text-xs max-w-md w-full font-sans transition-all duration-300">
      {/* Banner Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between cursor-pointer select-none pb-1"
      >
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-cyan-500/15 rounded-xl border border-cyan-500/30 text-cyan-400">
            <FaShieldAlt className="text-sm animate-pulse" />
          </div>
          <div>
            <h3 className="font-bold text-white text-xs tracking-wide flex items-center gap-1.5">
              <span>{title}</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold uppercase">
                Active Protocol
              </span>
            </h3>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Please review zero-trust authentication conditions before proceeding
            </p>
          </div>
        </div>

        <button className="text-slate-400 hover:text-cyan-400 transition p-1">
          {isExpanded ? (
            <FaChevronUp className="text-xs" />
          ) : (
            <FaChevronDown className="text-xs" />
          )}
        </button>
      </div>

      {/* Expanded Protocol Details */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2.5">
          <div className="grid grid-cols-1 gap-2">
            {conditions.map((item, idx) => (
              <div
                key={idx}
                className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/80 flex items-start space-x-2.5"
              >
                <div className="mt-0.5 p-1 bg-slate-900 rounded-lg border border-slate-800 flex-shrink-0">
                  {item.icon}
                </div>
                <div>
                  <div className="font-bold text-slate-200 text-[11px] flex items-center gap-1">
                    <span>{item.title}</span>
                    <FaCheckCircle className="text-emerald-400 text-[9px]" />
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                    {item.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center space-x-1.5 text-[10px] text-cyan-300 bg-cyan-500/10 p-2 rounded-xl border border-cyan-500/20 font-medium">
            <FaInfoCircle className="text-xs flex-shrink-0 text-cyan-400" />
            <span>
              By filling the form and logging in, you consent to continuous zero-trust behavioral verification.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
