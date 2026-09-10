import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import API_BASE_URL from "../config/api";
import Sidebar from "../components/Sidebar";
import "./history.css";

function History() {

  const username = localStorage.getItem("username");

  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState("");

  const fetchHistory = useCallback(async () => {

    try {

      const response = await axios.get(
        `${API_BASE_URL}/login-history/${username}`
      );

      setHistory(response.data.history);

    } catch (err) {

      console.log(err);

    }

  }, [username]);

  useEffect(() => {

    fetchHistory();

  }, [fetchHistory]);

  const filteredHistory = history.filter(item =>
    (item.device_id || "")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const exportCSV = () => {

    let csv = "Device ID,Timestamp,Status\n";

    filteredHistory.forEach(item => {

      const status =
        (item.device_id || "").includes("unknown") ||
        (item.device_id || "").includes("hacker")
          ? "Suspicious"
          : "Trusted";

      csv += `${item.device_id || "Unknown"},${item.timestamp},${status}\n`;

    });

    const blob = new Blob([csv], {
      type: "text/csv"
    });

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;
    a.download = "login_history.csv";
    a.click();

    window.URL.revokeObjectURL(url);

  };

  return (

    <div className="history-page">

      <Sidebar />

      <div className="history-content">

        <h1>Login History</h1>

        <div className="history-top">

          <div className="history-card">

            <h3>Total Logins</h3>

            <h1>{history.length}</h1>

          </div>

          <input
            className="search-box"
            placeholder="Search Device ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <button
            className="export-btn"
            onClick={exportCSV}
          >
            Export CSV
          </button>

        </div>

        <table className="history-table">

          <thead>

            <tr>

              <th>Device ID</th>

              <th>Timestamp</th>

              <th>Status</th>

            </tr>

          </thead>

          <tbody>

            {

              filteredHistory
                .slice()
                .reverse()
                .map((item, index) => {

                  const suspicious =
                    (item.device_id || "").includes("unknown") ||
                    (item.device_id || "").includes("hacker");

                  return (

                    <tr
                      key={index}
                      className={
                        suspicious
                          ? "danger-row"
                          : ""
                      }
                    >

                      <td>

                        {
                          item.device_id
                            ? item.device_id.substring(0, 18) + "..."
                            : "Unknown Device"
                        }

                      </td>

                      <td>

                        {item.timestamp}

                      </td>

                      <td>

                        {
                          suspicious
                            ? "⚠ Suspicious"
                            : "✅ Trusted"
                        }

                      </td>

                    </tr>

                  );

                })

            }

          </tbody>

        </table>

      </div>

    </div>

  );

}

export default History;