import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";
import { FaChartArea, FaShieldAlt } from "react-icons/fa";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function TelemetryCharts({ history = [] }) {
  // Format chart labels and dataset values from telemetry history
  const reversedHistory = [...history].reverse();

  const labels =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.timestamp || "0s")
      : ["t-20s", "t-15s", "t-10s", "t-5s", "Live"];

  const speedData =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.avgSpeed || 0)
      : [420, 680, 510, 920, 340];

  const peakSpeedData =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.peakSpeed || 0)
      : [1200, 1500, 1100, 2100, 890];

  const trustScores =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.trustScore || 95)
      : [98, 96, 99, 94, 98];

  // Kinematic Velocity Line Chart
  const lineChartData = {
    labels,
    datasets: [
      {
        label: "Avg Speed (px/s)",
        data: speedData,
        borderColor: "#06b6d4", // cyan-500
        backgroundColor: "rgba(6, 182, 212, 0.12)",
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
      },
      {
        label: "Peak Velocity (px/s)",
        data: peakSpeedData,
        borderColor: "#a855f7", // purple-500
        backgroundColor: "rgba(168, 85, 247, 0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
      },
    ],
  };

  // Trust Score Distribution Bar Chart
  const barChartData = {
    labels,
    datasets: [
      {
        label: "Trust Score (%)",
        data: trustScores,
        backgroundColor: trustScores.map((score) =>
          score < 50 ? "rgba(239, 68, 68, 0.85)" : score < 75 ? "rgba(245, 158, 11, 0.85)" : "rgba(16, 185, 129, 0.85)"
        ),
        borderRadius: 6,
      },
    ],
  };

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#94a3b8", // slate-400
          font: { family: "Inter", size: 11 },
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: "#0f172a",
        borderColor: "#334155",
        borderWidth: 1,
        titleColor: "#f8fafc",
        bodyColor: "#cbd5e1",
        padding: 10,
      },
    },
    scales: {
      x: {
        ticks: { color: "#64748b", font: { size: 10 } },
        grid: { color: "rgba(255, 255, 255, 0.04)" },
      },
      y: {
        ticks: { color: "#64748b", font: { size: 10 } },
        grid: { color: "rgba(255, 255, 255, 0.04)" },
      },
    },
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Kinematic Speed Line Chart */}
      <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FaChartArea className="text-cyan-400" />
            <span>Mouse Velocity Kinematics Trend</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">Real-time Windows</span>
        </div>
        <div className="h-64">
          <Line data={lineChartData} options={commonOptions} />
        </div>
      </div>

      {/* Trust Score Bar Chart */}
      <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FaShieldAlt className="text-emerald-400" />
            <span>Trust Score & Anomaly Score Distribution</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">0-100 Rating</span>
        </div>
        <div className="h-64">
          <Bar
            data={barChartData}
            options={{
              ...commonOptions,
              scales: {
                ...commonOptions.scales,
                y: { ...commonOptions.scales.y, min: 0, max: 100 },
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
