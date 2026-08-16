import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(__file__)

load_dotenv(os.path.join(BASE_DIR, ".env"))

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "mail.austinjiang.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 465))

DB_PATH = os.getenv("DB_PATH", "data/feachat.db")
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(BASE_DIR, DB_PATH)

SOCKET_HOST = os.getenv("SOCKET_HOST", "127.0.0.1")
SOCKET_PORT = int(os.getenv("SOCKET_PORT", 8888))
CLIENT_MAXIMUM = int(os.getenv("CLIENT_MAXIMUM", 100))
