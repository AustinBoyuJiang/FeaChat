import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class DialogDemo(QMainWindow):
    def __init__(self,parent=None):
        super(DialogDemo, self).__init__(parent)
        #设置主界面的标题及初始大小
        self.setWindowTitle('Dialog例子')
        self.resize(350,300)

        #创建按钮，注意()内的self必不可少，用于加载自身的一些属性设置
        self.btn=QPushButton(self)
        #设置按钮的属性：文本，移动位置，链接槽函数
        self.btn.setText('弹出对话框')
        self.btn.move(50,50)
        self.btn.clicked.connect(self.showdialog)

    def showdialog(self):
        #创建QDialog对象
        self.dialog=messageBoxUi()


class messageBoxUi(QWidget):
    width = 500
    height = 300
    titleWidth = 500
    titleHeight = 40

    def __init__(self):
        super().__init__()
        self.initWindow()
        self.show()

    def initWindow(self):
        self.resize(self.width, self.height)
        self.setWindowModality(Qt.ApplicationModal)

if __name__ == '__main__':
    app=QApplication(sys.argv)
    demo=DialogDemo()
    demo.show()
    sys.exit(app.exec_())