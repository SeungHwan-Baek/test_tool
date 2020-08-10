# qtable로 기본조회 , 페이징 처리 완료.
# log_main2 파일로 수정, tp 호출 방식 변경 반영 (tree, log 각각 부른다.)
# -*- coding: utf-8 -*-
import utils.thread
import utils.search
import sys
import time
import re

from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore, QtGui

form_class = uic.loadUiType("UI/log_dialog.ui")[0]

class LogDialog(QMainWindow, form_class):
    textlog = {}
    treelog = {}
    tot_cnt = 0
    cur_cnt = 0
    reset = 0

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.ipEdit.setText("150.28.65.76")
        self.trEdit.setText("ZNGMSATH10010_TR01")
        self.curcnt.setText("0")
        self.totcnt.setText("0")

        self.textlog = {}
        self.treelog = {}
        self.tot_cnt = 0
        self.cur_cnt = 0
        self.reset = 0
        self.lastStart = 0

        self.tbBtn.clicked.connect(self.tbBtnFunction)  # Tbl Search 버튼선택
        self.errBtn.clicked.connect(self.errBtnFunction)  # Tbl (E) 버튼선택 --> 에러로그만 조회

        self.twBtn.clicked.connect(self.twBtnFunction)  # tree Search 버튼선택
        self.tw.itemClicked.connect(self.twClkFunction)  # tree 선택 이벤트
        self.collpsBtn.clicked.connect(self.collpsBtnFunction)  # tree ▲ 버튼 이벤트
        self.expndBtn.clicked.connect(self.expndBtnFunction)  # tree ▼ 버튼 이벤트

        self.pageBtn.clicked.connect(self.pageBtnClkFunction)  # pageBtn 클릭 이벤트
        self.searchBtn.clicked.connect(self.searchBtnClkFunction)  # searchBtn 클릭 이벤트

        self.tw.hideColumn(1)           # Line
        self.tw.setColumnWidth(0, 300)  # function Name 컬럼 폭 강제 조절

    def setTransactionInfo(self, trx_code, ip_addr):
        self.ipEdit.setText(ip_addr)
        self.trEdit.setText(trx_code)

    # tree 선택시 event
    def twClkFunction(self):
        self.lastStart = 0
        text = self.tb.toPlainText()
        query = ':' + self.tw.currentItem().text(1)
        self.lastStart = text.find(query, 0)
        end = self.lastStart + len(query)
        self.moveCursor(self.lastStart - 3, end)

    def moveCursor(self, start, end):
        cursor = self.tb.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
        self.tb.setTextCursor(cursor)

    # tree > 버튼선택시 event
    def twnxtBtnFunction(self):
        QMessageBox.warning(self, 'Message', '준비중')

    # tree Search 버튼선택시 event
    def twBtnFunction(self):
        if self.reset != 0:
            for item in self.reset:
                item.setBackground(0, QtGui.QColor("white"))

        self.tw.expandAll()
        items = self.tw.findItems(self.twLine.text(), QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        self.reset = items

        for item in items:
            item.setBackground(0, QtGui.QColor("orange"))

    # tree ▲ 버튼 event --> tree 전체 접기
    def collpsBtnFunction(self):
        self.tw.collapseAll()

    # tree ▼ 버튼 event --> tree 전체 펼치기
    def expndBtnFunction(self):
        self.tw.expandAll()

    # text (E) 버튼 event --> 에러로그 찾는 기능
    def errBtnFunction(self):
        text = self.tb.toPlainText()
        query = '(E)'
        self.lastStart = text.find(query, self.lastStart + 1)

        if self.lastStart >= 0:
            self.moveFind(self.lastStart, text.find('\n', self.lastStart + 1))
        else:
            self.lastStart = 0
            self.moveFind(0, 0)

    # TextEdit Search 버튼 클릭
    def tbBtnFunction(self):
        text = self.tb.toPlainText()
        query = self.tbLine.text()
        self.lastStart = text.find(query, self.lastStart + 1)

        if self.lastStart >= 0:
            end = self.lastStart + len(query)
            self.moveFind(self.lastStart, end)
        else:
            self.lastStart = 0
            self.moveFind(0, 0)

    # TextEdit Search 단어 찾아 커서 이동
    def moveFind(self, start, end):
        cursor = self.tb.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, end - start)
        self.tb.setTextCursor(cursor)

    # Text 그리기
    def setTableWidgetData(self):
        for tree in self.textlog["output1"]:
            arg = tree["log_type"] + ':' + '{0:<10}'.format(tree["line"]) + ':  ' + (
                '{0:<50}'.format(tree["src_id"])).rstrip() + ':  ' + (
                      '{0:<100}'.format(tree["func_id"])).rstrip() + ':  ' + (
                      '{0:<1124}'.format(tree["log_string"]).rstrip())
            self.tb.append(arg)

    # tree 그리기
    def setTreeWidgetData(self):
        dic = {}
        for tree in self.treelog["output2"]:
            display_value = tree["display_value"]
            split_display_value = display_value.split(']')
            elapsed_time = split_display_value[0].replace("[", "")
            function_name = split_display_value[1]

            if tree["level"] == "1":
                item = QTreeWidgetItem(self.tw)
            else:
                cnt = tree["key_value"].rfind("-")
                item = QTreeWidgetItem(dic.get(tree["key_value"][0:cnt]))

            item.setText(0, function_name)
            item.setText(1, tree["line"])
            item.setText(2, elapsed_time)
            dic[tree["key_value"]] = item

    # 로그조회 (실행버튼 클릭)
    def searchBtnClkFunction(self):
        ip = self.ipEdit.text()
        tp = self.trEdit.text()

        self.tw.clear()  # 트리화면 초기화
        self.tb.clear()  # 텍스트화면 초기화

        # 첫페이지 로그조회 호출
        self.treelog, self.textlog = utils.search.tpcall(ip, tp)

        for tree in self.treelog["output2"]:
            self.tot_cnt = tree["total_cnt"]
            break

        for tree in self.textlog["output1"]:
            self.cur_cnt = tree["cur_cnt"]
            break

        cnt = divmod(int(self.tot_cnt), int(self.cur_cnt))
        self.curcnt.setText("1")

        if cnt[1] == 0:
            self.totcnt.setText(str(cnt[0]))
        else:
            self.totcnt.setText(str(cnt[0] + 1))

        self.setTreeWidgetData()  # Tree Widget 그리기
        self.setTableWidgetData()  # Tbl Widget 그리기

    # 페이지 넘기면 나머지 모든 데이터 가져오기
    def pageBtnClkFunction(self):
        start_time = time.time()
        totlog = utils.thread.tpcall(self.tot_cnt, self.cur_cnt, self.ipEdit.text(), self.trEdit.text())
        sdict = sorted(totlog.items())

        for tree in sdict:
            arg = tree["log_type"] + ':' + '{0:<10}'.format(tree["line"]) + ':  ' + (
                '{0:<50}'.format(tree["src_id"])).rstrip() + ':  ' + (
                      '{0:<100}'.format(tree["func_id"])).rstrip() + ':  ' + (
                      '{0:<1124}'.format(tree["log_string"]).rstrip())
            self.tb.append(arg)
        print("--- text 그리는 시간 time %s seconds ---" % (time.time() - start_time))

        self.curcnt.setText(self.totcnt.text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = LogDialog()
    myWindow.show()
    app.exec_()