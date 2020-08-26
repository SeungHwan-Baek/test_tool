# -*- coding: utf-8 -*-
import os, sys
import json

import pandas as pd
import copy
import datetime
import pickle
import pyperclip
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
#import PyQt5_stylesheets
from PyQt5 import uic
from functools import partial
from utils.lib import addTreeRoot, addTreeChild, horizontalLayout
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from dialogs.findDataDialog import FindDataDialog
from dialogs.scheduleDialog import ScheduleDialog
from dialogs.markingDataDialog import MarkingDataDialog
from utils.lib import findDictIndexByValue, findTrName, chunkList, make_marking_seq

from libs.suites import Suites
from libs.xhr import Xhr
from libs.browser import Browser
from libs.browser_command import BrowserCommand

from widgets.caseWidget import CaseWidget
from widgets.stepWidget import StepWidget
from widgets.mainSplash import ProgressSplash

from utils.suitesWorker import SuitesThread, SuitesRefThread             # Suites 단위 Thread 처리

__appname__ = 'Test Automation Tool'

currentDir = os.path.dirname(os.path.realpath(__file__))
parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
form_class = uic.loadUiType(os.path.join(parentDir, "UI/suites_widget.ui"))[0]

#sys.path.append(os.path.realpath("instantclient_12_2"))
#os.environ['path'] = os.environ['path'] + os.pathsep + os.path.realpath("instantclient_12_2")

class SuitesWidget(QWidget, form_class):
    caseRunning = pyqtSignal(str)
    caseFinished = pyqtSignal()
    suitesRunning = pyqtSignal()
    suitesFinished = pyqtSignal()
    changeCase = pyqtSignal()
    copiedCase = pyqtSignal("PyQt_PyObject")

    excludedTrEnabled = True

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    CASE_SAVE_PATH = os.path.join(SAVE_PATH, 'test_file', 'case')
    STEP_SAVE_PATH = os.path.join(SAVE_PATH, 'test_file', 'step')
    VARIABLE_SAVE_PATH = os.path.join(SAVE_PATH, 'var', '.var_info')

    def __init__(self, suites=None, parent=None):
        super(SuitesWidget, self).__init__(parent)

        self.mainWidget = parent
        self.config = self.mainWidget.config

        if suites is None:
            self.suites = Suites()
        else:
            self.suites = suites

        self.selected_case = None
        self.selected_step = None
        self.checked_case_list = []
        self.thread_list = []
        self.therad_worker_list = []
        self.tmp_marking_data = []
        self.complete_case_cnt = 0
        self.complete_step_cnt = 0
        self.suites_step_cnt = 0
        self.stop_thread = False
        self.schedule_list = []
        self.schedule_timer_list = []

        self.sched = BackgroundScheduler()
        self.sched.start()

        self.setupUi(self)

        self.splash = ProgressSplash()
        self.findDataDialog = FindDataDialog()

        self._initData()
        self._loadUiInit()
        self._loadSetting()
        self._setEvent()


    # ============================ UI Init ============================
    def _initData(self):
        pass

    def _loadUiInit(self):
        self.case_widget = CaseWidget(suites=self.suites, parent=self)
        self.case_widget.selected.connect(self._setSelectedCase)
        self.case_widget.stepFinished.connect(self._stepFinished)
        self.case_widget.caseFinished.connect(self._caseFinished)
        self.case_widget.varLoadApplied.connect(self._varLoadApplied)
        self.case_widget.changeStep.connect(self._changeStep)
        self.case_widget.run.connect(self._runCase)
        self.case_widget.saveVariable.connect(self._saveVariable)
        self.case_widget.copied.connect(self._copiedCase)
        # self.testCase_layout.selected.connect(self.__dataInfoSelected)
        self.testCase_layout.addWidget(self.case_widget)

        self.step_widget = StepWidget(suites=self.suites, parent=self)
        self.step_widget.xhrToDown.connect(self._runXhrToDown)
        self.testStep_layout.addWidget(self.step_widget)


        self.marking_widget = MarkingDataDialog()
        self.marking_widget.buttonBox.hide()
        self.marking_layout.addWidget(self.marking_widget)


        self.splitter_case_step.setSizes([250, 750])
        self.splitter_case_info.setSizes([700, 300])

        self.tw_scheduleList.hideColumn(1)          # Schedule ID
        self.tw_inputValue.setColumnWidth(0, 300)
        self.tw_inputValue.expandAll()


    def _loadSetting(self):
        selected_case_id = self.suites.getSelectedCaseId()

        if selected_case_id:
            self.case_widget.setSelectedTestCase(selected_case_id, select=True)


    def _setEvent(self):
        self.tw_scheduleList.itemExpanded.connect(self.twScheduleListItemClicked)      # Schedule Item Expanded 이벤트
        self.tw_scheduleList.itemCollapsed.connect(self.twScheduleListItemClicked)     # Schedule Item Collapse 이벤트

        self.action_autoAddTestStep.triggered.connect(self.autoAddTestStep)            # 메뉴 - Auto Add Test Step
        self.btn_playSuites.clicked.connect(self.btnPlaySuites)                        # Play Suites 버튼 클릭 이벤트

        self.edt_caseDesc.textChanged.connect(self._caseDescChanged)                   # Play Suites 버튼 클릭 이벤트

    # ============================ Case Widget Signal Event ============================
    def _setSelectedCase(self, case):
        '''
        Case 변경 시 발생 이벤트
            - Main 화면에 버튼 활성화 이벤트 발생
            - Step Widget View Setting
        :param case:
        :return: None
        '''
        self.selected_case = case

        self.changeCase.emit()

        self.step_widget.setComponetEnable()
        self.step_widget.setStepView()
        self.step_widget.setDataListView()

        self.setCaseInfoView(self.selected_case)

    def _runCase(self, run_type):
        '''
        Case 수행 시 발생 이벤트
            - step component 초기화
        :return:
        '''
        self.caseRunning.emit(run_type)
        self.sw_caseStep.setCurrentIndex(1)
        self.tab_caseStep.setCurrentIndex(1)
        self.step_widget.runCase()


    def _saveVariable(self, variables):
        '''
        변수 저장 시 발생 이벤트
        :param variables: (dict) {$VARIABLE1$:...}
        :return: None
        '''
        variable_info = {}

        # Variable Info Load
        if os.path.exists(self.VARIABLE_SAVE_PATH):
            with open(self.VARIABLE_SAVE_PATH, 'rb') as f:
                variable_info = pickle.load(f)

        alias, ok = QInputDialog.getText(self, 'Save Variable', '저장 할 변수의 Alias를 입력하세요.')

        if ok and alias:
            variable_info[alias] = variables

            with open(self.VARIABLE_SAVE_PATH, 'wb') as f:
                pickle.dump(variable_info, f, pickle.HIGHEST_PROTOCOL)

            QMessageBox.information(self, "Save Variable", "Complete")


    def _copiedCase(self, case_list):
        '''
        Case 복사 시 발생 이벤트
        :param case_list:
        :return:
        '''
        print(case_list)
        self.copiedCase.emit(case_list)


    def _stepFinished(self, step, idx):
        '''
        Case의 Step 수행 완료 시 발생 이벤트
        :param step: (Class) step
        :param idx: Step의 Seq
        :return: None
        '''
        self.step_widget.stepFisished(step, idx)

    def _caseFinished(self):
        self.marking_widget.loadData(self.selected_case)
        self.caseFinished.emit()
        self.step_widget.caseFisished()


    def _varLoadApplied(self):
        '''
        Case에 변수를 불러와 적용 시 발생 이벤트
        :return:
        '''
        self.step_widget.setStepView()


    def _changeStep(self, step_id, data_list_id, row_index, column_id):
        row = self.selected_case.findStepIndexByStepId(step_id)
        self.step_widget.setTestStepCurrnetRow(row)
        self.step_widget.setDataListCurrnetRow(data_list_id)
        self.step_widget.setDataDtlCurrnetRow(row_index, column_id)


    # ============================ Step Widget Signal Event ============================
    def _runXhrToDown(self, index):
        self.case_widget.action_playCase.setChecked(True)
        self.case_widget.playCaseClicked(index)


    # ============================ Find Data Dialog Signal Event ============================
    def _findStepIndex(self, step_index):
        self.step_widget.setTestStepCurrnetRow(step_index)

    def _findDataIndex(self, step_index, data_list_id, row_indx, column_id):
        self.step_widget.setTestStepCurrnetRow(step_index)
        self.step_widget.setDataListCurrnetRow(data_list_id)
        self.step_widget.setDataDtlCurrnetRow(row_indx, column_id)

    # ============================ Method ============================
    def getSuites(self):
        '''
        (class) suites 를 Return
        :return: (class) suites
        '''
        return self.suites

    def findData(self):
        '''
        Main 화면에서 메뉴 Find Data 클릭 시 발생
            - Find Data Dialog 활성화
        :return: None
        '''
        self.findDataDialog.findStep.connect(self._findStepIndex)
        self.findDataDialog.findData.connect(self._findDataIndex)
        self.findDataDialog.popUp(self.selected_case)

    def setExcludedTrEnabled(self, enabled):
        '''
        Main 화면에서 메뉴 Excluded Transaction Enabled 클릭 시 발생
        :param enabled:
        :return: None
        '''
        self.excludedTrEnabled = enabled

    def getExcludedTrList(self):
        '''
        Main 화면에서 메뉴 Excluded Transaction Setting 클릭 시 발생하는 이벤트
        :return: List
        '''
        return self.suites.getExcludedTrList()

    def setStepByRequest(self, request_list, excluded=True):
        '''
        Main 화면에서 Capture를 중지하거나 Set Requests 를 클릭 시 발생하는 이벤트
            - Browser 에서 Capture 한 Request List를 Step에 추가
        :param request_list: (list)
        :return:
        '''
        group, ok = QInputDialog.getText(self, 'Step grouping', 'Group명을 입력하세요.')
        excluded_cnt = 0
        add = 0

        OFFER_EXCLUSION_TR_LIST = self.config.getlist("section_tr", "OFFER_EXCLUSION_TR_LIST")

        for requestDtl in request_list:
            trxCode = requestDtl['trx_code']
            inputData = requestDtl['input_data']
            outputData = requestDtl['output_data']

            if excluded:
                index = findDictIndexByValue(self.suites.getExcludedTrList(), 'tr_id', trxCode)
            else:
                index = -1

            if self.excludedTrEnabled and index > -1:
                excluded_cnt += 1
            else:
                tx_name = findTrName(trxCode)

                step = Xhr(case=self.selected_case, step_type='XHR')
                step['group'] = group
                step['target'] = trxCode
                step['target_nm'] = tx_name
                step['error_option'] = 'Stop'

                if trxCode in OFFER_EXCLUSION_TR_LIST:
                    step['offer_exclusion'] = True

                self.selected_case.setStepList(step)

                # Data Info 추가
                step.setInputData(inputData)
                step.setOutputData(outputData)

                tr_info = step.getTrInfo(action='UDetail')
                step.setTrIO("CHANGE", tr_info)

                add += 1

        self.step_widget.setStepView()

        QMessageBox.information(self, "Setting Step By Request", "[{add}]건 추가완료, [{excluded}]건 제외".format(excluded=excluded_cnt, add=add))

    def setStepByUiEvent(self, ui_event_list, driver):
        group, ok = QInputDialog.getText(self, 'Step grouping', 'Group명을 입력하세요.')

        try:
            browser_step = self.selected_case.findStepByType('Open Browser')[0]
            browser_nm = browser_step.get('browser_nm')

            if driver:
                browser_step.setDriver(driver)
        except IndexError:
            browser_step = Browser(case=self.selected_case, step_type='Open Browser')
            browser_step.makeStep(driver)
            browser_nm = browser_step.get('browser_nm')
            self.selected_case.setStepList(browser_step)

        for ui_event in ui_event_list:
            browser_command_step = BrowserCommand(case=self.selected_case)
            browser_command_step.makeStep(browser_nm, ui_event)
            browser_command_step['group'] = group
            self.selected_case.setStepList(browser_command_step)

        self.step_widget.setStepView()


    def twScheduleListItemClicked(self, item):
        '''
        예약 리스트 스케줄 열기/닫기 시 이벤트
        :param item:
        :return: None
        '''
        schedule_id = item.text(1)

        try:
            index = next(idx for idx, schedule in enumerate(self.schedule_list) if schedule['schedule_id'] == schedule_id)
        except StopIteration:
            index = -1

        if index > -1:
            self.schedule_list[index]['expanded'] = item.isExpanded()


    def twScheduleListItemExpanded(self, item):
        '''
        예약 리스트 스케줄 확장 시 이벤트
        :param item:
        :return: None
        '''
        schedule_id = item.text(1)

        try:
            index = next(idx for idx, schedule in enumerate(self.schedule_list) if schedule['schedule_id'] == schedule_id)
        except StopIteration:
            index = -1

        if index > -1:
            self.schedule_list[index]['expanded'] = item.isExpanded()


    def autoAddTestStep(self):
        '''
        Main 화면에서 Copy한 Text(payload)를 붙여넣을때 발생하는 이벤트
            - HEAD Data에 Trx_Code가 존재하는 경우 Step으로 추가
        :return:
        '''
        if self.selected_case is not None:
            dicInputData = {}
            dicOutputData = {}
            copySting = pyperclip.paste()

            input_data = copySting.split("::")[0]

            try:
                output_data = copySting.split("::")[1]
            except IndexError:
                output_data = {}

            try:
                if type(input_data) == str:
                    input_data = input_data.replace("'", "\"")
                    try:
                        dicInputData = json.loads(input_data)
                    except json.JSONDecodeError as e:
                        print(e)
                elif type(input_data) == dict:
                    dicInputData = input_data


                if type(output_data) == str:
                    output_data = output_data.replace("'", "\"")
                    try:
                        dicOutputData = json.loads(output_data)
                    except json.JSONDecodeError as e:
                        print(e)
                elif type(output_data) == dict:
                    dicOutputData = output_data

                #print(dicInputData)
                trxCode = dicInputData['HEAD']['Trx_Code']

                reply = QMessageBox.question(self, 'Add Test Step', "[{}] Transaction Step을 추가하시겠습니까?".format(trxCode), QMessageBox.Yes, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    tx_name = findTrName(trxCode)

                    target_nm, ok = QInputDialog.getText(self, 'Step 추가', 'Target명을 입력하세요.', text=tx_name)

                    if ok:
                        current_step_index = self.selected_case.getSelectedStepRow()

                        if current_step_index > -1:
                            current_step = self.selected_case.getStep(idx=current_step_index)
                            group = current_step.get('group')
                        else:
                            group = ''

                        step = Xhr(case=self.selected_case, step_type='XHR')
                        step['group'] = group
                        step['target'] = trxCode
                        step['target_nm'] = target_nm
                        step['error_option'] = 'Stop'

                        step.setInputData(dicInputData)
                        step.setOutputData(dicOutputData)

                        self.selected_case.setStepList(step, index=current_step_index)
                        self.step_widget.setStepView()
            except:
                pass


    def addSchedule(self):
        '''
        Schedule 추가 버튼 클릭 시 이벤트
            - 스케줄 추가 팝업 활성화
            - case widget에서 호출함
        :return: None
        '''
        self.checked_case_list = self.case_widget.getCheckedCase()

        if self.checked_case_list:
            pass
        else:
            case = self.case_widget.getCurrentCase()

            if case:
                self.checked_case_list.append(case)

        if self.checked_case_list:
            scheduleDialog = ScheduleDialog()
            scheduleDialog.addSchedule.connect(self._addScheduleList)
            scheduleDialog.popUp()
        else:
            QMessageBox.information(self, "스케줄 추가", "선택된 Case가 없습니다.")


    def _caseDescChanged(self):
        '''
        Case 설명 변경 시 Case에 자동저장
        '''
        if self.selected_case:
            text = self.edt_caseDesc.toPlainText()
            self.selected_case.setCaseDesc(text)


    def btnPlaySuites(self):
        '''
        Play Suites 버튼 클릭 이벤트
        :return: None
        '''
        self.checked_case_list = self.case_widget.getCheckedCase()
        self.suites_step_cnt = 0
        self.complete_case_cnt = 0
        self.complete_step_cnt = 0

        caseCnt = len(self.checked_case_list)
        all_checked = False

        # 선택된 case가 존재하면 선택된 case만 수행
        if self.checked_case_list:
            pass
        else:
            # Case Widget Tree CheckBox Checked
            all_checked = self.case_widget.setChecked(checked=True)

            self.checked_case_list = self.case_widget.getCheckedCase()
            caseCnt = len(self.checked_case_list)

        for case in self.checked_case_list:
            self.suites_step_cnt += case.getStepCount()

        if self.btn_playSuites.isCheckable():
            self.stopSuitesWorker()
            self.btn_playSuites.setCheckable(False)
            self.btn_playSuites.setEnabled(False)
        else:
            reply = QMessageBox.question(self, 'Play This Suites', "[{caseCnt}] 건의 Test Case를 진행하시겠습니까?".format(caseCnt=caseCnt), QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.tmp_marking_data = []
                self.stop_thread = False

                MAX_THREAD_CNT = self.config.getInt("section_common", "MAX_THREAD_CNT")

                thread_cnt, ok = QInputDialog.getInt(self, 'Thread', 'Thread 수를 입력하세요.', value=1, min=1, max=MAX_THREAD_CNT)

                if ok:
                    self.sw_caseStep.setCurrentIndex(0)

                    #print(self.thread_list)

                    self.case_widget.tw_testCase.clearSelection()
                    self.case_widget.tw_testCase.setEnabled(False)

                    # 하단 Play Suites 버튼 수행중 상태로 변경
                    self.btn_playSuites.setCheckable(True)
                    self.btn_playSuites.setChecked(True)

                    # Suites의 모든 Case의 상태를 초기화
                    self.suites.initCaseStatus()
                    self.case_widget.setStatus(init=True)

                    # Main으로 Signal
                    self.suitesRunning.emit()

                    self.suitesRefWorker = SuitesRefThread(self.suites, case_list=self.checked_case_list, thread_cnt=thread_cnt)
                    self.suitesRefWorker.send_start_get_variable.connect(self.getCaseVariableStart)
                    self.suitesRefWorker.send_get_variable_signal.connect(self.getCaseVariableValue)
                    self.suitesRefWorker.send_end_get_variable.connect(self.getCaseVariableEnd)
                    self.suitesRefWorker.finished.connect(lambda: (self.getCaseVariableFinished(thread_cnt=thread_cnt)))

                    self.suitesRefWorker.start()

                    #print("Start - suitesWorker_{}".format(worker_index))

                    self.splash.setCaseProgressText('참조 데이타 조회...')
                    self.splash.popup()
            else:
                # 자동으로 모두 선택된 경우만 해제
                if all_checked:
                    self.case_widget.setChecked(checked=False)

    # ============================ QThread ============================
    def stopSuitesWorker(self):
        '''
        Suites 수행 중지 버튼 클릭 이벤트
        :return: None
        '''
        self.stop_thread = True

        self.suitesRefWorker.stop()

        for idx, case_list in enumerate(self.thread_list):
            getattr(self, "suitesWorker_{}".format(idx + 1)).stop()


    def workerProgessChaneValue(self, per, case):
        #text = 'Case [{case_nm}] ...'.format(case_nm=case.getCaseNm())
        #self.case_widget.setSelectedTestCase(case.getCaseId(), True)
        #self.case_widget.setFocusTestCase(case.getCaseId())
        #self.splash.startCaseProgress()
        pass


    def getSuitesCaseSignal(self, case, idx, marking_data):
        '''
        Case 수행 종료 시 이벤트
        :param case: (class) case
        :param idx: (int) 3
        :param marking_data: (list) []
        :return: None
        '''
        self.case_widget.setStatus(case)
        self.complete_case_cnt += 1
        self.splash.setCnt(self.complete_case_cnt, len(self.checked_case_list))
        #per = ((self.complete_case_cnt / len(self.checked_case_list)) * 100)
        #self.splash.setCaseProgressPer(per)

        self.tmp_marking_data.extend(marking_data)
        #self.case_widget.setSelectedTestCase(case.getCaseId(), False)
        self.case_widget.setCaseProgressbarVisible(case, visibled=False)


    def getSuitesStepStartSignal(self, step):
        '''
        Step 시작 시 Signal 이벤트
            - Splash 화면의 step 명을 변경
        :param step: (class) step
        :return: None
        '''
        text = 'Request [{target}] ...'.format(target=step.get('target'))
        #self.splash.setStepProgressText(text)


    def getSuitesStepFinishSignal(self, per, index, case, step):
        '''
        Step 완료 시 Signal 이벤트
        :param per: (int) 80 - Case 중 현재 진행 수치
        :param step: (class) step - 완료된 step
        :return: None
        '''
        text = 'Request [{target}] ...'.format(target=step.get('target'))
        self.complete_step_cnt += 1

        case_per = ((self.complete_step_cnt / self.suites_step_cnt) * 100)

        self.splash.setCaseProgressPer(case_per)
        #self.splash.setStepProgressPer(per, text)
        self.case_widget.setCaseDtlProgressbar(case=case, per=per)
        #self._stepFinished(step, index)

    def getCaseVariableStart(self, tot_cnt):
        '''
        Reference Data 가져오기 Thread 시작 시 발생 이벤트
        :param tot_cnt: (int) 3
        '''
        self.splash.setCnt(0, tot_cnt)


    def getCaseVariableEnd(self, tot_cnt, finished_cnt):
        '''
        Reference Data 가져오기 건별 종료시 발생 이벤트
        :param tot_cnt: (int) 3
        :param finished_cnt: (int) 1
        '''
        ref_per = ((finished_cnt / tot_cnt) * 100)
        self.splash.setCaseProgressPer(ref_per)
        self.splash.setCnt(finished_cnt, tot_cnt)


    def getCaseVariableValue(self, variable_nm):
        text = '[{target}] ...'.format(target=variable_nm)
        self.splash.setStepProgressText(text)


    def getCaseVariableFinished(self, thread_cnt):
        '''
        Reference Data 가져오기 Thread 종료 시 발생 이벤트
        '''
        if self.stop_thread:
            self.splash.endCaseProgress()

            self.case_widget.tw_testCase.setEnabled(True)
            self.btn_playSuites.setEnabled(True)
            self.btn_playSuites.setCheckable(False)
            self.btn_playSuites.setChecked(False)

            self.suitesFinished.emit()
            self.splash.close()

            QMessageBox.information(self, "Stop", "중지되었습니다.")
        else:
            self.splash.setCaseProgressText('Play Suites...')
            self.splash.endStepProgress('Case 수행...')
            self.splash.setCnt(0, len(self.checked_case_list))
            self.splash.setCaseProgressPer(0)

            self.therad_worker_list = []
            self.thread_list = chunkList(self.checked_case_list, thread_cnt)

            for idx, case_list in enumerate(self.thread_list):
                worker_index = idx + 1
                setattr(self, 'suitesWorker_{}'.format(worker_index), SuitesThread(self.suites, case_list=case_list, worker_index=worker_index))
                getattr(self, "suitesWorker_{}".format(worker_index)).change_value.connect(self.workerProgessChaneValue)
                getattr(self, "suitesWorker_{}".format(worker_index)).send_case_signal.connect(self.getSuitesCaseSignal)
                getattr(self, "suitesWorker_{}".format(worker_index)).send_step_finish_signal.connect(self.getSuitesStepFinishSignal)
                getattr(self, "suitesWorker_{}".format(worker_index)).finished.connect(self.suitesWorkerFinished)
                getattr(self, "suitesWorker_{}".format(worker_index)).terminated.connect(self.suitesWorkerTerminated)

                getattr(self, "suitesWorker_{}".format(worker_index)).start()  # Thread 실행

                self.therad_worker_list.append(getattr(self, "suitesWorker_{}".format(worker_index)))


    def suitesWorkerFinished(self):
        sender = self.sender()

        try:
            self.therad_worker_list.remove(sender)
        except ValueError:
            pass

        if self.therad_worker_list:
            pass
        else:
            self.splash.endCaseProgress()

            self.saveMarkingDataFile()

            self.suitesFinished.emit()
            self.case_widget.tw_testCase.setEnabled(True)
            self.btn_playSuites.setEnabled(True)
            self.btn_playSuites.setCheckable(False)
            self.btn_playSuites.setChecked(False)
            self.step_widget.caseFisished()

            self.splash.close()

            if self.stop_thread:
                QMessageBox.information(self, "Stop", "중지되었습니다.")
            else:
                QMessageBox.information(self, "Complete", "선택된 Case 테스트 진행이 완료되었습니다.")


    def suitesWorkerTerminated(self, worker_id, msg):
        sender = self.sender()

        try:
            self.therad_worker_list.remove(sender)
        except ValueError:
            pass

        self.suitesFinished.emit()

        if self.therad_worker_list:
            pass
        else:
            self.splash.close()
            self.case_widget.tw_testCase.setEnabled(True)
            self.btn_playSuites.setEnabled(True)
            self.btn_playSuites.setCheckable(False)
            self.btn_playSuites.setChecked(False)
            self.step_widget.caseFisished()

            QMessageBox.information(self, "Abnormally terminated", "비정상종료 되었습니다.\n[{}]".format(msg))


    def saveMarkingDataFile(self):
        '''
        Marking Data를 File로 저장
        :return: None
        '''
        marking_data = self.suites.loadMaringData()
        rebuild_marking_data = []

        for tmp_marking_data_dtl in self.tmp_marking_data:
            case_id = tmp_marking_data_dtl['case_id']

            try:
                index = next(idx for idx, pop_marking_data in enumerate(rebuild_marking_data) if
                             pop_marking_data['case_id'] == case_id and pop_marking_data['test_data_id'] ==
                             tmp_marking_data_dtl['test_data_id'])
            except StopIteration:
                index = -1

            if index > -1:
                tmp_marking_data_dtl['test_data_name'] = rebuild_marking_data[index]['test_data_name']
                rebuild_marking_data[index]['marking_data'].extend(tmp_marking_data_dtl['marking_data'])
            else:
                test_data_name = make_marking_seq(marking_data, case_id)
                tmp_marking_data_dtl['test_data_name'] = test_data_name
                rebuild_marking_data.append(tmp_marking_data_dtl)

        # print(rebuild_marking_data)
        marking_data.extend(rebuild_marking_data)
        self.suites.saveMarkingData(marking_data)


    def _addScheduleList(self, schedule):
        '''
        Schedule 추기 시 호출 이벤트
        :param schedule: (dict) {'schedule_id': 'f0b13950-e11d-4e70-a441-a6a6008ddea4',
                                 'schedule_name': '3',
                                 'schedule_date_time': datetime.datetime(2020, 7, 30, 21, 30, 34, 652000),
                                 'cycle_yn': False,
                                 'expanded': False,
                                 'case_list': [<libs.case.Case object at 0x182D7470>]}
        :return: None
        '''
        schedule['case_list'] = self.checked_case_list
        self.schedule_list.append(schedule)
        print(schedule)

        if schedule['cycle_yn']:
            if schedule['cycle_time_type'] == '시간':
                self.sched.add_job(self.runSchedule, 'interval', [schedule['schedule_id'], self.checked_case_list], start_date=schedule['schedule_date_time'], hours=schedule['cycle_value'], max_instances=5, id=schedule['schedule_id'])
            elif schedule['cycle_time_type'] == '분':
                self.sched.add_job(self.runSchedule, 'interval', [schedule['schedule_id'], self.checked_case_list], start_date=schedule['schedule_date_time'], minutes=schedule['cycle_value'], max_instances=5, id=schedule['schedule_id'])
            elif schedule['cycle_time_type'] == '초':
                self.sched.add_job(self.runSchedule, 'interval', [schedule['schedule_id'], self.checked_case_list], start_date=schedule['schedule_date_time'], seconds=schedule['cycle_value'], max_instances=5, id=schedule['schedule_id'])
        else:
            self.sched.add_job(self.runSchedule, 'cron', [schedule['schedule_id'], self.checked_case_list], start_date=schedule['schedule_date_time'], end_date=schedule['schedule_date_time'] + datetime.timedelta(seconds=1), id=schedule['schedule_id'])
        self.tab_caseList.setTabText(1, '예약 작업리스트 ({})'.format(len(self.schedule_list)))
        self.setScheduleView()

        QMessageBox.information(self, "스케줄 추가", "[{}] 예약작업이 추가 되었습니다.".format(schedule['schedule_name']))


    def runSchedule(self, schedule_id, case_list):
        '''
        Schedule 수행 시 호출 이벤트
        :param schedule_id: (str) 'a468ff23-9e7a-4230-9c93-03db3b222105'
        :param case_list: (list) [(calss) case1, (class) case2, ...]
        :return: None
        '''
        print('예약 수행')
        self.suitesRunning.emit()

        self.complete_case_cnt = 0

        for case in case_list:
            self.suites_step_cnt += case.getStepCount()

        suitesWorker = SuitesThread(self.suites, case_list=case_list, variable_skip=False)
        suitesWorker.send_case_signal.connect(self.getSuitesCaseSignal)
        suitesWorker.send_step_finish_signal.connect(self.getSuitesStepFinishSignal)
        suitesWorker.finished.connect(partial(self.scheduleFinished, schedule_id))
        suitesWorker.terminated.connect(self.suitesWorkerTerminated)
        suitesWorker.start()


    def scheduleFinished(self, schedule_id):
        '''
        Schedule 종료 시 호출 이벤트
        :return: None
        '''

        remaining_count = 0

        try:
            index = next(idx for idx, schedule in enumerate(self.schedule_list) if schedule['schedule_id'] == schedule_id)
        except StopIteration:
            index = -1

        if index > -1:
            remaining_count = self.schedule_list[index]['remaining_count']
            remaining_count = remaining_count - 1
            self.schedule_list[index]['remaining_count'] = remaining_count

        if remaining_count > 0:
            pass
        else:
            self.schedule_list.pop(index)
            exist_schedule = self.sched.get_job(schedule_id)

            if exist_schedule:
                self.sched.remove_job(schedule_id)

        if self.schedule_list:
            self.tab_caseList.setTabText(1, '예약 작업리스트 ({})'.format(len(self.schedule_list)))
        else:
            self.tab_caseList.setTabText(1, '예약 작업리스트')

        self.setScheduleView()
        self.splash.endCaseProgress()

        self.saveMarkingDataFile()

        self.suitesFinished.emit()
        self.case_widget.tw_testCase.setEnabled(True)
        self.btn_playSuites.setEnabled(True)
        self.btn_playSuites.setCheckable(False)
        self.btn_playSuites.setChecked(False)
        self.step_widget.caseFisished()

        self.splash.close()


    def setScheduleView(self):
        '''
        예약 작업리스트 Tree Widget View 설정
            - 예약작업이 추가되거나 완료 시 호출
        :return: None
        '''
        # Component 초기화
        for q_timer in self.schedule_timer_list:
            q_timer.stop()

        self.schedule_timer_list = []

        self.tw_scheduleList.clear()

        schedule_font = QFont('맑은 고딕', 10)
        schedule_font.setBold(True)

        for schedule in self.schedule_list:
            root_node = addTreeRoot(treeWidget=self.tw_scheduleList, idx=0, text=schedule['schedule_name'], check=False)
            root_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
            root_node.setForeground(0, Qt.cyan)
            root_node.setFont(0, schedule_font)
            root_node.setText(1, schedule['schedule_id'])
            root_node.setText(2, '{description} (잔여{remaining_count}회)'.format(description=schedule['description'], remaining_count=schedule['remaining_count']))

            expanded = schedule['expanded']
            root_node.setExpanded(expanded)

            labelWidget = QLabel()
            labelWidget.setStyleSheet("background-color: rgba(0,0,0,0%)")
            labelWidget.setText("남은시간")
            #labelWidget.setAlignment(Qt.AlignCenter)
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(labelWidget)
            layout.setContentsMargins(0, 0, 0, 0)
            timer = QTimer(self)
            timer.setInterval(1000)
            timer.timeout.connect(partial(self.timeout, labelWidget, schedule['schedule_date_time']))
            timer.start()
            self.schedule_timer_list.append(timer)
            self.tw_scheduleList.setItemWidget(root_node, 3, cell_widget)

            for case in schedule['case_list']:
                child_node = addTreeChild(parent=root_node, text=case.caseNm, check=False)


    def setCaseInfoView(self, case):
        if case:
            self.sw_caseStep.setCurrentIndex(1)
            self.edt_caseNm.setStyleSheet("background: qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 rgb(16, 158, 223), stop:1 rgb(8, 127, 170)); color:white;")
            self.edt_caseNm.setText(case.getCaseNm())
            self.edt_caseDesc.setText(case.getCaseDesc())

            self.marking_widget.loadData(case)
        else:
            self.sw_caseStep.setCurrentIndex(0)
            self.edt_caseNm.setStyleSheet("")
            self.edt_caseNm.clear()
            self.edt_caseDesc.clear()

        self.setCaseInputValueView(case)


    def setCaseInputValueView(self, case):
        self.tw_inputValue.clear()
        self.tw_inputValue.setRootIsDecorated(False)

        if case:
            root_font = QFont('맑은 고딕', 11)
            root_font.setBold(True)

            find_variables = case.getVariableByType(["Date", "Excel", "SQL", "Fixed Value", "SVC COMBO (Swing Only)"])

            for variable_type in find_variables:
                variable_type_item = QTreeWidgetItem(self.tw_inputValue)
                variable_type_item.setText(0, variable_type)
                variable_type_item.setForeground(0, QColor(255, 99, 71))
                variable_type_item.setFont(0, root_font)

                variable_list = find_variables[variable_type]

                for variable in variable_list:
                    variable_item = QTreeWidgetItem(variable_type_item)
                    variable_item.setText(0, variable.getId())
                    variable_item.setText(1, variable.get('description'))

                    input_value_item = QLineEdit(variable.getValue())
                    input_value_item.setStyleSheet("background-color: rgba(0,0,0,0%)")
                    input_value_item.editingFinished.connect(self._input_value_change)
                    input_value_cell_widget = horizontalLayout([input_value_item])
                    input_value_cell_widget.setMaximumWidth(200)
                    input_value_cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")

                    self.tw_inputValue.setItemWidget(variable_item, 2, input_value_cell_widget)

                self.tw_inputValue.expandToDepth(0)


    def _input_value_change(self):
        input_value_item = self.sender()
        print(input_value_item.text())

    def timeout(self, labelWidget, schedule_date_time):
        sender = self.sender()
        diff = schedule_date_time- datetime.datetime.now()
        seconds = int(diff.total_seconds())

        if seconds > 0:
            labelWidget.setText('남은시간 {}초'.format(seconds))
        else:
            labelWidget.setText('수행중...')
            sender.stop()
            self.schedule_timer_list.remove(sender)

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()


    def getCopyCaseList(self):
        copy_case_list = self.mainWidget.getCopyCaseList()
        return copy_case_list

    def removeCopyCaseList(self):
        self.mainWidget.removeCopyCaseList()