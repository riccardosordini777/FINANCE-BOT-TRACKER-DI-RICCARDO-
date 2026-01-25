import sqlite3
import datetime
import os

DB_NAME = "finance.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Create transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            category TEXT,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_transaction(user_id, amount, category, description, raw_text=""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO transactions (user_id, amount, category, description, raw_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, amount, category, description, raw_text))
    conn.commit()
    tx_id = c.lastrowid
    conn.close()
    return tx_id

def get_user_stats(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Total spent
    c.execute('SELECT SUM(amount) as total FROM transactions WHERE user_id = ?', (user_id,))
    total = c.fetchone()['total'] or 0.0
    
    # By Category
    c.execute('''
        SELECT category, SUM(amount) as total 
        FROM transactions 
        WHERE user_id = ? 
        GROUP BY category 
        ORDER BY total DESC
    ''', (user_id,))
    categories = [{"category": row['category'], "total": row['total']} for row in c.fetchall()]
    
    conn.close()
    return {"total": total, "categories": categories}
