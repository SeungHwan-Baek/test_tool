import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
import datetime

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/marking_data_dialog.ui"))[0]

class MarkingDataDialog(QDialog, dig_class):
    selected = pyqtSignal(str, str)

    appname = 'Marking Data Dialog'
    case = None
    step = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self._loadUiInit()
        self._setEvent()


    def _loadUiInit(self):
        self.splitter_marking_data.setSizes([500, 500])

        # TableWidget 사이즈 조정
        self.tw_testDataList.setColumnWidth(0, 80)   # 데이타 컬럼 폭 강제 조절
        self.tw_testDataList.setColumnWidth(1, 140)  # 시작시간 컬럼 폭 강제 조절
        self.tw_testDataList.setColumnWidth(2, 140)  # 종료시간 컬럼 폭 강제 조절

        self.tw_markingData.setColumnWidth(0, 150)   # Target 컬럼 폭 강제 조절
        self.tw_markingData.setColumnWidth(1, 80)    # DataList 컬럼 폭 강제 조절
        self.tw_markingData.setColumnWidth(2, 150)   # Column 컬럼 폭 강제 조절


    def _setEvent(self):
        self.tw_testDataList.itemSelectionChanged.connect(self.twTestDataItemSelectionChanged)  # Test Data List Item Selection Changed 이벤트


    def accept(self):
        self.close()


    def loadData(self, case):
        self.markingList = case.loadMaringData(case.caseId)
        self.setTestDataView()


    def popUp(self):
        self.exec_()


    def setTestDataView(self):
        self.tw_testDataList.clearContents()

        self.tw_testDataList.setRowCount(len(self.markingList))

        for idx, markingDataDtl in enumerate(self.markingList):
            test_data_name_item = QTableWidgetItem(markingDataDtl['test_data_name'])

            if markingDataDtl['result'] > 0:
                test_data_name_item.setIcon(QIcon(':/step/' + 'error.png'))
            elif markingDataDtl['result'] < 0:
                test_data_name_item.icon(0)
            else:
                test_data_name_item.setIcon(QIcon(':/step/' + 'correct.png'))

            self.tw_testDataList.setItem(idx, 0, QTableWidgetItem(test_data_name_item))
            self.tw_testDataList.setItem(idx, 1, QTableWidgetItem(markingDataDtl['start_time']))
            self.tw_testDataList.setItem(idx, 2, QTableWidgetItem(markingDataDtl['end_time']))
            self.tw_testDataList.setItem(idx, 4, QTableWidgetItem(markingDataDtl['result_msg']))

            if markingDataDtl['start_time'] and markingDataDtl['end_time']:
                start_date_time = datetime.datetime.strptime(markingDataDtl['start_time'], '%Y-%m-%d %H:%M:%S')
                end_date_time = datetime.datetime.strptime(markingDataDtl['end_time'], '%Y-%m-%d %H:%M:%S')

                time_delta = str(end_date_time - start_date_time)

                self.tw_testDataList.setItem(idx, 3, QTableWidgetItem(time_delta))

        self.tw_testDataList.selectRow(len(self.markingList)-1)


    def twTestDataItemSelectionChanged(self):
        index = self.tw_testDataList.currentRow()

        self.tw_markingData.clearContents()
        self.tw_markingData.setRowCount(0)

        if index > len(self.markingList)-1:
            index = len(self.markingList)-1

        if self.markingList:
            self.tw_markingData.setRowCount(len(self.markingList[index]['marking_data']))
            #print(self.refList)
            for idx, markingDataDtl in enumerate(self.markingList[index]['marking_data']):
                self.tw_markingData.setItem(idx, 0, QTableWidgetItem(markingDataDtl['target']))
                self.tw_markingData.setItem(idx, 1, QTableWidgetItem(markingDataDtl['dataList_id']))
                self.tw_markingData.setItem(idx, 2, QTableWidgetItem(markingDataDtl['column_id']))
                self.tw_markingData.setItem(idx, 3, QTableWidgetItem(markingDataDtl['value']))