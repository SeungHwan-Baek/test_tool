# -*- coding: utf-8 -*-
import os, sys
import pickle
from datetime import datetime

# 현재 모듈의 절대경로를 알아내서 상위 폴더 절대경로를 참조 path에 추가
#parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
#currentDir = os.path.dirname(os.path.realpath(__file__))
#sys.path.append(currentDir)

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from libs.suites import Suites
from utils.settings import Settings
from utils.config import Config
from widgets.suitesWidget import SuitesWidget
from widgets.statusWidget import StatusWidget
from dialogs.excludedTrSettingDialog import ExcludedTrDialog
from dialogs.refDataDialog import RefDataDialog
from dialogs.eventListDialog import EventListDialog
from dialogs.sqlEditorDialog import SqlEditorDialog
from dialogs.recordDialog import RecordDialog
from utils.webBrowser import WebBrowser
from PyQt5 import uic

from widgets.mainSplash import ProgressSplash
from dialogs.addStepDialog import AddStepDialog

from utils.eventWorker import EventThread

from libs.version import __version__

from pyqtkeybind import keybinder

import pandas as pd

import qdarkstyle

__appname__ = 'ReST Studio'

form_class = uic.loadUiType("UI/auto_test_main.ui")[0]
#sys.path.append(os.path.realpath("instantclient_12_2"))
#os.environ['path'] = os.environ['path'] + os.pathsep + os.path.realpath("instantclient_12_2")

config = Config()
CRACH_PROGRAM_LIST = config.getlist("section_common", "CRACH_PROGRAM_LIST")
RECENT_SUITES_HISTORY_CNT = config.getInt("section_common", "RECENT_SUITES_HISTORY_CNT")

class MainWindow(QMainWindow, form_class):
    cond = QWaitCondition()
    mutex = QMutex()

    web = None

    tab_seq = 1

    change_crach_program = {}
    recent_suites_list = []

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    SUITES_SAVE_PATH = os.path.join(SAVE_PATH, 'test_file', 'suites')
    HOME_SAVE_PATH = os.path.join(HOME, '.test_tool')
    TR_INFO_SAVE_PATH = os.path.join(HOME, 'Test_Tool', '.tr_info')
    VARIABLE_SAVE_PATH = os.path.join(SAVE_PATH, 'var')
    MARKING_SAVE_PATH = os.path.join(SAVE_PATH, 'marking')

    def __init__(self):
        super().__init__()
        self.caseRunning = False
        self.suitesRunning = False

        self.copy_case_list = []

        # Load setting in the main thread
        self.settings = Settings(self.HOME_SAVE_PATH)
        self.settings.load()
        self.settings.save()

        self.setupUi(self)
        #print(self.thread())
        self.setWindowTitle("{title} ({version})".format(title=__appname__, version=__version__))

        if not os.path.exists(self.SUITES_SAVE_PATH):
            os.makedirs(self.SUITES_SAVE_PATH)

        if not os.path.exists(self.VARIABLE_SAVE_PATH):
            os.makedirs(self.VARIABLE_SAVE_PATH)

        if not os.path.exists(self.MARKING_SAVE_PATH):
            os.makedirs(self.MARKING_SAVE_PATH)

        self._loadUiInit()
        self._loadSetting()
        self._setEvent()
        self._setRecentSuitesView()


    def _loadUiInit(self):
        '''
        UI 초기화
            - 최초 Load 시 수행
        :return: None
        '''
        self.sqlEditorDialog = SqlEditorDialog()

        self.eventListDialog = EventListDialog()
        self.eventListDialog.requestSelected.connect(self.setStepBySelectedRequest)

        self.recordDialog = RecordDialog()
        self.recordDialog.closed.connect(self.show)
        self.recordDialog.endRecord.connect(self.endRecordSignal)
        
        # 모든 QToolButton을 투명하게 변경
        action_list = self.findChildren(QToolButton)

        for item in action_list:
            item.setStyleSheet("background-color: rgba(0,0,0,0%)")

        self.tw_recentSuitesList.setColumnWidth(0, 200)
        self.tw_recentSuitesList.setColumnWidth(1, 300)
        self.tw_recentSuitesList.hideColumn(3)                                          # file path
    
    
    def _setEvent(self):
        '''
        Component Event Setting
        :return: None
        '''
        # ToolBar 버튼 이벤트
        self.action_openSuites.triggered.connect(self.openSuitesClicked)                # 메뉴 - Open Suites 버튼 클릭
        self.action_newSuites.triggered.connect(self.newSuitesClicked)                  # 메뉴 - New Suites 버튼 클릭
        self.action_saveSuites.triggered.connect(self.saveSuitesClicked)                # 메뉴 - Save Suites
        self.action_openTestCase.triggered.connect(self.openTestCaseClicked)            # 메뉴 - Open Test Case 버튼 클릭
        self.action_addTestCase.triggered.connect(self.addTestCaseClicked)              # 메뉴 - Add Test Case 버튼 클릭
        self.action_playCase.triggered.connect(self.playCaseClicked)                    # 메뉴 - Play Case 버튼 클릭
        self.action_RefData.triggered.connect(self.refDataClicked)                      # 메뉴 - ref Excel 버튼 클릭
        self.action_startSwing.triggered.connect(self.startSwingClicked)                # 메뉴 - Start Swing
        self.action_autoAddTestStep.triggered.connect(self.autoAddTestStepClicked)      # 메뉴 - Auto Add Test Step
        self.action_importTrInfo.triggered.connect(self.importTrInfoClicked)            # 메뉴 - Import Transaction Info
        self.action_excludedTrSetting.triggered.connect(self.excludedSettingClicked)    # 메뉴 - Excluded Transaction Setting
        self.action_excludedTrEnabled.toggled.connect(self.excludedEnableToggled)       # 메뉴 - Excluded Transaction Enabled
        self.action_test.triggered.connect(self.testClicked)                            # 메뉴 - test
        self.action_sqlEditor.triggered.connect(self.sqlEditorClicked)                  # 메뉴 - SQL Editor

        self.action_findData.triggered.connect(self.findDataClicked)                    # 메뉴 - Find Data
        self.action_capture.triggered.connect(self.recordRequest)                       # 메뉴 - Capture Requests
        self.action_clearRequests.triggered.connect(self.clearRequests)                 # 메뉴 - Clear Requests
        self.action_setRequests.triggered.connect(self.setRequests)                     # 메뉴 - Set Requests
        self.action_captureUiEvent.triggered.connect(self.recordUiEvent)                # 메뉴 - Capture UI Event
        self.action_eventList.triggered.connect(self.eventListClicked)                  # 메뉴 - Event List

        self.tab_main.currentChanged.connect(self.setComponent)

        self.btn_newSuites.clicked.connect(self.newSuitesClicked)
        self.btn_openSuites.clicked.connect(self.openSuitesClicked)

        # Close Tab
        self.tab_main.tabCloseRequested.connect(self.removeTab)

        self.tw_recentSuitesList.cellDoubleClicked.connect(self._twRecentSuitesDoubleClicked)


    def _loadSetting(self):
        '''
        설정값으로 재설정
        :return: None
        '''
        size = self.settings.get("SETTING_WIN_SIZE", QSize(1820, 900))
        position = self.settings.get("SETTING_WIN_POSE", False)
        geometry = self.settings.get("SETTING_WIN_GEOMETRY", False)
        self.recent_suites_list = self.settings.get("RECENT_SUITES_LIST", [])

        if size:
            self.resize(size)

        if position:
            #
            #self.move(position)
            pass

        if geometry:
            self.restoreGeometry(geometry)

        self.progressBar = StatusWidget()
        self.progressBar.setRange(0, 100)
        self.statusBar().addPermanentWidget(self.progressBar)


    def _setRecentSuitesView(self):
        '''
        Recent Suites View Setting
        :return: None
        '''
        self.tw_recentSuitesList.clearContents()

        for idx, suites_info in enumerate(reversed(self.recent_suites_list)):
            if os.path.exists(suites_info['file_path']):
                pass
            else:
                self.recent_suites_list.remove(suites_info)

        self.tw_recentSuitesList.setRowCount(len(self.recent_suites_list))

        for idx, suites_info in enumerate(reversed(self.recent_suites_list)):
            self.tw_recentSuitesList.setItem(idx, 0, QTableWidgetItem(suites_info['suites_file']))
            self.tw_recentSuitesList.setItem(idx, 1, QTableWidgetItem(suites_info['suites_nm']))
            self.tw_recentSuitesList.setItem(idx, 2, QTableWidgetItem(suites_info['modified_time']))
            self.tw_recentSuitesList.setItem(idx, 3, QTableWidgetItem(suites_info['file_path']))


    def setComponent(self):
        '''
        화면 Component 설정
        :return: None
        '''
        if self.caseRunning:
            self.action_newSuites.setEnabled(False)
            self.action_openSuites.setEnabled(False)
            self.action_openTestCase.setEnabled(False)
            self.action_addTestCase.setEnabled(False)
            self.action_saveSuites.setEnabled(False)
            self.action_RefData.setEnabled(False)
            self.action_autoAddTestStep.setEnabled(False)
            self.action_excludedTrSetting.setEnabled(False)
            self.action_excludedTrEnabled.setEnabled(False)

            self.action_findData.setEnabled(False)
            self.action_capture.setEnabled(False)
            self.action_captureUiEvent.setEnabled(False)
            self.action_setRequests.setEnabled(False)
            self.action_playCase.setChecked(True)

            self.action_startSwing.setEnabled(False)
            self.action_capture.setEnabled(False)
            self.action_captureUiEvent.setEnabled(False)
            self.action_setRequests.setEnabled(False)
            self.action_clearRequests.setEnabled(False)
            self.action_eventList.setEnabled(False)
            self.action_sqlEditor.setEnabled(False)
        elif self.suitesRunning:
            self.action_newSuites.setEnabled(False)
            self.action_openSuites.setEnabled(False)
            self.action_openTestCase.setEnabled(False)
            self.action_addTestCase.setEnabled(False)
            self.action_saveSuites.setEnabled(False)
            self.action_RefData.setEnabled(False)
            self.action_autoAddTestStep.setEnabled(False)
            self.action_excludedTrSetting.setEnabled(False)
            self.action_excludedTrEnabled.setEnabled(False)

            self.action_findData.setEnabled(False)
            self.action_capture.setEnabled(False)
            self.action_captureUiEvent.setEnabled(False)
            self.action_setRequests.setEnabled(False)
            self.action_playCase.setEnabled(False)

            self.action_startSwing.setEnabled(False)
            self.action_capture.setEnabled(False)
            self.action_captureUiEvent.setEnabled(False)
            self.action_setRequests.setEnabled(False)
            self.action_clearRequests.setEnabled(False)
            self.action_eventList.setEnabled(False)
            self.action_sqlEditor.setEnabled(False)
        else:
            self.action_newSuites.setEnabled(True)
            self.action_openSuites.setEnabled(True)

            self.action_startSwing.setEnabled(True)
            self.action_capture.setEnabled(True)
            self.action_setRequests.setEnabled(True)
            self.action_clearRequests.setEnabled(True)
            self.action_captureUiEvent.setEnabled(True)
            self.action_eventList.setEnabled(True)
            self.action_sqlEditor.setEnabled(True)

            self.action_playCase.setChecked(False)
            index = self.tab_main.currentIndex()
            suites = self.tab_main.currentWidget()

            if type(suites) == QWidget:
                isSuites = False
                isCase = False
            else:
                if suites:
                    case = suites.selected_case

                    if index < 0:
                        isSuites = False
                    else:
                        isSuites = True

                    if case is None:
                        isCase = False
                    else:
                        isCase = True
                else:
                    isSuites = False
                    isCase = False

            self.action_openTestCase.setEnabled(isSuites)
            self.action_addTestCase.setEnabled(isSuites)
            self.action_saveSuites.setEnabled(isSuites)
            self.action_RefData.setEnabled(isSuites)
            self.action_autoAddTestStep.setEnabled(isSuites)
            self.action_excludedTrSetting.setEnabled(isSuites)
            self.action_excludedTrEnabled.setEnabled(isSuites)

            self.action_findData.setEnabled(isCase)
            self.action_capture.setEnabled(isCase)
            self.action_captureUiEvent.setEnabled(isCase)
            self.action_setRequests.setEnabled(isCase)
            self.action_playCase.setEnabled(isCase)


    # ============================ Action Event ============================
    def newSuitesClicked(self):
        '''
        Suites 생성 버튼 클릭 이벤트
        :return: None
        '''
        reply = QMessageBox.question(self, 'New Suites', "New Suites를 추가하시겠습니까?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            suites_nm, ok = QInputDialog.getText(self, 'New Suites', 'Suites명을 입력하세요.')

            if ok and suites_nm:
                suites = Suites(suites_nm)
                self.addSuites(suites=suites, tab_name=suites_nm)


    def openSuitesClicked(self, file_path):
        '''
        Suites 열기 버튼 클릭 이벤트
        :return: None
        '''
        if file_path:
            filePath = file_path
        else:
            fd = QFileDialog(self)
            filename = fd.getOpenFileName(self, '%s - Choose Suites File' % __appname__, self.SUITES_SAVE_PATH,'Suites Files(*.att)')
            filePath = filename[0]

        if filePath:
            with open(filePath, 'rb') as f:
                #print(filePath)
                unpickler = pickle.Unpickler(f)
                suites = unpickler.load()
                suites.setFileNm(filePath)
                # suites.setModifiedTime(datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
                self.addSuites(suites, os.path.split(filePath)[1])
                self.addRecentSuites(suites, filePath)
                self._setRecentSuitesView()


    def saveSuitesClicked(self):
        '''
        Suites 저장
        :return: None
        '''
        suitesWidget = self.tab_main.currentWidget()
        suitesFileNm = suitesWidget.suites.getFileNm()

        if suitesFileNm == '':
            fd = QFileDialog(self)
            filename = fd.getSaveFileName(self, '%s - Save Suites File' % __appname__, self.SUITES_SAVE_PATH, 'Suites Files(*.att)')
            filePath = filename[0]

            if filePath:
                with open(filePath, 'wb') as f:
                    suitesWidget.suites.setFileNm(filePath)
                    suitesWidget.suites.setModifiedTime(datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
                    pickle.dump(suitesWidget.suites, f, pickle.HIGHEST_PROTOCOL)
                    self.tab_main.setTabText(self.tab_main.currentIndex(), os.path.split(filePath)[1])
                    self.addRecentSuites(suitesWidget.suites, filePath)
                    QMessageBox.information(self, "Save Suites File", "Save Complete")
        else:
            with open(suitesFileNm, 'wb') as f:
                suitesWidget.suites.setModifiedTime(datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
                pickle.dump(suitesWidget.suites, f, pickle.HIGHEST_PROTOCOL)
                self.addRecentSuites(suitesWidget.suites, suitesFileNm)
                QMessageBox.information(self, "Save Suites File", "Save Complete")


    def openTestCaseClicked(self):
        '''
        case 파일 open 클릭 이벤트
            - case widget의 openTestCaseClicked 호출
        :return:
        '''
        suites = self.tab_main.currentWidget()
        suites.case_widget.openTestCaseClicked()


    def addTestCaseClicked(self):
        '''
        case 추가 클릭 이벤트
            - case widget의 addTestCaseClicked 호출
        :return:
        '''
        suites = self.tab_main.currentWidget()
        suites.case_widget.addTestCaseClicked()


    def playCaseClicked(self):
        '''
        case 수행 클릭 이벤트
            - action_playCase checked 이벤트가 발생되고 호출
            - action_playCase 버튼이 체크가 된 상태라면 case 수행
            - action_playCase 버튼이 체크해제가 된 상태라면 case 수행 정지
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        if self.action_playCase.isChecked():
            suites.case_widget.playCaseClicked()
        else:
            self.action_playCase.setChecked(True)
            suites.case_widget.stopCaseWorker()


    def getCopyCaseList(self):
        '''
        복제할 case 리스트를 Return
        :return: (list) [(class) case1, (class) case2, ...]
        '''
        return self.copy_case_list


    def removeCopyCaseList(self):
        '''
        복제할 case 리스트 초기화
        :return:
        '''
        self.copy_case_list = []


    def refDataClicked(self):
        '''
        Reference data Dialog 활성화 버튼 클릭 이벤트
        :return: None
        '''
        suites_widget = self.tab_main.currentWidget()
        suites = suites_widget.getSuites()
        self.refDataDialog = RefDataDialog(suites, self.web)
        self.refDataDialog.popUp()


    def startSwingClicked(self):
        '''
        이벤트 Capture를 위해 Swing WebBrowser 수행
            - 이미 수행중인 경우 재수행하지 않고 해당 Browser로 Focus
        :return:
        '''
        if self.web:
            if self.web.getStatus():
                driver = self.web.getDriver()
                currentWindow = driver.current_window_handle
                driver.switch_to_window(currentWindow)

                currentWindow = driver.current_window_handle
                driver.switch_to_window(currentWindow)
            else:
                self.web = WebBrowser('SWGS')
                self.progressBar.setRange(0, 0)
                self.progressBar.setMsg('Swing Browser Open...')
                self.tab_main.setEnabled(False)
                self.eventWorker = EventThread(self.web.popUp)
                self.eventWorker.finished.connect(self.swingBrowserOpened)
                self.eventWorker.start()
        else:
            self.web = WebBrowser('SWGS')
            self.progressBar.setRange(0, 0)
            self.progressBar.setMsg('Swing Browser Open...')
            self.tab_main.setEnabled(False)
            self.eventWorker = EventThread(self.web.popUp)
            self.eventWorker.finished.connect(self.swingBrowserOpened)
            self.eventWorker.start()


    def swingBrowserOpened(self):
        '''
        Swing Browser 활성화 후 호출되는 이벤트
        :return: None
        '''
        #self.web.setSessionId('231d3067045a6c967ccfa68d876e5b3e')
        self.progressBar.setRange(0, 100)
        self.progressBar.setMsg('')
        self.tab_main.setEnabled(True)
        print(self.web.getSessionId())


    def recordRequest(self):
        '''
        Request Record Click 이벤트
            - 클릭 시 Record를 시작
            - 다시 클릭 시 Record 중지
        :return:
        '''
        if self.action_capture.isChecked():
            if self.web:
                self.web.clear()
                self.web.recordUiEvent()

                suites_widget = self.tab_main.currentWidget()
                suites_widget.case_widget.action_capture.setChecked(True)
                #self.recordDialog.popUp(self.web)
                #self.hide()
            else:
                self.action_capture.setChecked(False)
        else:
            suites_widget = self.tab_main.currentWidget()
            record_type = suites_widget.case_widget.cb_capture_type.currentText()
            self.endRecordSignal(record_type)
            #self.recordDialog.btn_record.setChecked(False)
            #self.recordDialog.btnRecordClicked()


    def endRecordSignal(self, record_type):
        '''
        Record Dialog 화면에서 Record 중지 시 발생 이벤트
            - 중지 시 Step으로 추가
        :param record_type: (str) 'TR'
        :return: None
        '''
        self.action_capture.setChecked(False)

        if record_type == 'TR':
            requestList = self.web.getRequest()
            self.setXhrStep(requestList, excluded=True)
        elif record_type == 'UI':
            self.web.recordUiEvent()
            eventList = self.web.getBrowserEvents()
            self.setUiEvent(eventList)
        else:
            print('현재 미지원')

        suites_widget = self.tab_main.currentWidget()
        suites_widget.case_widget.action_capture.setChecked(False)


    def recordUiEvent(self):
        '''
        UI Event Capture 시작
        :return: None
        '''
        if self.action_captureUiEvent.isChecked():
            self.web.recordUiEvent()


    def setRequests(self):
        '''
        Request Set 이벤트
        :return: None
        '''
        if self.web is not None:
            requestList = self.web.getRequest()
            self.setXhrStep(requestList, excluded=True)


    def setXhrStep(self, requestList, excluded=True):
        '''
        XHR Step 추가 이벤트
        :param requestList: (list) []
        :param excluded: (bool) True
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        case = suites.selected_case

        if case is not None:
            if requestList:
                reply = QMessageBox.question(self, 'Add Step',"{cnt}건의 Request 결과를 Step에 추가하시겠습니까?".format(cnt=len(requestList)),QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    suites.setStepByRequest(requestList, excluded)


    def clearRequests(self):
        '''
        Capture 된 Requrest 모두 삭제
        :return: None
        '''
        if self.web is not None:
            requestList = self.web.getRequest()

            if requestList:
                reply = QMessageBox.question(self, 'Clear Requests',"Capture된 Request 결과를 모두 삭제하시겠습니까?", QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.web.clear()


    def setUiEvent(self, ui_event_list):
        '''
        Capture 된 UI Event Step으로 추가
        :param ui_event_list: (list) []
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        case = suites.selected_case

        if case is not None:
            if ui_event_list:
                reply = QMessageBox.question(self, 'Add Step', "{cnt}건의 UI Event를 Step에 추가하시겠습니까?".format(cnt=len(ui_event_list)), QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    suites.setStepByUiEvent(ui_event_list, self.web.getDriver())


    def findDataClicked(self):
        '''
        찾기 버튼 클릭 이벤트
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        suites.findData()


    def eventListClicked(self):
        '''
        Event Dialog 활성화 (수정필요)
        :return: None
        '''
        self.eventListDialog.popUp(self.web)


    def setStepBySelectedRequest(self, requestList):
        '''
        Event Dialog 에서 선택된 Request를 Step으로 추가
        :param requestList: (list) []
        :return: None
        '''
        self.setXhrStep(requestList, excluded=False)


    def autoAddTestStepClicked(self):
        '''
        붙여넣기(Ctrl + V) 시 Step 자동 추가 이벤트
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        suites.autoAddTestStep()


    def importTrInfoClicked(self):
        '''
        Transaction Info 추가 (수정필요)
            - Excel (TX_CODE, TX_NAME, SVC_NAME)
        :return: None
        '''
        fd = QFileDialog(self)
        filename = fd.getOpenFileName(self, '%s - Choose Transaction Info Excel File' % __appname__, self.SAVE_PATH,'Excel Files(*.xlsx *.xlsm *.xlsb *.xlam *.xltx *.xltm *.xls *.xla *.xlt *.xlm *.xlw)')
        filePath = filename[0]

        if filePath:
            with open(filePath, 'rb') as f:
                df_from_excel = pd.read_excel(filePath)
                tr_info_data = df_from_excel.to_dict('records')

                with open(self.TR_INFO_SAVE_PATH, 'wb') as f:
                    pickle.dump(tr_info_data, f, pickle.HIGHEST_PROTOCOL)

                suites = self.tab_main.currentWidget()
                suites.setTrInfo(tr_info_data)

            QMessageBox.information(self, "Import Transaction Info", "Complete")


    def excludedSettingClicked(self):
        '''
        제외 리스트 Dialog 활성화
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        excluded_tr_list = suites.getExcludedTrList()

        self.excludedTrDialog = ExcludedTrDialog()
        self.excludedTrDialog.changed.connect(self.setExcludedTrList)
        self.excludedTrDialog.popUp(excluded_tr_list)


    def setExcludedTrList(self, excluded_tr_list):
        '''
        제외 리스트에 Step 추가
        :param excluded_tr_list: (list) []
        :return: None
        '''
        suitesWidget = self.tab_main.currentWidget()
        suitesWidget.suites.setExcludedTrList(excluded_tr_list)


    def excludedEnableToggled(self, enabled):
        '''
        제외 리스트 활성화 버튼 클릭 이벤트
        :param enabled: (bool) True
        :return: None
        '''
        suites = self.tab_main.currentWidget()
        suites.setExcludedTrEnabled(enabled)


    def sqlEditorClicked(self):
        '''
        SQL Editor Dialog 클릭 이벤트
        :return: None
        '''
        self.sqlEditorDialog.popUp(show=True)


    def _twRecentSuitesDoubleClicked(self, row, col):
        '''
        Recent Suites Table Double Click 이벤트
            - Suites 파일을 Open
        :param row: (int) 0
        :param col: (int) 1
        :return: None
        '''
        item = self.tw_recentSuitesList.item(row, 3)
        suites_file_item = self.tw_recentSuitesList.item(row, 0)
        suites_file_nm = suites_file_item.text()

        reply = QMessageBox.question(self, 'Open Suites', "[{}] Suites 파일을 불러오시겠습니까?".format(suites_file_nm), QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.openSuitesClicked(item.text())


    # ============================ Tab Event ============================
    def addSuites(self, suites=None, tab_name=''):
        '''
        Suites 추가(신규 추가/불러오기) 시 Tab으로 추가하는 이벤트
        :param suites: (clase) suites
        :param tab_name: (str) 'tab_1'
        :return: None
        '''
        # Tab Name
        if tab_name:
            tabName = os.path.split(tab_name)[1]
        else:
            tab_name = "{work_type} {seq}".format(work_type='Suites', seq=self.tab_seq)

        suitesWidget = SuitesWidget(suites, self)
        suitesWidget.caseRunning.connect(self.startCase)
        suitesWidget.caseFinished.connect(self.finishedCase)
        suitesWidget.suitesRunning.connect(self.startSuites)
        suitesWidget.suitesFinished.connect(self.finishedSuites)
        suitesWidget.changeCase.connect(self.setComponent)
        suitesWidget.copiedCase.connect(self.copyCase)

        tab_index = self.tab_main.addTab(suitesWidget, tab_name)
        self.tab_main.setCurrentIndex(tab_index)

        self.tab_seq += 1

    def removeTab(self, index):
        '''
        Tab Close 시 발생 이벤트
        :param index: (int) 1
        :return: None
        '''
        widget = self.tab_main.widget(index)
        if widget is not None:
            widget.deleteLater()
        self.tab_main.removeTab(index)


    # ============================ Signal Event ============================
    def startCase(self):
        '''
        Case 수행 시 발생 Signal 이벤트
            - 하단 Progressbar 수행중으로 변경
        :return: None
        '''
        self.caseRunning = True
        self.progressBar.setRange(0, 0)
        self.progressBar.setMsg('Loading...')
        self.setComponent()

        suitesWidget = self.tab_main.currentWidget()
        suitesWidget.btn_playSuites.setEnabled(False)


    def finishedCase(self):
        '''
        Case 수행 종료 시 발생 Signal 이벤트
            - 하단 Progressbar 중지
        :return: None
        '''
        self.caseRunning = False
        self.progressBar.setRange(0, 100)
        self.progressBar.setMsg('')
        self.setComponent()

        suitesWidget = self.tab_main.currentWidget()
        suitesWidget.btn_playSuites.setEnabled(True)


    def startSuites(self):
        '''
        Suites 테스트 수행 시 발생 이벤트
            - progressbar 수행
            - 화면 Component 재설정
        :return: None
        '''
        self.suitesRunning = True
        self.progressBar.setRange(0, 0)
        self.progressBar.setMsg('Loading...')
        self.setComponent()
        #suites = self.tab_main.currentWidget()
        #suites.qqqq()


    def finishedSuites(self):
        '''
        Suites 테스트 완료 시 발생 이벤트
            - progressbar 수행 정지
            - 화면 Component 재설정
        :return: None
        '''
        self.suitesRunning = False
        self.progressBar.setRange(0, 100)
        self.progressBar.setMsg('')
        self.setComponent()


    def copyCase(self, case_list):
        '''
        case 복사 시 발생 이벤트
        :param case_list:
        :return:
        '''
        print(case_list)
        self.copy_case_list = case_list


    def addRecentSuites(self, suites, file_path):
        '''
        recent suites list에 추가 이벤트
            - Suites Open 시 리스트에 추가
            - Suitest 저장 시 리스트에 추가
            - 목록은 최대 저장 가능 건수는 config로 관리
        :param suites: (class) suites
        :param file_path: (str) file_path
        :return: None
        '''
        suites_info = {}
        suites_info['suites_file'] = os.path.split(file_path)[1]
        suites_info['suites_nm'] = suites.getSuitesNm()
        suites_info['modified_time'] = suites.getModifiedTime()
        suites_info['file_path'] = file_path

        try:
            index = next(idx for idx, pop_suites_info in enumerate(self.recent_suites_list) if pop_suites_info['file_path'] == file_path)
        except StopIteration:
            index = -1

        if index > -1:
            self.recent_suites_list.pop(index)
        elif RECENT_SUITES_HISTORY_CNT <= len(self.recent_suites_list):
            self.recent_suites_list.pop(0)

        self.recent_suites_list.append(suites_info)


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit', "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.settingSave()

            if self.web is not None:
                self.web.quit()
            self.deleteLater()
            event.accept()
        else:
            event.ignore()

    def settingSave(self, save_cl='all'):
        self.settings.load()
        settings = self.settings

        if save_cl == 'all':
            settings["SETTING_WIN_SIZE"] = self.size()
            settings["SETTING_WIN_POSE"] = self.pos()
            settings["SETTING_WIN_GEOMETRY"] = self.saveGeometry()
            settings["RECENT_SUITES_LIST"] = self.recent_suites_list

        settings.save()


    def testClicked(self):
        '''
        Test Button 클릭 이벤트
        :return: None
        '''
        QMessageBox.information(self, "Test Button", "Complete\n[ main.py - testClicked() ]")




'''
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)

        menu = QMenu(parent)
        menu.addAction("Exit")

        self.setContextMenu(menu)
        menu.triggered.connect(self.exit)

    def exit(self):
        QCoreApplication.exit()
'''
class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


def main():
    change_crach_program = {}

    for crach_program in CRACH_PROGRAM_LIST:
        if os.path.exists(crach_program):
            change_program_name = '{}_xxx'.format(crach_program)
            change_crach_program[change_program_name] = crach_program

            os.rename(crach_program, change_program_name)

    app = QApplication(sys.argv)
    test_tool_window = MainWindow()
    # Back up the reference to the exceptionhook
    sys._excepthook = sys.excepthook

    # Set the exception hook to our wrapping function
    sys.excepthook = my_exception_hook

    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    # the shortcut
    keybinder.init()

    def recordRequest():
        test_tool_window.action_capture.setChecked(not test_tool_window.action_capture.isChecked())
        test_tool_window.recordRequest()

    def recordUiEvent():
        test_tool_window.action_captureUiEvent.setChecked(not test_tool_window.action_captureUiEvent.isChecked())
        test_tool_window.recordUiEvent()

    keybinder.register_hotkey(test_tool_window.winId(), "Ctrl+F3", recordRequest)
    keybinder.register_hotkey(test_tool_window.winId(), "Ctrl+F5", recordUiEvent)

    # Install a native event filter to receive events from the OS
    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)

    # System tray application
    #widget = QWidget()
    #icon = newIcon('auto_test.png')
    #trayIcon = SystemTrayIcon(icon, widget)
    #trayIcon.show()

    test_tool_window.show()
    app.exec()

    try:
        keybinder.unregister_hotkey(test_tool_window.winId(), "Ctrl+F3")
        keybinder.unregister_hotkey(test_tool_window.winId(), "Ctrl+F5")
    except:
        pass

    try:
        for crach_program in list(change_crach_program.keys()):
            if os.path.exists(crach_program):
                change_program_name = change_crach_program[crach_program]
                os.rename(crach_program, change_program_name)
    except:
        pass


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    # sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())