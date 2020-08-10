import os
from PyQt5.QtWidgets import *
from PyQt5 import uic

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/add_dataInfo.ui"))[0]

class AddDataDialog(QDialog, dig_class):

    appname = 'Add Data Info'
    case = None
    step = None

    def __init__(self, step):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self.edt_dataInfo.setStyleSheet("background-color: white; color: black")
        self.step = None

        self.step = step

    def accept(self):
        if self.checkValue():
            #step = Step(type=self.cb_type.currentText(), target=self.edt_target.text(), description=self.edt_description.text())
            #self.case.setStepList(step)
            self.step.setInputData(self.edt_dataInfo.toPlainText())
            self.close()

    def popUp(self):
        self.exec_()

    def checkValue(self):
        if self.edt_dataInfo.toPlainText() == '':
            QMessageBox.information(self, "Add Data Info", "입력된 값이 없습니다.")
            return False

        return True
