import os
import logging
import json
import uuid
import database
from utils import send_whatsapp_message, download_media
from sheets import save_to_sheet
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_gemini_model():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def process_twilio_message(form_data):
    """
    Handles incoming Twilio webhook (Form Data).
    """
    from_number = form_data.get('From')
    body_text = form_data.get('Body', '')
    num_media = int(form_data.get('NumMedia', 0))
    
    database.init_db()

    # 1. Handle Audio / Voice Note
    if num_media > 0:
        media_type = form_data.get('MediaContentType0', '')
        if 'audio' in media_type:
            media_url = form_data.get('MediaUrl0')
            handle_audio_message(from_number, media_url)
            return
        else:
             send_whatsapp_message(from_number, "Mandami un audio o del testo.")
             return

    # 2. Handle Text
    if body_text:
        handle_text_message(from_number, body_text)

def handle_text_message(user_id, text):
    if text.strip() == "/stats" or "stat" in text.lower():
        stats = database.get_user_stats(user_id)
        report = f"📊 *Report Finanziario*\n\n💰 Totale: {stats['total']:.2f}€\n\n📂 *Dettaglio:*"
        for cat in stats['categories']:
            report += f"\n- {cat['category']}: {cat['total']:.2f}€"
        send_whatsapp_message(user_id, report)
        return

    process_transaction_with_llm(user_id, text)

def handle_audio_message(user_id, media_url):
    send_whatsapp_message(user_id, "🎧 Ascolto...")
    
    filename = f"temp_{uuid.uuid4()}.ogg"
    if not download_media(media_url, filename):
        send_whatsapp_message(user_id, "❌ Errore download audio.")
        return

    try:
        model = get_gemini_model()
        myfile = genai.upload_file(filename)
        
        prompt = """
        Ascolta questo audio e identifica TUTTE le spese menzionate.
        Restituisci una LISTA JSON:
        [
            {
                "amount": numero,
                "category": stringa,
                "description": stringa,
                "type": "expense" o "income"
            },
            ...
        ]
        """
        result = model.generate_content([myfile, prompt])
        
        os.remove(filename)
        parse_and_save_transaction(user_id, result.text)

    except Exception as e:
        logger.error(f"Audio Error: {e}")
        send_whatsapp_message(user_id, f"❌ Errore AI: {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)

def process_transaction_with_llm(user_id, text):
    model = get_gemini_model()
    prompt = f"""
    Analizza testo: "{text}"
    Estrai JSON LIST (array di oggetti):
    [
        {{
            "amount": numero,
            "category": stringa,
            "description": stringa,
            "type": "expense"
        }},
        ...
    ]
    """
    try:
        result = model.generate_content(prompt)
        parse_and_save_transaction(user_id, result.text)
    except Exception as e:
        send_whatsapp_message(user_id, "❌ Errore AI.")

def parse_and_save_transaction(user_id, json_text):
    try:
        clean_text = json_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Normalize to list
        if isinstance(data, dict):
            data = [data]
            
        if not isinstance(data, list):
             send_whatsapp_message(user_id, "❌ Errore formato AI.")
             return

        final_msg = ""
        
        for item in data:
            if "error" in item:
                continue

            amount = float(item.get("amount", 0))
            cat = item.get("category", "Altro")
            desc = item.get("description", "")
            tx_type = item.get("type", "expense")
            
            database.add_transaction(user_id, amount, cat, desc, json.dumps(item))

            # Save to Google Sheets
            saved_sheet, _ = save_to_sheet(amount, cat, desc, tx_type)
            
            icon = "✅" if saved_sheet else "⚠️"
            final_msg += f"{icon} {amount}€ ({cat}) - {desc}\n"

        if not final_msg:
            send_whatsapp_message(user_id, "❌ Nessuna transazione trovata.")
        else:
            send_whatsapp_message(user_id, final_msg)
        
    except Exception as e:
        logger.error(f"Parse Error: {e}")
        send_whatsapp_message(user_id, "❌ Errore elaborazione.")
