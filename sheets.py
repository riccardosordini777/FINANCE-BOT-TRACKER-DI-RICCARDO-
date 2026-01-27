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
    Organizes data by Month (Tab Name: "Mese YYYY", e.g., "Gennaio 2026")
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
        
        # Calculate Tab Name (Italian)
        now = datetime.now()
        months_it = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
            5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
            9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }
        tab_name = f"{months_it[now.month]} {now.year}"
        
        # Try to Select or Create Worksheet
        try:
            worksheet = sh.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            # Create new worksheet
            worksheet = sh.add_worksheet(title=tab_name, rows=100, cols=10)
            # Add Header
            worksheet.append_row(["Data", "Importo (€)", "Categoria", "Descrizione", "Tipo"])
            # Optional: Style header (bold) - requires more API calls, keeping it simple.

        # Append row: [Date, Amount, Category, Description, Type]
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([date_str, amount, category, description, type_])
        
        return True, f"Salvato su '{tab_name}'"

    except Exception as e:
        print(f"❌ Errore GSheets: {e}")
        return False, str(e)
