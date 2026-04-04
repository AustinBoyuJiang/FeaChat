# _*_coding:utf-8_*_

import pyautogui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core


class uiShadow(QWidget):
    def __init__(self, *info):
        super().__init__()
        self.press = False
        self.radius = 10
        self.color = "#212121"
        self.initWindow(info)
        self.addShadow()
        self.show()
        core.feachat.app.exec_()

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
        if pos.x() >= self.radius and pos.x() <= self.mainWindow.titleWidth + self.radius:
            if pos.y() >= self.radius and pos.y() <= self.mainWindow.titleHeight + self.radius:
                self.press = True

    def mouseReleaseEvent(self, event):
        self.windowX = self.x()
        self.windowY = self.y()
        self.press = False

    def mouseMoveEvent(self, event):
        if self.press:
            moveX, moveY = pyautogui.position()
            nextX = self.windowX + moveX - self.startX
            nextY = self.windowY + moveY - self.startY
            self.move(nextX, nextY)

    def center(self):
        window = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        window.moveCenter(center)
        return window.topLeft()
