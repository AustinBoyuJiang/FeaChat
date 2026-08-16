# _*_coding:utf-8_*_

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core


def _make_simple_dialog(title_str, width=800, height=600):
    # Factory: generate simple dialog classes with identical structure.
    class _Dialog(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.title = title_str
            self.width = width
            self.height = height
            self.titleWidth = width
            self.titleHeight = 40
            self.resize(self.width, self.height)
            self.parent.setWindowTitle(self.title)
            self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
            self.setStyleSheet("background-color: #ffffff;")
            self.content = QLabel(self)
            self.content.resize(self.width, self.height)
            self.content.move(0, 0)
            self.content.setStyleSheet("background-color: #ffffff;border-radius: 10px;")
            self.titleText = QLabel(self)
            self.titleText.resize(self.titleWidth - 15, self.titleHeight)
            self.titleText.move(15, 0)
            self.titleText.setText(self.title)
            self.titleText.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;color: #727272;background-color: transparent;")
            self.closeButton = QPushButton(self)
            self.closeButton.resize(40, 30); self.closeButton.move(self.width - 45, 5)
            self.closeButton.setText("×"); self.closeButton.clicked.connect(self.parent.close)
            self.closeButton.setToolTip("Close"); self.closeButton.setObjectName("closeButton")
            self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;font-size: 25px;color: #727272;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton#closeButton:hover{background-color: #e1e1e1;}QPushButton#closeButton:pressed{background-color: #c9c9c9;}")
            self.minButton = QPushButton(self)
            self.minButton.resize(40, 30); self.minButton.move(self.width - 90, 5)
            self.minButton.setText("-"); self.minButton.clicked.connect(self.parent.showMinimized)
            self.minButton.setToolTip("Minimize"); self.minButton.setObjectName("minButton")
            self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;font-size: 30px;color: #727272;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton#minButton:hover{background-color: #e1e1e1}QPushButton#minButton:pressed{background-color: #c9c9c9;}")
    _Dialog.__name__ = title_str.replace(" ", "") + "Ui"
    return _Dialog


class addFriendsUi(QWidget):
    width = 500
    height = 390
    titleWidth = 500
    titleHeight = 40

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.resize(self.width, self.height)
        self.parent.setWindowTitle("Add Friends")
        self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
        self.setStyleSheet("background-color: #ffffff;border-radius: 10px;")
        self.content = QLabel(self)
        self.content.setGeometry(0, 0, self.width, self.height)
        self.content.setStyleSheet("background-color: #ffffff;border-radius: 10px;")

        self.titleText = QLabel(self)
        self.titleText.setGeometry(16, 0, 300, 40)
        self.titleText.setText("Add Friends")
        self.titleText.setStyleSheet("font-family: Arial;font-size: 18px;color: #727272;background-color: transparent;")

        self.closeButton = QPushButton(self)
        self.closeButton.setGeometry(self.width - 45, 5, 40, 30)
        self.closeButton.setText("×")
        self.closeButton.clicked.connect(self.parent.close)
        self.closeButton.setStyleSheet("QPushButton{font-family: Arial;font-size: 22px;color: #727272;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton:hover{background-color: #e1e1e1;}")

        self.searchEdit = QLineEdit(self)
        self.searchEdit.setGeometry(24, 62, 342, 42)
        self.searchEdit.setPlaceholderText("Search number or nickname")
        self.searchEdit.returnPressed.connect(self.search)
        self.searchEdit.setStyleSheet("font-family: Arial;font-size: 16px;color: #111111;background-color: #f5f5f5;border: 1px solid #d0d0d0;border-radius: 6px;padding-left: 12px;")

        self.searchButton = QPushButton(self)
        self.searchButton.setGeometry(378, 62, 94, 42)
        self.searchButton.setText("Search")
        self.searchButton.clicked.connect(self.search)
        self.searchButton.setStyleSheet("QPushButton{font-family: Arial;font-size: 16px;color: #ffffff;background-color: #0076F6;border: 0px;border-radius: 6px;}QPushButton:hover{background-color: #006bdf;}")

        self.statusText = QLabel(self)
        self.statusText.setGeometry(24, 112, 448, 28)
        self.statusText.setStyleSheet("font-family: Arial;font-size: 14px;color: #777777;background-color: transparent;")

        self.resultList = QListWidget(self)
        self.resultList.setGeometry(24, 148, 448, 216)
        self.resultList.setStyleSheet("QListWidget{background-color: #ffffff;border: 1px solid #eeeeee;border-radius: 6px;outline: none;}QListWidget::item{border-bottom: 1px solid #eeeeee;}")
        self.show()

    def search(self):
        keyword = self.searchEdit.text().strip()
        self.resultList.clear()
        if not keyword:
            self.statusText.setText("Enter a number or nickname.")
            return
        results = core.feachat.searchUsers(keyword)
        if not results:
            self.statusText.setText("No users found.")
            return
        self.statusText.setText(f"{len(results)} user(s) found.")
        for number, nickname, avatar, motto in results:
            item = QListWidgetItem(self.resultList)
            item.setSizeHint(QSize(448, 64))
            self.resultList.setItemWidget(item, self.resultItem(number, nickname, motto))

    class resultItem(QWidget):
        def __init__(self, number, nickname, motto):
            super().__init__()
            self.number = number
            self.setStyleSheet("background-color: transparent;")
            self.nameText = QLabel(self)
            self.nameText.setGeometry(14, 8, 260, 24)
            self.nameText.setText(f"{nickname or number} ({number})")
            self.nameText.setStyleSheet("font-family: Arial;font-size: 16px;color: #222222;background-color: transparent;")
            self.mottoText = QLabel(self)
            self.mottoText.setGeometry(14, 34, 310, 20)
            self.mottoText.setText(motto or "")
            self.mottoText.setStyleSheet("font-family: Arial;font-size: 13px;color: #777777;background-color: transparent;")
            self.addButton = QPushButton(self)
            self.addButton.setGeometry(338, 14, 86, 36)
            self.addButton.setText("Request")
            self.addButton.clicked.connect(self.add)
            self.addButton.setStyleSheet("QPushButton{font-family: Arial;font-size: 14px;color: #ffffff;background-color: #0076F6;border: 0px;border-radius: 5px;}QPushButton:hover{background-color: #006bdf;}QPushButton:disabled{background-color: #aaaaaa;}")

        def add(self):
            request = core.feachat.addFriend(self.number)
            if request[0]:
                self.addButton.setText("Sent")
                self.addButton.setEnabled(False)
                try:
                    cw = core.feachat.chatWindow.mainWindow
                    if cw.page == "Contacts":
                        cw.switchContacts()
                except Exception:
                    pass
            else:
                self.addButton.setText("Failed")

createGroupUi = _make_simple_dialog("Create Group")
shareMomentsUi = _make_simple_dialog("Share Moments")
settingUi = _make_simple_dialog("Setting")
fileManagerUi = _make_simple_dialog("File Manager")


class messageBoxUi(QWidget):
    width = 500
    height = 300
    titleWidth = 500
    titleHeight = 40

    def __init__(self, window, parent, title, message, event):
        super().__init__(window)
        self.window = window
        self.parent = parent
        self.resize(self.width, self.height)
        self.parent.setWindowTitle(title)
        self.window.setWindowModality(Qt.ApplicationModal)
        self.parent.setWindowIcon(QIcon("pic/logo/logo.png"))
        self.setStyleSheet(core.feachat.getStyleSheet("messageBoxUi"))
        self.content = QLabel(self); self.content.resize(self.width, self.height); self.content.move(0, 0)
        self.content.setStyleSheet("background-color: #ffffff;border-radius: 10px;")
        self.titleText = QLabel(self); self.titleText.setGeometry(15, 0, 485, 40)
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;color: #727272;background-color: transparent;")
        self.messageText = QLabel(self); self.messageText.setGeometry(20, 40, 460, 200)
        self.messageText.setText(message); self.messageText.setWordWrap(True)
        self.messageText.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.messageText.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;color: #000000;background-color: transparent;")
        self.closeButton = QPushButton(self); self.closeButton.setGeometry(self.width - 45, 5, 40, 30)
        self.closeButton.setText("×"); self.closeButton.setObjectName("closeButton")
        self.closeButton.clicked.connect(self.window.close)
        self.confirmButton = QPushButton(self); self.confirmButton.setGeometry(250, 240, 100, 40)
        self.confirmButton.setText("Confirm"); self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.clicked.connect(event)
        self.cancelButton = QPushButton(self); self.cancelButton.setGeometry(370, 240, 100, 40)
        self.cancelButton.setText("Cancel"); self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.clicked.connect(self.window.close)
        self.show()
