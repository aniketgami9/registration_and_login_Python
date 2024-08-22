from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management and flash messages

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Validate username
def is_valid_username(username):
    if not username or not username[0].isalpha() or not username.islower():
        return False
    return True

# Validate email
def is_valid_email(email):
    return '@' in email

# Validate password
def is_valid_password(password):
    return len(password) >= 8

@app.route('/')
def home():
    if 'user' in session:
        return render_template('home.html', username=session['user'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()  # Convert username to lowercase
        email = request.form['email']
        password = request.form['password']

        # Validate input
        if not is_valid_username(username):
            flash('Username must start with an alphabet, be in lowercase, and be unique.', 'error')
        elif not is_valid_email(email):
            flash('Invalid email address. It should contain an @ symbol.', 'error')
        elif not is_valid_password(password):
            flash('Password must be at least 8 characters long.', 'error')
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user_by_username = cursor.fetchone()
            
            # Check if email already exists
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_by_email = cursor.fetchone()
            
            if user_by_username:
                flash('Username already exists. Please choose another one.', 'error')
            elif user_by_email:
                flash('Email already registered. Please choose another one.', 'error')
            else:
                try:
                    conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                                 (username, email, generate_password_hash(password, method='pbkdf2:sha256')))
                    conn.commit()
                    flash('Account successfully created!', 'success')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    flash('An unexpected error occurred. Please try again.', 'error')
                finally:
                    conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not is_valid_email(email):
            flash('Invalid email address. It should contain an @ symbol.', 'error')
        elif not is_valid_password(password):
            flash('Password must be at least 8 characters long.', 'error')
        else:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()

            if user is None:
                flash('User not registered. Please check your email or register.', 'error')
            elif check_password_hash(user['password'], password):
                session['user'] = user['username']
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
