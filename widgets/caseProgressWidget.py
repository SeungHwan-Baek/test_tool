import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
widget_class = uic.loadUiType(os.path.join(parentDir, "UI/case_progress_widget.ui"))[0]

class CaseProgressWidget(QWidget, widget_class):
    def __init__(self, parent=None):
        super(CaseProgressWidget, self).__init__(parent)
        self.setupUi(self)

        self.case = None

        self.setStyleSheet("background-color: rgba(47,79,79,30%)")

        # 모든 Label을 투명하게 변경
        label_list = self.findChildren(QLabel)

        for item in label_list:
            item.setStyleSheet("background-color: rgba(0,0,0,0%)")

    def setCaseDtl(self, case):
        self.case = case
        self.setCaseNm(self.case.getCaseNm())

    def setCaseNm(self, text):
        self.lbl_caseNm.setText(text)
        #print(self.lbl_caseNm.styleSheet())

    def setValue(self, value):
        per = value / 100

        if per < 1:
            self.lbl_caseNm.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop: 0 #1bb77b, stop: ' + str(per) + ' #1bb77b, stop: ' + str(per + 0.001) + ' rgba(0, 0, 0, 0), stop: 1 white)')
        elif per == 1:
            self.lbl_caseNm.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop: 0 #1bb77b, stop: ' + str(per) + ' #1bb77b, stop: ' + str(per) + ' rgba(0, 0, 0, 0), stop: 1 white)')
        else:
            self.lbl_caseNm.setStyleSheet("background-color: rgba(0,0,0,0%)")
        #self.lbl_caseNm.setText('progress %s' % self.value)
        # palette = self.lbl_caseNm.palette()
        # rect = QRectF(self.lbl_caseNm.rect())
        # gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        # gradient.setColorAt(value - 0.001, QColor('#ffffff'))
        # gradient.setColorAt(value, QColor('#f99e41'))
        # gradient.setColorAt(value + 0.001, QColor('#f99e41'))
        # palette.setBrush(QPalette.Base, QBrush(gradient))
        # self.lbl_caseNm.setPalette(palette)
