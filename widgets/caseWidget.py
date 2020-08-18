import os
import copy
import pickle
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from functools import partial

from utils.lib import addTreeRoot, addTreeChild, newIcon

from widgets.caseProgressWidget import CaseProgressWidget
from dialogs.caseDialog import CaseDialog
from dialogs.autoVariableDialog import AutoVariableDialog
from dialogs.variableListDialog import VariableListDialog
from dialogs.markingDataDialog import MarkingDataDialog
from widgets.mainSplash import ProgressSplash

from utils.caseWorker import CaseThread              # Case 단위 Thread 처리
from utils.eventWorker import EventThread

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
widget_class = uic.loadUiType(os.path.join(parentDir, "UI/case_widget.ui"))[0]

__appname__ = 'Test Automation Tool'

class CaseWidget(QWidget, widget_class):
    selected = pyqtSignal("PyQt_PyObject")
    stepFinished = pyqtSignal("PyQt_PyObject", int)
    caseFinished = pyqtSignal()
    varLoadApplied = pyqtSignal()
    run = pyqtSignal()
    changeStep = pyqtSignal(str, str, int, str)
    saveVariable = pyqtSignal(dict)
    copied = pyqtSignal("PyQt_PyObject")

    worker_id = ''

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    CASE_SAVE_PATH = os.path.join(SAVE_PATH, 'test_file', 'case')

    def __init__(self, suites=None, parent=None):
        super(CaseWidget, self).__init__(parent)
        self.setupUi(self)

        self.suitesWidget = parent
        self.suites = suites
        self.case_running = False
        self.selected_case = self.suites.selectedCase()
        self.caseWorker = None
        self.loadUiInit()
        self.setEvent()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == 'selected_case':
            if not value:
                self.suites.selectedCaseId = ''

            self.selected.emit(value)
            self.setComponent()


    def loadUiInit(self):
        # Test Case Treeview Column Hide
        self.tw_testCase.hideColumn(1)  # Case ID
        self.tw_testCase.hideColumn(2)  # Category ID
        self.tw_testCase.setColumnWidth(0, 380)  # Case Nm 컬럼 폭 강제 조절
        self.tw_testCase.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tw_testCase.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tw_testCase.header().setStretchLastSection(False)

        case_tool_bar = QToolBar()
        #case_tool_bar.addAction(self.action_addCategory)
        #case_tool_bar.addAction(self.action_removeCategory)
        #case_tool_bar.addSeparator()
        case_tool_bar.addAction(self.action_addTestCase)
        #case_tool_bar.addAction(self.action_openTestCase)
        case_tool_bar.addAction(self.action_removeCase)
        case_tool_bar.addSeparator()
        case_tool_bar.addAction(self.action_playCase)
        case_tool_bar.addSeparator()
        case_tool_bar.addAction(self.action_startSwing)


        case_tool_bar.addSeparator()
        lbl_capture_type = QLabel('Capture Type')
        lbl_capture_type.setStyleSheet("background-color: rgba(0,0,0,0%)")
        self.cb_capture_type = QComboBox()
        self.cb_capture_type.addItem(QIcon(':/case/' + 'tr_test.png'), 'TR')
        self.cb_capture_type.addItem(QIcon(':/case/' + 'ui_test.png'), 'UI')

        #btn_capture.setText('Capture')
        #btn_capture.setPopupMode(QToolButton.MenuButtonPopup)
        #btn_capture.setMenu(self.pop_file_menu())

        case_tool_bar.addWidget(lbl_capture_type)
        case_tool_bar.addWidget(self.cb_capture_type)

        self.tool_bar_layout.addWidget(case_tool_bar)
        case_tool_bar.addAction(self.action_capture)

        # 모든 QToolButton을 투명하게 변경
        #action_list = self.findChildren(QToolButton)

        #for item in action_list:
        #    item.setStyleSheet("background-color: rgba(0,0,0,0%)")
        
        self.setTestCaseView()

    def pop_file_menu(self):
        aMenu = QMenu(self)
        aMenu.addAction(self.action_capture)
        aMenu.addAction(self.action_capture)
        return aMenu

    def setEvent(self):
        # ToolBar 버튼 이벤트
        self.action_addCategory.triggered.connect(self.addCategoryClicked)                  # 메뉴 - Add Category
        self.action_categorySetting.triggered.connect(self.categorySettingClicked)          # 메뉴 - Category Setting
        self.action_addTestCase.triggered.connect(self.addTestCaseClicked)                  # 메뉴 - Add Test Case
        self.action_openTestCase.triggered.connect(self.openTestCaseClicked)                # 메뉴 - Open Test Case
        self.action_saveTestCase.triggered.connect(self.saveTestCaseClicked)                # 메뉴 - Save Test Case
        self.action_copyTestCase.triggered.connect(self.copyTestCaseClicked)                # 메뉴 - Copy Test Case
        self.action_pasteTestCase.triggered.connect(self.pasteTestCaseClicked)              # 메뉴 - Paste Test Case
        self.action_removeCase.triggered.connect(self.removeTestCaseClicked)                # 메뉴 - Remove Test Case
        self.action_scheduleCase.triggered.connect(self.scheduleCaseClicked)                # 메뉴 - Schedule Test Case
        self.action_resetRowInfo.triggered.connect(self.resetRowInfoClicked)                # 메뉴 - Reset Row Info
        self.action_autoVariable.triggered.connect(self.autoVariableClicked)                # 메뉴 - Auto Variable
        self.action_variableList.triggered.connect(self.variableListClicked)                # 메뉴 - Variable List
        self.action_saveVariableList.triggered.connect(self.saveVariableClicked)            # 메뉴 - Save Variable
        self.action_loadVariableList.triggered.connect(self.loadVariableClicked)            # 메뉴 - Load Variable
        self.action_playCase.triggered.connect(partial(self.playCaseClicked, 0))            # 메뉴 - Play Test Case
        self.action_markingDataView.triggered.connect(self.markingDataView)                 # 메뉴 - Marking Data View
        self.action_clearMarkingData.triggered.connect(self.clearMarkingData)               # 메뉴 - Clear Marking Data
        self.action_getTransactionNm.triggered.connect(self.getTransactionNm)               # 메뉴 - Transaction명 가져오기

        self.action_startSwing.triggered.connect(self.startSwingClicked)                    # 메뉴 - Swing Browser 시작
        self.action_capture.triggered.connect(self.captureClicked)                          # 메뉴 - capture

        # Tree 이벤트
        self.tw_testCase.customContextMenuRequested.connect(self.setTestCaseContextMenu)

        self.tw_testCase.itemSelectionChanged.connect(self.twTestCaseItemSelectionChanged)  # Test Case Item Selection Changed 이벤트
        self.tw_testCase.itemClicked.connect(self.twTestCaseItemClicked)                    # Test Case Item Clicked 이벤트
        self.tw_testCase.itemDoubleClicked.connect(self.twTestCaseItemDoubleClicked)        # Test Case Item Double Clicked 이벤트
        self.tw_testCase.itemExpanded.connect(self.twTestCaseItemExpanded)                  # Test Case Item Expanded 이벤트
        self.tw_testCase.itemCollapsed.connect(self.twTestCaseItemCollapsed)                # Test Case Item Collapse 이벤트

        # Tree Drop 이벤트
        self.tw_testCase.dropEvent = self._twCaseDroped                                     # Test Case Row Drop

        # Button Click 이벤트
        self.btn_expandAll.clicked.connect(self.btnExpandAll)                               # expand All 버튼 클릭 이벤트
        self.btn_collapseAll.clicked.connect(self.btnCollapseAll)                           # collapse All 버튼 클릭 이벤트


    def setComponent(self):

        if self.case_running:
            self.action_addTestCase.setEnabled(False)
            self.action_removeCase.setEnabled(False)
            self.action_startSwing.setEnabled(False)
            self.action_capture.setEnabled(False)
            self.action_playCase.setChecked(True)

            self.tw_testCase.setEnabled(False)
        else:
            self.action_addTestCase.setEnabled(True)
            self.action_startSwing.setEnabled(True)
            self.tw_testCase.setEnabled(True)
            self.action_playCase.setChecked(False)

            if self.selected_case is None:
                isCase = False
            else:
                isCase = True

            self.action_removeCase.setEnabled(isCase)
            self.action_playCase.setEnabled(isCase)
            self.action_capture.setEnabled(isCase)


    def findSelectedCase(self):
        selectedNode = None

        selectedItems = self.tw_testCase.selectedItems()

        if len(selectedItems) > 1:
            self.selected_case = self.suites.findCase('')
        else:
            for item in selectedItems:
                parentNode = item.parent()
                selectedNode = item

            if selectedNode is not None:
                caseId = selectedNode.text(1)
                self.selected_case = self.suites.findCase(caseId)
            else:
                self.selected_case = None


    def _twCaseDroped(self, event):
        '''
        Test Case List Drop event
            - Case의 Category를 변경
        :param event:
        :return:
        '''
        selectedItems = self.tw_testCase.selectedItems()
        to_category_item = self.tw_testCase.itemAt(event.pos().x(), event.pos().y())

        if to_category_item:
            to_category_id = to_category_item.text(2)
            to_category_name = to_category_item.text(0)

            if to_category_id:
                for from_case_item in selectedItems:
                    from_case_id = from_case_item.text(1)

                    if from_case_id:
                        case = self.suites.findCase(from_case_id, selected=False)
                        case.setCategory(to_category_id)
                    else:
                        from_category_id = from_case_item.text(2)
                        from_category_info = self.suites.findCategory(from_category_id, pop=True)
                        from_category_info['parent_category_id'] = to_category_id
                        self.suites.category.append(from_category_info)
        else:
            for from_case_item in selectedItems:
                from_category_id = from_case_item.text(2)

                if from_category_id:
                    from_category_id = from_case_item.text(2)
                    from_category_info = self.suites.findCategory(from_category_id)
                    from_category_info['parent_category_id'] = ''

        self.setTestCaseView()


    # ============================ Context ============================
    def setTestCaseContextMenu(self, pos):
        index = self.tw_testCase.indexAt(pos)

        menu = QMenu()
        menu.setMinimumSize(QSize(350, 0))

        copy_case_list = self.suitesWidget.getCopyCaseList()

        if not index.isValid():
            self.tw_testCase.clearSelection()

        if not index.isValid():
            if pos:
                menu.addAction(self.action_addCategory)
                menu.addSeparator()
                menu.addAction(self.action_addTestCase)
                menu.addSeparator()
                menu.addAction(self.action_openTestCase)
                if copy_case_list:
                    menu.addAction(self.action_pasteTestCase)
                menu.addAction(self.action_closeAllTestCase)
                menu.addSeparator()
                menu.exec_(self.tw_testCase.mapToGlobal(pos))
        elif self.selected_case is None:
            menu.addAction(self.action_addCategory)
            menu.addAction(self.action_categorySetting)
            menu.addSeparator()
            menu.addAction(self.action_addTestCase)
            menu.addSeparator()
            menu.addAction(self.action_openTestCase)
            if copy_case_list:
                menu.addAction(self.action_pasteTestCase)
            menu.addAction(self.action_closeAllTestCase)
            menu.addSeparator()
            menu.exec_(self.tw_testCase.mapToGlobal(pos))
        else:
            if pos:
                menu.addAction(self.action_playCase)
                menu.addAction(self.action_scheduleCase)
                menu.addSeparator()
                menu.addAction(self.action_addTestCase)
                menu.addSeparator()
                menu.addAction(self.action_saveTestCase)
                menu.addAction(self.action_openTestCase)
                menu.addAction(self.action_copyTestCase)
                if copy_case_list:
                    menu.addAction(self.action_pasteTestCase)
                menu.addAction(self.action_closeAllTestCase)
                menu.addSeparator()
                menu.addAction(self.action_removeCase)
                #menu.addAction(self.action_resetRowInfo)
                menu.addSeparator()
                menu.addAction(self.action_autoVariable)
                menu.addAction(self.action_variableList)
                menu.addAction(self.action_saveVariableList)
                menu.addAction(self.action_loadVariableList)
                menu.addSeparator()
                menu.addAction(self.action_markingDataView)
                menu.addAction(self.action_clearMarkingData)
                #menu.addAction(self.action_getTransactionNm)
                menu.exec_(self.tw_testCase.mapToGlobal(pos))

    # ============================ Action Event ============================
    def addCategoryClicked(self):
        category, ok = QInputDialog.getText(self, 'Category 추가', 'Category 명을 입력하세요.')

        if ok and category:
            parent_category_id = ''
            selectedNode = None

            for item in self.tw_testCase.selectedItems():
                parentNode = item.parent()
                selectedNode = item

            if selectedNode is not None:
                parent_category_id = selectedNode.text(2)

            find_category = self.suites.findCategory(category, parent_category_id)

            if find_category:
                QMessageBox.information(self, "Category 추가", "동일한 Category가 존재합니다.")

                return False
            else:
                categoryInfo = self.suites.addCategory(category, parent_category_id)

                if parent_category_id:
                    parent_node = self.tw_testCase.findItems(categoryInfo['parent_category_id'], Qt.MatchExactly | Qt.MatchRecursive, column=2)[0]
                    child_node = addTreeChild(parent=parent_node, text=categoryInfo['category_name'], check=True)
                    child_node.setText(2, categoryInfo['category_id'])
                    child_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                    child_node.setForeground(0, Qt.cyan)
                    child_node.setFont(0, QFont('맑은 고딕'))
                else:
                    root_node = addTreeRoot(treeWidget=self.tw_testCase, idx=0, text=categoryInfo['category_name'], check=True)
                    root_node.setText(2, categoryInfo['category_id'])
                    root_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                    root_node.setForeground(0, Qt.cyan)
                    root_node.setFont(0, QFont('맑은 고딕'))

                QMessageBox.information(self, "Category 추가", "[{}] Category를 추가하였습니다.".format(categoryInfo['category_name']))

                return categoryInfo
        else:
            return False


    def categorySettingClicked(self):
        item = self.tw_testCase.currentItem()

        category_name = item.text(0)
        category_id = item.text(2)
        new_category_name, ok = QInputDialog.getText(self, 'Category 수정', 'Category 명을 입력하세요.', text=category_name)

        if ok and new_category_name:
            item.setText(0, new_category_name)
            find_category = self.suites.findCategory(category_id)
            find_category['category_name'] = new_category_name


    def addTestCaseClicked(self):
        item = self.tw_testCase.currentItem()

        if item:
            category_id = item.text(2)

            if category_id:
                category_name = item.text(0)

                caseDialog = CaseDialog(call_gubun='New', category_id=category_id, category_name=category_name, suites=self.suites)
                caseDialog.added.connect(self.addCase)
                caseDialog.popUp()
            else:
                case_id = item.text(1)

                if case_id:
                    category_id = item.parent().text(2)
                    category_name = item.parent().text(0)

                    caseDialog = CaseDialog(call_gubun='New', category_id=category_id, category_name=category_name, suites=self.suites)
                    caseDialog.added.connect(self.addCase)
                    caseDialog.popUp()
                else:
                    QMessageBox.information(self, "New Test Case", "Category 선택 후 Case 추가하세요.")
        else:
            caseDialog = CaseDialog(call_gubun='New', suites=self.suites)
            caseDialog.added.connect(self.addCase)
            caseDialog.popUp()


    def openTestCaseClicked(self):
        fd = QFileDialog(self)
        filename = fd.getOpenFileName(self, '%s - Choose Case File' % __appname__, self.CASE_SAVE_PATH,'Case Files(*.atc)')
        filePath = filename[0]

        if filePath:
            with open(filePath, 'rb') as f:
                case = pickle.load(f)

            self.suites.setCaseList(case)
            self.setTestCaseView()
            self.setFocusTestCase(case.caseId)


    def saveTestCaseClicked(self):
        fd = QFileDialog(self)
        filename = fd.getSaveFileName(self, '%s - Save Case File' % __appname__, self.CASE_SAVE_PATH,'List Files(*.atc)')
        filePath = filename[0]

        if filePath:
            with open(filePath, 'wb') as f:
                pickle.dump(self.selected_case, f, pickle.HIGHEST_PROTOCOL)
                QMessageBox.information(self, "Save Case File", "Save Complete")


    def copyTestCaseClicked(self):
        '''
        case 복사
            - main 화면으로 (list)[(class) case]를 보냄
        :return: None
        '''
        #print(self.getCheckedCase())
        checked_case_list = self.getCheckedCase()

        if checked_case_list:
            self.copied.emit(checked_case_list)
        else:
            self.copied.emit([self.selected_case])
        QMessageBox.information(self, "Copy Case", "Copy Complete")


    def pasteTestCaseClicked(self):
        copy_case_list = self.suitesWidget.getCopyCaseList()
        if copy_case_list:
            reply = QMessageBox.question(self, "Paste Case", "[{}] 건의 Case를 추가하시겠습니까?".format(len(copy_case_list)), QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                for case in copy_case_list:
                    # 재귀호출로 인해 deepcopy -> pickle로 변경
                    #copied_case = copy.deepcopy(case)
                    copied_case = pickle.loads(pickle.dumps(case, -1))
                    copied_case.initStatus()
                    self.suites.setCaseList(copied_case)

                self.setTestCaseView()
                self.setFocusTestCase(copied_case.caseId)
                self.suitesWidget.removeCopyCaseList()


    def removeTestCaseClicked(self):
        reply = QMessageBox.question(self, "Remove Case", "Case를 삭제하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            case = self.selected_case
            self.suites.removeCase(case)
            self.setTestCaseView()
            #self.setFocusTestCase(case.caseId)
            QMessageBox.information(self, "Remove Case", "Complete")


    def scheduleCaseClicked(self):
        self.suitesWidget.addSchedule()


    def resetRowInfoClicked(self):
        reply = QMessageBox.question(self, "Reset Row Info", "Row Info를 재설정 하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            case = self.selected_case
            self.selected_case.resetStepRowInfo()
            self.setTestCaseView()
            self.setFocusTestCase(case.caseId)
            QMessageBox.information(self, "Reset Row Info", "Complete")


    def autoVariableClicked(self):
        autoVariableDialog = AutoVariableDialog()
        autoVariableDialog.applied.connect(self.variableListChanged)
        autoVariableDialog.doubleClicked.connect(self.moveToStep)
        autoVariableDialog.popUp(self.selected_case)


    def variableListClicked(self):
        variableListDialog = VariableListDialog(self.selected_case)
        variableListDialog.declared.connect(self.variableListDeclared)
        variableListDialog.saved.connect(self.variableListChanged)
        variableListDialog.removed.connect(self.variableListChanged)
        variableListDialog.doubleClicked.connect(self.moveToStep)
        variableListDialog.refListClicked.connect(self.moveToStep)
        variableListDialog.popUp()


    def saveVariableClicked(self):
        variables = self.selected_case.getVariables()

        if len(variables) > 0:
            for variable_id in variables:
                variable = variables[variable_id]
                variable['ref_target_list'] = self.selected_case.getStepRowsByRef(key='ref_target', variable_id=variable_id)
                variable['ref_option_list'] = self.selected_case.getStepRowsByRef(key='ref_option', variable_id=variable_id)

            self.saveVariable.emit(variables)
        else:
            QMessageBox.information(self, "Save Variable", "저장 가능한 변수가 없습니다.")

    def loadVariableClicked(self):
        variableListDialog = VariableListDialog(self.selected_case)
        variableListDialog.loadApplied.connect(self.variableLoadApplied)
        variableListDialog.varObjListClicked.connect(self.moveToStep)
        variableListDialog.popUp(open_type='load')


    def variableListDeclared(self):
        self.suitesWidget.setCaseInputValueView(self.selected_case)

    def variableListChanged(self):
        self.selected.emit(self.selected_case)


    def variableLoadApplied(self):
        self.varLoadApplied.emit()


    def markingDataView(self):
        markingDataDialog = MarkingDataDialog()
        markingDataDialog.loadData(self.selected_case)
        markingDataDialog.popUp()


    def moveToStep(self, step_id, data_list_id, row_index, column_id):
        self.changeStep.emit(step_id, data_list_id, row_index, column_id)


    def clearMarkingData(self):
        reply = QMessageBox.question(self, 'Clear Marking Data', "Test Data정보를 삭제하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.selected_case.clearMarkingData()


    def getTransactionNm(self):
        '''
        Transaction명 현행화
        :return: None
        '''
        reply = QMessageBox.question(self, 'Transaction명 현행화', "Transaction명을 갱신 하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            items = ("Suites 전체", "Case 전체")
            get_transaction_type, ok = QInputDialog.getItem(self, 'Transaction명 현행화', '현행화 대상을 선택하세요.', items, 0, False)

            if ok and get_transaction_type:
                if get_transaction_type == 'Case 전체':
                    self.selected_case.resetTransactionNm()
                else:
                    for case in self.suites.caseList:
                        case.resetTransactionNm()
            self.suitesWidget.step_widget.setStepView()
            QMessageBox.information(self, "Transaction명 현행화", "완료 되었습니다.")


    def startSwingClicked(self):
        self.suitesWidget.mainWidget.startSwingClicked()


    def captureClicked(self):
        if self.suitesWidget.mainWidget.web:
            self.suitesWidget.mainWidget.action_capture.trigger()
        else:
            self.action_capture.setChecked(False)


    def addCase(self, case):
        if case:
            self.suites.setCaseList(case)

            #Test Case Treeview Setting
            self.setTestCaseView()

            # Test Case Focus
            self.setFocusTestCase(case_id=case.caseId)


    def playCaseClicked(self, index=0):
        '''
        case 수행 클릭 이벤트
            - action_playCase checked 이벤트가 발생되고 호출
            - action_playCase 버튼이 체크가 된 상태라면 case 수행
            - action_playCase 버튼이 체크해제가 된 상태라면 case 수행 정지
        :param index: (int) 0
        :return: None
        '''
        if self.action_playCase.isChecked():
            self.selected_case.initStepStatus()                         # Step 상태 초기화
            self.setCaseDtlStatusInit(self.selected_case.getCaseId())   # Case 상태 초기화

            self.case_running = True
            self.setComponent()

            self.run.emit()

            self.caseWorker = CaseThread(self.suites, self.selected_case, index, self.worker_id, self.suitesWidget.mainWidget)
            self.caseWorker.send_start_step_signal.connect(self.getCaseStepStartSignal)
            self.caseWorker.send_end_step_signal.connect(self.getCaseStepEndSignal)
            self.caseWorker.send_start_get_variable.connect(self.getCaseVariableStart)
            self.caseWorker.send_end_get_variable.connect(self.getCaseVariableEnd)
            self.caseWorker.send_get_variable_signal.connect(self.getCaseVariableValue)
            self.caseWorker.finished.connect(self.caseWorkerFinished)
            self.caseWorker.terminated.connect(self.caseWorkerTerminated)
            self.caseWorker.start()

            self.splash = ProgressSplash()
            self.splash.setCaseProgressText(self.selected_case.getCaseNm())
            #self.splash.setCaseCnt(1, 1)
            self.splash.popup()
        else:
            self.action_playCase.setChecked(True)
            self.stopCaseWorker()

    # ============================ QThread Temp ============================
    def stopCaseWorker(self):
        if self.caseWorker:
            self.caseWorker.stop()


    def getCaseVariableStart(self):
        '''
        참조데이타 조회 시작 시 이벤트
            - Step Progressbar 활성화 시작
        :return: None
        '''
        text = '참조 데이타 조회...'
        self.splash.startStepProgress(text)


    def getCaseVariableEnd(self):
        '''
        참조데이타 조회 종료 시 이벤트
            - Step Progressbar 활성화 종료
        :return: None
        '''
        self.splash.endStepProgress()


    def getCaseVariableValue(self, variable_nm):
        '''
        참조데이타 조회 건별 시작 시 이벤트
        :param variable_nm: (str) '5G 단말기'
        :return: None
        '''
        text = '참조 데이타 조회 [{target}] ...'.format(target=variable_nm)
        self.splash.startStepProgress(text)


    def getCaseStepStartSignal(self, step):
        '''
        Step 시작 시 이벤트
        :param per:
        :param case:
        :param step:
        :return:
        '''
        target = step.get('target')
        desc = step.get('description')

        if desc:
            text = desc
        elif target:
            text = target
        else:
            text = '--'

        text = 'Request [{text}] ...'.format(text=text)
        self.splash.setStepProgressText(text)


    def getCaseStepEndSignal(self, per, case, step, idx):
        '''
        Step 종료 시 이벤트
        :param step: (class) step
        :param idx: (int) 3
        :return: None
        '''
        self.stepFinished.emit(step, idx)
        self.splash.setStepProgressPer(per)
        self.setCaseDtlProgressbar(case, per)


    def caseWorkerFinished(self):
        '''
        Case Thred 종료 시 이벤트
        :return: None
        '''
        self.splash.setCaseProgressPer(100, 'Case 수행완료')
        self.splash.close()

        self.setCaseProgressbarVisible(self.selected_case, visibled=False)

        self.case_running = False
        self.setComponent()

        # 정상적으로 종료된 경우만 Alert
        #print(self.caseWorker.getError())

        if self.caseWorker.kill:
            self.selected_case.setMarkingDataResult(self.caseWorker.worker_id, 999, "중지되었습니다.")
            self.caseFinished.emit()
            QMessageBox.information(self, "Stop", "중지되었습니다.")
        elif not self.caseWorker.getError():
            self.worker_id = ''
            self.selected_case.setMarkingDataResult(self.caseWorker.worker_id, 0, "Successful")
            self.selected_case.setRefExcelUsed()
            self.selected_case.setStatus(0)
            self.setStatus(self.selected_case)
            self.caseFinished.emit()
            QMessageBox.information(self, "Successful", "Play Case Successful")
        else:
            pass


    def caseWorkerTerminated(self, worker_id, msg):
        '''
        Case Thread 비정상종료 시 이벤트
        :param worker_id: (str) 'acbef741-ce9e-4e4e-883b-aff5e9bfef31'
        :param msg: (str) '에러발생'
        :return: None
        '''
        self.splash.close()
        self.tw_testCase.setEnabled(True)

        # 비정상 종료 후 재수행 시 사용하기 위함
        self.worker_id = worker_id

        # 비정상 종료 시 메시지 Setting
        self.selected_case.setMarkingDataResult(worker_id, 1, msg)
        self.setStatus(self.selected_case)
        self.caseFinished.emit()
        QMessageBox.information(self, "Abnormally terminated", "비정상종료 되었습니다.\n[{}]".format(msg))


    # ============================ Component Event Setting ============================
    def twTestCaseItemClicked(self, item):
        checkCnt = 0

        for item in self.tw_testCase.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            if item.text(1) == '':
                pass
            else:
                if item.checkState(0) == Qt.Checked:
                    checkCnt += 1


    def twTestCaseItemSelectionChanged(self):
        self.findSelectedCase()


    def twTestCaseItemDoubleClicked(self, item, index):
        if self.selected_case is not None:
            caseDialog = CaseDialog(call_gubun='Change', case=self.selected_case, suites=self.suites)
            caseDialog.changed.connect(self.testCaseChanged)
            caseDialog.popUp()


    def twTestCaseItemExpanded(self, item):
        case_category_info = self.suites.findCategory(item.text(2))
        case_category_info['expanded'] = item.isExpanded()


    def twTestCaseItemCollapsed(self, item):
        case_category_info = self.suites.findCategory(item.text(2))
        case_category_info['expanded'] = item.isExpanded()


    def testCaseChanged(self, case):
        self.setTestCaseView()
        self.setFocusTestCase(case_id=case.caseId)
        QMessageBox.information(self, "Successful", "Case Change Successful")


    def btnExpandAll(self):
        self.tw_testCase.expandAll()


    def btnCollapseAll(self):
        self.tw_testCase.collapseAll()


    # ============================ UI Setting ============================
    def setTestCaseView(self):
        '''
        Case Tree Widget View Setting
        :return: None
        '''
        # Component 초기화
        self.tw_testCase.clear()

        '''
        # category 구버전을 위한 로직
        old_category_cases = list(case for case in self.suites.caseList if type(case.category) == str)

        for idx, case in enumerate(old_category_cases):
            case_category_info = self.suites.findCategory(case.category)

            if case_category_info:
                pass
            else:
                case_category_info = self.suites.addCategory(case.category)

            case.setCategory(case_category_info['category_id'])
        '''

        category = self.suites.getCategory(copy=True)

        new_category_list = []

        if category:
            category_font = QFont('맑은 고딕', 10)
            category_font.setBold(True)

            while True:
                '''
                category 리스트 순서상 Parent category보다 앞에 있는 경우 오류가 발생하여
                exception 발생 시 리스트의 뒤로 보내고 수행함
                category Tree 구성 후 category 새로운 리스트(순서변경됨)로 suites에 저장
                '''
                categoryInfo = category.pop(0)
                try:
                    if categoryInfo['parent_category_id']:
                        parent_node = self.tw_testCase.findItems(categoryInfo['parent_category_id'], Qt.MatchExactly | Qt.MatchRecursive, column=2)[0]
                        child_node = addTreeChild(parent=parent_node, text=categoryInfo['category_name'], check=True)
                        child_node.setText(2, categoryInfo['category_id'])
                        child_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                        child_node.setForeground(0, Qt.cyan)
                        child_node.setFont(0, category_font)

                        expanded = self.suites.getCategoryInfo(categoryInfo['category_id'], 'expanded', False)
                        child_node.setExpanded(expanded)
                    else:
                        root_node = addTreeRoot(treeWidget=self.tw_testCase, idx=0, text=categoryInfo['category_name'], check=True)
                        root_node.setText(2, categoryInfo['category_id'])
                        root_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                        root_node.setForeground(0, Qt.cyan)
                        root_node.setFont(0, category_font)

                        expanded = self.suites.getCategoryInfo(categoryInfo['category_id'], 'expanded', False)
                        root_node.setExpanded(expanded)
                    new_category_list.append(categoryInfo)
                except IndexError:
                    category.append(categoryInfo)

                if not category:
                    break

            self.suites.category = new_category_list

        for case in self.suites.caseList:
            '''
            caseDtlWidget = CaseProgressWidget()
            caseDtlWidget.setCaseDtl(case)
            # caseDtlWidget.setValue(100)
            category_node = self.tw_testCase.findItems(case.getCategory(), Qt.MatchExactly | Qt.MatchRecursive, column=2)[0]

            myQTreeWidgetItem = QTreeWidgetItem(category_node)
            myQTreeWidgetItem.setFlags(myQTreeWidgetItem.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            myQTreeWidgetItem.setText(1, case.caseId)
            myQTreeWidgetItem.setCheckState(0, Qt.Unchecked)

            self.tw_testCase.setItemWidget(myQTreeWidgetItem, 0, caseDtlWidget)
            '''

            category_node = self.tw_testCase.findItems(case.getCategory(), Qt.MatchExactly | Qt.MatchRecursive,column=2)[0]
            child_node = addTreeChild(parent=category_node, text=case.caseNm, check=True)
            child_node.setText(1, case.caseId)

            if case.caseType == 'UI':
                case_type_pixmap = QPixmap(':/case/ui_test.png')

            else:
                case_type_pixmap = QPixmap(':/case/tr_test.png')

            labelWidget = QLabel()
            labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
            labelWidget.setPixmap(case_type_pixmap)
            labelWidget.setScaledContents(True)
            labelWidget.setMaximumSize(QSize(20, 20))
            labelWidget.setAlignment(Qt.AlignCenter)
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(labelWidget)
            layout.setContentsMargins(0, 0, 0, 0)
            self.tw_testCase.setItemWidget(child_node, 2, cell_widget)

            code = case.getStatus()

            if code > 0:
                child_node.setIcon(0, QIcon(':/step/' + 'error.png'))
            elif code < 0:
                child_node.icon(0)
            else:
                child_node.setIcon(0, QIcon(':/step/' + 'correct.png'))


        #self.tw_testCase.expandAll()
        # self.tw_testCase.setCurrentItem(self.tw_testCase.topLevelItem(0))


    def setFocusTestCase(self, case_id):
        '''
        Input으로 받은 case id 에 해당하는 Tree node로 Focus를 이동함
        :param case_id: (str) 'acbef741-ce9e-4e4e-883b-aff5e9bfef31'
        :return: None
        '''
        if case_id:
            if self.selected_case is None:
                self.selected_case = self.suites.findCase(case_id)

            selectTreeItem = self.tw_testCase.findItems(case_id, Qt.MatchExactly | Qt.MatchRecursive, column=1)
            self.tw_testCase.setCurrentItem(selectTreeItem[0])


    def setSelectedTestCase(self, case_id, select=True):
        '''
        Input으로 받은 case id 에 해당하는 Tree node로 Focus를 이동함
        :param case_id: (str) 'acbef741-ce9e-4e4e-883b-aff5e9bfef31'
        :return: None
        '''
        if case_id:
            if self.selected_case is None:
                self.selected_case = self.suites.findCase(case_id)

            selectTreeItem = self.tw_testCase.findItems(case_id, Qt.MatchExactly | Qt.MatchRecursive, column=1)
            selectTreeItem[0].setSelected(select)


    def setStatus(self, case=None, init=False):
        '''
        Case의 상태를 변경
            - Input으로 받은 case의 상태로 UI 수행결과 icon을 변경함
            - 초기화의 경우 모두 icon을 삭제함
        :param case: (class) case
        :param init: (bool) True
        :return: None
        '''
        if init:
            for item in self.tw_testCase.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                if item.text(1) == '':
                    pass
                else:
                    item.setIcon(0, QIcon(''))
        else:
            selectTreeItem = self.tw_testCase.findItems(case.getCaseId(), Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]

            code = case.getStatus()

            if code > 0:
                selectTreeItem.setIcon(0, QIcon(':/step/' + 'error.png'))
            elif code < 0:
                selectTreeItem.setIcon(0, QIcon(''))
            else:
                selectTreeItem.setIcon(0, QIcon(':/step/' + 'correct.png'))


    def setChecked(self, checked=True):
        '''
        Case Tree Widget Checkbox를 변경
            - Suites 단위로 수행 전 모든 Case를 Check함
        :param checked: (bool) True
        :return: (bool) True
        '''
        for item in self.tw_testCase.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            if item.text(1) == '':
                pass
            else:
                if checked:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)

        return checked


    def getCheckedCase(self):
        '''
        Case Tree Widget에 Check된 case를 List 형태로 Return
        :return: (list) [(class) case1, (class) case2, ...]
        '''
        checked_case_list = []

        for item in self.tw_testCase.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            if item.text(1) == '':
                pass
            else:
                if item.checkState(0) == Qt.Checked:
                    case = self.suites.findCase(item.text(1))
                    checked_case_list.append(case)

        return checked_case_list


    def getCurrentCase(self):
        '''
        현재 case tree widget에 선택된 case를 Return
        :return: (class) case
        '''
        case = None
        item = self.tw_testCase.currentItem()

        if item.text(1) == '':
            pass
        else:
            case = self.suites.findCase(item.text(1))

        return case


    def setCaseDtlStatusInit(self, case_id):
        '''
        Case Dtl Widget 수행결과를 초기화
        :param case_id: (str) 'acbef741-ce9e-4e4e-883b-aff5e9bfef31'
        :return: None
        '''
        # selectTreeItem = self.tw_testCase.findItems(case_id, Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]
        # caseDtlWidget = self.tw_testCase.itemWidget(selectTreeItem, 0)
        # caseDtlWidget.initStatus()
        caseItem = self.tw_testCase.findItems(case_id, Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]
        caseItem.setIcon(0, QIcon(''))
        pass


    def setCaseDtlProgressbar(self, case, per):
        '''
        Case Dtl Widget에 진행상태를 표기하기 위함
        :param case_id: (str) 'acbef741-ce9e-4e4e-883b-aff5e9bfef31'
        :param per: (int) 25
        :return: None
        '''
        caseDtlWidget = self.setCaseProgressbarVisible(case, visibled=True)
        caseDtlWidget.setValue(per)


    def setCaseProgressbarVisible(self, case, visibled):
        '''
        Case Progressbar 활성화
        :param case: (class) case
        :param visibled: (bool) True
        :return: (widget) caseDtlWidget
        '''
        caseItem = self.tw_testCase.findItems(case.getCaseId(), Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]
        caseDtlWidget = self.tw_testCase.itemWidget(caseItem, 0)

        if visibled:
            if caseDtlWidget is None:
                caseItem.setText(0, '')
                caseDtlWidget = CaseProgressWidget()
                caseDtlWidget.setCaseDtl(case)
                self.tw_testCase.setItemWidget(caseItem, 0, caseDtlWidget)
            else:
                pass

            return caseDtlWidget
        else:
            caseItem.setText(0, case.getCaseNm())
            self.tw_testCase.removeItemWidget(caseItem, 0)

            return None






