import React, { useState } from "react";
import {
  FaHistory,
  FaSearch,
  FaFilter,
  FaCheckCircle,
  FaExclamationTriangle,
  FaTimesCircle,
  FaSync,
} from "react-icons/fa";

export default function KeystrokeActivityTable({
  history = [],
  isSyncing = false,
  onRefresh,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");

  const getRiskBadge = (risk) => {
    switch ((risk || "").toUpperCase()) {
      case "CRITICAL":
        return {
          bg: "bg-red-500/20 text-red-400 border-red-500/40",
          icon: <FaTimesCircle className="text-red-400" />,
        };
      case "HIGH":
        return {
          bg: "bg-orange-500/20 text-orange-400 border-orange-500/40",
          icon: <FaExclamationTriangle className="text-orange-400" />,
        };
      case "MEDIUM":
        return {
          bg: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
          icon: <FaExclamationTriangle className="text-yellow-400" />,
        };
      default:
        return {
          bg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          icon: <FaCheckCircle className="text-emerald-400" />,
        };
    }
  };

  const filteredHistory = history.filter((item) => {
    const matchesRisk =
      riskFilter === "ALL" || (item.riskLevel || "").toUpperCase() === riskFilter;
    const matchesSearch =
      searchTerm === "" ||
      item.timestamp?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.status?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesRisk && matchesSearch;
  });

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Table Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-cyan-500/10 rounded-xl border border-cyan-500/30 text-cyan-400">
            <FaHistory className="text-xl" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Keystroke Authentication & Prediction Logs</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-medium">
                {history.length} Snapshots
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Captured keyboard biometrics and Isolation Forest evaluation history
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Search Input */}
          <div className="relative">
            <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:border-cyan-500/50 w-36 sm:w-44"
            />
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-xl px-2 py-1.5">
            <FaFilter className="text-slate-500 text-xs" />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Risks</option>
              <option value="LOW" className="bg-slate-900">Low Risk</option>
              <option value="MEDIUM" className="bg-slate-900">Medium Risk</option>
              <option value="HIGH" className="bg-slate-900">High Risk</option>
              <option value="CRITICAL" className="bg-slate-900">Critical Risk</option>
            </select>
          </div>

          {/* Refresh Trigger */}
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

      {/* Log Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800/80">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 uppercase text-slate-400 text-[11px] font-semibold tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3.5 px-4">Timestamp</th>
              <th className="py-3.5 px-4">Typing Speed</th>
              <th className="py-3.5 px-4">Hold Time</th>
              <th className="py-3.5 px-4">Flight Time</th>
              <th className="py-3.5 px-4">Keypresses / Errors</th>
              <th className="py-3.5 px-4">Trust Score</th>
              <th className="py-3.5 px-4">Risk Level</th>
              <th className="py-3.5 px-4">Session Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
            {filteredHistory.length === 0 ? (
              <tr>
                <td colSpan="8" className="text-center py-8 text-slate-500 font-sans">
                  No keystroke logs captured yet. Type in any input field to generate telemetry.
                </td>
              </tr>
            ) : (
              filteredHistory.map((row) => {
                const badge = getRiskBadge(row.riskLevel);
                return (
                  <tr key={row.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 text-slate-400 font-medium">{row.timestamp}</td>
                    <td className="py-3 px-4 text-cyan-300 font-semibold">{row.typingSpeed} WPM</td>
                    <td className="py-3 px-4">{row.holdTime} ms</td>
                    <td className="py-3 px-4 text-purple-300">{row.flightTime} ms</td>
                    <td className="py-3 px-4 text-slate-300">
                      {row.keypresses} keys | {row.errors} errors
                    </td>
                    <td className="py-3 px-4 font-bold text-white">{row.trustScore} / 100</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[10px] font-extrabold uppercase ${badge.bg}`}
                      >
                        {badge.icon}
                        {row.riskLevel || "LOW"}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans font-semibold text-slate-300">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        {row.status || "Trusted"}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
