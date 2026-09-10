import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";
import { toast } from "react-toastify";
import API_BASE_URL from "../config/api";
import { FaCheckCircle, FaExclamationTriangle, FaCamera, FaLock, FaShieldAlt, FaTimes } from "react-icons/fa";
import "./settings.css";

function Settings() {
  const navigate = useNavigate();

  const [mfa, setMfa] = useState(false);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [trustDevices, setTrustDevices] = useState(false);
  const [autoLogout, setAutoLogout] = useState(true);

  // Face Security State
  const [faceEnabled, setFaceEnabled] = useState(false);
  const [faceRegistered, setFaceRegistered] = useState(false);
  const [loadingFaceStatus, setLoadingFaceStatus] = useState(true);

  // Re-auth Modal State
  const [showReauthModal, setShowReauthModal] = useState(false);
  const [reauthPassword, setReauthPassword] = useState("");
  const [reauthLoading, setReauthLoading] = useState(false);

  const username = localStorage.getItem("username");
  const token = localStorage.getItem("token");

  useEffect(() => {
    const savedMfa = localStorage.getItem("mfa");
    const savedAlerts = localStorage.getItem("emailAlerts");
    const savedDark = localStorage.getItem("darkMode");
    const savedTrust = localStorage.getItem("trustDevices");

    if (savedMfa !== null) setMfa(JSON.parse(savedMfa));
    if (savedAlerts !== null) setEmailAlerts(JSON.parse(savedAlerts));
    if (savedDark !== null) setDarkMode(JSON.parse(savedDark));
    if (savedTrust !== null) setTrustDevices(JSON.parse(savedTrust));

    if (username) {
      checkFaceRegistrationStatus();
    }
  }, []);

  const checkFaceRegistrationStatus = async () => {
    setLoadingFaceStatus(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/face/status/${encodeURIComponent(username)}`);
      if (res.data) {
        setFaceRegistered(Boolean(res.data.registered || res.data.face_registered));
        setFaceEnabled(Boolean(res.data.face_enabled));
      }
    } catch (err) {
      console.error("Error fetching face registration status:", err);
      setFaceRegistered(false);
      setFaceEnabled(false);
    } finally {
      setLoadingFaceStatus(false);
    }
  };

  const handleStartReauthentication = () => {
    setReauthPassword("");
    setShowReauthModal(true);
  };

  const handleReauthenticateSubmit = async (e) => {
    e.preventDefault();
    if (!reauthPassword) {
      toast.error("Please enter your current password.");
      return;
    }

    setReauthLoading(true);
    try {
      const res = await axios.post(
        `${API_BASE_URL}/api/auth/reauthenticate`,
        { password: reauthPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (res.data && res.data.success && res.data.reauth_token) {
        sessionStorage.setItem("biometric_reauth_token", res.data.reauth_token);
        toast.success("Security Re-authentication Successful! Redirecting to Face Registration...");
        setShowReauthModal(false);
        setTimeout(() => {
          navigate("/face-auth?flow=settings_register");
        }, 800);
      } else {
        toast.error(res.data.message || "Re-authentication failed.");
      }
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.message || "Invalid password. Security re-authentication required.";
      toast.error(msg);
    } finally {
      setReauthLoading(false);
    }
  };

  const handleDisableFace = async () => {
    if (!window.confirm("Are you sure you want to disable Face Recognition Authentication?")) {
      return;
    }
    try {
      const res = await axios.post(
        `${API_BASE_URL}/api/face/disable`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.data && res.data.success) {
        toast.success("Face Recognition Disabled Successfully.");
        setFaceEnabled(false);
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to disable face authentication.");
    }
  };

  const saveSettings = async () => {
    try {
      await axios.post(`${API_BASE_URL}/update-settings`, {
        username,
        mfa_enabled: mfa,
        trust_devices: trustDevices,
        email_alerts: emailAlerts,
        dark_mode: darkMode,
        auto_logout: autoLogout,
      });

      localStorage.setItem("mfa", JSON.stringify(mfa));
      localStorage.setItem("emailAlerts", JSON.stringify(emailAlerts));
      localStorage.setItem("darkMode", JSON.stringify(darkMode));
      localStorage.setItem("trustDevices", JSON.stringify(trustDevices));
      localStorage.setItem("autoLogout", JSON.stringify(autoLogout));

      const userData = JSON.parse(localStorage.getItem("userData")) || {};
      userData.mfa_enabled = mfa;
      userData.trust_devices = trustDevices;
      userData.email_alerts = emailAlerts;
      userData.dark_mode = darkMode;
      userData.auto_logout = autoLogout;
      localStorage.setItem("userData", JSON.stringify(userData));

      toast.success("Security Settings Saved Successfully!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to save settings on backend.");
    }
  };

  return (
    <div className="settings-page">
      <Sidebar />

      <div className="settings-content">
        <h1>Security Settings</h1>

        <div className="settings-card">

          {/* Biometric Face Recognition Status Section */}
          <div className="p-5 rounded-2xl border mb-6 bg-slate-900 border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <FaLock className="text-indigo-400" /> Face Recognition Authentication
              </h3>
              <div>
                {loadingFaceStatus ? (
                  <span className="text-xs text-slate-400">Checking status...</span>
                ) : faceEnabled ? (
                  <span className="px-3 py-1 text-xs rounded-full font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                    <FaCheckCircle /> Status: Enabled
                  </span>
                ) : (
                  <span className="px-3 py-1 text-xs rounded-full font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                    Status: Disabled
                  </span>
                )}
              </div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Face authentication provides an additional identity verification layer during multi-factor login.
            </p>

            {loadingFaceStatus ? (
              <p className="text-xs text-slate-400">Loading biometric configuration...</p>
            ) : faceEnabled ? (
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={handleStartReauthentication}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
                >
                  <FaCamera /> Re-register Face
                </button>
                <button
                  onClick={handleDisableFace}
                  className="px-4 py-2 bg-rose-950/60 hover:bg-rose-900/70 border border-rose-500/40 text-rose-300 font-bold text-xs rounded-xl transition"
                >
                  Disable Face Recognition
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
                <span className="text-xs text-slate-300">
                  Enable Face Recognition to require biometric verification during login.
                </span>
                <button
                  onClick={handleStartReauthentication}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5 shrink-0 ml-3"
                >
                  <FaShieldAlt /> Enable Face Recognition
                </button>
              </div>
            )}
          </div>

          <div className="setting-row">
            <span>🔐 Enable Multi-Factor Authentication</span>
            <input
              type="checkbox"
              checked={mfa}
              onChange={() => setMfa(!mfa)}
            />
          </div>

          <div className="setting-row">
            <span>📧 Email Login Alerts</span>
            <input
              type="checkbox"
              checked={emailAlerts}
              onChange={() => setEmailAlerts(!emailAlerts)}
            />
          </div>

          <div className="setting-row">
            <span>💻 Trust New Devices Automatically</span>
            <input
              type="checkbox"
              checked={trustDevices}
              onChange={() => setTrustDevices(!trustDevices)}
            />
          </div>

          <div className="setting-row">
            <span>🌙 Dark Mode</span>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
            />
          </div>

          <div className="setting-row">
            <span>⏱ Auto Logout (15 Minutes)</span>
            <input
              type="checkbox"
              checked={autoLogout}
              onChange={() => setAutoLogout(!autoLogout)}
            />
          </div>

          <hr />

          <div className="security-info">
            <h3>Current Security Level</h3>
            <h2 className="secure">🟢 HIGH</h2>
            <p>
              Your Zero Trust configuration follows enterprise security recommendations.
            </p>
          </div>

          <button className="save-btn" onClick={saveSettings}>
            Save Changes
          </button>
        </div>
      </div>

      {/* Security Re-Authentication Modal */}
      {showReauthModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 max-w-md w-full shadow-2xl space-y-5 text-slate-100 relative">
            <button
              onClick={() => setShowReauthModal(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white text-lg"
            >
              <FaTimes />
            </button>

            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl">
                <FaLock className="text-xl" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">Security Re-Authentication</h3>
                <p className="text-xs text-slate-400">Confirm password to modify biometric settings</p>
              </div>
            </div>

            <form onSubmit={handleReauthenticateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">
                  Enter Password for <strong>{username}</strong>:
                </label>
                <input
                  type="password"
                  value={reauthPassword}
                  onChange={(e) => setReauthPassword(e.target.value)}
                  placeholder="Current Password"
                  required
                  autoFocus
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReauthModal(false)}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition border border-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reauthLoading}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg transition flex items-center gap-2"
                >
                  {reauthLoading ? "Authenticating..." : "Authorize Registration"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Settings;