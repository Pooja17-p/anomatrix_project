import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import FingerprintJS from "@fingerprintjs/fingerprintjs";
import { toast } from "react-toastify";
import API_BASE_URL from "../config/api";
import "./login.css";

function OtpVerification() {
  const navigate = useNavigate();
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(300);

  const inputRefs = [
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null)
  ];

  const initialUsername = useRef(sessionStorage.getItem("otp_username"));
  const username = initialUsername.current;

  const [faceAuthenticationEnabled, setFaceAuthenticationEnabled] = useState(
    sessionStorage.getItem("face_enabled") === "true"
  );

  useEffect(() => {
    if (!initialUsername.current) {
      navigate("/");
      return;
    }

    axios
      .get(`${API_BASE_URL}/api/face/status/${encodeURIComponent(initialUsername.current)}`)
      .then((res) => {
        if (res.data) {
          const isEnabled = Boolean(res.data.face_enabled && (res.data.registered || res.data.face_registered));
          setFaceAuthenticationEnabled(isEnabled);
          sessionStorage.setItem("face_enabled", isEnabled ? "true" : "false");
        }
      })
      .catch((err) => {
        console.warn("Could not fetch face status:", err);
      });
  }, [navigate]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);


  const handleChange = (index, value) => {
    if (isNaN(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.substring(value.length - 1);
    setOtp(newOtp);

    if (value && index < 5) {
      inputRefs[index + 1].current.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs[index - 1].current.focus();
    }
  };

  const handleVerify = async () => {
    const otpCode = otp.join("");
    if (otpCode.length < 6) {
      setError("Please enter the full 6-digit verification code.");
      toast.error("Please enter the full 6-digit verification code.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      let visitorId = "fp_" + Math.random().toString(36).substring(2, 10);
      try {
        const fp = await FingerprintJS.load();
        const fingerprint = await fp.get();
        if (fingerprint && fingerprint.visitorId) {
          visitorId = fingerprint.visitorId;
        }
      } catch (fpErr) {
        console.warn("FingerprintJS load error:", fpErr);
      }

      const response = await axios.post(`${API_BASE_URL}/verify-otp`, {
        username,
        otp: otpCode,
        device_id: visitorId
      });

      toast.success("OTP Verified Successfully!");
      sessionStorage.setItem("otp_verified", "true");
      sessionStorage.setItem("pending_user", username);
      localStorage.setItem("username", username);

      if (response.data && response.data.face_required) {
        if (response.data.pre_auth_token) {
          localStorage.setItem("pre_token", response.data.pre_auth_token);
        }
        setTimeout(() => {
          navigate("/face-auth?flow=mfa_verify", { replace: true });
        }, 800);
      } else {
        if (response.data && response.data.access_token) {
          localStorage.setItem("token", response.data.access_token);
        }
        localStorage.setItem("userData", JSON.stringify(response.data));
        sessionStorage.setItem("authenticated", "true");
        localStorage.setItem("authenticated", "true");
        
        toast.info("Authentication Complete! Redirecting to Dashboard...");
        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 800);
      }


    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.message || "Invalid or expired OTP code.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE_URL}/resend-otp`, {
        username
      });
      const msg = res.data?.message || "A new verification code has been sent to your email!";
      toast.info(msg);
      setCountdown(300);
      setOtp(["", "", "", "", "", ""]);
      if (inputRefs[0] && inputRefs[0].current) {
        inputRefs[0].current.focus();
      }
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.message || "Failed to resend OTP code.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="login-container" style={{ textAlign: "center", maxWidth: "450px" }}>
      <h2 className="login-title" style={{ fontSize: "28px" }}>Zero Trust Verification</h2>

      <p style={{ color: "#cbd5e1", marginBottom: "10px", fontSize: "15px" }}>
        Enter the 6-digit security code sent to the registered email for <strong>{username}</strong>.
      </p>

      <div style={{ display: "flex", justifyContent: "space-between", margin: "30px 0" }}>
        {otp.map((digit, index) => (
          <input
            key={index}
            ref={inputRefs[index]}
            type="text"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            style={{
              width: "50px",
              height: "55px",
              fontSize: "24px",
              textAlign: "center",
              background: "#334155",
              border: "2px solid #475569",
              borderRadius: "10px",
              color: "white",
              fontWeight: "bold",
              outline: "none",
              boxShadow: digit ? "0 0 10px cyan" : "none",
              borderColor: digit ? "cyan" : "#475569",
              transition: "all 0.2s ease"
            }}
          />
        ))}
      </div>

      {error && (
        <p style={{ color: "#ff4d4d", fontSize: "14px", margin: "10px 0", fontWeight: "500" }}>
          🚨 {error}
        </p>
      )}

      <p style={{ color: "#94a3b8", fontSize: "14px", margin: "15px 0" }}>
        Code expires in: <span style={{ color: "cyan", fontWeight: "bold" }}>{formatTime(countdown)}</span>
      </p>

      <button
        className="login-button"
        onClick={handleVerify}
        disabled={loading || countdown === 0}
        style={{
          opacity: (loading || countdown === 0) ? 0.6 : 1,
          cursor: (loading || countdown === 0) ? "not-allowed" : "pointer"
        }}
      >
        {loading
          ? "Verifying OTP..."
          : faceAuthenticationEnabled
          ? "Verify OTP & Proceed to Face Auth"
          : "Verify OTP & Login"}
      </button>


      <div style={{ marginTop: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button
          onClick={handleResend}
          disabled={loading}
          style={{
            background: "none",
            border: "none",
            color: "cyan",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "14px",
            textDecoration: "underline"
          }}
        >
          Resend Security Code
        </button>

        <button
          onClick={() => {
            sessionStorage.removeItem("otp_username");
            navigate("/");
          }}
          style={{
            background: "none",
            border: "none",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: "14px",
            textDecoration: "underline"
          }}
        >
          Cancel & Return to Login
        </button>
      </div>
    </div>
  );
}

export default OtpVerification;
