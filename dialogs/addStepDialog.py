"""
Step 추가 시
    1. UI add_step.ui에 추가
    2. (class) step을 상속받은 신규 step class (.py) 개발
    3. addStepDialog 신규 step Import
    4. addStepDialog _twStepTypeCurrentItemChanged Method에 Index 변경로직 추가
    5. accept, _setStep Method에 로직 추가
    6. stepDtlWidget setTarget, setType에 추가
"""

import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5 import uic
from libs.xhr import Xhr
from libs.sleep import Sleep
from libs.browser import Browser
from libs.if_condtion import If
from libs.browser_command import BrowserCommand
from libs.database import Database
from libs.message import Message
from dialogs.variableListDialog import VariableListDialog
from dialogs.sqlEditorDialog import SqlEditorDialog
from widgets.smsTextWidget import SmsTextWidget

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/add_step.ui"))[0]

class AddStepDialog(QDialog, dig_class):
    added = pyqtSignal("PyQt_PyObject", int)
    changed = pyqtSignal()

    appname = 'Add Step'
    step = None

    def __init__(self, call_gubun='New', case=None, step=None, group='', index=-1, condition_step_id=''):
        super().__init__()
        self.setupUi(self)

        self.callGubun = call_gubun
        self.case = case
        self.step = step
        self.group = group
        self.variables = {}

        if step:
            self.index = step.getSeq()
        elif index > -1:
            self.index = index
        else:
            self.index = case.getStepCount()

        self.condition_step_id = condition_step_id
        self.step_type = ''
        self.step_type_group = ''

        self.tmp_query = None
        self.tmp_session = None

        if self.callGubun == 'New':
            self.appname = 'Add Step'
        else:
            self.appname = 'Step Info'

        self.setWindowTitle(self.appname)
        self._loadUiInit()
        self._setEvent()


    def _loadUiInit(self):
        self.tw_stepType.hideColumn(1)
        self.tw_stepType.expandToDepth(1)

        self.splitter_type_option.setSizes([300, 700])

        self.edt_smsText = SmsTextWidget()
        #self.edt_logView.findText.connect(self.setFindText)
        if self.case:
            self.variables = self.case.getApplicableVariables(seq=self.index)
            self.edt_smsText.setAutocompletions(self.variables)

            # Line Edit 자동완성 Setting
            variable_keys = list(self.variables.keys())
            completer = QCompleter(variable_keys)
            completer.setCaseSensitivity(Qt.CaseInsensitive)

            self.edt_ifVariable.setCompleter(completer)
            self.edt_value.setCompleter(completer)
            self.edt_bCommandValue.setCompleter(completer)
        self.message_layout.addWidget(self.edt_smsText)


    def _setEvent(self):
        self.btn_setVariable.clicked.connect(self._setVariableClicked)
        self.btn_sqlDialog.clicked.connect(self._sqlDialogClicked)
        self.btn_addMobileNum.clicked.connect(self._addMobileNumClicked)

        # Item Change 이벤트
        self.tw_stepType.currentItemChanged.connect(self._twStepTypeCurrentItemChanged)  # Step Tree Item Selection Changed 이벤트


    def _twStepTypeCurrentItemChanged(self, new, old):
        self.step_type = new.text(1)
        parentNode = new.parent()

        if parentNode:
            self.step_type_group = parentNode.text(0)

            if self.step_type == '':
                self.sw_typeDtl.setCurrentIndex(0)
            elif self.step_type == 'Group':
                self.sw_typeDtl.setCurrentIndex(1)
            elif self.step_type_group == 'Request':
                self.sw_typeDtl.setCurrentIndex(2)
            elif self.step_type_group == 'Statement':
                self.sw_typeDtl.setCurrentIndex(3)

                if self.step_type =='IF':
                    self.sw_statementOption.setCurrentIndex(0)
                elif self.step_type =='Sleep':
                    self.sw_statementOption.setCurrentIndex(1)
                else:
                    self.sw_typeDtl.setCurrentIndex(0)
            elif self.step_type_group == 'Browser':
                self.sw_typeDtl.setCurrentIndex(4)

                if self.step_type =='Open Browser':
                    self.sw_browserOption.setCurrentIndex(0)
                elif self.step_type =='Refresh Browser':
                    self.sw_browserOption.setCurrentIndex(1)

                    self.cb_reloadBrowser.clear()
                    browser_step_list = self.case.findStepByType('Open Browser', key='browser_nm')
                    self.cb_reloadBrowser.addItems(browser_step_list)
                else:
                    self.sw_typeDtl.setCurrentIndex(0)

            elif self.step_type_group in ['Browser Command', 'Browser Command (Swing)']:
                self.sw_typeDtl.setCurrentIndex(5)

                self.cb_browser.clear()
                browser_step_list = self.case.findStepByType('Open Browser', key='browser_nm')
                self.cb_browser.addItems(browser_step_list)

                self.sw_bcommandOption.show()
                self.grp_gridInfo.hide()

                if self.step_type in ['Click', 'Double Click', 'Type', 'Execute Script', 'Switch to Frame', 'Grid Click', 'Grid Double Click', 'Grid Type', 'Combo Click']:
                    self.sw_bcommandOption.setCurrentIndex(0)

                    self.lbl_bCommandTarget.show()
                    self.cb_by.show()
                    self.edt_bCommandTarget.show()

                    if self.step_type in ['Click', 'Double Click', 'Switch to Frame', 'Grid Click', 'Grid Double Click']:
                        self.lbl_bCommandValue.hide()
                        self.edt_bCommandValue.hide()
                        self.cb_autoEnter.hide()
                    else:
                        self.lbl_bCommandValue.show()
                        self.edt_bCommandValue.show()
                        self.cb_autoEnter.show()

                    if self.step_type in ['Grid Click', 'Grid Double Click', 'Grid Type']:
                        self.grp_gridInfo.show()

                elif self.step_type == 'Alert':
                    self.sw_bcommandOption.setCurrentIndex(1)

                    self.lbl_bCommandTarget.hide()
                    self.cb_by.hide()
                    self.edt_bCommandTarget.hide()
                elif self.step_type == 'Switch to Default':
                    self.lbl_bCommandTarget.hide()
                    self.cb_by.hide()
                    self.edt_bCommandTarget.hide()
                    self.sw_bcommandOption.hide()

            elif self.step_type == 'Validation':
                self.sw_typeDtl.setCurrentIndex(6)
            elif self.step_type  == 'SMS':
                self.sw_typeDtl.setCurrentIndex(7)

        else:
            self.sw_typeDtl.setCurrentIndex(1)

    def _sqlDialogClicked(self):
        '''
        Database - Validation 에서 SQL 상세보기 클릭 이벤트
        :return: None
        '''
        sqlEditorDialog = SqlEditorDialog(case=self.case, step_seq=self.index)
        sqlEditorDialog.saved.connect(self._sqlEditorSaved)
        sqlEditorDialog.popUp(session=self.tmp_session, query=self.tmp_query)


    def _addMobileNumClicked(self):
        '''
        SMS - 수신자 추가 버튼 클릭 이벤트
        :return:
        '''
        self.tw_mobileList.insertRow(self.tw_mobileList.rowCount())


    def _setVariableClicked(self):
        '''
        Statement - IF 에서 tool 버튼 클릭 이벤트
        :return: None
        '''
        variableListDialog = VariableListDialog(self.case)
        variableListDialog.applied.connect(self._applyRefVariable)
        variableListDialog.popUp(open_type='select', step_seq=self.index)


    def _applyRefVariable(self, variable_id, ref_option_info):
        '''
        Variable Dialog에서 적용 시 발생 이벤트
        :param variable_id: (str) '$SVC_MGMT_NUM$'
        :param ref_option_info:
        :return: None
        '''
        self.edt_ifVariable.setText(variable_id)


    def _sqlEditorSaved(self, name, session, query):
        '''
        SQL Dialog에서 저장 시 발생 이벤트
        :param name: (str) 'ref_name' 참조에서 사용되는 항목으로 Step에서는 미사용
        :param session: (class) session
        :param query: (class) query
        :return: None
        '''
        self.tmp_session = session
        self.tmp_query = query
        self.tmp_query.setSession(self.tmp_session)

        self.edt_sid.setText(session.id + ' @ ' + session.sid)


    def _setUiValue(self):
        '''
        화면에 Step 값 Setting
            - 신규가 아닌 기존 Step 선택 시 Step의 정보로 화면에 노출하기 위함
        :return: none
        '''
        self.tw_stepType.setEnabled(False)
        step_type = self.step.getType()
        group = self.step.get('group')
        description = self.step.get('description')
        self.edt_description.setText(description)
        error_option = self.step.get('error_option', 'Stop')
        self.condition_step_id = self.step.get('condition_step_id')

        self.edt_group.setText(group)
        #combo_idx = self.cb_type.findText(type)
        #self.cb_type.setCurrentIndex(combo_idx)
        #self.cb_type.setEnabled(False)

        selectTreeItem = self.tw_stepType.findItems(step_type, Qt.MatchExactly | Qt.MatchRecursive, column=1)
        self.tw_stepType.setCurrentItem(selectTreeItem[0])

        err_option_combo_idx = self.cb_errOption.findText(error_option)
        self.cb_errOption.setCurrentIndex(err_option_combo_idx)

        #if self.condition_step_id:
        #    self.cb_errOption.setEnabled(False)

        if step_type == 'XHR':
            target = self.step.get('target')
            target_nm = self.step.get('target_nm')

            self.edt_xhrTarget.setText(target)
            self.edt_xhrTargetNm.setText(target_nm)

        elif step_type == 'Sleep':
            sec = self.step.get('sec')
            self.sp_sec.setValue(sec)
        elif step_type == 'Open Browser':
            browser_nm = self.step.get('browser_nm')
            sid = self.step.get('sid')
            url = self.step.get('url', '')

            self.edt_browserNm.setText(browser_nm)
            sid_combo_idx = self.cb_sid.findText(sid)
            self.cb_sid.setCurrentIndex(sid_combo_idx)
            self.edt_url.setText(url)
        elif step_type in ['Click', 'Type', 'Alert', 'Execute Script', 'Switch to Frame', 'Switch to Default', 'Grid Click', 'Grid Double Click', 'Grid Type', 'Combo Click']:
            browser_step_id = self.step.get('browser_step_id')
            browser_step = self.case.getStep(step_id=browser_step_id)
            browser_nm = browser_step.get('browser_nm')

            if step_type in ['Click', 'Type', 'Execute Script', 'Switch to Frame', 'Grid Click', 'Grid Double Click', 'Grid Type', 'Combo Click']:
                locator = self.step.get('locator')
                url = self.step.get('url', "")
                command_target = self.step.get('command_target')

                frame = self.step.get('frame', "")
                value = self.step.get('value', "")
                auto_enter = self.step.get('auto_enter', False)
                wait_sec = self.step.get('wait_sec', 0)

                browser_combo_idx = self.cb_browser.findText(browser_nm)
                self.cb_browser.setCurrentIndex(browser_combo_idx)

                locator_combo_idx = self.cb_by.findText(locator)
                self.cb_by.setCurrentIndex(locator_combo_idx)

                self.edt_bCommandTarget.setText(command_target)
                self.edt_bCommandValue.setText(value)
                self.edt_frame.setText(frame)
                self.cb_autoEnter.setChecked(auto_enter)
                self.sb_bCommandWaitSec.setValue(wait_sec)

                if step_type in ['Grid Click', 'Grid Double Click', 'Grid Type']:
                    column = self.step.get('column')
                    row_index = self.step.get('row_index')
                    self.edt_column.setText(str(column))

                    if type(row_index) == int:
                        method_combo_idx = self.cb_rowMethod.findText("Fix")
                        self.cb_rowMethod.setCurrentIndex(method_combo_idx)
                        self.sb_rowIndex.setValue(row_index)
                    else:
                        self.sw_rowIndex.setCurrentIndex(1)
                        method_combo_idx = self.cb_rowMethod.findText("By Value")
                        self.cb_rowMethod.setCurrentIndex(method_combo_idx)

                        row_index_column = row_index["column"]
                        row_index_value = row_index["value"]

                        self.sb_rowIndexColumn.setValue(row_index_column)
                        self.edt_rowIndexColumnValue.setText(row_index_value)

            elif step_type == 'Alert':
                activity = self.step.get('activity')

                if activity == 'Accept':
                    self.rb_accept.setChecked(True)
                else:
                    self.rb_dismiss.setChecked(True)
        elif step_type == 'IF':
            variable = self.step.get('variable')
            operator = self.step.get('operator')
            value = self.step.get('value')

            self.edt_ifVariable.setText(variable)
            operator_combo_idx = self.cb_operator.findText(operator)
            self.cb_operator.setCurrentIndex(operator_combo_idx)
            self.edt_value.setText(value)
        elif step_type == 'Validation':
            sql_name = self.step.get('sql_name')
            session = self.step.get('session')
            query = self.step.get('query')
            validation_chk = self.step.get('validation_chk')

            self.tmp_session = session
            self.tmp_query = query

            self.edt_queryNm.setText(sql_name)
            self.edt_sid.setText(session.id + ' @ ' + session.sid)

            if validation_chk == 'Data Exists':
                self.rb_validationExists.setChecked(True)
            elif validation_chk == 'Data Not Exists':
                self.rb_validationNotExists.setChecked(True)
            elif validation_chk == 'Output Value Check':
                self.rb_validationOutputChk.setChecked(True)
        elif step_type == 'SMS':
            text = self.step.get('text')
            callback_num = self.step.get('callback_num')
            mobile_num_list = self.step.get('mobile_num_list')

            self.edt_smsText.setText(text)
            self.edt_sender.setText(callback_num)

            self.tw_mobileList.clearContents()
            self.tw_mobileList.setRowCount(len(mobile_num_list))

            for idx, mobile_num in enumerate(mobile_num_list):
                self.tw_mobileList.setItem(idx, 0, QTableWidgetItem(mobile_num))


    def _checkValue(self):
        '''
        저장 전 Step Value 체크
        :return: (bool) True
        '''
        if self.step_type == 'XHR':
            if self.edt_xhrTarget.text() == '':
                QMessageBox.information(self, "Add Step", "Target을 입력하세요")
                self.edt_xhrTarget.setFocus()
                return False

            # if self.edt_xhrTargetNm.text() == '':
            #     QMessageBox.information(self, "Add Step", "Target명을 입력하세요")
            #     self.edt_xhrTargetNm.setFocus()
            #     return False
        elif self.step_type == 'Open Browser':
            if self.edt_browserNm.text() == '':
                QMessageBox.information(self, "Add Step", "Browser명을 입력하세요")
                self.edt_browserNm.setFocus()
                return False

            browser_step_list = self.case.findStepByType(self.step_type, key='browser_nm')

            if self.callGubun == 'New' and len(browser_step_list) > 0:
                if self.edt_browserNm.text() in browser_step_list:
                    QMessageBox.information(self, "Add Step", "동일한 Browser명이 존재합니다")
                    self.edt_browserNm.setFocus()
                    return False
        elif self.step_type_group in ['Browser Command', 'Browser Command (Swing)']:
            if self.cb_browser.currentText() == '':
                QMessageBox.information(self, "Add Step", "Browser를 선택하세요")
                self.cb_browser.setFocus()
                return False
        elif self.step_type == 'Validation':
            if self.tmp_query is None:
                QMessageBox.information(self, "Add Step", "SQL정보가 없습니다.")
                self.btn_sqlDialog.setFocus()
                return False
            elif self.edt_queryNm.text() == '':
                QMessageBox.information(self, "Add Step", "SQL명을 입력하세요")
                self.edt_queryNm.setFocus()
                return False
        elif self.step_type == 'SMS':
            mobile_list = []

            for idx in range(self.tw_mobileList.rowCount()):
                message_item = self.tw_mobileList.item(idx, 0)
                if message_item:
                    message_text = message_item.text()

                    if message_text:
                        mobile_list.append(message_text)

            if self.edt_smsText.text() == '':
                QMessageBox.information(self, "Add Step", "메세지 내용이 없습니다")
                self.edt_smsText.setFocus()
                return False
            elif self.edt_sender.text() == '':
                QMessageBox.information(self, "Add Step", "발신번호 정보가 없습니다")
                self.edt_sender.setFocus()
                return False
            elif len(mobile_list) == 0:
                QMessageBox.information(self, "Add Step", "수신번호 정보가 없습니다")
                self.tw_mobileList.setFocus()
                return False

        return True


    def _setStep(self, step):
        '''
        Step 생성
        :param step: (class) step
        :return: (class) step
        '''
        step['group'] = self.edt_group.text()
        step['error_option'] = self.cb_errOption.currentText()
        step['condition_step_id'] = self.condition_step_id
        step['description'] = self.edt_description.text()

        if self.step_type == 'XHR':
            step['target'] = self.edt_xhrTarget.text()
            step['target_nm'] = self.edt_xhrTargetNm.text()

        elif self.step_type == 'Sleep':
            step['target'] = 'Sleep ({}Sec)'.format(self.sp_sec.value())
            step['description'] = '{} Sec.'.format(self.sp_sec.value())
            step['sec'] = self.sp_sec.value()
        elif self.step_type_group == 'Browser':
            step['activity'] = self.step_type
            step['step_type_group'] = self.step_type_group

            if self.step_type == 'Open Browser':
                step['browser_nm'] = self.edt_browserNm.text()
                step['sid'] = self.cb_sid.currentText()

                if self.cb_sid.currentText() == 'URL':
                    step['description'] = '{}'.format(self.edt_url.toPlainText())
                    step['url'] = self.edt_url.toPlainText()
                else:
                    step['description'] = 'URL 시작 및 탐색'
            elif self.step_type == 'Refresh Browser':
                browser_step = self.case.findStepByType('Open Browser', key='browser_nm', value=self.cb_reloadBrowser.currentText())[0]
                step['browser_step_id'] = browser_step.getId()
                step['description'] = 'Browser 새로고침'

        elif self.step_type_group in ['Browser Command', 'Browser Command (Swing)']:
            browser_step = self.case.findStepByType('Open Browser', key='browser_nm', value=self.cb_browser.currentText())[0]
            step['browser_step_id'] = browser_step.getId()
            step['command'] = self.step_type
            step['step_type_group'] = self.step_type_group

            if self.step_type == 'open':
                step['description'] = 'URL 이동'
                step['url'] = self.edt_getUrl.toPlainText()
            elif self.step_type == 'Switch to Frame':
                step['description'] = '프레임 전환'
                step['locator'] = self.cb_by.currentText()
                step['command_target'] = self.edt_bCommandTarget.text()
                step['wait_sec'] = self.sb_bCommandWaitSec.value()
                step['frame'] = self.edt_frame.text()
            elif self.step_type == 'Switch to Default':
                step['description'] = '부모 창 프레임으로 다시 전환'
            elif self.step_type == 'Execute Script':
                step['locator'] = self.cb_by.currentText()
                step['command_target'] = self.edt_bCommandTarget.text()
                step['wait_sec'] = self.sb_bCommandWaitSec.value()
                step['frame'] = self.edt_frame.text()
                step['value'] = self.edt_bCommandValue.text()
            elif self.step_type == 'Alert':
                step['description'] = '알림창 확인'
                step['activity'] = 'Accept' if self.rb_accept.isChecked() else 'Dismiss'
            else:
                step['locator'] = self.cb_by.currentText()
                step['command_target'] = self.edt_bCommandTarget.text()
                step['wait_sec'] = self.sb_bCommandWaitSec.value()
                step['frame'] = self.edt_frame.text()

                if self.step_type in ['Type', 'Grid Type', 'Combo Click']:
                    step['value'] = self.edt_bCommandValue.text()
                    step['auto_enter'] = self.cb_autoEnter.isChecked()
                
                if self.step_type in ['Grid Click', 'Grid Double Click', 'Grid Type']:
                    row_method = self.cb_rowMethod.currentText()
                    step['column'] = self.edt_column.text()

                    if row_method == 'Fix':
                        row_index = self.sb_rowIndex.value()
                    else:
                        row_index_column = self.sb_rowIndexColumn.value()
                        row_index_value = self.edt_rowIndexColumnValue.text()
                        row_index = {'column': row_index_column, 'value': row_index_value}

                    step['row_index'] = row_index

        elif self.step_type == 'IF':
            step['target'] = 'IF {variable} {operator} {value}'.format(variable=self.edt_ifVariable.text(), operator=self.cb_operator.currentText(), value=self.edt_value.text())

            if self.edt_description.text() == '':
                step['description'] = '조건 만족 시 수행 할 Step을 추가하세요'

            step['variable'] = self.edt_ifVariable.text()
            step['operator'] = self.cb_operator.currentText()
            step['value'] = self.edt_value.text()

            step.clearCondition()
            step.setCondition(self.edt_ifVariable.text(), self.cb_operator.currentText(), self.edt_value.text())

        elif self.step_type == 'Validation':
            validation_chk = ''

            step['sql_name'] = self.edt_queryNm.text()
            step['sid'] = self.edt_sid.text()
            step['session'] = self.tmp_session
            step['query'] = self.tmp_query

            if self.rb_validationExists.isChecked():
                validation_chk = 'Data Exists'
            elif self.rb_validationNotExists.isChecked():
                validation_chk = 'Data Not Exists'
            elif self.rb_validationOutputChk.isChecked():
                validation_chk = 'Output Value Check'

            step['validation_chk'] = validation_chk

            if self.edt_description.text() == '':
                step['description'] = 'DATA 검증'
        elif self.step_type == 'SMS':
            mobile_list = []

            for idx in range(self.tw_mobileList.rowCount()):
                message_item = self.tw_mobileList.item(idx, 0)
                if message_item:
                    message_text = message_item.text()

                    if message_text:
                        mobile_list.append(message_text)

            step['text'] = self.edt_smsText.text()
            step['callback_num'] = self.edt_sender.text()
            step['mobile_num_list'] = mobile_list

            if self.edt_description.text() == '':
                step['description'] = 'SMS 발송'

        return step


    def popUp(self):
        if self.callGubun == 'New':
            self.edt_group.setText(self.group)

            if self.condition_step_id:
                err_option_combo_idx = self.cb_errOption.findText("Skip")
                self.cb_errOption.setCurrentIndex(err_option_combo_idx)
                self.cb_errOption.setEnabled(False)

        else:
            self._setUiValue()
            self.edt_description.setFocus()

        self.exec_()


    def accept(self):
        if self.sw_typeDtl.currentIndex() == 0:
            QMessageBox.information(self, "Add Step", "현재 지원되지 않는 Step Type입니다.")
        elif self.sw_typeDtl.currentIndex() == 1:
            QMessageBox.information(self, "Add Step", "Step Type을 선택하세요.")
        else:
            if self._checkValue():
                if self.callGubun == 'New':
                    if self.step_type == 'XHR':
                        step = Xhr(case=self.case, step_type=self.step_type)
                    elif self.step_type == 'Sleep':
                        step = Sleep(case=self.case, step_type=self.step_type)
                    elif self.step_type_group == 'Browser':
                        step = Browser(case=self.case, step_type=self.step_type)
                    elif self.step_type_group in ['Browser Command', 'Browser Command (Swing)']:
                        step = BrowserCommand(case=self.case, step_type=self.step_type)
                    elif self.step_type == 'IF':
                        step = If(case=self.case, step_type=self.step_type)
                    elif self.step_type_group == 'Database':
                        step = Database(case=self.case, step_type=self.step_type)
                    elif self.step_type == 'SMS':
                        step = Message(case=self.case, step_type=self.step_type)
                    else:
                        QMessageBox.information(self, "Add Step", "현재 지원되지 않는 Step Type입니다.")
                        return False

                    step = self._setStep(step)
                    self.added.emit(step, self.index)
                else:
                    self._setStep(self.step)
                    self.changed.emit()
                self.close()