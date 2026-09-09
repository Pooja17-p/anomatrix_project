import React from "react";

function StatCard({ title, value, status, description, color }) {
  const getGlowStyle = () => {
    switch (color) {
      case "cyan":
        return {
          boxShadow: "0 8px 32px 0 rgba(0, 212, 255, 0.15)",
          border: "1px solid rgba(0, 212, 255, 0.2)"
        };
      case "green":
        return {
          boxShadow: "0 8px 32px 0 rgba(0, 255, 136, 0.15)",
          border: "1px solid rgba(0, 255, 136, 0.2)"
        };
      case "red":
        return {
          boxShadow: "0 8px 32px 0 rgba(255, 77, 77, 0.15)",
          border: "1px solid rgba(255, 77, 77, 0.2)"
        };
      case "yellow":
        return {
          boxShadow: "0 8px 32px 0 rgba(250, 204, 21, 0.15)",
          border: "1px solid rgba(250, 204, 21, 0.2)"
        };
      default:
        return {
          boxShadow: "0 8px 32px 0 rgba(255, 255, 255, 0.05)",
          border: "1px solid rgba(255, 255, 255, 0.1)"
        };
    }
  };

  const getTitleColor = () => {
    switch (color) {
      case "cyan": return "#00d4ff";
      case "green": return "#00ff88";
      case "red": return "#ff4d4d";
      case "yellow": return "#facc15";
      default: return "#ffffff";
    }
  };

  return (
    <div 
      style={{
        background: "rgba(30, 41, 59, 0.7)",
        backdropFilter: "blur(12px)",
        borderRadius: "16px",
        padding: "24px",
        flex: "1",
        minWidth: "200px",
        margin: "12px",
        transition: "transform 0.3s ease, box-shadow 0.3s ease",
        cursor: "pointer",
        ...getGlowStyle()
      }}
      className="stat-card"
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-5px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <h3 style={{ margin: "0 0 12px 0", color: "#94a3b8", fontSize: "14px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "1px" }}>
        {title}
      </h3>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <h1 style={{ margin: "0", fontSize: "36px", fontWeight: "800", color: getTitleColor() }}>
          {value}
        </h1>
        {status && (
          <span style={{ 
            fontSize: "12px", 
            fontWeight: "bold", 
            padding: "4px 8px", 
            borderRadius: "12px", 
            background: "rgba(255,255,255,0.1)",
            color: getTitleColor()
          }}>
            {status}
          </span>
        )}
      </div>
      {description && (
        <p style={{ margin: "12px 0 0 0", color: "#cbd5e1", fontSize: "13px" }}>
          {description}
        </p>
      )}
    </div>
  );
}

export default StatCard;
