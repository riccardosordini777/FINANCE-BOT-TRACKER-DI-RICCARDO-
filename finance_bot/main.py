import os
import logging
from flask import Flask, request
from dotenv import load_dotenv
from services import process_twilio_message

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Twilio Finance Bot Running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Twilio sends data as application/x-www-form-urlencoded
    """
    form_data = request.form
    logger.info(f"Incoming Twilio Msg from {form_data.get('From')}")
    
    try:
        process_twilio_message(form_data)
    except Exception as e:
        logger.error(f"Error: {e}")
        
    # Twilio expects XML response or empty 200 OK
    return str("<Response></Response>"), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
