import sqlite3
import pandas as pd
import os

DB_NAME = "finance.db"
OUTPUT_XLSX = "report_finanziario.xlsx"
OUTPUT_CSV = "report_finanziario.csv"

def export_db():
    if not os.path.exists(DB_NAME):
        print("❌ Database non trovato.")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # Read transactions
    try:
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
        
        if df.empty:
            print("⚠️ Il database è vuoto.")
        else:
            df.to_excel(OUTPUT_XLSX, index=False)
            df.to_csv(OUTPUT_CSV, index=False)
            # Print Summary
            print("\n" + "="*30)
            print(" 💰 RIEPILOGO SPESE")
            print("="*30)
            print(f"TOTALE SPESO: {df['amount'].sum():.2f} €\n")
            
            print("PER CATEGORIA:")
            summary = df.groupby('category')['amount'].sum().sort_values(ascending=False)
            for cat, amount in summary.items():
                print(f"- {cat}: {amount:.2f} €")
            print("="*30 + "\n")
            
            print(f"✅ Export completato! File creati:\n- {OUTPUT_XLSX} (Excel)\n- {OUTPUT_CSV} (per Google Sheets)")
            print("\nEcco le ultime transazioni:\n")
            print(df.tail())
            
    except Exception as e:
        print(f"❌ Errore durante l'export: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    export_db()
