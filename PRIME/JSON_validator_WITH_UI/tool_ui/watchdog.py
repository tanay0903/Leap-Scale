import subprocess
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_SUBJECT = 'Flask App Crashed!'
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
LOG_FILE = r'D:\Leap and scale\project\json_validator_logfile.log'

def send_email(message_body):
    msg = MIMEText(message_body)
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ Crash email sent.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def log_crash(message):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{datetime.now()}: {message}\n")

# 🔁 Watchdog loop
while True:
    print("▶️  Starting Flask app...")
    process = subprocess.Popen(
        ["C:\\Users\\tanay\\AppData\\Local\\Programs\\Python\\Python313\\python.exe", "app.py"],  # Use full path if needed
        cwd=r"D:\Leap and scale\project\prime\JSON_validator_WITH_UI\tool_ui"
    )
    
    process.wait()

    crash_msg = f"Flask app crashed with exit code {process.returncode}"
    print(crash_msg)
    log_crash(crash_msg)
    send_email(crash_msg)

    time.sleep(2)
    print("🔁 Restarting Flask app...")
