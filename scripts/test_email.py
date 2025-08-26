#!/usr/bin/env python3
"""
Test script for email functionality
"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, backend_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(backend_root, '.env'))
except ImportError:
    print("Warning: python-dotenv not installed")

from estatecore_backend import create_app
from estatecore_backend.app.utils.email_sms import send_email

def test_email_configuration():
    """Test email configuration and sending"""
    
    print("Testing Email Functionality")
    print("=" * 50)
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER', 'Not configured')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT', 'Not configured')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS', 'Not configured')}")
        print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME', 'Not configured')}")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER', 'Not configured')}")
        
        mail_configured = bool(
            app.config.get('MAIL_USERNAME') and 
            app.config.get('MAIL_PASSWORD')
        )
        
        print(f"Email Configured: {'Yes' if mail_configured else 'No'}")
        print()
        
        if mail_configured:
            print("Testing email send...")
            test_email = app.config.get('MAIL_USERNAME')
            if test_email:
                result = send_email(
                    to_email=test_email,
                    subject="EstateCore Email Test",
                    body="This is a test email to verify email functionality is working correctly."
                )
                print(f"Email send result: {'Success' if result else 'Failed'}")
            else:
                print("No test email address available")
        else:
            print("Email not configured. Set MAIL_USERNAME and MAIL_PASSWORD in .env file")
            print()
            print("Example configuration:")
            print("MAIL_SERVER=smtp.gmail.com")
            print("MAIL_PORT=587") 
            print("MAIL_USE_TLS=true")
            print("MAIL_USERNAME=your_email@gmail.com")
            print("MAIL_PASSWORD=your_app_password")
            print("MAIL_DEFAULT_SENDER=EstateCore <your_email@gmail.com>")
        
        print()
        print("Email test completed")

if __name__ == "__main__":
    try:
        test_email_configuration()
    except Exception as e:
        print(f"Error during email test: {e}")
        sys.exit(1)