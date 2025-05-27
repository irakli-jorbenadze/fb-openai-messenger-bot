import os
from openai import OpenAI
import requests
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request

app = Flask(__name__)

# Retrieve environment variables
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_TOKEN = os.environ.get("PAGE_TOKEN")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def send_message(recipient_id, text):
    """Send a response back to the Facebook user."""
    params = {"access_token": PAGE_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    response = requests.post(
        "https://graph.facebook.com/v18.0/me/messages",
        params=params,
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code} - {response.text}")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Webhook verification
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        mode = request.args.get("hub.mode")
        if token == VERIFY_TOKEN and mode == "subscribe":
            return challenge, 200
        return "Verification token mismatch", 403

    elif request.method == "POST":
        # Handle incoming messages
        payload = request.get_json()
        for entry in payload.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    user_message = messaging_event["message"]["text"]

                    # Generate response using OpenAI
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": user_message}]
                        )
                        reply = response.choices[0].message.content.strip()
                    except Exception as e:
                        print(f"OpenAI API error: {e}")
                        reply = "I'm sorry, I'm having trouble processing your request right now."

                    send_message(sender_id, reply)
        return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Flask app is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
