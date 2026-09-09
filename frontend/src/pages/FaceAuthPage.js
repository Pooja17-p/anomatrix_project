import React from "react";
import { useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import FaceAuthWidget from "../components/FaceAuthWidget";
import { FaShieldAlt, FaCamera, FaUserCheck, FaInfoCircle } from "react-icons/fa";

export default function FaceAuthPage() {
  const [searchParams] = useSearchParams();
  const flow = searchParams.get("flow");
  const isMfaFlow = flow === "mfa_verify" || (sessionStorage.getItem("otp_verified") === "true" && flow !== "settings_register");


  const username = sessionStorage.getItem("pending_user") || localStorage.getItem("username") || "admin";

  // During MFA login sequence, render full-screen clean authentication UI
  if (isMfaFlow) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 sm:p-6 animate-fade-in">
        <div className="w-full max-w-xl">
          <FaceAuthWidget username={username} />
        </div>
      </div>
    );
  }

  // When updating from Settings/Profile
  return (
    <div className="dashboard-page flex bg-slate-950 min-h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col ml-[250px] min-w-0">
        <Topbar />

        <main className="p-8 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <div>
              <div className="flex items-center gap-3">
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
                  <FaCamera className="text-2xl" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-100">Face Recognition Authentication</h1>
                  <p className="text-sm text-slate-400">Zero Trust Biometric Multi-Factor Authentication</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 text-slate-300">
              <FaShieldAlt className="text-emerald-400" />
              <span>Biometric Protection: Active</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7">
              <FaceAuthWidget username={username} />
            </div>

            <div className="lg:col-span-5 space-y-6">
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 border-b border-slate-800 pb-3">
                  <FaUserCheck className="text-indigo-400" /> Registration Guidelines
                </h3>

                <ul className="text-xs text-slate-300 space-y-3">
                  <li className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>Center Alignment:</strong> Position your face within the camera target box with clear lighting.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>Single Person Rule:</strong> Ensure exactly 1 face is visible.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>128-d Vector Storage:</strong> Raw photos are never saved. Only 128-d mathematical vectors are stored securely.</span>
                  </li>
                </ul>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 border-b border-slate-800 pb-3">
                  <FaInfoCircle className="text-cyan-400" /> Technical Parameters
                </h3>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Match Threshold</span>
                    <strong className="text-cyan-300 font-mono">Confidence ≥ 90%</strong>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Embedding Dimension</span>
                    <strong className="text-indigo-300 font-mono">128 Float Vector</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
