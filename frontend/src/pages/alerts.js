import Sidebar from "../components/Sidebar";
import "./alerts.css";

function Alerts() {

  const user =
    JSON.parse(localStorage.getItem("userData"));

  const alerts = user?.alerts || [];

  return (

    <div className="alerts-page">

      <Sidebar />

      <div className="alerts-content">

        <h1>Security Alerts</h1>

        {

          alerts.length === 0 ?

          (

            <div className="alert-card low">

              <h2>✅ No Alerts</h2>

              <p>
                Your account is secure.
              </p>

            </div>

          )

          :

          (

            alerts.map((alert,index)=>(

              <div
                key={index}
                className={`alert-card ${alert.level.toLowerCase()}`}
              >

                <h2>

                  {

                    alert.level==="High"

                    ?

                    "🔴"

                    :

                    alert.level==="Medium"

                    ?

                    "🟡"

                    :

                    "🟢"

                  }

                  {" "}

                  {alert.title}

                </h2>

                <p>

                  {alert.message}

                </p>

                <h4>

                  Risk Level :

                  {" "}

                  {alert.level}

                </h4>

              </div>

            ))

          )

        }

      </div>

    </div>

  );

}

export default Alerts;