# -*- coding: utf-8 -*-
'''
logDialog.py
utils/logWorker.py
widgets/logTextWidget.py

UI/log_dialog.ui
'''
import sys, os

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(parentDir)

import time
import socket
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore, QtGui
from PyQt5.Qsci import QsciScintillaBase

from utils.logWorker import LogThread, LogMultiThread
from widgets.logTextWidget import LogTextWidget


form_class = uic.loadUiType(os.path.join(parentDir, "UI/log_dialog.ui"))[0]

class LogDialog(QMainWindow, form_class):
    log_text = {}
    log_tree = {}
    tot_cnt = 0
    cur_cnt = 0
    reset = 0

    def __init__(self):
        super().__init__()

        self.setupUi(self)

        ip_addr = socket.gethostbyname(socket.getfqdn())

        self.ipEdit.setText(ip_addr)
        self.trEdit.setText("ZORDSS0400380_TR01")
        self.curcnt.setText("0")
        self.totcnt.setText("0")

        self.ip = ''
        self.tp = ''

        self.log_text = {}
        self.log_tree = {}
        self.tot_cnt = 0
        self.cur_cnt = 0
        self.reset = 0
        self.lastStart = 0
        self.thread_cnt = 10
        self.therad_worker_list = []

        self._loadUiInit()
        self._setEvent()


    def _loadUiInit(self):
        '''
        UI 초기설정
        :return: None
        '''
        self.edt_logView = LogTextWidget()
        self.edt_logView.findText.connect(self.setFindText)
        self.log_layout.addWidget(self.edt_logView)

        self.tw_logTree.hideColumn(1)  # Line
        self.tw_logTree.hideColumn(2)  # end time
        self.tw_logTree.setColumnWidth(0, 250)  # function Name 컬럼 폭 강제 조절
        self.tw_logTree.setColumnWidth(3, 150)  # 프로그램명 컬럼 폭 강제 조절

        self.splitter_tree_view.setSizes([350, 650])


    def _setEvent(self):
        '''
        Component Event Connect
        :return: None
        '''
        self.btn_findPrevious.clicked.connect(lambda: self.findText(forward=False))  # Tbl 이전 Search 버튼선택
        self.btn_findNext.clicked.connect(lambda: self.findText(forward=True))  # Tbl 이후 Search 버튼선택
        self.errBtn.clicked.connect(self.errBtnFunction)  # Tbl (E) 버튼선택 --> 에러로그만 조회
        self.edt_searchLogView.textChanged.connect(self.searchLogViewTextChanged)  # Log View 검색 Edit 변경

        self.twBtn.clicked.connect(self.twBtnFunction)  # tree Search 버튼선택
        self.tw_logTree.itemClicked.connect(self.twClkFunction)  # tree 선택 이벤트
        self.collpsBtn.clicked.connect(self.collpsBtnFunction)  # tree ▲ 버튼 이벤트
        self.expndBtn.clicked.connect(self.expndBtnFunction)  # tree ▼ 버튼 이벤트

        self.pageBtn.clicked.connect(self.pageBtnClkFunction)  # pageBtn 클릭 이벤트
        self.searchBtn.clicked.connect(self.searchBtnClkFunction)  # searchBtn 클릭 이벤트


    def initComponent(self):
        '''
        UI Componet 초기화
            - 조회 시
        :return: None
        '''
        self.tw_logTree.clear()     # 트리화면 초기화
        self.edt_logView.clear()    # 텍스트화면 초기화
        self.edt_guid.clear()       # GUID 초기화
        self.curcnt.setText("0")    # Current Count 초기화
        self.totcnt.setText("0")    # Total Count 초기화

        self.pageBtn.setEnabled(False)


    def setTransactionInfo(self, trx_code, ip_addr):
        '''
        Popup으로 호출 시 Argument Setting
        :param trx_code: (str) 'ZORDSS0400380_TR01'
        :param ip_addr: (str) '150.28.79.196'
        :return:
        '''
        self.ipEdit.setText(ip_addr)
        self.trEdit.setText(trx_code)


    # ============================ View ============================
    def setTableWidgetData(self, log_text):
        '''
        Log View append
        :return: None
        '''
        arg = self.edt_logView.text()

        for tree in log_text:
            arg += tree["log_type"] + ':' + '{0:<10}'.format(tree["line"]) + ':  ' + ('{0:<12}'.format(tree["time"])).rstrip() + ':  ' + ('{0:<50}'.format(tree["src_id"])).rstrip() + ':  ' + (
                      '{0:<100}'.format(tree["func_id"])).rstrip() + ':  ' + ('{0:<1124}'.format(tree["log_string"]).rstrip()) + '\n'

        self.edt_logView.setText(arg)
        pass


    def setTreeWidgetData(self):
        '''
        Log Tree 그리기
        :return: None
        '''
        dic = {}
        for tree in self.log_tree["output2"]:
            display_value = tree["display_value"]
            split_display_value = display_value.split(']')
            elapsed_time = split_display_value[0].replace("[", "")
            split_function = split_display_value[1].split('(')
            function_name = split_function[0]
            source_file_name = split_function[1].replace(")", "")


            if tree["level"] == "1":
                item = QTreeWidgetItem(self.tw_logTree)
            else:
                cnt = tree["key_value"].rfind("-")
                item = QTreeWidgetItem(dic.get(tree["key_value"][0:cnt]))

            item.setText(0, function_name)
            item.setText(1, tree["line"])
            item.setText(2, tree["start_time"])
            item.setText(3, source_file_name)
            item.setText(4, elapsed_time)
            dic[tree["key_value"]] = item


    def setEnabledComponent(self, enabled):
        '''
        Component 활설화/비활성화
        :param enabled: (bool) True
        :return: None
        '''
        self.grp_searchInfo.setEnabled(enabled)
        self.grp_logTree.setEnabled(enabled)
        self.grp_logView.setEnabled(enabled)

    # ============================ Thread ============================
    def searchBtnClkFunction(self):
        '''
        로그조회 (실행버튼 클릭)
            - Log Tree 조회 (Thread)
        :return: None
        '''
        self.ip = self.ipEdit.text()
        self.tp = self.trEdit.text()

        self.initComponent()
        self.setEnabledComponent(False)

        self.progressDialog = QProgressDialog()
        self.progressDialog.setWindowTitle('Log 조회')
        self.progressDialog.setLabelText('Log Tree 조회중...')
        self.progressDialog.setCancelButton(None)
        self.progressDialog.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)
        self.progressDialog.show()
        self.progressDialog.setRange(0, 0)

        self.logTreeWorker = LogThread(ip=self.ip, tp=self.tp)
        self.logTreeWorker.logTreeFinished.connect(self._logTreeSearchFinished)
        self.logTreeWorker.logViewFinished.connect(self._logViewSearchFinished)
        self.logTreeWorker.start()


        # # 첫페이지 로그조회 호출
        # self.log_tree, self.log_text = utils.search.tpcall(ip, tp)
        #
        # for tree in self.log_tree["output2"]:
        #     self.tot_cnt = tree["total_cnt"]
        #     break
        #
        # for tree in self.log_text["output1"]:
        #     self.cur_cnt = tree["cur_cnt"]
        #     break
        #
        # cnt = divmod(int(self.tot_cnt), int(self.cur_cnt))
        # self.curcnt.setText("1")
        #
        # if cnt[1] == 0:
        #     self.totcnt.setText(str(cnt[0]))
        # else:
        #     self.totcnt.setText(str(cnt[0] + 1))
        #
        # self.setTreeWidgetData()  # Tree Widget 그리기
        # self.setTableWidgetData()  # Tbl Widget 그리기

    def _logTreeSearchFinished(self, log_tree, tot_cnt, guid):
        print(log_tree)

        self.log_tree = log_tree

        if tot_cnt > 0:
            self.tot_cnt = tot_cnt

            print('다음 조회 시작 - [{}]번 조회 필요'.format(self.tot_cnt))
            self.progressDialog.setLabelText('Log 상세 조회중...')
            self.totcnt.setText(str(self.tot_cnt))
            self.edt_guid.setText(guid)
        else:
            self.progressDialog.setRange(0, 100)
            self.progressDialog.hide()

            QMessageBox.information(self, "Log 조회", "조회된 결과가 없습니다.")

            self.setEnabledComponent(True)


    def _logViewSearchFinished(self, log_view, page):
        #print(log_view)

        # Tree Widget 그리기
        self.setTreeWidgetData()

        self.curcnt.setText(str(page))

        self.log_text = log_view
        self.setTableWidgetData(log_view["output1"])

        self.progressDialog.setRange(0, 100)
        self.progressDialog.hide()

        self.setEnabledComponent(True)

        # 추가적으로 조회 할 로그가 남아 있는 경우만 활성화
        if int(self.curcnt.text()) < int(self.totcnt.text()):
            self.pageBtn.setEnabled(True)


    def pageBtnClkFunction(self):
        '''
        페이지 모두 가져오기 버튼 클릭 시 발생 이벤트
        :return: None
        '''
        self.progressDialog.show()
        self.progressDialog.setRange(0, 100)

        rem_page_list = list(range(1, self.tot_cnt))
        thread_list = self.chunkList(rem_page_list, thread_cnt=self.thread_cnt)

        print(thread_list)

        self.setEnabledComponent(False)

        self.log_view_tmp = []
        self.complete_cnt = 1

        for idx, icnt_list in enumerate(thread_list):
            worker_index = idx + 1
            setattr(self, 'logMultiWorker_{}'.format(worker_index), LogMultiThread(ip=self.ip, tp=self.tp, guid=self.edt_guid.text(), icnt_list=icnt_list))
            getattr(self, "logMultiWorker_{}".format(worker_index)).logViewFinished.connect(self._logViewMultiSearchFinished)
            getattr(self, "logMultiWorker_{}".format(worker_index)).logPagingFinished.connect(self._logViewMultiSearchPagingFinished)
            getattr(self, "logMultiWorker_{}".format(worker_index)).start()  # Thread 실행

            self.therad_worker_list.append(getattr(self, "logMultiWorker_{}".format(worker_index)))
            
        # self.logTreeWorker.start()
        
        # start_time = time.time()
        # totlog = utils.thread.tpcall(self.tot_cnt, self.cur_cnt, self.ipEdit.text(), self.trEdit.text())
        # sdict = sorted(totlog.items())
        #
        # for tree in sdict:
        #     arg = tree["log_type"] + ':' + '{0:<10}'.format(tree["line"]) + ':  ' + (
        #         '{0:<50}'.format(tree["src_id"])).rstrip() + ':  ' + (
        #               '{0:<100}'.format(tree["func_id"])).rstrip() + ':  ' + (
        #               '{0:<1124}'.format(tree["log_string"]).rstrip())
        #     self.edt_logView.append(arg)
        #print("--- text 그리는 시간 time %s seconds ---" % (time.time() - start_time))

        #self.curcnt.setText(self.totcnt.text())

    def _logViewMultiSearchPagingFinished(self):
        self.complete_cnt += 1
        per = ((self.complete_cnt) / (self.tot_cnt) * 100)
        self.progressDialog.setValue(per)


    def _logViewMultiSearchFinished(self, log_view):
        sender = self.sender()

        print(sender.icnt_list)

        self.log_view_tmp.extend(log_view)

        try:
            self.therad_worker_list.remove(sender)
        except ValueError:
            pass

        if self.therad_worker_list:
            pass
        else:
            #print(self.log_view_tmp)
            print('조회완료')
            start_time = time.time()
            self.log_view_tmp = [dict(y) for y in set(tuple(x.items()) for x in self.log_view_tmp)]
            print("--- 중복제거 time [%s] seconds ---" % (time.time() - start_time))

            start_time = time.time()
            self.log_view_tmp = sorted(self.log_view_tmp, key=lambda log: (int(log['time'])))
            print("--- 정렬 time [%s] seconds ---" % (time.time() - start_time))

            start_time = time.time()
            self.setTableWidgetData(self.log_view_tmp)

            self.curcnt.setText(str(self.complete_cnt))

            print("--- Text Append time [%s] seconds ---" % (time.time() - start_time))

            self.progressDialog.hide()
            self.setEnabledComponent(True)

            QMessageBox.information(self, "Complete", "Log 조회가 완료되었습니다.")

    # ============================ Component Event ============================
    # tree 선택시 event
    def twClkFunction(self):
        query = ':' + '{0:<10}'.format(self.tw_logTree.currentItem().text(1)) + ':  ' + ('{0:<12}'.format(self.tw_logTree.currentItem().text(2))).rstrip()
        self.setFocusByText(query, 0, 0)

        # self.lastStart = 0
        # text = self.edt_logView.text()

        # self.lastStart = text.find(query, 0)
        # end = self.lastStart + len(query)
        # self.moveCursor(self.lastStart - 3, end)


    def moveCursor(self, start, end):
        cursor = self.edt_logView.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
        self.edt_logView.setTextCursor(cursor)


    # tree > 버튼선택시 event
    def twnxtBtnFunction(self):
        QMessageBox.warning(self, 'Message', '준비중')


    # tree Search 버튼선택시 event
    def twBtnFunction(self):
        if self.reset != 0:
            for item in self.reset:
                item.setBackground(0, QtGui.QColor("white"))

        self.tw_logTree.expandAll()
        items = self.tw_logTree.findItems(self.twLine.text(), QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        self.reset = items

        for item in items:
            item.setBackground(0, QtGui.QColor("orange"))


    # tree ▲ 버튼 event --> tree 전체 접기
    def collpsBtnFunction(self):
        self.tw_logTree.collapseAll()


    # tree ▼ 버튼 event --> tree 전체 펼치기
    def expndBtnFunction(self):
        self.tw_logTree.expandAll()


    # text (E) 버튼 event --> 에러로그 찾는 기능
    def errBtnFunction(self):
        text_to_find = '(E)'
        self.setFocusByText(text_to_find)

        # text = self.edt_logView.toPlainText()
        # query = '(E)'
        # self.lastStart = text.find(query, self.lastStart + 1)
        #
        # if self.lastStart >= 0:
        #     self.moveFind(self.lastStart, text.find('\n', self.lastStart + 1))
        # else:
        #     self.lastStart = 0
        #     self.moveFind(0, 0)


    def searchLogViewTextChanged(self, text_to_find):
        '''
        log view search edit에 text 변경 시 발생 이벤트
            - 입력한 텍스트를 포함한 위치에 highlight 하기 위함
        :param text_to_find: (str) 'ordss08s0020t01.c'
        :return: None
        '''
        #text_to_find = self.edt_searchLogView.text()

        lastLine = self.edt_logView.lines() - 1
        self.edt_logView.clearIndicatorRange(0, 0, lastLine, len(self.edt_logView.text(lastLine)) - 1, 0)

        log = self.edt_logView.text()

        # 문자열을 Byte로 변환 (한글이 존재하는 경우 위치오류를 수정하기 위해)
        log = log.encode()
        text_to_find = text_to_find.encode()

        try:
            end = log.rindex(text_to_find)
        except ValueError:
            end = -1

        cur = -1

        self.edt_logView.SendScintilla(QsciScintillaBase.SCI_INDICSETSTYLE, 0, QsciScintillaBase.INDIC_ROUNDBOX)
        self.edt_logView.SendScintilla(QsciScintillaBase.SCI_INDICSETFORE, 0, QtGui.QColor(Qt.yellow))

        if end > -1:
            while(cur!=end):
                cur = log.index(text_to_find, cur + 1)
                self.edt_logView.SendScintilla(QsciScintillaBase.SCI_INDICATORFILLRANGE, cur, len(text_to_find))


    # TextEdit Search 단어 찾아 커서 이동
    # def moveFind(self, start, end):
    #     cursor = self.edt_logView.textCursor()
    #     cursor.setPosition(start)
    #     cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, end - start)
    #     self.edt_logView.setTextCursor(cursor)


    def setFindText(self, text):
        '''
        LogTextWidget에서 findText Signal을 받은 경우 수행되는 이벤트
        :param text: (str) 'usg_eqp_mdl_cd'
        :return: None
        '''
        self.edt_searchLogView.setText(text)
        self.edt_searchLogView.setFocus()


    def findText(self, forward):
        '''
        검색 수행 이벤트
        :param forward: (bool) True
        :return: None
        '''
        text_to_find = self.edt_searchLogView.text()

        if forward:
            line, index = self.edt_logView.getSelection()[2:]
        else:
            line, index = self.edt_logView.getSelection()[:2]

        state_ = (
            self.re.isChecked(), self.cs.isChecked(),
            self.wo.isChecked(), self.wrap.isChecked(),
            forward, line, index,
            self.show_.isChecked(), self.posix.isChecked(),
        )

        self.text_to_find = text_to_find
        self.state_ = state_
        self.edt_logView.findFirst(text_to_find, *state_)


    def setFocusByText(self, text_to_find, line=-1, index=-1):
        '''
        text_to_find 에 해당하는 위치로 이동하기 위한 이벤트 (보완 필요)
            - 로그 트리에서 function 클릭 시 해당 위치로 이동
            - 에러 로그 위치로 이동
        :param text_to_find: (str) ':239       :  ordss08s0020t01.c:'
        :param line: (int) 0
        :param index: (int) 0
        :return: None
        '''
        if line == -1 and index == -1:
            line, index = self.edt_logView.getSelection()[2:]

        state_ = (
            False, True,
            False, True,
            True, line, index,
            False, False,
        )

        self.text_to_find = text_to_find
        self.state_ = state_
        self.edt_logView.findFirst(text_to_find, *state_)


    def chunkList(self, case_list, thread_cnt):
        resultList = [case_list[i::thread_cnt] for i in range(thread_cnt)]
        # 빈리스트는 삭제
        resultList = [x for x in resultList if x]
        return resultList

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = LogDialog()
    myWindow.show()
    app.exec_()