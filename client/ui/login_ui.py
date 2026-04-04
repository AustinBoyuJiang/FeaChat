# _*_coding:utf-8_*_

import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core
from core import DEV_MODE


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

            def initNumberShow(self):
                self.numberShow = QLabel(self)
                self.numberShow.setGeometry(70, 10, 160, 20)
                self.numberShow.setText(self.number)
                self.numberShow.setStyleSheet("font-family: Microsoft YaHei; font-size: 14px; color: #333333; background: transparent;")

            def initNicknameShow(self):
                pass  # 暂无昵称缓存，留空

            def initRemoveButton(self):
                self.removeButton = QPushButton(self)
                self.removeButton.setText("x")
                self.removeButton.setGeometry(255, 15, 30, 30)
                self.removeButton.clicked.connect(self.remove)

            def remove(self):
                self.parent.parent.switchRemoveAccountPage(self.number)

            def eventFilter(self, object, event):
                if event.type() == QEvent.Enter:
                    self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                    self.eventFlag = True
                elif event.type() == QEvent.Leave:
                    self.itemArea.setStyleSheet("background-color: #ebebeb;")
                    self.eventFlag = False
                if self.parent.numberEdit.lineEdit().text() == self.number:
                    self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                elif not self.eventFlag:
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
            self.logoImage.setPixmap(QPixmap("pic/logo/logo.png"))

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
            self.rememberPasswordButton.setChecked(core.feachat.readLocalData("remember password"))
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
            if self.parent.number in self.parent.loginHistory:
                self.passwordEdit.setText(self.parent.loginHistory[self.parent.number])

        def passwordChanged(self):
            self.parent.hidePromptInformation()
            self.parent.password = self.passwordEdit.text()

        def hidePassword(self):
            self.parent.hidePromptInformation()
            if self.hidePasswordButton.isChecked():
                self.passwordEdit.setEchoMode(QLineEdit.Password)
            else:
                self.passwordEdit.setEchoMode(QLineEdit.Normal)

        def rememberPassword(self):
            core.feachat.writeLocalData("remember password", self.rememberPasswordButton.isChecked())

        def login(self):
            self.parent.hidePromptInformation()
            self.buttonStatus = self.rememberPasswordButton.isChecked()
            core.feachat.writeLocalData("remember password", int(self.buttonStatus))
            self.parent.loginHistory[self.parent.number] = self.parent.password * self.buttonStatus
            core.feachat.writeLocalData("login history", self.parent.loginHistory)
            if DEV_MODE:
                from core import DEV_MOCK_USERS, DEV_MOCK_MESSAGES, _setup_dev_assets
                _setup_dev_assets()
                account = "alice"  # DEV_MODE 固定用 alice 匹配 mock 数据
                core.feachat.account = account
                core.feachat.user_info = dict(DEV_MOCK_USERS)
                if account not in core.feachat.user_info:
                    core.feachat.user_info[account] = [account, "dev_avatar", "dev_bg", "2000-01-01", "Boy", ""]
                core.feachat.all_message = list(DEV_MOCK_MESSAGES)
                self.loginSucceeded()
                return
            request = core.feachat.request("login", self.parent.number, self.parent.password)
            if request[0] == True:
                self.loginSucceeded()
            else:
                self.parent.promptError(request[1])

        def loginSucceeded(self):
            self.parent.promptSucceeded("Login succeeded")
            self.numberEdit.setEnabled(False)
            self.passwordEdit.setEnabled(False)
            self.loginButton.setEnabled(False)
            self.rememberPasswordButton.setEnabled(False)
            self.switchRegisterButton.setEnabled(False)
            core.feachat.number = self.parent.number
            # DEV_MODE 下 account 已在 login() 裡設置，不覆蓋
            if not DEV_MODE:
                core.feachat.account = self.parent.number
            core.feachat.password = self.parent.password
            QTimer.singleShot(1000, self.openChatWindow)

        def openChatWindow(self):
            from ui.chat_ui import chatUi
            from ui.shadow import uiShadow
            self.parent.window.close()
            core.feachat.chatWindow = uiShadow(chatUi)

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
                    if event.type() == QEvent.Enter:
                        self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                        self.eventFlag = True
                    elif event.type() == QEvent.Leave:
                        self.itemArea.setStyleSheet("background-color: #ebebeb;")
                        self.eventFlag = False
                    if self.parent.genderEdit.currentText() == self.gender:
                        self.itemArea.setStyleSheet("background-color: #d0d0d0;")
                    elif not self.eventFlag:
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
                if not path:
                    return
                self.parent.avatar = "pic/loginUi/registerPage/avatar/select avatar.png"
                from PIL import Image
                img = core.feachat.cropCircle(Image.open(path), 500)
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
                request = core.feachat.request("sendRegisterCode", self.parent.email)
                if request[0] == True:
                    self.parent.parent.promptSucceeded(request[1])
                else:
                    self.parent.parent.promptError(request[1])

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
            self.page = loginUi.registerPage.userInfoPage(self)

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
            self.animation = QPropertyAnimation(self.switchPageSlider, b"pos")
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
            self.page = loginUi.registerPage.userInfoPage(self)

        def switchAccountInfoPage(self):
            self.parent.hidePromptInformation()
            self.animation = QPropertyAnimation(self.switchPageSlider, b"pos")
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
            self.page = loginUi.registerPage.accountInfoPage(self)

        def register(self):
            self.parent.hidePromptInformation()
            msg = (self.number, self.password, self.email, self.code, core.feachat.macAddress)
            request = core.feachat.request("register", *msg)
            if request[0] == True:
                self.registerSucceeded(request[1])
            else:
                self.parent.promptError(request[1])

        def registerSucceeded(self, prompt):
            print("[register] uploading avatar:", self.avatar)
            avatarId = core.feachat.uploadFile(self.avatar)
            print("[register] avatar id:", avatarId)
            backgroundId = core.feachat.uploadFile(self.background)
            print("[register] background id:", backgroundId)
            core.feachat.modifyUserInfo(self.number, "avatar", avatarId)
            core.feachat.modifyUserInfo(self.number, "background", backgroundId)
            core.feachat.modifyUserInfo(self.number, "nickname", self.nickname)
            core.feachat.modifyUserInfo(self.number, "birth", self.birth)
            core.feachat.modifyUserInfo(self.number, "gender", self.gender)
            core.feachat.modifyUserInfo(self.number, "motto", "")
            if core.feachat.readLocalData("remember password"):
                self.parent.loginHistory[self.number] = self.password
            else:
                self.parent.loginHistory[self.number] = ""
            core.feachat.writeLocalData("login history", self.parent.loginHistory)
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
            self.warningImage.setPixmap(QPixmap("pic/loginUi/removeAccountPage/warning.png"))

        def initOptions(self):
            self.option1 = QRadioButton(self)
            self.option1.move(50, 190)
            self.option1.setChecked(True)
            self.option1.setText("Remove the account from\nthe login history")
            self.option1.setObjectName("removeAccountPage-option1")
            self.option2 = QRadioButton(self)
            self.option2.move(50, 280)
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

        def optionChanged(self, obj):
            self.parent.hidePromptInformation()
            self.option = self.options.id(obj)

        def removeAccount(self):
            self.parent.hidePromptInformation()
            if self.option == 1:
                if self.number in self.parent.loginHistory:
                    del self.parent.loginHistory[self.number]
                    core.feachat.writeLocalData("login history", self.parent.loginHistory)
                self.parent.switchLoginPage()
            else:
                from ui.dialogs import messageBoxUi
                from ui.shadow import uiShadow
                uiShadow(messageBoxUi, self.parent, "Remove Account",
                         "Confirm you want to remove all files about the account from this device again",
                         self.removeOption2)

        def removeOption2(self):
            if self.number in self.parent.loginHistory:
                del self.parent.loginHistory[self.number]
                core.feachat.writeLocalData("login history", self.parent.loginHistory)
            messages = core.feachat.readLocalData("messages")
            if self.number in messages:
                del messages[self.number]
                core.feachat.writeLocalData("messages", messages)
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
            self.parent.page = loginUi.loginPage(self.parent)

        def codeChanged(self):
            self.parent.hidePromptInformation()
            self.code = self.codeEdit.text()

        def sendCode(self):
            self.parent.hidePromptInformation()
            print(666)

        def verify(self):
            self.parent.hidePromptInformation()
            self.switchLogin()

    # --- loginUi main ---

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.loginHistory = core.feachat.readLocalData("login history")
        if len(self.loginHistory):
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
        self.page = loginUi.loginPage(self)

    def initWindow(self):
        self.resize(self.width, self.height)
        self.window.setWindowTitle(core.feachat.name)
        self.window.setWindowIcon(QIcon("pic/logo/logo.png"))
        self.setStyleSheet(core.feachat.getStyleSheet("loginUi"))

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
        self.titleText.setText(core.feachat.name)
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
        self.page = loginUi.loginPage(self)

    def switchRegisteredPage(self):
        self.hidePromptInformation()
        self.page.close()
        self.page = loginUi.registerPage(self)

    def switchRemoveAccountPage(self, number):
        self.hidePromptInformation()
        self.page.close()
        self.page = loginUi.removeAccountPage(self, number)
