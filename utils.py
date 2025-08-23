import os
import requests
import dateparser

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def send_message(to, body):
    """Send WhatsApp message using Cloud API"""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    requests.post(url, headers=headers, json=data)

def parse_reminder(text):
    """
    Very simple parser: looks for 'remind me to <task> at <time>'
    Example: 'Remind me to drink water in 10 minutes'
    """
    text = text.lower()
    if "remind me" in text:
        task_part = text.split("remind me to")[-1].strip()
        # crude split: if ' at ' exists
        if " at " in task_part:
            task, time_str = task_part.split(" at ", 1)
        else:
            task, time_str = task_part, task_part  # fallback
        dt = dateparser.parse(time_str)
        return task.strip(), dt
    return None, None
