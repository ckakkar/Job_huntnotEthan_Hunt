"""Store your credentials here or load from environment variables."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email credentials
EMAIL = {
    "sender": os.getenv("EMAIL_SENDER", ""),
    "password": os.getenv("EMAIL_PASSWORD", ""),
    "recipient": os.getenv("EMAIL_RECIPIENT", ""),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587"))
}