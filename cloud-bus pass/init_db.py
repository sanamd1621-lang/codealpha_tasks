import sqlite3

def create_tables():
    # Connects to database.db (creates it if it doesn't exist)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')

    # 2. Bus Passes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pass_type TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            start_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            photo TEXT,
            status TEXT DEFAULT 'Pending',
            qr_code TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database 'database.db' created and tables initialized successfully!")

if __name__ == '__main__':
    create_tables()