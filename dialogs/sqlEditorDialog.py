import os
import copy

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from widgets.sqlEditorWidget import SqlEditorWidget


parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/sql_editor_dialog.ui"))[0]

class SqlEditorDialog(QDialog, dig_class):
    saved = pyqtSignal(str, "PyQt_PyObject", "PyQt_PyObject")

    appname = 'SQL Editor'

    def __init__(self, case=None, step_seq=-1):
        super().__init__()

        self.case = case
        self.step_seq = step_seq
        self.sql_name = ''

        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self._loadUiInit()


    def _loadUiInit(self):
        self.sql_editor_widget = SqlEditorWidget(self.case, self.step_seq)
        self.sql_layout.addWidget(self.sql_editor_widget)

    def accept(self):
        if self._checkValue():
            query = self.sql_editor_widget.getQuery()
            session = self.sql_editor_widget.getSession()
            self.sql_editor_widget.saveModel()
            self.saved.emit(self.sql_name, session, query)

            try:
                self.sql_editor_widget.tw_bind.itemChanged.disconnect(self._twBindCurrentItemChanged)
            except:
                pass

            self.close()

    def popUp(self, sql_name='', session=None, query=None, show=False):
        self.session = copy.deepcopy(session)
        self.query = copy.copy(query)

        if sql_name:
            self.sql_name = sql_name
            self.appname = '({name}) {appname}'.format(name=sql_name, appname=self.appname)
            self.setWindowTitle(self.appname)

        if session:
            self.sql_editor_widget.addSession(self.session)

        if query:
            self.sql_editor_widget.setQuery(self.query)

        if show:
            self.show()
        else:
            self.exec_()


    def _checkValue(self):
        query = self.sql_editor_widget.getQuery()
        session = self.sql_editor_widget.getSession()

        if not session:
            QMessageBox.information(self, self.appname, "Session 정보가 없습니다.")
            return False

        if not query:
            QMessageBox.information(self, self.appname, "Test Query 수행 후 저장이 가능합니다.")
            return False

        return True