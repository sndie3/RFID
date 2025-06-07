import sqlite3
import hashlib
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('rfid_system.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        # Create admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create RFID cards table (updated with new fields)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rfid_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Student', 'Employee')),
                school_id TEXT,
                employee_id TEXT,
                phone_number TEXT,
                program TEXT NOT NULL,
                photo BLOB,
                status TEXT DEFAULT 'Active',
                registered_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create access log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create default admin if doesn't exist
        cursor.execute("SELECT COUNT(*) FROM admin")
        if cursor.fetchone()[0] == 0:
            default_password = self.hash_password("admin123")
            cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", 
                         ("admin", default_password))
        self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_admin(self, username, password):
        cursor = self.conn.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", 
                      (username, hashed_password))
        return cursor.fetchone() is not None
    
    def add_rfid_card(self, card_data):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO rfid_cards (card_id, first_name, last_name, role, school_id, 
                                      employee_id, phone_number, program, photo, registered_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', card_data)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_cards(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rfid_cards ORDER BY created_at DESC")
        return cursor.fetchall()
    
    def update_card_status(self, card_id, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE rfid_cards SET status = ? WHERE card_id = ?", 
                      (status, card_id))
        self.conn.commit()
    
    def get_card_by_id(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rfid_cards WHERE card_id = ?", (card_id,))
        return cursor.fetchone()
    
    def log_access(self, card_id, full_name, role, status):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO access_log (card_id, full_name, role, status, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        ''', (card_id, full_name, role, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
    
    def get_access_log(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM access_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def delete_card(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM rfid_cards WHERE card_id = ?", (card_id,))
        self.conn.commit()

    # ... (rest of the DatabaseManager methods) ... 