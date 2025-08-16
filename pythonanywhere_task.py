#!/usr/bin/env python3
"""
PythonAnywhere Task Scheduler Script
Run this script every 2 minutes via PythonAnywhere's task scheduler
"""

import os
import sys
import sqlite3
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# Configuration
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
NUM_DEALS = int(os.getenv('NUM_DEALS', 10))

def get_subscribers():
    """Get active subscribers from database"""
    try:
        db_path = os.path.join(SCRIPT_DIR, 'subscribers.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM subscribers WHERE is_active = 1')
        subscribers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return subscribers
    except Exception as e:
        print(f"Error getting subscribers: {e}")
        return []

def scrape_rfd_forum():
    """Scrape RedFlagDeals forum"""
    url = "https://forums.redflagdeals.com/hot-deals-f9/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        topic_items = soup.find_all('li', class_='topic')
        
        print(f"Found {len(topic_items)} topic items")
        
        scraped_data = []
        for item in topic_items:
            try:
                title_link = item.find('a', class_='thread_title_link')
                title = title_link.get_text(strip=True) if title_link else ''
                url = title_link.get('href') if title_link else ''
                
                if url and url.startswith('/'):
                    url = 'https://forums.redflagdeals.com' + url
                
                time_elements = item.find_all('time')
                created_at = ''
                if time_elements:
                    created_at = time_elements[0].get_text(strip=True)
                
                views_element = item.find('div', class_='views')
                rating = views_element.get_text(strip=True) if views_element else ''
                
                votes_element = item.find('div', class_='votes')
                votes_count = ''
                vote_type = ''
                
                if votes_element:
                    vote_span = votes_element.find('span')
                    if vote_span:
                        votes_count = vote_span.get_text(strip=True)
                    
                    thumbs_up = votes_element.find('use', href='#thumbs-up')
                    thumbs_down = votes_element.find('use', href='#thumbs-down')
                    
                    if thumbs_up:
                        vote_type = '👍'
                    elif thumbs_down:
                        vote_type = '👎'
                
                author_element = item.find('span', class_='author_name')
                author = author_element.get_text(strip=True) if author_element else ''
                
                topic_data = {
                    'title': title,
                    'url': url,
                    'created_at': created_at,
                    'rating': rating,
                    'votes': votes_count,
                    'vote_type': vote_type,
                    'author': author
                }
                
                scraped_data.append(topic_data)
                
            except Exception as e:
                print(f"Error processing item: {e}")
                continue
        
        return scraped_data
        
    except requests.exceptions.ProxyError as e:
        print(f"Proxy error: {e}")
        print("Please whitelist forums.redflagdeals.com in your PythonAnywhere web app settings")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def format_deals_email(deals_data):
    """Format deals data into HTML email"""
    if not deals_data:
        return "<p>No deals found today.</p>"
    
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .deal {{ 
                border: 1px solid #ddd; 
                margin: 10px 0; 
                padding: 15px; 
                border-radius: 5px;
                background-color: #f9f9f9;
            }}
            .deal-title {{ 
                font-size: 16px; 
                font-weight: bold; 
                color: #333; 
                margin-bottom: 5px;
            }}
            .deal-meta {{ 
                font-size: 12px; 
                color: #666; 
                margin-bottom: 10px;
            }}
            .deal-link {{ 
                color: #0066cc; 
                text-decoration: none;
            }}
            .header {{ 
                background-color: #e74c3c; 
                color: white; 
                padding: 15px; 
                border-radius: 5px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 Today's Top RedFlagDeals</h1>
            <p>Found {len(deals_data)} hot deals for you!</p>
        </div>
    """
    
    for i, deal in enumerate(deals_data[:NUM_DEALS], 1): 
        html_body += f"""
        <div class="deal">
            <div class="deal-title">{i}. {deal['title']}</div>
            <div class="deal-meta">
                👤 {deal['author']} | 📅 {deal['created_at']} | 👁️ {deal['rating']} | {deal['vote_type']} {deal['votes']}
            </div>
            <a href="{deal['url']}" class="deal-link" target="_blank">View Deal →</a>
        </div>
        """
    
    html_body += """
        <p style="margin-top: 20px; font-size: 12px; color: #666;">
            Powered by RFD Scraper | <a href="https://forums.redflagdeals.com/hot-deals-f9/" target="_blank">View All Deals</a>
        </p>
    </body>
    </html>
    """
    
    return html_body

def send_email(subject, body, sender, recipients, password):
    """Send email to recipients"""
    try:
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = sender  # Set To field to sender to avoid showing recipients
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
           smtp_server.login(sender, password)
           smtp_server.sendmail(sender, recipients, msg.as_string())
        
        print(f"Email sent successfully to {len(recipients)} recipients")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    """Main function to run the task"""
    try:
        # Get current time in Eastern Time
        eastern_tz = pytz.timezone('US/Eastern')
        now_eastern = datetime.now(eastern_tz)
        
        print(f"=== Task started at {now_eastern.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
        
        # Check if we have email credentials
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            print("ERROR: Email credentials not configured. Please set EMAIL_SENDER and EMAIL_PASSWORD in .env file")
            return
        
        # Get subscribers
        subscribers = get_subscribers()
        if not subscribers:
            print("No active subscribers found")
            return
        
        print(f"Found {len(subscribers)} active subscribers")
        
        # Scrape deals
        print("Scraping RedFlagDeals...")
        deals = scrape_rfd_forum()
        
        if deals:
            print(f"Found {len(deals)} deals")
            
            # Format and send email
            email_body = format_deals_email(deals)
            success = send_email(
                "Today's Top Deals",
                email_body,
                EMAIL_SENDER,
                subscribers,
                EMAIL_PASSWORD
            )
            
            if success:
                print("Task completed successfully")
            else:
                print("Task failed - email sending error")
        else:
            print("No deals found to send")
            
    except Exception as e:
        print(f"Task failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
