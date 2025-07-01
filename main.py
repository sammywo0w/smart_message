from fastapi import FastAPI, Request, HTTPException
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
TEMPLATE_ID = os.getenv("MAILERSEND_TEMPLATE_ID")
FROM_EMAIL = os.getenv("MAILERSEND_FROM_EMAIL", "noreply@app.smartbuyer.co")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


@app.post("/incoming-message")
async def handle_incoming_message(request: Request):
    body = await request.json()
    record = body.get("record")

    if not record or "_id_read_user" not in record or "text" not in record:
        raise HTTPException(status_code=400, detail="Invalid Supabase webhook payload")

    user_id = record["_id_read_user"]
    message_text = record["text"]

    # Получаем email пользователя из user_data_bubble по _id
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    supa_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/user_data_bubble?select=email&_id=eq.{user_id}",
        headers=headers
    )

    if supa_resp.status_code != 200 or not supa_resp.json():
        raise HTTPException(status_code=404, detail="User not found")

    recipient_email = supa_resp.json()[0]["email"]

    # Формируем письмо
    payload = {
        "template_id": TEMPLATE_ID,
        "from": {
            "email": FROM_EMAIL,
            "name": "SmartBuyer"
        },
        "to": [{
            "email": recipient_email
        }],
        "personalization": [{
            "email": recipient_email,
            "data": {
                "senderName": "SmartBuyer Bot",
                "messageContent": message_text
            }
        }]
    }

    headers = {
        "Authorization": f"Bearer {MAILERSEND_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.mailersend.com/v1/email", json=payload, headers=headers)

    if response.status_code != 202:
        raise HTTPException(status_code=500, detail=f"MailerSend error: {response.text}")

    return {"status": "sent"}
