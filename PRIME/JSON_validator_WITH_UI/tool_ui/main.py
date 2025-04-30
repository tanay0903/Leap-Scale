import subprocess
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
import signal
import threading
from flask import Flask, render_template, request, jsonify
import json
from tool import validateData
from dotenv import load_dotenv
import sys


load_dotenv()

# === Email Configuration ===
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_SUBJECT = 'Flask App Crashed!'
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
LOG_FILE = 'json_validator_logfile.log'

# === Flask App Setup ===
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    try:
        json_data = request.get_json()
        raw_data = json.dumps(json_data, indent=4)
        result = validateData(json_data, raw_data)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"result": f"Error: {str(e)}"})

# === Simulate Crash after N seconds ===
def simulate_crash():
    time.sleep(120) 
    print("⚠️ Simulated crash triggered.")
    os.kill(os.getpid(), signal.SIGINT)

# === Logging and Email ===
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

# === Watchdog Function ===
def run_watchdog():
    try:
        while True:
            print("▶️  Starting Flask app...")
            process = subprocess.Popen(
                ["python", __file__, "--child"],
                cwd=os.getcwd()
            )
            process.wait()
            exit_code = process.returncode

            if exit_code == 0:
                print("✅ Flask exited cleanly. Not restarting.")
                break

            crash_msg = f"Flask app crashed with exit code {exit_code}"
            print(crash_msg)
            log_crash(crash_msg)
            send_email(crash_msg)

            # ✅ If child exited cleanly (Ctrl+C), don't restart
            if exit_code == 0:
                print("✅ Flask exited cleanly. Not restarting.")
                break

            print("🔁 Automatically restarting Flask app in 60 seconds...\n")
            time.sleep(60)

    except KeyboardInterrupt:
        print("🛑 Watchdog interrupted by user.")
    finally:
        print("✅ Watchdog exited cleanly.")


# === Watchdog Function ===
# def run_watchdog():
#     while True:
#         print("▶️  Starting Flask app...")
#         process = subprocess.Popen(
#             ["python", __file__, "--child"],
#             cwd=os.getcwd()
#         )
#         process.wait()

#         crash_msg = f"Flask app crashed with exit code {process.returncode}"
#         print(crash_msg)
#         log_crash(crash_msg)
#         send_email(crash_msg)

#         print("🔁 Automatically restarting Flask app in 2 seconds...\n")
#         time.sleep(60)

# === Flask Child Mode ===
def run_flask_child():
    def handle_sigint(signum, frame):
        print("🛑 Flask child received Ctrl+C. Exiting cleanly...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # Start simulated crash thread
    threading.Thread(target=simulate_crash, daemon=True).start()
    app.run(debug=True, use_reloader=False)

# === Main Entry ===
if __name__ == '__main__':
    if '--child' in sys.argv:
        run_flask_child()
    else:
        run_watchdog()