import os
import cx_Oracle as oci
import pandas as pd
import sqlite3
from PyQt5.Qt import QAbstractTableModel, Qt
from PyQt5.QtCore import pyqtSignal


class QueryModel(QAbstractTableModel):
    executed = pyqtSignal(str, name='executed')
    connected = pyqtSignal(str, name='connected')
    disconnected = pyqtSignal()
    fetch_changed = pyqtSignal(bool, name='fetch_changed')

    def __init__(self):
        super().__init__()
        self.query = None
        self._headers = []
        self._data = []
        self._row_count = 0
        self._column_count = 0

    def execute(self, case=None):
         if self.query:
            self.query.execute(case)

            first_row = self.query.fetchOne()
            header_info = self.query.getHeaders()

            if first_row:
                # Fetch first row
                self.beginResetModel()
                #print('fetched first row')
                self._column_count = len(first_row)
                self._headers = header_info
                # print('headers:', self._headers)
                self._data = [first_row]
                self._row_count = 1
                self.endResetModel()
                #print('Must be 1 row here!')
                # Fetch additional rows
                self.fetch_more()
            else:
                # Try to read from Cursor.description if zero rows
                # returned
                self.beginResetModel()

                if header_info:
                    self._headers = header_info
                    # print('headers:', self._headers)
                    self._column_count = len(self._headers)
                    self._row_count = 0
                    self._data = []
                    self.endResetModel()
                    self.fetch_changed.emit(False)
                else:
                    self._headers = []
                    self._column_count = 0
                    self._row_count = 0
                    self._data = []
                    self.endResetModel()
                    # Disable further fetching
                    self.fetch_changed.emit(False)

            # print('data:', [tuple(r) for r in self._data])
            self.executed.emit('Executed')

    def fetch_more(self):
        limit = 100
        # Try to fetch more
        more = self.query.fetchMore(limit)
        print('fetched {} rows in fetch_more'.format(len(more)))

        if len(more) > 0:
            self.beginResetModel()
            count = self._row_count + len(more)
            print('fetched {} rows in total'.format(count))
            self._data.extend(more)
            self._row_count = count
            self.endResetModel()

            self.fetch_changed.emit(len(more) >= limit)

    def commit(self):
        con = self.session.getCon()
        con.commit()
        self.executed.emit('Committed')
        print('commit')

    def rollback(self):
        con = self.session.getCon()
        con.rollback()
        self.executed.emit('Rollback')
        print('rollback')

    def rowCount(self, parent):
        return self._row_count

    def columnCount(self, parent):
        return self._column_count

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if len(self._headers) > 0:
                return self._headers[section]

        return None

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        return None

    def getTnsInfo(self):
        print(os.environ['TNS_ADMIN'])

    def getColumns(self):
        return self._headers

    def setQuery(self, query):
        self.query = query
        self._headers = self.query.headers
        self._data = self.query.data
        self._row_count = self.query.row_count
        self._column_count = self.query.column_count

    def getRowCount(self):
        return self._row_count

    def getHeaderId(self, index):
        return self._headers[index]

    def getData(self, index):
        return str(self._data[index.row()][index.column()])