import logging
import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Configure logging format across Flask app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Explicitly load backend/.env file relative to this script
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(backend_dir, ".env")

try:
    from dotenv import load_dotenv
    if os.path.exists(env_file_path):
        load_dotenv(dotenv_path=env_file_path, override=True)
        print(f"[ENV LOADER] Loaded runtime environment from: {env_file_path}")
    else:
        print(f"[ENV LOADER WARNING] Environment file not found at: {env_file_path}")
except ImportError:
    print("[ENV LOADER WARNING] python-dotenv package not installed.")

# Check for SMTP credentials at startup
smtp_user = os.getenv("SMTP_USERNAME") or os.getenv("MAIL_USERNAME")
smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")

if not smtp_user or not smtp_pass:
    startup_warning = "[SMTP CONFIG WARNING] SMTP credentials are missing in backend/.env. OTP emails cannot be sent."
    print(startup_warning)
    logger.warning(startup_warning)
else:
    print(f"[SMTP CONFIG SUCCESS] SMTP credentials loaded for user: {smtp_user}")

from routes.auth import auth_bp
from routes.behavior import behavior_bp
from routes.mouse_auth import mouse_auth_bp
from routes.keystroke_auth import keystroke_auth_bp
from routes.device_fingerprint import device_fingerprint_bp
from routes.face_auth import face_auth_bp
from routes.blockchain_security import blockchain_security_bp

app = Flask(__name__)

CORS(app)

app.config['JWT_SECRET_KEY'] = 'anomatrix_super_secure_zero_trust_secret_key_2026'

jwt = JWTManager(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(behavior_bp, url_prefix='/api/behavior')

# Register mouse authentication blueprint at root and /api/mouse for maximum routing flexibility
app.register_blueprint(mouse_auth_bp)
app.register_blueprint(mouse_auth_bp, name="mouse_auth_api", url_prefix='/api/mouse')

app.register_blueprint(keystroke_auth_bp)
app.register_blueprint(keystroke_auth_bp, name="keystroke_auth_api", url_prefix='/api/keystroke')

# Register device fingerprinting blueprint at root and /api/device
app.register_blueprint(device_fingerprint_bp)
app.register_blueprint(device_fingerprint_bp, name="device_fingerprint_api", url_prefix='/api/device')

# Register face authentication blueprint at root and /api/face
app.register_blueprint(face_auth_bp)
app.register_blueprint(face_auth_bp, name="face_auth_api", url_prefix='/api/face')

# Register blockchain blueprint
app.register_blueprint(blockchain_security_bp)


@app.route('/')
def home():
    return {
        "message": "AnomatriX Backend Running",
        "status": "online",
        "modules": ["auth", "behavior", "mouse", "keystroke", "device", "face"]
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)