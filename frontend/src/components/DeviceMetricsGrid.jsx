import React from "react";
import {
  FaFingerprint,
  FaLaptop,
  FaMicrochip,
  FaDesktop,
} from "react-icons/fa";

export default function DeviceMetricsGrid({
  fingerprintId = "a4f8901bce23991209ffae7812...",
  fingerprint = {},
  trustScore = 100,
}) {
  const stats = [
    {
      title: "SHA-256 Fingerprint ID",
      value: fingerprintId ? `${fingerprintId.substring(0, 16)}...` : "Extracting...",
      unit: "",
      subtext: "Immutable Cryptographic Signature",
      icon: <FaFingerprint className="text-cyan-400 text-xl" />,
      iconBg: "bg-cyan-500/10 border-cyan-500/30",
    },
    {
      title: "Browser & Environment",
      value: fingerprint.browser_name ? `${fingerprint.browser_name} ${fingerprint.browser_version?.split(".")[0]}` : "Chrome 124",
      unit: "",
      subtext: `${fingerprint.os || "Windows"} (${fingerprint.platform || "Win32"})`,
      icon: <FaLaptop className="text-indigo-400 text-xl" />,
      iconBg: "bg-indigo-500/10 border-indigo-500/30",
    },
    {
      title: "Hardware Specs",
      value: `${fingerprint.hardware_concurrency || 8} Cores`,
      unit: `${fingerprint.device_memory || 8}GB RAM`,
      subtext: fingerprint.webgl_renderer ? fingerprint.webgl_renderer.substring(0, 22) + "..." : "NVIDIA GPU",
      icon: <FaMicrochip className="text-purple-400 text-xl" />,
      iconBg: "bg-purple-500/10 border-purple-500/30",
    },
    {
      title: "Display & Canvas Hash",
      value: fingerprint.screen_resolution || "1920x1080",
      unit: `${fingerprint.color_depth || 24}bit`,
      subtext: fingerprint.canvas_hash ? `Canvas: ${fingerprint.canvas_hash.substring(0, 14)}...` : "Canvas Verified",
      icon: <FaDesktop className="text-emerald-400 text-xl" />,
      iconBg: "bg-emerald-500/10 border-emerald-500/30",
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
            <div className="text-base font-extrabold text-white mt-1 font-mono tracking-tight flex items-baseline gap-1 truncate">
              <span>{stat.value}</span>
              {stat.unit && <span className="text-xs font-normal text-cyan-300">{stat.unit}</span>}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 truncate">{stat.subtext}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
