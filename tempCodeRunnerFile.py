import sqlite3

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # # Create table
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS users (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     username TEXT NOT NULL,
    #     email TEXT NOT NULL UNIQUE,
    #     password TEXT NOT NULL
    # )
    # ''')
    
    cursor.execute('DELETE FROM users')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
