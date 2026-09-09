import {
  BrowserRouter,
  Routes,
  Route
} from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import Register from "./pages/Register";
import Login from "./pages/login";
import Dashboard from "./pages/dashboard";
import Devices from "./pages/devices";
import History from "./pages/history";
import Analytics from "./pages/analytics";
import Alerts from "./pages/alerts";
import Settings from "./pages/settings";
import Profile from "./pages/Profile";
import OtpVerification from "./pages/OtpVerification";

import LiveSessionStatusPanel from "./components/LiveSessionStatusPanel";

import MouseDashboardPage from "./pages/MouseDashboardPage";
import KeystrokeDashboardPage from "./pages/KeystrokeDashboardPage";
import FaceAuthPage from "./pages/FaceAuthPage";
import BlockchainDashboardPage from "./pages/BlockchainDashboardPage";

function App() {
  return (
    <BrowserRouter>
      <LiveSessionStatusPanel />
      <ToastContainer
        position="top-right"
        autoClose={3500}
        hideProgressBar={false}
        newestOnTop={true}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />

      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Login />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/otp" element={<OtpVerification />} />

        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/mouse-dashboard" element={<MouseDashboardPage />} />
        <Route path="/mouse" element={<MouseDashboardPage />} />
        <Route path="/keystroke-dashboard" element={<KeystrokeDashboardPage />} />
        <Route path="/keystroke" element={<KeystrokeDashboardPage />} />
        <Route path="/face-auth" element={<FaceAuthPage />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/history" element={<History />} />
        <Route path="/blockchain" element={<BlockchainDashboardPage />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;