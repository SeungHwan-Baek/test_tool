import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from widgets.variableWidget import VariableWidget

from utils.lib import makeVariableId

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/auto_variable_dialog.ui"))[0]

class AutoVariableDialog(QDialog, dig_class):
    applied = pyqtSignal()
    doubleClicked = pyqtSignal(str, str, int, str)
    auto_variable_list = []

    appname = 'Auto Variable Dialog'

    def __init__(self):
        super().__init__()
        self.case = None
        self.auto_variable_list = []
        self.auto_svc_combo_variable_list = []

        self.setupUi(self)
        self.setWindowTitle(self.appname)

        self._loadUiInit()
        self._setEvent()

    def _loadUiInit(self):
        self.btn_variableRowIndexSave.hide()

        # TableWidget 사이즈 조정
        self.tw_variableObjListSvcCombo.setColumnWidth(0, 150)  # Variable ID 컬럼 폭 강제 조절
        self.tw_variableObjListSvcCombo.setColumnWidth(1, 150)  # Variable Description 컬럼 폭 강제 조절
        self.tw_variableObjListSvcCombo.setColumnWidth(2, 150)  # Value 컬럼 폭 강제 조절

        self.tw_variableObjList.setColumnWidth(0, 150)          # Variable ID 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(1, 150)          # Variable Description 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(2, 150)          # Value 컬럼 폭 강제 조절

        self.tw_variableObjRowList.setColumnWidth(0, 50)        # Checkbox 컬럼 폭 강제 조절
        self.tw_variableObjRowList.setColumnWidth(1, 150)       # Target 컬럼 폭 강제 조절
        self.tw_variableObjRowList.setColumnWidth(2, 180)       # Description 컬럼 폭 강제 조절

        self.splitter_value_row.setSizes([380, 620])

    def _setEvent(self):
        self.tw_variableObjList.currentCellChanged.connect(self._twVariableObjListCurrentCellChanged)
        self.tw_variableObjListSvcCombo.currentCellChanged.connect(self._twVariableObjListSvcComboCurrentCellChanged)
        self.tw_variableObjRowList.cellDoubleClicked.connect(self._twVariableObjRowListCellDoubleClicked)
        self.btn_variableRowIndexSave.clicked.connect(self._btnVariableRowIndexSaveClicked)

        # Context Menu 설정
        self.tw_variableObjListSvcCombo.customContextMenuRequested.connect(self._setVariableObjListSvcComboContextMenu)

        self.action_removeVariable.triggered.connect(self._removeVariableClicked)  # Remove Variable


    def _setVariableObjListSvcComboContextMenu(self, pos):
        index = self.tw_variableObjListSvcCombo.indexAt(pos)

        if not index.isValid():
            return

        if pos:
            menu = QMenu()
            menu.addAction(self.action_removeVariable)
            menu.exec_(self.tw_variableObjListSvcCombo.mapToGlobal(pos))

    def _removeVariableClicked(self):
        row = self.tw_variableObjListSvcCombo.currentRow()

        variable = self.auto_svc_combo_variable_list[row]
        variable_id = variable.getId()

        reply = QMessageBox.question(self, self.appname,"[{}] 변수를 적용 대상에서 삭제 하시겠습니까?".format(variable_id), QMessageBox.Yes,QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.auto_svc_combo_variable_list.pop(row)
            self._setVariableView()


    def _btnVariableRowIndexSaveClicked(self):
        value_row_index = self.tw_variableObjList.currentRow()

        row_method = self.cb_rowMethod.currentText()

        if row_method == 'Fix':
            row_index = self.sb_rowIndex.value()
        else:
            row_index_column_id = self.cb_rowIndexColumnId.currentText()
            row_index_value = self.edt_rowIndexColumnValue.text()
            row_index = {'column_id': row_index_column_id, 'value': row_index_value}

        self.auto_variable_list[value_row_index]['variable_row_index'] = row_index


    def _twVariableObjListCurrentCellChanged(self, row, col):
        self.sw_variableObjList.setCurrentIndex(0)
        self.tw_variableObjList.selectRow(row)
        row_list = self.auto_variable_list[row]['row_list']
        index = self.auto_variable_list[row]['index']
        variable_row_index = self.auto_variable_list[row]['variable_row_index']
        self.tw_variableObjRowList.clearContents()
        self.tw_variableObjRowList.setRowCount(len(row_list))

        for idx, row in enumerate(row_list):
            # Checkbox 설정
            chk = QCheckBox()
            chk.clicked.connect(self._row_checkbox_change)
            chk_cell_widget = QWidget()
            chk_lay_out = QHBoxLayout(chk_cell_widget)
            chk_lay_out.addWidget(chk)
            chk_lay_out.setAlignment(Qt.AlignCenter)
            chk_lay_out.setContentsMargins(0, 0, 0, 0)
            chk_cell_widget.setLayout(chk_lay_out)
            chk_cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")

            step = self.case.getStep(step_id=row.getStepId())

            if idx == index:
                chk.setCheckState(Qt.Checked)

                column_id_list = step.getColumnList(row.get('data_list_id'))
                self.cb_rowIndexColumnId.clear()
                self.cb_rowIndexColumnId.addItems(column_id_list)
                self.frame_rowIndex.setEnabled(True)

            self.tw_variableObjRowList.setCellWidget(idx, 0, chk_cell_widget)
            self.tw_variableObjRowList.setItem(idx, 1, QTableWidgetItem(step.get('target')))
            self.tw_variableObjRowList.setItem(idx, 2, QTableWidgetItem(step.get('target_nm')))
            self.tw_variableObjRowList.setItem(idx, 3, QTableWidgetItem(row.get('data_list_id')))
            self.tw_variableObjRowList.setItem(idx, 4, QTableWidgetItem(row.get('column_id')))
            self.tw_variableObjRowList.setItem(idx, 5, QTableWidgetItem(str(row.get('row_index'))))
            self.tw_variableObjRowList.setItem(idx, 6, QTableWidgetItem(row.getStepId()))

        self._setVariableRowIndex(variable_row_index)

    def _twVariableObjListSvcComboCurrentCellChanged(self, row, col, old_row, old_col):
        self.sw_variableObjList.setCurrentIndex(1)

        self.variable_widget.setType("SVC COMBO (Swing Only)")
        self.variable_widget.setRefSvcComboInfo()

        self.tw_variableObjListSvcCombo.selectRow(row)
        variable = self.auto_svc_combo_variable_list[row]

        self.variable_widget.setComponent(variable)


    def _twVariableObjListCurrentItemChanged(self, item):
        col = item.column()
        row = item.row()

        if col == 0:
            variable_id = makeVariableId(item.text())
            item.setText(variable_id)

            self.auto_variable_list[row]['variable_id'] = variable_id
        elif col == 1:
            variable_desc = item.text()
            self.auto_variable_list[row]['variable_desc'] = variable_desc

        self._redrawTwVariableView()

    def _twVariableObjListSvcCombCurrentItemChanged(self, item):
        col = item.column()
        row = item.row()

        if col == 0:
            variable_id = makeVariableId(item.text())
            item.setText(variable_id)

            variable = self.auto_svc_combo_variable_list[row]
            variable.variable_id = variable_id

            self.auto_svc_combo_variable_list[row] = variable
            self.variable_widget.setVariableId(variable_id)
        elif col == 1:
            variable_desc = item.text()

            variable = self.auto_svc_combo_variable_list[row]
            variable['description'] = variable_desc

            self.auto_svc_combo_variable_list[row] = variable
            self.variable_widget.setDesc(variable_desc)

        self._redrawTwVariableView()

    def _twVariableObjRowListCellDoubleClicked(self):
        value_row_index = self.tw_variableObjList.currentRow()
        row_index = self.tw_variableObjRowList.currentRow()
        row_list = self.auto_variable_list[value_row_index]['row_list']

        step_row = row_list[row_index]
        step_id = step_row.getStepId()
        data_list_id = step_row.get('data_list_id')
        row_index = step_row.get('row_index')
        column_id = step_row.get('column_id')

        self.doubleClicked.emit(step_id, data_list_id, row_index, column_id)

    def _row_checkbox_change(self):
        chk = self.sender()
        checked = chk.isChecked()
        value_row_index = self.tw_variableObjList.currentRow()

        for idx in range(self.tw_variableObjRowList.rowCount()):
            widget = self.tw_variableObjRowList.cellWidget(idx, 0)

            if widget:
                row_checkbox = widget.findChild(type(QCheckBox()))
                if chk == row_checkbox:
                    self.tw_variableObjRowList.selectRow(idx)
                    chk.setChecked(checked)

                    item = self.tw_variableObjList.item(value_row_index, 0)

                    if checked:
                        self.auto_variable_list[value_row_index]['index'] = idx
                        item.setForeground(QColor(255, 215, 0))

                        row = self.auto_variable_list[value_row_index]['row_list'][idx]
                        step = self.case.getStep(step_id=row.getStepId())
                        column_id_list = step.getColumnList(row.get('data_list_id'))
                        self.cb_rowIndexColumnId.clear()
                        self.cb_rowIndexColumnId.addItems(column_id_list)
                        self.frame_rowIndex.setEnabled(True)
                    else:
                        self.auto_variable_list[value_row_index]['index'] = -1
                        item.setForeground(QColor(169, 169, 169))

                        self.cb_rowIndexColumnId.clear()
                        self.frame_rowIndex.setEnabled(False)
                else:
                    row_checkbox.setChecked(False)

        self._redrawTwVariableView()

    def accept(self):
        for idx in range(self.tw_variableObjListSvcCombo.rowCount()):
            item = self.tw_variableObjListSvcCombo.item(idx, 0)
            variable_id = item.text()

            if self._checkDupId(variable_id):
                pass
            else:
                self.tw_variableObjListSvcCombo.selectRow(idx)
                QMessageBox.information(self, self.appname, "중복된 변수ID가 존재합니다.")
                return False

        for idx in range(self.tw_variableObjList.rowCount()):
            item = self.tw_variableObjList.item(idx, 0)
            variable_id = item.text()

            if self.auto_variable_list[idx]['index'] == -1:
                pass
            elif self._checkDupId(variable_id):
                pass
            else:
                self.tw_variableObjList.selectRow(idx)
                QMessageBox.information(self, self.appname, "중복된 변수ID가 존재합니다.")
                return False

        apply_variable_rows = list(filter(lambda variable_row: variable_row['index'] > -1, self.auto_variable_list))
        apply_variable_cnt = len(apply_variable_rows)

        reply = QMessageBox.question(self, self.appname,
                                     "SVC_COMBO [{svc_combo_cnt}] 건 자동으로 적용이 가능합니다.\n[{cnt}] 건 중 [{match_step_row_cnt}] 건 자동으로 적용이 가능합니다.\n적용하시겠습니까?\n[모든 변수, 참조정보 삭제 후 진행됩니다.]\n(해당 기능은 편의기능입니다. 실제 적용된 값은 확인하시기 바랍니다.)".format(
                                         svc_combo_cnt=len(self.auto_svc_combo_variable_list), cnt=len(self.auto_variable_list), match_step_row_cnt=apply_variable_cnt),
                                     QMessageBox.Yes,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            variable_id_list = self.case.removeAllVariable()

            for variable_id in variable_id_list:
                ref_apply_count = self.case.setStepRefByVariableId('', variable_id, True)
                ref_option_apply_count = self.case.setStepRefOptionByVariableId('', variable_id, True)

            self.case.setAutoVariableSvcCombo(self.auto_svc_combo_variable_list)
            self.case.setAutoVariableDataList(self.auto_variable_list)
            self.applied.emit()
            QMessageBox.information(self, self.appname, "[{}] 건 적용되었습니다.".format(apply_variable_cnt))


    def popUp(self, case):
        self.case = case
        self.variable_widget = VariableWidget(case=self.case, option=False)
        self.variable_widget.setEnabled(False)
        self.variable_layout.addWidget(self.variable_widget)

        self._getVariableObject()
        self.exec_()


    def _getVariableObject(self):
        self.auto_variable_list = self.case.getAutoVariableDataList()
        self.auto_svc_combo_variable_list = self.case.getAutoVariableSvcCombo()
        self._setVariableView()


    def _setVariableView(self):
        self.tw_variableObjList.setRowCount(len(self.auto_variable_list))

        for idx, variable_value_info in enumerate(self.auto_variable_list):
            variable_id = variable_value_info['variable_id']
            variable_desc = variable_value_info['variable_desc']
            variable_value = variable_value_info['value']

            variable_id_item = QTableWidgetItem(variable_id)
            variable_id_item.setForeground(QColor(255, 215, 0))

            self.tw_variableObjList.setItem(idx, 0, variable_id_item)
            self.tw_variableObjList.setItem(idx, 1, QTableWidgetItem(variable_desc))
            self.tw_variableObjList.setItem(idx, 2, QTableWidgetItem(str(variable_value)))

        self.tw_variableObjListSvcCombo.setRowCount(len(self.auto_svc_combo_variable_list))

        for idx, variable in enumerate(self.auto_svc_combo_variable_list):
            variable_id = variable.getId()
            variable_desc = variable.get('description')
            variable_value = variable.get('value')

            variable_id_item = QTableWidgetItem(variable_id)
            variable_id_item.setForeground(QColor(255, 215, 0))

            self.tw_variableObjListSvcCombo.setItem(idx, 0, variable_id_item)
            self.tw_variableObjListSvcCombo.setItem(idx, 1, QTableWidgetItem(variable_desc))
            self.tw_variableObjListSvcCombo.setItem(idx, 2, QTableWidgetItem(str(variable_value)))

        self._redrawTwVariableView()
        self.tw_variableObjList.itemChanged.connect(self._twVariableObjListCurrentItemChanged)
        self.tw_variableObjListSvcCombo.itemChanged.connect(self._twVariableObjListSvcCombCurrentItemChanged)


    def _setVariableRowIndex(self, row_index):
        if type(row_index) == int:
            self.sw_rowIndex.setCurrentIndex(0)
            method_combo_idx = self.cb_rowMethod.findText("Fix")
            self.cb_rowMethod.setCurrentIndex(method_combo_idx)
            self.sb_rowIndex.setValue(row_index)

            self.edt_rowIndexColumnValue.setText("")

        else:
            self.sw_rowIndex.setCurrentIndex(1)
            method_combo_idx = self.cb_rowMethod.findText("By Value")
            self.cb_rowMethod.setCurrentIndex(method_combo_idx)

            row_index_column_id = row_index["column_id"]
            row_index_value = row_index["value"]

            row_index_column_id_idx = self.cb_rowIndexColumnId.findText(row_index_column_id)
            self.cb_rowIndexColumnId.setCurrentIndex(row_index_column_id_idx)
            self.edt_rowIndexColumnValue.setText(row_index_value)


    def _checkDupId(self, variable_id):
        variable_list = list(filter(lambda variable_value_info: variable_value_info['variable_id'] == variable_id and variable_value_info['index'] > -1, self.auto_variable_list))
        svc_combo_variable_list = list(filter(lambda variable: variable.getId() == variable_id , self.auto_svc_combo_variable_list))

        variable_list.extend(svc_combo_variable_list)

        if len(variable_list) > 1:
            return False
        else:
            return True


    def _redrawTwVariableView(self):
        for idx in range(self.tw_variableObjList.rowCount()):
            item = self.tw_variableObjList.item(idx, 0)
            variable_id = item.text()

            if self.auto_variable_list[idx]['index'] == -1:
                item.setForeground(QColor(169, 169, 169))
            elif self._checkDupId(variable_id):
                item.setForeground(QColor(255, 215, 0))
            else:
                item.setForeground(QColor(255, 0, 0))

        for idx in range(self.tw_variableObjListSvcCombo.rowCount()):
            item = self.tw_variableObjListSvcCombo.item(idx, 0)
            variable_id = item.text()

            if self._checkDupId(variable_id):
                item.setForeground(QColor(255, 215, 0))
            else:
                item.setForeground(QColor(255, 0, 0))


