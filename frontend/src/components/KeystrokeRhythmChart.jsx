import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { FaChartLine } from "react-icons/fa";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function KeystrokeRhythmChart({ history = [] }) {
  const reversedHistory = [...history].reverse();

  const labels =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.timestamp || "0s")
      : ["t-20s", "t-15s", "t-10s", "t-5s", "Live"];

  const holdTimes =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.holdTime || 90)
      : [88, 92, 85, 96, 90];

  const flightTimes =
    reversedHistory.length > 0
      ? reversedHistory.map((item) => item.flightTime || 140)
      : [135, 142, 130, 150, 138];

  const chartData = {
    labels,
    datasets: [
      {
        label: "Avg Key Hold Time (ms)",
        data: holdTimes,
        borderColor: "#6366f1", // indigo-500
        backgroundColor: "rgba(99, 102, 241, 0.12)",
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
      },
      {
        label: "Avg Key Flight Time (ms)",
        data: flightTimes,
        borderColor: "#a855f7", // purple-500
        backgroundColor: "rgba(168, 85, 247, 0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#94a3b8",
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
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <FaChartLine className="text-indigo-400" />
          <span>Keystroke Kinematics & Rhythm Trend</span>
        </h3>
        <span className="text-xs text-slate-400 font-mono">Hold vs Flight Latency (ms)</span>
      </div>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
