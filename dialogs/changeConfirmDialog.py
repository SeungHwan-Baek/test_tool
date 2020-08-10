import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/change_confirm_dialog.ui"))[0]

class ChangeConfirmDialog(QDialog, dig_class):
    cancle = pyqtSignal("PyQt_PyObject", str)
    changed = pyqtSignal(int)

    appname = '변경적용'
    step = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)

        self.popup_type = ''
        self.step = None
        self.data_list_id = ''
        self.column_id = ''
        self.column_index = -1
        self.row_count = 0
        self.row_index = -1
        self.bef_desc = ''
        self.atf_desc = ''
        self.value = ''
        self.column_component = None

    # ============================ Popup  ============================
    def popUp(self):
        self.exec_()

    def changeDataPopUp(self, step, data_list_id, row_index, column_id, value):
        self.popup_type = 'change_data'
        self.step = step
        self.data_list_id = data_list_id
        self.column_id = column_id
        self.row_index = row_index
        self.value = value
        self.popUp()

    def changeColumnDescPopUp(self, step, data_list_id, column_id, bef_desc, atf_desc, column_component):
        self.popup_type = 'change_column_desc'
        self.step = step
        self.data_list_id = data_list_id
        self.column_id = column_id
        self.bef_desc = bef_desc
        self.atf_desc = atf_desc
        self.column_component = column_component
        self.popUp()


    def addColumnPopUp(self, step, data_list_id, column_id, column_index):
        self.popup_type = 'add_column'
        self.step = step
        self.data_list_id = data_list_id
        self.column_id = column_id
        self.column_index = column_index
        self.popUp()


    def addRowPopUp(self, step, data_list_id, row_count):
        self.popup_type = 'add_row'
        self.step = step
        self.data_list_id = data_list_id
        self.row_count = row_count
        self.popUp()


    def deleteRowPopUp(self, step, data_list_id, row_index):
        self.popup_type = 'delete_row'
        self.step = step
        self.data_list_id = data_list_id
        self.row_index = row_index
        self.popUp()

    def deleteColumnPopUp(self, step, data_list_id, column_id):
        self.popup_type = 'delete_column'
        self.step = step
        self.data_list_id = data_list_id
        self.column_id = column_id
        self.popUp()

    # ============================ Accept ============================
    def accept(self):
        step_list = []

        if self.rb_thisStep.isChecked():
            step_list.append(self.step)
        elif self.rb_thisCase.isChecked():
            case = self.step.getCase()
            step_list = case.findStepByTrxCode(self.step.getTrxCode())
        elif self.rb_thisSuites.isChecked():
            case = self.step.getCase()
            suites = case.getSuites()
            step_list = suites.findStepByTrxCode(self.step.getTrxCode())

        if self.popup_type == 'change_data':
            self._changeDataAccept(step_list)
        elif self.popup_type == 'change_column_desc':
            self._columnDescAccept(step_list)
        elif self.popup_type == 'add_column':
            self._addColumnAccept(step_list)
        elif self.popup_type == 'add_row':
            self._addRowAccept(step_list)
        elif self.popup_type == 'delete_row':
            self._deleteRowAccept(step_list)
        elif self.popup_type == 'delete_column':
            self._deleteColumnAccept(step_list)

        super(ChangeConfirmDialog, self).accept()

    def _changeDataAccept(self, step_list):
        '''
        Data Value 변경적용
        :return: None
        '''
        # 변경적용
        for step in step_list:
            step.setInputDataValue(self.data_list_id, self.row_index, self.column_id, self.value)

        self.changed.emit(len(step_list))

    def _columnDescAccept(self, step_list):
        '''
        Column Description 변경적용
        :return: None
        '''
        # 변경적용
        for step in step_list:
            step.setColumnValue(self.data_list_id, self.column_id, 'description', self.atf_desc)

        self.changed.emit(len(step_list))


    def _addColumnAccept(self, step_list):
        '''
        Column 추가
        :return: None
        '''
        # 변경적용
        for step in step_list:
            step.addColumn(self.data_list_id, self.column_id, self.column_index)

        self.changed.emit(len(step_list))


    def _addRowAccept(self, step_list):
        '''
        Row 추가
        :return: None
        '''
        for step in step_list:
            step.addRow(self.data_list_id, self.row_count)

        self.changed.emit(len(step_list))


    def _deleteRowAccept(self, step_list):
        '''
        Row 삭제
        :return: None
        '''
        for step in step_list:
            step.deleteRow(self.data_list_id, self.row_index)

        self.changed.emit(len(step_list))


    def _deleteColumnAccept(self, step_list):
        '''
        Column 삭제
        :return: None
        '''
        for step in step_list:
            step.deleteColumn(self.data_list_id, self.column_id)

        self.changed.emit(len(step_list))

    # ============================ Reject ============================
    def reject(self):
        if self.popup_type == 'change_column_desc':
            self.cancle.emit(self.column_component, self.bef_desc)
        super(ChangeConfirmDialog, self).reject()