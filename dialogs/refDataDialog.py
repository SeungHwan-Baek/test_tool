import os
import pandas as pd
import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from libs.reference import Reference
from utils.tableModel import PandasModel
from utils.lib import addTreeRoot, addTreeChild, makeVariableId
from widgets.refExcelDataWidget import RefExcelDataWidget
from widgets.sqlEditorWidget import SqlEditorWidget
from dialogs.sqlEditorDialog import SqlEditorDialog

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException


parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/ref_list.ui"))[0]

class RefDataDialog(QDialog, dig_class):
    changed = pyqtSignal()

    appname = 'Reference Excel'
    HOME = os.path.expanduser("~")
    LOAD_PATH = os.path.join(HOME, 'Test_Tool')

    refDataList = []
    find_element_list = []
    selectedRef = None

    def __init__(self, suites, web):
        super().__init__()
        self.suites = suites
        self.web = web

        self.setupUi(self)
        self.setWindowTitle(self.appname)

        self.refDataList = []
        self.find_element_list = []

        self.selectedRef = None

        self.action_reload.triggered.connect(self.reloadClicked)                              # 메뉴 - Reload
        self.action_remove.triggered.connect(self.removeClicked)                              # 메뉴 - Remove

        # Context Menu 설정
        self.tw_refList.customContextMenuRequested.connect(self.setRefListContextMenu)

        # Tree Item Change 이벤트
        self.tw_refList.itemSelectionChanged.connect(self.twRefListItemSelectionChanged)      # Ref List Item Selection Changed 이벤트

        # Button 클릭 이벤트
        self.btn_loadRefData.clicked.connect(self.btnLoadRefDataClicked)                      # Load Ref Data 버튼 클릭
        self.btn_addRefData.clicked.connect(self.btnAddRefDataClicked)                        # Add Ref Data 버튼 클릭
        self.btn_addRow.clicked.connect(self.btnAddRowClicked)                                # Add Row 버튼 클릭
        self.btn_removeRow.clicked.connect(self.btnRemoveRowClicked)                          # Remove Row 버튼 클릭
        self.btn_saveRefInfo.clicked.connect(self.btnSaveRefInfoClicked)                      # Save Svc Combo 버튼 클릭

        self.chk_stayOnTop.clicked.connect(self.chkStayOnTopClicked)

        self.edt_filter.textChanged.connect(self.test)

        self.tw_svcCombo.currentChanged = self._twSvcComboCurrentChanged

        self.tw_svcCombo.doubleClicked.connect(self._twSvcComboDoubleClicked)


    def _twSvcComboCurrentChanged(self, current, previous):
        col = current.column()

        if col == -1:
            self.edt_oparamVariableID.clear()
            self.edt_oparamDesc.clear()
            self.edt_oparamVariableID.setEnabled(False)
            self.edt_oparamDesc.setEnabled(False)
        else:
            oparam_variable_id = self.selectedRef.get('oparam{}_variable_id'.format(col+1))
            oparam_desc = self.selectedRef.get('oparam{}_desc'.format(col + 1))
            self.edt_oparamVariableID.setEnabled(True)
            self.edt_oparamDesc.setEnabled(True)
            self.edt_oparamVariableID.setText(oparam_variable_id)
            self.edt_oparamDesc.setText(oparam_desc)

    def _twSvcComboDoubleClicked(self, index):
        '''
        SVC COMBO Table View 더블클릭 이벤트
            - Web 이 열려있고 Input에 Focus 되어 있다면 index에 해당하는 Table View 값을 화면에 Setting
        :param index: (QModelIndex)
        :return: None
        '''
        self.find_element_list = []

        if self.web:
            driver = self.web.getDriver()

            try:
                driver.switch_to.default_content()
            except WebDriverException:
                self.web = None
                return False

            self.findSelectElements()
            self.find_element_list = sorted(self.find_element_list, key=lambda k: k['full_frame'], reverse=True)
            element_id = self.switchFrame()

            if self.web and element_id:
                data_model = self.tw_svcCombo.model()
                value = data_model.getData(index)
                driver.execute_script("document.getElementById('{id}').value='{value}'".format(id=element_id, value=value))


    def test(self, input):
        selectTreeItem = self.tw_refList.findItems(input, Qt.MatchContains | Qt.MatchRecursive, column=0)
        print(len(selectTreeItem))


    def accept(self):
        self.save(self.refDataList)
        self.close()


    def popUp(self):
        self.load()
        self._loadUiInit()
        #self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()
        #self.exec_()


    def _loadUiInit(self):
        self.btn_saveRefInfo.hide()
        self.tw_refList.hideColumn(1)  # ref_id

        self.setRefListVeiw()
        self.setRefExcelView()

        self.sql_widget = SqlEditorWidget()
        self.sql_layout.addWidget(self.sql_widget)
        self.sql_widget.sessionChanged.connect(self._sqlSessionChanged)
        self.sql_widget.queryChanged.connect(self._sqlQueryChanged)


    def findRefIndex(self, ref_id):
        try :
            index = next(idx for idx, ref in enumerate(self.refDataList) if ref.getId() == ref_id)
        except:
            index = -1
        return index


    def findRef(self, ref_id):
        index = self.findRefIndex(ref_id)
        if index == -1:
            self.selectedRef = None
        else:
            self.selectedRef = self.refDataList[index]

        return self.selectedRef


    def reloadClicked(self):
        parentNode = None

        for item in self.tw_refList.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is not None:
            ref_nm = parentNode.text(0)
            ref_id = selectedNode.text(1)

            index = self.findDictIndexByValue(self.refDataList, 'ref_id', ref_id)
            ref = self.refDataList[index]
            ref_type = ref.getType()

            if ref_type == 'Excel':
                old_ref = self.refDataList.pop(index)
                self.setExcelView(ref.get('file_path'))
            elif ref_type =='SVC COMBO (Swing Only)':
                ref.getXhrSvcCombo()
                self._setSvcComboResultView(ref)


    def removeClicked(self):
        parentNode = None

        for item in self.tw_refList.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is not None:
            ref_method = parentNode.text(0)
            ref_nm = selectedNode.text(0)
            ref_id = selectedNode.text(1)

            index = self.findDictIndexByValue(self.refDataList, 'ref_id', ref_id)

            reply = QMessageBox.question(self, 'Remove Reference', "[{ref_method}] '{ref_nm}'을 삭제하시겠습니까?".format(ref_method=ref_method, ref_nm=ref_nm), QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.refDataList.pop(index)
                self.setRefListVeiw()


    def setRefListContextMenu(self, pos):
        parentNode = None

        for item in self.tw_refList.selectedItems():
            parentNode = item.parent()

        if parentNode is not None:
            index = self.tw_refList.indexAt(pos)

            menu = QMenu()

            if not index.isValid():
                pass
            else:
                if pos:
                    menu.addAction(self.action_reload)
                    menu.addAction(self.action_remove)
                    menu.exec_(self.tw_refList.mapToGlobal(pos))


    def setRefExcelView(self):
        self.tab_excel.clear()

        if self.selectedRef is not None:
            for idx, excelInfo in enumerate(self.selectedRef.get('data')):
                sheet = excelInfo['sheet']
                df = pd.DataFrame.from_dict(excelInfo['value'])
                self.addTab(sheet, df)


    def setRefListVeiw(self, ref_id=''):
        self.tw_refList.clear()

        svc_combo_node = addTreeRoot(treeWidget=self.tw_refList, idx=0, text='SVC COMBO (Swing Only)', check=False)
        excel_node = addTreeRoot(treeWidget=self.tw_refList, idx=0, text='Excel', check=False)
        sql_node = addTreeRoot(treeWidget=self.tw_refList, idx=0, text='SQL', check=False)

        svc_combo_node.setForeground(0, QColor(255, 99, 71))
        excel_node.setForeground(0, QColor(255, 99, 71))
        sql_node.setForeground(0, QColor(255, 99, 71))

        for refInfo in self.refDataList:
            if refInfo.getType() == 'Excel':
                file_node = addTreeChild(parent=excel_node, text=refInfo.get('name'), check=False)
                file_node.setText(1, refInfo.getId())
            elif refInfo.getType() == 'SVC COMBO (Swing Only)':
                file_node = addTreeChild(parent=svc_combo_node, text=refInfo.get('name'), check=False)
                file_node.setText(1, refInfo.getId())
            elif refInfo.getType() == 'SQL':
                file_node = addTreeChild(parent=sql_node, text=refInfo.get('name'), check=False)
                file_node.setText(1, refInfo.getId())

        self.tw_refList.expandToDepth(0)

        if ref_id:
            selectTreeItem = self.tw_refList.findItems(ref_id, Qt.MatchExactly | Qt.MatchRecursive, column=1)

            if selectTreeItem:
                self.tw_refList.setCurrentItem(selectTreeItem[0])
            else:
                # select the root item
                self.tw_refList.setCurrentItem(self.tw_refList.topLevelItem(0))


    def _setSvcComboResultView(self, ref):
        if ref.getType() == 'SVC COMBO (Swing Only)':
            step = ref.get('target')

            if step:
                data = step.getDataList('output1', return_type='dataframe')

                if data is not None:
                    data_model = PandasModel(data)
                    data_model.setStep(step, 'output1')
                    self.tw_svcCombo.setModel(data_model)
                else:
                    none_Df = pd.DataFrame()
                    none_model = PandasModel(none_Df)
                    self.tw_svcCombo.setModel(none_model)
            else:
                none_Df = pd.DataFrame()
                none_model = PandasModel(none_Df)
                self.tw_svcCombo.setModel(none_model)


    def twRefListItemSelectionChanged(self):
        type = ''
        parentNode = None
        selectedNode = None

        for item in self.tw_refList.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is not None:
            type = parentNode.text(0)
            file = selectedNode.text(0)
            ref_id = selectedNode.text(1)

            self.selectedRef = self.findRef(ref_id)
        else:
            self.selectedRef = None

            #if selectedNode:
            #    type = selectedNode.text(0)

        if type == 'SVC COMBO (Swing Only)':
            self.sw_dataDtl.setCurrentIndex(3)
            self.edt_refDbioName.setText(self.selectedRef.get('name'))
            self.edt_mapId.setText(self.selectedRef.get('map_id'))
            self.edt_iparam1.setText(self.selectedRef.get('iparam1'))
            self.edt_iparam2.setText(self.selectedRef.get('iparam2'))
            self.edt_iparam3.setText(self.selectedRef.get('iparam3'))
            self.edt_iparam4.setText(self.selectedRef.get('iparam4'))
            self.edt_iparam5.setText(self.selectedRef.get('iparam5'))

            self._setSvcComboResultView(self.selectedRef)
        elif type == 'Excel':
            self.sw_dataDtl.setCurrentIndex(1)
            self.setRefExcelView()
        elif type == 'SQL':
            self.sw_dataDtl.setCurrentIndex(2)
            self.edt_refSqlName.setText(self.selectedRef.get('name'))
            self.sql_widget.addSession(self.selectedRef.get('session'))
            self.sql_widget.setQuery(self.selectedRef.get('query'))
        else:
            self.sw_dataDtl.setCurrentIndex(0)



    def btnLoadRefDataClicked(self):
        fd = QFileDialog(self)
        filename = fd.getOpenFileName(self, '%s - Load Reference' % self.appname, self.LOAD_PATH, 'Suites Files(*.att)')
        filePath = filename[0]

        if filePath:
            with open(filePath, 'rb') as f:
                unpickler = pickle.Unpickler(f)
                suites = unpickler.load()
                load_ref_data_list = suites.getRefDataList()

                for ref_data in load_ref_data_list:
                    self.refDataList.append(ref_data)

                # UI Setting
                self.setRefListVeiw(ref_data.getId())


    def btnAddRefDataClicked(self):
        parentNode = None
        selectedNode = None

        for item in self.tw_refList.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is not None:
            ref_method = parentNode.text(0)
        elif selectedNode is not None:
            ref_method = selectedNode.text(0)
        else:
            ref_method = ''

        if ref_method == 'SVC COMBO (Swing Only)':
            idx = 0
        elif ref_method == 'Excel':
            idx = 1
        elif ref_method == 'SQL':
            idx = 2
        else:
            idx = 0

        items = ("SVC COMBO (Swing Only)", "Excel", "SQL")
        ref_data_type, ok = QInputDialog.getItem(self, 'Select Type', '추가하는 Reference Data Type을 선택하세요.', items, idx, False)

        if ok and ref_data_type:
            if ref_data_type == 'SVC COMBO (Swing Only)':
                name, ok = QInputDialog.getText(self, 'SVC COMBO (Swing Only)', 'Reference Data Name을 입력하세요.')

                if ok and name:
                    ref_data = Reference('SVC COMBO (Swing Only)')
                    ref_data['name'] = name
                    ref_data['map_id'] = ''
                    ref_data['iparam1'] = ''
                    ref_data['iparam2'] = ''
                    ref_data['iparam3'] = ''
                    ref_data['iparam4'] = ''
                    ref_data['iparam5'] = ''
                    self.refDataList.append(ref_data)

                    # UI Setting
                    self.setRefListVeiw(ref_data.getId())

            elif ref_data_type == 'Excel':
                self._loadExcelClicked()
            elif ref_data_type == 'SQL':
                name, ok = QInputDialog.getText(self, 'SQL', 'Reference Data Name을 입력하세요.')

                if ok and name:
                    self.sqlEditorClicked(name)


    def _loadExcelClicked(self):
        fd = QFileDialog(self)
        filename = fd.getOpenFileName(self, '%s - Load Reference Excel File' % self.appname, self.LOAD_PATH, 'Excel Files(*.xlsx *.xlsm *.xlsb *.xlam *.xltx *.xltm *.xls *.xla *.xlt *.xlm *.xlw)')
        filePath = filename[0]

        if filePath:
            self.setExcelView(filePath)


    def sqlEditorClicked(self, name):
        sqlEditorDialog = SqlEditorDialog()
        sqlEditorDialog.saved.connect(self._sqlEditorSaved)
        sqlEditorDialog.popUp(name)
        
    def _sqlEditorSaved(self, name, session, query):
        ref_data = Reference('SQL')
        ref_data['name'] = name
        ref_data['session'] = session
        ref_data['query'] = query

        self.refDataList.append(ref_data)
        self.setRefListVeiw(ref_data.getId())


    def setExcelView(self, filePath):
        #try:
        xl = pd.ExcelFile(filePath)
        xl_sheets = xl.sheet_names

        ref_data_info = {}
        excel_data = []

        ''' Reference
        [{type : 'Excel',
          name : 'test_data (1)',
          real_file_name : 'test_data',
          file_path : 'C:/Users/Administrator/Test_Tool/test_data.xlsx'
          ref_id : 'xxxxx-xxxxx-xxxx-xxxx'
          data :  [{sheet : 'Sheet1', columns : [list], value : [{dict}]},
                   {sheet : 'Sheet2', columns : [list], value : [{dict}]}]    << -- excel_data
          }                                                                  << -- ref_data_info
         ]                                                                   << -- self.refDataList
        '''
        for sheet in xl_sheets:
            sheet_column = list(pd.read_excel(filePath, sheet_name=sheet).columns)
            if sheet_column:
                converter = {col: str for col in sheet_column}
                df_from_excel = pd.read_excel(filePath, converters=converter, sheet_name=sheet)
                df_from_excel.insert(loc=0, column='Used', value=0)

                dict_from_excel = df_from_excel.to_dict('records')

                sheet_data = {'sheet': sheet, 'columns': sheet_column, 'value': dict_from_excel}

                excel_data.append(sheet_data)

                # self.addTab(sheet_name=sheet, df=df_from_excel)

        name = os.path.splitext(os.path.basename(filePath))[0]
        real_file_name = os.path.splitext(os.path.basename(filePath))[0]

        findFileList = self.findRefDataByValue(self.refDataList, 'real_file_name', name)

        if len(findFileList) > 0:
            name = '{name} ({seq})'.format(name=name, seq=len(findFileList))

        ref_data = Reference('Excel')
        ref_data['name'] = name
        ref_data['real_file_name'] = real_file_name
        ref_data['file_path'] = filePath
        ref_data['data'] = excel_data

        self.refDataList.append(ref_data)

        # UI Setting
        self.setRefListVeiw(ref_data.getId())

        #print(self.refDataList)
        QMessageBox.information(self, "Load Excel File", "Load Complete")
        #except:
        #    print('Error : Load Excel Error')


    def btnAddRowClicked(self):
        refExcelDataWidget = self.tab_excel.currentWidget()
        indices = refExcelDataWidget.tw_excelData.selectionModel().selectedRows()

        refExcelDataWidget.addRow()
        '''
        # in case none selected or no table to select
        if len(indices) == 0:
            refExcelDataWidget.ref_excel_model.insertRows(0)
        else:
            for index in sorted(indices):
                refExcelDataWidget.ref_excel_model.insertRow(index)
        '''


    def btnRemoveRowClicked(self):
        refExcelDataWidget = self.tab_excel.currentWidget()
        tab_index = self.tab_excel.currentIndex()
        index = refExcelDataWidget.getIndex()
        row = index.row()

        if self.selectedRef is not None:
            excelInfo = self.selectedRef['data'][tab_index]
            excelInfo['value'].pop(row)
            df = pd.DataFrame.from_dict(excelInfo['value'])
            refExcelDataWidget.setDataFrame(df)
                #sheet = excelInfo['sheet']
                #df = pd.DataFrame.from_dict(excelInfo['value'])
                #self.addTab(sheet, df)


    def btnSaveRefInfoClicked(self):
        if self.selectedRef.getType() == 'SVC COMBO (Swing Only)':
            self.selectedRef['name'] = self.edt_refDbioName.text()
            self.selectedRef['map_id'] = self.edt_mapId.text()
            self.selectedRef['iparam1'] = self.edt_iparam1.text()
            self.selectedRef['iparam2'] = self.edt_iparam2.text()
            self.selectedRef['iparam3'] = self.edt_iparam3.text()
            self.selectedRef['iparam4'] = self.edt_iparam4.text()
            self.selectedRef['iparam5'] = self.edt_iparam5.text()

            index = self.tw_svcCombo.currentIndex()
            col = index.column()

            self.edt_oparamVariableID.setText(makeVariableId(self.edt_oparamVariableID.text()))
            self.selectedRef['oparam{}_variable_id'.format(col+1)] = self.edt_oparamVariableID.text()
            self.selectedRef['oparam{}_desc'.format(col + 1)] = self.edt_oparamDesc.text()

            item = self.tw_refList.currentItem()
            item.setText(0, self.edt_refDbioName.text())
        elif self.selectedRef.getType() == 'SQL':
            self.selectedRef['name'] = self.edt_refSqlName.text()
            item = self.tw_refList.currentItem()
            item.setText(0, self.edt_refSqlName.text())


    def addTab(self, sheet_name, df):
        #print(sheet_name)

        refExcelDataWidget = RefExcelDataWidget(sheet_name, df)
        refExcelDataWidget.dataChanged.connect(self.refDataChanged)
        #refExcelData.setModel()

        tab_index = self.tab_excel.addTab(refExcelDataWidget, sheet_name)
        #self.tab_excel.setCurrentIndex(tab_index)


    def load(self):
        self.refDataList = self.suites.getRefDataList()


    def save(self, ref_data):
        self.suites.setRefDataList(ref_data)


    def refDataChanged(self, sheet_name, ref_data):
        parentNode = None

        for item in self.tw_refList.selectedItems():
            parentNode = item.parent()
            selectedNode = item

        if parentNode is not None:
            ref_method = parentNode.text(0)
            ref_nm = selectedNode.text(0)
            ref_id = selectedNode.text(1)

            ref_index = self.findDictIndexByValue(self.refDataList, 'ref_id', ref_id)
            data_index = self.findDictIndexByValue(self.refDataList[ref_index]['data'], 'sheet', sheet_name)
            self.refDataList[ref_index]['data'][data_index]['value'] = ref_data


    def findRefDataByValue(self, data_list, key, value):
        resultList = []

        if type(data_list) == list:
            if data_list:
                resultList = list(filter(lambda data: data.get(key) == value, data_list))
        else:
            print('Type Error : {}'.format(type(data_list)))

        return resultList


    def findDictIndexByValue(self, data_list, key, value):
        index = -1

        if type(data_list) == list:
            '''
            [{key1:value1}, {key1:value2}]
            '''
            if data_list:
                try:
                    if key == 'ref_id':
                        index = next(idx for idx, row in enumerate(data_list) if row.getId() == value)
                    else:
                        index = next(idx for idx, row in enumerate(data_list) if row.get(key) == value)
                except StopIteration:
                    index = -1
        else:
            print('Type Error : {}'.format(type(data_list)))

        return index


    def _sqlSessionChanged(self, session):
        self.selectedRef['session'] = session

    def _sqlQueryChanged(self, query):
        self.selectedRef['query'] = query

    # ============================ Browser Event ============================
    def findSelectElements(self, driver=None, element=None, frame='top', full_frame='top'):
        if self.web:
            if driver is None:
                driver = self.web.getDriver()

            if element is None:
                element = driver.switch_to.active_element

            if element.tag_name == 'input':
                #print(frame + ' 존재')
                element_info = {'frame': frame, 'full_frame': full_frame, 'element': element}
                self.find_element_list.append(element_info)
                #print(element_info)
            else:
                iframes = driver.find_elements_by_tag_name('iframe')

                for iframe in iframes:

                    iframe_id = iframe.get_attribute('id')

                    if iframe_id:
                        tmp_full_frame = full_frame + '-' + iframe_id

                        WebDriverWait(driver, 0).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))
                        element = driver.switch_to.active_element
                        self.findSelectElements(driver, element, iframe_id, tmp_full_frame)
                        driver.switch_to.parent_frame()


    def switchFrame(self):
        '''
        다건의 element 중 원하는 frame으로 전환하기 위해 사용
            - 첫번째 element로 전환함
        :return: None
        '''
        if self.web:
            driver = self.web.getDriver()

        if len(self.find_element_list) > 0:
            index = 0
        else:
            index = -1

        if index > -1:
            element_info = self.find_element_list[index]
            full_frame = element_info['full_frame'].split('-')

            for frame in full_frame:
                if frame == 'top':
                    driver.switch_to.default_content()
                else:
                    WebDriverWait(driver, 0).until(EC.frame_to_be_available_and_switch_to_it((By.ID, frame)))

            element_id = element_info['element'].get_attribute('id')

            return element_id


    def chkStayOnTopClicked(self):
        if self.chk_stayOnTop.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.show()