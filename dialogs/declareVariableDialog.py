import os
import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from libs.variable import Variable

from widgets.variableWidget import VariableWidget


parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/declare_variable_dialog.ui"))[0]

class DeclareVariableDialog(QDialog, dig_class):
    declared = pyqtSignal(str)

    appname = 'Declare Variable'
    step = None
    ref_data_list = []

    def __init__(self, case=None):
        super().__init__()
        self.case = case

        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self._loadUiInit()

        self.ref_data_list = []

    def _loadUiInit(self):
        self.variable_widget = VariableWidget(case=self.case, option=False)
        self.variable_layout.addWidget(self.variable_widget)

    def accept(self):
        if self._checkValue():
            variable_id = self.variable_widget.getVariableId()
            if self._variableIdCheck(variable_id):
                var = self.variable_widget.getVariable()

                self.case.setVariableList(var)
                self.declared.emit(variable_id)
                self.close()

    def popUp(self, variable_type, target=None, sub_id='', row_index=-1, col_id='', col_desc='', value=''):
        if variable_type == 'Data List':
            self.target = target
            target_nm = self.target.get('target')
            target_id = self.target.id
            desc = col_desc

            variable = self.target.getVariable(sub_id, row_index, col_id)

            # 동일 row, column에 해당하는 variable이 존재하는 경우 대체
            if variable:
                variable_type = variable.variable_type
                col_id = variable.get('column_id')
                target_nm = variable.get('target_nm')
                target_id = variable.get('target').id
                row_index = variable.get('row_index')
                desc = variable.get('description')

            column_id_list = target.getColumnList(sub_id)

            self.variable_widget.setTarget(target)
            self.variable_widget.setType(variable_type)
            self.variable_widget.setVariableId('${}$'.format(col_id.upper()))
            self.variable_widget.setTargetNm(target_nm)
            self.variable_widget.setTargetId(target_id)
            self.variable_widget.setSubId(sub_id)
            self.variable_widget.setRowIndexColumnId(column_id_list)
            self.variable_widget.setRowIndex(row_index)
            self.variable_widget.setColumnId(col_id)
            self.variable_widget.setDesc(desc)
            self.variable_widget.setDataListValue(value)
            self.exec_()
        elif variable_type == 'Date':
            self.variable_widget.setType(variable_type)
            self.exec_()
        elif variable_type == 'Excel':
            self.variable_widget.setType(variable_type)
            self.variable_widget.setRefExcelInfo()
            self.exec_()
        elif variable_type == 'Fixed Value':
            self.variable_widget.setType(variable_type)
            self.exec_()
        elif variable_type == 'SVC COMBO (Swing Only)':
            self.variable_widget.setType(variable_type)
            self.variable_widget.setRefSvcComboInfo()
            self.exec_()
        elif variable_type == 'SQL':
            self.variable_widget.setType(variable_type)
            self.variable_widget.setRefSqlInfo()
            self.exec_()
        else:
            QMessageBox.information(self, self.appname, "현재 지원되지 않는 Varialble Type입니다.")
            self.close()


    def _checkValue(self):
        variable_id = self.variable_widget.getVariableId()

        if variable_id == '':
            QMessageBox.information(self, self.appname, "Variable ID를 입력하세요")
            return False

        case_variables = self.case.getVariables()

        if variable_id in list(case_variables.keys()):
            reply = QMessageBox.question(self, self.appname, "Case에 동일한 변수명이 존재합니다. 변수를 변경하시겠습니까?\n[{}]".format(variable_id), QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                pass
            else:
                return False

        return True

    def _variableIdCheck(self, variable_id):
        if variable_id[0] != '$' or variable_id[-1] != '$' or variable_id.find('$$') > -1:
            QMessageBox.information(self, self.appname, "변수명을 확인하세요.\n[$Variable ID$]")
            return False

        return True