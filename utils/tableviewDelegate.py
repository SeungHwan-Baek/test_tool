from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class ComboDelegate(QItemDelegate):
    editorItems=['Fixed value', 'DataList','SQL']
    height = 25
    width = 200
    def createEditor(self, parent, option, index):
        editor = QListWidget(parent)
        # editor.addItems(self.editorItems)
        # editor.setEditable(True)
        editor.currentItemChanged.connect(self.currentItemChanged)
        return editor

    def setEditorData(self,editor,index):
        z = 0
        for item in self.editorItems:
            ai = QListWidgetItem(item)
            editor.addItem(ai)
            if item == index.data():
                editor.setCurrentItem(editor.item(z))
            z += 1
        editor.setGeometry(0,index.row()*self.height,self.width,self.height*len(self.editorItems))

    def setModelData(self, editor, model, index):
        editorIndex=editor.currentIndex()
        text=editor.currentItem().text()
        model.setData(index, text, None)
        # print '\t\t\t ...setModelData() 1', text

    @pyqtSlot()
    def currentItemChanged(self):
        self.commitData.emit(self.sender())

class CheckBoxDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox cell of the column to which it's applied.
    """
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        self.drawCheck(painter, option, option.rect, Qt.Unchecked if int(index.data()) == 0 else Qt.Checked)

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable. Otherwise do nothing.
        '''
        if not int(index.flags() & Qt.ItemIsEditable) > 0:
            return False

        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            # Change the checkbox-state
            self.setModelData(None, model, index)
            return True

        return False

    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        model.setData(index, 1 if int(index.data()) == 0 else 0, Qt.EditRole)


class ImageDelegate(QItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        #painter.fillRect(option.rect, QColor(191, 222, 185))
        if int(index.data()) == 1:
            path = "UI\\icon\\insert.png"
            #painter.fillRect(option.rect, QColor(53, 65, 99))
        elif int(index.data()) == 2:
            path = "UI\\icon\\update_insert.png"
            #painter.fillRect(option.rect, QColor(53, 65, 99))
        else:
            path = ""

        #image = QImage(str(path))
        #pixmap = QPixmap.fromImage(image)
        #pixmap.scaled(20, 20, QtCore.Qt.KeepAspectRatio)
        #painter.drawPixmap(option.rect, pixmap)
        icon = QIcon(path)
        icon.paint(painter, option.rect, Qt.AlignCenter)
        #painter.fillRect(option.rect, QColor(QtCore.Qt.darkRed))