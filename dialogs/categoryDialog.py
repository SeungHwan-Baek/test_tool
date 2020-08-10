import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

from utils.lib import addTreeRoot, addTreeChild

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/category_dialog.ui"))[0]

class CategoryDialog(QDialog, dig_class):
    selected = pyqtSignal(str, str)

    appname = 'Category Dialog'

    def __init__(self, suites):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self.suites = suites
        self._loadUiInit()
        self._setEvent()

    def _loadUiInit(self):
        self.tw_category.hideColumn(1)  # Category ID


    def _setEvent(self):
        # ToolBar 버튼 이벤트
        self.action_addCategory.triggered.connect(self.addCategoryClicked)                   # 메뉴 - Add Category

        # Tree 이벤트
        self.tw_category.customContextMenuRequested.connect(self.setCategoryContextMenu)     # Context Menu 설정
        self.tw_category.itemDoubleClicked.connect(self.twCategoryItemDoubleClicked)         # Category Item Double Clicked 이벤트

        # Button Click 이벤트
        self.btn_expandAll.clicked.connect(self._btnExpandAll)                               # expand All 버튼 클릭 이벤트
        self.btn_collapseAll.clicked.connect(self._btnCollapseAll)                           # collapse All 버튼 클릭 이벤트
        self.btn_addCategory.clicked.connect(self.addCategoryClicked)                        # add Category 버튼 클릭 이벤트


    def _btnExpandAll(self):
        self.tw_category.expandAll()


    def _btnCollapseAll(self):
        self.tw_category.collapseAll()


    def accept(self):
        item = self.tw_category.currentItem()

        category_name = item.text(0)
        category_id = item.text(1)

        self.selected.emit(category_name, category_id)
        self.close()

    def popUp(self, category_id=''):
        self._setCategoryView(category_id)
        self.exec_()

    def setCategoryContextMenu(self, pos):
        index = self.tw_category.indexAt(pos)

        menu = QMenu()

        if not index.isValid():
            self.tw_category.clearSelection()

        menu.addAction(self.action_addCategory)
        menu.exec_(self.tw_category.mapToGlobal(pos))


    def twCategoryItemDoubleClicked(self, item):
        category_name = item.text(0)
        category_id = item.text(1)

        self.selected.emit(category_name, category_id)
        self.close()


    def _setCategoryView(self, category_id):
        category = self.suites.getCategory(copy=True)

        new_category_list = []

        if category:
            category_font = QFont('맑은 고딕', 10)
            #category_font.setBold(True)

            while True:
                '''
                category 리스트 순서상 Parent category보다 앞에 있는 경우 오류가 발생하여
                exception 발생 시 리스트의 뒤로 보내고 수행함
                category Tree 구성 후 category 새로운 리스트(순서변경됨)로 suites에 저장
                '''
                categoryInfo = category.pop(0)
                try:
                    if categoryInfo['parent_category_id']:
                        parent_node = self.tw_category.findItems(categoryInfo['parent_category_id'], Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]
                        child_node = addTreeChild(parent=parent_node, text=categoryInfo['category_name'], check=False)
                        child_node.setText(1, categoryInfo['category_id'])
                        child_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                        child_node.setForeground(0, Qt.cyan)
                        child_node.setFont(0, category_font)

                        expanded = self.suites.getCategoryInfo(categoryInfo['category_id'], 'expanded', False)
                        child_node.setExpanded(expanded)
                    else:
                        root_node = addTreeRoot(treeWidget=self.tw_category, idx=0, text=categoryInfo['category_name'], check=False)
                        root_node.setText(1, categoryInfo['category_id'])
                        root_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                        root_node.setForeground(0, Qt.cyan)
                        root_node.setFont(0, category_font)

                        expanded = self.suites.getCategoryInfo(categoryInfo['category_id'], 'expanded', False)
                        root_node.setExpanded(expanded)
                    new_category_list.append(categoryInfo)
                except IndexError:
                    category.append(categoryInfo)

                if not category:
                    break

            self.suites.category = new_category_list

            if category_id:
                self.tw_category.expandAll()
                selected_node = self.tw_category.findItems(category_id, Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]
                selected_node.setSelected(True)


    def addCategoryClicked(self):
        category, ok = QInputDialog.getText(self, 'Category 추가', 'Category 명을 입력하세요.')

        if ok and category:
            parent_category_id = ''
            selectedNode = None

            for item in self.tw_category.selectedItems():
                parentNode = item.parent()
                selectedNode = item

            if selectedNode is not None:
                parent_category_id = selectedNode.text(1)

            find_category = self.suites.findCategory(category, parent_category_id)

            if find_category:
                QMessageBox.information(self, "Category 추가", "동일한 Category가 존재합니다.")

                return False
            else:
                categoryInfo = self.suites.addCategory(category, parent_category_id)

                if parent_category_id:
                    parent_node = self.tw_category.findItems(categoryInfo['parent_category_id'], Qt.MatchExactly | Qt.MatchRecursive, column=1)[0]
                    child_node = addTreeChild(parent=parent_node, text=categoryInfo['category_name'], check=False)
                    child_node.setText(1, categoryInfo['category_id'])
                    child_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                    child_node.setForeground(0, Qt.cyan)
                    child_node.setFont(0, QFont('맑은 고딕'))
                    child_node.setSelected(True)
                    self.tw_category.setCurrentItem(child_node)
                else:
                    root_node = addTreeRoot(treeWidget=self.tw_category, idx=0, text=categoryInfo['category_name'], check=False)
                    root_node.setText(1, categoryInfo['category_id'])
                    root_node.setIcon(0, QIcon(':/case/' + 'open_folder.png'))
                    root_node.setForeground(0, Qt.cyan)
                    root_node.setFont(0, QFont('맑은 고딕'))
                    root_node.setSelected(True)
                    self.tw_category.setCurrentItem(root_node)

                QMessageBox.information(self, "Category 추가", "[{}] Category를 추가하였습니다.".format(categoryInfo['category_name']))

                return categoryInfo
        else:
            return False
