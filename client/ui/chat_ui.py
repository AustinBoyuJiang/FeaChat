# _*_coding:utf-8_*_

import webbrowser
from PIL import Image
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core
from core import DEV_MODE, get_user_info, download_file


class chatUi(QWidget):
    class expandMoreArea(QListWidget):
        class addFriendsButton(QWidget):
            def __init__(self, item):
                super().__init__()
                item.setSizeHint(QSize(180, 50))
                self.resize(200, 50)
                self.setStyleSheet("background-color: transparent;")
                self.text = QLabel(self)
                self.text.resize(150, 50)
                self.text.move(50, 0)
                self.text.setText("Add Friends")
                self.text.setAlignment(Qt.AlignVCenter)
                self.text.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #ffffff;")

        class createGroupButton(QWidget):
            def __init__(self, item):
                super().__init__()
                item.setSizeHint(QSize(180, 50))
                self.resize(200, 50)
                self.setStyleSheet("background-color: transparent;")
                self.text = QLabel(self)
                self.text.resize(150, 50)
                self.text.move(50, 0)
                self.text.setText("Create Group")
                self.text.setAlignment(Qt.AlignVCenter)
                self.text.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #ffffff;")

        class shareMomentsButton(QWidget):
            def __init__(self, item):
                super().__init__()
                item.setSizeHint(QSize(180, 50))
                self.resize(200, 50)
                self.setStyleSheet("background-color: transparent;")
                self.text = QLabel(self)
                self.text.resize(150, 50)
                self.text.move(50, 0)
                self.text.setText("Share Moments")
                self.text.setAlignment(Qt.AlignVCenter)
                self.text.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #ffffff;")

        def __init__(self, parent):
            super().__init__(parent)
            self.resize(200, 150)
            self.move(225, 67)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
            self.itemClicked.connect(self.buttonClicked)
            self.setStyleSheet("QListWidget {background-color: #727272;outline: none;border:0px;}"
                               "QListWidget:Item:hover{background-color: #808080;}"
                               "QListWidget:Item:selected{background-color: #808080;}")
            for cls in [self.addFriendsButton, self.createGroupButton, self.shareMomentsButton]:
                item = QListWidgetItem()
                self.addItem(item)
                self.setItemWidget(item, cls(item))
            self.show()

        def buttonClicked(self):
            if not self.selectedItems():
                return
            from ui.dialogs import addFriendsUi, createGroupUi, shareMomentsUi
            from ui.shadow import uiShadow
            button = type(self.itemWidget(self.selectedItems()[0]))
            core.feachat.chatWindow.mainWindow.retakeMore()
            cw = core.feachat.chatWindow.mainWindow
            if button == self.addFriendsButton:
                if "addFriendsWindow" in vars(cw) and cw.addFriendsWindow.isVisible():
                    cw.addFriendsWindow.showNormal(); cw.addFriendsWindow.raise_()
                else:
                    cw.addFriendsWindow = uiShadow(addFriendsUi); core.feachat.app.exec_()
            elif button == self.createGroupButton:
                if "createGroupWindow" in vars(cw) and cw.createGroupWindow.isVisible():
                    cw.createGroupWindow.showNormal(); cw.createGroupWindow.raise_()
                else:
                    cw.createGroupWindow = uiShadow(createGroupUi); core.feachat.app.exec_()
            elif button == self.shareMomentsButton:
                if "shareMomentsWindow" in vars(cw) and cw.shareMomentsWindow.isVisible():
                    cw.shareMomentsWindow.showNormal(); cw.shareMomentsWindow.raise_()
                else:
                    cw.shareMomentsWindow = uiShadow(shareMomentsUi); core.feachat.app.exec_()

    class searchList(QListWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.resize(375, 765)
            self.move(75, 75)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
            self.setStyleSheet("QListWidget {background-color: #ffffff;outline: none;border:0px;}"
                               "QListWidget:Item:hover{background-color: #e0e0e0;}"
                               "QListWidget:Item:selected{background-color: #d0d0d0;}")
            self.show()

        def mouseReleaseEvent(self, event):
            core.feachat.chatWindow.mainWindow.retakeMore()
            super().mouseReleaseEvent(event)

    class chatList(QListWidget):
        class chatsSelectBox(QWidget):
            def __init__(self, item, number, lastMessage):
                super().__init__()
                self.nickname = get_user_info(number)[0]
                self.profile_picture = "data/temp/%s" % get_user_info(number)[1]
                self.number = number
                if lastMessage[4] == "text":
                    self.lastMessage = lastMessage[5]
                elif lastMessage[4] == "file":
                    file_info = core.feachat.get_file_info(lastMessage[5])
                    self.lastMessage = "[file] %s" % (file_info[1] + file_info[2])
                elif lastMessage[4] == "link":
                    self.lastMessage = "[link] %s" % lastMessage[5]
                elif lastMessage[4] == "emoji":
                    self.lastMessage = "[emoji]"
                self.lastSendTime = set_time(lastMessage[3])
                self.notReceived = 0
                item.setSizeHint(QSize(375, 90))
                self.resize(750, 90)
                self.initAvatarShow()
                self.initNicknameShow()
                self.initLastMessageShow()
                self.initLastSendTimeShow()
                self.initNotReceivedReminder()
                self.setNotReceived(0)

            def initAvatarShow(self):
                self.avatarShow = QLabel(self)
                self.avatarShow.resize(60, 60)
                self.avatarShow.move(20, 15)
                self.avatarShow.setStyleSheet("border-radius: 30px;border-image: url(%s);" % self.profile_picture)

            def initNicknameShow(self):
                self.nicknameShow = QLabel(self)
                self.nicknameShow.resize(90, 20)
                self.nicknameShow.move(100, 15)
                self.nicknameShow.setText(self.nickname)
                self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.nicknameShow.setStyleSheet("font-family: Arial;font-size: 18px;color: #222222;background-color: transparent;")

            def initLastMessageShow(self):
                self.lastMessageShow = QLabel(self)
                self.lastMessageShow.move(100, 35)
                self.lastMessageShow.setText(self.lastMessage)
                self.lastMessageShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.lastMessageShow.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #888888;background-color: transparent;")

            def initLastSendTimeShow(self):
                self.lastSendTimeShow = QLabel(self)
                self.lastSendTimeShow.resize(160, 20)
                self.lastSendTimeShow.move(200, 15)
                self.lastSendTimeShow.setText(self.lastSendTime)
                self.lastSendTimeShow.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.lastSendTimeShow.setStyleSheet("font-family: Microsoft YaHei;font-size: 15px;color: #aaaaaa;background-color: transparent;")

            def initNotReceivedReminder(self):
                self.notReceivedReminder = QLabel(self)
                self.notReceivedReminder.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.notReceivedReminder.setStyleSheet("font-family: Microsoft YaHei;font-size: 14px;color: #ffffff;background-color: #ff0000;border-radius: 10px;")

            def setNotReceived(self, number):
                self.notReceived = number
                if self.notReceived == 0:
                    self.notReceivedReminder.setVisible(False)
                    self.lastMessageShow.resize(260, 40)
                elif len(str(self.notReceived)) == 1:
                    self.notReceivedReminder.setVisible(True)
                    self.lastMessageShow.resize(230, 40)
                    self.notReceivedReminder.resize(20, 20)
                    self.notReceivedReminder.move(340, 45)
                    self.notReceivedReminder.setText(str(self.notReceived))
                elif len(str(self.notReceived)) == 2:
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
            self.resize(375, 765)
            self.move(75, 75)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
            self.itemClicked.connect(self.showMessageList)
            self.setStyleSheet("QListWidget {background-color: #ffffff;outline: none;border:0px;}"
                               "QListWidget:Item:hover{background-color: #e0e0e0;}"
                               "QListWidget:Item:selected{background-color: #d0d0d0;}")
            self.number_item = {}
            user_info = core.feachat.user_info
            account = core.feachat.account
            all_message = core.feachat.all_message if hasattr(core.feachat, "all_message") else []
            for i in range(len(all_message) - 1, -1, -1):
                if all_message[i][1] != account and all_message[i][2] != account:
                    number = all_message[i][2]
                elif all_message[i][1] == account:
                    number = all_message[i][2]
                else:
                    number = all_message[i][1]
                if number not in user_info:
                    user_info[number] = get_user_info(number)
                    download_file(user_info[number][1], "data")
                    download_file(user_info[number][2], "data")
                if number not in self.number_item:
                    item = QListWidgetItem()
                    self.number_item[number] = item
                    self.addItem(item)
                    self.setItemWidget(item, self.chatsSelectBox(item, number, all_message[i]))
            self.show()

        def showMessageList(self):
            if self.selectedItems():
                number = self.itemWidget(self.selectedItems()[0]).number
                cw = core.feachat.chatWindow.mainWindow
                cw.titleText.setText(core.feachat.user_info[number][0])
                cw.close_content()
                cw.set_content(cw.messageContent(cw, number))
                self.itemWidget(self.selectedItems()[0]).setNotReceived(0)
            else:
                core.feachat.chatWindow.mainWindow.content[-1].close()

        def mouseReleaseEvent(self, event):
            core.feachat.chatWindow.mainWindow.retakeMore()
            super().mouseReleaseEvent(event)

    class contactList(QListWidget):
        class contactSelectBox(QWidget):
            def __init__(self, item, number, nickname, avatar, motto):
                super().__init__()
                self.number = number
                self.nickname = nickname or number
                self.avatar = avatar
                self.motto = motto or ""
                item.setSizeHint(QSize(375, 76))
                self.resize(375, 76)
                self.avatarShow = QLabel(self)
                self.avatarShow.setGeometry(18, 13, 50, 50)
                self.avatarShow.setScaledContents(True)
                if avatar is not None:
                    download_file(avatar, "data")
                    self.avatarShow.setPixmap(QPixmap("data/temp/%s" % avatar))
                self.avatarShow.setStyleSheet("background-color: transparent;border-radius: 25px;")
                self.nicknameShow = QLabel(self)
                self.nicknameShow.setGeometry(86, 13, 220, 24)
                self.nicknameShow.setText(self.nickname)
                self.nicknameShow.setStyleSheet("font-family: Arial;font-size: 17px;color: #222222;background-color: transparent;")
                self.mottoShow = QLabel(self)
                self.mottoShow.setGeometry(86, 39, 260, 22)
                self.mottoShow.setText(self.motto)
                self.mottoShow.setStyleSheet("font-family: Arial;font-size: 13px;color: #888888;background-color: transparent;")
                self.deleteButton = QPushButton(self)
                self.deleteButton.setGeometry(300, 20, 58, 32)
                self.deleteButton.setText("Delete")
                self.deleteButton.clicked.connect(self.delete)
                self.deleteButton.setStyleSheet("QPushButton{font-family: Arial;font-size: 12px;color: #555555;background-color: #eeeeee;border: 0px;border-radius: 5px;}QPushButton:hover{background-color: #dddddd;}")

            def delete(self):
                core.feachat.deleteFriend(self.number)
                cw = core.feachat.chatWindow.mainWindow
                cw.switchContacts()

        class requestSelectBox(QWidget):
            def __init__(self, item, number, nickname, avatar, motto):
                super().__init__()
                self.number = number
                item.setSizeHint(QSize(375, 88))
                self.resize(375, 88)
                self.label = QLabel(self)
                self.label.setGeometry(18, 8, 330, 20)
                self.label.setText("Friend request")
                self.label.setStyleSheet("font-family: Arial;font-size: 12px;color: #0076F6;background-color: transparent;")
                self.nameText = QLabel(self)
                self.nameText.setGeometry(18, 30, 210, 22)
                self.nameText.setText(f"{nickname or number} ({number})")
                self.nameText.setStyleSheet("font-family: Arial;font-size: 16px;color: #222222;background-color: transparent;")
                self.acceptButton = QPushButton(self)
                self.acceptButton.setGeometry(225, 42, 62, 32)
                self.acceptButton.setText("Accept")
                self.acceptButton.clicked.connect(self.accept)
                self.acceptButton.setStyleSheet("QPushButton{font-family: Arial;font-size: 12px;color: #ffffff;background-color: #0076F6;border: 0px;border-radius: 5px;}QPushButton:hover{background-color: #006bdf;}")
                self.rejectButton = QPushButton(self)
                self.rejectButton.setGeometry(296, 42, 62, 32)
                self.rejectButton.setText("Reject")
                self.rejectButton.clicked.connect(self.reject)
                self.rejectButton.setStyleSheet("QPushButton{font-family: Arial;font-size: 12px;color: #555555;background-color: #eeeeee;border: 0px;border-radius: 5px;}QPushButton:hover{background-color: #dddddd;}")

            def accept(self):
                core.feachat.acceptFriendRequest(self.number)
                core.feachat.chatWindow.mainWindow.switchContacts()

            def reject(self):
                core.feachat.rejectFriendRequest(self.number)
                core.feachat.chatWindow.mainWindow.switchContacts()

        def __init__(self, parent):
            super().__init__(parent)
            self.resize(375, 765)
            self.move(75, 75)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
            self.itemClicked.connect(self.showMessageList)
            self.setStyleSheet("QListWidget {background-color: #ffffff;outline: none;border:0px;}"
                               "QListWidget:Item:hover{background-color: #e0e0e0;}"
                               "QListWidget:Item:selected{background-color: #d0d0d0;}")
            self.number_item = {}
            for number, nickname, avatar, motto, created_at in core.feachat.getFriendRequests():
                item = QListWidgetItem()
                self.addItem(item)
                self.setItemWidget(item, self.requestSelectBox(item, number, nickname, avatar, motto))
            for number, nickname, avatar, motto in core.feachat.getFriends():
                info = get_user_info(number)
                core.feachat.user_info[number] = info
                item = QListWidgetItem()
                self.number_item[number] = item
                self.addItem(item)
                self.setItemWidget(item, self.contactSelectBox(item, number, info[0], info[1], info[5]))
            self.show()

        def showMessageList(self):
            if not self.selectedItems():
                return
            widget = self.itemWidget(self.selectedItems()[0])
            if not isinstance(widget, self.contactSelectBox):
                return
            number = widget.number
            cw = core.feachat.chatWindow.mainWindow
            cw.titleText.setText(core.feachat.user_info[number][0])
            cw.close_content()
            cw.set_content(cw.messageContent(cw, number))

        def mouseReleaseEvent(self, event):
            core.feachat.chatWindow.mainWindow.retakeMore()
            super().mouseReleaseEvent(event)

    class messageContent(QListWidget):
        class timeBox(QWidget):
            def __init__(self, item, datetime):
                super().__init__()
                self.item = item
                self.text = set_time(datetime)
                width = message_area_width()
                self.resize(width, 60)
                self.item.setSizeHint(QSize(width, 60))
                self.timeLabel = QLabel(self)
                self.timeLabel.resize(width, 60)
                self.timeLabel.move(0, 0)
                self.timeLabel.setText(self.text)
                self.timeLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.timeLabel.setStyleSheet("font-family: Microsoft YaHei;font-size: 17px;color: #aaaaaa;background-color: transparent")

            def relayout(self, width):
                self.resize(width, 60)
                self.item.setSizeHint(QSize(width, 60))
                self.timeLabel.resize(width, 60)

        class rightTextBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item
                self.text_height = 21
                self.font_size = 10
                self.startX = 86
                self.startY = 20
                self.radius = 8
                self.width_border = 15
                self.height_border = 10
                self.max_length = 400
                self.text = message_info[5] if message_info[5] != "" else " "
                self.sender = message_info[1]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.avatarShow = QPushButton(self)
                self.avatarShow.resize(50, 50)
                self.avatarShow.move(message_area_width() - 72, self.startY - 5)
                self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)

            def paintEvent(self, event):
                text = self.text
                startX = self.startX; startY = self.startY; radius = self.radius
                width_border = self.width_border; height_border = self.height_border
                boxWidth = message_area_width()
                max_length = max(120, min(self.max_length, boxWidth - startX - 120))
                self.avatarShow.move(boxWidth - 72, self.startY - 5)
                font = QFont("Arial", 13)
                metrics = QFontMetrics(font)
                all_line = []; left, right = 0, 0
                while left < len(text):
                    while right <= len(text) and metrics.boundingRect(text[left:right]).width() <= max_length:
                        right += 1
                    right -= 1
                    all_line.append(text[left:right]); left = right
                line_height = metrics.height()
                width = min(max_length, max(metrics.boundingRect(line).width() for line in all_line)) + width_border * 2
                height = len(all_line) * line_height + height_border * 2
                boxHeight = height + startY * 2 + 20
                self.resize(boxWidth, boxHeight); self.item.setSizeHint(QSize(boxWidth, boxHeight))
                p = QPainter(self); brush = QBrush(Qt.SolidPattern)
                p.setRenderHint(QPainter.Antialiasing)
                p.setFont(font)
                p.setPen(QColor("#c9e7ff")); brush.setColor(QColor("#c9e7ff")); p.setBrush(brush)
                tri = QPolygon()
                tri.setPoints(boxWidth-startX+10, startY+20, boxWidth-startX, startY+20, boxWidth-startX, startY+32)
                p.drawPolygon(tri)
                bubble = QRect(boxWidth-startX-width, startY+20, width, height)
                p.drawRoundedRect(bubble, radius, radius)
                p.setPen(QColor("#000000"))
                text_rect = bubble.adjusted(width_border, height_border, -width_border, -height_border)
                p.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, "\n".join(all_line))
                p.end()

            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow
                cw.close_content(); cw.set_content(cw.userInfoContent(cw, self.sender))

            def relayout(self, width):
                self.update()

        class leftTextBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item
                self.text_height = 21; self.font_size = 10; self.startX = 86; self.startY = 20
                self.radius = 8; self.width_border = 15; self.height_border = 10; self.max_length = 400
                self.text = message_info[5] if message_info[5] != "" else " "
                self.sender = message_info[1]
                self.nickname = core.feachat.user_info[self.sender][0]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.avatarShow = QPushButton(self)
                self.avatarShow.resize(50, 50); self.avatarShow.move(30, self.startY - 5)
                self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                self.nicknameShow = QLabel(self)
                self.nicknameShow.resize(message_area_width() - self.startX, 30); self.nicknameShow.move(self.startX, 10)
                self.nicknameShow.setText(self.nickname); self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;font-size: 16px;background-color: transparent;")

            def paintEvent(self, event):
                text = self.text
                startX = self.startX; startY = self.startY; radius = self.radius
                width_border = self.width_border; height_border = self.height_border
                boxWidth = message_area_width()
                max_length = max(120, min(self.max_length, boxWidth - startX - 80))
                self.nicknameShow.resize(max(120, boxWidth - self.startX - 20), 30)
                font = QFont("Arial", 13)
                metrics = QFontMetrics(font)
                all_line = []; left, right = 0, 0
                while left < len(text):
                    while right <= len(text) and metrics.boundingRect(text[left:right]).width() <= max_length:
                        right += 1
                    right -= 1; all_line.append(text[left:right]); left = right
                line_height = metrics.height()
                width = min(max_length, max(metrics.boundingRect(line).width() for line in all_line)) + width_border * 2
                height = len(all_line) * line_height + height_border * 2
                boxHeight = height + startY * 2 + 20
                self.resize(boxWidth, boxHeight); self.item.setSizeHint(QSize(boxWidth, boxHeight))
                p = QPainter(self); brush = QBrush(Qt.SolidPattern)
                p.setRenderHint(QPainter.Antialiasing)
                p.setFont(font)
                p.setPen(QColor("#dddddd")); brush.setColor(QColor("#dddddd")); p.setBrush(brush)
                tri = QPolygon()
                tri.setPoints(startX-10, startY+20, startX, startY+20, startX, startY+32)
                p.drawPolygon(tri)
                bubble = QRect(startX, startY+20, width, height)
                p.drawRoundedRect(bubble, radius, radius)
                p.setPen(QColor("#000000"))
                text_rect = bubble.adjusted(width_border, height_border, -width_border, -height_border)
                p.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, "\n".join(all_line))
                p.end()

            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow
                cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

            def relayout(self, width):
                self.update()

        class rightFileBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item; self.startX = 100; self.startY = 20
                self.sender = message_info[1]; self.file = message_info[5]
                self.file_info = core.feachat.get_file_info(self.file) if hasattr(core.feachat, "get_file_info") else [0, self.file, ""]
                self.file_size = self.file_info[0]; self.file_name = self.file_info[1] + self.file_info[2]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.resize(750, 200); self.item.setSizeHint(QSize(750, 200))
                self.avatarShow = QPushButton(self); self.avatarShow.resize(50, 50)
                self.avatarShow.move(670, self.startY - 5); self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                self.fileBox = QLabel(self); self.fileBox.resize(320, 140)
                self.fileBox.move(750-self.startX-320, self.startY+20)
                self.fileBox.setStyleSheet("background-color: #ffffff;border-radius: 10px;border: 1px solid #dddddd;")
                self.fileImage = QLabel(self); self.fileImage.resize(70, 70)
                self.fileImage.move(750-self.startX-90, self.startY+40)
                self.fileImage.setPixmap(QPixmap("pic/chatUi/file.png")); self.fileImage.setScaledContents(True)
                self.fileImage.setStyleSheet("background-color: transparent;")
                self._initFileName(); self._initFileSize(); self._initDownloadButton()

            def _initFileName(self):
                text = "[file] %s" % self.file_name; max_length = 150
                font = QPainter(self); font.setFont(QFont("Microsoft YaHei", 20))
                all_line = ""; left, right = 0, 0
                while left < len(text):
                    while right <= len(text) and font.fontMetrics().boundingRect(text[left:right]).width() <= max_length: right += 1
                    right -= 1; all_line += text[left:right] + "\n"; left = right
                self.fileName = QLabel(self); self.fileName.resize(200, 55)
                self.fileName.move(750-self.startX-300, self.startY+40); self.fileName.setText(all_line)
                self.fileName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.fileName.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;background-color: transparent;")

            def _initFileSize(self):
                self.fileSize = QLabel(self); self.fileSize.resize(200, 30)
                self.fileSize.move(750-self.startX-300, self.startY+125); self.fileSize.setText(set_size(self.file_size))
                self.fileSize.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.fileSize.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #bbbbbb;background-color: transparent;")

            def _initDownloadButton(self):
                self.downloadButton = QPushButton(self); self.downloadButton.resize(100, 30)
                self.downloadButton.move(750-self.startX-120, self.startY+120); self.downloadButton.clicked.connect(self.downloadFile)
                self.downloadButton.setText("Download file"); self.downloadButton.setObjectName("downloadButton")
                self.downloadButton.setStyleSheet("QPushButton#downloadButton{font-family: Microsoft YaHei;font-size: 15px;color: #000000;background-color: transparent;}QPushButton#downloadButton:hover{color: #555555;}QPushButton#downloadButton:pressed{color: #777777;}")

            def downloadFile(self): download_file(self.file, "file"); os.startfile("file")
            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow; cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

        class leftFileBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item; self.startX = 100; self.startY = 20
                self.sender = message_info[1]; self.file = message_info[5]
                self.file_info = core.feachat.get_file_info(self.file) if hasattr(core.feachat, "get_file_info") else [0, self.file, ""]
                self.file_size = self.file_info[0]; self.file_name = self.file_info[1] + self.file_info[2]
                self.nickname = core.feachat.user_info[self.sender][0]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.resize(750, 200); self.item.setSizeHint(QSize(750, 200))
                self.avatarShow = QPushButton(self); self.avatarShow.resize(50, 50)
                self.avatarShow.move(30, self.startY-5); self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                self.nicknameShow = QLabel(self); self.nicknameShow.resize(750-self.startX, 30)
                self.nicknameShow.move(self.startX, 10); self.nicknameShow.setText(self.nickname)
                self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;font-size: 16px;background-color: transparent;")
                self.fileBox = QLabel(self); self.fileBox.resize(320, 140)
                self.fileBox.move(self.startX, self.startY+20)
                self.fileBox.setStyleSheet("background-color: #ffffff;border-radius: 10px;border: 1px solid #dddddd;")
                self.fileImage = QLabel(self); self.fileImage.resize(70, 70)
                self.fileImage.move(self.startX+230, self.startY+40)
                self.fileImage.setPixmap(QPixmap("pic/chatUi/file.png")); self.fileImage.setScaledContents(True)
                self.fileImage.setStyleSheet("background-color: transparent;")
                self._initFileName(); self._initFileSize(); self._initDownloadButton()

            def _initFileName(self):
                text = "[file] %s" % self.file_name; max_length = 150
                font = QPainter(self); font.setFont(QFont("Microsoft YaHei", 20))
                all_line = ""; left, right = 0, 0
                while left < len(text):
                    while right <= len(text) and font.fontMetrics().boundingRect(text[left:right]).width() <= max_length: right += 1
                    right -= 1; all_line += text[left:right] + "\n"; left = right
                self.fileName = QLabel(self); self.fileName.resize(200, 55)
                self.fileName.move(self.startX+20, self.startY+40); self.fileName.setText(all_line)
                self.fileName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.fileName.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;background-color: transparent;")

            def _initFileSize(self):
                self.fileSize = QLabel(self); self.fileSize.resize(200, 30)
                self.fileSize.move(self.startX+20, self.startY+125); self.fileSize.setText(set_size(self.file_size))
                self.fileSize.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.fileSize.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #bbbbbb;background-color: transparent;")

            def _initDownloadButton(self):
                self.downloadButton = QPushButton(self); self.downloadButton.resize(100, 30)
                self.downloadButton.move(self.startX+200, self.startY+120); self.downloadButton.clicked.connect(self.downloadFile)
                self.downloadButton.setText("Download file"); self.downloadButton.setObjectName("downloadButton")
                self.downloadButton.setStyleSheet("QPushButton#downloadButton{font-family: Microsoft YaHei;font-size: 15px;color: #000000;background-color: transparent;}QPushButton#downloadButton:hover{color: #555555;}QPushButton#downloadButton:pressed{color: #777777;}")

            def downloadFile(self): download_file(self.file, "file"); os.startfile("file")
            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow; cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

        class rightLinkBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item; self.startX = 100; self.startY = 20
                self.sender = message_info[1]; self.link = message_info[5]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.resize(750, 200); self.item.setSizeHint(QSize(750, 200))
                self.avatarShow = QPushButton(self); self.avatarShow.resize(50, 50)
                self.avatarShow.move(670, self.startY-5); self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                self.linkBox = QLabel(self); self.linkBox.resize(320, 140)
                self.linkBox.move(750-self.startX-320, self.startY+20)
                self.linkBox.setStyleSheet("background-color: #ffffff;border-radius: 10px;border: 1px solid #dddddd;")
                self.linkImage = QLabel(self); self.linkImage.resize(60, 60)
                self.linkImage.move(750-self.startX-85, self.startY+45)
                self.linkImage.setPixmap(QPixmap("pic/chatUi/link.png")); self.linkImage.setScaledContents(True)
                self.linkImage.setStyleSheet("background-color: transparent;")
                self._initLink(); self._initOpenLinkButton()

            def _initLink(self):
                text = "[link] %s" % self.link; max_length = 150
                font = QPainter(self); font.setFont(QFont("Microsoft YaHei", 20))
                all_line = ""; left, right = 0, 0
                while left < len(text):
                    while right <= len(text) and font.fontMetrics().boundingRect(text[left:right]).width() <= max_length: right += 1
                    right -= 1; all_line += text[left:right] + "\n"; left = right
                self.linkName = QLabel(self); self.linkName.resize(200, 55)
                self.linkName.move(750-self.startX-300, self.startY+40); self.linkName.setText(all_line)
                self.linkName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.linkName.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;background-color: transparent;")

            def _initOpenLinkButton(self):
                self.openLinkButton = QPushButton(self); self.openLinkButton.resize(80, 30)
                self.openLinkButton.move(750-self.startX-100, self.startY+120); self.openLinkButton.clicked.connect(self.openLink)
                self.openLinkButton.setText("Open link"); self.openLinkButton.setObjectName("openLinkButton")
                self.openLinkButton.setStyleSheet("QPushButton#openLinkButton{font-family: Microsoft YaHei;font-size: 15px;color: #000000;background-color: transparent;}QPushButton#openLinkButton:hover{color: #555555;}QPushButton#openLinkButton:pressed{color: #777777;}")

            def openLink(self): webbrowser.open(self.link)
            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow; cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

        class leftLinkBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item; self.startX = 100; self.startY = 20
                self.sender = message_info[1]; self.link = message_info[5]
                self.nickname = core.feachat.user_info[self.sender][0]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.resize(750, 200); self.item.setSizeHint(QSize(750, 200))
                self.avatarShow = QPushButton(self); self.avatarShow.resize(50, 50)
                self.avatarShow.move(30, self.startY-5); self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                self.nicknameShow = QLabel(self); self.nicknameShow.resize(750-self.startX, 30)
                self.nicknameShow.move(self.startX, 10); self.nicknameShow.setText(self.nickname)
                self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;font-size: 16px;background-color: transparent;")
                self.linkBox = QLabel(self); self.linkBox.resize(320, 140)
                self.linkBox.move(self.startX, self.startY+20)
                self.linkBox.setStyleSheet("background-color: #ffffff;border-radius: 10px;border: 1px solid #dddddd;")
                self.linkImage = QLabel(self); self.linkImage.resize(60, 60)
                self.linkImage.move(self.startX+235, self.startY+45)
                self.linkImage.setPixmap(QPixmap("pic/chatUi/link.png")); self.linkImage.setScaledContents(True)
                self.linkImage.setStyleSheet("background-color: transparent;")
                self._initLink(); self._initOpenLinkButton()

            def _initLink(self):
                text = "[link] %s" % self.link; max_length = 150
                font = QPainter(self); font.setFont(QFont("Microsoft YaHei", 20))
                all_line = ""; left, right = 0, 0
                while left < len(text):
                    while right <= len(text) and font.fontMetrics().boundingRect(text[left:right]).width() <= max_length: right += 1
                    right -= 1; all_line += text[left:right] + "\n"; left = right
                self.linkName = QLabel(self); self.linkName.resize(200, 55)
                self.linkName.move(self.startX+20, self.startY+40); self.linkName.setText(all_line)
                self.linkName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.linkName.setStyleSheet("font-family: Microsoft YaHei;font-size: 20px;background-color: transparent;")

            def _initOpenLinkButton(self):
                self.openLinkButton = QPushButton(self); self.openLinkButton.resize(80, 30)
                self.openLinkButton.move(self.startX+220, self.startY+120); self.openLinkButton.clicked.connect(self.openLink)
                self.openLinkButton.setText("Open link"); self.openLinkButton.setObjectName("openLinkButton")
                self.openLinkButton.setStyleSheet("QPushButton#openLinkButton{font-family: Microsoft YaHei;font-size: 15px;color: #000000;background-color: transparent;}QPushButton#openLinkButton:hover{color: #555555;}QPushButton#openLinkButton:pressed{color: #777777;}")

            def openLink(self): webbrowser.open(self.link)
            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow; cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

        class rightEmojiBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item; self.startX = 100; self.startY = 20
                self.sender = message_info[1]; self.emoji = message_info[5]
                download_file(self.emoji, "data")
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.resize(750, 200); self.item.setSizeHint(QSize(750, 210))
                self.avatarShow = QPushButton(self); self.avatarShow.resize(50, 50)
                self.avatarShow.move(670, self.startY-5); self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                emojiSize = Image.open("data/temp/%s" % self.emoji).size
                ew, eh = emojiSize
                self.emojiBox = QLabel(self)
                if ew > eh:
                    self.emojiBox.resize(150, int(150/ew*eh)); self.emojiBox.move(750-self.startX-150, self.startY+int((150-(150/ew*eh))/2)+20)
                else:
                    self.emojiBox.resize(int(150/eh*ew), 150); self.emojiBox.move(750-self.startX-int(150/eh*ew), self.startY+20)
                self.gif = QMovie("data/temp/%s" % self.emoji); self.emojiBox.setMovie(self.gif)
                self.emojiBox.setScaledContents(True); self.gif.start()
                self.emojiBox.setStyleSheet("background-color: transparent;")

            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow; cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

        class leftEmojiBox(QWidget):
            def __init__(self, item, message_info):
                super().__init__()
                self.item = item; self.startX = 100; self.startY = 20
                self.sender = message_info[1]; self.emoji = message_info[5]
                download_file(self.emoji, "data")
                self.nickname = core.feachat.user_info[self.sender][0]
                self.profile_picture = "data/temp/%s" % core.feachat.user_info[self.sender][1]
                self.resize(750, 200); self.item.setSizeHint(QSize(750, 210))
                self.avatarShow = QPushButton(self); self.avatarShow.resize(50, 50)
                self.avatarShow.move(30, self.startY-5); self.avatarShow.clicked.connect(self.showUserInfo)
                self.avatarShow.setStyleSheet("border-radius: 25px;border-image: url(%s);" % self.profile_picture)
                self.nicknameShow = QLabel(self); self.nicknameShow.resize(750-self.startX, 30)
                self.nicknameShow.move(self.startX, 10); self.nicknameShow.setText(self.nickname)
                self.nicknameShow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.nicknameShow.setStyleSheet("font-family: Microsoft YaHei;font-size: 16px;background-color: transparent;")
                emojiSize = Image.open("data/temp/%s" % self.emoji).size
                ew, eh = emojiSize
                self.emojiBox = QLabel(self)
                if ew > eh:
                    self.emojiBox.resize(150, int(150/ew*eh)); self.emojiBox.move(self.startX, self.startY+int((150-(150/ew*eh))/2)+20)
                else:
                    self.emojiBox.resize(int(150/eh*ew), 150); self.emojiBox.move(self.startX+int((150-150/eh*ew)/2), self.startY+20)
                self.gif = QMovie("data/temp/%s" % self.emoji); self.emojiBox.setMovie(self.gif)
                self.emojiBox.setScaledContents(True); self.gif.start()
                self.emojiBox.setStyleSheet("background-color: transparent;")

            def showUserInfo(self):
                cw = core.feachat.chatWindow.mainWindow; cw.close_content(); cw.content = cw.userInfoContent(cw, self.sender)

        def __init__(self, parent, number):
            super().__init__(parent)
            self.number = number; self.chat_message = []
            self.loaded_message = 0
            self.loadMessage()
            self.resize(600, 560); self.move(360, 64)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
            self.verticalScrollBar().valueChanged.connect(self.isTop)
            self.setStyleSheet("QListWidget {background-color: transparent;outline: none;border:0px;}"
                               "QListWidget:Item:hover{background-color: transparent;}"
                               "QListWidget:Item:selected{background-color: transparent;}")
            self.show()

        def relayout(self, x, y, width, height):
            self.setGeometry(x, y, width, height)
            for index in range(self.count()):
                item = self.item(index)
                widget = self.itemWidget(item)
                if hasattr(widget, "relayout"):
                    widget.relayout(width)
                elif widget is not None:
                    widget.update()
            self.scrollToBottom()

        def loadMessage(self):
            all_message = core.feachat.all_message if hasattr(core.feachat, "all_message") else []
            account = core.feachat.account
            self.clear()
            self.chat_message = []
            for msg in all_message:
                number = msg[2] if msg[1] == account else (msg[1] if msg[2] == account else msg[2])
                if number == self.number:
                    self.chat_message.append(msg)
            self.chat_message = self.chat_message[-80:]
            for i in range(len(self.chat_message)):
                self.addBox(self.chat_message, i)
            self.loaded_message = len(self.chat_message)
            QTimer.singleShot(0, self.scrollToBottom)

        def addBox(self, message_info, index):
            account = core.feachat.account
            msg = message_info[index]
            if index == 0 or compare_time(msg[3], message_info[index - 1][3]) > 300:
                titem = QListWidgetItem()
                self.addItem(titem)
                self.setItemWidget(titem, self.timeBox(titem, msg[3]))
            item = QListWidgetItem()
            if msg[4] == "text":
                self.addItem(item)
                self.setItemWidget(item, self.rightTextBox(item, msg) if msg[1] == account else self.leftTextBox(item, msg))
            elif msg[4] == "file":
                self.addItem(item)
                self.setItemWidget(item, self.rightFileBox(item, msg) if msg[1] == account else self.leftFileBox(item, msg))
            elif msg[4] == "link":
                self.addItem(item)
                self.setItemWidget(item, self.rightLinkBox(item, msg) if msg[1] == account else self.leftLinkBox(item, msg))
            elif msg[4] == "emoji":
                self.addItem(item)
                self.setItemWidget(item, self.rightEmojiBox(item, msg) if msg[1] == account else self.leftEmojiBox(item, msg))
            self.scrollToBottom()

        def isTop(self):
            pass

        def mouseReleaseEvent(self, event):
            core.feachat.chatWindow.mainWindow.retakeMore()
            super().mouseReleaseEvent(event)

    class userInfoContent(QWidget):
        def __init__(self, parent, number):
            super().__init__(parent)
            info = get_user_info(number)
            self.nickname = info[0]
            profile_picture = info[1]; background_picture = info[2]; self.motto = info[5]
            download_file(profile_picture, "data"); download_file(background_picture, "data")
            self.img1 = QPixmap("data/temp/%s" % profile_picture)
            self.img2 = QPixmap("data/temp/%s" % background_picture)
            core.feachat.chatWindow.mainWindow.titleText.setText(self.nickname)
            self.resize(750, 765); self.move(450, 75)
            self.setStyleSheet("background-color: transparent;")
            self.backgroundPictureArea = QLabel(self); self.backgroundPictureArea.resize(750, 250)
            self.backgroundPictureArea.move(0, 0); self.backgroundPictureArea.setPixmap(self.img2)
            self.backgroundPictureArea.setScaledContents(True)
            self.profilePictureArea = QLabel(self); self.profilePictureArea.resize(100, 100)
            self.profilePictureArea.move(75, 200); self.profilePictureArea.setPixmap(self.img1)
            self.profilePictureArea.setScaledContents(True)
            self.profilePictureArea.setStyleSheet("background-color: transparent;")
            self.nicknameArea = QLabel(self); self.nicknameArea.resize(560, 50)
            self.nicknameArea.move(190, 200); self.nicknameArea.setText(self.nickname)
            self.nicknameArea.setStyleSheet("font-family: Microsoft YaHei;font-size: 30px;color: #ffffff;background-color: transparent;")
            self.mottoArea = QLabel(self); self.mottoArea.resize(545, 100)
            self.mottoArea.move(190, 260); self.mottoArea.setWordWrap(True); self.mottoArea.setText(self.motto)
            self.mottoArea.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.mottoArea.setStyleSheet("font-family: Microsoft YaHei;font-size: 18px;color: #000000;background-color: transparent;")
            self.show()

        def relayout(self, x, y, width, height):
            self.setGeometry(x, y, width, height)
            bg_h = min(230, max(170, int(height * 0.34)))
            self.backgroundPictureArea.setGeometry(0, 0, width, bg_h)
            avatar_size = 86
            avatar_y = max(110, bg_h - 46)
            self.profilePictureArea.setGeometry(56, avatar_y, avatar_size, avatar_size)
            self.nicknameArea.setGeometry(160, avatar_y, max(120, width - 180), 46)
            self.mottoArea.setGeometry(160, avatar_y + 58, max(120, width - 180), max(80, height - avatar_y - 70))

        def mouseReleaseEvent(self, event):
            core.feachat.chatWindow.mainWindow.retakeMore()
            super().mouseReleaseEvent(event)

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        core.feachat.user_info[core.feachat.account] = get_user_info(core.feachat.account)
        self.page = ""
        self.list = []
        self.moreFlag = False
        self.initWindow()
        self.initMenuArea(); self.initListArea(); self.initContentArea()
        self.initAvatarArea(); self.initSearchArea(); self.initTitleArea()
        self.initMenuFilling(); self.initContentFilling()
        self.initAvatarFilling1(); self.initAvatarFilling2()
        self.initTitleFilling1(); self.initTitleFilling2()
        self.initCloseButton(); self.initMinButton()
        self.initChatsButton(); self.initContactsButton(); self.initMomentsButton()
        self.initFavoritesButton(); self.initMyselfButton()
        self.initFileManagerButton(); self.initSettingButton(); self.initlogOutButton()
        self.initAvatar()
        self.initSearchFilling(); self.initSearchIconArea(); self.initSearchIcon()
        self.initSearchBox(); self.initMoreButton(); self.initTitleText()
        self.initMessageComposer()
        self.initMessagePolling()
        self.titleText.setText("FeaChat")
        self.switchChats()
        self.layoutUi()

    def initWindow(self):
        self.width = 960; self.height = 680; self.minWidth = 840; self.minHeight = 560
        self.titleWidth = self.width; self.titleHeight = 75
        self.resize(self.width, self.height)
        self.window.setWindowTitle("FeaChat")
        self.window.setWindowIcon(QIcon("pic/logo/logo.png"))

    def initMenuArea(self):
        self.menuArea = QLabel(self); self.menuArea.resize(75, 840); self.menuArea.move(0, 0)
        self.menuArea.setStyleSheet("background-color: #0076F6;border-radius: 10px;")

    def initListArea(self):
        self.listArea = QLabel(self); self.listArea.resize(375, 840); self.listArea.move(75, 0)
        self.listArea.setStyleSheet("background-color: #ffffff;")

    def initContentArea(self):
        self.contentArea = QLabel(self); self.contentArea.resize(750, 840); self.contentArea.move(450, 0)
        self.contentArea.setStyleSheet("background-color: #f5f5f5;border-radius: 10px;")

    def initAvatarArea(self):
        self.avaterArea = QLabel(self); self.avaterArea.resize(75, 75); self.avaterArea.move(0, 0)
        self.avaterArea.setStyleSheet("background-color: #0062cd;border-radius: 10px;")

    def initSearchArea(self):
        self.searchArea = QLabel(self); self.searchArea.resize(375, 75); self.searchArea.move(75, 0)
        self.searchArea.setStyleSheet("background-color: #f5f5f5")

    def initTitleArea(self):
        self.titleArea = QLabel(self); self.titleArea.resize(750, 75); self.titleArea.move(450, 0)
        self.titleArea.setStyleSheet("background-color: #e5e5e5;border-radius: 10px;")

    def initMenuFilling(self):
        self.menuFilling = QLabel(self); self.menuFilling.resize(10, 10); self.menuFilling.move(65, 830)
        self.menuFilling.setStyleSheet("background-color: #0076F6;")

    def initContentFilling(self):
        self.contentFilling = QLabel(self); self.contentFilling.resize(10, 840); self.contentFilling.move(450, 0)
        self.contentFilling.setStyleSheet("background-color: #f5f5f5;")

    def initAvatarFilling1(self):
        self.avaterFilling1 = QLabel(self); self.avaterFilling1.resize(10, 75); self.avaterFilling1.move(65, 0)
        self.avaterFilling1.setStyleSheet("background-color: #0062cd;")

    def initAvatarFilling2(self):
        self.avaterFilling2 = QLabel(self); self.avaterFilling2.resize(10, 10); self.avaterFilling2.move(0, 65)
        self.avaterFilling2.setStyleSheet("background-color: #0062cd;")

    def initTitleFilling1(self):
        self.titleFilling1 = QLabel(self); self.titleFilling1.resize(10, 75); self.titleFilling1.move(450, 0)
        self.titleFilling1.setStyleSheet("background-color: #e5e5e5;")

    def initTitleFilling2(self):
        self.titleFilling2 = QLabel(self); self.titleFilling2.resize(10, 10); self.titleFilling2.move(1190, 65)
        self.titleFilling2.setStyleSheet("background-color: #e5e5e5;")

    def initCloseButton(self):
        self.closeButton = QPushButton(self); self.closeButton.resize(45, 35); self.closeButton.move(1150, 5)
        self.closeButton.setText("×"); self.closeButton.clicked.connect(self.window.close)
        self.closeButton.setToolTip("Close"); self.closeButton.setObjectName("closeButton")
        self.closeButton.setStyleSheet("QPushButton#closeButton{font-family: Microsoft YaHei;font-size: 25px;color: #555555;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton#closeButton:hover{background-color: #d1d1d1;}QPushButton#closeButton:pressed{background-color: #b9b9b9;}")

    def initMinButton(self):
        self.minButton = QPushButton(self); self.minButton.resize(45, 35); self.minButton.move(1100, 5)
        self.minButton.setText("-"); self.minButton.clicked.connect(self.window.showMinimized)
        self.minButton.setToolTip("Minimize"); self.minButton.setObjectName("minButton")
        self.minButton.setStyleSheet("QPushButton#minButton{font-family: Microsoft YaHei;font-size: 30px;color: #555555;background-color: transparent;border: 0px;border-radius: 5px;}QPushButton#minButton:hover{background-color: #d1d1d1;}QPushButton#minButton:pressed{background-color: #b9b9b9;}")

    def initChatsButton(self):
        self.chatsButton = QPushButton(self); self.chatsButton.resize(75, 75); self.chatsButton.move(0, 75)
        self.chatsButton.setToolTip("Chats"); self.chatsButton.clicked.connect(self.switchChats)
        self.chatsButton.setObjectName("chatsButton")
        self.chatsButton.setStyleSheet("QPushButton#chatsButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/chats1.png);}QPushButton#chatsButton:hover{background-color: #006bdf;}QPushButton#chatsButton:pressed{background-color: #0062cd;}")

    def initContactsButton(self):
        self.contactsButton = QPushButton(self); self.contactsButton.resize(75, 75); self.contactsButton.move(0, 150)
        self.contactsButton.clicked.connect(self.switchContacts); self.contactsButton.setToolTip("Contacts")
        self.contactsButton.setObjectName("contactsButton")
        self.contactsButton.setStyleSheet("QPushButton#contactsButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/contacts1.png);}QPushButton#contactsButton:hover{background-color: #006bdf;}QPushButton#contactsButton:pressed{background-color: #0062cd;}")

    def initMomentsButton(self):
        self.momentsButton = QPushButton(self); self.momentsButton.resize(75, 75); self.momentsButton.move(0, 225)
        self.momentsButton.clicked.connect(self.switchMoments); self.momentsButton.setToolTip("Moments")
        self.momentsButton.setObjectName("momentsButton")
        self.momentsButton.setStyleSheet("QPushButton#momentsButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/moments1.png);}QPushButton#momentsButton:hover{background-color: #006bdf;}QPushButton#momentsButton:pressed{background-color: #0062cd;}")

    def initFavoritesButton(self):
        self.favoritesButton = QPushButton(self); self.favoritesButton.resize(75, 75); self.favoritesButton.move(0, 300)
        self.favoritesButton.clicked.connect(self.switchFavorites); self.favoritesButton.setToolTip("Favorites")
        self.favoritesButton.setObjectName("favoritesButton")
        self.favoritesButton.setStyleSheet("QPushButton#favoritesButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/favourites1.png);}QPushButton#favoritesButton:hover{background-color: #006bdf;}QPushButton#favoritesButton:pressed{background-color: #0062cd;}")

    def initMyselfButton(self):
        self.myselfButton = QPushButton(self); self.myselfButton.resize(75, 75); self.myselfButton.move(0, 375)
        self.myselfButton.clicked.connect(self.switchMyself); self.myselfButton.setToolTip("Myself")
        self.myselfButton.setObjectName("myselfButton")
        self.myselfButton.setStyleSheet("QPushButton#myselfButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/myself1.png);}QPushButton#myselfButton:hover{background-color: #006bdf;}QPushButton#myselfButton:pressed{background-color: #0062cd;}")

    def initFileManagerButton(self):
        self.fileManagerButton = QPushButton(self); self.fileManagerButton.resize(75, 75); self.fileManagerButton.move(0, 575)
        self.fileManagerButton.clicked.connect(self.openFileManager); self.fileManagerButton.setToolTip("File Manager")
        self.fileManagerButton.setObjectName("fileManagerButton")
        self.fileManagerButton.setStyleSheet("QPushButton#fileManagerButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/file manager.png);}QPushButton#fileManagerButton:hover{background-color: #006bdf;}QPushButton#fileManagerButton:pressed{background-color: #0062cd;}")

    def initSettingButton(self):
        self.settingButton = QPushButton(self); self.settingButton.resize(75, 75); self.settingButton.move(0, 650)
        self.settingButton.clicked.connect(self.openSetting); self.settingButton.setToolTip("Setting")
        self.settingButton.setObjectName("settingButton")
        self.settingButton.setStyleSheet("QPushButton#settingButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/setting.png);}QPushButton#settingButton:hover{background-color: #006bdf;}QPushButton#settingButton:pressed{background-color: #0062cd;}")

    def initlogOutButton(self):
        self.logOutButton = QPushButton(self); self.logOutButton.resize(75, 75); self.logOutButton.move(0, 725)
        self.logOutButton.clicked.connect(self.logOut); self.logOutButton.setToolTip("Log out")
        self.logOutButton.setObjectName("logOutButton")
        self.logOutButton.setStyleSheet("QPushButton#logOutButton{background-color: transparent;border: 0px;border-image: url(pic/chatUi/log out.png);}QPushButton#logOutButton:hover{background-color: #006bdf;}QPushButton#logOutButton:pressed{background-color: #0062cd;}")

    def initAvatar(self):
        self.avatar = QLabel(self); self.avatar.resize(50, 50); self.avatar.move(12, 12)
        avatar = core.feachat.user_info[core.feachat.account][1]
        download_file(avatar, "data")
        self.avatar.setPixmap(QPixmap("data/temp/%s" % avatar))
        self.avatar.setScaledContents(True); self.avatar.setStyleSheet("background-color: transparent;")

    def initSearchFilling(self):
        self.searchFilling = QLabel(self); self.searchFilling.resize(275, 40); self.searchFilling.move(100, 17)
        self.searchFilling.setStyleSheet("background-color: #e0e0e0;border: 0px;border-radius: 5px;")

    def initSearchIconArea(self):
        self.searchIconArea = QLabel(self); self.searchIconArea.resize(40, 40); self.searchIconArea.move(100, 17)
        self.searchIconArea.setStyleSheet("background-color: #e0e0e0;border: 0px;border-top-left-radius: 5px;border-bottom-left-radius: 5px;")

    def initSearchIcon(self):
        self.searchIcon = QLabel(self); self.searchIcon.resize(25, 25); self.searchIcon.move(107, 24)
        self.searchIcon.setPixmap(QPixmap("pic/chatUi/search.png")); self.searchIcon.setScaledContents(True)
        self.searchIcon.setStyleSheet("background-color: transparent;")

    def initSearchBox(self):
        self.searchBox = QLineEdit(self); self.searchBox.resize(225, 40); self.searchBox.move(140, 17)
        self.searchBox.textChanged.connect(self.search); self.searchBox.setPlaceholderText("Search")
        self.searchBox.setStyleSheet("background-color: transparent;border: 0px;font-family: Arial;font-size: 18px;color: #222222;")

    def initMoreButton(self):
        self.moreButton = QPushButton(self); self.moreButton.resize(40, 40); self.moreButton.move(385, 17)
        self.moreButton.clicked.connect(self.clickedMore); self.moreButton.setToolTip("More")
        self.moreButton.setObjectName("moreButton")
        self.moreButton.setStyleSheet("QPushButton#moreButton{background-color: #e0e0e0;border: 0px;border-radius: 5px;border-image: url(pic/chatUi/more.png);}QPushButton#moreButton:hover{background-color: #d1d1d1;}QPushButton#moreButton:pressed{background-color: #b9b9b9;}")

    def initTitleText(self):
        self.titleText = QLabel(self); self.titleText.resize(610, 75); self.titleText.move(480, 0)
        self.titleText.setStyleSheet("font-family: Microsoft YaHei;font-size: 30px;color: #000000;background-color: transparent;")

    def initMessageComposer(self):
        self.messageInput = QLineEdit(self)
        self.messageInput.resize(620, 45)
        self.messageInput.move(470, 780)
        self.messageInput.setPlaceholderText("Type a message")
        self.messageInput.returnPressed.connect(self.sendCurrentText)
        self.messageInput.setStyleSheet("background-color: #ffffff;border: 1px solid #c7c7c7;border-radius: 5px;font-family: Arial;font-size: 16px;color: #111111;padding-left: 12px;selection-background-color: #b6d7ff;")
        self.sendButton = QPushButton(self)
        self.sendButton.resize(80, 45)
        self.sendButton.move(1100, 780)
        self.sendButton.setText("Send")
        self.sendButton.clicked.connect(self.sendCurrentText)
        self.sendButton.setStyleSheet("QPushButton{font-family: Microsoft YaHei;font-size: 18px;color: #ffffff;background-color: #0076F6;border: 0px;border-radius: 5px;}QPushButton:hover{background-color: #006bdf;}QPushButton:pressed{background-color: #0062cd;}QPushButton:disabled{background-color: #a9c9ee;}")
        self.setComposerEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layoutUi()

    def layoutUi(self):
        width = self.size().width()
        height = self.size().height()
        menu_w = 68
        list_w = max(280, min(330, int(width * 0.32)))
        title_h = 64
        composer_h = 58
        content_x = menu_w + list_w
        content_w = max(360, width - content_x)

        self.width = width
        self.height = height
        self.titleWidth = width
        self.titleHeight = title_h
        self.menuWidth = menu_w
        self.listWidth = list_w
        self.contentX = content_x
        self.contentW = content_w
        self.contentTop = title_h
        self.composerHeight = composer_h

        if hasattr(self, "menuArea"):
            self.menuArea.setGeometry(0, 0, menu_w, height)
        if hasattr(self, "listArea"):
            self.listArea.setGeometry(menu_w, 0, list_w, height)
        if hasattr(self, "contentArea"):
            self.contentArea.setGeometry(content_x, 0, content_w, height)
        if hasattr(self, "avaterArea"):
            self.avaterArea.setGeometry(0, 0, menu_w, title_h)
        if hasattr(self, "searchArea"):
            self.searchArea.setGeometry(menu_w, 0, list_w, title_h)
        if hasattr(self, "titleArea"):
            self.titleArea.setGeometry(content_x, 0, content_w, title_h)
        if hasattr(self, "menuFilling"):
            self.menuFilling.setGeometry(menu_w - 10, height - 10, 10, 10)
        if hasattr(self, "contentFilling"):
            self.contentFilling.setGeometry(content_x, 0, 10, height)
        if hasattr(self, "avaterFilling1"):
            self.avaterFilling1.setGeometry(menu_w - 10, 0, 10, title_h)
        if hasattr(self, "avaterFilling2"):
            self.avaterFilling2.setGeometry(0, title_h - 10, 10, 10)
        if hasattr(self, "titleFilling1"):
            self.titleFilling1.setGeometry(content_x, 0, 10, title_h)
        if hasattr(self, "titleFilling2"):
            self.titleFilling2.setGeometry(width - 10, title_h - 10, 10, 10)
        if hasattr(self, "closeButton"):
            self.closeButton.setGeometry(width - 50, 5, 42, 32)
        if hasattr(self, "minButton"):
            self.minButton.setGeometry(width - 96, 5, 42, 32)

        nav_buttons = [
            ("chatsButton", title_h),
            ("contactsButton", title_h + menu_w),
            ("momentsButton", title_h + menu_w * 2),
            ("favoritesButton", title_h + menu_w * 3),
            ("myselfButton", title_h + menu_w * 4),
        ]
        for name, y in nav_buttons:
            if hasattr(self, name):
                getattr(self, name).setGeometry(0, y, menu_w, menu_w)
        bottom_buttons = ["fileManagerButton", "settingButton", "logOutButton"]
        for offset, name in enumerate(bottom_buttons[::-1], start=1):
            if hasattr(self, name):
                getattr(self, name).setGeometry(0, max(title_h, height - menu_w * offset), menu_w, menu_w)
        if hasattr(self, "avatar"):
            avatar_size = 46
            self.avatar.setGeometry((menu_w - avatar_size) // 2, (title_h - avatar_size) // 2, avatar_size, avatar_size)

        search_x = menu_w + 18
        search_w = max(160, list_w - 76)
        if hasattr(self, "searchFilling"):
            self.searchFilling.setGeometry(search_x, 14, search_w, 36)
        if hasattr(self, "searchIconArea"):
            self.searchIconArea.setGeometry(search_x, 14, 36, 36)
        if hasattr(self, "searchIcon"):
            self.searchIcon.setGeometry(search_x + 9, 23, 18, 18)
        if hasattr(self, "searchBox"):
            self.searchBox.setGeometry(search_x + 36, 14, max(80, search_w - 42), 36)
        if hasattr(self, "moreButton"):
            self.moreButton.setGeometry(menu_w + list_w - 50, 14, 36, 36)
        if hasattr(self, "titleText"):
            self.titleText.setGeometry(content_x + 24, 0, max(100, content_w - 130), title_h)
            self.titleText.setStyleSheet("font-family: Arial;font-size: 24px;color: #000000;background-color: transparent;")

        input_visible = hasattr(self, "messageInput") and self.messageInput.isVisible()
        content_bottom = height - composer_h if input_visible else height
        if hasattr(self, "messageInput"):
            self.messageInput.setGeometry(content_x + 20, height - 48, max(120, content_w - 120), 38)
        if hasattr(self, "sendButton"):
            self.sendButton.setGeometry(width - 90, height - 48, 70, 38)

        for layout in getattr(self, "list", []):
            if isinstance(layout, self.expandMoreArea):
                layout.setGeometry(menu_w + list_w - 208, title_h - 4, 200, 150)
            else:
                layout.setGeometry(menu_w, title_h, list_w, max(1, height - title_h))
        if hasattr(self, "content") and self.content is not None:
            if isinstance(self.content, self.messageContent):
                self.content.relayout(content_x, title_h, content_w, max(1, content_bottom - title_h))
            elif hasattr(self.content, "relayout"):
                self.content.relayout(content_x, title_h, content_w, max(1, height - title_h))
            else:
                self.content.setGeometry(content_x, title_h, content_w, max(1, height - title_h))

    def initMessagePolling(self):
        self.messagePoller = QTimer(self)
        self.messagePoller.timeout.connect(self.refreshMessages)
        if not DEV_MODE:
            self.messagePoller.start(2000)

    def setComposerEnabled(self, enabled):
        connected = DEV_MODE or getattr(core.feachat, "connect", False)
        self.messageInput.setVisible(enabled)
        self.sendButton.setVisible(enabled)
        self.messageInput.setEnabled(enabled and connected)
        self.sendButton.setEnabled(enabled and connected)
        if not enabled:
            self.messageInput.clear()
        if enabled and not connected:
            self.messageInput.setPlaceholderText("Server not connected")
        else:
            self.messageInput.setPlaceholderText("Type a message")

    def sendCurrentText(self):
        if "content" not in vars(self) or not isinstance(self.content, self.messageContent):
            return
        text = self.messageInput.text().strip()
        if not text:
            return
        request = core.feachat.sendMessage(self.content.number, "text", text)
        if request[0]:
            self.messageInput.clear()
            self.titleText.setText(core.feachat.user_info[self.content.number][0])
            self.new_message(request[1])
        else:
            self.titleText.setText(f"Send failed: {request[1]}")

    def refreshMessages(self):
        old_ids = {msg[0] for msg in getattr(core.feachat, "all_message", [])}
        request = core.feachat.getMessages()
        if not request[0]:
            return
        for message in request[1]:
            if message[0] not in old_ids:
                self.new_message(message)

    def expandMore(self):
        self.moreFlag = True; self.more = self.expandMoreArea(self)
        self.layoutUi()
        self.moreButton.setStyleSheet("QPushButton#moreButton{background-color: #b9b9b9;border: 0px;border-radius: 5px;border-image: url(pic/chatUi/more.png);}")

    def retakeMore(self):
        try:
            self.moreFlag = False; self.more.close()
            self.moreButton.setStyleSheet("QPushButton#moreButton{background-color: #e0e0e0;border: 0px;border-radius: 5px;border-image: url(pic/chatUi/more.png);}QPushButton#moreButton:hover{background-color: #d1d1d1;}QPushButton#moreButton:pressed{background-color: #b9b9b9;}")
        except: pass

    def setButtonStyle(self):
        styles = {
            "chatsButton": ("pic/chatUi/chats1.png", "pic/chatUi/chats2.png", "Chats"),
            "contactsButton": ("pic/chatUi/contacts1.png", "pic/chatUi/contacts2.png", "Contacts"),
            "momentsButton": ("pic/chatUi/moments1.png", "pic/chatUi/moments2.png", "Moments"),
            "favoritesButton": ("pic/chatUi/favourites1.png", "pic/chatUi/favourites2.png", "Favourites"),
            "myselfButton": ("pic/chatUi/myself1.png", "pic/chatUi/myself2.png", "Myself"),
        }
        for name, (img1, img2, page) in styles.items():
            btn = getattr(self, name)
            obj = name
            if self.page == page:
                btn.setStyleSheet("QPushButton#%s{background-color: #0062cd;border: 0px;border-image: url(%s);}" % (obj, img2))
            else:
                btn.setStyleSheet("QPushButton#%s{background-color: transparent;border: 0px;border-image: url(%s);}QPushButton#%s:hover{background-color: #006bdf;}QPushButton#%s:pressed{background-color: #0062cd;}" % (obj, img1, obj, obj))

    def switchChats(self):
        self.page = "Chats"; self.setButtonStyle(); self.retakeMore(); self.close_list(); self.close_content()
        self.titleText.setText("Chats")
        self.setComposerEnabled(False)
        self.set_list(self.chatList(self))

    def switchContacts(self):
        self.page = "Contacts"; self.setButtonStyle(); self.retakeMore(); self.close_list(); self.close_content()
        self.titleText.setText("Contacts")
        self.setComposerEnabled(False)
        self.set_list(self.contactList(self))

    def switchMoments(self):
        self.page = "Moments"; self.setButtonStyle(); self.retakeMore(); self.close_list(); self.close_content()
        self.titleText.setText("Moments")
        self.setComposerEnabled(False)

    def switchFavorites(self):
        self.page = "Favourites"; self.setButtonStyle(); self.retakeMore(); self.close_list(); self.close_content()
        self.titleText.setText("Favourites")
        self.setComposerEnabled(False)

    def switchMyself(self):
        self.page = "Myself"; self.setButtonStyle(); self.retakeMore(); self.close_list(); self.close_content()
        self.titleText.setText("Myself")
        self.setComposerEnabled(False)

    def openSetting(self):
        from ui.dialogs import settingUi
        from ui.shadow import uiShadow
        self.retakeMore()
        if "settingWindow" in vars(self) and self.settingWindow.isVisible():
            self.settingWindow.showNormal(); self.settingWindow.raise_()
        else:
            self.settingWindow = uiShadow(settingUi); core.feachat.app.exec_()

    def openFileManager(self):
        from ui.dialogs import fileManagerUi
        from ui.shadow import uiShadow
        self.retakeMore()
        if "fileManagerWindow" in vars(self) and self.fileManagerWindow.isVisible():
            self.fileManagerWindow.showNormal(); self.fileManagerWindow.raise_()
        else:
            self.fileManagerWindow = uiShadow(fileManagerUi); core.feachat.app.exec_()

    def logOut(self):
        from ui.dialogs import messageBoxUi
        from ui.shadow import uiShadow
        self.retakeMore()
        self.messageBox = uiShadow(messageBoxUi, self, "Log out",
                                   "You won't be notified of any new messages after logging out. Confirm to log out.",
                                   sys.exit)

    def search(self):
        self.retakeMore()
        if self.list and isinstance(self.list[-1], self.searchList):
            self.remove_list()
        if self.searchBox.text() != "":
            self.set_list(self.searchList(self))

    def clickedMore(self):
        if not self.moreFlag: self.expandMore()
        else: self.retakeMore()

    def close_list(self):
        try: self.searchBox.setText("")
        except: pass
        for i in range(len(self.list) - 1, -1, -1):
            self.list[i].close(); del self.list[i]

    def set_list(self, layout):
        self.list.append(layout)
        self.layoutUi()
    def remove_list(self): self.list[-1].close(); del self.list[-1]
    def close_content(self):
        if "content" in vars(self): self.content.close()
    def set_content(self, layout):
        self.content = layout
        self.setComposerEnabled(isinstance(layout, self.messageContent))
        self.layoutUi()

    def new_message(self, message):
        import _thread, sys
        account = core.feachat.account
        user_info = core.feachat.user_info
        all_message = core.feachat.all_message if hasattr(core.feachat, "all_message") else []
        if any(existing[0] == message[0] for existing in all_message):
            return
        all_message.append(message)

        number = message[2] if message[1] == account else (message[1] if message[2] == account else message[2])
        if number not in user_info:
            user_info[number] = get_user_info(number)
            download_file(user_info[number][1], "data"); download_file(user_info[number][2], "data")

        content_is_current_chat = (
            "content" in vars(self)
            and isinstance(self.content, self.messageContent)
            and number == self.content.number
        )
        if content_is_current_chat:
            self.content.chat_message.append(message)
            self.content.addBox(self.content.chat_message, len(self.content.chat_message) - 1)
            self.content.loaded_message += 1

        if self.page == "Chats" and self.list and isinstance(self.list[0], self.chatList):
            if content_is_current_chat:
                if number in self.list[0].number_item:
                    item = self.list[0].number_item[number]
                    self.list[0].takeItem(self.list[0].row(item))
                item = QListWidgetItem(); self.list[0].number_item[number] = item
                self.list[0].insertItem(0, item)
                self.list[0].setItemWidget(item, self.list[0].chatsSelectBox(item, number, message))
                self.list[0].setCurrentItem(self.list[0].number_item[number])
            else:
                notReceived = 0
                if number in self.list[0].number_item:
                    item = self.list[0].number_item[number]
                    notReceived = self.list[0].itemWidget(item).notReceived
                    self.list[0].takeItem(self.list[0].row(item))
                item = QListWidgetItem(); self.list[0].number_item[number] = item
                self.list[0].insertItem(0, item)
                self.list[0].setItemWidget(item, self.list[0].chatsSelectBox(item, number, message))
                if message[1] != account:
                    self.list[0].itemWidget(item).setNotReceived(notReceived + 1)

    def mouseReleaseEvent(self, event):
        self.retakeMore(); super().mouseReleaseEvent(event)


# 辅助函数（原来是全局函数，这里保留为模块级）
import os, sys

def message_area_width(default=600):
    try:
        cw = core.feachat.chatWindow.mainWindow
        if hasattr(cw, "content") and isinstance(cw.content, chatUi.messageContent):
            return max(360, cw.content.viewport().width())
        return max(360, getattr(cw, "contentW", default))
    except Exception:
        return default

def set_time(datetime):
    return datetime  # placeholder，正式版由服务器逻辑实现

def compare_time(dt1, dt2):
    import time
    try:
        t1 = time.mktime(time.strptime(dt1, "%Y-%m-%d %H:%M:%S"))
        t2 = time.mktime(time.strptime(dt2, "%Y-%m-%d %H:%M:%S"))
        return t1 - t2
    except: return 0

def set_size(size):
    unit = ["B", "KB", "MB", "GB", "TB"]; count = 0
    while size >= 1024: size /= 1024; count += 1
    return str(round(size, 1)) + unit[count]
