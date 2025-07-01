from fastapi import FastAPI, Request, HTTPException
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
TEMPLATE_ID = os.getenv("MAILERSEND_TEMPLATE_ID")

@app.post("/incoming-message")
async def handle_incoming_message(request: Request):
    body = await request.json()

    # Ожидаемые поля от Supabase/Bubble:
    sender_name = body.get("sender_name")
    message_text = body.get("message_text")
    recipient_email = body.get("recipient_email")

    if not all([sender_name, message_text, recipient_email]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    payload = {
        "template_id": TEMPLATE_ID,
        "to": [{"email": recipient_email}],
        "variables": [
            {"var": "senderName", "value": sender_name},
            {"var": "messageContent", "value": message_text}
        ]
    }

    headers = {
        "Authorization": f"Bearer {MAILERSEND_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.mailersend.com/v1/email", json=payload, headers=headers)

    if response.status_code != 202:
        raise HTTPException(status_code=500, detail=f"MailerSend error: {response.text}")

    return {"status": "sent"}
