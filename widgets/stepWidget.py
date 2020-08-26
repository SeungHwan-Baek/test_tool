import os
import pandas as pd
import pickle
import pyperclip
import socket
from functools import partial
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from libs.xhr import Xhr
from libs.case import Case

from utils.tableModel import PandasModel
from utils.lib import split_seq, horizontalLayout

from widgets.stepDtlWidget import StepDtlWidget
from dialogs.addStepDialog import AddStepDialog
from dialogs.addDataDialog import AddDataDialog
from dialogs.declareVariableDialog import DeclareVariableDialog
from dialogs.variableListDialog import VariableListDialog
from dialogs.caseStepDialog import CaseStepDialog
from dialogs.changeConfirmDialog import ChangeConfirmDialog
from dialogs.logDialog import LogDialog

from utils.eventWorker import EventThread

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
widget_class = uic.loadUiType(os.path.join(parentDir, "UI/step_widget.ui"))[0]

__appname__ = 'Test Automation Tool'

class StepWidget(QMainWindow, widget_class):
    selected = pyqtSignal(int, int)
    xhrToDown = pyqtSignal(int)

    none_Df = pd.DataFrame()
    none_model = PandasModel(none_Df)
    data_model = PandasModel(none_Df)

    selectedStepItems = []

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    STEP_SAVE_PATH = os.path.join(SAVE_PATH, 'test_file', 'step')

    def __init__(self, parent=None, suites=None):
        super(StepWidget, self).__init__(parent)
        self.suites = suites
        self.selected_step = None
        self.selected_data_id = ''
        self.selected_row = -1
        self.selected_column_id = ''
        self.suitesWidget = parent

        self.setupUi(self)

        self._loadUiInit()
        self._setEvent()

        self.logDialog = LogDialog()
        self.changeConfirmDialog = ChangeConfirmDialog()
        self.changeConfirmDialog.changed.connect(self._stepColumnChanged)
        self.changeConfirmDialog.cancle.connect(self._stepColumnCancle)

    def _loadUiInit(self):
        self.tw_testStep.hideColumn(1)  # Step Seq
        self.tw_testStep.hideColumn(2)  # Step Id
        self.tw_columnInfo.setColumnWidth(0, 250)

        self.splitter_step_data.setSizes([750, 250])
        self.splitter_list_data.setSizes([150, 850])

        # 트리 컬럼 사이즈 조정
        self.tw_property.setColumnWidth(0, 150)  # Property 컬럼 폭 강제 조절
        self.tw_property.setStyleSheet("QTreeView::branch { border-image: none; }")

        step_tool_bar = QToolBar()
        step_tool_bar.addAction(self.action_newStep)
        step_tool_bar.addAction(self.action_removeStep)
        step_tool_bar.addAction(self.action_copyTestData)
        step_tool_bar.addAction(self.action_addExclutionTrList)
        step_tool_bar.addSeparator()
        step_tool_bar.addAction(self.action_moveToUp)
        step_tool_bar.addAction(self.action_moveToDown)
        step_tool_bar.addSeparator()
        step_tool_bar.addAction(self.action_replayXhr)
        self.toolbar_layout.addWidget(step_tool_bar)


    def findSelectedStep(self):
        selectedStep = None

        case = self.suites.selectedCase()

        if case is not None:
            stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
            if stepWidget is None:
                pass
            else:
                row = stepWidget.getSeq()
                selectedStep = case.getStep(row-1)

        return selectedStep


    def _setEvent(self):
        # ToolBar 버튼 이벤트
        self.action_beforeNewStep.triggered.connect(self._beforeNewStepClicked)                     # 메뉴 - Add before current Step
        self.action_afterNewStep.triggered.connect(self._afterNewStepClicked)                       # 메뉴 - Add after current Step
        self.action_addNewStepToGroup.triggered.connect(self._addNewStepToGroupClicked)             # 메뉴 - Add step to group
        self.action_renameGroup.triggered.connect(self._renameGroupClicked)                         # 메뉴 - Group명 변경
        self.action_newStep.triggered.connect(self._addStepClicked)                                 # 메뉴 - Add Test Case
        self.action_ifNewStep.triggered.connect(self._ifNewStepClicked)                             # 메뉴 - Add Step inside conditional statement
        self.action_openTestStep.triggered.connect(self._openTestStepClicked)                       # 메뉴 - Open Test Step
        self.action_saveTestStepGroup.triggered.connect(self._saveTestStepGroupClicked)             # 메뉴 - Save Test Step Group
        self.action_addDataList.triggered.connect(self._addDataListClicked)                         # 메뉴 - Add Data List
        self.action_saveTestStep.triggered.connect(self._saveTestStepClicked)                       # 메뉴 - Save Test Step
        self.action_removeStep.triggered.connect(self._btnRemoveStepClicked)                        # 메뉴 - Remove Step
        self.action_removeStepByExlTrList.triggered.connect(self._btnRemoveStepByExlTrListClicked)  # 메뉴 - Remove Step By Excluded Tr List
        self.action_removeAllStep.triggered.connect(self._btnRemoveAllStepClicked)                  # 메뉴 - Remove All Step
        self.action_replayXhr.triggered.connect(self._replayXhrClicked)                             # 메뉴 - Replay XHR
        self.action_replayAllXhrToDown.triggered.connect(self.replayAllXhrToDownClicked)            # 메뉴 - Replay All XHR to Down
        self.action_declareVariable.triggered.connect(self._declareVariableClicked)                 # 메뉴 - Declare Variable
        self.action_removeVariable.triggered.connect(self._removeVariableClicked)                   # 메뉴 - Remove Variable
        self.action_declareVariableColumn.triggered.connect(self._declareVariableColumnClicked)     # 메뉴 - Declare Variable (Column)
        self.action_removeVariableColumn.triggered.connect(self._removeVariableColumnClicked)       # 메뉴 - Remove Variable (Column)
        self.action_setReference.triggered.connect(self._setReferenceClicked)                       # 메뉴 - Set Reference
        self.action_romoveReference.triggered.connect(self._removeReferenceClicked)                 # 메뉴 - Remove Reference
        self.action_getReferenceValue.triggered.connect(self._getReferenceValueClicked)             # 메뉴 - Get Reference Value
        self.action_getTrIOInfo.triggered.connect(self._getTrIOInfo)                                # 메뉴 - Get Transaction IO Info
        self.action_getTrNm.triggered.connect(self._getTrNm)                                        # 메뉴 - Get Transaction Name
        self.action_addExclutionTrList.triggered.connect(self._addExclutionTrListClicked)           # 메뉴 - Add to exclusion transaction list
        self.action_group.triggered.connect(self.groupClicked)                                      # 메뉴 - Group
        self.action_setRefByValue.triggered.connect(lambda: self.setRefByValue(ref_variable='Row')) # 메뉴 - Set Reference By Value
        self.action_copyTestData.triggered.connect(self._copyJsonDataClicked)                       # 메뉴 - Copy to Json
        self.action_transactionLog.triggered.connect(self._transactionLogClicked)                   # 메뉴 - Transaction Log
        self.action_addDataColumn.triggered.connect(self._addDataColumnClicked)                     # 메뉴 - Data Column 추가
        self.action_addDataRow.triggered.connect(self._addDataRowClicked)                           # 메뉴 - Data Row 추가
        self.action_deleteDataColumn.triggered.connect(self._deleteDataColumnClicked)               # 메뉴 - Data Row 삭제
        self.action_deleteDataRow.triggered.connect(self._deleteDataRowClicked)                     # 메뉴 - Data Column 삭제
        self.action_moveToUp.triggered.connect(self._stepMoveToUp)                                  # 메뉴 - Step 이동 (위)
        self.action_moveToDown.triggered.connect(self._stepMoveToDown)                              # 메뉴 - Step 이동 (아래)

        # Step View
        self.tw_testStep.customContextMenuRequested.connect(self._setTestStepContextMenu)           # Step Context Menu 설정
        self.tw_testStep.currentItemChanged.connect(self._twTestStepItemSelectionChanged)           # Step Tree Item Selection Changed 이벤트
        self.tw_testStep.itemDoubleClicked.connect(self._lwTestStepCellDoubleClicked)               # Step Cell Double Clicked 이벤트
        self.tw_testStep.dropEvent = self._twStepDroped                                             # Step Row Drop

        # DataList View
        self.tw_dataList.currentItemChanged.connect(self._twDataListItemSelectionChanged)           # Data List Tree Item Selection Changed 이벤트

        # Data Dtl View
        self.tw_data.customContextMenuRequested.connect(self._setDataContextMenu)
        self.tw_data.currentChanged = self._twDataCurrentChanged                                    # Test Step Cell Double Clicked 이벤트
        self.tw_data_header = self.tw_data.horizontalHeader()
        self.tw_data_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tw_data_header.customContextMenuRequested.connect(self._setDataHeaderContextMenu)

        # Column Info View
        self.tw_columnInfo.cellClicked.connect(self._twColumnInfoClicked)
        self.tw_columnInfo.customContextMenuRequested.connect(self._setColumnInfoContextMenu)       # Column Info Context Menu 설정

        # Add Info
        self.cb_addInfo.currentIndexChanged['QString'].connect(self._cbAddInfoColumnIdCurrentIndexChanged)


    def _setTestStepContextMenu(self, pos):
        self.setComponetEnable()
        self.selectedStepItems = self.tw_testStep.selectedItems()

        menu = QMenu()
        menu.setMinimumSize(QSize(350, 0))
        index = self.tw_testStep.indexAt(pos)

        if len(self.selectedStepItems) > 1:
            menu.addAction(self.action_group)
            menu.addAction(self.action_removeStep)
            menu.exec_(self.tw_testStep.mapToGlobal(pos))

        else:
            # Step 이 아닌 여백 선택 시
            if not index.isValid():
                if pos:
                    menu.addAction(self.action_newStep)
                    menu.addAction(self.action_openTestStep)
                    menu.addSeparator()
                    menu.addAction(self.action_removeAllStep)
                    menu.exec_(self.tw_testStep.mapToGlobal(pos))
                else:
                    menu.addAction(self.action_newStep)
                    menu.exec_(self.tw_testStep.mapToGlobal(pos))
            # Step 리스트 목록에서 선택 시
            else:
                if pos:
                    # 그룹 선택 시
                    if self.selected_step is None:
                        menu.addAction(self.action_renameGroup)
                        menu.addSeparator()
                        menu.addAction(self.action_addNewStepToGroup)
                        menu.addAction(self.action_openTestStep)
                        menu.addSeparator()
                        menu.addAction(self.action_saveTestStepGroup)
                        menu.exec_(self.tw_testStep.mapToGlobal(pos))
                    # Step 선택 시
                    else:
                        if self.selected_step.getType() == 'IF':
                            menu.addAction(self.action_ifNewStep)

                        menu.addAction(self.action_newStep)
                        addStep_menu = menu.addMenu(QIcon(':/step/' + 'add_step.png'), 'Step 삽입')
                        addStep_menu.addAction(self.action_beforeNewStep)
                        addStep_menu.addAction(self.action_afterNewStep)
                        menu.addAction(self.action_openTestStep)
                        menu.addAction(self.action_saveTestStep)
                        removeStep_menu = menu.addMenu(QIcon(':/step/' + 'remove.png'), 'Step 삭제')
                        removeStep_menu.addAction(self.action_removeStep)
                        removeStep_menu.addAction(self.action_removeStepByExlTrList)
                        removeStep_menu.addAction(self.action_removeAllStep)
                        menu.addSeparator()

                        if self.selected_step.getType() == 'XHR':
                            menu.addAction(self.action_addExclutionTrList)
                            menu.addSeparator()
                            menu.addAction(self.action_addDataList)
                            # dataList_menu = menu.addMenu('Data List')
                            # for dataListId in self.selected_step.getDataListId('input'):
                            #     action = QAction(QIcon(':/step/' + 'circle_arrow.png'), dataListId, self)
                            #     #action.triggered.connect(partial(self.dataValueDialogPopup, dataListId))
                            #     dataList_menu.addAction(action)
                            #
                            # dataList_menu.addSeparator()

                            # for dataListId in self.selected_step.getDataListId('output'):
                            #     action = QAction(QIcon(':/step/' + 'circle_arrow.png'), dataListId, self)
                            #     #action.triggered.connect(partial(self.dataValueDialogPopup, dataListId))
                            #     dataList_menu.addAction(action)
                            menu.addAction(self.action_copyTestData)
                            transaction_info_menu = menu.addMenu('Transaction 정보')
                            transaction_info_menu.addAction(self.action_getTrIOInfo)
                            transaction_info_menu.addAction(self.action_getTrNm)
                            menu.addSeparator()
                        menu.addAction(self.action_replayXhr)
                        menu.addAction(self.action_replayAllXhrToDown)
                        menu.addSeparator()
                        menu.addAction(self.action_transactionLog)

                        menu.exec_(self.tw_testStep.mapToGlobal(pos))


    def _setDataContextMenu(self, pos):
        index = self.tw_data.indexAt(pos)
        data_list_type = self.selected_step.getDataListType(self.selected_data_id)

        if not index.isValid():
            if data_list_type == 'output':
                pass
            else:
                menu = QMenu()
                menu.addAction(self.action_addDataRow)
                menu.addAction(self.action_addDataColumn)
                menu.exec_(self.tw_data.mapToGlobal(pos))
        elif pos:
            row = index.row()
            column_id = self.data_model.getColumnId(index)

            isVar = self.selected_step.getIsVar(self.selected_data_id, row, column_id)
            isRef = self.selected_step.getIsRef(self.selected_data_id, row, column_id)

            menu = QMenu()
            menu.addAction(self.action_declareVariable)
            menu.addAction(self.action_setRefByValue)

            if isVar:
                menu.addAction(self.action_removeVariable)

            if data_list_type == 'input':

                menu.addSeparator()
                menu.addAction(self.action_setReference)

                if isRef:
                    menu.addAction(self.action_romoveReference)
                #findRef_menu = menu.addMenu('Find Reference')
                #findRef_menu.addAction(self.action_findRefByValue)
                #findRef_menu.addAction(self.action_findRefByColumn)
                menu.addAction(self.action_getReferenceValue)
                menu.addSeparator()
                row_menu = menu.addMenu('Row')
                row_menu.addAction(self.action_addDataRow)
                row_menu.addAction(self.action_deleteDataRow)
                column_menu = menu.addMenu('Column')
                column_menu.addAction(self.action_addDataColumn)
                column_menu.addAction(self.action_deleteDataColumn)
            menu.exec_(self.tw_data.mapToGlobal(pos))


    def _setDataHeaderContextMenu(self, pos):
        self.column_pos = pos
        
        index = self.tw_data.indexAt(self.column_pos)
        column = index.column()
        col_id = self.data_model.getHeader(column)
        
        isVar = self.selected_step.getIsColVar(self.selected_data_id, col_id)
        
        menu = QMenu()
        menu.addAction(self.action_declareVariableColumn)
        
        if isVar:
            menu.addAction(self.action_removeVariableColumn)
        
        menu.exec_(self.tw_data_header.mapToGlobal(pos))


    def _setColumnInfoContextMenu(self, pos):
        row = self.tw_columnInfo.currentRow()
        item = self.tw_columnInfo.item(row, 0)
        col_id = item.text()

        isVar = self.selected_step.getIsColVar(self.selected_data_id, col_id)

        menu = QMenu()
        menu.addAction(self.action_declareVariableColumn)

        if isVar:
            menu.addAction(self.action_removeVariableColumn)

        menu.exec_(self.tw_data_header.mapToGlobal(pos))


    def setComponetEnable(self):
        # Case가 선택된경우
        if self.suites.selectedCaseId:
            isCase = True
        else:
            isCase = False

        if self.selected_step:
            isStep = True
        else:
            isStep = False

        self.tw_testStep.setEnabled(isCase)
        self.action_newStep.setEnabled(isCase)
        self.action_removeStep.setEnabled(isCase)
        self.action_copyTestData.setEnabled(isCase)
        self.action_openTestStep.setEnabled(isCase)
        self.action_moveToUp.setEnabled(isCase)
        self.action_moveToDown.setEnabled(isCase)

        self.action_removeStep.setEnabled(isStep)
        self.action_copyTestData.setEnabled(isStep)
        self.action_addExclutionTrList.setEnabled(isStep)
        # self.action_moveToUp.setEnabled(isStep)
        # self.action_moveToDown.setEnabled(isStep)
        self.action_replayXhr.setEnabled(isStep)
        self.action_transactionLog.setEnabled(isStep)

    # ============================ Action Event ============================
    def _beforeNewStepClicked(self):
        case = self.suites.selectedCase()
        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        index = stepWidget.getSeq() - 1
        group = stepWidget.getGroup()
        addStepDialog = AddStepDialog(call_gubun='New', case=case, group=group, index=index)
        addStepDialog.added.connect(self._stepAdded)
        addStepDialog.popUp()


    def _afterNewStepClicked(self):
        case = self.suites.selectedCase()
        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        index = stepWidget.getSeq()
        group = stepWidget.getGroup()
        addStepDialog = AddStepDialog(call_gubun='New', case=case, group=group, index=index)
        addStepDialog.added.connect(self._stepAdded)
        addStepDialog.popUp()


    def _addNewStepToGroupClicked(self):
        case = self.suites.selectedCase()

        for item in self.tw_testStep.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is None:
            group = selectedNode.text(0)

        group_step_index_list = []
        for idx in range(0, self.tw_testStep.currentItem().childCount()):
            child_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem().child(idx), 0)
            child_step_index = child_stepWidget.getSeq() - 1
            group_step_index_list.append(child_step_index)

        last_step = case.getStep(group_step_index_list[-1])
        index = last_step.getSeq()

        addStepDialog = AddStepDialog(call_gubun='New', case=case, group=group, index=index)
        addStepDialog.added.connect(self._stepAdded)
        addStepDialog.popUp()


    def _renameGroupClicked(self):
        '''
        Group명 변경 이벤트
        '''
        for item in self.tw_testStep.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is None:
            group = selectedNode.text(0)

        new_group, ok = QInputDialog.getText(self, 'Group명 변경', 'Group명을 입력하세요.',  text=group)

        if ok and new_group:
            for idx in range(0, self.tw_testStep.currentItem().childCount()):
                child_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem().child(idx), 0)
                child_step = child_stepWidget.getStep()
                child_step['group'] = new_group

            self.setStepView()
            QMessageBox.information(self, "Group명 변경", "Group명을 변경하였습니다.")



    def _addStepClicked(self):
        case = self.suites.selectedCase()
        addStepDialog = AddStepDialog(call_gubun='New', case=case)
        addStepDialog.added.connect(self._stepAdded)
        addStepDialog.popUp()


    def _ifNewStepClicked(self):
        case = self.suites.selectedCase()
        addStepDialog = AddStepDialog(call_gubun='New', case=case, condition_step_id=self.selected_step.getId())
        addStepDialog.added.connect(self._stepAdded)
        addStepDialog.popUp()


    def _openTestStepClicked(self):
        fd = QFileDialog(self)
        filename = fd.getOpenFileName(self, '%s - Choose Step File' % __appname__, self.STEP_SAVE_PATH,'All Files(*.ats *.atc *.atg);;Step Files(*.ats);;Case Files(*.atc);;Step Group Files(*.atg)')
        filePath = filename[0]

        if filePath:
            case = self.suites.selectedCase()

            with open(filePath, 'rb') as f:
                loadData = pickle.load(f)

                if type(loadData) == Case:
                    self.caseStepDialog = CaseStepDialog(loadData)
                    self.caseStepDialog.popUp()

                    for idx, step in enumerate(self.caseStepDialog.selectedStepList):
                        case.setStepList(step)
                elif type(loadData) == Xhr:
                    case.setStepList(loadData)
                elif type(loadData) == list:
                    for idx, step in enumerate(loadData):
                        case.setStepList(step)

            self.setStepView()

    def _saveTestStepGroupClicked(self):
        for item in self.tw_testStep.selectedItems():
            group = item.text(0)

        reply = QMessageBox.question(self, 'Save Test Step Group', "Group [{group}] 을 저장하시겠습니까?".format(group=group), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            fd = QFileDialog(self)
            filename = fd.getSaveFileName(self, '%s - Save Step Group File' % __appname__, self.STEP_SAVE_PATH,'Step Group Files(*.atg)')
            filePath = filename[0]

            if filePath:
                group_step_list = []
                for idx in range(0, self.tw_testStep.currentItem().childCount()):
                    child_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem().child(idx), 0)
                    child_step_index = child_stepWidget.getStep()
                    group_step_list.append(child_step_index)

                with open(filePath, 'wb') as f:
                    pickle.dump(group_step_list, f, pickle.HIGHEST_PROTOCOL)
                    QMessageBox.information(self, "Save Step Group File", "Save Complete")


    def _addDataListClicked(self):
        addDataInfoDialog = AddDataDialog(self.selected_step)
        addDataInfoDialog.popUp()

        self.setDataListView()

        #self.setTestDataView()
        #self.setValueView()

        # Step Ref정보 변경
        #self.setStepRefInfo()


    def _saveTestStepClicked(self):
        fd = QFileDialog(self)
        filename = fd.getSaveFileName(self, '%s - Save Step File' % __appname__, self.STEP_SAVE_PATH, 'List Files(*.ats)')
        filePath = filename[0]

        if filePath:
            with open(filePath, 'wb') as f:
                pickle.dump(self.selected_step, f, pickle.HIGHEST_PROTOCOL)
                QMessageBox.information(self, "Save Step File", "Save Complete")


    def _btnRemoveStepClicked(self):
        '''
        Step을 삭제하는 이벤트
            - N건의 Step을 선택하여 삭제 가능
        :return: None
        '''
        remove_list = []
        remove_index_list = []
        case = self.suites.selectedCase()

        if self.selectedStepItems:
            pass
        else:
            self.selectedStepItems = self.tw_testStep.selectedItems()

        reply = QMessageBox.question(self, 'Remove Step', "{cnt} 건의 Step을 삭제하시겠습니까?".format(cnt=len(self.selectedStepItems)), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            for item in self.selectedStepItems:
                stepWidget = self.tw_testStep.itemWidget(item, 0)

                if stepWidget is None:
                    pass
                else:
                    row = stepWidget.getSeq()
                    remove_list.append(case.getStep(row - 1))
                    remove_index_list.append(row - 1)

            min_index = min(remove_index_list)
            max_index = max(remove_index_list)

            previous_step = case.getStep(min_index - 1)
            next_step = case.getStep(max_index + 1)

            for step in remove_list:
                case.removeStep(step)

            selectedIndex = row - 1
            stepCnt = case.getStepCount()

            if next_step:
                self.selected_step = next_step
            elif previous_step:
                self.selected_step = previous_step
            elif stepCnt == 0:
                self.selected_step = None
            else:
                self.selected_step = case.getStep(stepCnt - 1)

            index = case.findStepIndexByStep(self.selected_step)
            case.setSelectedStepRow(index)

            self.setComponetEnable()
            self.setStepView()


    def _btnRemoveStepByExlTrListClicked(self):
        excluded_tr_list = self.suites.getExcludedTrList()
        case = self.suites.selectedCase()

        removeCnt = case.removeStepByExcludeTrList(excluded_tr_list, apply=False)

        if removeCnt > 0:
            reply = QMessageBox.question(self, 'Remove Step By Excluded Transaction List',"{count}건의 Step을 삭제하시겠습니까?".format(count=removeCnt), QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                case.removeStepByExcludeTrList(excluded_tr_list, apply=True)
                self.setStepView()
                QMessageBox.information(self, "Remove Step By Excluded Transaction List", "Remove Complete")
        else:
            QMessageBox.information(self, "Remove Step By Excluded Transaction List", "제외 대상에 해당하는 Transaction이 없습니다.")


    def _btnRemoveAllStepClicked(self):
        '''
        Case의 Step을 모두 삭제하는 이벤트
        :return: None
        '''
        case = self.suites.selectedCase()
        count = case.getStepCount()

        if count > 0:
            reply = QMessageBox.question(self, 'Remove All Step',"{count}건의 Step을 모두 삭제하시겠습니까?".format(count=count), QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                case.removeAllStep()
                self.setStepView()


    def _declareVariableClicked(self):
        case = self.suites.selectedCase()

        target = self.selected_step
        sub_id = self.selected_data_id
        row_index = self.selected_row
        col_id = self.selected_column_id
        col_desc = self.selected_step.getColumnValue(self.selected_data_id, self.selected_column_id, 'description')
        value = self.data_model.getData(self.tw_data.currentIndex())

        declareVariableDialog = DeclareVariableDialog(case)
        declareVariableDialog.declared.connect(self._rowDeclaredVariable)
        declareVariableDialog.popUp(variable_type='Data List', target=target, sub_id=sub_id, row_index=row_index, col_id=col_id, col_desc=col_desc, value=value)


    def _removeVariableClicked(self):
        case = self.suites.selectedCase()
        index = self.tw_data.currentIndex()
        row = index.row()
        column_id = self.data_model.getColumnId(index)

        variable_id = self.selected_step.getRowInfoValue(self.selected_data_id, row, column_id, 'variable')

        isVar = self.selected_step.getIsVar(self.selected_data_id, row, column_id)

        if isVar == 'Link':
            reply = QMessageBox.question(self, __appname__, "[{}] 변수를 참조하고 있는 경우 삭제 후 참조가 불가능합니다. 변수를 삭제하시겠습니까?".format(variable_id), QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                case.removeVariable(variable_id)

                ref_count = case.setStepRefByVariableId('', variable_id, False)

                if ref_count > 0:
                    reply = QMessageBox.question(self, __appname__, "변수가 삭제되었습니다.\n기존 변수ID를 참조하고 있는 Step [{}]건의 정보도 변경하시겠습니까?".format(ref_count), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        ref_apply_count = case.setStepRefByVariableId('', variable_id, True)
                        QMessageBox.information(self, __appname__, "Step [{}]건 적용되었습니다.".format(ref_apply_count))

                self.setStepView()
        elif isVar == 'Unlink':
            reply = QMessageBox.question(self, __appname__, "변수정보를 삭제하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.selected_step.setRowInfoValue(self.selected_data_id, row, column_id, 'variable', '')
                self.setDataDtlView()
                QMessageBox.information(self, __appname__, "삭제되었습니다.")


    def _declareVariableColumnClicked(self):
        if self.tab_dataDtl.currentIndex() == 0:
            index = self.tw_data.indexAt(self.column_pos)
            row = index.row()
            column = index.column()
            col_id = self.data_model.getHeader(column)
        else:
            row = self.tw_columnInfo.currentRow()
            item = self.tw_columnInfo.item(row, 0)
            col_id = item.text()

        case = self.suites.selectedCase()
        target = self.selected_step
        sub_id = self.selected_data_id
        row_index = self.selected_row
        col_desc = self.selected_step.getColumnValue(self.selected_data_id, col_id, 'description')
        value = self.data_model.getData(self.tw_data.currentIndex())

        declareVariableDialog = DeclareVariableDialog(case)
        declareVariableDialog.declared.connect(self._columnDeclaredVariable)
        declareVariableDialog.popUp(variable_type='Data List', target=target, sub_id=sub_id, row_index=row_index, col_id=col_id, col_desc=col_desc, value=value)


    def _removeVariableColumnClicked(self):
        if self.tab_dataDtl.currentIndex() == 0:
            index = self.tw_data.indexAt(self.column_pos)
            row = index.row()
            column = index.column()
            column_id = self.data_model.getHeader(column)
        else:
            row = self.tw_columnInfo.currentRow()
            item = self.tw_columnInfo.item(row, 0)
            column_id = item.text()

        case = self.suites.selectedCase()
        variable_id = self.selected_step.getColumnValue(self.selected_data_id, column_id, 'variable')

        isVar = self.selected_step.getIsColVar(self.selected_data_id, column_id)

        if isVar == 'Link':
            reply = QMessageBox.question(self, __appname__, "[{}] 변수를 참조하고 있는 경우 삭제 후 참조가 불가능합니다. 변수를 삭제하시겠습니까?".format(variable_id), QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                case.removeVariable(variable_id)
                ref_count = case.setStepRefByVariableId('', variable_id, False)

                if ref_count > 0:
                    reply = QMessageBox.question(self, __appname__, "변수가 삭제되었습니다.\n기존 변수ID를 참조하고 있는 Step [{}]건의 정보도 변경하시겠습니까?".format(ref_count), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        ref_apply_count = case.setStepRefByVariableId('', variable_id, True)
                        QMessageBox.information(self, __appname__, "Step [{}]건 적용되었습니다.".format(ref_apply_count))

                self.selected_step.setColumnValue(self.selected_data_id, column_id, 'variable', '')
                self.setStepView()
        elif isVar == 'Unlink':
            reply = QMessageBox.question(self, __appname__, "변수정보를 삭제하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.selected_step.setColumnValue(self.selected_data_id, column_id, 'variable', '')
                self.setDataDtlView()
                QMessageBox.information(self, __appname__, "삭제되었습니다.")


    def _setReferenceClicked(self):
        case = self.suites.selectedCase()
        variables = case.getApplicableVariables(self.selected_step, self.selected_row, self.selected_column_id)
        variable_key_list = list(variables.keys())

        if variable_key_list:
            variableListDialog = VariableListDialog(case)
            variableListDialog.applied.connect(self._applyRefVariable)
            variableListDialog.removed.connect(self._removeVariable)
            variableListDialog.popUp(self.selected_step, self.selected_data_id, self.selected_row, self.selected_column_id)
        else:
            QMessageBox.information(self, "Setting Reference", "참조 가능한 변수가 없습니다.")


    def _removeReferenceClicked(self):
        ase = self.suites.selectedCase()
        index = self.tw_data.currentIndex()
        row = index.row()
        column_id = self.data_model.getColumnId(index)

        ref_target = self.selected_step.getRowInfoValue(self.selected_data_id, row, column_id, 'ref_target')
        reply = QMessageBox.question(self, __appname__, "[{}] 참조 정보를 삭제하시겠습니까?".format(ref_target), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            row = self.selected_step.getRowInfo(self.selected_data_id, row, column_id)
            row['ref_target'] = ""

            QMessageBox.information(self, "Remove Reference Info", "참조 정보를 삭제하였습니다.")
            self.setStepView()


    def _getReferenceValueClicked(self):
        case = self.suites.selectedCase()
        self.selected_step.getValueByRef()
        self.setDataDtlView()


    def _getTrIOInfo(self):
        '''
        Tr I/O 정보를 조회하여 Setting
        :return: None
        '''
        tr_info = self.selected_step.getTrInfo(action='UDetail')

        if tr_info:
            reply = QMessageBox.question(self, 'Get Transaction IO Info',"Transaction IO 정보를 변경하시겠습니까?",QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                items = ("CHANGE", "MERGE")
                item, ok = QInputDialog.getItem(self, 'Select Method', 'Transaction IO 정보 변환 방법을 선택하세요', items, 0, False)

                if ok and item:
                    self.selected_step.setTrIO(item, tr_info)
                    self.setDataDtlView()


    def _getTrNm(self):
        '''
        Transaction Name 정보를 조회하여 Setting
        :return: None
        '''
        tr_info = self.selected_step.getTrInfo(action='US')

        if tr_info:
            self.selected_step['target_nm'] = tr_info['BasicInfo'][0]['TrxCodeName']
            self.setStepView()
            self.setPropertyView()
            QMessageBox.information(self, "Transaction Name 변경", "Transaction Name을 변경하였습니다.")



    def _addExclutionTrListClicked(self):
        excluded_tr_list = self.suites.getExcludedTrList()
        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)

        target = stepWidget.getTaget()
        description = stepWidget.getDesc()

        reply = QMessageBox.question(self, 'Add to exclusion transaction list', "[{target}] Transaction을 제외 리스트에 추가하시겠습니까?\n\n(이후 Request Capture로 Step 추가 시 [{target}] 은 제외됩니다.)".format(target=target),QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            tr_info = {'tr_id': target, 'tr_name': description}

            if tr_info in excluded_tr_list:
                pass
            else:
                excluded_tr_list.append(tr_info)

            reply = QMessageBox.question(self, 'Remove Step By Excluded Transaction List', "Case에서 제외 리스트에 추가된 [{target}] Transaction을 제외 하시겠습니까?".format(target=target), QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                tmp_excluded_tr_list = [{'tr_id': target, 'tr_name': description}]
                case = self.suites.selectedCase()
                case.removeStepByExcludeTrList(tmp_excluded_tr_list, apply=True)
                self.setStepView()

    def _copyJsonDataClicked(self):
        if self.selected_step is not None:
            if self.selected_step.getType() == 'XHR':
                input_json = self.selected_step.input_data
                output_json = self.selected_step.output_data
                pyperclip.copy(str(input_json) + "::" + str(output_json))
                QMessageBox.information(self, "Copy Test Data", "Complete")


    def _transactionLogClicked(self):
        if self.selected_step is not None:
            if self.selected_step.getType() == 'XHR':
                trx_code = self.selected_step.getTrxCode()
                ip_addr = socket.gethostbyname(socket.getfqdn())
                self.logDialog.setTransactionInfo(trx_code, ip_addr)
                self.logDialog.show()

    def groupClicked(self):
        case = self.suites.selectedCase()
        grouping_step_seq = []

        for item in self.selectedStepItems:
            stepWidget = self.tw_testStep.itemWidget(item, 0)

            if stepWidget is None:
                pass
            else:
                row = stepWidget.getSeq()
                # grouping_step.append(self.selectedCase.getStep(row - 1))
                grouping_step_seq.append(row - 1)

        grouping_step_seq = sorted(grouping_step_seq)
        split_grouping_step = split_seq(grouping_step_seq)

        if len(split_grouping_step) > 1:
            add_msg = '\n(Step의 순서가 변경됩니다.)'
        else:
            add_msg = ''

        group, ok = QInputDialog.getText(self, 'Step grouping', 'Group명을 입력하세요.' + add_msg)

        if ok and group:
            insert_index = grouping_step_seq[0]
            for step_index in grouping_step_seq:

                step = case.getStep(step_index)
                step['group'] = group

                popStep = case.stepList.pop(step_index)
                case.stepList.insert(insert_index, popStep)

                insert_index += 1

            self.setStepView()
            QMessageBox.information(self, "Successful", "Step grouping Successful")


    def _addDataColumnClicked(self):
        '''
        Data Column 추가
        :return: None
        '''
        print(self.selected_column_id)
        new_column_id, ok = QInputDialog.getText(self, 'Column 추가', 'Column명을 입력하세요')

        if ok and new_column_id:
            column_list = self.selected_step.getColumnList(self.selected_data_id)

            if new_column_id in column_list:
                QMessageBox.warning(self, "Column 추가", "동일한 Column이 존재합니다.")
                return False
            else:

                if self.selected_column_id:
                    column_index = column_list.index(self.selected_column_id)
                else:
                    column_index = -1

                self.changeConfirmDialog.addColumnPopUp(self.selected_step, self.selected_data_id, new_column_id, column_index)
                self.setDataDtlView()


    def _addDataRowClicked(self):
        '''
        Data Row 추가
        :return: None
        '''
        column_count = self.selected_step.getColumnCount(self.selected_data_id)

        if column_count > 0 :
            new_row_count, ok = QInputDialog.getInt(self, 'Row 추가', '추가할 Row Count를 입력하세요', 1, 1, 100, 1)

            if ok and new_row_count:
                self.changeConfirmDialog.addRowPopUp(self.selected_step, self.selected_data_id, new_row_count)
                self.setDataDtlView()
        else:
            QMessageBox.information(self, "Row 추가", "DataList에 존재하는 Column이 없습니다.\nColumn추가 후 Row추가 가능합니다.")


    def _deleteDataRowClicked(self):
        '''
        Data Row 삭제
        :return:
        '''
        reply = QMessageBox.question(self, 'Row 삭제', "[{row}] 번째 Row를 삭제하시겠습니까?".format(row=self.selected_row), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.changeConfirmDialog.deleteRowPopUp(self.selected_step, self.selected_data_id, self.selected_row)
            self.setDataDtlView()


    def _deleteDataColumnClicked(self):
        '''
        Data Column 삭제
        :return: None
        '''
        reply = QMessageBox.question(self, 'Column 삭제', "Column [{column_id}]을 삭제하시겠습니까?".format(column_id=self.selected_column_id), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.changeConfirmDialog.deleteColumnPopUp(self.selected_step, self.selected_data_id, self.selected_column_id)
            self.setDataDtlView()


    def _stepMoveToUp(self):
        '''
        Step을 위로 이동
        '''
        sort_step_list = self.getSelectedSteps()
        self.stepMoveTo(sort_step_list, increase=-1)


    def _stepMoveToDown(self):
        '''
        Step을 아래로 이동
        '''
        sort_step_list = self.getSelectedSteps(reverse=True)
        self.stepMoveTo(sort_step_list, increase=1)


    def setRefByValue(self, ref_variable='Row'):
        '''
        현재 값 기준으로 동일한 값을 가진 Row의 참조 정보를 해당 변수로 변경함
            - 참조 정보로 사용되기 위해선 사전에 변수로 선언되어 있어야함
        :return: None
        '''
        case = self.suites.selectedCase()
        index = self.tw_data.currentIndex()
        row = index.row()
        column = index.column()

        if row > -1 and column > -1:
            find_value = self.data_model.getData(index)
            column_id = self.data_model.getHeader(column)

        if ref_variable == 'Row':
            variable = self.selected_step.getRowInfoValue(self.selected_data_id, row, column_id, 'variable')
        elif ref_variable == 'Column':
            variable = self.selected_step.getColumnValue(self.selected_data_id, column_id, 'variable')

        if variable:
            if find_value:
                setCount = case.setStepRefByValue(find_value, variable, min_row=self.selected_step.getSeq(), apply=False)

                if setCount > 0:
                    reply = QMessageBox.question(self, 'Set Reference By Value', "[{cnt}]건 적용가능합니다.\n적용 하시겠습니까?".format(cnt=setCount), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        setCount = case.setStepRefByValue(find_value, variable, min_row=self.selected_step.getSeq(), apply=True)
                        QMessageBox.information(self, "Set Reference By Value", "[{cnt}]건 적용완료".format(cnt=setCount))
                else:
                    QMessageBox.information(self, "Set Reference By Value", "적용가능한 Column이 없습니다.")
        else:
            reply = QMessageBox.question(self, 'Set Reference By Value', "변수 선언 후 진행가능합니다.\n변수로 정의 하시겠습니까?", QMessageBox.Yes,QMessageBox.No)

            if reply == QMessageBox.Yes:
                self._declareVariableClicked()


    def _replayXhrClicked(self):
        if self.selected_step is not None:
            # Reference DataList Setting
            #self.selectedCase.setRefExcelValue(self.suite.getRefDataList())

            # Reference DataList Setting
            #self.selectedCase.setRefDataListValue()
            #self.selectedCase.setRefTodayValue()

            #self.setTestDataDtlView()

            #self.selectedData.replayRequest()

            #self.running.emit()
            try:
                self.selected_step.getValueByRef()
            except StopIteration:
                stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
                stepWidget.setStatus()
                QMessageBox.information(self, "Replay Step", "참조값을 확인하세요.")
                return False

            if self.selected_step.get('step_type_group') in ['Browser', 'Browser Command', 'Browser Command (Swing)']:
                self.selected_step.setWeb(self.suitesWidget.mainWidget.web)

            self.eventWorker = EventThread(self.selected_step.startStep)
            self.eventWorker.finished.connect(self.replayXhrFinished)
            self.eventWorker.start()
        else:
            QMessageBox.information(self, "Replay Request", "[{}] Test data does not exist\n".format(self.selectedStep.target))

    def replayAllXhrToDownClicked(self):
        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        index = stepWidget.getSeq() - 1

        self.xhrToDown.emit(index)

    def replayXhrFinished(self):
        if self.selected_step.get('step_type_group') in ['Browser', 'Browser Command', 'Browser Command (Swing)']:
            self.suitesWidget.mainWidget.web = self.selected_step.getWeb()

        add_info_type = self.cb_addInfo.currentText()

        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        stepWidget.setStatus()
        stepWidget.setTarget()
        stepWidget.setAddInfo(add_info_type)

        msg = self.selected_step.getParamsMsg()

        self.setDataListView()

        QMessageBox.information(self, "Replay Request", "Replay Request Complete\n[{}]".format(msg))


    # ============================ Component Event ============================
    def _twTestStepItemSelectionChanged(self, item):
        '''
        step list tree item 변경 이벤트
            - item 변경 시 선택된 step의 정보를 갱신
            - data list view, data dtl view, property view 를 갱신
            - action widget 활성화/비활성화
        :param item:
        :return:
        '''

        self.selectedStepItems = []

        # List Clear 시는 Skip
        index = self.tw_testStep.indexFromItem(item, column=0)

        if index.row() >= 0:
            self.selected_step = self.findSelectedStep()
        else:
            self.selected_step = None

        self.selected_column_id = ''
        self.selected_row = -1
        self.setDataListView()
        self.setDataDtlView()
        self.setPropertyView()
        self.setComponetEnable()


    def _twDataListItemSelectionChanged(self, item):
        '''
        data list tree item 변경 이벤트
            - item 변경 시 data dtl view, property view를 갱신
        :param item: tree에서 선택된 item
        :return: None
        '''
        self.selected_data_id = ''
        self.selected_column_id = ''
        self.selected_row = -1

        if item is not None:
            if self.selected_step is not None:
                parent_node = item.parent()

                if parent_node is not None:
                    self.selected_data_id = item.text(0)

                self.setDataDtlView()
        self.setPropertyView()


    def _lwTestStepCellDoubleClicked(self):
        '''
        step list 더블클릭 이벤트
        step의 정보를 변경 할 수 있는 화면 활성화
        :return: None
        '''
        if self.selected_step is not None:
            case = self.suites.selectedCase()
            addStepDialog = AddStepDialog(call_gubun='Change', case=case, step=self.selected_step)
            addStepDialog.changed.connect(self._stepChanged)
            addStepDialog.popUp()


    def _twDataCurrentChanged(self, current, previous):
        '''
        data dtl view column 변경 이벤트
            - column 변경 시 data dtl view, property view, column Info view를 갱신
        :param current:
        :param previous:
        :return:
        '''
        row = current.row()

        if row > -1:
            col = current.column()
            self.selected_row = row
            self.selected_column_id = self.data_model.getHeader(col)
            self.setPropertyView()
            self.setColumnInfoRow(col)
            self.tw_data.scrollTo(self.data_model.index(row, col))
        else:
            self.selected_row = row
            self.selected_column_id = ''


    def _twColumnInfoClicked(self, row, col):
        '''
        Column Info Click 이벤트
            - selected_column_id 변경하고 property view 갱신
        '''
        self.tw_data.clearSelection()
        item = self.tw_columnInfo.item(row, 0)
        self.selected_column_id = item.text()
        #self.selected_row = -1
        self.setPropertyView()
        self.setDataDtlCurrnetRow(0, row)


    def _twStepDroped(self, event):
        '''
        Test Step List Drop event
            - Step의 순서를 변경
        :param event:
        :return:
        '''
        from_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        to_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.itemAt(event.pos().x(), event.pos().y()), 0)
        case = self.suites.selectedCase()

        # Group Title로 이동한 경우는 Skip
        if to_stepWidget is not None:
            moved_to = to_stepWidget.getSeq() - 1
            moved_to_step = case.getStep(moved_to)

            if from_stepWidget is None:
                fromTarget = 'Group : {}'.format(self.tw_testStep.currentItem().text(0))
                group_step_index_list = []
                for idx in range(0, self.tw_testStep.currentItem().childCount()):
                    child_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem().child(idx), 0)
                    child_step_index = child_stepWidget.getSeq() - 1
                    group_step_index_list.append(child_step_index)

                first_step = case.getStep(group_step_index_list[0])
                moved_from = first_step.getSeq()

                if moved_from > moved_to:
                    position = '이전으로'
                else:
                    position = '이후로'


                # 그룹 전체를 다른 그룹으로 이동 (그룹 변경)
                if moved_to_step.get('group') and moved_to_step.get('group') != first_step.get('group'):
                    reply = QMessageBox.question(self, 'Change step order', "[{group}] 그룹 Step 순서를 [{to_step}] {position} 변경하시겠습니까?\n(Group도 {toGroup}으로 변경됨)".format(group=first_step.get('group'), to_step=moved_to_step.get('target'), position=position, toGroup=moved_to_step.get('group')), QMessageBox.Yes, QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        for step_index in reversed(group_step_index_list):
                            popStep = case.stepList.pop(step_index)
                            popStep['group'] = moved_to_step.get('group')
                            case.stepList.insert(moved_to, popStep)

                        self.setStepView()
                # 그룹 전체를 그룹이 아닌 Step으로 이동 (그룹 유지)
                else:
                    reply = QMessageBox.question(self, 'Change step order', "[{group}] 그룹 Step 순서를 [{to_step}] {position} 변경하시겠습니까?".format(group=first_step.get('group'), to_step=moved_to_step.get('target'), position=position), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        for step_index in reversed(group_step_index_list):
                            popStep = case.stepList.pop(step_index)
                            case.stepList.insert(moved_to, popStep)

                        self.setStepView()
            else:
                moved_from = from_stepWidget.getSeq()-1
                to_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.itemAt(event.pos().x(), event.pos().y()), 0)
                moved_to = to_stepWidget.getSeq()-1

                from_step = case.getStep(moved_from)
                to_step = case.getStep(moved_to)

                if to_step.getType() == 'IF':
                    reply = QMessageBox.question(self, 'Change step order',"[{from_step}] Step을 조건문 하위 Step으로 이동하시겠습니까?".format(from_step=from_step.get('target')), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        from_step['condition_step_id'] = to_step.getId()
                        popStep = case.stepList.pop(moved_from)
                        case.stepList.insert(moved_to+1, popStep)
                        self.setStepView()

                else:
                    if moved_from > moved_to:
                        position = '이전으로'
                    else:
                        position = '이후로'

                    reply = QMessageBox.question(self, 'Change step order', "[{from_step}] Step 순서를 [{to_step}] {position} 이동하시겠습니까?".format(from_step=from_step.get('target'), to_step=to_step.get('target'), position=position), QMessageBox.Yes, QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        from_step_group = from_step.get('group')
                        from_step['group'] = to_step.get('group')
                        #to_step['group'] = from_step_group

                        popStep = case.stepList.pop(moved_from)
                        case.stepList.insert(moved_to, popStep)
                        self.setStepView()


    def _cbAddInfoColumnIdCurrentIndexChanged(self, add_info_type):
        '''
        추가정보 Combobox 변경 시 발생되는 이벤트
            - Step 상세의 추가정보를 표기하기 위함
        :param add_info_type: (str) '수행시간'
        :return: None
        '''
        for item in self.tw_testStep.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            stepWidget = self.tw_testStep.itemWidget(item, 0)
            if stepWidget:
                stepWidget.setAddInfo(add_info_type)

        if add_info_type == '수행시간':
            self.displayMaxElapsedTime()


    def _stepAdded(self, step, index):
        '''
        AddStepDialog를 통해 Step 추가 시 발생되는 이벤트
            - 현재 Step 이전에 추가
            - 현재 Step 이후에 추가
        :param step:
        :param index: (int) 1
        :return: None
        '''
        case = self.suites.selectedCase()

        if index > -1:
            case.setStepList(step, index)
        else:
            index = len(case.stepList)
            case.setStepList(step)

        self.setStepView()

        case = self.suites.selectedCase()
        self.setTestStepCurrnetRow(index)


    def _stepChanged(self):
        '''
        AddStepDialog를 통해 Step 변경 시 발생되는 이벤트
        :return: None
        '''
        self.setStepView()
        QMessageBox.information(self, "Successful", "Step Change Successful")


    def _rowDeclaredVariable(self, variable_id):
        '''
        DeclareVariabldDialog를 통해 변수로 등록된 경우 발생되는 이벤트
            - Row Info에 variable 정보를 Setting하고 property view를 갱신
        :return: None
        '''
        self.selected_step.setRowInfoValue(self.selected_data_id, self.selected_row, self.selected_column_id, 'variable', variable_id)
        self.setPropertyView()
        self.setRefByValue(ref_variable='Row')

        self.setStepView()
        #stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        #stepWidget.setVarChkRst()


    def _columnDeclaredVariable(self, variable_id):
        '''
        DeclareVariabldDialog를 통해 변수로 등록된 경우 발생되는 이벤트
            - Column Info에 variable 정보를 Setting하고 property view를 갱신
        :return: None
        '''
        self.selected_step.setColumnValue(self.selected_data_id, self.selected_column_id, 'variable', variable_id)
        self.setPropertyView()
        self.setRefByValue(ref_variable='Column')

        self.setStepView()


    def _applyRefVariable(self, variable_id, ref_option_info):
        '''
        VariableListDialog를 통해 참조 변수를 선택한 경우 발생되는 이벤트
            - Row Info에 ref_target 정보를 Setting하고 property view를 갱신
        :return: None
        '''
        self.selected_step.setRowInfoValue(self.selected_data_id, self.selected_row, self.selected_column_id, 'ref_target', variable_id)
        self.selected_step.setRowInfoValue(self.selected_data_id, self.selected_row, self.selected_column_id, 'ref_option', ref_option_info)
        self.setPropertyView()

        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        stepWidget.setRefChkRst()


    def _removeVariable(self):
        '''
        VariableListDialog에서 변수를 삭제한 경우 발생되는 이벤트
            - property view를 갱신
        :return: None
        '''
        self.setPropertyView()


    def _setInputData(self, index):
        '''
        Step Data Dtl View 값 변경 시 발생 이벤트
            - Step input_data 를 변경
            - property view를 갱신
        :return: None
        '''
        row = index.row()
        column = self.data_model.getColumnId(index)
        value = self.data_model.getData(index)

        self.changeConfirmDialog.changeDataPopUp(self.selected_step, self.selected_data_id, row, column, value)

        #self.selected_step.setInputDataValue(self.selected_data_id, row, column, value)
        self.setDataDtlView()
        self.setPropertyView()


    def _columnDescChanged(self, column_id):
        '''
        Column 설명 변경 시 발생 이벤트
        :param column_id: (str) svc_num
        :return: None
        '''
        column_desc = self.sender()

        bef_desc = self.selected_step.getColumnValue(self.selected_data_id, column_id, 'description')
        atf_desc = column_desc.text()

        if bef_desc != atf_desc:
            if self.changeConfirmDialog.isVisible():
                pass
            else:
                self.changeConfirmDialog.changeColumnDescPopUp(self.selected_step, data_list_id=self.selected_data_id, column_id=column_id, bef_desc=bef_desc, atf_desc=atf_desc, column_component=column_desc)

    def _columnDescClicked(self, row, event):
        '''
        Column Info QLine Editor 변경 시 발생 이벤트
            - Column Info Table Widget Row를 변경
        '''
        self.tw_columnInfo.setCurrentCell(row, 0)

    def _stepColumnChanged(self, cnt):
        QMessageBox.information(self, "Successful", "[{}] 건 적용되었습니다.".format(cnt))


    def _stepColumnCancle(self, column_component, bef_desc):
        column_component.setText(bef_desc)


    # ============================ Component Setting ============================
    def setStepView(self):
        '''
        Step List View Setting
        :return: None
        '''
        self.tw_testStep.clear()

        case = self.suites.selectedCase()
        if case is not None:
            add_info_type = self.cb_addInfo.currentText()

            for idx, step in enumerate(case.stepList):
                #ref_link_chk_rst = step.refExistChk(case)

                stepWidget = StepDtlWidget()
                stepWidget.setSeq(str(idx + 1))
                stepWidget.setStepDtl(step)
                stepWidget.setAddInfo(add_info_type)

                # Add QListWidgetItem into QListWidget
                if step.get('condition_step_id'):
                    selectTreeItem = self.tw_testStep.findItems(step.get('condition_step_id'), Qt.MatchExactly | Qt.MatchRecursive, column=2)

                    if selectTreeItem:
                        childWidgetItem = QTreeWidgetItem(selectTreeItem[0])
                        childWidgetItem.setText(1, str(idx))
                        childWidgetItem.setText(2, step.getId())
                        self.tw_testStep.setItemWidget(childWidgetItem, 0, stepWidget)
                    else:
                        step.remove('condition_step_id')
                        myQTreeWidgetItem = QTreeWidgetItem(self.tw_testStep)
                        myQTreeWidgetItem.setText(1, str(idx))
                        myQTreeWidgetItem.setText(2, step.getId())
                        self.tw_testStep.setItemWidget(myQTreeWidgetItem, 0, stepWidget)

                elif step.get('group'):
                    selectTreeItem = self.tw_testStep.findItems(step.get('group'), Qt.MatchExactly | Qt.MatchRecursive, column=0)

                    if selectTreeItem:
                        childWidgetItem = QTreeWidgetItem(selectTreeItem[0])
                        childWidgetItem.setText(1, str(idx))
                        childWidgetItem.setText(2, step.getId())
                        self.tw_testStep.setItemWidget(childWidgetItem, 0, stepWidget)
                    else:
                        parentWidgetItem = QTreeWidgetItem(self.tw_testStep)
                        parentWidgetItem.setText(0, step.get('group'))
                        parentWidgetItem.setForeground(0, QColor(255, 99, 71))
                        parentWidgetItem.setFont(0, QFont('맑은 고딕', 10))

                        childWidgetItem = QTreeWidgetItem(parentWidgetItem)
                        childWidgetItem.setText(1, str(idx))
                        childWidgetItem.setText(2, step.getId())
                        self.tw_testStep.setItemWidget(childWidgetItem, 0, stepWidget)
                else:
                    myQTreeWidgetItem = QTreeWidgetItem(self.tw_testStep)
                    myQTreeWidgetItem.setText(1, str(idx))
                    myQTreeWidgetItem.setText(2, step.getId())
                    self.tw_testStep.setItemWidget(myQTreeWidgetItem, 0, stepWidget)

            self.tw_testStep.expandToDepth(1)

            if add_info_type == '수행시간':
                self.displayMaxElapsedTime()

            if case.getSelectedStepRow() > -1:
                self.setTestStepCurrnetRow(case.getSelectedStepRow())
    
    
    def setDataListView(self):
        '''
        Step Data List View Setting
        :return: None
        '''
        self.tw_dataList.clear()

        first_item = None

        if self.selected_step is not None:
            if self.selected_step.getType() == 'XHR':
                selected_data_list = self.selected_step.getSelectedDataList()
                input_data_list = self.selected_step.getDataListId('input')
                output_data_list = self.selected_step.getDataListId('output')

                if input_data_list:
                    input_node = QTreeWidgetItem(self.tw_dataList)
                    input_node.setText(0, 'Input')

                    for child in input_data_list:
                        childWidgetItem = QTreeWidgetItem(input_node)
                        childWidgetItem.setText(0, child)

                        ref_check = self.selected_step.getIsRef(child)
                        var_check = self.selected_step.getIsVar(child)

                        icon = ''
                        if ref_check == 'Link' and var_check == 'Link':
                            icon = QIcon(':/variable/' + 'var_and_link.png')
                        elif ref_check == 'Link' and var_check == 'Unlink':
                            icon = QIcon(':/variable/' + 'unvar_and_link.png')
                        elif ref_check == 'Unlink' and var_check == 'Link':
                            icon = QIcon(':/variable/' + 'var_and_unlink.png')
                        elif ref_check == 'Unlink' and var_check == 'Unlink':
                            icon = QIcon(':/variable/' + 'unvar_and_unlink.png')
                        elif ref_check == 'Link':
                            icon = QIcon(':/ref/' + 'link.png')
                        elif ref_check == 'Unlink':
                            icon = QIcon(':/ref/' + 'unlink.png')
                        elif var_check == 'Link':
                            icon = QIcon(':/variable/' + 'var.png')
                        elif var_check == 'Unlink':
                            icon = QIcon(':/variable/' + 'unvar.png')

                        if icon:
                            childWidgetItem.setIcon(0, icon)

                        if first_item is None:
                            first_item = childWidgetItem

                if output_data_list:
                    output_node = QTreeWidgetItem(self.tw_dataList)
                    output_node.setText(0, 'Output')

                    for child in output_data_list:
                        childWidgetItem = QTreeWidgetItem(output_node)
                        childWidgetItem.setText(0, child)

                        var_check = self.selected_step.getIsVar(child)

                        icon = ''
                        if var_check == 'Link':
                            icon = QIcon(':/variable/' + 'var.png')
                        elif var_check == 'Unlink':
                            icon = QIcon(':/variable/' + 'unvar.png')

                        if icon:
                            childWidgetItem.setIcon(0, icon)

                        if first_item is None:
                            first_item = childWidgetItem

                self.tw_dataList.expandToDepth(0)

                if selected_data_list:
                    selectTreeItem = self.tw_dataList.findItems(selected_data_list, Qt.MatchExactly | Qt.MatchRecursive, column=0)

                    if selectTreeItem:
                        self.tw_dataList.setCurrentItem(selectTreeItem[0])
                else:
                    self.tw_dataList.setCurrentItem(first_item)


    def setDataDtlView(self):
        '''
        Step Data Dtl View Setting
            - Step Type에 따라 정보영역 변경
        :return: None
        '''
        self.tw_groupVariable.clearContents()
        self.tw_groupReference.clearContents()

        self.tw_columnInfo.clearContents()
        self.tw_columnInfo.setRowCount(0)

        if self.selected_step is None:
            case = self.suites.selectedCase()
            stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
            if stepWidget is not None:
                self.sw_stepDtl.setCurrentIndex(0)
            elif case is None:
                self.sw_stepDtl.setCurrentIndex(0)
            else:
                variable_list = []
                ref_list = []
                item = self.tw_testStep.currentItem()

                if item:
                    group = item.text(0)
                    case = self.suites.selectedCase()
                    step_list = case.findStepByType('XHR', key='group', value=group)

                    for step in step_list:
                        variable_list.extend(step.getVariables())
                        ref_list.extend(step.getRefVariables())

                    self.tw_groupVariable.setRowCount(len(variable_list))
                    self.tw_groupReference.setRowCount(len(ref_list))

                    for idx, variable_id in enumerate(variable_list):
                        self.tw_groupVariable.setItem(idx, 0, QTableWidgetItem(variable_id))

                    for idx, ref in enumerate(ref_list):
                        self.tw_groupReference.setItem(idx, 0, QTableWidgetItem(ref))

                self.sw_stepDtl.setCurrentIndex(1)
        elif self.selected_step.getType() == 'XHR':
            self.sw_stepDtl.setCurrentIndex(2)
            if self.selected_data_id:
                data = self.selected_step.getDataList(self.selected_data_id, return_type='dataframe')
                self.data_model = PandasModel(data)
                self.data_model.dataChanged.connect(self._setInputData)
                self.data_model.setEditable(True)
                self.data_model.setStep(self.selected_step, self.selected_data_id)
                self.tw_data.setModel(self.data_model)

                column_info = self.selected_step.getColumnValues(self.selected_data_id, 'description')

                self.tw_columnInfo.setRowCount(len(column_info))

                for idx, column_id in enumerate(column_info):
                    desc_item = QLineEdit(column_info[column_id])
                    desc_item.editingFinished.connect(partial(self._columnDescChanged, column_id))
                    desc_item.focusInEvent = partial(self._columnDescClicked, idx)
                    desc_item_cell_widget = horizontalLayout([desc_item])

                    isVar = self.selected_step.getIsColVar(self.selected_data_id, column_id)

                    if isVar:
                        column_item = QTableWidgetItem(QIcon(':/variable/' + 'var.png'), column_id)
                    else:
                        column_item = QTableWidgetItem(column_id)

                    self.tw_columnInfo.setItem(idx, 0, column_item)
                    self.tw_columnInfo.setCellWidget(idx, 1, desc_item_cell_widget)
                    #self.tw_columnInfo.setItem(idx, 1, QTableWidgetItem(column_info[column_id]))
            else:
                self.tw_data.setModel(self.none_model)
        else:
            self.sw_stepDtl.setCurrentIndex(0)


    def setPropertyView(self):
        '''
        Property View Setting
        :return: None
        '''
        self.tw_property.clear()

        if self.selected_step is not None:
            root_font = QFont('맑은 고딕', 11)
            root_font.setBold(True)

            # Step Info
            step_info_root_item = QTreeWidgetItem(self.tw_property)
            step_info_root_item.setText(0, "Step")
            step_info_root_item.setForeground(0, QColor(0, 191, 255))
            step_info_root_item.setFont(0, root_font)
            #step_info_root_item.setText(1, "Step Info")

            step_id = QTreeWidgetItem(step_info_root_item)
            step_id.setText(0, "type")
            step_id.setText(1, str(self.selected_step.getType()))

            step_id = QTreeWidgetItem(step_info_root_item)
            step_id.setText(0, "step seq")
            step_id.setText(1, str(self.selected_step.getSeq()))

            step_id = QTreeWidgetItem(step_info_root_item)
            step_id.setText(0, "step id")
            step_id.setText(1, self.selected_step.getId())

            step_info_keys = self.selected_step.getKey()

            if step_info_keys:
                for key in step_info_keys:
                    item = QTreeWidgetItem(step_info_root_item)
                    item.setText(0, key)
                    #item.setText(1, str(self.selected_step.get(key)))
                    labelWidget = QLabel(str(self.selected_step.get(key)))
                    labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                    self.tw_property.setItemWidget(item, 1, labelWidget)

            # Data Info
            if self.selected_data_id:
                data_info_root_item = QTreeWidgetItem(self.tw_property)
                data_info_root_item.setText(0, "Data")
                data_info_root_item.setForeground(0, QColor(0, 191, 255))
                data_info_root_item.setFont(0, root_font)
                #data_info_root_item.setText(1, "Data Info")

                data_id = QTreeWidgetItem(data_info_root_item)
                data_id.setText(0, "data id")
                labelWidget = QLabel(self.selected_data_id)
                labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                self.tw_property.setItemWidget(data_id, 1, labelWidget)

            # Column Info
            if self.selected_column_id:
                column_info_root_item = QTreeWidgetItem(self.tw_property)
                column_info_root_item.setText(0, "Column")
                column_info_root_item.setForeground(0, QColor(0, 191, 255))
                column_info_root_item.setFont(0, root_font)
                #column_info_root_item.setText(1, "Column Info")

                column_id = QTreeWidgetItem(column_info_root_item)
                column_id.setText(0, "column id")
                labelWidget = QLabel(self.selected_column_id)
                labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                self.tw_property.setItemWidget(column_id, 1, labelWidget)

                desc = self.selected_step.getColumnValue(self.selected_data_id, self.selected_column_id, 'description')
                column_desc = QTreeWidgetItem(column_info_root_item)
                column_desc.setText(0, "column desc")
                labelWidget = QLabel(desc)
                labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                self.tw_property.setItemWidget(column_desc, 1, labelWidget)

                variable = self.selected_step.getColumnValue(self.selected_data_id, self.selected_column_id, 'variable')
                column_variable = QTreeWidgetItem(column_info_root_item)
                column_variable.setText(0, "variable")
                labelWidget = QLabel(variable)
                labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                labelWidget.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='SandyBrown', text=variable))
                self.tw_property.setItemWidget(column_variable, 1, labelWidget)

            # Row Info
            if self.selected_row > -1:
                row_info_root_item = QTreeWidgetItem(self.tw_property)
                row_info_root_item.setText(0, "Row")
                row_info_root_item.setForeground(0, QColor(0, 191, 255))
                row_info_root_item.setFont(0, root_font)
                #row_info_root_item.setText(1, "Row Info")

                row_info = self.selected_step.getRowInfo(self.selected_data_id, self.selected_row, self.selected_column_id)

                if row_info:
                    row_info_keys = row_info.getKey()

                    if row_info_keys:
                        for key in row_info_keys:
                            item = QTreeWidgetItem(row_info_root_item)
                            item.setText(0, key)

                            value = row_info.get(key)

                            if type(value) == bool:
                                checkWidget = QCheckBox()
                                checkWidget.setChecked(value)
                                checkWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                                checkWidget.stateChanged.connect(self._checkbox_change)
                                self.tw_property.setItemWidget(item, 1, checkWidget)
                                #item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                                #item.setCheckState(1, value)
                            else:
                                text = str(row_info.get(key))
                                labelWidget = QLabel(text)
                                labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
                                if key == 'variable':
                                    labelWidget.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='SandyBrown', text=text))
                                elif key == 'ref_target':
                                    labelWidget.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='DeepSkyBlue', text=text))
                                self.tw_property.setItemWidget(item, 1, labelWidget)

            self.tw_property.expandToDepth(0)


    def stepMoveTo(self, step_list, increase=-1):
        '''
        Step Tree Widget에서 이동
            - case step list에서 순서 변경
            - step의 seq 변경
            - step 위로 이동하거나 아래로 이동 시 호출
        :param step_list: [(class) step1, (class) step2, ...]
        :param increase: (int) -1
        :return: None
        '''
        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        case = self.suites.selectedCase()

        if stepWidget:
            for step in step_list:
                from_index = case.getStepIndex(step)
                to_index = from_index + increase

                if from_index == 0 or to_index == case.getStepCount():
                    pass
                else:
                    from_step = case.getStep(from_index)
                    to_step = case.getStep(to_index)

                    if from_step.getGroup() == to_step.getGroup():
                        from_step = case.stepList.pop(from_index)
                        from_step.setSeq(to_index)
                        to_step.setSeq(from_index)
                        from_step['group'] = to_step.getGroup()
                        case.stepList.insert(to_index, from_step)
                    else:
                        from_step['group'] = to_step.getGroup()
                        case.setSelectedStepRow(from_index)

            self.setStepView()

            for step in step_list:
                selected_stepWidget = self.getStepWidget(step)
                selected_stepWidget.setSelected(True)
        else:
            group_step_list = []
            for idx in range(0, self.tw_testStep.currentItem().childCount()):
                child_stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem().child(idx), 0)
                child_step = child_stepWidget.getStep()
                group_step_list.append(child_step)

            first_step_index = case.getStepIndex(group_step_list[0])
            last_step_index = case.getStepIndex(group_step_list[-1])

            '''
            이동하는 Group의 가장 처음의 Step Index 앞으로 이동
            '''
            if increase > 0:
                to_step_index = last_step_index + increase
            else:
                to_step_index = first_step_index + increase

            if to_step_index == case.getStepCount():
                pass
            else:
                to_step = case.getStep(to_step_index)
                to_step_group = to_step.getGroup()
                to_step_first_index = case.findStepIndexByGroup(to_step_group)

                for step in reversed(group_step_list):
                    step_index = case.getStepIndex(step)
                    pop_step = case.stepList.pop(step_index)
                    case.stepList.insert(to_step_first_index, pop_step)

                self.setStepView()
                currentItem = self.tw_testStep.findItems(group_step_list[0].getGroup(), Qt.MatchExactly | Qt.MatchRecursive, column=0)
                self.tw_testStep.setCurrentItem(currentItem[0])


    def getStepWidget(self, step):
        '''
        Step id로 TreeWidget을 찾아 Return
        :param step: (class) step
        :return: QWidget
        '''
        stepWidgetItem = self.tw_testStep.findItems(step.getId(), Qt.MatchExactly | Qt.MatchRecursive, column=2)
        return stepWidgetItem[0]


    def getSelectedSteps(self, reverse=False):
        '''
        현재 선택된 Step을 List로 Return
        :return: (list) [(class) step1, (class) step2, ...]
        '''
        selected_step_list = []
        selectedStepItems = self.tw_testStep.selectedItems()

        for item in selectedStepItems:
            stepWidget = self.tw_testStep.itemWidget(item, 0)

            if stepWidget is None:
                pass
            else:
                step = stepWidget.getStep()
                selected_step_list.append(step)

        selected_step_list = sorted(selected_step_list, key=lambda step: (step.getSeq()), reverse=reverse)

        return selected_step_list


    def setTestStepCurrnetRow(self, row):
        '''
        Step TreeWidget row 로 Focus
        :param row: (int) 3
        :return: None
        '''
        selectTreeItem = self.tw_testStep.findItems(str(row), Qt.MatchExactly | Qt.MatchRecursive, column=1)

        if selectTreeItem:
            self.tw_testStep.setCurrentItem(selectTreeItem[0])


    def setDataListCurrnetRow(self, data_list_id):
        '''
        data list TreeWidget 에 data_list_id 해당하는 Row에 Focus
        :param data_list_id: (str) 'input1'
        :return: None
        '''
        selectTreeItem = self.tw_dataList.findItems(data_list_id, Qt.MatchExactly | Qt.MatchRecursive, column=0)

        if selectTreeItem:
            self.tw_dataList.setCurrentItem(selectTreeItem[0])


    def setDataDtlCurrnetRow(self, row_index, column):
        '''
        data dtl TableView 에 row_index, column 해당하는 위치로 Focus
        :param row_index: (int) 0
        :param column: (str) or (int) svc_chg_cd
        :return: None
        '''
        if type(column) == str:
            column_index = self.data_model.getColumnIndex(column)
        elif type(column) == int:
            column_index = column

        index = self.data_model.index(row_index, column_index)
        self.tw_data.setCurrentIndex(index)


    def setColumnInfoRow(self, row):
        '''
        Column Info Table의 row에 Focus
        :param row: (int) 0
        '''
        if type(row) == str:
            column_list = self.selected_step.getColumnList(self.selected_data_id)
            row_index = column_list.index(row)
        elif type(row) == int:
            row_index = row

        self.tw_columnInfo.setCurrentCell(row_index, 0)


    def _checkbox_change(self):
        '''
        Properties 항목 중 Checkbox 클릭 시 발생 이벤트
            - marking, input_value
        :return: None
        '''
        chk = self.sender()

        for item in self.tw_property.selectedItems():
            selectedNode = item

        key = selectedNode.text(0)
        self.selected_step.setRowInfoValue(self.selected_data_id, self.selected_row, self.selected_column_id, key, chk.isChecked())


    def displayMaxElapsedTime(self):
        '''
        Step의 추가정보가 수행시간인 경우 Max 수행시간의 Step 정보를 표기
        :return: None
        '''
        case = self.suites.selectedCase()
        elapsed_max_time_step_list = case.findMaxElapsedTimeStep(rank=3)

        for step in elapsed_max_time_step_list:
            selectTreeItem = self.tw_testStep.findItems(step.getId(), Qt.MatchExactly | Qt.MatchRecursive, column=2)[0]
            stepWidget = self.tw_testStep.itemWidget(selectTreeItem, 0)

            if stepWidget:
                stepWidget.setDesc("<h4><font color='Crimson'>{}</font></h4>".format(step.get('exec_time')))



    # ============================ Component Setting ============================
    def runCase(self):
        '''
        Suites Widget에서 Case 수행 시 호출하는 이벤트
            - case 수행 시 data list view, data dtl view, property view를 비활성화
        :return: None
        '''
        self.tw_dataList.clear()
        self.tw_property.clear()
        self.tw_data.setModel(self.none_model)

        self.setStepView()

        self.tw_testStep.setEnabled(False)
        self.tw_dataList.setEnabled(False)
        self.tw_data.setEnabled(False)
        self.tw_property.setEnabled(False)


    def stepFisished(self, step, idx):
        '''
        Suites Widget에서 Step 수행 완료시 호출하는 이벤트
            - 완료 된 Step에 Focus를 이동하고 수행결과(code, msg) 정보를 Step Dtl Widget에 Setting함
        :param step: (Class) Step
        :param idx: seq
        :return: None
        '''
        add_info_type = self.cb_addInfo.currentText()

        selectTreeItem = self.tw_testStep.findItems(str(idx), Qt.MatchExactly | Qt.MatchRecursive, column=1)
        self.tw_testStep.setCurrentItem(selectTreeItem[0])

        stepWidget = self.tw_testStep.itemWidget(self.tw_testStep.currentItem(), 0)
        stepWidget.setStatus()
        stepWidget.setAddInfo(add_info_type)

        self.tw_testStep.setEnabled(False)


    def caseFisished(self):
        '''
        Suites Widget에서 Case 수행 완료 시 호출하는 이벤트
            - case 수행 시 data list view, data dtl view, property view를 활성화
        :return: None
        '''
        self.tw_testStep.setEnabled(True)
        self.tw_dataList.setEnabled(True)
        self.tw_data.setEnabled(True)
        self.tw_property.setEnabled(True)

        self.setDataListView()
        self.setDataDtlView()