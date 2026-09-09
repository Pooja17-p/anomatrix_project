import FingerprintJS from "@fingerprintjs/fingerprintjs";
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { toast } from "react-toastify";
import SecurityConditionsBanner from "../components/SecurityConditionsBanner";
import "./login.css";

function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      toast.error("Please enter both username and password.");
      return;
    }

    setLoading(true);

    try {
      // Generate Browser Fingerprint
      let visitorId = "fp_" + Math.random().toString(36).substring(2, 10);
      try {
        const fp = await FingerprintJS.load();
        const fingerprint = await fp.get();
        if (fingerprint && fingerprint.visitorId) {
          visitorId = fingerprint.visitorId;
        }
      } catch (fpErr) {
        console.warn("FingerprintJS load fallback:", fpErr);
      }

      // Login Request
      const response = await axios.post("http://127.0.0.1:5000/login", {
        username,
        password,
        device_id: visitorId,
      });

      // Clear any stale tokens
      localStorage.removeItem("token");
      sessionStorage.setItem("username", username);

      // Check if MFA is required
      if (response.data && response.data.mfa_required) {
        sessionStorage.setItem("otp_username", username);
        sessionStorage.setItem("face_enabled", response.data.face_enabled ? "true" : "false");
        toast.info("MFA Required. Redirecting to OTP Verification...");
        setTimeout(() => {
          navigate("/otp");
        }, 800);
        return;
      }


      // If MFA Disabled -> Direct Login
      if (response.data && response.data.access_token) {
        localStorage.setItem("token", response.data.access_token);
        localStorage.setItem("userData", JSON.stringify(response.data));
        localStorage.setItem("username", username);

        toast.success("Login Successful! Redirecting to Dashboard...");
        setTimeout(() => {
          navigate("/dashboard");
        }, 1000);
      } else {
        // Fallback for direct response
        localStorage.setItem("userData", JSON.stringify(response.data));
        localStorage.setItem("username", username);
        toast.success("Login Successful!");
        navigate("/dashboard");
      }
    } catch (error) {
      console.error(error);
      const msg = error.response?.data?.message || "Invalid Username or Password";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2 className="login-title">AnomatriX Login</h2>

      {/* Security Conditions Banner */}
      <SecurityConditionsBanner title="Zero-Trust Authentication Protocol" />

      <input
        className="input-field"
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />

      <input
        className="input-field"
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button
        className="login-button"
        onClick={handleLogin}
        disabled={loading}
      >
        {loading ? "Authenticating..." : "Login"}
      </button>

      <p style={{ marginTop: "20px", color: "white" }}>
        New User?
        <Link
          to="/register"
          style={{
            color: "#00d4ff",
            marginLeft: "8px",
          }}
        >
          Register Here
        </Link>
      </p>
    </div>
  );
}

export default Login;