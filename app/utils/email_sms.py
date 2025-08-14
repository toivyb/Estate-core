import os

def send_email(to_email: str, subject: str, body: str):
    # Placeholder: plug in your SMTP provider or service SDK
    print(f"[EMAIL] To: {to_email} | Subject: {subject} | Body: {body[:120]}")

def send_sms(to_phone: str, body: str):
    # Placeholder: plug in Twilio or equivalent
    print(f"[SMS] To: {to_phone} | Body: {body[:120]}")
