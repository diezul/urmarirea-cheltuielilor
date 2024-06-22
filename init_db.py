import sqlite3

DATABASE = 'database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        DROP TABLE IF EXISTS expenses;
        ''')
        cursor.execute('''
        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            month TEXT NOT NULL,
            index_value INTEGER,
            amount REAL,
            is_paid BOOLEAN DEFAULT 0,
            UNIQUE(category, month)
        )
        ''')
        conn.commit()

if __name__ == '__main__':
    init_db()
