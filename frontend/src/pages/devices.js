import React, { useState, useEffect } from "react";
import axios from "axios";
import API_BASE_URL from "../config/api";
import Sidebar from "../components/Sidebar";
import useDeviceFingerprint from "../hooks/useDeviceFingerprint";
import DeviceMetricsGrid from "../components/DeviceMetricsGrid";
import DeviceSimilarityGauge from "../components/DeviceSimilarityGauge";
import DeviceHistoryTable from "../components/DeviceHistoryTable";

import {
  FaFingerprint,
  FaSync,
  FaClock,
  FaPlug,
  FaCheckCircle,
  FaLaptop,
} from "react-icons/fa";

const API_DEVICE_URL = `${API_BASE_URL}/api/device`;

export default function Devices() {
  const {
    fingerprint,
    fingerprintId,
    matchPercentage,
    riskLevel,
    trustScore,
    breakdown,
    isLoading,
    refreshFingerprint,
  } = useDeviceFingerprint({ autoVerify: true });

  const [sessionUptime, setSessionUptime] = useState(0);
  const [trustedDevices, setTrustedDevices] = useState([]);
  const [historyLogs, setHistoryLogs] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Uptime Timer
  useEffect(() => {
    const timer = setInterval(() => setSessionUptime((prev) => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatUptime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Fetch trusted devices & history logs from Flask backend
  const fetchDeviceData = async () => {
    setIsSyncing(true);
    const username = localStorage.getItem("username") || "anonymous_user";

    try {
      const [listRes, histRes] = await Promise.all([
        axios.get(`${API_DEVICE_URL}/trusted-list?username=${username}`),
        axios.get(`${API_DEVICE_URL}/history?username=${username}&limit=25`),
      ]);

      if (listRes.data && listRes.data.devices) {
        setTrustedDevices(listRes.data.devices);
      }
      if (histRes.data && histRes.data.history) {
        setHistoryLogs(histRes.data.history);
      }
    } catch (err) {
      console.warn("Using local device data stream:", err.message);
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    fetchDeviceData();
  }, [fingerprintId]);

  const handleRevoke = async (fpId) => {
    const username = localStorage.getItem("username") || "anonymous_user";
    try {
      await axios.post(`${API_DEVICE_URL}/revoke`, {
        username,
        fingerprint_id: fpId,
      });
      fetchDeviceData();
    } catch (err) {
      console.error("Failed to revoke device trust:", err);
    }
  };

  const handleManualSync = () => {
    refreshFingerprint();
    fetchDeviceData();
  };

  return (
    <div className="flex bg-slate-950 min-h-screen text-slate-100 font-sans">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content Container with Margin Clearing Sidebar */}
      <div className="flex-1 pl-[260px] p-6 overflow-y-auto min-h-screen space-y-6">
        
        {/* Top Session Status Banner */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-6 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 relative overflow-hidden">
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center space-x-4">
            <div className="p-4 bg-cyan-500/10 rounded-2xl border border-cyan-500/30 text-cyan-400">
              <FaFingerprint className="text-3xl animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-extrabold tracking-tight text-white">
                  Device Fingerprinting Framework
                </h1>
                <span className="text-xs px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                  Live Zero-Trust Biometrics
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Continuous browser biometrics capture, HTML5 Canvas hashing, WebGL GPU vendor verification, and weighted fuzzy similarity analysis.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Session Uptime */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold flex items-center gap-1">
                <FaClock className="text-cyan-400" /> Session Uptime
              </span>
              <span className="text-cyan-300 font-bold">{formatUptime(sessionUptime)}</span>
            </div>

            {/* AI Engine Status */}
            <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold flex items-center gap-1">
                <FaPlug className="text-emerald-400" /> Matching Engine
              </span>
              <span className="font-bold flex items-center gap-1 text-emerald-400">
                <FaCheckCircle className="text-[10px]" />
                Weighted Fuzzy Matcher
              </span>
            </div>

            {/* Manual Sync Button */}
            <button
              onClick={handleManualSync}
              disabled={isSyncing || isLoading}
              className="flex items-center space-x-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 px-4 py-2.5 rounded-xl transition text-xs font-bold shadow-lg"
            >
              <FaSync className={isSyncing ? "animate-spin" : ""} />
              <span>{isSyncing ? "Evaluating..." : "Sync Biometrics"}</span>
            </button>
          </div>
        </div>

        {/* 1. Device Hardware & Biometrics Metrics Grid */}
        <DeviceMetricsGrid
          fingerprintId={fingerprintId}
          fingerprint={fingerprint || {}}
          trustScore={trustScore}
        />

        {/* 2. Device Similarity Meter & Baseline Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <DeviceSimilarityGauge
              matchPercentage={matchPercentage}
              riskLevel={riskLevel}
              breakdown={breakdown}
            />
          </div>

          <div className="lg:col-span-1 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FaLaptop className="text-cyan-400" />
              <span>Device Biometric Signatures</span>
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-sans">Canvas Signature</span>
                <span className="text-cyan-300 font-bold truncate block">{fingerprint?.canvas_hash || "Generating..."}</span>
              </div>

              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-sans">WebGL GPU Vendor</span>
                <span className="text-purple-300 font-bold truncate block">{fingerprint?.webgl_vendor || "WebGL Active"}</span>
              </div>

              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-sans">Timezone & Locale</span>
                <span className="text-emerald-400 font-bold truncate block">{fingerprint?.timezone || "Asia/Kolkata"} ({fingerprint?.language || "en-US"})</span>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Trusted Devices Manager & Audit History Table */}
        <DeviceHistoryTable
          devices={trustedDevices}
          history={historyLogs}
          isSyncing={isSyncing}
          onRefresh={handleManualSync}
          onRevoke={handleRevoke}
        />
      </div>
    </div>
  );
}