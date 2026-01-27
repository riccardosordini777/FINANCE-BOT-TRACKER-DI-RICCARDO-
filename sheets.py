import os
import json
import gspread
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_client():
    # 1. Try Loading from ENV (Render / Production) usually passed as string
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if creds_json_str:
        # If it is a file path that exists (Local dev using .env pointing to file)
        if os.path.isfile(creds_json_str):
             return gspread.service_account(filename=creds_json_str)
        
        # If it's the actual JSON content string (Render Env Var)
        try:
            creds_dict = json.loads(creds_json_str)
            return gspread.service_account_from_dict(creds_dict)
        except json.JSONDecodeError:
            pass # Not a valid JSON string, maybe just a partial path or undefined

    # 2. Fallback hardcoded check
    if os.path.exists("google_credentials.json"):
        return gspread.service_account(filename="google_credentials.json")
    
    return None

def save_to_sheet(amount, category, description, type_="expense"):
    """
    Appends a new transaction row to the configured Google Sheet.
    Row format: [Date, Amount, Category, Description, Type]
    """
    try:
        gc = get_client()
        if not gc:
            print("❌ Errore: Credenziali Google non trovate.")
            return False, "Credenziali mancanti"

        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        if not sheet_id:
             print("❌ Errore: GOOGLE_SHEETS_ID mancante.")
             return False, "Sheet ID mancante"

        # Open the spreadsheet
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0) # Open first tab

        # Check if header exists, if not create it (Optional, but good for UX)
        # Reading cell A1 requires an API call, we'll skip for speed or do it blindly.
        # Just appending.
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append row: [Date, Amount, Category, Description, Type]
        worksheet.append_row([now, amount, category, description, type_])
        
        return True, "Salvato su Sheets"

    except Exception as e:
        print(f"❌ Errore GSheets: {e}")
        return False, str(e)
