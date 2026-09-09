import FingerprintJS from "@fingerprintjs/fingerprintjs";
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import SecurityConditionsBanner from "../components/SecurityConditionsBanner";
import "./login.css";

function Register() {

  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleRegister = async () => {

    if(password !== confirmPassword){
      alert("Passwords do not match");
      return;
    }

    try{

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

      await axios.post(
        "http://127.0.0.1:5000/register",
        {
          name,
          email,
          department,
          employee_id: employeeId,
          username,
          password,
          device_id: visitorId,
          browser: navigator.userAgent,
          os: navigator.platform
        }
      );

      alert("Registration Successful");

      navigate("/");

    }
    catch(error){

      console.log(error);

      alert("Registration Failed");

    }

  };

  return(

    <div className="login-container">

      <h2 className="login-title">
        Register User
      </h2>

      {/* Security Conditions & Protocol Banner */}
      <SecurityConditionsBanner title="Zero-Trust Registration Protocol" />

      <input
        className="input-field"
        placeholder="Full Name"
        onChange={(e)=>setName(e.target.value)}
      />

      <input
        className="input-field"
        placeholder="Email"
        onChange={(e)=>setEmail(e.target.value)}
      />

      <input
        className="input-field"
        placeholder="Department"
        onChange={(e)=>setDepartment(e.target.value)}
      />

      <input
        className="input-field"
        placeholder="Employee / Student ID"
        onChange={(e)=>setEmployeeId(e.target.value)}
      />

      <input
        className="input-field"
        placeholder="Username"
        onChange={(e)=>setUsername(e.target.value)}
      />

      <input
        type="password"
        className="input-field"
        placeholder="Password"
        onChange={(e)=>setPassword(e.target.value)}
      />

      <input
        type="password"
        className="input-field"
        placeholder="Confirm Password"
        onChange={(e)=>setConfirmPassword(e.target.value)}
      />

      <button
        className="login-button"
        onClick={handleRegister}
      >
        Register
      </button>

      <p
        style={{
          marginTop:"20px",
          color:"white"
        }}
      >
        Already have an account?

        <Link
          to="/"
          style={{
            color:"#00d4ff",
            marginLeft:"8px"
          }}
        >
          Login
        </Link>

      </p>

    </div>

  );

}

export default Register;