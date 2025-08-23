from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
app = Flask(__name__)
load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

def parse_reminder(text):
    """
    Parses user input like 'Remind me to drink water in 2 minutes'
    Returns (task, datetime) or (None, None)
    """
    text_lower = text.lower()
    if text_lower.startswith("remind me"):
        # Extract after "remind me to"
        try:
            parts = text_lower.split(" to ", 1)
            if len(parts) == 2:
                task_part = parts[1]
                # Split time keyword if present
                for keyword in [" in ", " at ", " on ", " after "]:
                    if keyword in task_part:
                        task, time_part = task_part.split(keyword, 1)
                        dt = dateparser.parse(time_part, settings={"PREFER_DATES_FROM": "future"})
                        return task.strip(), dt
        except Exception as e:
            print("⚠️ Parsing error:", e)
    return None, None

# --- Routes ---
@app.route("/webhook", methods=["GET"])
def verify():
    """
    Webhook verification (Meta will call this once)
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return challenge, 200
    else:
        return "❌ Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Handles incoming WhatsApp messages
    """
    data = request.get_json()
    print("📩 Incoming:", data)

    if data.get("entry"):
        try:
            msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
            sender = msg["from"]  # phone number
            text = msg["text"]["body"]

            # Try parsing as reminder
            task, dt = parse_reminder(text)

            if task and dt:
                send_message(sender, f"✅ Got it! I’ll remind you to '{task}' at {dt.strftime('%H:%M:%S')}.")
                scheduler.add_job(
                    send_message,
                    "date",
                    run_date=dt,
                    args=[sender, f"⏰ Reminder: {task}"]
                )
            else:
                send_message(sender, f"Got it: {text}")

        except Exception as e:
            print("⚠️ Error handling webhook:", e)

    return "EVENT_RECEIVED", 200

import requests
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
load_dotenv()
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# --- Utils ---
def send_message(to, body):
    """
    Sends a WhatsApp message using Cloud API
    """
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print("❌ Error sending message:", response.text)
    else:
        print("✅ Message sent:", body)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
