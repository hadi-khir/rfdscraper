#!/usr/bin/env python3
"""
Setup script for RFD Daily Deals application
This script helps you configure environment variables for the application.
"""

import os
import secrets
import string

def generate_secret_key(length=32):
    """Generate a secure secret key for Flask"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_env_file():
    """Create a .env file with user input"""
    
    print("🚀 RFD Daily Deals Setup")
    print("=" * 50)
    print("This script will help you configure your environment variables.")
    print("Press Enter to use default values (shown in brackets).\n")
    
    # Email configuration
    print("📧 Email Configuration:")
    email_sender = input("Gmail address [dailyrfd@gmail.com]: ").strip() or "dailyrfd@gmail.com"
    
    print("\n⚠️  IMPORTANT: You need to generate a Gmail App Password:")
    print("1. Go to your Google Account settings")
    print("2. Enable 2-factor authentication")
    print("3. Go to Security > App passwords")
    print("4. Generate a password for 'Mail'")
    print("5. Use that password below\n")
    
    email_password = input("Gmail App Password: ").strip()
    if not email_password:
        print("❌ Gmail App Password is required!")
        return False
    
    # Default recipients
    default_recipients = input("Default email recipients (comma-separated) [khir.hadi@gmail.com,Louaykhir@gmail.com]: ").strip()
    email_recipients = default_recipients or "khir.hadi@gmail.com,Louaykhir@gmail.com"
    
    # Flask configuration
    print("\n🔐 Flask Configuration:")
    flask_secret = input(f"Flask Secret Key [auto-generate]: ").strip()
    if not flask_secret:
        flask_secret = generate_secret_key()
        print(f"Generated secret key: {flask_secret[:20]}...")
    
    # Create .env file
    env_content = f"""# Email Configuration
EMAIL_SENDER={email_sender}
EMAIL_PASSWORD={email_password}
EMAIL_RECIPIENTS={email_recipients}

# Flask Configuration
FLASK_SECRET_KEY={flask_secret}

# Optional: Database Configuration
DATABASE_URL=sqlite:///subscribers.db

# Optional: Web App Configuration
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ Environment file created successfully!")
        print(f"📁 File: .env")
        print(f"🔒 Make sure to keep this file secure and never commit it to version control.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main setup function"""
    
    # Check if .env already exists
    if os.path.exists('.env'):
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    # Create .env file
    if create_env_file():
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the scraper: python scraper.py")
        print("3. Run the web app: python app.py")
        print("4. Visit: http://localhost:8080")
    else:
        print("\n❌ Setup failed. Please try again.")

if __name__ == "__main__":
    main()
