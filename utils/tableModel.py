import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal

currentDir = os.path.dirname(os.path.realpath(__file__))
parentDir = os.path.normpath(os.path.join(currentDir, ".."))

class PandasModel(QAbstractTableModel):
    fixedList = []
    dataList = []
    sql = []
    excel = []
    rowlevel = []

    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.step = None
        self.changedDataIndex = []
        self.dataChanged.connect(self.setChangedDataIndex)
        self.headerIcon = False
        self.editabled = False

    def setChangedDataIndex(self, a, b):
        self.changedDataIndex.append((a.row(), a.column()))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if self.headerIcon:
            if orientation == Qt.Horizontal:
                col = self._data.columns[section]

                if role == Qt.DecorationRole:
                    header_icon = ''

                    if col in self.fixedList:
                        header_icon = os.path.join(parentDir, 'UI/icon/nail.png')
                    elif col in self.dataList:
                        header_icon = os.path.join(parentDir, 'UI/icon/link.png')
                    elif col in self.sql:
                        header_icon = os.path.join(parentDir, 'UI/icon/sql.png')
                    elif col in self.excel:
                        header_icon = os.path.join(parentDir, 'UI/icon/excel.png')

                    if header_icon:
                        return QVariant(QPixmap(header_icon).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

                if role == Qt.ToolTipRole:
                    tooltip = ''

                    if col in self.fixedList:
                        tooltip = '고정값'
                    elif col in self.dataList:
                        tooltip = 'DataList 참조'
                    elif col in self.sql:
                        tooltip = 'SQL'
                    elif col in self.excel:
                        tooltip = 'Excel'

                    return tooltip

        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            try:
                return self._data.columns.tolist()[section]
            except (IndexError, ):
                return QVariant()
        if orientation == Qt.Vertical:
            try:
                return QVariant(str(section+1))
            except (IndexError, ):
                return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        col = self._data.columns[index.column()]
        #data, changed = self._data.iloc[index.row()][index.column()]
        changed = (index.row(), index.column()) in self.changedDataIndex

        try:
            if role == Qt.EditRole:
                return QVariant(str(self._data.iloc[index.row(), index.column()]))
            elif role == Qt.ForegroundRole:
                ref = self.step.getIsRef(self.data_list_id, index.row(), col)
                var = self.step.getIsVar(self.data_list_id, index.row(), col)
                if ref == 'Unlink' or var == 'Unlink':
                    return QBrush(Qt.red)
                elif ref == 'Link':
                    return QBrush(Qt.darkGray)
                elif changed:
                    return QBrush(Qt.red)
            elif role == Qt.DecorationRole:
                ref = self.step.getIsRef(self.data_list_id, index.row(), col)
                var = self.step.getIsVar(self.data_list_id, index.row(), col)
                icon = ''

                if ref == 'Link' and var == 'Link':
                    icon = QIcon(':/variable/' + 'var_and_link.png')
                elif ref == 'Link' and var == 'Unlink':
                    icon = QIcon(':/variable/' + 'unvar_and_link.png')
                elif ref == 'Unlink' and var == 'Link':
                    icon = QIcon(':/variable/' + 'var_and_unlink.png')
                elif ref == 'Unlink' and var == 'Unlink':
                    icon = QIcon(':/variable/' + 'unvar_and_unlink.png')
                elif ref == 'Link':
                    icon = QIcon(':/ref/' + 'link.png')
                elif ref == 'Unlink':
                    icon = QIcon(':/ref/' + 'unlink.png')
                elif var == 'Link':
                    icon = QIcon(':/variable/' + 'var.png')
                elif var == 'Unlink':
                    icon = QIcon(':/variable/' + 'unvar.png')

                return icon
            #elif role == Qt.ForegroundRole:
            #    return QBrush(Qt.darkGray)
            # elif role == Qt.ForegroundRole and self.diff_mask is not None and self.diff_mask.iloc[index.row(), index.column()]:
            #     return QBrush(Qt.red)
            # elif role == Qt.BackgroundColorRole and self.target_diff and index.row() in self.sync:
            #     if self.style == "Dark (Default)":
            #         return QBrush(QColor(53, 65, 99))
            #     else:
            #         return QBrush(QColor(210, 225, 255))
            elif role != Qt.DisplayRole:
                return QVariant()

            if not index.isValid():
                return QVariant()

            if self.headerIcon and col not in self.fixedList:
                return QVariant('(Ref) ' + str(self._data.iloc[index.row(), index.column()]))
            else:
                return QVariant(str(self._data.iloc[index.row(), index.column()]))
        except:
            print('data error')

    def setData(self, index, value, role):
        row = self._data.index[index.row()]
        col = self._data.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            value = value.toPyObject()
        else:
            dtype = self._data[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)

        if self._data.loc[row, col] != value:
            #self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0))
            self._data.loc[row, col] = value
            self.dataChanged.emit(index, index)

        return True

    def rowCount(self, parent=None):
        return len(self._data.index)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def sort(self, column, order):
        colname = self._data.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._data.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def flags(self, index):
        col = self._data.columns[index.column()]

        if self.editabled:
            return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def getData(self, index):
        return str(self._data.iloc[index.row(), index.column()])

    def getColumnId(self, index):
        return self._data.columns[index.column()]

    def getColumnIndex(self, column_id):
        try:
            index = list(self._data.columns).index(column_id)
        except ValueError:
            index = -1
        return index

    def getHeader(self, section):
        return self._data.columns.tolist()[section]

    def setEditable(self, editabled):
        self.editabled = editabled

    def setStep(self, step, data_list_id):
        self.step = step
        self.data_list_id = data_list_id


class CheckPandasModel(QAbstractTableModel):

    def __init__(self, data, parent=None, style="Dark (Default)"):
        QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.style = style
        self.header_icon = None
        self.chk_enable = True

        topLeft = self.index(0, 0)
        bottomRight = self.index(self.rowCount(), 0)
        #self.setHeaderIcon()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        try:
            if role != Qt.DisplayRole:
                return QVariant()

            col = self._data.columns[section]
            #print(col)

            if orientation == Qt.Horizontal and role == Qt.DecorationRole:
                if col == 'CHECK':
                    return QVariant(QPixmap(self.header_icon).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return self._data.columns.tolist()[section]

        except (IndexError, ):
            return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        col = self._data.columns[index.column()]

        try:
            if role == Qt.EditRole:
                return QVariant(str(self._data.iloc[index.row(), index.column()]))
            elif role == Qt.ForegroundRole and col == 'Used' and self._data.iloc[index.row(), index.column()] == 1:
                return QBrush(Qt.red)
            elif role != Qt.DisplayRole:
                return QVariant()

            if not index.isValid():
                return QVariant()
            return QVariant(str(self._data.iloc[index.row(), index.column()]))
        except:
            print('data error')

    def setData(self, index, value, role):
        try:
            row = self._data.index[index.row()]
            col = self._data.columns[index.column()]

            if hasattr(value, 'toPyObject'):
                value = value.toPyObject()
            else:
                dtype = self._data[col].dtype
                if dtype != object:
                    value = None if value == '' else dtype.type(value)
            #self._data.set_value(row, col, value)
            if self._data.loc[row, col] != value:
                self._data.loc[row, col] = value
                self.dataChanged.emit(index, index)

            if role == Qt.CheckStateRole and col == 'CHECK':
                if value == Qt.Checked:
                    self._data.loc[row, 'CHECK'] = 1
                else:
                    self._data.loc[row, 'CHECK'] = 0
                #self.setHeaderIcon()
            return True
        except:
            print('setData error')

    def rowCount(self, parent=None):
        return len(self._data.index)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def sort(self, column, order):
        colname = self._data.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._data.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def flags(self, index):
        try:
            #if not index.isValid():
            #    return None

            col = self._data.columns[index.column()]
            row = self._data.index[index.row()]

            if col == 'Used':
                if self.chk_enable:
                    return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
                else:
                    return Qt.NoItemFlags
            else:
                return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        except:
            print('flags error')

    def setting(self, chk_enable=True):
        self.chk_enable = chk_enable

    def setHeaderIcon(self):
        if self._data['CHECK'].all():
            self.header_icon = os.path.join(parentDir, 'UI/icon/checked.png')
        elif self._data['CHECK'].any():
            self.header_icon = os.path.join(parentDir, 'UI/icon/intermediate.png')
        else:
            self.header_icon = os.path.join(parentDir, 'UI/icon/unchecked.png')
        self.headerDataChanged.emit(Qt.Horizontal, 0, 0)

    def toggleCheckState(self, index):
        col = self._data.columns[index]

        if col == 'CHECK':
            if self._data['CHECK'].any():
                self._data['CHECK'] = 0
            else:
                self._data['CHECK'] = 1

            # NOT EXISTS ROW 선택불가
            for idx in range(len(self._data)):
                if idx in self.not_exist_row:
                    self._data.loc[idx, 'CHECK'] = 0

            topLeft = self.index(0, 0)
            bottomRight = self.index(self.rowCount(), 0)
            self.dataChanged.emit(topLeft, bottomRight)
            #self.setHeaderIcon()