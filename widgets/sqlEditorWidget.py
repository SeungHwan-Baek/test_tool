import os
from functools import partial

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from libs.query import Query
from widgets.sqlTextWidget import SqlTextWidget
from utils.lib import tnsnameParser, sqlFindBindVar, sqlFindDml, makeVariableId, horizontalLayout
from utils.config import Config
from utils.queryModel import QueryModel
from dialogs.sessionDialog import SessionDialog
from dialogs.variableListDialog import VariableListDialog
import pandas as pd
import threading
from functools import partial

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/sql_editor_widget.ui"))[0]

class SqlEditorWidget(QWidget, dig_class):
    sessionChanged = pyqtSignal("PyQt_PyObject")
    queryChanged = pyqtSignal("PyQt_PyObject")

    appname = 'SQL EDITOR'
    sessionList = []
    session = None
    query = None
    case = None
    df = pd.DataFrame()

    def __init__(self, case=None, step_seq=-1):
        super().__init__()

        self.sessionList = []
        self.query = Query()
        self.session = None
        self.case = case
        self.step_seq = step_seq

        self.setupUi(self)
        self.setWindowTitle(self.appname)
        self._loadUiInit()

        self.config = Config()
        self.session_cnt = self.config.get('section_session', 'SESSION_CNT')

        #self.sqlBindDialog = SqlBindDialog()

        # ToolBar 버튼 이벤트
        self.action_connectDialog.triggered.connect(self._connectDialogClicked)           # 메뉴 - Connect 버튼
        self.action_queryTest.triggered.connect(self._executeClicked)                     # 메뉴 - Run Cursor 버튼
        self.tw_bind.itemChanged.connect(self._twBindCurrentItemChanged)
        self.tw_output.itemChanged.connect(self._twOutputCurrentItemChanged)

        self.tw_sqlResult.doubleClicked.connect(self._sqlResultItemDoubleClicked)
        self.tw_sqlResult_header = self.tw_sqlResult.horizontalHeader()
        self.tw_sqlResult_header.sectionDoubleClicked.connect(self._sqlResultSectionDoubleClicked)


    def _loadUiInit(self):
        '''
        UI 초기화
        :return: None
        '''
        self.tw_bind.setColumnWidth(0, 150)     # 변수명 컬럼 폭 강제 조절
        self.tw_bind.setColumnWidth(1, 100)     # DB Type 컬럼 폭 강제 조절
        self.tw_bind.setColumnWidth(2, 200)     # Comment Type 컬럼 폭 강제 조절
        self.tw_output.setColumnWidth(0, 150)   # Column 컬럼 폭 강제 조절

        self.splitter_sql_result.setSizes([600, 400])

        # Tool bar Setting
        session_tool_bar = QToolBar()

        self.cb_session = QComboBox()                                                   # Session Combobox
        self.cb_session.setMinimumWidth(200)
        self.cb_session.setToolTip("Session List")

        self.cb_session.currentIndexChanged.connect(self.cbSessionCurrentIndexChanged)  # 콤보박스 변경 이벤트

        session_tool_bar.addWidget(self.cb_session)
        session_tool_bar.addSeparator()
        session_tool_bar.addAction(self.action_connectDialog)
        session_tool_bar.addAction(self.action_queryTest)

        self.session_layout.addWidget(session_tool_bar)

        # SQL Editor Setting
        self.query_text_widget = SqlTextWidget()
        self.query_text_widget.textChanged.connect(self._queryTextChanged)  # SQL Text Changed 이벤트
        self.query_text_widget.setText('SELECT * \n FROM zord_svc')

        self.sa_query.setWidget(self.query_text_widget)

        #stautus_bar = QStatusBar()
        #self.status_layout.addWidget(stautus_bar)


    def getQuery(self):
        '''
        query를 Return
        :return: (class) query
        '''
        return self.query


    def getSession(self):
        '''
        Session을 Return
        :return: (class) session
        '''
        return self.session


    def saveModel(self):
        '''
        model의 내용을 query에 자장
        :return: None
        '''
        self.query.setQueryModel(self.model)


    def loadModel(self):
        '''
        query의 model값을 Load하여 화면에 Setting
        :return:
        '''
        self.model = QueryModel()
        self.model._headers = self.query.headers
        self.model._data = self.query.data
        self.model._row_count = self.query.row_count
        self.model._column_count = self.query.column_count

        self.tw_sqlResult.setModel(self.model)
        self._setOutputView()


    def popUp(self):
        '''
        화면 활성화
        :return: None
        '''
        self.exec_()


    def addSession(self, session):
        '''
        Session 추가
        :param session: (class) session
        :return: None
        '''
        #print(str(len(self.sessionList)))

        if int(self.session_cnt) == 1:
            self.sessionList = []
            self.cb_session.clear()

        self.sessionList.append(session)
        self.cb_session.addItem(session.id + ' @ ' + session.sid)
        self.cb_session.setCurrentIndex(len(self.sessionList)-1)


    def setQuery(self, query):
        '''
        Query Setting
        :param query: (class) query
        :return: None
        '''
        self.query = query
        self.query_text_widget.setText(query.getSql())
        self.loadModel()


    def _connectDialogClicked(self):
        '''
        DB Connection Dialog 활성화
        :return: None
        '''
        sessionDialog = SessionDialog()
        reply = sessionDialog.exec()

        if reply == QDialog.Accepted:
            self.addSession(sessionDialog.session)
            self.sessionChanged.emit(self.session)


    def _executeClicked(self):
        '''
        Query 수행
        :return: None
        '''
        self.model = QueryModel()
        self.model.executed.connect(self._queryModelExecuted)

        sql = self.query_text_widget.text()

        dml_type = sqlFindDml(sql)

        if dml_type in ['INSERT', 'UPDATE', 'DELETE', 'MERGE']:
            QMessageBox.information(self, "오류", '조회(SELECT)만 가능합니다.')
            return False
        else:
            try:
                self.tab_result.setCurrentIndex(2)
                bind_info_list = self._getBindVariable()
                output_info_list = self._getOutput()

                self.query.setSql(sql)
                self.query.setBindInfo(bind_info_list)
                self.query.setOutputInfo(output_info_list)
                self.query.setSession(self.session)

                self.model.setQuery(self.query)
                self.model.execute(self.case)
            except Exception as e:
                self.tw_sqlResult.setModel(self.model)
                QMessageBox.information(self, "오류", str(e))


    def _queryModelExecuted(self):
        '''
        Query 수행완료 후 이벤트
        :return:
        '''
        self.tw_sqlResult.setModel(self.model)

        self._setOutputView()

        output_info_list = self._getOutput()
        self.query.setOutputInfo(output_info_list)

        self.tw_output.itemChanged.connect(self._twOutputCurrentItemChanged)

        QMessageBox.information(self, "성공", "정상적으로 조회되었습니다.")


    def _twBindCurrentItemChanged(self, item):
        '''
        bind TableWidget 값 변경 시 발생 이벤트
        :param item:
        :return: None
        '''
        if self.query:
            bind_info_list = self._getBindVariable()

            if bind_info_list:
                self.query.setBindInfo(bind_info_list)
                self.queryChanged.emit(self.query)


    def _twOutputCurrentItemChanged(self, item):
        '''
        output TableWidget 값 변경 시 발생 이벤트
        :return: None
        '''
        if item:
            col = item.column()
            row = item.row()

            if col == 1:
                variable_id = makeVariableId(item.text())
                item.setText(variable_id)

            output_info_list = self._getOutput()
            self.query.setOutputInfo(output_info_list)

            self.queryChanged.emit(self.query)


    def _sqlResultItemDoubleClicked(self, index):
        '''
        Sql Result Table View Double Click 이벤트
            - Text에 선택한 Table 값을 추가
            - Cursor Position 변경
        :param index: QModelIndex
        :return: None
        '''
        value = self.model.getData(index)
        pos = self.query_text_widget.getCursorPosition()
        self.query_text_widget.insertAt(value, pos[0], pos[1])
        self.query_text_widget.setCursorPosition(pos[0], pos[1] + len(value))
        self.query_text_widget.setFocus()


    def _sqlResultSectionDoubleClicked(self, col):
        '''
        Sql Result Table View Head Double Click 이벤트
            - Text에 선택한 Head Id를 추가
            - Cursor Position 변경
        :param col: (int) 3
        :return: None
        '''
        header_id = self.model.getHeaderId(col)
        pos = self.query_text_widget.getCursorPosition()
        self.query_text_widget.insertAt(header_id, pos[0], pos[1])
        self.query_text_widget.setCursorPosition(pos[0], pos[1] + len(header_id))
        self.query_text_widget.setFocus()


    def cbSessionCurrentIndexChanged(self, index):
        '''
        Session Combobox 변경 이벤트
        :param index: (int) 0
        :return: None
        '''
        if index > -1:
            self.session = self.sessionList[index]
            self.action_queryTest.setEnabled(True)
        else:
            self.action_queryTest.setEnabled(False)


    def _queryTextChanged(self):
        '''
        Query Text 변경 시 발생 이벤트
            - bind 변수를 찾아 TableWidget에 Setting
            - 기존 실행된 Query에 bind변수가 존재하는 경우 자동으로 셋팅
        :return: None
        '''
        bind_list = sqlFindBindVar(self.query_text_widget.text())

        self.tw_bind.clearContents()
        self.tw_bind.setRowCount(len(bind_list))

        typeList = ['String', 'Number']

        if bind_list:
            old_bind_info = {}
            #print(bind_list)

            for idx, bind_variable in enumerate(bind_list):
                # Combo 설정
                db_type_combo = QComboBox()
                db_type_combo.addItems(typeList)

                self.tw_bind.setItem(idx, 0, QTableWidgetItem(bind_variable))
                self.tw_bind.setCellWidget(idx, 1, db_type_combo)

                value_item = QLineEdit()
                value_item.setObjectName('edt_bindValue_{}'.format(idx))
                value_item.textChanged.connect(self._value_changed)
                ref_option_item = QLineEdit()
                ref_option_item.setObjectName('edt_bindRefOption_{}'.format(idx))
                ref_option_item.textChanged.connect(self._value_changed)
                button_item = QToolButton()
                button_item.clicked.connect(partial(self._btnVariableDialogPopup, idx))
                button_item.setIcon(QIcon(':/variable/variable.png'))

                #ref_option_item.setMinimumSize(100, 20)

                # (class) case 존재 시에만 Variable 변수 버튼 추가
                if self.case:
                    value_cell_widget = horizontalLayout([value_item, ref_option_item, button_item])
                else:
                    value_cell_widget = horizontalLayout([value_item])

                self.tw_bind.setCellWidget(idx, 3, value_cell_widget)


                if self.query:
                    old_bind_info = self.query.getBindInfoByVariable(bind_variable)

                if old_bind_info:
                    combo_idx = db_type_combo.findText(old_bind_info['db_type'])
                    db_type_combo.setCurrentIndex(combo_idx)
                    self.tw_bind.setItem(idx, 2, QTableWidgetItem(str(old_bind_info['comment'])))
                    #self.tw_bind.setItem(idx, 3, QTableWidgetItem(str(old_bind_info['value'])))
                    value_item.setText(str(old_bind_info['value']))
                    ref_option_item.setText(str(old_bind_info['ref_option']))

        self.queryChanged.emit(self.query)


    def _value_changed(self, text):
        '''
        Bind Variable value 변경 이벤트
        :param text: (str) '700000001'
        :return: None
        '''
        value = self.sender()

        bind_info_list = self._getBindVariable()

        if bind_info_list:
            self.query.setBindInfo(bind_info_list)
            self.queryChanged.emit(self.query)


    def _btnVariableDialogPopup(self, index):
        '''
        variable tool 버튼 클릭 이벤트
        :return: None
        '''
        self.tw_bind.selectRow(index)
        variableListDialog = VariableListDialog(self.case)
        variableListDialog.applied.connect(self._applyRefVariable)
        variableListDialog.popUp(open_type='select', step_seq=self.step_seq)


    def _applyRefVariable(self, variable_id, ref_option_info):
        '''
        Variable Dialog에서 적용 시 발생 이벤트
        :param variable_id: (str) '$SVC_MGMT_NUM$'
        :param ref_option_info:
        :return: None
        '''
        row = self.tw_bind.currentRow()
        val_item = self.tw_bind.cellWidget(row, 3).findChild(type(QLineEdit()), name='edt_bindValue_{}'.format(row))
        ref_option_item = self.tw_bind.cellWidget(row, 3).findChild(type(QLineEdit()), name='edt_bindRefOption_{}'.format(row))
        val_item.setText(variable_id)
        ref_option_item.setText(ref_option_info)

    def _setOutputView(self):
        '''
        출력변수 TableWidget Setting
        :return:
        '''

        try:
            self.tw_output.itemChanged.disconnect(self._twOutputCurrentItemChanged)
        except:
            pass

        self.tw_output.clearContents()
        self.tw_output.setRowCount(len(self.model.getColumns()))

        for idx, column in enumerate(self.model.getColumns()):
            old_output_info = self.query.getOutputInfoByColumn(column)

            self.tw_output.setItem(idx, 0, QTableWidgetItem(column))

            if old_output_info:
                self.tw_output.setItem(idx, 1, QTableWidgetItem(str(old_output_info['variable_id'])))
                self.tw_output.setItem(idx, 2, QTableWidgetItem(str(old_output_info['comment'])))

        self.tw_output.itemChanged.connect(self._twOutputCurrentItemChanged)


    def _getBindVariable(self):
        '''
        입력변수 TableWidget에서 변수정보를 List형태로 Return
        :return: (list) [{'bind_variable':'iparam1', 'db_type':'String', 'comment':'서비스번호', 'value': '01012345678'}, {}...]
        '''
        bind_variable_list = []

        for idx in range(self.tw_bind.rowCount()):
            sql_variable_info = {}

            var_item = self.tw_bind.item(idx, 0)

            if var_item:
                var = var_item.text()
            else:
                var = ''

            comboWidget = self.tw_bind.cellWidget(idx, 1)

            if not comboWidget:
                return False

            valType = comboWidget.currentText()

            comment_item = self.tw_bind.item(idx, 2)
            val_item = self.tw_bind.cellWidget(idx, 3).findChild(type(QLineEdit()), name='edt_bindValue_{}'.format(idx))
            ref_option_item = self.tw_bind.cellWidget(idx, 3).findChild(type(QLineEdit()), name='edt_bindRefOption_{}'.format(idx))

            if val_item:
                val = val_item.text()
            else:
                val = ''

            if comment_item:
                comment = comment_item.text()
            else:
                comment = ''

            if ref_option_item:
                ref_option = ref_option_item.text()
            else:
                ref_option = ''

            if not var == '':
                sql_variable_info['bind_variable'] = var

                if valType == 'String':
                    sql_variable_info['value'] = str(val)
                elif valType == 'Number':
                    try:
                        sql_variable_info['value'] = int(val)
                    except ValueError:
                        try:
                            sql_variable_info['value'] = float(val)
                        except ValueError:
                            sql_variable_info['value'] = str(val)
                sql_variable_info['db_type'] = valType
                sql_variable_info['comment'] = comment
                sql_variable_info['ref_option'] = ref_option

            bind_variable_list.append(sql_variable_info)

        return bind_variable_list


    def _getOutput(self):
        '''
        출력변수 TableWidget에서 변수정보를 List형태로 Return
        :return: (list) [{'column':'svc_mgmt_num', 'variable_id':'$SVC_MGMT_NUM$', 'comment':'서비스관리번호'}, {}...]
        '''
        output_info_list = []

        for idx in range(self.tw_output.rowCount()):
            output_info = {}

            column_item = self.tw_output.item(idx, 0)
            variable_id_item = self.tw_output.item(idx, 1)
            comment_item = self.tw_output.item(idx, 2)

            if column_item:
                column = column_item.text()
            else:
                column = ''

            if variable_id_item:
                variable_id = variable_id_item.text()
            else:
                variable_id = ''

            if comment_item:
                comment = comment_item.text()
            else:
                comment = ''

            if column:
                output_info['column'] = column
                output_info['variable_id'] = variable_id
                output_info['comment'] = comment

            output_info_list.append(output_info)

        return output_info_list