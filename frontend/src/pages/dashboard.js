import { useNavigate } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import StatCard from "../components/StatCard";
import FingerprintJS from "@fingerprintjs/fingerprintjs";
import axios from "axios";
import "./dashboard.css";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";

import { Line, Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function Dashboard() {

  const navigate = useNavigate();

  const [currentUser, setCurrentUser] = useState(JSON.parse(localStorage.getItem("userData")));
  const user = currentUser;
  const username = localStorage.getItem("username");

  const [history, setHistory] = useState([]);
  const [deviceId, setDeviceId] = useState("");

  useEffect(() => {

    if (!currentUser) {
      navigate("/");
    }

  }, [currentUser, navigate]);

  // Fingerprint calculation
  useEffect(() => {
    const initFingerprint = async () => {
      try {
        const fp = await FingerprintJS.load();
        const result = await fp.get();
        setDeviceId(result.visitorId);
      } catch (err) {
        console.error("Fingerprint error:", err);
      }
    };
    initFingerprint();
  }, []);

  const verifySession = useCallback(async () => {
    if (!currentUser || !deviceId) return;
    try {
      const mockIp = localStorage.getItem("mockIp") || "";
      const response = await axios.post(
        "http://127.0.0.1:5000/verify-session",
        {
          device_id: deviceId,
          mock_ip: mockIp
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`
          }
        }
      );

      const { trust_score, anomaly_score, risk_level } = response.data;
      
      // Update state and localStorage
      const updatedUser = {
        ...currentUser,
        trust_score,
        anomaly_score,
        risk_level
      };
      
      localStorage.setItem("userData", JSON.stringify(updatedUser));
      setCurrentUser(updatedUser);
      
    } catch (err) {
      console.error("Continuous auth verification failed:", err);
      const msg = err.response?.data?.message || "Continuous Zero-Trust validation failed.";
      alert(`🚨 Zero-Trust Alert: ${msg}`);
      localStorage.clear();
      navigate("/");
    }
  }, [currentUser, deviceId, navigate]);

  // Perform continuous authentication check every 15 seconds
  useEffect(() => {
    if (!deviceId || !currentUser) return;
    
    verifySession(); // Immediate initial check
    const interval = setInterval(verifySession, 15000);
    return () => clearInterval(interval);
  }, [deviceId, verifySession]);

  const fetchHistory = useCallback(async () => {

    try {

      const response = await axios.get(
        `http://127.0.0.1:5000/login-history/${username}`
      );

      setHistory(response.data.history);

    } catch (err) {

      console.log(err);

    }

  }, [username]);

  useEffect(() => {

    fetchHistory();

  }, [fetchHistory]);

  if (!currentUser) return null;


  const trusted = history.filter(
    item =>
      !((item.device_id || "").includes("unknown") ||
        (item.device_id || "").includes("hacker"))
  ).length;

  const suspicious = history.length - trusted;

  const trustData = {
    labels: ["Current Session"],
    datasets: [
      {
        label: "Trust Score",
        data: [user.trust_score],
        borderColor: "#00d4ff",
        backgroundColor: "#00d4ff",
        tension: 0.4
      }
    ]
  };

  const loginData = {
    labels: ["Trusted", "Suspicious"],
    datasets: [
      {
        label: "Logins",
        data: [trusted, suspicious],
        backgroundColor: [
          "#00ff88",
          "#ff4d4d"
        ]
      }
    ]
  };

  return (

    <div className="dashboard-page">

      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", marginLeft: "250px" }}>

        <Topbar />

        <div style={{ padding: "35px" }}>

          <h1 style={{ marginTop: "0" }}>
            Welcome, {username}
          </h1>

          <div className="cards" style={{ display: "flex", flexWrap: "wrap", margin: "10px -12px" }}>

            <StatCard 
              title="Trust Score" 
              value={user.trust_score} 
              status={`${user.trust_score}%`} 
              description="Continuous trust evaluation index." 
              color="cyan" 
            />

            <StatCard 
              title="Risk Level" 
              value={user.risk_level} 
              description="Overall threat risk classification." 
              color={user.risk_level === "High" ? "red" : user.risk_level === "Medium" ? "yellow" : "green"} 
            />

            <StatCard 
              title="Anomaly Score" 
              value={user.anomaly_score} 
              description="Behavioral analysis deviation metric." 
              color={user.anomaly_score >= 50 ? "red" : user.anomaly_score >= 20 ? "yellow" : "cyan"} 
            />

            <StatCard 
              title="Device Status" 
              value={user.known_device ? "Trusted" : "New Device"} 
              status={user.known_device ? "Authorized" : "Flagged"} 
              description="Hardware fingerprint check result." 
              color={user.known_device ? "green" : "red"} 
            />

          </div>

          <div className="charts">

            <div className="chart-card">
              <h3>Trust Score</h3>
              <Line data={trustData} />
            </div>

            <div className="chart-card">
              <h3>Login Distribution</h3>
              <Bar data={loginData} />
            </div>

            <div className="chart-card">
              <h3>Security Status</h3>

              <Doughnut
                data={{
                  labels: ["Trust", "Remaining"],
                  datasets: [
                    {
                      data: [
                        user.trust_score,
                        100 - user.trust_score
                      ],
                      backgroundColor: [
                        "#00d4ff",
                        "#1f2937"
                      ]
                    }
                  ]
                }}
              />

            </div>

          </div>

          <div className="recent-logins">

            <h2>Recent Login History</h2>

            <table>

              <thead>

                <tr>

                  <th>Device</th>

                  <th>Timestamp</th>

                </tr>

              </thead>

              <tbody>

                {

                  history
                    .slice()
                    .reverse()
                    .slice(0, 5)
                    .map((item, index) => (

                      <tr key={index}>

                        <td>

                          {item.device_id
                            ? item.device_id.substring(0, 18) + "..."
                            : "Unknown"}

                        </td>

                        <td>{item.timestamp}</td>

                      </tr>

                    ))

                }

              </tbody>

            </table>

          </div>

          <div className="ai-box">

            <h2>AI Recommendation</h2>

            <p>

              {

                user.risk_level === "Low"

                  ? "✅ User behaviour appears normal. No additional action required."

                  : user.risk_level === "Medium"

                  ? "⚠ Moderate risk detected. Continue monitoring user activity."

                  : "🚨 High risk detected. Trigger MFA and notify the administrator immediately."

              }

            </p>

          </div>

        </div>

      </div>

    </div>

  );

}

export default Dashboard;