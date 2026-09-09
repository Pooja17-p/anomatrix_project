import React from "react";
import Sidebar from "../components/Sidebar";
import BehaviorDashboard from "../components/BehaviorDashboard";
import "./analytics.css";

function Analytics() {
  return (
    <div className="analytics-page flex bg-slate-950 min-h-screen text-slate-100 font-sans">
      <Sidebar />
      <div className="analytics-content flex-1 pl-[260px] p-6 overflow-y-auto min-h-screen">
        <BehaviorDashboard />
      </div>
    </div>
  );
}

export default Analytics;