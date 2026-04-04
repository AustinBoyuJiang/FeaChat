import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "mail.austinjiang.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 465))

DB_PATH = os.getenv("DB_PATH", "data/feachat.db")

SOCKET_PORT = 8888
CLIENT_MAXIMUM = 100
