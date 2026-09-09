import React, { useState } from "react";
import {
  FaLaptop,
  FaSearch,
  FaCheckCircle,
  FaExclamationTriangle,
  FaTimesCircle,
  FaSync,
  FaTrashAlt,
} from "react-icons/fa";

export default function DeviceHistoryTable({
  devices = [],
  history = [],
  isSyncing = false,
  onRefresh,
  onRevoke,
}) {
  const [activeTab, setActiveTab] = useState("trusted"); // "trusted" or "logs"
  const [searchTerm, setSearchTerm] = useState("");

  const getRiskBadge = (risk) => {
    switch ((risk || "").toUpperCase()) {
      case "HIGH RISK":
      case "CRITICAL":
      case "REVOKED":
        return {
          bg: "bg-red-500/20 text-red-400 border-red-500/40",
          icon: <FaTimesCircle className="text-red-400 text-xs" />,
        };
      case "MEDIUM RISK":
      case "SUSPICIOUS":
        return {
          bg: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400 text-xs" />,
        };
      default:
        return {
          bg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400 text-xs" />,
        };
    }
  };

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Tab Selectors and Search Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-cyan-500/10 rounded-xl border border-cyan-500/30 text-cyan-400">
            <FaLaptop className="text-xl" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setActiveTab("trusted")}
                className={`text-base font-bold transition px-2 py-0.5 rounded-lg ${
                  activeTab === "trusted"
                    ? "text-white bg-slate-800"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Registered Trusted Devices ({devices.length})
              </button>
              <span className="text-slate-600">|</span>
              <button
                onClick={() => setActiveTab("logs")}
                className={`text-base font-bold transition px-2 py-0.5 rounded-lg ${
                  activeTab === "logs"
                    ? "text-white bg-slate-800"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Verification Audit Logs ({history.length})
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuous hardware biometrics signature matching & trust revocation
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Search Input */}
          <div className="relative">
            <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
            <input
              type="text"
              placeholder="Search devices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-cyan-500/50 w-36 sm:w-44"
            />
          </div>

          <button
            onClick={onRefresh}
            disabled={isSyncing}
            className="flex items-center space-x-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 px-3 py-1.5 rounded-xl transition text-xs font-semibold"
          >
            <FaSync className={`text-xs ${isSyncing ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">{isSyncing ? "Syncing" : "Refresh"}</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Registered Trusted Devices Table */}
      {activeTab === "trusted" && (
        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 uppercase text-slate-400 text-[11px] font-semibold tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Device Name</th>
                <th className="py-3.5 px-4">SHA-256 Fingerprint ID</th>
                <th className="py-3.5 px-4">Browser & OS</th>
                <th className="py-3.5 px-4">First Verified</th>
                <th className="py-3.5 px-4">Last Active</th>
                <th className="py-3.5 px-4">Trust Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
              {devices.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 font-sans">
                    No registered trusted devices found. Load this dashboard on your primary browser to register your baseline.
                  </td>
                </tr>
              ) : (
                devices
                  .filter(
                    (d) =>
                      !searchTerm ||
                      d.device_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      d.fingerprint_id?.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((dev) => {
                    const badge = getRiskBadge(dev.status);
                    return (
                      <tr key={dev.fingerprint_id} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-sans font-bold text-white">
                          {dev.device_name || "Primary Workstation"}
                        </td>
                        <td className="py-3 px-4 text-cyan-300 font-semibold">
                          {dev.fingerprint_id?.substring(0, 16)}...
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          {dev.attributes?.browser_name} {dev.attributes?.browser_version?.split(".")[0]} on {dev.attributes?.os}
                        </td>
                        <td className="py-3 px-4 text-slate-400">{dev.first_seen ? new Date(dev.first_seen).toLocaleDateString() : "Today"}</td>
                        <td className="py-3 px-4 text-slate-400">{dev.last_verified ? new Date(dev.last_verified).toLocaleTimeString() : "Live"}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${badge.bg}`}>
                            {badge.icon}
                            {dev.status || "Trusted"}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => onRevoke && onRevoke(dev.fingerprint_id)}
                            className="bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/40 px-2.5 py-1 rounded-lg transition text-[11px] font-sans font-semibold inline-flex items-center gap-1"
                          >
                            <FaTrashAlt className="text-[10px]" />
                            Revoke
                          </button>
                        </td>
                      </tr>
                    );
                  })
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Verification Audit Logs Table */}
      {activeTab === "logs" && (
        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 uppercase text-slate-400 text-[11px] font-semibold tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4">Fingerprint ID</th>
                <th className="py-3.5 px-4">Match %</th>
                <th className="py-3.5 px-4">Canvas / WebGL</th>
                <th className="py-3.5 px-4">Hardware Cores</th>
                <th className="py-3.5 px-4">Risk Level</th>
                <th className="py-3.5 px-4">Verification Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
              {history.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 font-sans">
                    No verification audit logs captured yet.
                  </td>
                </tr>
              ) : (
                history.map((log, idx) => {
                  const badge = getRiskBadge(log.risk_level);
                  return (
                    <tr key={idx} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 text-slate-400">{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "Live"}</td>
                      <td className="py-3 px-4 text-cyan-300">{log.fingerprint_id?.substring(0, 16)}...</td>
                      <td className="py-3 px-4 font-bold text-emerald-400">{log.match_percentage}%</td>
                      <td className="py-3 px-4 text-slate-300">
                        {log.attributes?.canvas_hash ? log.attributes.canvas_hash.substring(0, 12) : "Canvas"} | {log.attributes?.webgl_vendor || "GPU"}
                      </td>
                      <td className="py-3 px-4">{log.attributes?.hardware_concurrency || 8} Cores | {log.attributes?.device_memory || 8}GB RAM</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${badge.bg}`}>
                          {badge.icon}
                          {log.risk_level || "Trusted"}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans font-semibold text-slate-200">{log.status || "Verified"}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
