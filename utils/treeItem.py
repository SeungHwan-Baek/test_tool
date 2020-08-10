from PyQt5 import QtCore

class Item:
    __slots__ = ('login', 'itemData', 'children', 'parent', 'check_state')

    def __init__(self, *args, parent=None):
        super().__init__()
        self.login = args[0]
        self.itemData = [''] + list(args)
        self.children = []
        self.parent = parent
        self.check_state = QtCore.Qt.Unchecked

        if parent is not None:
            self.parent.addChild(self)

    def addChild(self, child):
        self.children.append(child)
        child.parent = self

    def removeChild(self, row):
        child = self.children.pop(row)

    def child(self, row):
        try:
            return self.children[row]
        except IndexError:
            return self.children[-1]

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return len(self.itemData) + 1

    def setData(self, column, data):
        if column < 0 or column > len(self.itemData) - 1:
            return False
        self.itemData[column] = data
        return True

    def data(self, column):
        if self.parent.is_root():
            return self.login if column == 0 else ''
        return self.itemData[column] if column < len(self.itemData) else ''

    def checkState(self):
        return self.check_state

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)

    def is_root(self):
        return self.parent is None

    def __len__(self):
        return len(self.children)

    def __repr__(self):
        return "<Item: {}; Children count {}>".format(self.login, len(self.children))

    def __hash__(self):
        return hash(self.login)