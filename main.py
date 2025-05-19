import os
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_TOKEN = os.environ.get("PAGE_TOKEN")
openai.api_key = os.environ.get("OPENAI_API_KEY")


def send_message(recipient_id, text):
    """Send response back to Facebook user"""
    params = {"access_token": PAGE_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post("https://graph.facebook.com/v18.0/me/messages",
                  params=params, headers=headers, json=data)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verification
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Verification token mismatch", 403

    if request.method == "POST":
        payload = request.json
        for event in payload.get("entry", []):
            for messaging in event.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                if "message" in messaging and "text" in messaging["message"]:
                    user_msg = messaging["message"]["text"]

                    # Send message to OpenAI
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "user", "content": user_msg}
                        ]
                    )
                    reply = response.choices[0].message.content.strip()
                    send_message(sender_id, reply)
        return "OK", 200
