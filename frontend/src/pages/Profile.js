import Sidebar from "../components/Sidebar";
import "./profile.css";

function Profile() {

  const user = JSON.parse(localStorage.getItem("userData"));

  const username = localStorage.getItem("username");

  if(!user){

    return <h2>No User Found</h2>;

  }

  return(

    <div className="app-container">

      <Sidebar/>

      <div className="profile-container">

        <h1>User Profile</h1>

        <div className="profile-card">

          <div className="profile-item">

            <h3>Name</h3>

            <p>{user.name}</p>

          </div>

          <div className="profile-item">

            <h3>Email</h3>

            <p>{user.email}</p>

          </div>

          <div className="profile-item">

            <h3>Department</h3>

            <p>{user.department}</p>

          </div>

          <div className="profile-item">

            <h3>Employee ID</h3>

            <p>{user.employee_id}</p>

          </div>

          <div className="profile-item">

            <h3>Username</h3>

            <p>{username}</p>

          </div>

          <div className="profile-item">

            <h3>Browser</h3>

            <p>{user.browser}</p>

          </div>

          <div className="profile-item">

            <h3>Operating System</h3>

            <p>{user.os}</p>

          </div>

          <div className="profile-item">

            <h3>Trust Score</h3>

            <p>{user.trust_score}</p>

          </div>

          <div className="profile-item">

            <h3>Risk Level</h3>

            <p>{user.risk_level}</p>

          </div>

        </div>

      </div>

    </div>

  );

}

export default Profile;