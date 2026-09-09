import React from "react";
import {
  FaMousePointer,
  FaTachometerAlt,
  FaChartLine,
  FaRoute,
  FaBolt,
  FaWaveSquare,
  FaHandPointer,
  FaScroll,
} from "react-icons/fa";

export default function MovementStatsGrid({
  livePosition = { x: 0, y: 0 },
  currentSpeed = 0,
  avgSpeed = 0,
  peakSpeed = 0,
  acceleration = 0,
  totalDistance = 0,
  curvatureIndex = 1.0,
  clickCount = 0,
  scrollCount = 0,
}) {
  const stats = [
    {
      title: "Live Mouse Position",
      value: `X: ${livePosition.x}, Y: ${livePosition.y}`,
      subtext: "Screen Canvas Coordinates",
      icon: <FaMousePointer className="text-cyan-400 text-xl" />,
      iconBg: "bg-cyan-500/10 border-cyan-500/30",
      accentColor: "text-cyan-400",
    },
    {
      title: "Current Speed",
      value: `${currentSpeed.toLocaleString()}`,
      unit: "px/s",
      subtext: `Peak: ${peakSpeed.toLocaleString()} px/s`,
      icon: <FaTachometerAlt className="text-emerald-400 text-xl" />,
      iconBg: "bg-emerald-500/10 border-emerald-500/30",
      accentColor: "text-emerald-400",
    },
    {
      title: "Average Speed",
      value: `${avgSpeed.toLocaleString()}`,
      unit: "px/s",
      subtext: "Rolling Window Velocity",
      icon: <FaChartLine className="text-indigo-400 text-xl" />,
      iconBg: "bg-indigo-500/10 border-indigo-500/30",
      accentColor: "text-indigo-400",
    },
    {
      title: "Acceleration",
      value: `${acceleration.toLocaleString()}`,
      unit: "px/s²",
      subtext: "Instantaneous Kinematic Delta",
      icon: <FaBolt className="text-amber-400 text-xl" />,
      iconBg: "bg-amber-500/10 border-amber-500/30",
      accentColor: "text-amber-400",
    },
    {
      title: "Total Distance",
      value: `${totalDistance.toLocaleString()}`,
      unit: "px",
      subtext: `~${(totalDistance * 0.000264583).toFixed(2)} meters`,
      icon: <FaRoute className="text-purple-400 text-xl" />,
      iconBg: "bg-purple-500/10 border-purple-500/30",
      accentColor: "text-purple-400",
    },
    {
      title: "Curvature / Jitter",
      value: `${curvatureIndex}`,
      unit: "ratio",
      subtext: curvatureIndex > 1.8 ? "High Entropy (Human)" : "Straight Path",
      icon: <FaWaveSquare className="text-rose-400 text-xl" />,
      iconBg: "bg-rose-500/10 border-rose-500/30",
      accentColor: "text-rose-400",
    },
    {
      title: "Clicks Captured",
      value: `${clickCount}`,
      unit: "clicks",
      subtext: "Active Mouse Clicks",
      icon: <FaHandPointer className="text-sky-400 text-xl" />,
      iconBg: "bg-sky-500/10 border-sky-500/30",
      accentColor: "text-sky-400",
    },
    {
      title: "Scroll Events",
      value: `${scrollCount}`,
      unit: "events",
      subtext: "Wheel Scroll Behaviors",
      icon: <FaScroll className="text-teal-400 text-xl" />,
      iconBg: "bg-teal-500/10 border-teal-500/30",
      accentColor: "text-teal-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
            <div className="text-xl font-extrabold text-white mt-1 font-mono tracking-tight flex items-baseline gap-1.5 truncate">
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
