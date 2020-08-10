import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/find_data_dialog.ui"))[0]

class FindDataDialog(QDialog, dig_class):
    findStep = pyqtSignal(int)
    findData = pyqtSignal(int, str, int, str)

    appname = 'Find Data'
    case = None
    start_step_index = 0
    find_data_list_id = ''
    start_row_index = 0
    start_column_index = 0

    def __init__(self):
        super().__init__()
        self.case = None
        self.start_step_index = 0
        self.find_data_list_id = ''
        self.start_row_index = 0
        self.start_column_index = 0
        self.setupUi(self)

        self.setWindowTitle(self.appname)
        self._setEvent()

    def _setEvent(self):
        self.btn_find.clicked.connect(self._btnFindClicked)

    def popUp(self, case):
        self.case = case
        self.start_step_index = self.case.getSelectedStepRow()
        self.find_data_list_id = ''
        self.start_row_index = 0
        self.start_column_index = 0
        self.edt_searchText.setFocus()
        self.exec_()

    def _btnFindClicked(self, none_click):
        if self.cb_searchType.currentText() == 'Step':
            text = self.edt_searchText.text()
            find_index = self.case.findStepByText(text, self.start_step_index)

            if find_index > -1:
                self.start_step_index = find_index + 1
                self.findStep.emit(find_index)
            else:
                if none_click:
                    pass
                else:
                    self.start_step_index = 0
                    self._btnFindClicked(True)
        elif self.cb_searchType.currentText() == 'Data':
            text = self.edt_searchText.text()
            find_step_index, find_data_list_id, find_row_index, find_column_index, find_column_id = self.case.findDataByText(text, self.start_step_index, self.find_data_list_id, self.start_row_index, self.start_column_index)

            if find_step_index > -1:
                self.start_step_index = find_step_index
                self.find_data_list_id = find_data_list_id
                self.start_row_index = find_row_index
                self.start_column_index = find_column_index + 1

                self.findData.emit(find_step_index, find_data_list_id, find_row_index, find_column_id)
            else:
                self.start_step_index = 0
                self.find_data_list_id = ""
                self.start_row_index = 0
                self.start_column_index = 0

                if none_click:
                    pass
                else:
                    self.start_step_index = 0
                    self._btnFindClicked(True)