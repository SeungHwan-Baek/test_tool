import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from utils.lib import findTrName
import libs.structure as structure

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/excluded_tr_dialog.ui"))[0]

class ExcludedTrDialog(QDialog, dig_class):
    changed = pyqtSignal(list)

    excludedTrList = []

    appname = 'Excluded Transaction Setting Dialog'

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)

        # TableWidget 사이즈 조정
        self.tw_excludedTr.setColumnWidth(0, 150)               # Transaction 컬럼 폭 강제 조절

        # Button 클릭 이벤트
        self.btn_add.clicked.connect(self.btnAddClicked)        # Add 버튼
        self.btn_remove.clicked.connect(self.btnRemoveClicked)  # Remove 버튼

    def accept(self):
        self.changed.emit(self.excludedTrList)
        self.close()

    def popUp(self, excluded_tr_list):
        self.excludedTrList = excluded_tr_list.copy()
        self.setValue()

        self.show()

    def setRefList(self, ref_list):
        self.refList = ref_list
        self.setValue()

    def setValue(self):
        self.tw_excludedTr.clearContents()

        self.tw_excludedTr.setRowCount(len(self.excludedTrList))
        #print(self.refList)
        for idx, trInfo in enumerate(self.excludedTrList):
            self.tw_excludedTr.setItem(idx, 0, QTableWidgetItem(trInfo['tr_id']))
            self.tw_excludedTr.setItem(idx, 1, QTableWidgetItem(trInfo['tr_name']))

    def btnAddClicked(self):
        transaction, ok = QInputDialog.getText(self, 'Excluded Transaction', '제외 할 Transaction을 입력하세요.')

        if ok and transaction:
            tr_name = findTrName(transaction)

            structure.excludedTrList(self.excludedTrList, transaction, tr_name)
            self.setValue()

    def btnRemoveClicked(self):
        row = self.tw_excludedTr.currentRow()
        self.excludedTrList.pop(row)
        self.setValue()