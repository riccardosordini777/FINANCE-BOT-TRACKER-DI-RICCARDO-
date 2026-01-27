import os
import requests
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

def get_twilio_client():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        # Avoid crashing if env vars not set yet
        return None
    return Client(account_sid, auth_token)

def send_whatsapp_message(to_number, text_body):
    """
    Sends a text message via Twilio WhatsApp API.
    """
    client = get_twilio_client()
    if not client:
        logger.error("Twilio credentials missing")
        return

    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    
    try:
        # Truncate message to avoid Twilio 1600 limit (HTTP 400)
        if len(text_body) > 1500:
            text_body = text_body[:1500] + "... (troncato)"

        message = client.messages.create(
            from_=from_number,
            body=text_body,
            to=to_number
        )
        logger.info(f"Message sent to {to_number}: {message.sid}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

def download_media(media_url, save_path):
    """
    Downloads media from Twilio URL (requires Auth).
    """
    # Twilio media URLs often require Basic Auth with Account SID & Token
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    response = requests.get(media_url, auth=(account_sid, auth_token))
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    
    logger.error(f"Failed to download media: {response.status_code}")
    return False
