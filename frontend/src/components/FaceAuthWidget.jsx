import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "react-toastify";
import {
  FaUserCheck,
  FaCamera,
  FaShieldAlt,
  FaCheckCircle,
  FaExclamationTriangle,
  FaTimesCircle,
  FaSync,
  FaUserPlus,
  FaLock,
  FaLightbulb,
  FaExpandArrowsAlt
} from "react-icons/fa";

const API_BASE = "http://localhost:5000/api/face";

export default function FaceAuthWidget({ username: propUsername }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const flow = searchParams.get("flow");
  const isRegisterMode = flow === "settings_register";

  const username = propUsername || sessionStorage.getItem("pending_user") || localStorage.getItem("username") || "admin";

  const videoRef = useRef(null);
  const hiddenCanvasRef = useRef(null);

  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [isRegistered, setIsRegistered] = useState(false);
  const [loading, setLoading] = useState(false);
  const [captureProgress, setCaptureProgress] = useState(0);

  // Live status & user guidance state
  const [guidanceText, setGuidanceText] = useState("Looking for face...");
  const [cameraStatus, setCameraStatus] = useState("Offline");
  const [detectionStatus, setDetectionStatus] = useState("Scanning...");
  const [faceQualityScore, setFaceQualityScore] = useState("Checking...");
  const [confidenceScore, setConfidenceScore] = useState(null);
  const [faceDistance, setFaceDistance] = useState(null);
  const [validFacesDetected, setValidFacesDetected] = useState(0);
  const [framesAnalyzed, setFramesAnalyzed] = useState(0);
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [errorCode, setErrorCode] = useState(null);

  const [steps, setSteps] = useState([
    { id: "otp", label: "OTP Verified", status: "done" },
    { id: "camera", label: "Camera Started", status: "idle" },
    { id: "face", label: "Face Detected", status: "idle" },
    { id: "quality", label: "Face Quality Good", status: "idle" },
    { id: "encoding", label: "Generating Face Encoding", status: "idle" },
    { id: "compare", label: isRegisterMode ? "Saving Profile" : "Comparing Face", status: "idle" },
    { id: "success", label: isRegisterMode ? "Registration Successful" : "Authentication Successful", status: "idle" }
  ]);

  useEffect(() => {
    checkFaceStatus();
    startCamera();

    return () => {
      stopCamera();
    };
  }, [username]);

  const setStepStatus = (stepId, status) => {
    setSteps((prevSteps) =>
      prevSteps.map((s) => (s.id === stepId ? { ...s, status } : s))
    );
  };

  const checkFaceStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/status/${encodeURIComponent(username)}`);
      if (res.data && (res.data.registered || res.data.face_registered)) {
        setIsRegistered(true);
      } else {
        setIsRegistered(false);
      }
    } catch (err) {
      console.error("Error checking face status:", err);
    }
  };

  const startCamera = async () => {
    setCameraError(null);
    setStepStatus("camera", "running");
    setGuidanceText("Starting camera feed...");

    // Ensure any existing stream is cleanly stopped first
    stopCamera();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
      setCameraStatus("Online (640x480)");
      setStepStatus("camera", "done");
      setGuidanceText("Looking for face...");

      // Auto-trigger verification or registration based on explicit mode
      setTimeout(() => {
        if (isRegisterMode) {
          handleRegisterFace();
        } else {
          performVerificationWithAutoRetry();
        }
      }, 800);

    } catch (err) {
      console.warn("Webcam access denied or unavailable:", err);
      const errTxt = "Webcam access denied or device unavailable.";
      setCameraError(errTxt);
      setCameraStatus("Error");
      setStepStatus("camera", "failed");
      setErrorCode("CAMERA_ERROR");
      setFeedbackMessage(errTxt);
      toast.error("Camera Permission Denied");
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject;
      if (stream && stream.getTracks) {
        stream.getTracks().forEach((track) => track.stop());
      }
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    setCameraStatus("Offline");
  };

  const captureSingleFrameBase64 = () => {
    if (!videoRef.current || !hiddenCanvasRef.current) return null;
    const video = videoRef.current;
    const canvas = hiddenCanvasRef.current;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL("image/jpeg", 0.85);
  };

  // Rapid multi-frame capture sequence (15 frames in ~0.5s)
  const captureMultiFrameSequence = async (count = 15, delayMs = 35) => {
    const frames = [];
    for (let i = 0; i < count; i++) {
      const frame = captureSingleFrameBase64();
      if (frame) frames.push(frame);
      setCaptureProgress(Math.round(((i + 1) / count) * 100));
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    return frames;
  };

  const getErrorMessageAndGuidance = (errCode, serverMsg, alignment) => {
    let userMessage = serverMsg || "Face verification failed.";
    let guidance = "Hold still under clear lighting...";

    if (alignment && alignment.guidance_text) {
      guidance = alignment.guidance_text;
    }

    switch (errCode) {
      case "NO_FACE":
      case "NO_FACE_DETECTED":
        userMessage = "No face detected. Please position your face inside the camera frame.";
        guidance = "Position face inside frame";
        break;
      case "MULTIPLE_FACES":
      case "MULTIPLE_FACES_DETECTED":
        userMessage = "Multiple faces detected. Only the authorized user's face should be visible.";
        guidance = "Only 1 face should be visible";
        break;
      case "LOW_FACE_QUALITY":
      case "FACE_BLURRY":
      case "POOR_LIGHTING":
        userMessage = "Face quality is insufficient. Please improve lighting and keep your face centered.";
        guidance = alignment?.guidance_text || "Improve lighting & center face";
        break;
      case "FACE_AUTH_NOT_CONFIGURED":
      case "REFERENCE_FACE_MISSING":
      case "USER_NOT_REGISTERED":
        userMessage = "Face authentication is not configured. Please enable it from Security Settings.";
        guidance = "Not configured in Settings";
        break;
      case "ENCODING_MISMATCH":
        userMessage = "Biometric encoding format updated. Please re-register your face in Security Settings.";
        guidance = "Re-registration required";
        break;
      case "FACE_NOT_MATCHED":
      case "FACE_MISMATCH":
        userMessage = "Face does not match the registered face profile. Authentication denied.";
        guidance = "Biometric mismatch";
        break;
      case "SPOOF_DETECTED":
        userMessage = "Static photo or spoofing detected. Please perform natural movement.";
        guidance = "Natural movement required";
        break;
      case "ACCOUNT_LOCKED":
      case "FACE_AUTHENTICATION_LOCKED":
        userMessage = serverMsg || "Face authentication is temporarily restricted due to multiple failed attempts.";
        guidance = "Face authentication locked";
        break;
      case "REAUTHENTICATION_REQUIRED":
        userMessage = "Biometric registration requires active security-settings re-authentication.";
        guidance = "Re-authentication required";
        break;
      default:
        userMessage = serverMsg || "Face verification failed. Please try again.";
        break;
    }
    return { userMessage, guidance };
  };

  const handleRegisterFace = async () => {
    setLoading(true);
    setFeedbackMessage("");
    setErrorCode(null);
    setGuidanceText("Hold still for registration scan...");
    setStepStatus("face", "running");
    setStepStatus("quality", "running");
    setStepStatus("encoding", "running");

    try {
      const frames = await captureMultiFrameSequence(15, 35);

      if (!frames || frames.length === 0) {
        toast.error("Camera capture failed. Hold face steady.");
        setStepStatus("encoding", "failed");
        setLoading(false);
        return;
      }

      setStepStatus("face", "done");
      setStepStatus("quality", "done");
      setStepStatus("encoding", "done");
      setGuidanceText("Generating facial embedding vector...");

      const token = localStorage.getItem("token");
      const reauthToken = sessionStorage.getItem("biometric_reauth_token");

      const res = await axios.post(
        `${API_BASE}/register`,
        {
          frames: frames,
          reauth_token: reauthToken
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Biometric-Reauth-Token": reauthToken
          }
        }
      );

      if (res.data && res.data.success) {
        setIsRegistered(true);
        setStepStatus("compare", "done");
        setStepStatus("success", "done");
        setGuidanceText("Registration successful!");
        setFeedbackMessage("Face Recognition Enabled Successfully!");
        toast.success("Face Biometric Profile Registered Successfully");

        sessionStorage.removeItem("biometric_reauth_token");
        setTimeout(() => {
          navigate("/settings");
        }, 1500);
      }
    } catch (err) {
      const errRes = err.response ? err.response.data : {};
      const errCode = errRes.error || "REGISTRATION_FAILED";
      const { userMessage, guidance } = getErrorMessageAndGuidance(errCode, errRes.message, errRes.alignment);
      
      setStepStatus("encoding", "failed");
      setErrorCode(errCode);
      setGuidanceText(guidance);
      setFeedbackMessage(userMessage);
      toast.error(userMessage);
    } finally {
      setLoading(false);
      setCaptureProgress(0);
    }
  };


  // Auto-retry verification loop with clear pipeline steps & user guidance
  const performVerificationWithAutoRetry = async () => {
    setLoading(true);
    setConfidenceScore(null);
    setFaceDistance(null);
    setErrorCode(null);
    setFeedbackMessage("");

    setStepStatus("face", "running");
    setStepStatus("quality", "idle");
    setStepStatus("encoding", "idle");
    setStepStatus("compare", "idle");
    setStepStatus("success", "idle");

    const startTime = Date.now();
    const timeoutMs = 8000; // 8 seconds auto-retry window

    let attemptCount = 0;
    let verifiedSuccess = false;
    let lastErrCode = null;
    let lastErrMsg = null;

    while (Date.now() - startTime < timeoutMs && !verifiedSuccess) {
      attemptCount += 1;
      setDetectionStatus("Scanning...");

      try {
        const frames = await captureMultiFrameSequence(15, 30);
        setFramesAnalyzed(frames.length);

        setStepStatus("face", "done");
        setDetectionStatus("Face Detected");
        setStepStatus("quality", "running");

        setStepStatus("encoding", "running");
        setStepStatus("compare", "running");

        const res = await axios.post(`${API_BASE}/verify`, {
          username: username,
          frames: frames
        });

        const dist = res.data.distance !== undefined ? res.data.distance : null;
        const score = res.data.confidence_score !== undefined ? res.data.confidence_score : 0;
        const validCount = res.data.valid_faces_detected || 0;
        const alignment = res.data.alignment;

        setFaceDistance(dist);
        setConfidenceScore(score);
        setValidFacesDetected(validCount);

        if (validCount > 0) {
          setStepStatus("quality", "done");
          setFaceQualityScore(`Good (${validCount}/${frames.length} frames)`);
        }

        if (res.data && res.data.is_match) {
          verifiedSuccess = true;
          setStepStatus("encoding", "done");
          setStepStatus("compare", "done");
          setStepStatus("success", "done");

          setGuidanceText("Authentication successful.");
          setFeedbackMessage(`Face Verified Successfully (${score}% Match, Distance: ${dist})! Redirecting...`);

          toast.success("Face Verified Successfully");
          toast.info("Redirecting to Dashboard...");

          if (res.data.access_token) {
            localStorage.setItem("token", res.data.access_token);
          }
          if (res.data.user) {
            localStorage.setItem("userData", JSON.stringify(res.data.user));
          }
          localStorage.setItem("username", username);

          sessionStorage.setItem("faceVerified", "true");
          sessionStorage.setItem("authenticated", "true");
          localStorage.setItem("faceVerified", "true");
          localStorage.setItem("authenticated", "true");

          sessionStorage.removeItem("otp_verified");
          sessionStorage.removeItem("otp_username");
          sessionStorage.removeItem("pending_user");

          setTimeout(() => {
            navigate("/dashboard", { replace: true });
          }, 1000);

          break;
        } else {
          lastErrCode = res.data.error || "FACE_NOT_MATCHED";
          lastErrMsg = res.data.message || "Face does not match registered profile.";
          const { userMessage, guidance } = getErrorMessageAndGuidance(lastErrCode, lastErrMsg, alignment);
          setGuidanceText(guidance);
        }

      } catch (err) {
        const errRes = err.response ? err.response.data : {};
        lastErrCode = errRes.error || "VERIFICATION_FAILED";
        lastErrMsg = errRes.message || "Face verification error.";

        const { userMessage, guidance } = getErrorMessageAndGuidance(lastErrCode, lastErrMsg, errRes.alignment);
        setGuidanceText(guidance);

        if (lastErrCode === "NO_FACE" || lastErrCode === "NO_FACE_DETECTED") {
          setStepStatus("face", "failed");
        } else if (lastErrCode === "LOW_FACE_QUALITY" || lastErrCode === "MULTIPLE_FACES") {
          setStepStatus("quality", "failed");
        } else if (lastErrCode === "REFERENCE_FACE_MISSING" || lastErrCode === "ENCODING_MISMATCH") {
          setStepStatus("encoding", "failed");
          setStepStatus("compare", "failed");
          break;
        } else if (lastErrCode === "FACE_NOT_MATCHED" || lastErrCode === "FACE_MISMATCH") {
          setStepStatus("quality", "done");
          setStepStatus("encoding", "done");
          setStepStatus("compare", "failed");
        }
      }

      await new Promise((r) => setTimeout(r, 350));
    }

    if (!verifiedSuccess) {
      if (lastErrCode === "FACE_NOT_MATCHED" || lastErrCode === "FACE_MISMATCH") {
        setStepStatus("quality", "done");
        setStepStatus("encoding", "done");
        setStepStatus("compare", "failed");
        setStepStatus("success", "failed");
      } else {
        setStepStatus("compare", "failed");
        setStepStatus("success", "failed");
      }
      setErrorCode(lastErrCode);

      const { userMessage, guidance } = getErrorMessageAndGuidance(lastErrCode, lastErrMsg, null);
      setGuidanceText(guidance);
      setFeedbackMessage(userMessage);

      toast.error(userMessage);
    }

    setLoading(false);
    setCaptureProgress(0);
  };

  const handleRetry = () => {
    setFeedbackMessage("");
    setErrorCode(null);
    setConfidenceScore(null);
    setFaceDistance(null);
    setSteps([
      { id: "otp", label: "OTP Verified", status: "done" },
      { id: "camera", label: "Camera Started", status: isCameraActive ? "done" : "idle" },
      { id: "face", label: "Face Detected", status: "idle" },
      { id: "quality", label: "Face Quality Good", status: "idle" },
      { id: "encoding", label: "Generating Face Encoding", status: "idle" },
      { id: "compare", label: "Comparing Face", status: "idle" },
      { id: "success", label: "Authentication Successful", status: "idle" }
    ]);
    if (!isCameraActive) {
      startCamera();
    } else {
      performVerificationWithAutoRetry();
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl text-slate-100 max-w-xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-500/10 rounded-2xl border border-indigo-500/30 text-indigo-400">
            <FaShieldAlt className="text-2xl" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">
              {isRegisterMode ? "Face Recognition Registration" : "Face Verification Required"}
            </h3>
            <p className="text-xs text-slate-400">
              {isRegisterMode
                ? "Capture trusted face biometric profile from Security Settings"
                : "Please look at the camera to verify your identity."}
            </p>
          </div>
        </div>

        <div>
          {isRegistered ? (
            <span className="px-3 py-1 text-xs rounded-full font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow">
              <FaUserCheck /> Registered
            </span>
          ) : (
            <span className="px-3 py-1 text-xs rounded-full font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 shadow">
              <FaUserPlus /> Not Registered
            </span>
          )}
        </div>
      </div>


      <canvas ref={hiddenCanvasRef} className="hidden" />

      {/* Video Stream Preview & Target Reticle */}
      <div className="relative w-full h-72 bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-inner flex items-center justify-center">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover transform -scale-x-100 ${isCameraActive ? "block" : "hidden"}`}
        />

        {/* Dynamic Target Alignment Reticle */}
        {isCameraActive && (
          <div className="absolute inset-0 border-2 border-indigo-500/20 pointer-events-none rounded-2xl flex flex-col items-center justify-center">
            <div className="w-52 h-60 border-2 border-emerald-400/70 rounded-full animate-pulse flex items-center justify-center shadow-lg shadow-emerald-500/20 relative">
              <span className="text-[11px] uppercase font-bold tracking-wider text-emerald-300 bg-slate-950/85 px-3.5 py-1.5 rounded-full border border-emerald-500/50 shadow flex items-center gap-1.5">
                <FaExpandArrowsAlt className="text-emerald-400" />
                {guidanceText}
              </span>
            </div>
          </div>
        )}

        {/* Camera Offline Fallback */}
        {!isCameraActive && (
          <div className="text-center p-6 space-y-3">
            <FaCamera className="text-5xl text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400 max-w-xs mx-auto">
              {cameraError || "Camera offline. Click below to start camera."}
            </p>
            <button
              onClick={startCamera}
              className="px-4 py-2 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-lg transition flex items-center gap-2 mx-auto"
            >
              <FaCamera /> Start Camera
            </button>
          </div>
        )}

        {/* Progress Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-sm flex flex-col items-center justify-center p-6 z-20 space-y-3">
            <FaSync className="text-4xl text-indigo-400 animate-spin" />
            <p className="text-xs font-bold text-indigo-200 uppercase tracking-wider">
              {guidanceText} ({captureProgress}%)
            </p>
            <div className="w-48 h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-200"
                style={{ width: `${captureProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Live System Diagnostics Dashboard Grid */}
      <div className="grid grid-cols-3 gap-2.5 text-xs font-mono">
        <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-500 block uppercase">Camera Status</span>
          <strong className="text-indigo-300 text-[11px] truncate block">{cameraStatus}</strong>
        </div>
        <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-500 block uppercase">Detection</span>
          <strong className="text-emerald-300 text-[11px] truncate block">{detectionStatus}</strong>
        </div>
        <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-500 block uppercase">Face Quality</span>
          <strong className="text-cyan-300 text-[11px] truncate block">{faceQualityScore}</strong>
        </div>
      </div>

      {/* Live Verification Pipeline */}
      <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2.5 text-xs">
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 border-b border-slate-800 pb-2">
          Live Verification Pipeline
        </h4>
        <div className="grid grid-cols-2 gap-2">
          {steps.map((step) => (
            <div
              key={step.id}
              className={`p-2.5 rounded-xl border flex items-center gap-2 transition ${
                step.status === "done"
                  ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-300 font-semibold"
                  : step.status === "running"
                  ? "bg-indigo-950/40 border-indigo-500/40 text-indigo-300 font-semibold animate-pulse"
                  : step.status === "failed"
                  ? "bg-rose-950/30 border-rose-500/40 text-rose-300 font-semibold"
                  : "bg-slate-900/40 border-slate-800 text-slate-500"
              }`}
            >
              {step.status === "done" ? (
                <FaCheckCircle className="text-emerald-400 text-sm shrink-0" />
              ) : step.status === "running" ? (
                <FaSync className="text-indigo-400 text-sm animate-spin shrink-0" />
              ) : step.status === "failed" ? (
                <FaTimesCircle className="text-rose-400 text-sm shrink-0" />
              ) : (
                <span className="w-3.5 h-3.5 rounded-full border border-slate-700 shrink-0" />
              )}
              <span className="truncate">{step.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* User Guidance / Feedback Banner */}
      {feedbackMessage && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-start gap-3 shadow-lg ${
            steps.find((s) => s.id === "success")?.status === "done"
              ? "bg-emerald-950/50 border-emerald-500/50 text-emerald-200"
              : steps.find((s) => s.id === "compare")?.status === "failed"
              ? "bg-rose-950/50 border-rose-500/50 text-rose-200"
              : "bg-indigo-950/50 border-indigo-500/50 text-indigo-200"
          }`}
        >
          {steps.find((s) => s.id === "success")?.status === "done" ? (
            <FaCheckCircle className="text-emerald-400 text-lg shrink-0 mt-0.5" />
          ) : (
            <FaExclamationTriangle className="text-amber-400 text-lg shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <div className="font-bold text-sm">{feedbackMessage}</div>
            {errorCode && <div className="text-[11px] opacity-80 font-mono mt-1">Code: {errorCode}</div>}
          </div>
        </div>
      )}

      {/* Recognition Confidence & Biometric Distance Metric Panel */}
      {(confidenceScore !== null || faceDistance !== null) && (
        <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex justify-between items-center text-xs font-bold border-b border-slate-800 pb-2">
            <span className="text-slate-400">Biometric Distance Metric</span>
            <span className="font-mono text-cyan-300 text-sm">
              Distance: {faceDistance !== null ? faceDistance : "N/A"} (Max Allowed: ≤ 0.58)
            </span>
          </div>

          <div className="flex justify-between text-xs font-bold">
            <span className="text-slate-400">Match Confidence Score</span>
            <span className={confidenceScore >= 70 ? "text-emerald-400 font-mono text-sm" : "text-rose-400 font-mono text-sm"}>
              {confidenceScore}%
            </span>
          </div>
          <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
            <div
              className={`h-full transition-all duration-700 ${
                confidenceScore >= 70
                  ? "bg-gradient-to-r from-emerald-500 to-teal-400 shadow-lg shadow-emerald-500/30"
                  : "bg-gradient-to-r from-rose-500 to-amber-500"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, confidenceScore))}%` }}
            />
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="w-full">
        {isRegisterMode ? (
          <button
            onClick={handleRegisterFace}
            disabled={loading || !isCameraActive}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl text-xs font-bold shadow-lg transition"
          >
            <FaUserPlus className="text-sm" /> {loading ? "Scanning & Registering Face..." : "Register Face Profile"}
          </button>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={handleRetry}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-3 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white rounded-xl text-xs font-bold shadow-lg transition"
            >
              <FaLock className="text-sm" /> {loading ? "Verifying Identity..." : "Start Face Verification"}
            </button>
            <button
              onClick={() => {
                sessionStorage.clear();
                localStorage.removeItem("pre_token");
                navigate("/");
              }}
              className="flex items-center justify-center gap-2 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition border border-slate-700"
            >
              Cancel & Return to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

