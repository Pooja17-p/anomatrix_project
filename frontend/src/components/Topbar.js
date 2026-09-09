import React from "react";
import { FaBell, FaShieldAlt, FaUser } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

function Topbar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("userData"));
  const username = localStorage.getItem("username") || "User";

  const alertsCount = user?.alerts?.length || 0;
  const riskLevel = user?.risk_level || "Low";

  const getRiskColor = () => {
    switch (riskLevel) {
      case "High": return "#ff4d4d";
      case "Medium": return "#facc15";
      default: return "#00ff88";
    }
  };

  return (
    <div style={{
      height: "70px",
      background: "rgba(15, 23, 42, 0.8)",
      backdropFilter: "blur(12px)",
      borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 40px",
      position: "sticky",
      top: "0",
      zIndex: "100",
      color: "white"
    }}>
      <div style={{ display: "flex", alignItems: "center" }}>
        <FaShieldAlt style={{ color: "#00d4ff", marginRight: "12px", fontSize: "24px" }} />
        <span style={{ fontSize: "18px", fontWeight: "700", letterSpacing: "0.5px" }}>
          Zero Trust Security Engine
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "25px" }}>
        {/* Risk Status Indicator */}
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          background: "rgba(255,255,255,0.05)", 
          padding: "6px 14px", 
          borderRadius: "20px",
          border: `1px solid ${getRiskColor()}33`
        }}>
          <span style={{ fontSize: "13px", color: "#cbd5e1", marginRight: "8px" }}>Risk Status:</span>
          <span style={{ fontSize: "13px", fontWeight: "bold", color: getRiskColor() }}>
            ● {riskLevel.toUpperCase()}
          </span>
        </div>

        {/* Alerts Notification Button */}
        <div 
          onClick={() => navigate("/alerts")}
          style={{ position: "relative", cursor: "pointer" }}
        >
          <FaBell style={{ fontSize: "20px", color: "#cbd5e1", transition: "color 0.2s" }} />
          {alertsCount > 0 && (
            <span style={{
              position: "absolute",
              top: "-5px",
              right: "-5px",
              background: "#ff4d4d",
              color: "white",
              fontSize: "10px",
              fontWeight: "bold",
              borderRadius: "50%",
              width: "16px",
              height: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 5px #ff4d4d"
            }}>
              {alertsCount}
            </span>
          )}
        </div>

        {/* User Profile Info */}
        <div 
          onClick={() => navigate("/profile")}
          style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }}
        >
          <div style={{
            width: "36px",
            height: "36px",
            borderRadius: "50%",
            background: "linear-gradient(135deg, #00d4ff, #00ff88)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 10px rgba(0, 212, 255, 0.3)"
          }}>
            <FaUser style={{ color: "#0f172a", fontSize: "16px" }} />
          </div>
          <span style={{ fontSize: "14px", fontWeight: "500", color: "#e2e8f0" }}>
            {username}
          </span>
        </div>
      </div>
    </div>
  );
}

export default Topbar;
