# _*_coding:utf-8_*_

import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core


class uiShadow(QWidget):
    def __init__(self, *info):
        super().__init__()
        self.press = False
        self.resizeEdge = None
        self.resizeMargin = 10
        self.radius = 10
        self.color = "#212121"
        self.initWindow(info)
        self.addShadow()
        self.show()
        core.feachat.app.exec_()

    def initWindow(self, info):
        window = info[0]
        self.mainWindow = window(self, *info[1:])
        if window.__name__ == "chatUi":
            core.feachat.chatWindow = self
        elif window.__name__ == "loginUi":
            core.feachat.loginWindow = self
        self.mainWindow.move(self.radius, self.radius)
        outer_width = self.mainWindow.width + self.radius * 2
        outer_height = self.mainWindow.height + self.radius * 2
        self.resize(outer_width, outer_height)
        min_width = getattr(self.mainWindow, "minWidth", self.mainWindow.width)
        min_height = getattr(self.mainWindow, "minHeight", self.mainWindow.height)
        self.setMinimumSize(min_width + self.radius * 2, min_height + self.radius * 2)
        self.setMouseTracking(True)
        self.mainWindow.setMouseTracking(True)
        self.mainWindow.installEventFilter(self)
        for child in self.mainWindow.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)
        self.move(self.center())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

    def addShadow(self):
        self.effectShadow = QGraphicsDropShadowEffect(self)
        self.effectShadow.setOffset(0, 0)
        self.effectShadow.setBlurRadius(self.radius)
        self.effectShadow.setColor(QColor(self.color))
        self.mainWindow.setGraphicsEffect(self.effectShadow)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        self.raise_()
        self.activateWindow()
        self.windowX = self.x()
        self.windowY = self.y()
        self.windowWidth = self.width()
        self.windowHeight = self.height()
        self.startPos = event.globalPos()
        pos = event.windowPos()
        self.resizeEdge = self.edgeAt(pos)
        if self.resizeEdge:
            self.grabMouse()
            return
        if pos.x() >= self.radius and pos.x() <= self.mainWindow.titleWidth + self.radius:
            if pos.y() >= self.radius and pos.y() <= self.mainWindow.titleHeight + self.radius:
                self.press = True

    def mouseReleaseEvent(self, event):
        self.windowX = self.x()
        self.windowY = self.y()
        self.press = False
        self.resizeEdge = None
        if QWidget.mouseGrabber() == self:
            self.releaseMouse()
        self.updateCursor(event.windowPos())

    def mouseMoveEvent(self, event):
        delta = event.globalPos() - self.startPos if hasattr(self, "startPos") else QPoint(0, 0)
        if self.resizeEdge:
            self.resizeFromEdge(delta.x(), delta.y())
        elif self.press:
            self.move(self.windowX + delta.x(), self.windowY + delta.y())
        else:
            self.updateCursor(event.windowPos())

    def edgeAt(self, pos):
        # Keep the resize hit-area inside the visible content. On macOS,
        # starting a drag from the transparent shadow margin can drop focus.
        margin = self.radius + self.resizeMargin
        left = pos.x() <= margin
        right = pos.x() >= self.width() - margin
        top = pos.y() <= self.radius
        bottom = pos.y() >= self.height() - margin
        if left and top:
            return "top-left"
        if right and top:
            return "top-right"
        if left and bottom:
            return "bottom-left"
        if right and bottom:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def updateCursor(self, pos):
        edge = self.edgeAt(pos)
        if edge in {"left", "right"}:
            self.setCursor(Qt.SizeHorCursor)
        elif edge in {"top", "bottom"}:
            self.setCursor(Qt.SizeVerCursor)
        elif edge in {"top-left", "bottom-right"}:
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge in {"top-right", "bottom-left"}:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def canResizeFromChild(self, watched, pos):
        if watched in (self, self.mainWindow):
            return True
        if not isinstance(watched, (QPushButton, QLineEdit, QComboBox, QTextEdit, QPlainTextEdit)):
            return True
        hard_margin = self.radius + 4
        return (
            pos.x() <= hard_margin
            or pos.x() >= self.width() - hard_margin
            or pos.y() <= hard_margin
            or pos.y() >= self.height() - hard_margin
        )

    def resizeFromEdge(self, dx, dy):
        min_w = self.minimumWidth()
        min_h = self.minimumHeight()
        x, y = self.windowX, self.windowY
        w, h = self.windowWidth, self.windowHeight

        if "right" in self.resizeEdge:
            w = max(min_w, self.windowWidth + dx)
        if "bottom" in self.resizeEdge:
            h = max(min_h, self.windowHeight + dy)
        if "left" in self.resizeEdge:
            new_w = max(min_w, self.windowWidth - dx)
            x = self.windowX + (self.windowWidth - new_w)
            w = new_w
        if "top" in self.resizeEdge:
            new_h = max(min_h, self.windowHeight - dy)
            y = self.windowY + (self.windowHeight - new_h)
            h = new_h

        self.setGeometry(x, y, w, h)
        self.mainWindow.resize(max(1, w - self.radius * 2), max(1, h - self.radius * 2))

    def eventFilter(self, watched, event):
        if event.type() not in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease):
            return super().eventFilter(watched, event)
        if not hasattr(event, "pos"):
            return super().eventFilter(watched, event)

        pos = watched.mapTo(self, event.pos())
        if event.type() == QEvent.MouseButtonPress:
            if hasattr(event, "button") and event.button() != Qt.LeftButton:
                return super().eventFilter(watched, event)
            edge = self.edgeAt(pos)
            if edge and self.canResizeFromChild(watched, pos):
                self.raise_()
                self.activateWindow()
                self.windowX = self.x()
                self.windowY = self.y()
                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.startPos = event.globalPos()
                self.resizeEdge = edge
                self.grabMouse()
                return True
        elif event.type() == QEvent.MouseMove:
            if self.resizeEdge:
                delta = event.globalPos() - self.startPos
                self.resizeFromEdge(delta.x(), delta.y())
                return True
            if self.canResizeFromChild(watched, pos):
                self.updateCursor(pos)
            else:
                self.setCursor(Qt.ArrowCursor)
        elif event.type() == QEvent.MouseButtonRelease:
            if self.resizeEdge:
                self.resizeEdge = None
                if QWidget.mouseGrabber() == self:
                    self.releaseMouse()
                self.updateCursor(pos)
                return True

        return super().eventFilter(watched, event)

    def center(self):
        window = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        window.moveCenter(center)
        point = window.topLeft()
        offset_x = int(os.getenv("FEACHAT_WINDOW_OFFSET_X", "0"))
        offset_y = int(os.getenv("FEACHAT_WINDOW_OFFSET_Y", "0"))
        return QPoint(point.x() + offset_x, point.y() + offset_y)
