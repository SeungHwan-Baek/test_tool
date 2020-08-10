import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from libs.step import Step
from PyQt5.QtGui import *

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/case_step.ui"))[0]

class CaseStepDialog(QDialog, dig_class):
    changed = pyqtSignal()

    appname = 'Add Step'
    case = None
    selectedStepList = []

    def __init__(self, case=None):
        super().__init__()
        self.setupUi(self)

        self.case = case
        self.setWindowTitle(self.appname)
        self.loadUiInit()

    def loadUiInit(self):
        self.tw_testStep.setColumnWidth(0, 50)  # Check  컬럼 폭 강제 조절
        self.tw_testStep.setColumnWidth(1, 50)  # Seq    컬럼 폭 강제 조절
        self.tw_testStep.setColumnWidth(2, 70)  # Type    컬럼 폭 강제 조절

    def accept(self):
        self.checkStep()
        self.close()

    def popUp(self):
        self.selectedStepList = []
        self.setValue()
        self.exec_()

    def setValue(self):
        self.tw_testStep.setRowCount(0)

        if self.case is not None:
            self.tw_testStep.setRowCount(len(self.case.stepList))

            for idx, step in enumerate(self.case.stepList):
                # Checkbox 설정
                chk = QCheckBox()
                chk_cell_widget = QWidget()
                chk_lay_out = QHBoxLayout(chk_cell_widget)
                chk_lay_out.addWidget(chk)
                chk_lay_out.setAlignment(Qt.AlignCenter)
                chk_lay_out.setContentsMargins(0, 0, 0, 0)
                chk_cell_widget.setLayout(chk_lay_out)

                # Error Option Combo 설정
                # option = ['Error occurred', 'Skip']
                # err_combo = QComboBox()
                # err_combo.addItems(option)

                self.tw_testStep.setCellWidget(idx, 0, chk_cell_widget)
                self.tw_testStep.setItem(idx, 1, QTableWidgetItem(str(step.getSeq())))
                self.tw_testStep.setItem(idx, 2, QTableWidgetItem(step.get('type')))
                self.tw_testStep.setItem(idx, 3, QTableWidgetItem(step.get('target')))
                self.tw_testStep.setItem(idx, 4, QTableWidgetItem(step.get('description')))
                self.tw_testStep.setItem(idx, 5, QTableWidgetItem(step.get('error_option')))


    def checkStep(self):
        self.selectedStepList = []
        for idx in range(self.tw_testStep.rowCount()):
            if self.tw_testStep.cellWidget(idx, 0).findChild(type(QCheckBox())).isChecked():
                self.selectedStepList.append(self.case.stepList[idx])

        return self.selectedStepList
