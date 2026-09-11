import os
import smtplib
import logging
import threading
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def send_otp_email_async(to_email, username, otp_code):
    """
    Spawns a background thread to send the production OTP email asynchronously without blocking the Flask API request,
    or calls _send_otp_email_sync synchronously when running on Vercel to prevent serverless execution freeze.
    """
    log_msg = f"[MFA EMAIL] Email function called for recipient: {to_email}"
    print(log_msg)
    logger.info(log_msg)

    # When deployed on Vercel, execute synchronously to prevent serverless process termination
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        vercel_log = "[MFA EMAIL] Vercel environment detected. Executing _send_otp_email_sync synchronously."
        print(vercel_log)
        logger.info(vercel_log)
        return _send_otp_email_sync(to_email, username, otp_code)

    thread = threading.Thread(
        target=_send_otp_email_sync,
        args=(to_email, username, otp_code),
        daemon=True
    )
    thread.start()



def _send_otp_email_sync(to_email, username, otp_code):
    """
    Connects to Gmail / SMTP server and transmits the production OTP verification code to user's registered email.
    Logs detailed progress and exact errors if delivery fails.
    """
    # Explicitly load backend/.env file relative to backend root
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file_path = os.path.join(backend_dir, ".env")
    try:
        from dotenv import load_dotenv
        if os.path.exists(env_file_path):
            load_dotenv(dotenv_path=env_file_path, override=True)
    except ImportError:
        pass

    # 1. Load SMTP configuration supporting both SMTP_* and MAIL_* env variables
    smtp_host = os.getenv("SMTP_HOST") or os.getenv("MAIL_SERVER") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("MAIL_PORT") or 587)
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("MAIL_USERNAME") or ""
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD") or ""
    smtp_sender = os.getenv("SMTP_SENDER") or os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("SENDER_EMAIL") or smtp_username or "noreply@anomatrix.io"
    use_tls_str = os.getenv("MAIL_USE_TLS") or os.getenv("USE_TLS") or os.getenv("SMTP_USE_TLS", "true")
    use_tls = str(use_tls_str).lower() == "true"

    # 2. Mask password for secure logging
    masked_password = "****" if smtp_password else "<NOT CONFIGURED>"
    display_username = smtp_username if smtp_username else "<NOT CONFIGURED>"

    # 3. Log loaded SMTP configuration
    config_log = (
        f"[MFA EMAIL CONFIG]\n"
        f"  - SMTP Host: {smtp_host}\n"
        f"  - SMTP Port: {smtp_port}\n"
        f"  - SMTP Username: {display_username}\n"
        f"  - SMTP Password: {masked_password}\n"
        f"  - SMTP Sender: {smtp_sender}\n"
        f"  - Use TLS: {use_tls}"
    )
    print(config_log)
    logger.info(config_log)

    # 4. Verify recipient email exists
    if not to_email:
        err_msg = f"[MFA EMAIL ERROR] No recipient email provided for user '{username}'. Delivery aborted."
        print(err_msg)
        logger.error(err_msg)
        return False

    # 5. Check if SMTP credentials are configured
    if not smtp_username or not smtp_password:
        warn_msg = f"[MFA EMAIL WARNING] SMTP credentials not fully configured in backend/.env for recipient {to_email}. Set SMTP_USERNAME and SMTP_PASSWORD (or MAIL_USERNAME / MAIL_PASSWORD)."
        print(warn_msg)
        logger.warning(warn_msg)
        return False

    try:
        # 6. Build MIME email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "ANOMATRIX Zero Trust Security Verification Code"
        msg["From"] = f"ANOMATRIX Security <{smtp_sender}>"
        msg["To"] = to_email

        text_body = (
            f"Hello {username},\n\n"
            f"Your One-Time Password (OTP) for authentication is: {otp_code}\n"
            f"This code expires in 5 minutes.\n"
            f"If you did not request this login, ignore this email.\n"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 500px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            .header {{ text-align: center; border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 20px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #00d4ff; letter-spacing: 1px; }}
            .code-box {{ background: #0f172a; border: 2px dashed #00d4ff; border-radius: 8px; padding: 15px; text-align: center; margin: 25px 0; }}
            .code {{ font-size: 36px; font-weight: bold; color: #38bdf8; letter-spacing: 8px; font-family: monospace; }}
            .footer {{ font-size: 12px; color: #64748b; text-align: center; margin-top: 25px; border-top: 1px solid #334155; padding-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="logo">ANOMATRIX Zero Trust</div>
              <p style="color: #94a3b8; font-size: 14px; margin-top: 5px;">Security Verification Protocol</p>
            </div>
            <p>Hello <strong>{username}</strong>,</p>
            <p style="color: #cbd5e1;">Your One-Time Password (OTP) for authentication is:</p>
            
            <div class="code-box">
              <div class="code">{otp_code}</div>
            </div>

            <p style="color: #94a3b8; font-size: 13px;">This code expires in <strong>5 minutes</strong>.</p>
            <p style="color: #ef4444; font-size: 12px;">If you did not request this login, ignore this email.</p>
            
            <div class="footer">
              ANOMATRIX Behavioral Biometrics & Zero Trust Engine &copy; 2026
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # 7. Connect to SMTP server
        connect_log = f"[MFA EMAIL] Attempting SMTP connection to {smtp_host}:{smtp_port}..."
        print(connect_log)
        logger.info(connect_log)

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            if use_tls or smtp_port == 587:
                server.starttls()

        conn_success_log = "[MFA EMAIL] SMTP connection established successfully"
        print(conn_success_log)
        logger.info(conn_success_log)

        # 8. Authenticate SMTP user
        auth_log = f"[MFA EMAIL] Authenticating SMTP user: {smtp_username}..."
        print(auth_log)
        logger.info(auth_log)

        server.login(smtp_username, smtp_password)

        auth_success_log = "[MFA EMAIL] SMTP Authentication successful"
        print(auth_success_log)
        logger.info(auth_success_log)

        # 9. Transmit message
        tx_log = f"[MFA EMAIL] Transmitting message from {smtp_sender} to {to_email}..."
        print(tx_log)
        logger.info(tx_log)

        server.sendmail(smtp_sender, [to_email], msg.as_string())
        server.quit()

        success_log = f"[MFA EMAIL] Email successfully sent to {to_email}"
        print(success_log)
        logger.info(success_log)
        return True

    except smtplib.SMTPAuthenticationError as auth_err:
        stack_trace = traceback.format_exc()
        err_msg = (
            f"[MFA EMAIL ERROR] SMTP Authentication Failed for {to_email}.\n"
            f"If using Gmail, verify that you are using a 16-character Google App Password (https://myaccount.google.com/apppasswords).\n"
            f"Exact SMTP Error: {str(auth_err)}\n"
            f"Stack Trace:\n{stack_trace}"
        )
        print(err_msg)
        logger.error(err_msg)
        return False
    except Exception as e:
        stack_trace = traceback.format_exc()
        err_msg = (
            f"[MFA EMAIL ERROR] Failed to send OTP email to {to_email}:\n"
            f"Exception Type: {type(e).__name__}\n"
            f"Details: {str(e)}\n"
            f"Stack Trace:\n{stack_trace}"
        )
        print(err_msg)
        logger.error(err_msg)
        return False


def send_face_security_alert_async(to_email, username, event_details):
    """
    Spawns a background thread to send a security alert email when facial verification fails.
    """
    log_msg = f"[SECURITY EMAIL] Spawning thread for security alert recipient: {to_email}"
    print(log_msg)
    logger.info(log_msg)

    thread = threading.Thread(
        target=_send_face_security_alert_sync,
        args=(to_email, username, event_details),
        daemon=True
    )
    thread.start()


def _send_face_security_alert_sync(to_email, username, event_details):
    """
    Connects to SMTP server and transmits ANOMATRIX Security Alert – Failed Face Authentication email.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file_path = os.path.join(backend_dir, ".env")
    try:
        from dotenv import load_dotenv
        if os.path.exists(env_file_path):
            load_dotenv(dotenv_path=env_file_path, override=True)
    except ImportError:
        pass

    smtp_host = os.getenv("SMTP_HOST") or os.getenv("MAIL_SERVER") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("MAIL_PORT") or 587)
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("MAIL_USERNAME") or ""
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD") or ""
    smtp_sender = os.getenv("SMTP_SENDER") or os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("SENDER_EMAIL") or smtp_username or "noreply@anomatrix.io"
    use_tls = str(os.getenv("MAIL_USE_TLS") or os.getenv("USE_TLS") or "true").lower() == "true"

    if not to_email:
        logger.warning(f"[SECURITY EMAIL] No recipient email for user '{username}'. Alert skipped.")
        return False

    if not smtp_username or not smtp_password:
        logger.warning(f"[SECURITY EMAIL] SMTP credentials not configured. Security alert for {username} logged locally.")
        print(f"[SECURITY ALERT FOR {username}] Failed Face Auth from IP: {event_details.get('ip_address')}, Device: {event_details.get('device')}, Reason: {event_details.get('reason')}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "ANOMATRIX Security Alert – Failed Face Authentication"
        msg["From"] = f"ANOMATRIX Security Alert <{smtp_sender}>"
        msg["To"] = to_email

        timestamp_str = event_details.get("timestamp") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        ip_addr = event_details.get("ip_address", "Unknown IP")
        location = event_details.get("location", "Unknown Location")
        device_info = event_details.get("device", "Unknown Device")
        risk_level = event_details.get("risk_level", "High")
        reason = event_details.get("reason", "Facial biometric verification failed")

        text_body = (
            f"ANOMATRIX SECURITY ALERT\n\n"
            f"Unsuccessful facial recognition attempt detected for account: {username}\n\n"
            f"Details:\n"
            f"Account: {username}\n"
            f"Authentication Method: Face Recognition\n"
            f"Status: FAILED\n"
            f"Date & Time: {timestamp_str}\n"
            f"IP Address: {ip_addr}\n"
            f"Location: {location}\n"
            f"Device: {device_info}\n"
            f"Risk Level: {risk_level}\n"
            f"Failure Reason: {reason}\n\n"
            f"If this was not you, please log into ANOMATRIX immediately and review your security settings."
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #1e293b; border: 1px solid #ef4444; border-radius: 12px; padding: 30px; box-shadow: 0 10px 25px rgba(239, 68, 68, 0.2); }}
            .header {{ text-align: center; border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 20px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #ef4444; letter-spacing: 1px; }}
            .alert-box {{ background: #450a0a; border: 1px solid #dc2626; border-radius: 8px; padding: 15px; margin: 20px 0; }}
            .field {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #334155; font-size: 13px; }}
            .field-label {{ color: #94a3b8; font-weight: 500; }}
            .field-val {{ color: #f8fafc; font-weight: bold; font-family: monospace; }}
            .badge-failed {{ color: #ef4444; background: rgba(239,68,68,0.2); padding: 2px 8px; border-radius: 4px; border: 1px solid #ef4444; }}
            .footer {{ font-size: 12px; color: #64748b; text-align: center; margin-top: 25px; border-top: 1px solid #334155; padding-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="logo">🚨 ANOMATRIX Security Alert</div>
              <p style="color: #fca5a5; font-size: 14px; margin-top: 5px;">Failed Biometric Authentication Attempt</p>
            </div>
            
            <p>Hello <strong>{username}</strong>,</p>
            <p style="color: #cbd5e1; font-size: 14px;">An unsuccessful facial authentication attempt occurred on your account.</p>

            <div class="alert-box">
              <div style="color: #f8fafc; font-weight: bold; margin-bottom: 10px; font-size: 14px;">Event Telemetry Overview</div>
              
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Account/User:</span> <strong style="color:#ffffff;">{username}</strong>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Authentication Method:</span> <strong style="color:#38bdf8;">Face Recognition</strong>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Status:</span> <span class="badge-failed">FAILED</span>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Timestamp:</span> <strong style="color:#ffffff;">{timestamp_str}</strong>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">IP Address:</span> <strong style="color:#ffffff;">{ip_addr}</strong>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Location:</span> <strong style="color:#ffffff;">{location}</strong>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Device Info:</span> <strong style="color:#ffffff;">{device_info}</strong>
              </div>
              <div className="field" style="margin-bottom: 6px;">
                <span style="color:#94a3b8;">Risk Level:</span> <strong style="color:#ef4444;">{risk_level}</strong>
              </div>
              <div className="field">
                <span style="color:#94a3b8;">Failure Reason:</span> <strong style="color:#fca5a5;">{reason}</strong>
              </div>
            </div>

            <p style="color: #94a3b8; font-size: 12px; line-height: 1.5;">
              If this attempt was NOT made by you, your credentials may be at risk. We recommend changing your password and inspecting active devices from your Security Settings.
            </p>

            <div class="footer">
              ANOMATRIX Behavioral Biometrics & Zero Trust Engine &copy; 2026
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            if use_tls or smtp_port == 587:
                server.starttls()

        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_sender, [to_email], msg.as_string())
        server.quit()
        logger.info(f"[SECURITY EMAIL] Successfully sent alert email to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[SECURITY EMAIL] Failed to send security alert email: {e}")
        return False


