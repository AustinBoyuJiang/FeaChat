import random
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

def send_code(receiver,type,code):
    sender = "ajcodetest@gmail.com"
    password = "jby1586886"

    message = MIMEMultipart()
    message["from"] = Header("FeaChat","utf-8")
    message["to"] = receiver
    message["subject"] = f"FeaChat: {type}"

    content = open(f"SMTP HTML/{type}.html","rb").read().decode("utf-8") % code
    message.attach(MIMEText(content, "html", "utf-8"))

    session = smtplib.SMTP("smtp.gmail.com", 587)
    session.starttls()
    session.login(sender, password)
    session.sendmail(sender, receiver, message.as_string())
    session.quit()


print(send_code("austinjiangboyu@gmail.com",
                "Login Code","555555"))