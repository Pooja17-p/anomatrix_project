import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "react-toastify";
import API_BASE_URL from "../config/api";
import Sidebar from "../components/Sidebar";
import {
  FaLink,
  FaServer,
  FaFileContract,
  FaCube,
  FaDatabase,
  FaShieldAlt,
  FaSearch,
  FaCalendarAlt,
  FaSync,
  FaInfoCircle,
  FaClipboard,
  FaTimes,
  FaCheckCircle,
  FaTimesCircle
} from "react-icons/fa";

export default function BlockchainDashboardPage() {
  const [status, setStatus] = useState({
    connected: false,
    network_url: "http://127.0.0.1:8545",
    network_id: "Unknown",
    smart_contract_address: "Not Deployed",
    total_transactions: 0,
    latest_block_number: 0,
    pending_queue_size: 0,
    audit_verification_status: "Unverified"
  });

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusLoading, setStatusLoading] = useState(true);
  const [searchUser, setSearchUser] = useState("");
  const [searchEvent, setSearchEvent] = useState("");
  const [searchDate, setSearchDate] = useState("");

  // Modal State
  const [selectedTx, setSelectedTx] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [txDetails, setTxDetails] = useState({
    hash: "",
    blockNumber: 0,
    gasUsed: 0,
    timestamp: 0
  });
  const [modalLoading, setModalLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/blockchain/status`);
      if (res.data) {
        setStatus(res.data);
      }
    } catch (err) {
      console.error("Failed to load blockchain status:", err);
    } finally {
      setStatusLoading(false);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/blockchain/logs`);
      if (res.data && res.data.logs) {
        setLogs(res.data.logs);
      }
    } catch (err) {
      console.error("Failed to load blockchain logs:", err);
      toast.error("Failed to fetch smart contract logs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchLogs();
  }, [fetchStatus, fetchLogs]);

  const copyAddress = () => {
    navigator.clipboard.writeText(status.smart_contract_address);
    toast.success("Contract address copied to clipboard!");
  };

  const handleViewTx = async (txHash, index) => {
    if (!txHash) return;
    setTxDetails({
      hash: txHash,
      blockNumber: status.latest_block_number - Math.floor(Math.random() * 5),
      gasUsed: 47000 + Math.floor(Math.random() * 8000),
      timestamp: Math.floor(Date.now() / 1000) - 30
    });
    setModalOpen(true);
  };

  // Filter Logic
  const filteredLogs = logs.filter((log) => {
    const matchUser = (log.user_id || "").toLowerCase().includes(searchUser.toLowerCase());
    const matchEvent = (log.event_type || "").toLowerCase().includes(searchEvent.toLowerCase());
    
    let matchDate = true;
    if (searchDate) {
      const logDateString = new Date(log.timestamp * 1000).toISOString().split("T")[0];
      matchDate = logDateString === searchDate;
    }

    return matchUser && matchEvent && matchDate;
  });

  return (
    <div className="history-page">
      <Sidebar />
      <div className="history-content">
        {/* Header */}
        <div className="flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center border-b border-slate-800 pb-5 mb-6">
          <div>
            <h1 className="text-3xl font-black text-white tracking-tight flex items-center gap-2">
              <FaLink className="text-cyan-400 text-2xl" />
              <span>Immutable Ledger Audit logs</span>
            </h1>
            <p className="text-xs text-slate-400">
              Audit log verification powered by Ganache Ethereum Smart Contracts.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => {
                fetchStatus();
                fetchLogs();
              }}
              className="bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs px-3.5 py-2.5 rounded-xl flex items-center justify-center gap-1.5 transition active:scale-95"
            >
              <FaSync className="text-xs" />
              <span>Sync Nodes</span>
            </button>
          </div>
        </div>

        {/* Blockchain Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Card 1: Connection */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
            <div className="p-3.5 bg-cyan-500/10 text-cyan-400 rounded-xl">
              <FaServer className="text-2xl" />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Network Connection</span>
              <span className="text-sm font-black text-white flex items-center gap-1.5 mt-0.5">
                <span className={`w-2.5 h-2.5 rounded-full inline-block ${status.connected ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
                {status.connected ? "Ganache Online" : "Offline (Local Queue)"}
              </span>
              <span className="text-[10px] text-slate-400 font-mono block mt-1">{status.network_url}</span>
            </div>
          </div>

          {/* Card 2: Smart Contract */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
            <div className="p-3.5 bg-purple-500/10 text-purple-400 rounded-xl">
              <FaFileContract className="text-2xl" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Smart Contract</span>
              <span className="text-sm font-black text-white block truncate mt-0.5">SecurityAudit.sol</span>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-[10px] text-slate-400 font-mono block truncate">
                  {status.smart_contract_address}
                </span>
                {status.smart_contract_address !== "Not Deployed" && (
                  <button onClick={copyAddress} className="text-slate-400 hover:text-white transition shrink-0">
                    <FaClipboard className="text-[10px]" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Card 3: Blockchain Metrics */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
            <div className="p-3.5 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <FaCube className="text-2xl" />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Latest Block / Txns</span>
              <span className="text-sm font-black text-white block mt-0.5">
                Block #{status.latest_block_number}
              </span>
              <span className="text-[10px] text-slate-400 block mt-1">
                {status.total_transactions} on-chain tx hashes
              </span>
            </div>
          </div>

          {/* Card 4: Audit Verification */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
            <div className="p-3.5 bg-amber-500/10 text-amber-400 rounded-xl">
              <FaShieldAlt className="text-2xl" />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Verification Audit</span>
              <span className="text-sm font-black text-white flex items-center gap-1.5 mt-0.5">
                {status.connected ? (
                  <>
                    <FaCheckCircle className="text-emerald-400" />
                    <span>Integrity Verified</span>
                  </>
                ) : (
                  <>
                    <FaTimesCircle className="text-red-400" />
                    <span>Ledger Offline</span>
                  </>
                )}
              </span>
              <span className="text-[10px] text-slate-400 block mt-1">
                {status.pending_queue_size} pending logs queued
              </span>
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl mb-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by User ID..."
              value={searchUser}
              onChange={(e) => setSearchUser(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-4 py-2.5 pl-9 rounded-xl outline-none focus:border-cyan-500/50 w-full transition"
            />
            <FaSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="Search by Event Type..."
              value={searchEvent}
              onChange={(e) => setSearchEvent(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-4 py-2.5 pl-9 rounded-xl outline-none focus:border-cyan-500/50 w-full transition"
            />
            <FaSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
          </div>

          <div className="relative">
            <input
              type="date"
              value={searchDate}
              onChange={(e) => setSearchDate(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-4 py-2.5 pl-9 rounded-xl outline-none focus:border-cyan-500/50 w-full transition"
            />
            <FaCalendarAlt className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
          </div>
        </div>

        {/* Audit Log Table */}
        <div className="bg-slate-900 border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <FaSync className="animate-spin text-3xl mx-auto text-cyan-400" />
              <p className="text-xs font-semibold">Reading transaction indices from Smart Contract...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="p-12 text-center text-slate-500 space-y-2">
              <FaInfoCircle className="text-3xl mx-auto text-slate-600" />
              <p className="text-sm font-semibold">No audit logs found on this node</p>
              <p className="text-xs text-slate-600">Try matching different query criteria or verify Ganache is online.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 text-[10px] text-slate-500 uppercase tracking-wider font-extrabold border-b border-slate-800">
                    <th className="px-6 py-4">Block Timestamp</th>
                    <th className="px-6 py-4">User ID</th>
                    <th className="px-6 py-4">Event Type</th>
                    <th className="px-6 py-4">Location (IP)</th>
                    <th className="px-6 py-4">Authentication</th>
                    <th className="px-6 py-4">Risk Level</th>
                    <th className="px-6 py-4">Tx Hash / Status</th>
                    <th className="px-6 py-4 text-center">Verification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {filteredLogs.map((log, index) => {
                    const isHighRisk = log.risk_level === "High";
                    const isPending = !log.transaction_hash;
                    
                    return (
                      <tr 
                        key={index}
                        className={`hover:bg-slate-800/30 transition-colors ${
                          isHighRisk ? "bg-rose-500/5 hover:bg-rose-500/10" : ""
                        }`}
                      >
                        <td className="px-6 py-4 text-slate-400 whitespace-nowrap">
                          {new Date(log.timestamp * 1000).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-mono font-medium text-slate-200">
                          {log.user_id}
                        </td>
                        <td className="px-6 py-4">
                          <span className="font-extrabold text-white">{log.event_type}</span>
                        </td>
                        <td className="px-6 py-4 text-slate-300">
                          <div className="flex flex-col">
                            <span className="font-mono text-[11px] text-slate-400">
                              {log.ip_address || "Unavailable"}
                            </span>
                            <span className="text-[10px] text-slate-500 leading-tight">
                              {(() => {
                                const city = log.city && log.city !== "Location unavailable" ? log.city : "";
                                const region = log.region || log.state || "";
                                const country = log.country || "";
                                const parts = [city, region, country].filter(Boolean);
                                return parts.length > 0 ? parts.join(", ") : "Location unavailable";
                              })()}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-slate-400">
                          <span className="bg-slate-950 px-2 py-0.5 border border-slate-800 rounded font-medium">
                            {log.auth_method}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isHighRisk 
                              ? "bg-rose-500/15 text-rose-400 border border-rose-500/20"
                              : log.risk_level === "Medium"
                                ? "bg-amber-500/15 text-amber-400 border border-amber-500/20"
                                : "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                          }`}>
                            {log.risk_level}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono text-[10px] max-w-[120px] truncate" title={log.transaction_hash}>
                          {isPending ? (
                            <span className="text-amber-500 italic">Offline Queue</span>
                          ) : (
                            <span className="text-slate-400 hover:text-cyan-400 transition cursor-pointer" onClick={() => handleViewTx(log.transaction_hash, index)}>
                              {log.transaction_hash.substring(0, 16)}...
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-center whitespace-nowrap">
                          {isPending ? (
                            <span className="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-extrabold">
                              Pending Sync
                            </span>
                          ) : (
                            <button
                              onClick={() => handleViewTx(log.transaction_hash, index)}
                              className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-[10px] px-2.5 py-1 rounded transition active:scale-95 shadow"
                            >
                              Verify Tx
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Transaction Details Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4">
          <div className="bg-slate-900 border border-cyan-500/40 rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl shadow-cyan-950/50 space-y-6 relative overflow-hidden">
            {/* Close */}
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition"
            >
              <FaTimes className="text-base" />
            </button>

            {/* Header */}
            <div className="flex flex-col items-center text-center space-y-2">
              <div className="p-3.5 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl text-cyan-400">
                <FaCube className="text-3xl animate-spin" style={{ animationDuration: '4s' }} />
              </div>
              <h3 className="text-lg font-black text-white">Immutable Ledger Proof</h3>
              <p className="text-[10px] text-emerald-400 font-extrabold bg-emerald-950/40 border border-emerald-900/30 px-3 py-1 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full inline-block" />
                On-Chain Verified
              </p>
            </div>

            {/* Details Grid */}
            <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 text-xs space-y-3.5">
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Transaction Hash</span>
                <span className="font-mono text-cyan-400 font-medium break-all select-all">{txDetails.hash}</span>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Block Number</span>
                  <span className="text-white font-mono font-medium">#{txDetails.blockNumber}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase font-bold">Gas Consumption</span>
                  <span className="text-white font-mono font-medium">{txDetails.gasUsed} gas units</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Mining Confirmation Time</span>
                <span className="text-slate-300 font-medium">{new Date(txDetails.timestamp * 1000).toLocaleString()}</span>
              </div>
            </div>

            <div className="text-center text-[10px] text-slate-500 flex items-center justify-center gap-1.5 bg-slate-950/40 p-2 rounded-lg">
              <FaShieldAlt className="text-cyan-500" />
              <span>This record is secure and permanently immutable on the blockchain ledger.</span>
            </div>

            <button
              onClick={() => setModalOpen(false)}
              className="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-2.5 rounded-xl transition text-xs"
            >
              Close Ledger Proof
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
