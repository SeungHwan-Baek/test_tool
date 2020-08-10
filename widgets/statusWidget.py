import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
widget_class = uic.loadUiType(os.path.join(parentDir, "UI/status_widget.ui"))[0]

class StatusWidget(QWidget, widget_class):
    def __init__(self, parent=None):
        super(StatusWidget, self).__init__(parent)
        self.setupUi(self)

        # Component를 투명하게 변경
        #progressbar_list = self.findChildren(QProgressBar)
        edit_list = self.findChildren(QLineEdit)

        transparency_list = edit_list

        for item in transparency_list:
            item.setStyleSheet("background-color: rgba(0,0,0,0%)")

    def setRange(self, min, max):
        self.pb_progressbar.setRange(min, max)

    def setMsg(self, text):
        self.edt_msg.setText(text)