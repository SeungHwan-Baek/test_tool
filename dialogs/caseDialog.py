import sys, os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from libs.case import Case

from dialogs.categoryDialog import CategoryDialog

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/new_test_case.ui"))[0]

class CaseDialog(QDialog, dig_class):

    appname = 'New Test Case'
    case = None
    added = pyqtSignal("PyQt_PyObject")
    changed = pyqtSignal("PyQt_PyObject")

    def __init__(self, call_gubun='New', case=None, category_id='', category_name='', suites=None):
        super().__init__()
        self.setupUi(self)
        self.callGubun = call_gubun
        self.case = case
        self.category_id = category_id
        self.category_name = category_name
        self.suites = suites

        if self.callGubun == 'New':
            self.appname = 'New Test Case'
        else:
            self.appname = 'Test Case'

        self.setWindowTitle(self.appname)
        self._setEvent()

    def accept(self):
        if self.checkValue():
            if self.callGubun == 'New':
                self.case = Case(category=self.category_id, case_type=self.cb_caseType.currentText(), case_seq=self.edt_caseSeq.text(), case_nm=self.edt_caseNm.text())
                self.added.emit(self.case)
            else:
                self.case.setCategory(self.category_id)
                self.case.setCaseType(self.cb_caseType.currentText())
                self.case.setCaseSeq(self.edt_caseSeq.text())
                self.case.setCaseNm(self.edt_caseNm.text())
                self.case.setCaseDesc(self.edt_caseDesc.toPlainText())
                self.changed.emit(self.case)
            self.close()

    def popUp(self):
        if self.callGubun == 'New':
            self.edt_category.setText(self.category_name)
        else:
            self.setValue()

        self.exec_()

    def _setEvent(self):
        # Button Click 이벤트
        self.btn_category.clicked.connect(self._btnCategory)  # category 버튼 클릭 이벤트

    def _btnCategory(self):
        categoryDialog = CategoryDialog(self.suites)
        categoryDialog.selected.connect(self._selectedCategory)
        categoryDialog.popUp(self.category_id)

    def _selectedCategory(self, category_name, category_id):
        self.category_id = category_id
        self.edt_category.setText(category_name)

    def setValue(self):
        category_name = self.case.getCategoryNm()
        self.category_id = self.case.getCategory()

        self.edt_category.setText(category_name)
        self.edt_caseSeq.setText(self.case.caseSeq)
        self.edt_caseNm.setText(self.case.caseNm)
        self.edt_caseDesc.setText(self.case.caseDesc)

        combo_idx = self.cb_caseType.findText(self.case.caseType)
        self.cb_caseType.setCurrentIndex(combo_idx)

    def checkValue(self):
        if self.edt_category.text() == '':
            QMessageBox.information(self, "Add Test Case", "Category를 선택해주세요")
            self.edt_category.setFocus()
            return False

        if self.edt_caseNm.text() == '':
            QMessageBox.information(self, "Add Test Case", "Case Name을 입력하세요")
            return False

        return True
