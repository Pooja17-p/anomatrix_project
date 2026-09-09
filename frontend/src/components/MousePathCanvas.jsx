import React, { useRef, useEffect, useState, useCallback } from "react";
import { FaPause, FaPlay, FaTrash, FaFire, FaExpand, FaCompass, FaCrosshairs } from "react-icons/fa";

export default function MousePathCanvas({
  pathPoints = [],
  clickMarkers = [],
  livePosition = { x: 0, y: 0 },
  currentSpeed = 0,
  onClear,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  const [isPaused, setIsPaused] = useState(false);
  const [heatmapMode, setHeatmapMode] = useState(false);
  const [trailLength, setTrailLength] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Resize canvas to match container width/height dynamically
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current && containerRef.current) {
        const canvas = canvasRef.current;
        const rect = containerRef.current.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Main Canvas Render Loop
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || isPaused) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    // Dark grid background
    ctx.fillStyle = "#020617"; // slate-950
    ctx.fillRect(0, 0, width, height);

    // Subtle grid lines
    ctx.strokeStyle = "rgba(30, 41, 59, 0.5)"; // slate-800
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const rect = canvas.getBoundingClientRect();
    const visiblePoints = pathPoints.slice(-trailLength);

    if (visiblePoints.length > 1) {
      // Draw Trajectory Segments with Speed-based Color Coding
      for (let i = 1; i < visiblePoints.length; i++) {
        const p1 = visiblePoints[i - 1];
        const p2 = visiblePoints[i];

        // Map viewport coords to local canvas coords
        const x1 = p1.x - rect.left;
        const y1 = p1.y - rect.top;
        const x2 = p2.x - rect.left;
        const y2 = p2.y - rect.top;

        // Skip if outside canvas container
        if (x1 < -100 || y1 < -100 || x2 > width + 100 || y2 > height + 100) continue;

        const progress = i / visiblePoints.length; // 0 to 1
        const alpha = Math.min(1, progress * 1.2);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);

        if (heatmapMode) {
          // Heatmap: Color based on velocity
          const spd = p2.speed || 0;
          if (spd > 3000) {
            ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`; // red
          } else if (spd > 1500) {
            ctx.strokeStyle = `rgba(245, 158, 11, ${alpha})`; // amber
          } else if (spd > 600) {
            ctx.strokeStyle = `rgba(16, 185, 129, ${alpha})`; // emerald
          } else {
            ctx.strokeStyle = `rgba(6, 182, 212, ${alpha})`; // cyan
          }
          ctx.lineWidth = Math.min(10, Math.max(2, spd / 400));
        } else {
          // Smooth Neon Cyan-Purple Trail
          const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
          gradient.addColorStop(0, `rgba(6, 182, 212, ${alpha * 0.4})`); // cyan
          gradient.addColorStop(1, `rgba(168, 85, 247, ${alpha})`); // purple
          ctx.strokeStyle = gradient;
          ctx.lineWidth = 3;
        }

        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.stroke();
      }
    }

    // Draw Click Ripples
    clickMarkers.slice(-10).forEach((click) => {
      const cx = click.x - rect.left;
      const cy = click.y - rect.top;
      const ageMs = Date.now() - click.timestamp;

      if (ageMs < 1200 && cx >= 0 && cx <= width && cy >= 0 && cy <= height) {
        const radius = (ageMs / 1200) * 35;
        const opacity = 1 - ageMs / 1200;

        ctx.beginPath();
        ctx.arc(cx, cy, Math.max(4, radius), 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(244, 63, 94, ${opacity})`; // rose red
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(244, 63, 94, ${opacity})`;
        ctx.fill();
      }
    });

    // Draw Active Live Cursor Crosshair & Halo
    const curX = livePosition.x - rect.left;
    const curY = livePosition.y - rect.top;

    if (curX >= 0 && curX <= width && curY >= 0 && curY <= height) {
      // Glow halo ring around cursor
      ctx.beginPath();
      ctx.arc(curX, curY, 14, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(6, 182, 212, 0.15)";
      ctx.fill();
      ctx.strokeStyle = "rgba(6, 182, 212, 0.6)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Center glowing point
      ctx.beginPath();
      ctx.arc(curX, curY, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#06b6d4";
      ctx.shadowColor = "#06b6d4";
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0; // Reset shadow
    }
  }, [pathPoints, clickMarkers, livePosition, isPaused, heatmapMode, trailLength]);

  useEffect(() => {
    let animId;
    const loop = () => {
      renderCanvas();
      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [renderCanvas]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl transition-all duration-300 ${
        isFullscreen ? "fixed inset-4 z-50 h-[92vh]" : "h-80 md:h-[400px]"
      }`}
    >
      {/* Top Overlay Badge & Header */}
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-3 bg-slate-900/80 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-700/60 text-xs text-slate-200 shadow-lg">
        <FaCompass className="text-cyan-400 animate-spin text-sm" style={{ animationDuration: "6s" }} />
        <span className="font-semibold tracking-wide">Live Path Visualization</span>
        <span className="text-[10px] bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded-full border border-cyan-500/30">
          {pathPoints.length} Points Tracked
        </span>
      </div>

      {/* Live Position Pointer Badge */}
      <div className="absolute top-4 right-4 z-10 flex items-center space-x-2 bg-slate-900/80 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-indigo-500/30 text-xs text-indigo-300 font-mono shadow-lg">
        <FaCrosshairs className="text-indigo-400 text-xs" />
        <span>X: {livePosition.x}</span>
        <span className="text-slate-600">|</span>
        <span>Y: {livePosition.y}</span>
      </div>

      {/* HTML5 Canvas Element */}
      <canvas ref={canvasRef} className="w-full h-full cursor-crosshair block" />

      {/* Bottom Floating Canvas Controls */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center space-x-2 bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-2xl border border-slate-700/60 shadow-2xl text-xs text-slate-300">
        <button
          onClick={() => setIsPaused(!isPaused)}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border font-medium transition ${
            isPaused
              ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
              : "bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-600"
          }`}
          title="Pause or Resume path rendering"
        >
          {isPaused ? <FaPlay className="text-xs" /> : <FaPause className="text-xs" />}
          <span>{isPaused ? "Resume" : "Pause"}</span>
        </button>

        <button
          onClick={() => setHeatmapMode(!heatmapMode)}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border font-medium transition ${
            heatmapMode
              ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
              : "bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-600"
          }`}
          title="Toggle Speed Heatmap mode"
        >
          <FaFire className={heatmapMode ? "text-rose-400" : "text-slate-400"} />
          <span>Heatmap</span>
        </button>

        <div className="h-4 w-px bg-slate-700 mx-1" />

        <div className="flex items-center space-x-1 text-[11px] text-slate-400">
          <span>Trail:</span>
          <select
            value={trailLength}
            onChange={(e) => setTrailLength(Number(e.target.value))}
            className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-1.5 py-1 focus:outline-none"
          >
            <option value={50}>Short (50)</option>
            <option value={100}>Medium (100)</option>
            <option value={200}>Long (200)</option>
          </select>
        </div>

        <div className="h-4 w-px bg-slate-700 mx-1" />

        <button
          onClick={onClear}
          className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition font-medium"
          title="Clear canvas path"
        >
          <FaTrash className="text-xs" />
          <span>Clear</span>
        </button>

        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition ml-1"
          title="Toggle Fullscreen Canvas"
        >
          <FaExpand className="text-xs" />
        </button>
      </div>
    </div>
  );
}
