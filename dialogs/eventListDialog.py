import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from utils.lib import findTrName

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/event_list_dialog.ui"))[0]

class EventListDialog(QDialog, dig_class):
    requestSelected = pyqtSignal(list)
    changed = pyqtSignal()

    appname = 'Browser Event List'
    step = None

    def __init__(self):
        super().__init__()
        self.web = None
        self.request_list = []

        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self._loadUiInit()
        self._setEvent()


    def _loadUiInit(self):
        self.tw_requestList.setColumnWidth(0, 50)   # Check    컬럼 폭 강제 조절
        self.tw_requestList.setColumnWidth(1, 180)  # Trx_code 컬럼 폭 강제 조절
        self.tw_requestList.setColumnWidth(2, 230)  # Trx_name 컬럼 폭 강제 조절

        self.tw_uiEventList.setColumnWidth(0, 50)   # Check    컬럼 폭 강제 조절
        self.tw_uiEventList.setColumnWidth(1, 80)   # Event    컬럼 폭 강제 조절
        self.tw_uiEventList.setColumnWidth(2, 200)  # Frame    컬럼 폭 강제 조절
        self.tw_uiEventList.setColumnWidth(3, 180)  # Id       컬럼 폭 강제 조절

    def _setEvent(self):
        self.tab_event.currentChanged.connect(self._tabEventCurrentChanged)
        self.btn_reload.clicked.connect(self._btnReloadClicked)

    def _tabEventCurrentChanged(self):
        self.reloadEvent()

    def _btnReloadClicked(self):
        self.reloadEvent()

    def _setRequestListView(self):
        if self.web:
            self.request_list = self.web.getRequestHst()

            self.tw_requestList.clearContents()
            self.tw_requestList.setRowCount(len(self.request_list))

            for idx, request in enumerate(self.request_list):
                # Checkbox 설정
                chk = QCheckBox()
                chk_cell_widget = QWidget()
                chk_lay_out = QHBoxLayout(chk_cell_widget)
                chk_lay_out.addWidget(chk)
                chk_lay_out.setAlignment(Qt.AlignCenter)
                chk_lay_out.setContentsMargins(0, 0, 0, 0)
                chk_cell_widget.setLayout(chk_lay_out)
                chk_cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")

                tx_name = findTrName(request['trx_code'])
                input_data_list = ', '.join(sorted(list(request['input_data'].keys())))
                output_data_list = ', '.join(sorted(list(request['output_data'].keys())))
                self.tw_requestList.setCellWidget(idx, 0, chk_cell_widget)
                self.tw_requestList.setItem(idx, 1, QTableWidgetItem(request['trx_code']))
                self.tw_requestList.setItem(idx, 2, QTableWidgetItem(tx_name))
                self.tw_requestList.setItem(idx, 3, QTableWidgetItem(input_data_list))
                self.tw_requestList.setItem(idx, 4, QTableWidgetItem(output_data_list))


    def _setUiEventListView(self):
        if self.web:
            ui_event_list = self.web.getEventList()

            self.tw_uiEventList.clearContents()
            self.tw_uiEventList.setRowCount(len(ui_event_list))

            for idx, event in enumerate(ui_event_list):
                # Checkbox 설정
                chk = QCheckBox()
                chk_cell_widget = QWidget()
                chk_lay_out = QHBoxLayout(chk_cell_widget)
                chk_lay_out.addWidget(chk)
                chk_lay_out.setAlignment(Qt.AlignCenter)
                chk_lay_out.setContentsMargins(0, 0, 0, 0)
                chk_cell_widget.setLayout(chk_lay_out)
                chk_cell_widget.setStyleSheet("background-color: rgba(0,0,0,0%)")

                xy_pos = [str(pos) for pos in event[6]]
                position = ', '.join(xy_pos)

                self.tw_uiEventList.setCellWidget(idx, 0, chk_cell_widget)
                self.tw_uiEventList.setItem(idx, 1, QTableWidgetItem(event[1]))
                self.tw_uiEventList.setItem(idx, 2, QTableWidgetItem(event[2]))
                self.tw_uiEventList.setItem(idx, 3, QTableWidgetItem(event[3]))
                self.tw_uiEventList.setItem(idx, 4, QTableWidgetItem(event[5]))
                self.tw_uiEventList.setItem(idx, 5, QTableWidgetItem(position))

    def reloadEvent(self):
        if self.tab_event.currentIndex() == 0:
            self._setRequestListView()
        elif self.tab_event.currentIndex() == 1:
            self._setUiEventListView()

    def popUp(self, web):
        self.web = web
        self.reloadEvent()
        self.show()

    def accept(self):
        if self.tab_event.currentIndex() == 0:
            selectedRequestList = []
            for idx in range(self.tw_requestList.rowCount()):
                if self.tw_requestList.cellWidget(idx, 0).findChild(type(QCheckBox())).isChecked():
                    selectedRequestList.append(self.request_list[idx])

            self.requestSelected.emit(selectedRequestList)
            self.hide()

