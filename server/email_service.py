import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import EMAIL_ACCOUNT, EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT


def send_email(to_address: str, content: MIMEText, subject: str):
    message = MIMEMultipart()
    message["from"] = f"FeaChat <{EMAIL_ACCOUNT}>"
    message["to"] = to_address
    message["subject"] = f"FeaChat: {subject}"
    message.attach(content)

    session = smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
    session.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    session.sendmail(EMAIL_ACCOUNT, to_address, message.as_string())
    session.quit()
