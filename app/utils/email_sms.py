from flask import current_app
from flask_mail import Message

def send_email(to_email: str, subject: str, body: str):
    """
    Send email using Flask-Mail configuration.
    Falls back to console logging if mail is not configured.
    """
    try:
        mail = current_app.extensions.get('mail')
        if mail is None:
            print(f"[EMAIL - NOT CONFIGURED] To: {to_email} | Subject: {subject} | Body: {body[:120]}")
            return False
            
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        mail.send(msg)
        print(f"[EMAIL - SENT] To: {to_email} | Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"[EMAIL - ERROR] Failed to send to {to_email}: {str(e)}")
        print(f"[EMAIL - FALLBACK] To: {to_email} | Subject: {subject} | Body: {body[:120]}")
        return False

def send_sms(to_phone: str, body: str):
    """
    Send SMS using configured provider.
    Currently a placeholder - integrate with Twilio or similar service.
    """
    print(f"[SMS] To: {to_phone} | Body: {body[:120]}")
