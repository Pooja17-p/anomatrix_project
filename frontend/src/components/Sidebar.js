import { Link, useLocation } from "react-router-dom";
import "./Sidebar.css";
import {
  FaHome,
  FaMousePointer,
  FaKeyboard,
  FaLaptop,
  FaHistory,
  FaChartBar,
  FaBell,
  FaCog,
  FaUser,
  FaLink,
  FaSignOutAlt,
} from "react-icons/fa";

function Sidebar() {
  const location = useLocation();

  const handleLogout = () => {
    // Clear authentication session flags
    localStorage.removeItem("token");
    localStorage.removeItem("userData");
    localStorage.removeItem("username");
    sessionStorage.clear();
  };

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: <FaHome /> },
    { path: "/mouse-dashboard", label: "Mouse Motion", icon: <FaMousePointer /> },
    { path: "/keystroke-dashboard", label: "Keystroke Auth", icon: <FaKeyboard /> },
    { path: "/analytics", label: "AI Behaviour", icon: <FaChartBar /> },
    { path: "/devices", label: "Devices", icon: <FaLaptop /> },
    { path: "/history", label: "History", icon: <FaHistory /> },
    { path: "/blockchain", label: "Blockchain Audit", icon: <FaLink /> },
    { path: "/alerts", label: "Alerts", icon: <FaBell /> },
    { path: "/settings", label: "Settings", icon: <FaCog /> },
    { path: "/profile", label: "Profile", icon: <FaUser /> },
  ];

  return (
    <aside className="sidebar-container">
      {/* Header Logo */}
      <div className="sidebar-header">
        <h2 className="logo">AnomatriX</h2>
        <span className="logo-badge">ZERO TRUST</span>
      </div>

      {/* Scrollable Navigation List */}
      <nav className="sidebar-nav">
        <ul>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`nav-link ${isActive ? "active" : ""}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Permanently Pinned Bottom Logout Footer */}
      <div className="sidebar-footer">
        <Link to="/" onClick={handleLogout} className="logout-button">
          <FaSignOutAlt className="logout-icon" />
          <span>Logout</span>
        </Link>
      </div>
    </aside>
  );
}

export default Sidebar;