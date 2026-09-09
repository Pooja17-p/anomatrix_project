import React from "react";
import {
  FaKeyboard,
  FaClock,
  FaPlaneDeparture,
  FaWaveSquare,
  FaExclamationTriangle,
} from "react-icons/fa";

export default function KeystrokeMetricsGrid({
  typingSpeed = 55,
  avgHoldTime = 90,
  avgFlightTime = 140,
  rhythmVariance = 35,
  errorRate = 0.04,
  keypressCount = 0,
}) {
  const stats = [
    {
      title: "Typing Speed",
      value: `${typingSpeed}`,
      unit: "WPM",
      subtext: "Words Per Minute Velocity",
      icon: <FaKeyboard className="text-cyan-400 text-xl" />,
      iconBg: "bg-cyan-500/10 border-cyan-500/30",
    },
    {
      title: "Avg Key Hold Time",
      value: `${avgHoldTime}`,
      unit: "ms",
      subtext: "Press to Release Duration",
      icon: <FaClock className="text-indigo-400 text-xl" />,
      iconBg: "bg-indigo-500/10 border-indigo-500/30",
    },
    {
      title: "Avg Key Flight Time",
      value: `${avgFlightTime}`,
      unit: "ms",
      subtext: "Inter-Key Transition Delay",
      icon: <FaPlaneDeparture className="text-purple-400 text-xl" />,
      iconBg: "bg-purple-500/10 border-purple-500/30",
    },
    {
      title: "Rhythm Consistency",
      value: `${rhythmVariance}`,
      unit: "std dev",
      subtext: rhythmVariance < 25 ? "Consistent Rhythm" : "High Cadence Variance",
      icon: <FaWaveSquare className="text-emerald-400 text-xl" />,
      iconBg: "bg-emerald-500/10 border-emerald-500/30",
    },
    {
      title: "Backspace Error Rate",
      value: `${(errorRate * 100).toFixed(1)}%`,
      unit: "errors",
      subtext: `${keypressCount} total keypresses`,
      icon: <FaExclamationTriangle className="text-rose-400 text-xl" />,
      iconBg: "bg-rose-500/10 border-rose-500/30",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {stats.map((stat, idx) => (
        <div
          key={idx}
          className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-slate-700/80 transition-all duration-300 flex items-center space-x-4"
        >
          <div className={`p-3.5 rounded-2xl border ${stat.iconBg} flex-shrink-0`}>
            {stat.icon}
          </div>

          <div className="flex-1 min-w-0">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider truncate">
              {stat.title}
            </div>
            <div className="text-xl font-extrabold text-white mt-1 font-mono tracking-tight flex items-baseline gap-1 truncate">
              <span>{stat.value}</span>
              {stat.unit && <span className="text-xs font-normal text-slate-400">{stat.unit}</span>}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 truncate">{stat.subtext}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
