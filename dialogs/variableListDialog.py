import os
import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5 import uic
from libs.variable import Variable
from utils.lib import change_key
from utils.config import Config

from widgets.variableWidget import VariableWidget
from dialogs.declareVariableDialog import DeclareVariableDialog

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/variable_list_dialog.ui"))[0]

class VariableListDialog(QDialog, dig_class):
    applied = pyqtSignal(str, str)
    declared = pyqtSignal()
    removed = pyqtSignal()
    saved = pyqtSignal()
    loadApplied = pyqtSignal()
    doubleClicked = pyqtSignal(str, str, int, str)
    refListClicked = pyqtSignal(str, str, int, str)
    varObjListClicked = pyqtSignal(str, str, int, str)

    appname = 'Variable List'
    step = None

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    VARIABLE_SAVE_PATH = os.path.join(SAVE_PATH, 'var', '.var_info')

    def __init__(self, case=None):
        super().__init__()
        self.case = case
        self.open_type = ''
        self.variable = None
        self.step_seq = -1
        self.allRefRows = []

        self.selected_variable_key = ''
        self.load_variables = {}
        self.match_step_rows = {}
        self.match_index_info = {}

        self.tmp_variable = None

        self.config = Config()
        self.variable_list = self.config.getlist("section_variable", "VARIABLE_TYPE")
        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self._loadUiInit()
        self._setEvent()

    def _loadUiInit(self):
        # TableWidget 사이즈 조정
        self.tw_refList.setColumnWidth(0, 80)           # Ref Info 컬럼 폭 강제 조절
        self.tw_refList.setColumnWidth(1, 150)          # Target 컬럼 폭 강제 조절
        self.tw_refList.setColumnWidth(2, 150)          # Description 컬럼 폭 강제 조절
        self.tw_refList.setColumnWidth(3, 80)           # Data List ID 컬럼 폭 강제 조절
        self.tw_refList.setColumnWidth(4, 150)          # Column 컬럼 폭 강제 조절
        self.tw_refList.setColumnWidth(5, 50)           # Row 컬럼 폭 강제 조절

        self.tw_variableObjList.setColumnWidth(0, 50)   # Checkbox 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(1, 150)  # Target 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(2, 150)  # Description 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(3, 80)   # Data List ID 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(4, 150)  # Column 컬럼 폭 강제 조절
        self.tw_variableObjList.setColumnWidth(5, 50)   # Row 컬럼 폭 강제 조절

        self.variable_widget = VariableWidget(case=self.case, option=False)
        self.variable_layout.addWidget(self.variable_widget)


    def _setEvent(self):
        self.tw_variableList.currentItemChanged.connect(self._lwVariableListCurrentItemChanged)
        self.tw_variableList.itemDoubleClicked.connect(self._lwVariableListItemDoubleClicked)
        self.lw_variableKeyList.currentItemChanged.connect(self._lwVariableKeyListCurrentItemChanged)
        self.tw_refList.cellDoubleClicked.connect(self._twRefListCellDoubleClicked)
        self.tw_variableObjList.cellDoubleClicked.connect(self._twVariableObjListCellDoubleClicked)
        self.btn_applyVariable.clicked.connect(self._btnApplyVariableClicked)
        self.btn_loadApply.clicked.connect(self._btnLoadApplyClicked)
        self.btn_saveVariable.clicked.connect(self._btnSaveVariableClicked)
        self.btn_addVariable.clicked.connect(self._btnAddVariableClicked)

        self.action_renameKey.triggered.connect(self._renameKeyClicked)                 # 메뉴 - Key 값 변경
        self.action_removeKey.triggered.connect(self._removeKeyClicked)                 # 메뉴 - Key 값 삭제
        self.action_setRefByValue.triggered.connect(self._setRefByValueClicked)         # 메뉴 - Set Reference By Value
        self.action_removeVariable.triggered.connect(self._removeVariableClicked)       # 메뉴 - Remove Variable
        self.action_removeAllVariable.triggered.connect(self._removeAllVariableClicked) # 메뉴 - Remove All Variable

        # Context Menu 설정
        self.lw_variableKeyList.customContextMenuRequested.connect(self._setVariableKeyListContextMenu)
        self.tw_variableList.customContextMenuRequested.connect(self._setVariableListContextMenu)


    def _setVariableKeyListContextMenu(self, pos):
        index = self.lw_variableKeyList.indexAt(pos)

        menu = QMenu()

        if not index.isValid():
            pass
        else:
            if pos:
                menu.addAction(self.action_renameKey)
                menu.addSeparator()
                menu.addAction(self.action_removeKey)

                menu.exec_(self.lw_variableKeyList.mapToGlobal(pos))


    def _setVariableListContextMenu(self, pos):
        if self.open_type == 'list':
            parentNode = None

            for item in self.tw_variableList.selectedItems():
                parentNode = item.parent()
                selectedNode = item

            index = self.tw_variableList.indexAt(pos)

            menu = QMenu()

            if not index.isValid():
                pass
            else:
                if pos:
                    if parentNode is not None:
                        menu.addAction(self.action_setRefByValue)
                        menu.addSeparator()
                        menu.addAction(self.action_removeVariable)
                        menu.addAction(self.action_removeAllVariable)
                        menu.exec_(self.tw_variableList.mapToGlobal(pos))


    def _lwVariableListCurrentItemChanged(self, new_item, old_item):
        self.refRows = []
        self.refOptionRows = []
        self.allRefRows = []

        if new_item is not None:
            parentNode = new_item.parent()

            if parentNode:
                variable_id = new_item.text(0)

                if self.open_type == 'load':
                    variable_object_list = []

                    try:
                        variable_object_list = self.match_step_rows[variable_id]
                    except KeyError:
                        pass

                    self.tw_variableObjList.clearContents()
                    self.tw_variableObjList.setRowCount(len(variable_object_list))

                    if self.selected_variable_key:
                        self.variable = self.load_variables[self.selected_variable_key][variable_id]
                        self.refRows = self.variable.get('ref_target_list')
                        self.refOptionRows = self.variable.get('ref_option_list')

                        self.allRefRows.extend(self.refRows)
                        self.allRefRows.extend(self.refOptionRows)

                        for idx, row in enumerate(variable_object_list):
                            # Checkbox 설정
                            chk = QCheckBox()
                            chk.clicked.connect(self._variable_object_checkbox_change)
                            chk_cell_widget = QWidget()
                            chk_lay_out = QHBoxLayout(chk_cell_widget)
                            chk_lay_out.addWidget(chk)
                            chk_lay_out.setAlignment(Qt.AlignCenter)
                            chk_lay_out.setContentsMargins(0, 0, 0, 0)
                            chk_cell_widget.setLayout(chk_lay_out)
                            chk_cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")

                            if idx == self.match_index_info[variable_id]:
                                chk.setCheckState(Qt.Checked)

                            step = self.case.getStep(step_id=row.getStepId())

                            self.tw_variableObjList.setCellWidget(idx, 0, chk_cell_widget)
                            self.tw_variableObjList.setItem(idx, 1, QTableWidgetItem(step.get('target')))
                            self.tw_variableObjList.setItem(idx, 2, QTableWidgetItem(step.get('description')))
                            self.tw_variableObjList.setItem(idx, 3, QTableWidgetItem(row.get('data_list_id')))
                            self.tw_variableObjList.setItem(idx, 4, QTableWidgetItem(row.get('column_id')))
                            self.tw_variableObjList.setItem(idx, 5, QTableWidgetItem(str(row.get('row_index'))))
                            self.tw_variableObjList.setItem(idx, 6, QTableWidgetItem(row.getStepId()))

                    else:
                        self.variable = None
                        self.tw_variableList.clear()
                else:
                    self.variable = self.case.getVariable(variable_id)

                if self.variable:
                    self.variable_widget.setComponent(self.variable)
                    self.btn_applyVariable.setEnabled(True)
                    self.refRows = self.case.getStepRowsByRef(key='ref_target', variable_id=variable_id)
                    self.refOptionRows = self.case.getStepRowsByRef(key='ref_option', variable_id=variable_id)

                    self.allRefRows.extend(self.refRows)
                    self.allRefRows.extend(self.refOptionRows)
                else:
                    self.variable_widget.init()
                    self.variable_widget.typeSetEnabled(False)
            else:
                self.variable_widget.init()
                self.variable_widget.typeSetEnabled(False)
        else:
            self.variable_widget.init()
            self.btn_applyVariable.setEnabled(False)

        self._setRefList()

    def _variable_object_checkbox_change(self):
        chk = self.sender()
        checked = chk.isChecked()

        for idx in range(self.tw_variableObjList.rowCount()):
            widget = self.tw_variableObjList.cellWidget(idx, 0)

            if widget:
                row_checkbox = widget.findChild(type(QCheckBox()))
                if chk == row_checkbox:
                    chk.setChecked(checked)

                    item = self.tw_variableList.currentItem()
                    variable_id = item.text(0)

                    if checked:
                        self.match_index_info[variable_id] = idx
                    else:
                        self.match_index_info[variable_id] = -1
                        item.setForeground(0, QColor(169, 169, 169))
                    pass
                else:
                    row_checkbox.setChecked(False)

    def _lwVariableListItemDoubleClicked(self, item):
        if self.open_type == 'list':
            if item is not None:
                variable_id = item.text(0)
                self.variable = self.case.getVariable(variable_id)

                if self.variable.variable_type == 'Data List':
                    step_id = self.variable.get('target').id
                    data_list_id = self.variable.get('sub_id')
                    row_index = self.variable.getRowIndex()
                    column_id = self.variable.get('column_id')

                    self.doubleClicked.emit(step_id, data_list_id, row_index, column_id)


    def _lwVariableKeyListCurrentItemChanged(self, new_item, old_item):
        if new_item:
            self.tw_variableList.clear()
            self.selected_variable_key = new_item.text()

            variables = self.load_variables[self.selected_variable_key]

            self._setVariableListView(variables)
            self.tw_variableList.setCurrentItem(self.tw_variableList.topLevelItem(0))


    def _twRefListCellDoubleClicked(self, row, col):
        step_row = self.allRefRows[row]
        step_id = step_row.getStepId()
        data_list_id = step_row.get('data_list_id')
        row_index = step_row.get('row_index')
        column_id = step_row.get('column_id')

        self.refListClicked.emit(step_id, data_list_id, row_index, column_id)

    def _twVariableObjListCellDoubleClicked(self, row, col):
        item = self.tw_variableList.currentItem()
        variable_id = item.text(0)

        rows = self.match_step_rows[variable_id]

        step_row = rows[row]
        step_id = step_row.getStepId()
        data_list_id = step_row.get('data_list_id')
        row_index = step_row.get('row_index')
        column_id = step_row.get('column_id')

        self.varObjListClicked.emit(step_id, data_list_id, row_index, column_id)

    def _setVariableKeyList(self):
        self.lw_variableKeyList.clear()

        for variable_key in list(self.load_variables.keys()):
            self.lw_variableKeyList.addItem(variable_key)

        self.lw_variableKeyList.setCurrentRow(0)
        self.tw_variableList.setCurrentItem(self.tw_variableList.topLevelItem(0))

    def _setRefList(self):
        self.tw_refList.clearContents()
        self.tw_refList.setRowCount(len(self.allRefRows))

        for idx, row in enumerate(self.allRefRows):
            step = self.case.getStep(step_id=row.getStepId())

            if row in self.refRows:
                self.tw_refList.setItem(idx, 0, QTableWidgetItem('Ref'))
            else:
                self.tw_refList.setItem(idx, 0, QTableWidgetItem('Ref Option'))

            self.tw_refList.setItem(idx, 1, QTableWidgetItem(step.get('target')))
            self.tw_refList.setItem(idx, 2, QTableWidgetItem(step.get('description')))
            self.tw_refList.setItem(idx, 3, QTableWidgetItem(row.get('data_list_id')))
            self.tw_refList.setItem(idx, 4, QTableWidgetItem(row.get('column_id')))
            self.tw_refList.setItem(idx, 5, QTableWidgetItem(str(row.get('row_index'))))
            self.tw_refList.setItem(idx, 6, QTableWidgetItem(row.getStepId()))


    def _setVariableList(self):
        self.lw_variableKeyList.clear()

        if self.step:
            variables = self.case.getApplicableVariables(self.step, self.row_index, self.column_id)
            self.frame_variableKey.hide()
            self.btn_addVariable.hide()
            self.btn_saveVariable.hide()
            self.btn_applyVariable.show()
            self.btn_loadApply.hide()
            self.grp_refList.hide()
            self.grp_variableObject.hide()
            self.variable_widget.setRefOptionEnable(True)
            self.variable_widget.cb_rowMethod.setEnabled(False)
            self.variable_widget.sw_rowIndex.setEnabled(False)
            self.resize(QSize(940, 400))

        elif self.open_type == 'select':
            variables = self.case.getApplicableVariables(seq=self.step_seq)
            self.frame_variableKey.hide()
            self.btn_addVariable.hide()
            self.btn_saveVariable.hide()
            self.btn_applyVariable.show()
            self.btn_loadApply.hide()
            self.grp_refList.hide()
            self.grp_variableObject.hide()
            self.variable_widget.setRefOptionEnable(True)
            self.variable_widget.cb_rowMethod.setEnabled(False)
            self.variable_widget.sw_rowIndex.setEnabled(False)
            self.resize(QSize(940, 400))
        elif self.open_type == 'load':
            # Variable Info Load
            if os.path.exists(self.VARIABLE_SAVE_PATH):
                with open(self.VARIABLE_SAVE_PATH, 'rb') as f:
                    variable_info = pickle.load(f)

            self.load_variables = variable_info
            self._setVariableKeyList()

            if self.load_variables:
                variables = self.load_variables[list(self.load_variables.keys())[0]]

                self.frame_variableKey.show()
                self.variable_widget.frame_common.setEnabled(False)
                self.variable_widget.sw_variableDtl.setEnabled(False)
                self.btn_addVariable.hide()
                self.btn_saveVariable.hide()
                self.btn_applyVariable.hide()
                self.btn_loadApply.show()
                self.grp_refList.hide()
                self.grp_variableObject.show()
                self.variable_widget.setRefOptionEnable(False)
                self.variable_widget.cb_rowMethod.setEnabled(False)
                self.variable_widget.sw_rowIndex.setEnabled(False)
                self.resize(QSize(1300, 720))
            else:
                return False
        else:
            self.open_type = 'list'
            variables = self.case.getVariables()
            self.frame_variableKey.hide()
            self.btn_addVariable.show()
            self.btn_saveVariable.show()
            self.btn_applyVariable.hide()
            self.btn_loadApply.hide()
            self.grp_refList.show()
            self.grp_variableObject.hide()
            self.variable_widget.setRefOptionEnable(False)
            self.variable_widget.cb_rowMethod.setEnabled(True)
            self.variable_widget.sw_rowIndex.setEnabled(True)
            self.resize(QSize(940, 720))

        self._setVariableListView(variables)

        return True


    def _setVariableListView(self, variables):
        self.tw_variableList.clear()

        if self.open_type == 'load':
            self.match_step_rows = self.case.loadVariable(variables, apply=False)

        for match_variable_id in list(self.match_step_rows.keys()):
            self.match_index_info[match_variable_id] = 0

        for idx, variable_id in enumerate(variables):
            variable = variables[variable_id]
            variable_type = variable.getType()
            variable_id = variable.getId()

            selectTreeItem = self.tw_variableList.findItems(variable_type, Qt.MatchExactly | Qt.MatchRecursive, column=0)

            if selectTreeItem:
                childWidgetItem = QTreeWidgetItem(selectTreeItem[0])
                childWidgetItem.setText(0, variable_id)
            else:
                parentWidgetItem = QTreeWidgetItem(self.tw_variableList)
                parentWidgetItem.setText(0, variable_type)
                parentWidgetItem.setForeground(0, QColor(255, 99, 71))

                childWidgetItem = QTreeWidgetItem(parentWidgetItem)
                childWidgetItem.setText(0, variable_id)

            if self.open_type == 'load':
                if variable_id in self.match_step_rows:
                    childWidgetItem.setForeground(0, QColor(255, 215, 0))
                else:
                    childWidgetItem.setForeground(0, QColor(169, 169, 169))
            elif self.open_type == 'list':
                refRows = self.case.getStepRowsByRef(key='ref_target', variable_id=variable_id)
                refOptionRows = self.case.getStepRowsByRef(key='ref_option', variable_id=variable_id)

                if refRows == [] and refOptionRows == []:
                    childWidgetItem.setForeground(0, QColor(169, 169, 169))
            elif self.step:
                ref_target = self.step.getRowInfoValue(self.data_list_id, self.row_index, self.column_id, 'ref_target')
                ref_option = self.step.getRowInfoValue(self.data_list_id, self.row_index, self.column_id, 'ref_option')

                if ref_target:
                    selectTreeItem = self.tw_variableList.findItems(ref_target, Qt.MatchExactly | Qt.MatchRecursive, column=0)
                    try:
                        self.tw_variableList.setCurrentItem(selectTreeItem[0])
                        self.variable_widget.setRefOptionInfo(ref_option)
                    except IndexError:
                        pass

        self.tw_variableList.expandToDepth(0)

    def popUp(self, step=None, data_list_id='', row_index=-1, column_id='', open_type='', step_seq=-1):
        self.step = step
        self.data_list_id = data_list_id
        self.row_index = row_index
        self.column_id = column_id
        self.open_type = open_type
        self.step_seq = step_seq

        if self._setVariableList():
            self.exec_()
        else:
            QMessageBox.information(self, "Load Variable", "Load 할 수 있는 Variable이 없습니다.")
            self.close()

    def _btnAddVariableClicked(self):
        items = ("Date", "Excel", "SQL", "Fixed Value", "SVC COMBO (Swing Only)")
        variable_type, ok = QInputDialog.getItem(self, 'Select Type', '추가 Variable Type을 선택하세요.', items, 0, False)

        if ok and variable_type:
            declareVariableDialog = DeclareVariableDialog(self.case)
            declareVariableDialog.declared.connect(self._rowDeclaredVariable)
            declareVariableDialog.popUp(variable_type=variable_type)


    def _rowDeclaredVariable(self, variable_id):
        self._setVariableList()
        self._setFocusVariableList(variable_id)
        self.declared.emit()


    def _removeVariableClicked(self):
        '''
        [Remove] 버튼 클릭 이벤트
        :return:
        '''
        item = self.tw_variableList.currentItem()
        variable_id = item.text(0)

        reply = QMessageBox.question(self, self.appname,"[{}] 변수를 참조하고 있는 경우 삭제 후 참조가 불가능합니다. 변수를 삭제하시겠습니까?".format(variable_id), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.case.removeVariable(variable_id)
            self._setVariableList()

            ref_count = self.case.setStepRefByVariableId('', variable_id, False)
            ref_option_count = self.case.setStepRefOptionByVariableId('', variable_id, False)

            if ref_count > 0:
                reply = QMessageBox.question(self, self.appname,"변수가 삭제되었습니다.\n기존 변수ID를 참조하고 있는 Step 참조정보 [{ref_count}]건, 참조옵션정보 [{ref_option_count}]건의 정보도 변경하시겠습니까?".format(ref_count=ref_count, ref_option_count=ref_option_count), QMessageBox.Yes, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    ref_apply_count = self.case.setStepRefByVariableId('', variable_id, True)
                    ref_option_apply_count = self.case.setStepRefOptionByVariableId('', variable_id, True)
                    QMessageBox.information(self, self.appname, "Step 참조정보[{ref_apply_count}]건, 참조옵션정보[{ref_option_apply_count}] 적용되었습니다.".format(ref_apply_count=ref_apply_count, ref_option_apply_count=ref_option_apply_count))

            self.removed.emit()


    def _removeAllVariableClicked(self):
        '''
        [Remove All Variabble] 버튼 클릭 이벤트
        :return:
        '''

        reply = QMessageBox.question(self, self.appname, "모든 변수를 삭제하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            variable_id_list = self.case.removeAllVariable()
            self._setVariableList()

            reply = QMessageBox.question(self, self.appname, "변수가 삭제되었습니다.\nStep의 참조정보, 참조옵션정보도 초기화 하시겠습니까?", QMessageBox.Yes,QMessageBox.No)
            if reply == QMessageBox.Yes:
                for variable_id in variable_id_list:
                    ref_apply_count = self.case.setStepRefByVariableId('', variable_id, True)
                    ref_option_apply_count = self.case.setStepRefOptionByVariableId('', variable_id, True)

                QMessageBox.information(self, self.appname, "적용되었습니다.")

            self.removed.emit()


    def _renameKeyClicked(self):
        '''
        [Rename Key] 버튼 클릭 이벤트
        :return:
        '''
        key, ok = QInputDialog.getText(self, 'Rename Key', '변경 할 Key값을 입력하세요.', text=self.selected_variable_key)

        if ok and key:
            if key in list(self.load_variables.keys()) and key != self.selected_variable_key:
                QMessageBox.information(self, 'Rename Key', "동일한 Key값이 존재합니다.\n[{}]".format(key))
                return False
            else:
                self.load_variables = change_key(self.load_variables, key, self.selected_variable_key)
                self.selected_variable_key = key
                self._setVariableKeyList()

                with open(self.VARIABLE_SAVE_PATH, 'wb') as f:
                    pickle.dump(self.load_variables, f, pickle.HIGHEST_PROTOCOL)

                QMessageBox.information(self, "Rename Key", "변경되었습니다.")


    def _removeKeyClicked(self):
        '''
        [Remove Key] 버튼 클릭 이벤트
        :return:
        '''
        reply = QMessageBox.question(self, "Remove Key", "[{}] Key 값을 삭제하시겠습니까?\n( Key에 포함된 변수도 모두 삭제됩니다 )".format(self.selected_variable_key), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.load_variables[self.selected_variable_key]
            self.selected_variable_key = ''
            self._setVariableKeyList()

            with open(self.VARIABLE_SAVE_PATH, 'wb') as f:
                pickle.dump(self.load_variables, f, pickle.HIGHEST_PROTOCOL)

            QMessageBox.information(self, "Remove Key", "삭제되었습니다.")


    def _setRefByValueClicked(self):
        value = self.variable.getValue()

        reply = QMessageBox.question(self, "Set Reference By Value", "[{}] Value를 가진 Data 참조값을 설정합니다.\n진행하시겠습니까?".format(value), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.refRows = []
            self.refOptionRows = []
            self.allRefRows = []
            setCount = self.case.setStepRefByValue(value, self.variable.variable_id, apply=True)
            self.refRows = self.case.getStepRowsByRef(key='ref_target', variable_id=self.variable.variable_id)
            self.refOptionRows = self.case.getStepRowsByRef(key='ref_option', variable_id=self.variable.variable_id)

            self.allRefRows.extend(self.refRows)
            self.allRefRows.extend(self.refOptionRows)
            self._setRefList()
            QMessageBox.information(self, "Set Reference By Value", "[{}] 건 적용되었습니다.".format(setCount))


    def _btnSaveVariableClicked(self):
        '''
        [Save] 버튼 클릭 이벤트
        :return:
        '''
        item = self.tw_variableList.currentItem()

        if item:
            case_variables = self.case.getVariables()
            variable_id = self.variable_widget.getVariableId()

            if self._variableIdCheck(variable_id):
                if self.variable:
                    if self.variable.variable_id in list(case_variables.keys()):
                        reply = QMessageBox.question(self, self.appname, "[{}] 변수의 정보를 변경하시겠습니까?".format(variable_id), QMessageBox.Yes, QMessageBox.No)

                        if reply == QMessageBox.Yes:
                            var = self.variable_widget.getVariable()
                            new_id = variable_id
                            old_id = self.variable.variable_id
                            self.case.changeVariable(new_id, old_id, var)

                            if new_id == old_id:
                                pass
                            else:
                                self._setVariableList()
                                ref_count = self.case.setStepRefByVariableId(new_id, old_id, False)
                                ref_option_count = self.case.setStepRefOptionByVariableId(new_id, old_id, False)

                                if ref_count > 0:
                                    reply = QMessageBox.question(self, self.appname, "변수ID가 변경되었습니다.\n기존 변수ID를 참조하고 있는 Step 참조정보 [{ref_count}]건, 참조옵션정보 [{ref_option_count}]건 의 정보도 변경하시겠습니까?".format(ref_count=ref_count, ref_option_count=ref_option_count), QMessageBox.Yes, QMessageBox.No)

                                    if reply == QMessageBox.Yes:
                                        ref_apply_count = self.case.setStepRefByVariableId(new_id, old_id, True)
                                        ref_option_apply_count = self.case.setStepRefOptionByVariableId(new_id, old_id, True)
                                        QMessageBox.information(self, self.appname, "Step 참조정보[{ref_apply_count}]건, 참조옵션정보[{ref_option_apply_count}] 적용되었습니다.".format(ref_apply_count=ref_apply_count, ref_option_apply_count=ref_option_apply_count))

                            self.variable_widget.setComponent(var)
                            self.saved.emit()
                else:
                    variable_id = self.variable_widget.getVariableId()
                    reply = QMessageBox.question(self, self.appname, "[{}] 변수를 추가하시겠습니까?".format(variable_id), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        var = self.variable_widget.getVariable()

                        self.case.setVariableList(var)
                        self._setVariableList()


    def _btnApplyVariableClicked(self):
        item = self.tw_variableList.currentItem()
        variable_id = item.text(0)
        ref_option_info =self.variable_widget.getRefOptionInfo()
        reply = QMessageBox.question(self, self.appname,"[{}] 변수를 참조 할 수 있도록 적용하시겠습니까?".format(variable_id), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.applied.emit(variable_id, ref_option_info)
            self.close()


    def _btnLoadApplyClicked(self):
        variables = self.load_variables[self.selected_variable_key]
        match_step_row = self.case.loadVariable(variables, apply=False)

        for variable_id in list(match_step_row.keys()):
            try:
                if self.match_index_info[variable_id] > -1:
                    pass
                else:
                    del match_step_row[variable_id]
            except KeyError:
                pass

        match_step_row_cnt = len(match_step_row)

        reply = QMessageBox.question(self, self.appname,
                                     "[{cnt}] 건 중 [{match_step_row_cnt}] 건 자동으로 적용이 가능합니다. 적용하시겠습니까?\n(해당 기능은 편의기능입니다. 실제 적용된 값은 확인하시기 바랍니다.)".format(
                                         cnt=len(variables), match_step_row_cnt=match_step_row_cnt), QMessageBox.Yes,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            match_step_row_cnt = self.case.loadVariable(variables, apply=True, match_index_info=self.match_index_info)
            self.loadApplied.emit()
            QMessageBox.information(self, self.appname, "적용되었습니다.")


    def _variableIdCheck(self, variable_id):
        if variable_id == '' or variable_id[0] != '$' or variable_id[-1] != '$' or variable_id.find('$$') > -1:
            QMessageBox.information(self, self.appname, "변수명을 확인하세요.\n[$Variable ID$]")
            return False

        return True


    def _setFocusVariableList(self, variable_id):
        if variable_id:
            selectTreeItem = self.tw_variableList.findItems(variable_id, Qt.MatchExactly | Qt.MatchRecursive, column=0)
            self.tw_variableList.setCurrentItem(selectTreeItem[0])

