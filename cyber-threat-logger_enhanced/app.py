from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import requests
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

LOG_FILE = "logs.txt"
BLACKLIST_FILE = "blacklist.txt"

# ✅ Email Configuration (Use Gmail App Password here)
EMAIL_ENABLED = True
EMAIL_SENDER = "ishfaqalpha14@gmail.com"
EMAIL_PASSWORD = "llbdgpqgkwlkqocw"  # Replace this with App Password
EMAIL_RECEIVER = "ishfaqahmadw9@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(subject, body):
    if not EMAIL_ENABLED:
        return
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    except Exception as e:
        print("Email failed:", e)

def get_geo_data(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        return response.json()
    except:
        return {}

def is_blacklisted(ip):
    if not os.path.exists(BLACKLIST_FILE):
        return False
    with open(BLACKLIST_FILE, 'r') as f:
        return ip in f.read()

@app.route('/')
def index():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if is_blacklisted(ip):
        return "Access denied."

    user_agent = request.headers.get('User-Agent')
    referrer = request.referrer
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    geo_data = get_geo_data(ip)
    city = geo_data.get("city", "N/A")
    region = geo_data.get("regionName", "N/A")
    country = geo_data.get("country", "N/A")
    isp = geo_data.get("isp", "N/A")

    log_entry = (
        f"Time: {timestamp}\n"
        f"IP: {ip}\n"
        f"City: {city}\nRegion: {region}\nCountry: {country}\nISP: {isp}\n"
        f"User-Agent: {user_agent}\nReferrer: {referrer}\n{'-'*60}\n"
    )

    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

    send_email("🚨 New Visit Logged", log_entry)
    return render_template('index.html')

@app.route('/logs')
def show_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            data = f.read()
        return f"<pre>{data}</pre>"
    return "No logs found."

@app.route('/blacklist/<ip>')
def blacklist_ip(ip):
    with open(BLACKLIST_FILE, 'a') as f:
        f.write(ip + "\n")
    return f"IP {ip} blacklisted."

@app.route('/dashboard')
def dashboard():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            logs = f.readlines()
    else:
        logs = []

    log_count = len([line for line in logs if line.startswith("Time: ")])
    return render_template('dashboard.html', count=log_count, logs=logs[-100:])

if __name__ == '__main__':
    app.run(debug=True)
