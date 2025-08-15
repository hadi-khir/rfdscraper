# RFD Daily Deals - Web Application

A modern web application that scrapes the best deals from RedFlagDeals.com and sends them to subscribers via email daily.

## 🚀 Features

- **Beautiful Web Interface**: Modern, responsive design with Bootstrap 5
- **Email Subscription System**: Users can subscribe/unsubscribe via web form
- **Daily Automated Emails**: Sends top 25 deals every morning at 9 AM
- **Community Ratings**: Shows thumbs up/down votes for each deal
- **Admin Panel**: Manage subscribers and send test emails
- **SQLite Database**: Stores subscriber information locally
- **BCC Email Sending**: Protects subscriber privacy

## 📋 Requirements

- Python 3.7+
- Gmail account with App Password
- Internet connection

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rfd-scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   
   **Option A: Use the setup script (Recommended)**:
   ```bash
   python setup.py
   ```
   This will guide you through creating a `.env` file with your credentials.
   
   **Option B: Manual setup**:
   ```bash
   cp env.example .env
   ```
   Then edit `.env` with your actual credentials.

4. **Generate Gmail App Password**:
   - Go to Google Account settings
   - Enable 2-factor authentication
   - Generate an App Password for "Mail"
   - Use this password in your `.env` file

## 🚀 Usage

### Running the Web Application

1. **Start the Flask app**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   - Main page: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

### Running the Scraper Only

If you just want to run the scraper without the web interface:

```bash
python scraper.py
```

## 📧 Email Features

### Daily Email Content
- **Top 30 deals** from RedFlagDeals.com
- **Deal titles** with direct links
- **Author information** and timestamps
- **View counts** and community ratings
- **Thumbs up/down** voting data
- **Beautiful HTML formatting**

### Email Schedule
- **Automatic sending**: Every day at 9:00 AM
- **Manual test**: Available in admin panel
- **BCC delivery**: Protects subscriber privacy

## 🎨 Web Interface

### Main Page (`/`)
- **Subscribe form**: Users can enter their email
- **Unsubscribe form**: Easy way to opt out
- **Feature showcase**: Explains the service benefits
- **Responsive design**: Works on mobile and desktop

### Admin Panel (`/admin`)
- **Subscriber management**: View all subscribers
- **Test email sending**: Send immediate test emails
- **Statistics**: View subscriber count and settings
- **Quick actions**: Remove subscribers, refresh data

## 🗄️ Database

The application uses SQLite to store subscriber information:

```sql
CREATE TABLE subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

## 🔧 Configuration

### Environment Variables

The application uses environment variables for sensitive configuration. Create a `.env` file in the project root:

```bash
# Email Configuration
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_RECIPIENTS=email1@example.com,email2@example.com

# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-flask-key

# Optional: Database Configuration
DATABASE_URL=sqlite:///subscribers.db

# Optional: Web App Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Email Settings
- **SMTP Server**: Gmail (smtp.gmail.com:465)
- **Authentication**: Gmail App Password
- **From Address**: Your Gmail address
- **BCC Delivery**: All recipients are BCC'd

### Scraping Settings
- **Source**: RedFlagDeals.com Hot Deals forum
- **Deals per email**: 25 (configurable)
- **Data extracted**: Title, URL, author, timestamps, votes, views

### Web App Settings
- **Port**: 5000 (configurable)
- **Host**: 0.0.0.0 (accessible from network)
- **Debug mode**: Enabled for development

## 🛡️ Privacy & Security

- **BCC emails**: Recipients can't see each other's addresses
- **No data sharing**: All data stays on your server
- **Easy unsubscribe**: One-click unsubscribe option
- **Secure storage**: SQLite database with proper indexing

## 🔄 Automation

The application includes a background task that:
- **Runs continuously** while the app is running
- **Checks time** every minute
- **Sends emails** at 9:00 AM daily
- **Handles errors** gracefully with retry logic

## 📱 Mobile Support

The web interface is fully responsive and works on:
- **Desktop computers**
- **Tablets**
- **Mobile phones**
- **All modern browsers**

## 🚨 Troubleshooting

### Common Issues

1. **Email not sending**:
   - Check Gmail App Password
   - Verify 2-factor authentication is enabled
   - Check internet connection

2. **No deals found**:
   - RedFlagDeals.com might be down
   - HTML structure might have changed
   - Check the debug output

3. **Web app not starting**:
   - Check if port 5000 is available
   - Verify all dependencies are installed
   - Check Python version (3.7+)

### Debug Mode

The application runs in debug mode by default, showing:
- Detailed error messages
- Request/response logs
- Database operations

## 📈 Future Enhancements

Potential improvements:
- **Email templates**: More customization options
- **Deal categories**: Filter by deal type
- **User preferences**: Customize email frequency
- **Analytics**: Track open rates and clicks
- **API endpoints**: REST API for integrations
- **Docker support**: Containerized deployment

## 📄 License

This project is for educational and personal use. Please respect RedFlagDeals.com's terms of service.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Note**: This application scrapes publicly available data from RedFlagDeals.com. Please ensure compliance with their terms of service and implement appropriate rate limiting.
