# _*_coding:utf-8_*_

import _thread
import base64
import ctypes
import os
import socket
import sys
import uuid
import webbrowser

import pyautogui
from PIL import Image, ImageDraw, ImageFilter
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class feachatUi:
    class uiShadow(QWidget):
        def __init__(self, *info):
            super().__init__()
            self.press = False
            self.radius = 10
            self.color = "#212121"
            self.initWindow(info)
            self.addShadow()
            self.show()
            feachat.app.exec_()

        def initWindow(self, info):
            window = info[0]
            self.mainWindow = window(self, *info[1:])
            self.mainWindow.move(self.radius, self.radius)
            self.height = self.mainWindow.width + self.radius * 2
            self.width = self.mainWindow.height + self.radius * 2
            self.resize(self.height, self.width)
            self.move(self.center())
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setWindowFlag(Qt.FramelessWindowHint)

        def addShadow(self):
            self.effectShadow = QGraphicsDropShadowEffect(self)
            self.effectShadow.setOffset(0, 0)
            self.effectShadow.setBlurRadius(self.radius)
            self.effectShadow.setColor(QColor(self.color))
            self.mainWindow.setGraphicsEffect(self.effectShadow)

        def mousePressEvent(self, event):
            self.windowX = self.x()
            self.windowY = self.y()
            self.startX, self.startY = pyautogui.position()
            pos = event.windowPos()
            if (pos.x() >= self.radius and pos.x() <= self.mainWindow.titleWidth + self.radius):
                if (pos.y() >= self.radius and pos.y() <= self.mainWindow.titleHeight + self.radius):
                    self.press = True

        def mouseReleaseEvent(self, event):
            self.windowX = self.x()
            self.windowY = self.y()
            self.press = False

        def mouseMoveEvent(self, event):
            if (self.press == True):
                moveX, moveY = pyautogui.position()
                nextX = self.windowX + moveX - self.startX
                nextY = self.windowY + moveY - self.startY
                self.move(nextX, nextY)

        def center(self):
            window = self.frameGeometry()
            center = QDesktopWidget().availableGeometry().center()
            window.moveCenter(center)
            return window.topLeft()

    class loginUi(QWidget):
        width = 400
        height = 600
        titleWidth = 400
        titleHeight = 40

        class loginPage(QWidget):
            class numberEditItem(QWidget):
                itemOpSignal = pyqtSignal(str)
                eventFlag = False

                def __init__(self, parent, item, number):
                    super().__init__()
                    self.parent = parent
                    self.item = item
                    self.number = number
                    self.initWindow()
                    self.initItemArea()
                    self.initAvatarShow()
                    self.initNumberShow()
                    self.initNicknameShow()
                    self.initRemoveButton()
                    self.installEventFilter(self)

                def initWindow(self):
                    self.item.setText(self.number)
                    self.item.setSizeHint(QSize(300, 60))

                def initItemArea(self):
                    self.itemArea = QLabel(self)
                    self.itemArea.setGeometry(0, 0, 300, 60)
                    self.itemArea.setStyleSheet("background-color: #ebebeb;")

                def initAvatarShow(self):
                    self.avatarShow = QLabel(self)
                    self.avatarShow.setGeometry(20, 10, 40, 40)
                    self.avatarShow.setScaledContents(True)
                    # avatar = feachat.getTempFile(feachat.getUserInfo(self.number)["avatar"])
                    # img = QPixmap(avatar)
                    # self.avatarShow.setPixmap(img)

                def initNumberShow(self):
                    return

                def initNicknameShow(self):
                    return

                def initRemoveButton(self):
                    self.removeButton = QPushButton(self)
                    self.removeButton.setText("x")
                    self.removeButton.setGeometry(255, 15, 30, 30)
                    self.removeButton.clicked.connect(self.remove)

                def remove(self):
                    self.parent.parent.switchRemoveAccountPage(self.number)

                def eventFilter(self, object, event):
                    if (event.type() == QEvent.Enter):
                        self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                        self.eventFlag = True
                    elif (event.type() == QEvent.Leave):
                        self.itemArea.setStyleSheet("background-color: #ebebeb;")
                        self.eventFlag = False
                    if (self.parent.numberEdit.lineEdit().text() == self.number):
                        self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                    elif (not (self.eventFlag)):
                        self.itemArea.setStyleSheet("background-color: #ebebeb;")
                    return QWidget.eventFilter(self, object, event)

            def __init__(self, parent):
                super().__init__(parent)
                self.parent = parent
                self.initWindow()
                self.initLogoImage()
                self.initLoginHint()
                self.initNumberEdit()
                self.initPasswordEdit()
                self.initHidePasswordButton()
                self.initLoginButton()
                self.initRememberPasswordButton()
                self.initSwitchRegisterButton()
                self.show()
                self.numberEdit.setEditText(self.parent.number)
                self.passwordEdit.setText(self.parent.password)
                for number in reversed(list(self.parent.loginHistory.keys())):
                    item = QListWidgetItem(self.numberSelect)
                    numberEditItem = self.numberEditItem(self, item, number)
                    self.numberSelect.setItemWidget(item, numberEditItem)

            def initWindow(self):
                self.setGeometry(0, 40, 400, 510)

            def initLogoImage(self):
                self.logoImage = QLabel(self)
                self.logoImage.setGeometry(165, 60, 70, 70)
                self.logoImage.setScaledContents(True)
                img = QPixmap("pic/logo/logo.png")
                self.logoImage.setPixmap(img)

            def initLoginHint(self):
                self.loginHint = QLabel(self)
                self.loginHint.setGeometry(50, 130, 300, 60)
                self.loginHint.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.loginHint.setText("Welcome to FeaChat")
                self.loginHint.setObjectName("loginPage-loginHint")

            def initNumberEdit(self):
                self.numberEdit = QComboBox(self)
                self.numberEdit.setGeometry(50, 215, 300, 60)
                self.numberEdit.setEditable(True)
                self.numberEdit.setMaxVisibleItems(5)
                self.numberSelect = QListWidget()
                self.numberSelect.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.numberSelect.setVerticalScrollMode(QListWidget.ScrollPerPixel)
                self.numberEdit.setView(self.numberSelect)
                self.numberEdit.setModel(self.numberSelect.model())
                validator = QRegExpValidator(QRegExp("[a-zA-Z0-9_]+$"), self)
                self.numberEdit.lineEdit().setValidator(validator)
                self.numberEdit.lineEdit().setPlaceholderText("Enter your number")
                self.numberEdit.setObjectName("loginPage-numberEdit")
                self.numberEdit.editTextChanged.connect(self.numberChanged)

            def initPasswordEdit(self):
                self.passwordEdit = QLineEdit(self)
                self.passwordEdit.setGeometry(50, 290, 300, 60)
                self.passwordEdit.setMaxLength(20)
                validator = QRegExpValidator(QRegExp("[a-zA-Z0-9_]+$"), self)
                self.passwordEdit.setValidator(validator)
                self.passwordEdit.setPlaceholderText("Enter your password")
                self.passwordEdit.setObjectName("loginPage-passwordEdit")
                self.passwordEdit.textChanged.connect(self.passwordChanged)

            def initHidePasswordButton(self):
                self.hidePasswordButton = QPushButton(self)
                self.hidePasswordButton.setGeometry(300, 300, 40, 40)
                self.hidePasswordButton.setCheckable(True)
                self.hidePasswordButton.setChecked(True)
                self.hidePasswordButton.setObjectName("loginPage-hidePasswordButton")
                self.hidePasswordButton.clicked.connect(self.hidePassword)
                self.hidePassword()

            def initLoginButton(self):
                self.loginButton = QPushButton(self)
                self.loginButton.setGeometry(50, 365, 300, 60)
                self.loginButton.setText("Log in")
                self.loginButton.setObjectName("loginPage-loginButton")
                self.loginButton.clicked.connect(self.login)

            def initRememberPasswordButton(self):
                self.rememberPasswordButton = QCheckBox(self)
                self.rememberPasswordButton.setGeometry(50, 440, 200, 20)
                self.rememberPasswordButton.setChecked(feachat.readLocalData("remember password"))
                self.rememberPasswordButton.setText("Remember password")
                self.rememberPasswordButton.setObjectName("loginPage-rememberPasswordButton")
                self.rememberPasswordButton.stateChanged.connect(self.rememberPassword)

            def initSwitchRegisterButton(self):
                self.switchRegisterButton = QPushButton(self)
                self.switchRegisterButton.setGeometry(270, 440, 80, 20)
                self.switchRegisterButton.setText("Register >")
                self.switchRegisterButton.setObjectName("loginPage-switchRegisterButton")
                self.switchRegisterButton.clicked.connect(self.parent.switchRegisteredPage)

            def numberChanged(self):
                self.parent.hidePromptInformation()
                self.parent.number = self.numberEdit.lineEdit().text()
                if (self.parent.number in self.parent.loginHistory):
                    self.passwordEdit.setText(self.parent.loginHistory[self.parent.number])

            def passwordChanged(self):
                self.parent.hidePromptInformation()
                self.parent.password = self.passwordEdit.text()

            def hidePassword(self):
                self.parent.hidePromptInformation()
                if (self.hidePasswordButton.isChecked()):
                    self.passwordEdit.setEchoMode(QLineEdit.Password)
                else:
                    self.passwordEdit.setEchoMode(QLineEdit.Normal)

            def rememberPassword(self):
                self.parent.hidePromptInformation
                feachat.writeLocalData("remember password", self.rememberPasswordButton.isChecked())

            def login(self):
                self.parent.hidePromptInformation()
                self.buttonStatus = self.rememberPasswordButton.isChecked()
                feachat.writeLocalData("remember password", int(self.buttonStatus))
                self.parent.loginHistory[self.parent.number] = self.parent.password * self.buttonStatus
                feachat.writeLocalData("login history", self.parent.loginHistory)
                # self.close()
                # self.parent.page = feachatUi.loginUi.verifyPage(self.parent)
                return
                msg = (self.parent.number, self.parent.password)
                feachat.server.send(feachat.format_data("login", msg))
                result = feachat.get_feedback()
                if (result == "succeeded"):
                    self.loginSucceeded()
                else:
                    self.parent.promptError(result)

            def loginSucceeded(self):
                return
                self.parent.promptInformation("succeeded", "Login succeeded")
                self.numberEdit.setEnabled(False)
                self.passwordEdit.setEnabled(False)
                self.loginButton.setEnabled(False)
                self.rememberPasswordButton.setEnabled(False)
                self.switchRegisteredButton.setEnabled(False)
                feachat.number = self.parent.number
                feachat.password = self.parent.password
                QTimer.singleShot(1000, self.openChatWindow)

            def openChatWindow(self):
                self.parent.window.close()
                feachat.chatWindow = feachatUi.uiShadow(feachatUi.chatUi)

        class registerPage(QWidget):
            class userInfoPage(QWidget):
                class genderEditItem(QWidget):
                    itemOpSignal = pyqtSignal(str)
                    eventFlag = False

                    def __init__(self, parent, item, gender):
                        super().__init__()
                        self.parent = parent
                        self.item = item
                        self.gender = gender
                        self.initWindow()
                        self.initItemArea()
                        self.initGenderShow()
                        self.installEventFilter(self)

                    def initWindow(self):
                        self.item.setText(self.gender)
                        self.item.setSizeHint(QSize(300, 60))

                    def initItemArea(self):
                        self.itemArea = QLabel(self)
                        self.itemArea.setGeometry(0, 0, 300, 60)
                        self.itemArea.setStyleSheet("background-color: #ebebeb;")

                    def initGenderShow(self):
                        self.genderShow = QLabel(self)
                        self.genderShow.setGeometry(20, 0, 280, 60)
                        self.genderShow.setText(self.gender)
                        self.genderShow.setObjectName("registerPage-userInfoPage-genderEditItem-genderShow")

                    def eventFilter(self, object, event):
                        if (event.type() == QEvent.Enter):
                            self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                            self.eventFlag = True
                        elif (event.type() == QEvent.Leave):
                            self.itemArea.setStyleSheet("background-color: #ebebeb;")
                            self.eventFlag = False
                        if (self.parent.genderEdit.currentText() == self.gender):
                            self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                        elif (not (self.eventFlag)):
                            self.itemArea.setStyleSheet("background-color: #ebebeb;")
                        return QWidget.eventFilter(self, object, event)

                def __init__(self, parent):
                    super().__init__(parent)
                    self.parent = parent
                    self.initWindow()
                    self.initAvatarButton()
                    self.initNicknameEdit()
                    self.initBirthEdit()
                    self.initGenderEdit()
                    self.show()
                    self.nicknameEdit.setText(self.parent.nickname)
                    self.birthEdit.setDate(QDate.fromString(self.parent.birth, "yyyy-MM-dd"))
                    self.genderEdit.setCurrentText(self.parent.gender)

                def initWindow(self):
                    self.setGeometry(0, 40, 400, 365)

                def initAvatarButton(self):
                    self.avatarButton = QPushButton(self)
                    self.avatarButton.setGeometry(150, 20, 100, 100)
                    self.avatarButton.setStyleSheet("border-image: url(%s);" % self.parent.avatar)
                    self.avatarButton.clicked.connect(self.avatarChanged)

                def initNicknameEdit(self):
                    self.nicknameEdit = QLineEdit(self)
                    self.nicknameEdit.setGeometry(50, 140, 300, 60)
                    self.nicknameEdit.setMaxLength(20)
                    self.nicknameEdit.setPlaceholderText("Set your nickname")
                    self.nicknameEdit.setObjectName("registerPage-userInfoPage-nicknameEdit")
                    self.nicknameEdit.textChanged.connect(self.nicknameChanged)

                def initBirthEdit(self):
                    self.birthEdit = QDateEdit(self)
                    self.birthEdit.setGeometry(50, 215, 300, 60)
                    self.birthEdit.setDisplayFormat("yyyy-MM-dd")
                    self.birthEdit.setMaximumDate(QDate.currentDate())
                    self.birthEdit.setMinimumDate(QDate.currentDate().addYears(-100))
                    self.birthEdit.setToolTip("Choose your Birth day")
                    self.birthEdit.setObjectName("registerPage-userInfoPage-birthEdit")
                    self.birthEdit.dateChanged.connect(self.birthChanged)

                def initGenderEdit(self):
                    self.genderEdit = QComboBox(self)
                    self.genderEdit.setGeometry(50, 290, 300, 60)
                    self.genderSelect = QListWidget()
                    self.genderEdit.setView(self.genderSelect)
                    self.genderEdit.setModel(self.genderSelect.model())
                    for gender in ["Boy", "Girl", "Other"]:
                        item = QListWidgetItem(self.genderSelect)
                        genderEditItem = self.genderEditItem(self, item, gender)
                        self.genderSelect.setItemWidget(item, genderEditItem)
                    self.genderEdit.setToolTip("Choose your Gender")
                    self.genderEdit.setObjectName("registerPage-userInfoPage-genderEdit")
                    self.genderEdit.currentTextChanged.connect(self.genderChanged)

                def avatarChanged(self):
                    self.parent.parent.hidePromptInformation()
                    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                    path = QFileDialog.getOpenFileName(self, "Select the image", desktop, "Images (*.png;*.jpg)")[0]
                    if (not path): return
                    self.parent.avatar = "pic/loginUi/registerPage/avatar/select avatar.png"
                    img = feachat.cropCircle(Image.open(path), 500)
                    img.save(self.parent.avatar)
                    self.avatarButton.setStyleSheet("border-image: url(%s)" % self.parent.avatar)

                def nicknameChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.nickname = self.nicknameEdit.text()

                def birthChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.birth = self.birthEdit.date().toString("yyyy-MM-dd")

                def genderChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.gender = self.genderEdit.currentText()

            class accountInfoPage(QWidget):
                def __init__(self, parent):
                    super().__init__(parent)
                    self.parent = parent
                    self.initWindow()
                    self.initNumberEdit()
                    self.initPasswordEdit()
                    self.initEmailEdit()
                    self.initCodeEdit()
                    self.initSendCodeButton()
                    self.show()
                    self.numberEdit.setText(self.parent.number)
                    self.passwordEdit.setText(self.parent.password)
                    self.emailEdit.setText(self.parent.email)
                    self.codeEdit.setText(self.parent.code)

                def initWindow(self):
                    self.setGeometry(0, 40, 400, 365)

                def initNumberEdit(self):
                    self.numberEdit = QLineEdit(self)
                    self.numberEdit.setGeometry(50, 65, 300, 60)
                    self.numberEdit.setMaxLength(20)
                    validator = QRegExpValidator(QRegExp("[a-zA-Z0-9_]+$"), self)
                    self.numberEdit.setValidator(validator)
                    self.numberEdit.setPlaceholderText("Set your number")
                    self.numberEdit.setObjectName("registerPage-accountInfoPage-numberEdit")
                    self.numberEdit.textChanged.connect(self.numberChanged)

                def initPasswordEdit(self):
                    self.passwordEdit = QLineEdit(self)
                    self.passwordEdit.setGeometry(50, 140, 300, 60)
                    self.passwordEdit.setMaxLength(20)
                    validator = QRegExpValidator(QRegExp("[a-zA-Z0-9_]+$"), self)
                    self.passwordEdit.setValidator(validator)
                    self.passwordEdit.setPlaceholderText("Set your password")
                    self.passwordEdit.setObjectName("registerPage-accountInfoPage-passwordEdit")
                    self.passwordEdit.textChanged.connect(self.passwordChanged)

                def initEmailEdit(self):
                    self.emailEdit = QLineEdit(self)
                    self.emailEdit.setGeometry(50, 215, 300, 60)
                    self.emailEdit.setPlaceholderText("Enter your email address")
                    self.emailEdit.setObjectName("registerPage-accountInfoPage-emailEdit")
                    self.emailEdit.textChanged.connect(self.emailChanged)

                def initCodeEdit(self):
                    self.codeEdit = QLineEdit(self)
                    self.codeEdit.setGeometry(50, 290, 300, 60)
                    self.codeEdit.setMaxLength(6)
                    validator = QRegExpValidator(QRegExp("[a-zA-Z0-9]+$"), self)
                    self.codeEdit.setValidator(validator)
                    self.codeEdit.setPlaceholderText("Enter verification code")
                    self.codeEdit.setObjectName("registerPage-accountInfoPage-codeEdit")
                    self.codeEdit.textChanged.connect(self.codeChanged)

                def initSendCodeButton(self):
                    self.sendCodeButton = QPushButton(self)
                    self.sendCodeButton.setGeometry(300, 300, 40, 40)
                    self.sendCodeButton.setObjectName("registerPage-accountInfoPage-sendCodeButton")
                    self.sendCodeButton.clicked.connect(self.sendCode)

                def numberChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.number = self.numberEdit.text()

                def passwordChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.password = self.passwordEdit.text()

                def emailChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.email = self.emailEdit.text()

                def codeChanged(self):
                    self.parent.parent.hidePromptInformation()
                    self.parent.code = self.codeEdit.text()

                def sendCode(self):
                    self.parent.parent.hidePromptInformation()
                    request = feachat.request("sendRegisterCode", self.parent.email)
                    if (request[0] == True): self.parent.parent.promptSucceeded(request[1])
                    else: self.parent.parent.promptError(request[1])

            def __init__(self, parent):
                super().__init__(parent)
                self.parent = parent
                self.avatar = "pic/loginUi/registerPage/avatar/default avatar.png"
                self.background = "pic/loginUi/registerPage/background/default background.png"
                self.nickname = ""
                self.birth = QDate.currentDate().toString("yyyy-MM-dd")
                self.gender = "Boy"
                self.number = ""
                self.password = ""
                self.email = ""
                self.code = ""
                self.initWindow()
                self.initSwitchLoginButton()
                self.initRegisterButton()
                self.initSwitchPageArea()
                self.initSwitchPageSlider()
                self.initSwitchUserInfoButton()
                self.initSwitchAccountInfoButton()
                self.show()
                self.switchUserInfoButton.setEnabled(False)
                self.page = feachatUi.loginUi.registerPage.userInfoPage(self)

            def initWindow(self):
                self.setGeometry(0, 40, 400, 510)

            def initSwitchPageArea(self):
                self.switchPageArea = QLabel(self)
                self.switchPageArea.setGeometry(60, 18, 280, 3)
                self.switchPageArea.setObjectName("registerPage-switchPageArea")

            def initSwitchPageSlider(self):
                self.switchPageSlider = QLabel(self)
                self.switchPageSlider.setGeometry(60, 18, 140, 3)
                self.switchPageSlider.setObjectName("registerPage-switchPageSlider")

            def initSwitchUserInfoButton(self):
                self.switchUserInfoButton = QPushButton(self)
                self.switchUserInfoButton.setGeometry(60, 23, 140, 20)
                self.switchUserInfoButton.setCheckable(True)
                self.switchUserInfoButton.setChecked(True)
                self.switchUserInfoButton.setText("User info")
                self.switchUserInfoButton.setObjectName("registerPage-switchUserInfoButton")
                self.switchUserInfoButton.clicked.connect(self.switchUserInfoPage)

            def initSwitchAccountInfoButton(self):
                self.switchAccountInfoButton = QPushButton(self)
                self.switchAccountInfoButton.setGeometry(200, 23, 140, 20)
                self.switchAccountInfoButton.setCheckable(True)
                self.switchAccountInfoButton.setChecked(False)
                self.switchAccountInfoButton.setText("Account info")
                self.switchAccountInfoButton.setObjectName("registerPage-switchAccountInfoButton")
                self.switchAccountInfoButton.clicked.connect(self.switchAccountInfoPage)

            def initRegisterButton(self):
                self.registerButton = QPushButton(self)
                self.registerButton.setGeometry(50, 405, 300, 60)
                self.registerButton.setText("Register")
                self.registerButton.setObjectName("registerPage-registerButton")
                self.registerButton.clicked.connect(self.register)

            def initSwitchLoginButton(self):
                self.switchLoginButton = QPushButton(self)
                self.switchLoginButton.move(50, 480)
                self.switchLoginButton.setText("< Log in")
                self.switchLoginButton.setObjectName("registerPage-switchLoginButton")
                self.switchLoginButton.clicked.connect(self.parent.switchLoginPage)

            def switchUserInfoPage(self):
                self.parent.hidePromptInformation()
                self.animation = QPropertyAnimation(self.switchPageSlider, b'pos')
                self.animation.setDuration(200)
                self.animation.setStartValue(QPoint(200, 18))
                self.animation.setEndValue(QPoint(60, 18))
                self.animation.setEasingCurve(QEasingCurve.InOutCubic)
                self.animation.start()
                self.switchUserInfoButton.setEnabled(False)
                self.switchAccountInfoButton.setEnabled(True)
                self.switchUserInfoButton.setChecked(True)
                self.switchAccountInfoButton.setChecked(False)
                self.page.close()
                self.page = feachatUi.loginUi.registerPage.userInfoPage(self)

            def switchAccountInfoPage(self):
                self.parent.hidePromptInformation()
                self.animation = QPropertyAnimation(self.switchPageSlider, b'pos')
                self.animation.setDuration(200)
                self.animation.setStartValue(QPoint(60, 18))
                self.animation.setEndValue(QPoint(200, 18))
                self.animation.setEasingCurve(QEasingCurve.InOutCubic)
                self.animation.start()
                self.switchUserInfoButton.setEnabled(True)
                self.switchAccountInfoButton.setEnabled(False)
                self.switchUserInfoButton.setChecked(False)
                self.switchAccountInfoButton.setChecked(True)
                self.page.close()
                self.page = feachatUi.loginUi.registerPage.accountInfoPage(self)

            def register(self):
                self.parent.hidePromptInformation()
                msg = (self.number, self.password, self.email, self.code, feachat.macAddress)
                request = feachat.request("register", *msg)
                if (request[0] == True): self.registerSucceeded(request[1])
                else: self.parent.promptError(request[1])

            def registerSucceeded(self,prompt):
                avatarId = feachat.uploadFile(self.avatar)
                backgroundId = feachat.uploadFile(self.background)
                feachat.modifyUserInfo(self.number, "avatar", avatarId)
                feachat.modifyUserInfo(self.number, "background", backgroundId)
                feachat.modifyUserInfo(self.number, "nickname", self.nickname)
                feachat.modifyUserInfo(self.number, "birth", self.birth)
                feachat.modifyUserInfo(self.number, "gender", self.gender)
                feachat.modifyUserInfo(self.number, "motto", "")
                if (feachat.readLocalData("remember password")): self.parent.loginHistory[self.number] = self.password
                else: self.parent.loginHistory[self.number] = ""
                feachat.writeLocalData("login history", self.parent.loginHistory)
                self.parent.number = self.number
                self.parent.password = self.password
                self.parent.switchLoginPage()
                self.parent.promptSucceeded(prompt)

        class removeAccountPage(QWidget):
            def __init__(self, parent, number):
                super().__init__(parent)
                self.parent = parent
                self.number = number
                self.option = 1
                self.initWindow()
                self.initWarningImage()
                self.initOptions()
                self.initConfirmButton()
                self.initCancelButton()
                self.show()

            def initWindow(self):
                self.setGeometry(0, 40, 400, 510)

            def initWarningImage(self):
                self.warningImage = QLabel(self)
                self.warningImage.setGeometry(165, 60, 70, 70)
                self.warningImage.setScaledContents(True)
                img = QPixmap("pic/loginUi/removeAccountPage/warning.png")
                self.warningImage.setPixmap(img)

            def initOptions(self):
                self.option1 = QRadioButton(self)
                self.option1.move(50,190)
                self.option1.setChecked(True)
                self.option1.setText("Remove the account from\nthe login history")
                self.option1.setObjectName("removeAccountPage-option1")
                self.option2 = QRadioButton(self)
                self.option2.move(50,280)
                self.option2.setText("Remove all files about the\naccount from this device")
                self.option2.setObjectName("removeAccountPage-option2")
                self.options = QButtonGroup(self)
                self.options.addButton(self.option1, 1)
                self.options.addButton(self.option2, 2)
                self.options.buttonClicked.connect(self.optionChanged)

            def initConfirmButton(self):
                self.confirmButton = QPushButton(self)
                self.confirmButton.resize(100, 40)
                self.confirmButton.move(90, 400)
                self.confirmButton.setText("Confirm")
                self.confirmButton.setObjectName("removeAccountPage-confirmButton")
                self.confirmButton.clicked.connect(self.removeAccount)

            def initCancelButton(self):
                self.cancelButton = QPushButton(self)
                self.cancelButton.resize(100, 40)
                self.cancelButton.move(210, 400)
                self.cancelButton.setText("Cancel")
                self.cancelButton.setObjectName("removeAccountPage-cancelButton")
                self.cancelButton.clicked.connect(self.parent.switchLoginPage)

            def optionChanged(self,obeject):
                self.parent.hidePromptInformation()
                self.option = self.options.id(obeject)

            def removeAccount(self):
                self.parent.hidePromptInformation()
                if(self.option==1):
                    if (self.number in self.parent.loginHistory):
                        del self.parent.loginHistory[self.number]
                        feachat.writeLocalData("login history", self.parent.loginHistory)
                    self.parent.switchLoginPage()
                else:
                    window=feachatUi.messageBoxUi
                    parent = self.parent
                    title="Remove Account"
                    prompt="Confirm you want to remove all files about the account from this device again"
                    event = self.removeOption2
                    feachatUi.uiShadow(window, parent, title, prompt, event)

            def removeOption2(self):
                if(self.number in self.parent.loginHistory):
                    del self.parent.loginHistory[self.number]
                    feachat.writeLocalData("login history", self.parent.loginHistory)
                messages = feachat.readLocalData("messages")
                if(self.number in messages):
                    del messages[self.number]
                    feachat.writeLocalData("messages", messages)
                self.parent.switchLoginPage()

        class verifyPage(QWidget):
            def __init__(self, parent):
                super().__init__(parent)
                self.parent = parent
                self.code = ""
                self.initWindow()
                self.initCodeEdit()
                self.initSendCodeButton()
                self.initVerifyButton()
                self.initSwitchLoginButton()
                self.show()

            def initWindow(self):
                self.setGeometry(0, 40, 400, 510)

            def initCodeEdit(self):
                self.codeEdit = QLineEdit(self)
                self.codeEdit.setGeometry(50, 255, 300, 60)
                self.codeEdit.setMaxLength(6)
                validator = QRegExpValidator(QRegExp("[a-zA-Z0-9]+$"), self)
                self.codeEdit.setValidator(validator)
                self.codeEdit.setPlaceholderText("Enter verification code")
                self.codeEdit.setObjectName("verifyPage-codeEdit")
                self.codeEdit.textChanged.connect(self.codeChanged)

            def initSendCodeButton(self):
                self.sendCodeButton = QPushButton(self)
                self.sendCodeButton.setGeometry(300, 265, 40, 40)
                self.sendCodeButton.setObjectName("verifyPage-sendCodeButton")
                self.sendCodeButton.clicked.connect(self.sendCode)

            def initVerifyButton(self):
                self.verifyButton = QPushButton(self)
                self.verifyButton.setGeometry(50, 330, 300, 60)
                self.verifyButton.setText("Verify")
                self.verifyButton.setObjectName("verifyPage-verifyButton")
                self.verifyButton.clicked.connect(self.verify)

            def initSwitchLoginButton(self):
                self.switchLoginButton = QPushButton(self)
                self.switchLoginButton.setGeometry(50, 405, 70, 20)
                self.switchLoginButton.setText("< Return")
                self.switchLoginButton.setObjectName("verifyPage-switchLoginButton")
                self.switchLoginButton.clicked.connect(self.switchLogin)

            def switchLogin(self):
                self.parent.hidePromptInformation()
                self.close()
                self.parent.page = feachatUi.loginUi.loginPage(self.parent)

            def codeChanged(self):
                self.parent.hidePromptInformation()
                self.code = self.codeEdit.text()

            def sendCode(self):
                self.parent.hidePromptInformation()
                print(666)

            def verify(self):
                self.parent.hidePromptInformation()
                self.switchLogin()

        def __init__(self, window):
            super().__init__(window)
            self.window = window
            self.loginHistory = feachat.readLocalData("login history")
            if (len(self.loginHistory)):
                self.number = list(self.loginHistory.keys())[-1]
                self.password = self.loginHistory[self.number]
            else:
                self.number = ""
                self.password = ""
            self.initWindow()
            self.initTitleArea()
            self.initLoginArea()
            self.initPromptSucceededArea()
            self.initPromptErrorArea()
            self.initTitleFilling()
            self.initLoginFilling()
            self.initPromptSucceededFilling()
            self.initPromptErrorFilling()
            self.initTitleText()
            self.initCloseButton()
            self.initMinButton()
            self.hidePromptInformation()
            self.show()
            self.page = feachatUi.loginUi.loginPage(self)

        def initWindow(self):
            self.resize(self.width, self.height)
            self.window.setWindowTitle(feachat.name)
            self.window.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet(feachat.getStyleSheet("loginUi"))

        def initTitleArea(self):
            self.titleArea = QLabel(self)
            self.titleArea.setGeometry(0, 0, 400, 40)
            self.titleArea.setObjectName("titleArea")

        def initLoginArea(self):
            self.loginArea = QLabel(self)
            self.loginArea.setGeometry(0, 40, 400, 560)
            self.loginArea.setObjectName("loginArea")

        def initPromptSucceededArea(self):
            self.promptSucceededArea = QLabel(self)
            self.promptSucceededArea.setGeometry(0, 550, 400, 50)
            self.promptSucceededArea.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.promptSucceededArea.setObjectName("promptSucceededArea")

        def initPromptErrorArea(self):
            self.promptErrorArea = QLabel(self)
            self.promptErrorArea.setGeometry(0, 550, 400, 50)
            self.promptErrorArea.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.promptErrorArea.setObjectName("promptErrorArea")

        def initTitleFilling(self):
            self.titleFilling = QLabel(self)
            self.titleFilling.setGeometry(0, 30, 400, 10)
            self.titleFilling.setObjectName("titleFilling")

        def initLoginFilling(self):
            self.loginFilling = QLabel(self)
            self.loginFilling.setGeometry(0, 40, 400, 10)
            self.loginFilling.setObjectName("loginFilling")

        def initPromptSucceededFilling(self):
            self.promptSucceededFilling = QLabel(self)
            self.promptSucceededFilling.setGeometry(0, 550, 400, 10)
            self.promptSucceededFilling.setObjectName("promptSucceededFilling")

        def initPromptErrorFilling(self):
            self.promptErrorFilling = QLabel(self)
            self.promptErrorFilling.setGeometry(0, 550, 400, 10)
            self.promptErrorFilling.setObjectName("promptErrorFilling")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.setGeometry(15, 0, 385, 40)
            self.titleText.setText(feachat.name)
            self.titleText.setObjectName("titleText")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.setGeometry(360, 5, 35, 30)
            self.closeButton.setText("×")
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.clicked.connect(self.window.close)

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.setGeometry(320, 5, 35, 30)
            self.minButton.setText("-")
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.clicked.connect(self.window.showMinimized)

        def promptSucceeded(self, hint):
            self.hidePromptInformation()
            self.promptSucceededArea.setVisible(True)
            self.promptSucceededFilling.setVisible(True)
            self.promptSucceededArea.setText(hint)

        def promptError(self, hint):
            self.hidePromptInformation()
            self.promptErrorArea.setVisible(True)
            self.promptErrorFilling.setVisible(True)
            self.promptErrorArea.setText(hint)

        def hidePromptInformation(self):
            self.promptSucceededArea.setVisible(False)
            self.promptSucceededFilling.setVisible(False)
            self.promptErrorArea.setVisible(False)
            self.promptErrorFilling.setVisible(False)

        def switchLoginPage(self):
            self.hidePromptInformation()
            self.page.close()
            self.page = feachatUi.loginUi.loginPage(self)

        def switchRegisteredPage(self):
            self.hidePromptInformation()
            self.page.close()
            self.page = feachatUi.loginUi.registerPage(self)

        def switchRemoveAccountPage(self, number):
            self.hidePromptInformation()
            self.page.close()
            self.page = feachatUi.loginUi.removeAccountPage(self, number)

    class chatUi(QWidget):
        class expandMoreArea(QListWidget):
            class addFriendsButton(QWidget):
                def __init__(self, item):
                    super().__init__()
                    item.setSizeHint(QSize(180, 50))
                    self.initWidget()
                    self.initText()

                def initWidget(self):
                    self.resize(200, 50)
                    self.setStyleSheet("background-color: transparent;")

                def initText(self):
                    self.text = QLabel(self)
                    self.text.resize(150, 50)
                    self.text.move(50, 0)
                    self.text.setText("Add Friends")
                    self.text.setAlignment(Qt.AlignVCenter)
                    self.text.setStyleSheet("font-family: Microsoft YaHei;"
                                            "font-size: 18px;"
                                            "color: #ffffff;")

            class createGroupButton(QWidget):
                def __init__(self, item):
                    super().__init__()
                    item.setSizeHint(QSize(180, 50))
                    self.initWidget()
                    self.initText()

                def initWidget(self):
                    self.resize(200, 50)
                    self.setStyleSheet("background-color: transparent;")

                def initText(self):
                    self.text = QLabel(self)
                    self.text.resize(150, 50)
                    self.text.move(50, 0)
                    self.text.setText("Create Group")
                    self.text.setAlignment(Qt.AlignVCenter)
                    self.text.setStyleSheet("font-family: Microsoft YaHei;"
                                            "font-size: 18px;"
                                            "color: #ffffff;")

            class shareMomentsButton(QWidget):
                def __init__(self, item):
                    super().__init__()
                    item.setSizeHint(QSize(180, 50))
                    self.initWidget()
                    self.initText()

                def initWidget(self):
                    self.resize(200, 50)
                    self.setStyleSheet("background-color: transparent;")

                def initText(self):
                    self.text = QLabel(self)
                    self.text.resize(150, 50)
                    self.text.move(50, 0)
                    self.text.setText("Share Moments")
                    self.text.setAlignment(Qt.AlignVCenter)
                    self.text.setStyleSheet("font-family: Microsoft YaHei;"
                                            "font-size: 18px;"
                                            "color: #ffffff;")

            def __init__(self, parent):
                super().__init__(parent)
                self.initWidget()
                item = QListWidgetItem()
                self.addItem(item)
                self.setItemWidget(item, self.addFriendsButton(item))
                item = QListWidgetItem()
                self.addItem(item)
                self.setItemWidget(item, self.createGroupButton(item))
                item = QListWidgetItem()
                self.addItem(item)
                self.setItemWidget(item, self.shareMomentsButton(item))
                self.show()

            def initWidget(self):
                self.resize(200, 150)
                self.move(225, 67.5)
                self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
                self.itemClicked.connect(self.buttonClicked)
                self.setStyleSheet("QListWidget {background-color: #727272;"
                                   "outline: none;"
                                   "border:0px;}"
                                   "QListWidget:Item:hover{"
                                   "background-color: #808080;}"
                                   "QListWidget:Item:selected{"
                                   "background-color: #808080;}")

            def buttonClicked(self):
                if (self.selectedItems()):
                    button = type(self.itemWidget(self.selectedItems()[0]))
                    chatWindow.mainWindow.retakeMore()
                    if (str(button) == "<class '__main__.chatUi.expandMoreArea.addFriendsButton'>"):
                        if ("addFriendsWindow" in vars(chatWindow.mainWindow)
                                and chatWindow.mainWindow.addFriendsWindow.isVisible()):
                            chatWindow.mainWindow.addFriendsWindow.showNormal()
                            chatWindow.mainWindow.addFriendsWindow.raise_()
                        else:
                            chatWindow.mainWindow.addFriendsWindow = uiShadow(addFriendsUi)
                            app.exec_()
                    if (str(button) == "<class '__main__.chatUi.expandMoreArea.createGroupButton'>"):
                        if ("createGroupWindow" in vars(chatWindow.mainWindow)
                                and chatWindow.mainWindow.addFriendsWindow.isVisible()):
                            chatWindow.mainWindow.createGroupWindow.showNormal()
                            chatWindow.mainWindow.createGroupWindow.raise_()
                        else:
                            chatWindow.mainWindow.createGroupWindow = uiShadow(createGroupUi)
                            app.exec_()
                    if (str(button) == "<class '__main__.chatUi.expandMoreArea.shareMomentsButton'>"):
                        if ("shareMomentsWindow" in vars(chatWindow.mainWindow)
                                and chatWindow.mainWindow.addFriendsWindow.isVisible()):
                            chatWindow.mainWindow.shareMomentsWindow.showNormal()
                            chatWindow.mainWindow.shareMomentsWindow.raise_()
                        else:
                            chatWindow.mainWindow.shareMomentsWindow = uiShadow(shareMomentsUi)
                            app.exec_()

        class searchList(QListWidget):
            def __init__(self, parent):
                super().__init__(parent)
                self.initWidget()
                self.show()

            def initWidget(self):
                self.resize(375, 765)
                self.move(75, 75)
                self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
                self.setStyleSheet("QListWidget {background-color: #ffffff;"
                                   "outline: none;"
                                   "border:0px;}"
                                   "QListWidget:Item:hover{background-color: #e0e0e0;}"
                                   "QListWidget:Item:selected{background-color: #d0d0d0;}")

            def mouseReleaseEvent(self, event):
                chatWindow.mainWindow.retakeMore()
                super().mouseReleaseEvent(event)

        class chatList(QListWidget):
            class chatsSelectBox(QWidget):
                def __init__(self, item, number, lastMessage):
                    super().__init__()
                    self.nickname = user_info[number][0]
                    self.profile_picture = "data/temp/%s" % user_info[number][1]
                    self.number = number
                    if (lastMessage[4] == "text"):
                        self.lastMessage = lastMessage[5]
                    elif (lastMessage[4] == "file"):
                        file_info = get_file_info(lastMessage[5])
                        self.lastMessage = "[file] %s" % (file_info[1] + file_info[2])
                    elif (lastMessage[4] == "link"):
                        self.lastMessage = "[link] %s" % lastMessage[5]
                    elif (lastMessage[4] == "emoji"):
                        self.lastMessage = "[emoji]"
                    self.lastSendTime = set_time(lastMessage[3])
                    self.notReceived = 0
                    item.setSizeHint(QSize(375, 90))
                    self.initWidget()
                    self.initAvatarShow()
                    self.initNicknameShow()
                    self.initLastMessageShow()
                    self.initLastSendTimeShow()
                    self.initNotReceivedReminder()
                    self.setNotReceived(0)

                def initWidget(self):
                    self.resize(750, 90)

                def initAvatarShow(self):
                    self.avatarShow = QLabel(self)
                    self.avatarShow.resize(60, 60)
                    self.avatarShow.move(20, 15)
                    self.avatarShow.setStyleSheet("border-radius: 30px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initNicknameShow(self):
                    self.nicknameShow = QLabel(self)
                    self.nicknameShow.resize(90, 20)
                    self.nicknameShow.move(100, 15)
                    self.nicknameShow.setText(self.nickname)
                    self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                    "font-size: 20px;"
                                                    "background-color: transparent;")

                def initLastMessageShow(self):
                    self.lastMessageShow = QLabel(self)
                    self.lastMessageShow.move(100, 35)
                    self.lastMessageShow.setText(self.lastMessage)
                    self.lastMessageShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.lastMessageShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                       "font-size: 18px;"
                                                       "color: #888888;"
                                                       "background-color: transparent;")

                def initLastSendTimeShow(self):
                    self.lastSendTimeShow = QLabel(self)
                    self.lastSendTimeShow.resize(160, 20)
                    self.lastSendTimeShow.move(200, 15)
                    self.lastSendTimeShow.setText(self.lastSendTime)
                    self.lastSendTimeShow.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.lastSendTimeShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                        "font-size: 15px;"
                                                        "color: #aaaaaa;"
                                                        "background-color: transparent;")

                def initNotReceivedReminder(self):
                    self.notReceivedReminder = QLabel(self)
                    self.notReceivedReminder.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                    self.notReceivedReminder.setStyleSheet("font-family: Microsoft YaHei;"
                                                           "font-size: 14px;"
                                                           "color: #ffffff;"
                                                           "background-color: #ff0000;"
                                                           "border-radius: 10px;")

                def setNotReceived(self, number):
                    self.notReceived = number
                    if (self.notReceived == 0):
                        self.notReceivedReminder.setVisible(False)
                        self.lastMessageShow.resize(260, 40)
                    elif (len(str(self.notReceived)) == 1):
                        self.notReceivedReminder.setVisible(True)
                        self.lastMessageShow.resize(230, 40)
                        self.notReceivedReminder.resize(20, 20)
                        self.notReceivedReminder.move(340, 45)
                        self.notReceivedReminder.setText(str(self.notReceived))
                    elif (len(str(self.notReceived)) == 2):
                        self.notReceivedReminder.setVisible(True)
                        self.lastMessageShow.resize(223, 40)
                        self.notReceivedReminder.resize(27, 20)
                        self.notReceivedReminder.move(333, 45)
                        self.notReceivedReminder.setText(str(self.notReceived))
                    else:
                        self.notReceivedReminder.setVisible(True)
                        self.lastMessageShow.resize(215, 40)
                        self.notReceivedReminder.resize(35, 20)
                        self.notReceivedReminder.move(325, 45)
                        self.notReceivedReminder.setText("99+")

            def __init__(self, parent):
                super().__init__(parent)
                self.initWidget()
                self.number_item = {}
                for i in range(len(all_message) - 1, -1, -1):
                    if (all_message[i][1] != account and all_message[i][2] != account):
                        number = all_message[i][2]
                    elif (all_message[i][1] == account):
                        number = all_message[i][2]
                    else:
                        number = all_message[i][1]
                    if (not (number in user_info)):
                        user_info[number] = get_user_info(number)
                        download_file(user_info[number][1], "data")
                        download_file(user_info[number][2], "data")
                    if (not (number in self.number_item)):
                        item = QListWidgetItem()
                        self.number_item[number] = item
                        self.addItem(item)
                        self.setItemWidget(item, self.chatsSelectBox(item, number, all_message[i]))
                self.show()

            def initWidget(self):
                self.resize(375, 765)
                self.move(75, 75)
                self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
                self.itemClicked.connect(self.showMessageList)
                self.setStyleSheet("QListWidget {background-color: #ffffff;"
                                   "outline: none;"
                                   "border:0px;}"
                                   "QListWidget:Item:hover{background-color: #e0e0e0;}"
                                   "QListWidget:Item:selected{background-color: #d0d0d0;}")

            def showMessageList(self):
                if (self.selectedItems()):
                    number = self.itemWidget(self.selectedItems()[0]).number
                    chatWindow.mainWindow.titleText.setText(user_info[number][0])
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.set_content(
                        chatWindow.mainWindow.messageContent(chatWindow.mainWindow, number))
                    self.itemWidget(self.selectedItems()[0]).setNotReceived(0)
                else:
                    chatWindow.mainWindow.content[-1].close()

            def mouseReleaseEvent(self, event):
                chatWindow.mainWindow.retakeMore()
                super().mouseReleaseEvent(event)

        class messageContent(QListWidget):
            class timeBox(QWidget):
                def __init__(self, item, datetime):
                    super().__init__()
                    self.item = item
                    self.text = set_time(datetime)
                    self.initWidget()
                    self.initTimeLabel()

                def initWidget(self):
                    self.resize(750, 60)
                    self.item.setSizeHint(QSize(750, 60))

                def initTimeLabel(self):
                    self.timeLabel = QLabel(self)
                    self.timeLabel.resize(750, 60)
                    self.timeLabel.move(0, 0)
                    self.timeLabel.setText(self.text)
                    self.timeLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                    self.timeLabel.setStyleSheet("font-family: Microsoft YaHei;"
                                                 "font-size: 17px;"
                                                 "color: #aaaaaa;"
                                                 "background-color: transparent")

            class rightTextBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.text_height = 21
                    self.font_size = 10
                    self.startX = 100
                    self.startY = 20
                    self.radius = 8
                    self.width_border = 15
                    self.height_border = 10
                    self.max_length = 400
                    if (message_info[5] == ""):
                        self.text = " "
                    else:
                        self.text = message_info[5]
                    self.sender = message_info[1]
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initAvatarShow()

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(670, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def paintEvent(self, event):
                    text = self.text
                    text_height = self.text_height
                    font_size = self.font_size
                    startX = self.startX
                    startY = self.startY
                    radius = self.radius
                    width_border = self.width_border
                    height_border = self.height_border
                    max_length = self.max_length
                    font = QPainter(self)
                    font.setFont(QFont("Microsoft YaHei", font_size))
                    all_line = []
                    left, right = 0, 0
                    while (left < len(text)):
                        while (right <= len(text) and font.fontMetrics().boundingRect(
                                text[left:right]).width() <= max_length):
                            right += 1
                        right -= 1
                        all_line.append(text[left:right])
                        left = right
                    line_height = font.fontMetrics().boundingRect(text).height()
                    width = min(max_length, font.fontMetrics().boundingRect(text).width()) + width_border * 2
                    height = len(all_line) * line_height + height_border * 2
                    boxWidth, boxHeight = 750, height + startY * 2 + 20
                    self.resize(boxWidth, boxHeight)
                    self.item.setSizeHint(QSize(boxWidth, boxHeight))
                    self.textBox = QPainter(self)
                    brush = QBrush(Qt.SolidPattern)
                    self.textBox.setFont(QFont("Microsoft YaHei", font_size))
                    self.textBox.setPen(QColor("#c9e7ff"))
                    brush.setColor(QColor("#c9e7ff"))
                    self.textBox.setBrush(brush)
                    self.textBox.begin(self)
                    triangle = QPolygon()
                    triangle.setPoints(boxWidth - startX + 10, startY + 20, boxWidth - startX, startY + 20,
                                       boxWidth - startX,
                                       startY + 32)
                    self.textBox.drawPolygon(triangle)
                    self.textBox.drawRect(boxWidth - startX - width + radius, startY + 20, width - radius * 2,
                                          height)
                    self.textBox.drawRect(boxWidth - startX - width, startY + radius + 20, width,
                                          height - radius * 2)
                    self.textBox.drawRect(boxWidth - startX - radius * 2, startY + 20, radius * 2, radius * 2)
                    self.textBox.drawEllipse(boxWidth - startX - radius * 2, startY + height - radius * 2 + 20,
                                             radius * 2, radius * 2)
                    self.textBox.drawEllipse(boxWidth - startX - width, startY + 20, radius * 2, radius * 2)
                    self.textBox.drawEllipse(boxWidth - startX - width, startY + height - radius * 2 + 20,
                                             radius * 2, radius * 2)
                    self.textBox.setPen(QColor("#000000"))
                    for line in all_line:
                        self.textBox.drawText(boxWidth - startX - width + width_border,
                                              startY + height_border + 20 + text_height, line)
                        text_height += line_height
                    self.textBox.end()

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.set_content(
                        chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow, self.sender))

            class leftTextBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.text_height = 21
                    self.font_size = 10
                    self.startX = 100
                    self.startY = 20
                    self.radius = 8
                    self.width_border = 15
                    self.height_border = 10
                    self.max_length = 400
                    if (message_info[5] == ""):
                        self.text = " "
                    else:
                        self.text = message_info[5]
                    self.sender = message_info[1]
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initAvatarShow()
                    self.initNicknameShow()

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(30, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initNicknameShow(self):
                    self.nicknameShow = QLabel(self)
                    self.nicknameShow.resize(750 - self.startX, 30)
                    self.nicknameShow.move(self.startX, 10)
                    self.nicknameShow.setText(self.nickname)
                    self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                    "font-size: 16px;"
                                                    "background-color: transparent;")

                def paintEvent(self, event):
                    text = self.text
                    text_height = self.text_height
                    font_size = self.font_size
                    startX = self.startX
                    startY = self.startY
                    radius = self.radius
                    width_border = self.width_border
                    height_border = self.height_border
                    max_length = self.max_length
                    font = QPainter(self)
                    font.setFont(QFont("Microsoft YaHei", font_size))
                    all_line = []
                    left, right = 0, 0
                    while (left < len(text)):
                        while (right <= len(text) and font.fontMetrics().boundingRect(
                                text[left:right]).width() <= max_length):
                            right += 1
                        right -= 1
                        all_line.append(text[left:right])
                        left = right
                    line_height = font.fontMetrics().boundingRect(text).height()
                    width = min(max_length, font.fontMetrics().boundingRect(text).width()) + width_border * 2
                    height = len(all_line) * line_height + height_border * 2
                    boxWidth, boxHeight = 750, height + startY * 2 + 20
                    self.resize(boxWidth, boxHeight)
                    self.item.setSizeHint(QSize(boxWidth, boxHeight))
                    self.textBox = QPainter(self)
                    brush = QBrush(Qt.SolidPattern)
                    self.textBox.setFont(QFont("Microsoft YaHei", font_size))
                    self.textBox.setPen(QColor("#dddddd"))
                    brush.setColor(QColor("#dddddd"))
                    self.textBox.setBrush(brush)
                    self.textBox.begin(self)
                    triangle = QPolygon()
                    triangle.setPoints(startX - 10, startY + 20, startX, startY + 20, startX, startY + 32)
                    self.textBox.drawPolygon(triangle)
                    self.textBox.drawRect(startX + radius, startY + 20, width - radius * 2, height)
                    self.textBox.drawRect(startX, startY + radius + 20, width, height - radius * 2)
                    self.textBox.drawRect(startX, startY + 20, radius * 2, radius * 2)
                    self.textBox.drawEllipse(startX, startY + height - radius * 2 + 20, radius * 2, radius * 2)
                    self.textBox.drawEllipse(startX + width - radius * 2, startY + 20, radius * 2, radius * 2)
                    self.textBox.drawEllipse(startX + width - radius * 2, startY + height - radius * 2 + 20,
                                             radius * 2, radius * 2)
                    self.textBox.setPen(QColor("#000000"))
                    for line in all_line:
                        self.textBox.drawText(startX + width_border, startY + height_border + text_height + 20,
                                              line)
                        text_height += line_height
                    self.textBox.end()

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            class rightFileBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.startX = 100
                    self.startY = 20
                    self.sender = message_info[1]
                    self.file = message_info[5]
                    self.file_info = get_file_info(self.file)
                    self.file_size = self.file_info[0]
                    self.file_name = self.file_info[1] + self.file_info[2]
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initAvatarShow()
                    self.initFileBox()
                    self.initFileImage()
                    self.initFileName()
                    self.initFileSize()
                    self.initDownloadButton()
                    self.initWindow()

                def initWindow(self):
                    self.resize(750, 200)
                    self.item.setSizeHint(QSize(750, 200))

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(670, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initFileBox(self):
                    self.fileBox = QLabel(self)
                    self.fileBox.resize(320, 140)
                    self.fileBox.move(750 - self.startX - 320, self.startY + 20)
                    self.fileBox.setStyleSheet("background-color: #ffffff;"
                                               "border-radius: 10px;"
                                               "border: 1px solid #dddddd;")

                def initFileImage(self):
                    self.fileImage = QLabel(self)
                    self.fileImage.resize(70, 70)
                    self.fileImage.move(750 - self.startX - 90, self.startY + 40)
                    img = QPixmap("pic/file.png")
                    self.fileImage.setPixmap(img)
                    self.fileImage.setScaledContents(True)
                    self.fileImage.setStyleSheet("background-color: transparent;")

                def initFileName(self):
                    text = "[file] %s" % self.file_name
                    max_length = 150
                    font = QPainter(self)
                    font.setFont(QFont("Microsoft YaHei", 20))
                    all_line = ""
                    left, right = 0, 0
                    while (left < len(text)):
                        while (right <= len(text) and font.fontMetrics().boundingRect(
                                text[left:right]).width() <= max_length):
                            right += 1
                        right -= 1
                        all_line += text[left:right] + "\n"
                        left = right
                    self.fileName = QLabel(self)
                    self.fileName.resize(200, 55)
                    self.fileName.move(750 - self.startX - 300, self.startY + 40)
                    self.fileName.setText(all_line)
                    self.fileName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.fileName.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 20px;"
                                                "background-color: transparent;")

                def initFileSize(self):
                    self.fileSize = QLabel(self)
                    self.fileSize.resize(200, 30)
                    self.fileSize.move(750 - self.startX - 300, self.startY + 125)
                    self.fileSize.setText(set_size(self.file_size))
                    self.fileSize.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.fileSize.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 18px;"
                                                "color: #bbbbbb;"
                                                "background-color: transparent;")

                def initDownloadButton(self):
                    self.downloadButton = QPushButton(self)
                    self.downloadButton.resize(100, 30)
                    self.downloadButton.move(750 - self.startX - 120, self.startY + 120)
                    self.downloadButton.clicked.connect(self.downloadFile)
                    self.downloadButton.setText("Download file")
                    self.downloadButton.setObjectName("downloadButton")
                    self.downloadButton.setStyleSheet("QPushButton#downloadButton{"
                                                      "font-family: Microsoft YaHei;"
                                                      "font-size: 15px;"
                                                      "color: #000000;"
                                                      "background-color: transparent;}"
                                                      "QPushButton#downloadButton:hover{"
                                                      "color: #555555;}"
                                                      "QPushButton#downloadButton:pressed{"
                                                      "color: #777777;}")

                def downloadFile(self):
                    download_file(self.file, "file")
                    os.startfile("file")

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            class leftFileBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.startX = 100
                    self.startY = 20
                    self.sender = message_info[1]
                    self.file = message_info[5]
                    self.file_info = get_file_info(self.file)
                    self.file_size = self.file_info[0]
                    self.file_name = self.file_info[1] + self.file_info[2]
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initAvatarShow()
                    self.initNicknameShow()
                    self.initFileBox()
                    self.initFileImage()
                    self.initFileName()
                    self.initFileSize()
                    self.initDownloadButton()
                    self.initWindow()

                def initWindow(self):
                    self.resize(750, 200)
                    self.item.setSizeHint(QSize(750, 200))

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(30, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initNicknameShow(self):
                    self.nicknameShow = QLabel(self)
                    self.nicknameShow.resize(750 - self.startX, 30)
                    self.nicknameShow.move(self.startX, 10)
                    self.nicknameShow.setText(self.nickname)
                    self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                    "font-size: 16px;"
                                                    "background-color: transparent;")

                def initFileBox(self):
                    self.fileBox = QLabel(self)
                    self.fileBox.resize(320, 140)
                    self.fileBox.move(self.startX, self.startY + 20)
                    self.fileBox.setStyleSheet("background-color: #ffffff;"
                                               "border-radius: 10px;"
                                               "border: 1px solid #dddddd;")

                def initFileImage(self):
                    self.fileImage = QLabel(self)
                    self.fileImage.resize(70, 70)
                    self.fileImage.move(self.startX + 230, self.startY + 40)
                    img = QPixmap("pic/file.png")
                    self.fileImage.setPixmap(img)
                    self.fileImage.setScaledContents(True)
                    self.fileImage.setStyleSheet("background-color: transparent;")

                def initFileName(self):
                    text = "[file] %s" % self.file_name
                    max_length = 150
                    font = QPainter(self)
                    font.setFont(QFont("Microsoft YaHei", 20))
                    all_line = ""
                    left, right = 0, 0
                    while (left < len(text)):
                        while (right <= len(text) and font.fontMetrics().boundingRect(
                                text[left:right]).width() <= max_length):
                            right += 1
                        right -= 1
                        all_line += text[left:right] + "\n"
                        left = right
                    self.fileName = QLabel(self)
                    self.fileName.resize(200, 55)
                    self.fileName.move(self.startX + 20, self.startY + 40)
                    self.fileName.setText(all_line)
                    self.fileName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.fileName.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 20px;"
                                                "background-color: transparent;")

                def initFileSize(self):
                    self.fileSize = QLabel(self)
                    self.fileSize.resize(200, 30)
                    self.fileSize.move(self.startX + 20, self.startY + 125)
                    self.fileSize.setText(set_size(self.file_size))
                    self.fileSize.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.fileSize.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 18px;"
                                                "color: #bbbbbb;"
                                                "background-color: transparent;")

                def initDownloadButton(self):
                    self.downloadButton = QPushButton(self)
                    self.downloadButton.resize(100, 30)
                    self.downloadButton.move(self.startX + 200, self.startY + 120)
                    self.downloadButton.clicked.connect(self.downloadFile)
                    self.downloadButton.setText("Download file")
                    self.downloadButton.setObjectName("downloadButton")
                    self.downloadButton.setStyleSheet("QPushButton#downloadButton{"
                                                      "font-family: Microsoft YaHei;"
                                                      "font-size: 15px;"
                                                      "color: #000000;"
                                                      "background-color: transparent;}"
                                                      "QPushButton#downloadButton:hover{"
                                                      "color: #555555;}"
                                                      "QPushButton#downloadButton:pressed{"
                                                      "color: #777777;}")

                def downloadFile(self):
                    download_file(self.file, "file")
                    os.startfile("file")

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            class rightLinkBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.startX = 100
                    self.startY = 20
                    self.sender = message_info[1]
                    self.link = message_info[5]
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initAvatarShow()
                    self.initLinkBox()
                    self.initLinkImage()
                    self.initLink()
                    self.initOpenLinkButton()
                    self.initWindow()

                def initWindow(self):
                    self.resize(750, 200)
                    self.item.setSizeHint(QSize(750, 200))

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(670, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initLinkBox(self):
                    self.linkBox = QLabel(self)
                    self.linkBox.resize(320, 140)
                    self.linkBox.move(750 - self.startX - 320, self.startY + 20)
                    self.linkBox.setStyleSheet("background-color: #ffffff;"
                                               "border-radius: 10px;"
                                               "border: 1px solid #dddddd;")

                def initLinkImage(self):
                    self.linkImage = QLabel(self)
                    self.linkImage.resize(60, 60)
                    self.linkImage.move(750 - self.startX - 85, self.startY + 45)
                    img = QPixmap("pic/link.png")
                    self.linkImage.setPixmap(img)
                    self.linkImage.setScaledContents(True)
                    self.linkImage.setStyleSheet("background-color: transparent;")

                def initLink(self):
                    text = "[link] %s" % self.link
                    max_length = 150
                    font = QPainter(self)
                    font.setFont(QFont("Microsoft YaHei", 20))
                    all_line = ""
                    left, right = 0, 0
                    while (left < len(text)):
                        while (right <= len(text) and font.fontMetrics().boundingRect(
                                text[left:right]).width() <= max_length):
                            right += 1
                        right -= 1
                        all_line += text[left:right] + "\n"
                        left = right
                    self.linkName = QLabel(self)
                    self.linkName.resize(200, 55)
                    self.linkName.move(750 - self.startX - 300, self.startY + 40)
                    self.linkName.setText(all_line)
                    self.linkName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.linkName.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 20px;"
                                                "background-color: transparent;")

                def initOpenLinkButton(self):
                    self.openLinkButton = QPushButton(self)
                    self.openLinkButton.resize(80, 30)
                    self.openLinkButton.move(750 - self.startX - 100, self.startY + 120)
                    self.openLinkButton.clicked.connect(self.openLink)
                    self.openLinkButton.setText("Open link")
                    self.openLinkButton.setObjectName("openLinkButton")
                    self.openLinkButton.setStyleSheet("QPushButton#openLinkButton{"
                                                      "font-family: Microsoft YaHei;"
                                                      "font-size: 15px;"
                                                      "color: #000000;"
                                                      "background-color: transparent;}"
                                                      "QPushButton#openLinkButton:hover{"
                                                      "color: #555555;}"
                                                      "QPushButton#openLinkButton:pressed{"
                                                      "color: #777777;}")

                def openLink(self):
                    webbrowser.open(self.link)

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            class leftLinkBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.startX = 100
                    self.startY = 20
                    self.sender = message_info[1]
                    self.link = message_info[5]
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initAvatarShow()
                    self.initNicknameShow()
                    self.initLinkBox()
                    self.initLinkImage()
                    self.initLink()
                    self.initOpenLinkButton()
                    self.initWindow()

                def initWindow(self):
                    self.resize(750, 200)
                    self.item.setSizeHint(QSize(750, 200))

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(30, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initNicknameShow(self):
                    self.nicknameShow = QLabel(self)
                    self.nicknameShow.resize(750 - self.startX, 30)
                    self.nicknameShow.move(self.startX, 10)
                    self.nicknameShow.setText(self.nickname)
                    self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                    "font-size: 16px;"
                                                    "background-color: transparent;")

                def initLinkBox(self):
                    self.linkBox = QLabel(self)
                    self.linkBox.resize(320, 140)
                    self.linkBox.move(self.startX, self.startY + 20)
                    self.linkBox.setStyleSheet("background-color: #ffffff;"
                                               "border-radius: 10px;"
                                               "border: 1px solid #dddddd;")

                def initLinkImage(self):
                    self.linkImage = QLabel(self)
                    self.linkImage.resize(60, 60)
                    self.linkImage.move(self.startX + 235, self.startY + 45)
                    img = QPixmap("pic/link.png")
                    self.linkImage.setPixmap(img)
                    self.linkImage.setScaledContents(True)
                    self.linkImage.setStyleSheet("background-color: transparent;")

                def initLink(self):
                    text = "[link] %s" % self.link
                    max_length = 150
                    font = QPainter(self)
                    font.setFont(QFont("Microsoft YaHei", 20))
                    all_line = ""
                    left, right = 0, 0
                    while (left < len(text)):
                        while (right <= len(text) and font.fontMetrics().boundingRect(
                                text[left:right]).width() <= max_length):
                            right += 1
                        right -= 1
                        all_line += text[left:right] + "\n"
                        left = right
                    self.linkName = QLabel(self)
                    self.linkName.resize(200, 55)
                    self.linkName.move(self.startX + 20, self.startY + 40)
                    self.linkName.setText(all_line)
                    self.linkName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    self.linkName.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 20px;"
                                                "background-color: transparent;")

                def initOpenLinkButton(self):
                    self.openLinkButton = QPushButton(self)
                    self.openLinkButton.resize(80, 30)
                    self.openLinkButton.move(self.startX + 220, self.startY + 120)
                    self.openLinkButton.clicked.connect(self.openLink)
                    self.openLinkButton.setText("Open link")
                    self.openLinkButton.setObjectName("openLinkButton")
                    self.openLinkButton.setStyleSheet("QPushButton#openLinkButton{"
                                                      "font-family: Microsoft YaHei;"
                                                      "font-size: 15px;"
                                                      "color: #000000;"
                                                      "background-color: transparent;}"
                                                      "QPushButton#openLinkButton:hover{"
                                                      "color: #555555;}"
                                                      "QPushButton#openLinkButton:pressed{"
                                                      "color: #777777;}")

                def openLink(self):
                    webbrowser.open(self.link)

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            class rightEmojiBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.startX = 100
                    self.startY = 20
                    self.sender = message_info[1]
                    self.emoji = message_info[5]
                    download_file(self.emoji, "data")
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initWidget()
                    self.initAvatarShow()
                    self.initEmojiBox()

                def initWidget(self):
                    self.resize(750, 200)
                    self.item.setSizeHint(QSize(750, 210))

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(670, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initEmojiBox(self):
                    emojiSize = Image.open("data/temp/%s" % self.emoji).size
                    emojiWidth = emojiSize[0]
                    emojiHeight = emojiSize[1]
                    self.emojiBox = QLabel(self)
                    if (emojiWidth > emojiHeight):
                        self.emojiBox.resize(150, 150 / emojiWidth * emojiHeight)
                        self.emojiBox.move(750 - self.startX - 150,
                                           self.startY + (150 - (150 / emojiWidth * emojiHeight)) / 2 + 20)
                    else:
                        self.emojiBox.resize(150 / emojiHeight * emojiWidth, 150)
                        self.emojiBox.move(750 - self.startX - 150 / emojiHeight * emojiWidth, self.startY + 20)
                    self.gif = QMovie("data/temp/%s" % self.emoji)
                    self.emojiBox.setMovie(self.gif)
                    self.emojiBox.setScaledContents(True)
                    self.gif.start()
                    self.emojiBox.setStyleSheet("background-color: transparent;")

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            class leftEmojiBox(QWidget):
                def __init__(self, item, message_info):
                    super().__init__()
                    self.item = item
                    self.startX = 100
                    self.startY = 20
                    self.sender = message_info[1]
                    self.emoji = message_info[5]
                    download_file(self.emoji, "data")
                    self.nickname = user_info[self.sender][0]
                    self.profile_picture = "data/temp/%s" % user_info[self.sender][1]
                    self.initWidget()
                    self.initAvatarShow()
                    self.initNicknameShow()
                    self.initEmojiBox()

                def initWidget(self):
                    self.resize(750, 200)
                    self.item.setSizeHint(QSize(750, 210))

                def initAvatarShow(self):
                    self.avatarShow = QPushButton(self)
                    self.avatarShow.resize(50, 50)
                    self.avatarShow.move(30, self.startY - 5)
                    self.avatarShow.clicked.connect(self.showUserInfo)
                    self.avatarShow.setStyleSheet("border-radius: 25px;"
                                                  "border-image: url(%s);" % self.profile_picture)

                def initNicknameShow(self):
                    self.nicknameShow = QLabel(self)
                    self.nicknameShow.resize(750 - self.startX, 30)
                    self.nicknameShow.move(self.startX, 10)
                    self.nicknameShow.setText(self.nickname)
                    self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;"
                                                    "font-size: 16px;"
                                                    "background-color: transparent;")

                def initEmojiBox(self):
                    emojiSize = Image.open("data/temp/%s" % self.emoji).size
                    emojiWidth = emojiSize[0]
                    emojiHeight = emojiSize[1]
                    self.emojiBox = QLabel(self)
                    if (emojiWidth > emojiHeight):
                        self.emojiBox.resize(150, 150 / emojiWidth * emojiHeight)
                        self.emojiBox.move(self.startX, self.startY + (150 - (150 / emojiWidth * emojiHeight)) / 2 + 20)
                    else:
                        self.emojiBox.resize(150 / emojiHeight * emojiWidth, 150)
                        self.emojiBox.move(self.startX + (150 - 150 / emojiHeight * emojiWidth) / 2, self.startY + 20)
                    self.gif = QMovie("data/temp/%s" % self.emoji)
                    self.emojiBox.setMovie(self.gif)
                    self.emojiBox.setScaledContents(True)
                    self.gif.start()
                    self.emojiBox.setStyleSheet("background-color: transparent;")

                def showUserInfo(self):
                    chatWindow.mainWindow.close_content()
                    chatWindow.mainWindow.content = chatWindow.mainWindow.userInfoContent(chatWindow.mainWindow,
                                                                                          self.sender)

            def __init__(self, parent, number):
                super().__init__(parent)
                self.number = number
                self.chat_message = []
                self.checked_message = len(all_message)
                self.loaded_message = 0
                self.loadMessage()
                self.initWidget()
                self.show()

            def initWidget(self):
                self.resize(750, 765)
                self.move(450, 75)
                self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
                self.verticalScrollBar().valueChanged.connect(self.isTop)
                self.setStyleSheet("QListWidget {background-color: transparent;"
                                   "outline: none;"
                                   "border:0px;}"
                                   "QListWidget:Item:hover{background-color: transparent;}"
                                   "QListWidget:Item:selected{background-color: transparent;}")

            def loadMessage(self):
                self.insert_message = 0
                while (self.checked_message > 0 and self.insert_message < 50):
                    self.checked_message -= 1
                    if (all_message[self.checked_message][1] != account and all_message[self.checked_message][
                        2] != account):
                        number = all_message[self.checked_message][2]
                    elif (all_message[self.checked_message][1] == account):
                        number = all_message[self.checked_message][2]
                    else:
                        number = all_message[self.checked_message][1]
                    if (number == self.number):
                        self.insert_message += 1
                        self.chat_message.append(all_message[self.checked_message])
                for i in range(self.insert_message):
                    self.addBox(self.chat_message, self.loaded_message + i)
                self.loaded_message += self.insert_message

            def addBox(self, message_info, index):
                if (message_info[index][4] == "text"):
                    if (message_info[index][1] == account):
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.rightTextBox(item, message_info[index]))
                    else:
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.leftTextBox(item, message_info[index]))
                elif (message_info[index][4] == "file"):
                    if (message_info[index][1] == account):
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.rightFileBox(item, message_info[index]))
                    else:
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.leftFileBox(item, message_info[index]))
                elif (message_info[index][4] == "link"):
                    if (message_info[index][1] == account):
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.rightLinkBox(item, message_info[index]))
                    else:
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.leftLinkBox(item, message_info[index]))
                elif (message_info[index][4] == "emoji"):
                    if (message_info[index][1] == account):
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.rightEmojiBox(item, message_info[index]))
                    else:
                        item = QListWidgetItem()
                        self.insertItem(0, item)
                        self.setItemWidget(item, self.leftEmojiBox(item, message_info[index]))
                if (index == self.loaded_message + self.insert_message - 1 or compare_time(message_info[index][3],
                                                                                           message_info[index + 1][
                                                                                               3]) > 300):
                    item = QListWidgetItem()
                    self.insertItem(0, item)
                    self.setItemWidget(item, self.timeBox(item, message_info[index][3]))

            def isTop(self):
                if (self.verticalScrollBar().value() == 0):
                    self.loadMessage()

            def mouseReleaseEvent(self, event):
                chatWindow.mainWindow.retakeMore()
                super().mouseReleaseEvent(event)

        class userInfoContent(QWidget):
            def __init__(self, parent, number):
                super().__init__(parent)
                user_info = get_user_info(number)
                self.nickname = user_info[0]
                profile_picture = user_info[1]
                background_picture = user_info[2]
                self.motto = user_info[5]
                download_file(profile_picture, "data")
                download_file(background_picture, "data")
                self.img1 = QPixmap("data/temp/%s" % profile_picture)
                self.img2 = QPixmap("data/temp/%s" % background_picture)
                chatWindow.mainWindow.titleText.setText(self.nickname)
                self.initWidget()
                self.showBackgroundPicture()
                self.showProfilePicture()
                self.showNickname()
                self.showMotto()
                self.show()

            def initWidget(self):
                self.resize(750, 765)
                self.move(450, 75)
                self.setStyleSheet("background-color: transparent;")

            def showBackgroundPicture(self):
                self.backgroundPictureArea = QLabel(self)
                self.backgroundPictureArea.resize(750, 250)
                self.backgroundPictureArea.move(0, 0)
                self.backgroundPictureArea.setPixmap(self.img2)
                self.backgroundPictureArea.setScaledContents(True)

            def showProfilePicture(self):
                self.profilePictureArea = QLabel(self)
                self.profilePictureArea.resize(100, 100)
                self.profilePictureArea.move(75, 200)
                self.profilePictureArea.setPixmap(self.img1)
                self.profilePictureArea.setScaledContents(True)
                self.profilePictureArea.setStyleSheet("background-color: transparent;")

            def showNickname(self):
                self.nicknameArea = QLabel(self)
                self.nicknameArea.resize(560, 50)
                self.nicknameArea.move(190, 200)
                self.nicknameArea.setText(self.nickname)
                self.nicknameArea.setStyleSheet("font-family: Microsoft YaHei;"
                                                "font-size: 30px;"
                                                "color: #ffffff;"
                                                "background-color: transparent;")

            def showMotto(self):
                self.mottoArea = QLabel(self)
                self.mottoArea.resize(545, 100)
                self.mottoArea.move(190, 260)
                self.mottoArea.setWordWrap(True)
                self.mottoArea.setText(self.motto)
                self.mottoArea.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.mottoArea.setStyleSheet("font-family: Microsoft YaHei;"
                                             "font-size: 18px;"
                                             "color: #000000;"
                                             "background-color: transparent;")

            def mouseReleaseEvent(self, event):
                chatWindow.mainWindow.retakeMore()
                super().mouseReleaseEvent(event)

        def __init__(self, window):
            super().__init__(window)
            self.window = window
            feachat.user_info[feachat.account] = get_user_info(feachat.account)
            self.page = ""
            self.list = []
            self.moreFlag = False
            self.initWindow()
            self.initMenuArea()
            self.initListArea()
            self.initContentArea()
            self.initAvatarArea()
            self.initSearchArea()
            self.initTitleArea()
            self.initMenuFilling()
            self.initContentFilling()
            self.initAvatarFilling1()
            self.initAvatarFilling2()
            self.initTitleFilling1()
            self.initTitleFilling2()
            self.initCloseButton()
            self.initMinButton()
            self.initChatsButton()
            self.initContactsButton()
            self.initMomentsButton()
            self.initFavoritesButton()
            self.initMyselfButton()
            self.initFileManagerButton()
            self.initSettingButton()
            self.initlogOutButton()
            self.initAvatar()
            self.initSearchFilling()
            self.initSearchIconArea()
            self.initSearchIcon()
            self.initSearchBox()
            self.initMoreButton()
            self.initTitleText()
            self.titleText.setText("FeaChat")
            self.switchChats()

        def initWindow(self):
            self.width = 1200
            self.height = 840
            self.titleWidth = 1200
            self.titleHeight = 75
            self.resize(self.width, self.height)
            self.window.setWindowTitle("FeaChat")
            self.window.setWindowIcon(QIcon("pic/logo/logo.png"))

        def initMenuArea(self):
            self.menuArea = QLabel(self)
            self.menuArea.resize(75, 840)
            self.menuArea.move(0, 0)
            self.menuArea.setStyleSheet("background-color: #0076F6;"
                                        "border-radius: 10px;")

        def initListArea(self):
            self.listArea = QLabel(self)
            self.listArea.resize(375, 840)
            self.listArea.move(75, 0)
            self.listArea.setStyleSheet("background-color: #ffffff;")

        def initContentArea(self):
            self.contentArea = QLabel(self)
            self.contentArea.resize(750, 840)
            self.contentArea.move(450, 0)
            self.contentArea.setStyleSheet("background-color: #f5f5f5;"
                                           "border-radius: 10px;")

        def initAvatarArea(self):
            self.avaterArea = QLabel(self)
            self.avaterArea.resize(75, 75)
            self.avaterArea.move(0, 0)
            self.avaterArea.setStyleSheet("background-color: #0062cd;"
                                          "border-radius: 10px;")

        def initSearchArea(self):
            self.searchArea = QLabel(self)
            self.searchArea.resize(375, 75)
            self.searchArea.move(75, 0)
            self.searchArea.setStyleSheet("background-color: #f5f5f5")

        def initTitleArea(self):
            self.titleArea = QLabel(self)
            self.titleArea.resize(750, 75)
            self.titleArea.move(450, 0)
            self.titleArea.setStyleSheet("background-color: #e5e5e5;"
                                         "border-radius: 10px;")

        def initMenuFilling(self):
            self.menuFilling = QLabel(self)
            self.menuFilling.resize(10, 10)
            self.menuFilling.move(65, 830)
            self.menuFilling.setStyleSheet("background-color: #0076F6;")

        def initContentFilling(self):
            self.contentFilling = QLabel(self)
            self.contentFilling.resize(10, 840)
            self.contentFilling.move(450, 0)
            self.contentFilling.setStyleSheet("background-color: #f5f5f5;")

        def initAvatarFilling1(self):
            self.avaterFilling1 = QLabel(self)
            self.avaterFilling1.resize(10, 75)
            self.avaterFilling1.move(65, 0)
            self.avaterFilling1.setStyleSheet("background-color: #0062cd;")

        def initAvatarFilling2(self):
            self.avaterFilling2 = QLabel(self)
            self.avaterFilling2.resize(10, 10)
            self.avaterFilling2.move(0, 65)
            self.avaterFilling2.setStyleSheet("background-color: #0062cd;")

        def initTitleFilling1(self):
            self.titleFilling1 = QLabel(self)
            self.titleFilling1.resize(10, 75)
            self.titleFilling1.move(450, 0)
            self.titleFilling1.setStyleSheet("background-color: #e5e5e5;")

        def initTitleFilling2(self):
            self.titleFilling2 = QLabel(self)
            self.titleFilling2.resize(10, 10)
            self.titleFilling2.move(1190, 65)
            self.titleFilling2.setStyleSheet("background-color: #e5e5e5;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.resize(45, 35)
            self.closeButton.move(1150, 5)
            self.closeButton.setText("×")
            self.closeButton.clicked.connect(self.window.close)
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;"
                                           "font-size: 25px;"
                                           "color: #555555;"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-radius: 5px;}"
                                           "QPushButton#closeButton:hover{background-color: #d1d1d1;}"
                                           "QPushButton#closeButton:pressed{background-color: #b9b9b9;}")

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.resize(45, 35)
            self.minButton.move(1100, 5)
            self.minButton.setText("-")
            self.minButton.clicked.connect(self.window.showMinimized)
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #555555;"
                                         "background-color: transparent;"
                                         "border: 0px;"
                                         "border-radius: 5px;}"
                                         "QPushButton#minButton:hover{background-color: #d1d1d1;}"
                                         "QPushButton#minButton:pressed{background-color: #b9b9b9;}")

        def initChatsButton(self):
            self.chatsButton = QPushButton(self)
            self.chatsButton.resize(75, 75)
            self.chatsButton.move(0, 75)
            self.chatsButton.setToolTip("Chats")
            self.chatsButton.clicked.connect(self.switchChats)
            self.chatsButton.setObjectName("chatsButton")
            self.chatsButton.setStyleSheet("QPushButton#chatsButton{"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-image: url(pic/chats1.png);}"
                                           "QPushButton#chatsButton:hover{background-color: #006bdf;}"
                                           "QPushButton#chatsButton:pressed{background-color: #0062cd;}")

        def initContactsButton(self):
            self.contactsButton = QPushButton(self)
            self.contactsButton.resize(75, 75)
            self.contactsButton.move(0, 150)
            self.contactsButton.clicked.connect(self.switchContacts)
            self.contactsButton.setToolTip("Contacts")
            self.contactsButton.setObjectName("contactsButton")
            self.contactsButton.setStyleSheet("QPushButton#contactsButton{"
                                              "background-color: transparent;"
                                              "border: 0px;"
                                              "border-image: url(pic/contacts1.png);}"
                                              "QPushButton#contactsButton:hover{background-color: #006bdf;}"
                                              "QPushButton#contactsButton:pressed{background-color: #0062cd;}")

        def initMomentsButton(self):
            self.momentsButton = QPushButton(self)
            self.momentsButton.resize(75, 75)
            self.momentsButton.move(0, 225)
            self.momentsButton.clicked.connect(self.switchMoments)
            self.momentsButton.setToolTip("Moments")
            self.momentsButton.setObjectName("momentsButton")
            self.momentsButton.setStyleSheet("QPushButton#momentsButton{"
                                             "background-color: transparent;"
                                             "border: 0px;"
                                             "border-image: url(pic/moments1.png);}"
                                             "QPushButton#momentsButton:hover{background-color: #006bdf;}"
                                             "QPushButton#momentsButton:pressed{background-color: #0062cd;}")

        def initFavoritesButton(self):
            self.favoritesButton = QPushButton(self)
            self.favoritesButton.resize(75, 75)
            self.favoritesButton.move(0, 300)
            self.favoritesButton.clicked.connect(self.switchFavorites)
            self.favoritesButton.setToolTip("Favorites")
            self.favoritesButton.setObjectName("favoritesButton")
            self.favoritesButton.setStyleSheet("QPushButton#favoritesButton{"
                                               "background-color: transparent;"
                                               "border: 0px;"
                                               "border-image: url(pic/favourites1.png);}"
                                               "QPushButton#favoritesButton:hover{background-color: #006bdf;}"
                                               "QPushButton#favoritesButton:pressed{background-color: #0062cd;}")

        def initMyselfButton(self):
            self.myselfButton = QPushButton(self)
            self.myselfButton.resize(75, 75)
            self.myselfButton.move(0, 375)
            self.myselfButton.clicked.connect(self.switchMyself)
            self.myselfButton.setToolTip("Myself")
            self.myselfButton.setObjectName("myselfButton")
            self.myselfButton.setStyleSheet("QPushButton#myselfButton{"
                                            "background-color: transparent;"
                                            "border: 0px;"
                                            "border-image: url(pic/myself1.png);}"
                                            "QPushButton#myselfButton:hover{background-color: #006bdf;}"
                                            "QPushButton#myselfButton:pressed{background-color: #0062cd;}")

        def initFileManagerButton(self):
            self.fileManagerButton = QPushButton(self)
            self.fileManagerButton.resize(75, 75)
            self.fileManagerButton.move(0, 575)
            self.fileManagerButton.clicked.connect(self.openFileManager)
            self.fileManagerButton.setToolTip("File Manager")
            self.fileManagerButton.setObjectName("fileManagerButton")
            self.fileManagerButton.setStyleSheet("QPushButton#fileManagerButton{"
                                                 "background-color: transparent;"
                                                 "border: 0px;"
                                                 "border-image: url(pic/file manager.png);}"
                                                 "QPushButton#fileManagerButton:hover{background-color: #006bdf;}"
                                                 "QPushButton#fileManagerButton:pressed{background-color: #0062cd;}")

        def initSettingButton(self):
            self.settingButton = QPushButton(self)
            self.settingButton.resize(75, 75)
            self.settingButton.move(0, 650)
            self.settingButton.clicked.connect(self.openSetting)
            self.settingButton.setToolTip("Setting")
            self.settingButton.setObjectName("settingButton")
            self.settingButton.setStyleSheet("QPushButton#settingButton{"
                                             "background-color: transparent;"
                                             "border: 0px;"
                                             "border-image: url(pic/setting.png);}"
                                             "QPushButton#settingButton:hover{background-color: #006bdf;}"
                                             "QPushButton#settingButton:pressed{background-color: #0062cd;}")

        def initlogOutButton(self):
            self.logOutButton = QPushButton(self)
            self.logOutButton.resize(75, 75)
            self.logOutButton.move(0, 725)
            self.logOutButton.clicked.connect(self.logOut)
            self.logOutButton.setToolTip("Log out")
            self.logOutButton.setObjectName("logOutButton")
            self.logOutButton.setStyleSheet("QPushButton#logOutButton{"
                                            "background-color: transparent;"
                                            "border: 0px;"
                                            "border-image: url(pic/log out.png);}"
                                            "QPushButton#logOutButton:hover{background-color: #006bdf;}"
                                            "QPushButton#logOutButton:pressed{background-color: #0062cd;}")

        def initAvatar(self):
            self.avatar = QLabel(self)
            self.avatar.resize(50, 50)
            self.avatar.move(12.5, 12.5)
            avatar = self.parent.user_info[self.parent.account][1]
            download_file(avatar, "data")
            profile_picture = avatar
            self.avatar.setPixmap(QPixmap("data/temp/%s" % profile_picture))
            self.avatar.setScaledContents(True)
            self.avatar.setStyleSheet("background-color: transparent;")

        def initSearchIconArea(self):
            self.searchIconArea = QLabel(self)
            self.searchIconArea.resize(40, 40)
            self.searchIconArea.move(100, 17.5)
            self.searchIconArea.setStyleSheet("background-color: #e0e0e0;"
                                              "border: 0px;"
                                              "border-radius: 5px;")

        def initSearchIcon(self):
            self.searchIcon = QLabel(self)
            self.searchIcon.resize(23, 23)
            self.searchIcon.move(110, 26)
            self.searchIcon.setPixmap(QPixmap("pic/search.png"))
            self.searchIcon.setScaledContents(True)
            self.searchIcon.setStyleSheet("background-color: #e0e0e0;"
                                          "border: 0px;"
                                          "border-radius: 5px;")

        def initSearchBox(self):
            self.searchBox = QLineEdit(self)
            self.searchBox.resize(225, 40)
            self.searchBox.move(140, 17.5)
            self.searchBox.textChanged.connect(self.search)
            self.searchBox.setPlaceholderText("Search");
            self.searchBox.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "background-color: #e0e0e0;"
                                         "border: 0px;")

        def initSearchFilling(self):
            self.searchFilling = QLineEdit(self)
            self.searchFilling.resize(245, 40)
            self.searchFilling.move(130, 17.5)
            self.searchFilling.setPlaceholderText("Search");
            self.searchFilling.setStyleSheet("background-color: #e0e0e0;"
                                             "border: 0px;"
                                             "border-radius: 5px;")

        def initMoreButton(self):
            self.moreButton = QPushButton(self)
            self.moreButton.resize(40, 40)
            self.moreButton.move(385, 17.5)
            self.moreButton.setObjectName("moreButton")
            self.moreButton.setToolTip("More")
            self.moreButton.clicked.connect(self.clickedMore)
            self.moreButton.setStyleSheet("QPushButton#moreButton{"
                                          "background-color: #e0e0e0;"
                                          "border: 0px;"
                                          "border-radius: 5px;"
                                          "border-image: url(pic/more.png);}"
                                          "QPushButton#moreButton:hover{background-color: #d1d1d1;}"
                                          "QPushButton#moreButton:pressed{background-color: #b9b9b9;}")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.resize(610, 75)
            self.titleText.move(480, 0)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #000000;"
                                         "background-color: transparent;")

        def expandMore(self):
            self.moreFlag = True
            self.more = self.expandMoreArea(self)
            self.moreButton.setStyleSheet("QPushButton#moreButton{"
                                          "background-color: #b9b9b9;"
                                          "border: 0px;"
                                          "border-radius: 5px;"
                                          "border-image: url(pic/more.png);}")

        def retakeMore(self):
            try:
                self.moreFlag = False
                self.more.close()
                self.moreButton.setStyleSheet("QPushButton#moreButton{"
                                              "background-color: #e0e0e0;"
                                              "border: 0px;"
                                              "border-radius: 5px;"
                                              "border-image: url(pic/more.png);}"
                                              "QPushButton#moreButton:hover{background-color: #d1d1d1;}"
                                              "QPushButton#moreButton:pressed{background-color: #b9b9b9;}")
            except:
                pass

        def setButtonStyle(self):
            self.chatsButton.setStyleSheet("QPushButton#chatsButton{"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-image: url(pic/chats1.png);}"
                                           "QPushButton#chatsButton:hover{background-color: #006bdf;}"
                                           "QPushButton#chatsButton:pressed{background-color: #0062cd;}")
            self.contactsButton.setStyleSheet("QPushButton#contactsButton{"
                                              "background-color: transparent;"
                                              "border: 0px;"
                                              "border-image: url(pic/contacts1.png);}"
                                              "QPushButton#contactsButton:hover{background-color: #006bdf;}"
                                              "QPushButton#contactsButton:pressed{background-color: #0062cd;}")
            self.momentsButton.setStyleSheet("QPushButton#momentsButton{"
                                             "background-color: transparent;"
                                             "border: 0px;"
                                             "border-image: url(pic/moments1.png);}"
                                             "QPushButton#momentsButton:hover{background-color: #006bdf;}"
                                             "QPushButton#momentsButton:pressed{background-color: #0062cd;}")
            self.favoritesButton.setStyleSheet("QPushButton#favoritesButton{"
                                               "background-color: transparent;"
                                               "border: 0px;"
                                               "border-image: url(pic/favourites1.png);}"
                                               "QPushButton#favoritesButton:hover{background-color: #006bdf;}"
                                               "QPushButton#favoritesButton:pressed{background-color: #0062cd;}")
            self.myselfButton.setStyleSheet("QPushButton#myselfButton{"
                                            "background-color: transparent;"
                                            "border: 0px;"
                                            "border-image: url(pic/myself1.png);}"
                                            "QPushButton#myselfButton:hover{background-color: #006bdf;}"
                                            "QPushButton#myselfButton:pressed{background-color: #0062cd;}")
            if (self.page == "Chats"):
                self.chatsButton.setStyleSheet("QPushButton#chatsButton{"
                                               "background-color: #0062cd;"
                                               "border: 0px;"
                                               "border-image: url(pic/chats2.png);}")
            if (self.page == "Contacts"):
                self.contactsButton.setStyleSheet("QPushButton#contactsButton{"
                                                  "background-color: #0062cd;"
                                                  "border: 0px;"
                                                  "border-image: url(pic/contacts2.png);}")
            if (self.page == "Moments"):
                self.momentsButton.setStyleSheet("QPushButton#momentsButton{"
                                                 "background-color: #0062cd;"
                                                 "border: 0px;"
                                                 "border-image: url(pic/moments2.png);}")
            if (self.page == "Favourites"):
                self.favoritesButton.setStyleSheet("QPushButton#favoritesButton{"
                                                   "background-color: #0062cd;"
                                                   "border: 0px;"
                                                   "border-image: url(pic/favourites2.png);}")
            if (self.page == "Myself"):
                self.myselfButton.setStyleSheet("QPushButton#myselfButton{"
                                                "background-color: #0062cd;"
                                                "border: 0px;"
                                                "border-image: url(pic/myself2.png);}")

        def switchChats(self):
            self.page = "Chats"
            self.setButtonStyle()
            self.retakeMore()
            self.close_list()
            self.close_content()
            self.titleText.setText("Chats")

        def switchContacts(self):
            self.page = "Contacts"
            self.setButtonStyle()
            self.retakeMore()
            self.close_list()
            self.close_content()
            self.titleText.setText("Contacts")

        def switchMoments(self):
            self.page = "Moments"
            self.setButtonStyle()
            self.retakeMore()
            self.close_list()
            self.close_content()
            self.titleText.setText("Moments")

        def switchFavorites(self):
            self.page = "Favourites"
            self.setButtonStyle()
            self.retakeMore()
            self.close_list()
            self.close_content()
            self.titleText.setText("Favourites")

        def switchMyself(self):
            self.page = "Myself"
            self.setButtonStyle()
            self.retakeMore()
            self.close_list()
            self.close_content()
            self.titleText.setText("Myself")

        def openSetting(self):
            self.retakeMore()
            if ("settingWindow" in vars(self) and self.settingWindow.isVisible()):
                self.settingWindow.showNormal()
                self.settingWindow.raise_()
            else:
                self.settingWindow = uiShadow(settingUi)
                app.exec_()

        def openFileManager(self):
            self.new_message(("0", "p000000000", "p000000001", "2020-12-29 11:02:45", "link", "1"))
            self.retakeMore()
            if ("fileManagerWindow" in vars(self) and self.fileManagerWindow.isVisible()):
                self.fileManagerWindow.showNormal()
                self.fileManagerWindow.raise_()
            else:
                self.fileManagerWindow = uiShadow(fileManagerUi)
                app.exec_()

        def logOut(self):
            self.retakeMore()
            self.messageBox = uiShadow(messageBoxUi, "Log out", "You won't be notified of any new messages after "
                                                                "logging out. Confirm to log out.", sys.exit)

        def search(self):
            self.retakeMore()
            if (self.list and isinstance(self.list[-1], self.searchList)):
                self.remove_list()
            if (self.searchBox.text() != ""):
                self.set_list(self.searchList(self))

        def clickedMore(self):
            if (not (self.moreFlag)):
                self.expandMore()
            else:
                self.retakeMore()

        def close_list(self):
            try:
                self.searchBox.setText("")
            except:
                pass
            for i in range(len(self.list) - 1, -1, -1):
                self.list[i].close()
                del self.list[i]

        def set_list(self, layout):
            self.list.append(layout)

        def remove_list(self):
            self.list[-1].close()
            del self.list[-1]

        def close_content(self):
            if ("content" in vars(self)):
                self.content.close()

        def set_content(self, layout):
            self.content = layout

        def new_message(self, message):
            if (message[1] == account):
                _thread.start_new_thread(play_sound, ("voice/sent.wav",))
            else:
                _thread.start_new_thread(play_sound, ("voice/received.wav",))
            all_message.append(message)
            if (self.page == "Chats"):
                if (message[1] != account and message[2] != account):
                    number = message[2]
                elif (message[1] == account):
                    number = message[2]
                else:
                    number = message[1]
                if (not (number in user_info)):
                    user_info[number] = get_user_info(number)
                    download_file(user_info[number][1], "data")
                    download_file(user_info[number][2], "data")
                if ("content" in vars(self) and str(type(self.content)) == "<class '__main__.chatUi.messageContent'>"
                        and number == self.content.number):
                    if (number in self.list[0].number_item):
                        item = self.list[0].number_item[number]
                        self.list[0].takeItem(self.list[0].row(item))
                    item = QListWidgetItem()
                    self.list[0].number_item[number] = item
                    self.list[0].insertItem(0, item)
                    self.list[0].setItemWidget(item, self.list[0].chatsSelectBox(item, number, message))
                    self.list[0].setCurrentItem(self.list[0].number_item[number])
                    self.content.chat_message.insert(0, message)
                    message_info = self.content.chat_message
                    index = 0
                    if (self.content.loaded_message == 0
                            or compare_time(message_info[index][3], message_info[index + 1][3]) > 300):
                        item = QListWidgetItem()
                        self.content.addItem(item)
                        self.content.setItemWidget(item, self.content.timeBox(item, message_info[index][3]))
                    if (message_info[index][4] == "text"):
                        if (message_info[index][1] == account):
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.rightTextBox(item, message_info[index]))
                        else:
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.leftTextBox(item, message_info[index]))
                    elif (message_info[index][4] == "file"):
                        if (message_info[index][1] == account):
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.rightFileBox(item, message_info[index]))
                        else:
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.leftFileBox(item, message_info[index]))
                    elif (message_info[index][4] == "link"):
                        if (message_info[index][1] == account):
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.rightLinkBox(item, message_info[index]))
                        else:
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.leftLinkBox(item, message_info[index]))
                    elif (message_info[index][4] == "emoji"):
                        if (message_info[index][1] == account):
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.rightEmojiBox(item, message_info[index]))
                        else:
                            item = QListWidgetItem()
                            self.content.addItem(item)
                            self.content.setItemWidget(item, self.content.leftEmojiBox(item, message_info[index]))
                    self.content.loaded_message += 1
                else:
                    notReceived = 0
                    if (number in self.list[0].number_item):
                        item = self.list[0].number_item[number]
                        notReceived = self.list[0].itemWidget(item).notReceived
                        self.list[0].takeItem(self.list[0].row(item))
                    item = QListWidgetItem()
                    self.list[0].number_item[number] = item
                    self.list[0].insertItem(0, item)
                    self.list[0].setItemWidget(item, self.list[0].chatsSelectBox(item, number, message))
                    if (message[1] != account):
                        self.list[0].itemWidget(item).setNotReceived(notReceived + 1)

        def mouseReleaseEvent(self, event):
            self.retakeMore()
            super().mouseReleaseEvent(event)

    class addFriendsUi(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = "Add Friends"
            self.initWindow()
            self.initContent()
            self.initTitleText()
            self.initCloseButton()
            self.initMinButton()

        def initWindow(self):
            self.width = 800
            self.height = 600
            self.titleWidth = 800
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")

        def initContent(self):
            self.content = QLabel(self)
            self.content.resize(800, 600)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;"
                                       "border-radius: 10px;")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "color: #727272;"
                                         "background-color: transparent;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30)
            self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×")
            self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;"
                                           "font-size: 25px;"
                                           "color: #727272;"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-radius: 5px;}"
                                           "QPushButton#closeButton:hover{background-color: #e1e1e1;}"
                                           "QPushButton#closeButton:pressed{background-color: #c9c9c9;}")

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30)
            self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-")
            self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #727272;"
                                         "background-color: transparent;"
                                         "border: 0px;"
                                         "border-radius: 5px;}"
                                         "QPushButton#minButton:hover{background-color: #e1e1e1}"
                                         "QPushButton#minButton:pressed{background-color: #c9c9c9;}")

    class createGroupUi(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = "Create Group"
            self.initWindow()
            self.initContent()
            self.initTitleText()
            self.initCloseButton()
            self.initMinButton()

        def initWindow(self):
            self.width = 800
            self.height = 600
            self.titleWidth = 800
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")

        def initContentArea(self):
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;"
                                       "border-radius: 10px;")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "color: #727272;"
                                         "background-color: transparent;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30)
            self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×")
            self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;"
                                           "font-size: 25px;"
                                           "color: #727272;"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-radius: 5px;}"
                                           "QPushButton#closeButton:hover{background-color: #e1e1e1;}"
                                           "QPushButton#closeButton:pressed{background-color: #c9c9c9;}")

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30)
            self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-")
            self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #727272;"
                                         "background-color: transparent;"
                                         "border: 0px;"
                                         "border-radius: 5px;}"
                                         "QPushButton#minButton:hover{background-color: #e1e1e1}"
                                         "QPushButton#minButton:pressed{background-color: #c9c9c9;}")

    class shareMomentsUi(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = "Share Moments"
            self.initWindow()
            self.initContent()
            self.initTitleText()
            self.initCloseButton()
            self.initMinButton()

        def initWindow(self):
            self.width = 800
            self.height = 600
            self.titleWidth = 800
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")

        def initContent(self):
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;"
                                       "border-radius: 10px;")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "color: #727272;"
                                         "background-color: transparent;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30)
            self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×")
            self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;"
                                           "font-size: 25px;"
                                           "color: #727272;"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-radius: 5px;}"
                                           "QPushButton#closeButton:hover{background-color: #e1e1e1;}"
                                           "QPushButton#closeButton:pressed{background-color: #c9c9c9;}")

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30)
            self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-")
            self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #727272;"
                                         "background-color: transparent;"
                                         "border: 0px;"
                                         "border-radius: 5px;}"
                                         "QPushButton#minButton:hover{background-color: #e1e1e1}"
                                         "QPushButton#minButton:pressed{background-color: #c9c9c9;}")

    class settingUi(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = "Setting"
            self.initWindow()
            self.initContent()
            self.initTitleText()
            self.initCloseButton()
            self.initMinButton()

        def initWindow(self):
            self.width = 800
            self.height = 600
            self.titleWidth = 800
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")

        def initContent(self):
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;"
                                       "border-radius: 10px;")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "color: #727272;"
                                         "background-color: transparent;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30)
            self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×")
            self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;"
                                           "font-size: 25px;"
                                           "color: #727272;"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-radius: 5px;}"
                                           "QPushButton#closeButton:hover{background-color: #e1e1e1;}"
                                           "QPushButton#closeButton:pressed{background-color: #c9c9c9;}")

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30)
            self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-")
            self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #727272;"
                                         "background-color: transparent;"
                                         "border: 0px;"
                                         "border-radius: 5px;}"
                                         "QPushButton#minButton:hover{background-color: #e1e1e1}"
                                         "QPushButton#minButton:pressed{background-color: #c9c9c9;}")

    class fileManagerUi(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = "File Manager"
            self.initWindow()
            self.initContent()
            self.initTitleText()
            self.initCloseButton()
            self.initMinButton()

        def initWindow(self):
            self.width = 800
            self.height = 600
            self.titleWidth = 800
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")

        def initContent(self):
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;"
                                       "border-radius: 10px;")

        def initTitleText(self):
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "color: #727272;"
                                         "background-color: transparent;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30)
            self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×")
            self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;"
                                           "font-size: 25px;"
                                           "color: #727272;"
                                           "background-color: transparent;"
                                           "border: 0px;"
                                           "border-radius: 5px;}"
                                           "QPushButton#closeButton:hover{background-color: #e1e1e1;}"
                                           "QPushButton#closeButton:pressed{background-color: #c9c9c9;}")

        def initMinButton(self):
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30)
            self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-")
            self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize")
            self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;"
                                         "font-size: 30px;"
                                         "color: #727272;"
                                         "background-color: transparent;"
                                         "border: 0px;"
                                         "border-radius: 5px;}"
                                         "QPushButton#minButton:hover{background-color: #e1e1e1}"
                                         "QPushButton#minButton:pressed{background-color: #c9c9c9;}")

    class messageBoxUi(QWidget):
        width = 500
        height = 300
        titleWidth = 500
        titleHeight = 40

        def __init__(self, window,parent, title, message, event):
            super().__init__(window)
            self.window=window
            self.parent = parent
            self.initWindow(title)
            self.initContent()
            self.initTitleText(title)
            self.initMessageText(message)
            self.initCloseButton()
            self.initConfirmButton(event)
            self.initCancelButton()
            self.show()

        def initWindow(self, title):
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(title)
            self.window.setWindowModality(Qt.ApplicationModal)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet(feachat.getStyleSheet("messageBoxUi"))

        def initContent(self):
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;"
                                       "border-radius: 10px;")

        def initTitleText(self, title):
            self.titleText = QLabel(self)
            self.titleText.setGeometry(15, 0,485, 40)
            self.titleText.setText(title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;"
                                         "font-size: 20px;"
                                         "color: #727272;"
                                         "background-color: transparent;")

        def initMessageText(self, message):
            self.messageText = QLabel(self)
            self.messageText.setGeometry(20, 40,460, 200)
            self.messageText.setText(message)
            self.messageText.setWordWrap(True)
            self.messageText.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.messageText.setStyleSheet("font-family: Microsoft YaHei;"
                                           "font-size: 20px;"
                                           "color: #000000;"
                                           "background-color: transparent;")

        def initCloseButton(self):
            self.closeButton = QPushButton(self)
            self.closeButton.setGeometry(self.width - 45, 5,40, 30)
            self.closeButton.setText("×")
            self.closeButton.setObjectName("closeButton")
            self.closeButton.clicked.connect(self.window.close)

        def initConfirmButton(self, event):
            self.confirmButton = QPushButton(self)
            self.confirmButton.setGeometry(250, 240,100, 40)
            self.confirmButton.setText("Confirm")
            self.confirmButton.setObjectName("confirmButton")
            self.confirmButton.clicked.connect(event)

        def initCancelButton(self):
            self.cancelButton = QPushButton(self)
            self.cancelButton.setGeometry(370, 240,100, 40)
            self.cancelButton.setText("Cancel")
            self.cancelButton.setObjectName("cancelButton")
            self.cancelButton.clicked.connect(self.window.close)

    def __init__(self):
        self.name = "FeaChat"
        self.app = self.uiSetting()
        self.hostname = socket.gethostname()
        self.ipAddress = socket.gethostbyname(self.hostname)
        self.macAddress = self.getMacAddress()
        self.userInfo = self.readLocalData("user info")
        self.connect = False

    def connectServer(self, host, port):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((host, port))
            self.connect = True
        except Exception as ex:
            print(ex)
            pass

    def request(self,*request):
        if (not self.connect): return (False, "Server not connected")
        self.server.send(repr(request).encode("utf-8"))
        return eval(self.server.recv(1024).decode("utf-8"))

    def uiSetting(self):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.name)
        app = QApplication(sys.argv)
        app.setEffectEnabled(Qt.UI_AnimateCombo, False)
        return app

    def getMacAddress(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[i:i + 2] for i in range(0, 11, 2)])

    def getStyleSheet(self, file):
        return open(f"style/{file}.qss").read()

    def cropCircle(self, img, width):
        square = img.resize((width, width))
        mask = Image.new("L", (width, width), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, width), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        result = square.copy()
        result.putalpha(mask)
        return result

    def readLocalData(self, name):
        file = open("data/local/%s.fct" % name, "r")
        data = eval(file.read())
        file.close()
        return data

    def writeLocalData(self, name, data):
        file = open("data/local/%s.fct" % name, "w")
        file.write(repr(data))
        file.close()

    def getUserInfo(self, number):
        if (not (number in self.userInfo)):
            result = self.update_user_info(number)
            if(result[0]==False): return
        return self.userInfo[number]

    def updateUserInfo(self, number):
        request = self.request("getUserInfo", number)
        if(request[0]==False): return request[1]
        self.userInfo[number] = request[1]
        self.write_data("user info", self.userInfo)

    def modifyUserInfo(self, number, type, value):
        self.request("modifyUserInfo", number, type, value)

    def getTempFile(self, id):
        return

    def uploadFile(self, path):
        request = self.request("uploadFile", *self.readFile(path))
        return request.responseInfo

    def downloadFile(self, id):
        return

    def readFile(self, path):
        size = os.path.getsize(path)
        file = os.path.basename(path)
        name = os.path.splitext(file)[0]
        extension = os.path.splitext(file)[-1]
        file = open(path, "rb")
        data = base64.b64encode(file.read()).decode("utf-8")
        file.close()
        return (size, name, extension, data)

    '''
    def split_time(self, datetime):
        return time.strptime(datetime, "%Y-%m-%d %H:%M:%S")

    def format_time(self, datetime):
        datetime = list(self.split_time(datetime))[:6]
        time_now = list(time.localtime(time.time()))[:6]
        if (datetime[0] != time_now[0]):
            type = "year"
        elif (datetime[1:3] != time_now[1:3]):
            type = "month"
        else:
            type = "day"
        datetime[4] = str(datetime[4]).rjust(2, "0")
        if (type == "year"):
            if (datetime[3] >= 12):
                if (datetime[3] > 12):
                    datetime[3] -= 12
                return "%s-%s-%s %s:%s PM" % tuple(map(str, datetime[:5]))
            else:
                return "%s-%s-%s %s:%s AM" % tuple(map(str, datetime[:5]))
        elif (type == "month"):
            if (datetime[3] >= 12):
                if (datetime[3] > 12):
                    datetime[3] -= 12
                return "%s-%s %s:%s PM" % tuple(map(str, datetime[1:5]))
            else:
                return "%s-%s %s:%s AM" % tuple(map(str, datetime[1:5]))
        else:
            if (datetime[3] >= 12):
                if (datetime[3] > 12):
                    datetime[3] -= 12
                return "%s:%s PM" % tuple(map(str, datetime[3:5]))
            else:
                return "%s:%s AM" % tuple(map(str, datetime[3:5]))

    def compare_time(self, datetime1, datetime2):
        datetime1 = self.split_time(datetime1)
        datetime2 = self.split_time(datetime2)
        return time.mktime(datetime1) - time.mktime(datetime2)

    def format_size(self, size):
        unit = ["B", "KB", "MB", "GB", "TB"]
        count = 0
        while (size >= 1024):
            size /= 1024
            count += 1
        return str(round(size, 1)) + unit[count]

    def play_sound(self, file_path):
        global voice_flag
        try:
            if (voice_flag == False):
                voice_flag = True
                playsound.playsound(file_path)
                voice_flag = False
        except:
            voice_flag = True
            playsound.playsound(file_path)
            voice_flag = False

    def get_file_info(self, id):
        self.server.send(self.set_data("file_info", id))
        return self.get_feedback()

    def download_file(self, number, type):
        self.server.send(self.set_data("download", number))
        result = self.get_feedback()
        size, name, extension, data = result
        if (type == "data"):
            file = open("data/temp/%s" % number, "wb")
        else:
            file_name = name + extension
            dir_files = os.listdir("file")
            count = 0
            while (file_name in dir_files):
                count += 1
                file_name = "%s(%s)%s" % (name, str(count), extension)
            file = open("file/%s" % file_name, "wb")
        file.write(base64.b64decode(data.encode("utf-8")))
        file.close()
    '''


if (__name__ == "__main__"):
    feachat = feachatUi()
    _thread.start_new_thread(feachat.connectServer,(feachat.ipAddress, 8888))
    feachat.request("connect", feachat.hostname, feachat.macAddress)
    feachat.loginWindow = feachatUi.uiShadow(feachatUi.loginUi)
