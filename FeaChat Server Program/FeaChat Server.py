import _thread
import math
import random
import re
import smtplib
import socket
import string
import time
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pymysql


class socketServer:
    def __init__(self):
        self.emailAccount = "ajcodetest@gmail.com"
        self.emailPassword = "jby1586886"
        self.dbHost="localhost"
        self.dbUser = "root"
        self.dbPassword = "jby1586886"
        self.dbName = "FeaChat"
        self.ipAddress = socket.gethostname()
        self.socketPort = 8888
        self.clientMaximum = 100
        self.clients = {}

    def build_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ipAddress, self.socketPort))
        self.server.listen(self.clientMaximum)

    def connect_database(self):
        info = {"host":self.dbHost,"user":self.dbUser, "password":self.dbPassword, "database":self.dbName}
        self.db = pymysql.connect(**info)
        self.cursor = self.db.cursor()

    def listen(self):
        while (True):
            client, ipAddress = self.server.accept()
            self.clients[ipAddress] = socketClient(client, ipAddress)

    def close(self):
        self.db.close()
        self.server.close()

    def initDb(self):
        sql = "drop table users;"
        self.dbQuery(sql)
        sql = "drop table files;"
        self.dbQuery(sql)
        sql = "drop table messages;"
        self.dbQuery(sql)
        sql = "create table users(id int, number char(20), password char(20), email varchar(256), devices text, avatar int, background int, nickname char(20), birth char(20), gender char(20), motto text);"
        self.dbQuery(sql)
        sql = "create table files(id int,size int, name char(50), extension char(50), data longtext);"
        self.dbQuery(sql)
        sql = "create table messages(id bigint, sender int, receiver int, time char(20), type char(20), message text); "
        self.dbQuery(sql)

    def clearDb(self):
        sql = "delete from users;"
        self.dbQuery(sql)
        sql = "delete from files;"
        self.dbQuery(sql)
        sql = "delete from messages;"
        self.dbQuery(sql)

    def dbQuery(self, sql, *value):
        self.cursor.execute(sql, value)
        self.db.commit()
        return self.cursor.fetchall()


class socketClient:
    def __init__(self, client, ipAddress):
        self.client = client
        self.ipAddress = ipAddress
        self.number = None
        self.loginCode = None
        self.registerCode = None
        self.loginCodeSendTime = 0
        self.registerCodeSendTime = 0
        _thread.start_new_thread(self.listen, ())

    def listen(self):
        while (True):
            try:
                request=eval(self.client.recv(1024 ** 2 * 100).decode("utf-8"))
                try:response = eval(f"self.{request[0]}")(request[1:])
                except Exception as ex:response =(False,str(ex))
                self.client.send(repr(response).encode("utf-8"))
            except:
                self.disconnect()
                break

    def disconnect(self):
        del server.clients[self.ipAddress]
        self.client.close()

    def count(self, table):
        sql = f"select count(*) from {table};"
        return server.dbQuery(sql)[0][0]

    def createCode(self, length):
        totle_string = string.ascii_letters + string.digits * 6
        return ''.join(random.sample(totle_string, length))

    def validateEmail(self,email):
        if (re.compile(r'^.+@.+').match(email)): return True
        else: return False

    def connect(self, info):
        self.hostname, self.macAddress = info

    def getUserInfo(self, info):
        number = info[0]
        sql = "select avatar, background, nickname, birth, gender, motto from users where number = %s;"
        result = server.dbQuery(sql, number)
        if(result==()): return (False,"Account is not registered")
        else: return (True,server.dbQuery(sql, number)[0])

    def modifyUserInfo(self, info):
        number, type, value = info
        if (number!=self.number): return
        sql = f"update users set {type} = %s where number = %s;"
        server.dbQuery(sql, value, number)

    def getLoginDevices(self, info):
        number = info[0]
        if (number!=self.number): return
        sql = "select devices from users where number = %s;"
        return (True,server.dbQuery(sql, number)[0][0])

    def register(self, info):
        number, password, email, code, macAddress = info
        if (len(number) < 6):
            return (False,"The number length is at least 10")
        elif (len(password) < 6):
            return (False,"The password length is at least 6")
        elif (not (len(email))):
            return (False,"The email can't be empty")
        elif (code == None or code != self.registerCode):
            return (False,"The verification code is wrong")
        elif (time.time() - self.registerCodeSendTime > 600):
            return (False,"The verification code has expired")
        else:
            sql = "select number from users where number = %s;"
            result = server.dbQuery(sql, number)
            if (result != ()):
                return (False,"The number has already been registered")
            else:
                sql = "select number from users where email = %s;"
                result = server.dbQuery(sql, email)
                if (result != ()):
                    return (False,"The email has already been bound")
                else:
                    id = self.count("users")
                    devices = {self.macAddress: self.hostname}
                    sql = "insert into users(id, number, password, email, devices) value (%s, %s, %s, %s, %s);"
                    server.dbQuery(sql, id, number, password, email, str(devices))
                    return (True,"Registered successfully")

    def sendRegisterCode(self, info):
        email = info[0]
        sendSpacing = 60 - time.time() + self.registerCodeSendTime
        if (sendSpacing > 0):
            return (False,f"You need to wait {math.ceil(sendSpacing)}s")
        elif (not (len(email))):
            return (False,"The email can't be empty")
        elif(not(self.validateEmail(email))):
            return (False,"The email format is incorrect")
        self.registerCodeSendTime = time.time()
        self.registerCode = self.createCode(6)
        file = open("SMTP HTML/Register Code.html", "rb").read().decode("utf-8") % self.registerCode
        content = MIMEText(file, "html", "utf-8")
        _thread.start_new_thread(self.sendEmail, (email, content, "Register Code",))
        return (True,"Sent successfully")

    def sendEmail(self, email, content, subject):
        sender = server.emailAccount
        password = server.emailPassword
        message = MIMEMultipart()
        message["from"] = Header("FeaChat", "utf-8")
        message["to"] = email
        message["subject"] = f"FeaChat: {subject}"
        message.attach(content)
        session = smtplib.SMTP("smtp.gmail.com", 587)
        session.starttls()
        session.login(sender, password)
        session.sendmail(sender, email, message.as_string())
        session.quit()

    def uploadFile(self, info):
        id = self.count("files")
        size, name, extension, data = info
        sql = "insert into files (id, size, name, extension, data) value (%s, %s, %s, %s, %s);"
        server.dbQuery(sql, id, size, name, extension, data)
        return (True,id)


'''
def get_count(type):
    sql = "select %s from count" % (type)
    cursor.execute(sql)
    return int(cursor.fetchall()[0][0])


def set_count(type, value):
    sql = "update count set %s = %s" % (type, str(value))
    cursor.execute(sql)
    db.commit()


def read_file(file_path):
    size = os.path.getsize(file_path)
    file = os.path.basename(file_path)
    name = os.path.splitext(file)[0]
    extension = os.path.splitext(file)[-1]
    file = open(file_path, "rb")
    data = base64.b64encode(file.read()).decode("utf-8")
    file.close()
    return (size, name, extension, data)


def file_info(content):
    sql = "select size,name,extension from files where id = '%s';" % content
    cursor.execute(sql)
    result = cursor.fetchall()
    return result[0]


def login(content):
    number, password = content
    if (number == ""):
        return "The number can't be empty"
    elif (password == ""):
        return "The password can't be empty"
    else:
        sql = "select number,password from users where number = '%s' and  password = '%s';" % content
        cursor.execute(sql)
        result = cursor.fetchall()
        if (result == ()):
            return "The number or password is wrong"
        elif (number in online_users):
            return "Account login elsewhere"
        else:
            online_users[number] = address
            login_address[address] = number
            return "succeeded"


def download_file(content):
    sql = "select size,name,extension,data from files where id = '%s';" % content
    cursor.execute(sql)
    size, name, extension, data = cursor.fetchall()[0]
    msg = (size, name, extension, data)
    return msg
'''

if (__name__ == "__main__"):
    server = socketServer()
    server.connect_database()
    server.build_server()
    server.listen()
