import pickle
import copy
import io
from PyQt5 import QtCore

class PyObjMime(QtCore.QMimeData):
    MIMETYPE = 'application/x-pyobj'

    def __init__(self, data=None):
        super().__init__()

        self.data = data
        if data is not None:
            # Try to pickle data
            try:
                pdata = pickle.dumps(data)
            except:
                return

            self.setData(self.MIMETYPE, pickle.dumps(data.__class__) + pdata)

    def itemInstance(self):
        if self.data is not None:
            return self.data
        i_o = io.StringIO(str(self.data(self.MIMETYPE)))
        try:
            pickle.load(i_o)
            return pickle.load(i_o)
        except:
            pass
        return None

class TreeModel(QtCore.QAbstractItemModel):
    header_labels = ["Column 1", "Column 2", "Column 3"]

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.header_labels[section]

    def itemFromIndex(self, index):
        if index.isValid():
            return index.internalPointer()
        return self.root

    def rowCount(self, index):
        item = self.itemFromIndex(index)
        return len(item)

    def columnCount(self, index):
        return len(self.header_labels)
        # item = self.itemFromIndex(index)
        # return item.columnCount()

    def flags(self, index):
        """
        Returns whether or not the current item is editable/selectable/etc.
        """
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        enabled = QtCore.Qt.NoItemFlags
        selectable = QtCore.Qt.NoItemFlags
        editable = QtCore.Qt.NoItemFlags
        draggable = QtCore.Qt.NoItemFlags
        droppable = QtCore.Qt.NoItemFlags
        checkable = QtCore.Qt.ItemIsUserCheckable

        item = index.internalPointer()

        if not item.is_root() and not item.parent.is_root():
            draggable = QtCore.Qt.ItemIsDragEnabled
            selectable = QtCore.Qt.ItemIsSelectable
            enabled = QtCore.Qt.ItemIsEnabled

        if item.parent.is_root():
            droppable = QtCore.Qt.ItemIsDropEnabled
            enabled = QtCore.Qt.ItemIsEnabled
        if index.column() == 8:
            editable = QtCore.Qt.ItemIsEditable

        # return our flags.
        return enabled | selectable | editable | draggable | droppable | checkable

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            item = self.itemFromIndex(index)
            return item.data(index.column())
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            return self.itemFromIndex(index).checkState()

    def index(self, row, column, parent):
        item = self.itemFromIndex(parent)
        if row < len(item):
            return self.createIndex(row, column, item.child(row))
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        item = self.itemFromIndex(index)
        parent = item.parent
        if parent == self.root:
            return QtCore.QModelIndex()
        return self.createIndex(parent.row(), 0, parent)

    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row + count - 1)
        parent = self.itemFromIndex(parentIndex)

        if not parent.is_root():
            for i in range(count):
                parent.removeChild(row)
        self.endRemoveRows()
        return True

    def mimeTypes(self):
        return ['application/x-pyobj']

    def mimeData(self, index):
        items = set(self.itemFromIndex(item) for item in index)
        mimedata = PyObjMime(items)
        return mimedata

    def dropMimeData(self, mimedata, action, row, column, parentIndex):
        item = mimedata.itemInstance()
        dropParent = self.itemFromIndex(parentIndex)
        itemCopy = copy.deepcopy(item)
        for child in itemCopy:
            dropParent.addChild(child)
        self.dataChanged.emit(parentIndex, parentIndex)
        return True

    def setCheckState(self):
        pass