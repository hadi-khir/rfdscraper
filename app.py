from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import sqlite3
import os
from datetime import datetime
import pytz
from scraper import scrape_rfd_forum, send_email, format_deals_email
from dotenv import load_dotenv
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = (
    os.getenv('FLASK_SECRET_KEY')
)


EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subscribers.db')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def add_subscriber(email):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First check if the email already exists
        cursor.execute('SELECT is_active FROM subscribers WHERE email = ?', (email,))
        result = cursor.fetchone()
        
        if result:
            # Email exists, check if it's inactive
            if result[0] == 0:
                # Reactivate the subscriber
                cursor.execute('UPDATE subscribers SET is_active = 1 WHERE email = ?', (email,))
                conn.commit()
                conn.close()
                return True, "reactivated"
            else:
                # Already active
                conn.close()
                return False, "already_active"
        else:
            # New email, insert it
            cursor.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()
            conn.close()
            return True, "new"
            
    except sqlite3.IntegrityError:
        return False, "error"

def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM subscribers WHERE is_active = 1')
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers

def get_inactive_subscribers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM subscribers WHERE is_active = 0')
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers

def remove_subscriber(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE subscribers SET is_active = 0 WHERE email = ?', (email,))
    conn.commit()
    conn.close()


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get('logged_in'):
            next_url = request.path
            return redirect(url_for('login', next=next_url))
        return view_func(*args, **kwargs)
    return wrapped_view

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    
    if not email or '@' not in email:
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('index'))
    
    success, status = add_subscriber(email)
    
    if success:
        if status == "new":
            flash('Successfully subscribed! You\'ll receive daily deals starting tomorrow.', 'success')
        elif status == "reactivated":
            flash('Welcome back! Your subscription has been reactivated.', 'success')
    else:
        if status == "already_active":
            flash('This email is already subscribed.', 'info')
        else:
            flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form.get('email')
    
    if email:
        remove_subscriber(email)
        flash('Successfully unsubscribed. You won\'t receive any more emails.', 'success')
    
    return redirect(url_for('index'))

@app.route('/reactivate', methods=['POST'])
def reactivate():
    email = request.form.get('email')
    add_subscriber(email)
    return redirect(url_for('admin'))

@app.route('/admin')
@login_required
def admin():
    subscribers = get_all_subscribers()
    inactive_subscribers = get_inactive_subscribers()
    return render_template('admin.html', subscribers=subscribers, inactive_subscribers=inactive_subscribers, count=len(subscribers))

@app.route('/send-test', methods=['POST'])
@login_required
def send_test():
    try:
        # Scrape current deals
        deals = scrape_rfd_forum()
        
        if deals:
            # Get all subscribers
            subscribers = get_all_subscribers()
            
            if subscribers:
                # Send email to all subscribers
                email_body = format_deals_email(deals)
                send_email(
                    "Today's Top Deals - Test",
                    email_body,
                    EMAIL_SENDER,
                    subscribers,
                    EMAIL_PASSWORD
                )
                flash(f'Test email sent to {len(subscribers)} subscribers!', 'success')
            else:
                flash('No subscribers found.', 'error')
        else:
            flash('No deals found to send.', 'error')
            
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')
    
    return redirect(url_for('admin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or url_for('admin')
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        next_post = request.form.get('next') or url_for('admin')

        if not ADMIN_USERNAME or not ADMIN_PASSWORD:
            flash('Admin credentials are not configured on the server.', 'error')
            return redirect(url_for('login', next=next_post))

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(next_post)
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login', next=next_post))

    return render_template('login.html', next_url=next_url)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def send_deals_email():
    """Background task to send deals emails"""
    try:
        eastern_tz = pytz.timezone('US/Eastern')
        now_eastern = datetime.now(eastern_tz)
        
        deals = scrape_rfd_forum()
        if deals:
            subscribers = get_all_subscribers()
            if subscribers:
                email_body = format_deals_email(deals)
                send_email(
                    "Today's Top Deals",
                    email_body,
                    EMAIL_SENDER,
                    subscribers,
                    EMAIL_PASSWORD
                )
                print(f"Daily email sent to {len(subscribers)} subscribers at {now_eastern.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                print("No subscribers found for daily email")
        else:
            print("No deals found for daily email")
            
    except Exception as e:
        print(f"Error in daily email task: {e}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
