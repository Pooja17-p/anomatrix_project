import { Link, useNavigate } from "react-router-dom";

function Navbar() {

  const navigate = useNavigate();

  return (
    <div className="navbar">

      <h2>AnomatriX</h2>

      <div>

        <button
          className="nav-btn"
          onClick={() => navigate(-1)}
        >
          ← Back
        </button>

        <Link to="/dashboard">Dashboard</Link>
        <Link to="/history">History</Link>
        <Link to="/analytics">Analytics</Link>

      </div>

    </div>
  );
}

export default Navbar;