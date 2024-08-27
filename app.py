from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management and flash messages

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'Your email ID here replace this'
EMAIL_PASSWORD = 'your password is here'  # Use your App Password here

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

def generate_otp():
    otp = ''.join(random.choices(string.digits, k=6))
    return otp

def send_otp_email(email, otp):
    msg = MIMEMultipart()
    msg['From'] = 'TEST OTP'
    msg['To'] = email
    msg['Subject'] = 'Your OTP Code'

    body = f'Your OTP code is {otp}'
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route('/')
def home():
    if 'user' in session:
        return render_template('home.html', username=session['user'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        email = request.form['email']
        password = request.form['password']

        if not is_valid_username(username):
            flash('Username must start with an alphabet, be in lowercase, and be unique.', 'error')
        elif not is_valid_email(email):
            flash('Invalid email address. It should contain an @ symbol.', 'error')
        elif not is_valid_password(password):
            flash('Password must be at least 8 characters long.', 'error')
        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user_by_username = cursor.fetchone()

            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_by_email = cursor.fetchone()

            if user_by_username:
                flash('Username already exists. Please choose another one.', 'error')
            elif user_by_email:
                flash('Email already registered. Please choose another one.', 'error')
            else:
                otp = generate_otp()
                send_otp_email(email, otp)
                session['otp'] = otp
                session['otp_email'] = email
                session['username'] = username
                session['password'] = generate_password_hash(password, method='pbkdf2:sha256')
                return redirect(url_for('otp_verification'))

    return render_template('register.html')

@app.route('/otp_verification', methods=['GET', 'POST'])
def otp_verification():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (session['username'], session['otp_email'], session['password']))
            conn.commit()
            conn.close()
            flash('Account successfully created!', 'success')
            session.pop('otp', None)
            session.pop('otp_email', None)
            session.pop('username', None)
            session.pop('password', None)
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('otp_verification.html')

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
