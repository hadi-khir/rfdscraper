import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

num_deals = int(os.getenv('NUM_DEALS', 10))

subject = "Today's Top Deals"


def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender  # Set To field to sender to avoid showing recipients
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       # Send to BCC recipients (they won't see each other's email addresses)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

def format_deals_email(deals_data):
    """Format the scraped deals data into an HTML email body"""
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
            .deal-link:hover {{ 
                text-decoration: underline;
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
    
    for i, deal in enumerate(deals_data[:num_deals], 1): 
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

def scrape_rfd_forum():
    url = "https://forums.redflagdeals.com/hot-deals-f9/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Add timeout and retry logic for PythonAnywhere
        session = requests.Session()
        session.headers.update(headers)
        
        # Try with different timeout settings
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
                updated_at = ''
                
                if time_elements:
                    created_at = time_elements[0].get_text(strip=True)
                    if len(time_elements) > 1:
                        updated_at = time_elements[-1].get_text(strip=True)
                    else:
                        updated_at = created_at
                
                views_element = item.find('div', class_='views')
                rating = views_element.get_text(strip=True) if views_element else ''
                
                # Extract voting information
                votes_element = item.find('div', class_='votes')
                votes_count = ''
                vote_type = ''
                
                if votes_element:
                    # Get the vote count
                    vote_span = votes_element.find('span')
                    if vote_span:
                        votes_count = vote_span.get_text(strip=True)
                    
                    # Determine if it's thumbs up or down
                    thumbs_up = votes_element.find('use', href='#thumbs-up')
                    thumbs_down = votes_element.find('use', href='#thumbs-down')
                    
                    if thumbs_up:
                        vote_type = '👍'
                    elif thumbs_down:
                        vote_type = '👎'
                
                # Extract author information
                author_element = item.find('span', class_='author_name')
                author = author_element.get_text(strip=True) if author_element else ''
                
                # Extract thread ID
                thread_id = item.get('data-thread-id', '')
                
                topic_data = {
                    'title': title,
                    'url': url,
                    'created_at': created_at,
                    'updated_at': updated_at,
                    'rating': rating,
                    'votes': votes_count,
                    'vote_type': vote_type,
                    'author': author,
                    'thread_id': thread_id
                }
                
                scraped_data.append(topic_data)
                
            except Exception as e:
                print(f"Error processing item: {e}")
                continue
        
        return scraped_data
        
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []

def main():
    print("Scraping RedFlagDeals forum...")
    data = scrape_rfd_forum()
    
    if data:
        print(f"Successfully scraped {len(data)} topics:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Save to file
        with open('rfd_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\nData saved to rfd_data.json")
        
        # Send email with scraped deals
        print("\nSending email with deals...")
        email_body = format_deals_email(data)
        send_email(subject, email_body, sender, recipients, password)
        
    else:
        print("No data was scraped.")

