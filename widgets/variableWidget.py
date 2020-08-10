"""
Variable Type 추가 시
    1. UI variable_widget.ui에 추가
    2. VariableListDialog _btnAddVariableClicked Method에 item으로 추가
    3. DeclareVariableDialog popup에 추가
    4. VariableWidget setComponent에 추가
    5. VariableWidget getVariable에 추가
    6. variable getValue에 추가
"""
import os
import re
import pickle
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import *
from PyQt5 import uic

from libs.variable import Variable
from utils.lib import makeVariableId

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
widget_class = uic.loadUiType(os.path.join(parentDir, "UI/variable_widget.ui"))[0]

class VariableWidget(QWidget, widget_class):
    HOME = os.path.expanduser("~")
    REF_SAVE_PATH = os.path.join(HOME, 'Test_Tool', 'ref', 'ref.ref_info')

    def __init__(self, parent=None, case=None, option=True):
        super(VariableWidget, self).__init__(parent)
        self.setupUi(self)
        self.target = None
        self.case = case
        self.variable = None
        self.option = option
        self._loadUiInit()

        self.ref_data_list = []
        self.sql_column_list = []

        self.edt_variableId.textEdited.connect(self._variableIdTextEdited)
        self.edt_variableId.editingFinished.connect(self._variableIdEditingFinished)

        self.sb_refSubStrOption1.valueChanged.connect(self._subStrOptionChanged)
        self.sb_refSubStrOption2.valueChanged.connect(self._subStrOptionChanged)
        self.edt_refAddOption.textEdited.connect(self._refAddOptionTextEdited)

        self.cb_oparamColumnId.currentIndexChanged['QString'].connect(self._cbOparamCurrentIndexChanged)
        self.cb_refOption.currentIndexChanged['QString'].connect(self._cbRefOptionCurrentIndexChanged)

        self.cb_excelFileNm.currentIndexChanged['QString'].connect(self._cbExcelFileNmCurrentIndexChanged)
        self.cb_excelSheet.currentIndexChanged['QString'].connect(self._cbExcelSheetCurrentIndexChanged)
        self.cb_excelColumnId.currentIndexChanged['QString'].connect(self._cbExcelColumnIdCurrentIndexChanged)
        self.cb_sqlNm.currentIndexChanged['QString'].connect(self._cbSqlNmCurrentIndexChanged)
        self.cb_sqlColumnId.currentIndexChanged['QString'].connect(self._cbSqlColumnIdCurrentIndexChanged)

        self.edt_refEvalOption.textChanged.connect(self._refEvalOptionTextChanged)

    def _loadUiInit(self):
        self.edt_refId.hide()
        self.edt_variableId.setStyleSheet("color: rgb(244, 164, 96);")
        self.de_designatedDate.setDate(QDate.currentDate())
        self.setRefOptionEnable(self.option)

    def _variableIdTextEdited(self, variable_id):
        if variable_id:
            if variable_id[0] != '$' or variable_id[-1] != '$' or variable_id.find('$$') > -1:
                self.edt_variableId.setStyleSheet("color: rgb(255, 0, 0);")
            else:
                self.edt_variableId.setStyleSheet("color: rgb(244, 164, 96);")

    def _variableIdEditingFinished(self):
        variable_id = makeVariableId(self.edt_variableId.text())
        self.edt_variableId.setText(variable_id)

        self._variableIdTextEdited(variable_id)

    def _subStrOptionChanged(self):
        value = self.variable.getValue()
        self.setDataListValue(value)

    def _refAddOptionTextEdited(self):
        value = self.variable.getValue()
        self.setDataListValue(value)

    def _cbOparamCurrentIndexChanged(self, item):
        self.getOparamInfo(item)

    def getOparamInfo(self, column_id):
        if self.variable is None:
            svc_combo_name = self.getSvcComboNm()
            svc_combo_index = next(idx for idx, refDataInfo in enumerate(self.ref_data_list) if refDataInfo.get('name') == svc_combo_name)

            ref_data = self.ref_data_list[svc_combo_index]

            variable_id = ref_data.get('{}_variable_id'.format(column_id))
            variable_desc = ref_data.get('{}_desc'.format(column_id))
            self.setVariableId(variable_id)
            self.setDesc(variable_desc)

    def _cbRefOptionCurrentIndexChanged(self, item):
        if item is not None:
            value = self.variable.getValue()
            self.setDataListValue(value)

    def _refEvalOptionTextChanged(self):
        if self.getType() == 'Data List':
            self.setDataListValue()
        elif self.getType() == 'SVC COMBO (Swing Only)':
            self.setSvcComboValue()

    def _cbExcelFileNmCurrentIndexChanged(self, item):
        if item:
            self.cb_excelSheet.clear()
            self.cb_excelColumnId.clear()
            try:
                file_index = next(idx for idx, refDataInfo in enumerate(self.ref_data_list) if refDataInfo.get('name') == item)
                ref_file = self.ref_data_list[file_index]
                sheet_list = list(sheetData['sheet'] for idx, sheetData in enumerate(ref_file.get('data')))
                self.cb_excelSheet.addItems(sheet_list)
                self.lbl_excelFileNmDesc.setText("")
            except StopIteration:
                self.lbl_excelFileNmDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))

    def _cbExcelSheetCurrentIndexChanged(self, item):
        file_name = self.getExcelFileNm()

        if item and file_name:
            self.cb_excelColumnId.clear()
            try:
                file_index = next(idx for idx, refDataInfo in enumerate(self.ref_data_list) if refDataInfo.get('name') == file_name)
                ref_file = self.ref_data_list[file_index]
                sheet_index = next(idx for idx, sheetData in enumerate(ref_file.get('data')) if sheetData['sheet'] == item)
                ref_sheet = ref_file.get('data')[sheet_index]
                column_list = ref_sheet['columns']
                self.cb_excelColumnId.addItems(column_list)
                self.lbl_excelSheetDesc.setText("")
            except StopIteration:
                self.lbl_excelSheetDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))

    def _cbExcelColumnIdCurrentIndexChanged(self, item):
        file_name = self.getExcelFileNm()
        sheet = self.getExcelSheet()

        if item and file_name:
            try:
                file_index = next(idx for idx, refDataInfo in enumerate(self.ref_data_list) if refDataInfo.get('name') == file_name)
                ref_file = self.ref_data_list[file_index]
                sheet_index = next(idx for idx, sheetData in enumerate(ref_file.get('data')) if sheetData['sheet'] == sheet)
                ref_sheet = ref_file.get('data')[sheet_index]
                column_list = ref_sheet['columns']

                if item in column_list:
                    self.lbl_excelColumnIdDesc.setText("")
                else:
                    self.lbl_excelColumnIdDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))
            except StopIteration:
                self.lbl_excelColumnIdDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))

    def _cbSqlNmCurrentIndexChanged(self, item):
        if item:
            ref_data = self.getRefData('name', item, 'SQL')
            query = ref_data.get('query')
            self.sql_column_list = query.getOutputInfo()
            self.edt_refId.setText(ref_data.getId())
            self.setSqlColumnId(column_list=self.sql_column_list)

    def _cbSqlColumnIdCurrentIndexChanged(self, item):
        if item:
            column_index = next(idx for idx, column_info in enumerate(self.sql_column_list) if column_info.get('column') == item)
            selected_column_info = self.sql_column_list[column_index]
            self.setVariableId(selected_column_info['variable_id'])
            self.setDesc(selected_column_info['comment'])

    def init(self):
        self.cb_variableType.setCurrentIndex(0)
        self.edt_variableId.setText('')
        self.edt_targetNm.setText('')
        self.edt_targetId.setText('')
        self.edt_subId.setText('')
        self.sb_rowIndex.setValue(0)
        self.edt_columnId.setText('')
        self.edt_descripton.setText('')
        self.edt_dataListValue.setText('')

    def setType(self, variable_type):
        combo_idx = self.cb_variableType.findText(variable_type)
        self.cb_variableType.setCurrentIndex(combo_idx)

    def setTarget(self, target):
        self.target = target

    def setVariableId(self, variable_id):
        self.edt_variableId.setText(variable_id)

    def setTargetNm(self, target_nm):
        self.edt_targetNm.setText(target_nm)

    def setTargetId(self, target_id):
        self.edt_targetId.setText(target_id)

    def setSubId(self, sub_id):
        self.edt_subId.setText(sub_id)

    def setRowIndex(self, row_index):
        if type(row_index) == int:
            self.sw_rowIndex.setCurrentIndex(0)
            method_combo_idx = self.cb_rowMethod.findText("Fix")
            self.cb_rowMethod.setCurrentIndex(method_combo_idx)
            self.sb_rowIndex.setValue(row_index)

            self.edt_rowIndexColumnValue.setText("")

        else:
            self.sw_rowIndex.setCurrentIndex(1)
            method_combo_idx = self.cb_rowMethod.findText("By Value")
            self.cb_rowMethod.setCurrentIndex(method_combo_idx)
            row_index_column_id = row_index["column_id"]
            row_index_value = row_index["value"]

            row_index_column_id_idx = self.cb_rowIndexColumnId.findText(row_index_column_id)
            self.cb_rowIndexColumnId.setCurrentIndex(row_index_column_id_idx)
            self.edt_rowIndexColumnValue.setText(row_index_value)

    def setRowIndexColumnId(self, column_id_list):
        self.cb_rowIndexColumnId.clear()
        self.cb_rowIndexColumnId.addItems(column_id_list)

    def setColumnId(self, column_id):
        self.edt_columnId.setText(column_id)

    def setDesc(self, description):
        self.edt_descripton.setText(description)

    def setDataListValue(self, value=''):
        value = self.applyRefOption(value)
        self.edt_dataListValue.setText(str(value))

    def applyRefOption(self, value=''):
        ref_option = self.getRefOption()

        if ref_option == 'Substr':
            value = self.variable.getValue()
            start_index = self.sb_refSubStrOption1.value()
            end_index = self.sb_refSubStrOption2.value()
            value = value[start_index:end_index]
        elif ref_option == 'Sum':
            value = self.variable.getValue()

            try:
                value = int(value)
                addOption = self.getRefAddOption()
                option_variables = [x.strip() for x in addOption.split(',')]

                for variable_id in option_variables:
                    variable = self.case.getVariable(variable_id)

                    if variable is None:
                        pass
                    else:
                        try:
                            add_value = int(variable.getValue())
                            value += add_value
                        except ValueError:
                            pass
            except ValueError:
                value = self.variable.getValue()
        elif ref_option == 'Eval':
            evalOption = self.getRefEvalOption()
            try:
                find_variables = re.findall(r"(?:[^\$]+[\$$])", evalOption, flags=re.MULTILINE | re.DOTALL)
                if find_variables:
                    for tmp_variable_id in find_variables:
                        variable_id = makeVariableId(tmp_variable_id)
                        variable = self.case.getVariable(variable_id)

                        if variable:
                            value = variable.getValue()
                            evalOption = evalOption.replace(variable_id, "'{}'".format(value))

                # print(evalOption)
                value = eval(evalOption)
            except NameError:
                value = ''
            except SyntaxError:
                value = ''
            except TypeError:
                value = ''

        return value

    def setDateFormat(self, format):
        format_combo_idx = self.cb_dateFormat.findText(format)
        self.cb_dateFormat.setCurrentIndex(format_combo_idx)

    def setDateOption(self, date_option):
        date_option_combo_idx = self.cb_dateOption.findText(date_option)
        self.cb_dateOption.setCurrentIndex(date_option_combo_idx)

    def setDesignatedDate(self, designated_date):
        if designated_date:
            date = QDate.fromString(designated_date, "yyyyMMdd")
            self.de_designatedDate.setDate(date)

    def setDateValue(self, value):
        self.edt_dateValue.setText(value)

    def setExcelFileNm(self, file_nm):
        file_nm_combo_idx = self.cb_excelFileNm.findText(file_nm)
        if file_nm_combo_idx > -1:
            self.lbl_excelFileNmDesc.setText('')
        else:
            self.cb_excelFileNm.insertItem(0, file_nm)
            self.cb_excelFileNm.insertSeparator(1)
            self.lbl_excelFileNmDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))
            file_nm_combo_idx = 0
        self.cb_excelFileNm.setCurrentIndex(file_nm_combo_idx)

    def setExcelSheet(self, sheet):
        sheet_combo_idx = self.cb_excelSheet.findText(sheet)

        if sheet_combo_idx > -1:
            self.lbl_excelSheetDesc.setText('')
        else:
            self.cb_excelSheet.insertItem(0, sheet)
            self.cb_excelSheet.insertSeparator(1)
            self.lbl_excelSheetDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))
            sheet_combo_idx = 0

        self.cb_excelSheet.setCurrentIndex(sheet_combo_idx)

    def setExcelColumnId(self, column_id):
        column_id_combo_idx = self.cb_excelColumnId.findText(column_id)

        if column_id_combo_idx > -1:
            self.lbl_excelColumnIdDesc.setText('')
        else:
            self.cb_excelColumnId.insertItem(0, column_id)
            self.cb_excelColumnId.insertSeparator(1)
            self.lbl_excelColumnIdDesc.setText("<h4><font color='{color}'> {text} </font></h4>".format(color='Red', text='Does not exist'))
            column_id_combo_idx = 0

        self.cb_excelColumnId.setCurrentIndex(column_id_combo_idx)

    def setExcelValue(self, value):
        self.edt_excelValue.setText(value)

    def setFixedValue(self, value):
        self.edt_fixedValue.setText(value)

    def setRefOptionEnable(self, enabled):
        if enabled:
            self.lbl_refOption.show()
            self.cb_refOption.show()
            self.sw_refOptionDtl.show()
        else:
            self.lbl_refOption.hide()
            self.cb_refOption.hide()
            self.sw_refOptionDtl.hide()

    def setRefOptionInfo(self, ref_option):
        if ref_option:
            ref_option_split = [x.strip() for x in ref_option.split('|')]
            ref_option_type = ref_option_split[0]
            ref_option_info = ref_option_split[1]

            ref_option_combo_idx = self.cb_refOption.findText(ref_option_type)
            self.cb_refOption.setCurrentIndex(ref_option_combo_idx)

            if ref_option_type == 'Substr':
                index_list = [x.strip() for x in ref_option_info.split(',')]
                start_index = int(index_list[0])
                end_index = int(index_list[1])

                self.sb_refSubStrOption1.setValue(start_index)
                self.sb_refSubStrOption2.setValue(end_index)
            elif ref_option_type == 'Sum':
                self.edt_refAddOption.setText(ref_option_info)
            elif ref_option_type == 'Eval':
                self.edt_refEvalOption.setText(ref_option_info)


    def setOparamRowIndex(self, row_index):
        if type(row_index) == int:
            self.sw_oparamRowIndex.setCurrentIndex(0)
            method_combo_idx = self.cb_oparamRowMethod.findText("Fix")
            self.cb_oparamRowMethod.setCurrentIndex(method_combo_idx)
            self.sb_oparamRowIndex.setValue(row_index)

            self.edt_oparamRowIndexColumnValue.setText("")

        else:
            self.sw_oparamRowIndex.setCurrentIndex(1)
            method_combo_idx = self.cb_rowMethod.findText("By Value")
            self.cb_oparamRowMethod.setCurrentIndex(method_combo_idx)

            row_index_column_id = row_index["column_id"]
            row_index_value = row_index["value"]

            row_index_column_id_idx = self.cb_oparamRowIndexColumnId.findText(row_index_column_id)
            self.cb_oparamRowIndexColumnId.setCurrentIndex(row_index_column_id_idx)
            self.edt_oparamRowIndexColumnValue.setText(row_index_value)

    def setSvcComboValue(self, value=''):
        value = self.applyRefOption(value)
        self.edt_svcComboValue.setText(str(value))

    def setSqlValue(self, value=''):
        value = self.applyRefOption(value)
        self.edt_sqlValue.setText(str(value))

    def setSqlColumnId(self, column_list):
        column_id_list = []

        for column_info in column_list:
            column_id_list.append(column_info['column'])

        self.cb_sqlColumnId.clear()
        self.cb_sqlColumnId.addItems(column_id_list)
        self.cb_sqlRowIndexColumnId.clear()
        self.cb_sqlRowIndexColumnId.addItems(column_id_list)

    def getRefData(self, key, value, ref_type):
        '''
        reference data에서 key에 해당하는 value 값과 동일한 ref_data 를 Return
        :param key: (str) 'name'
        :param value: (str) '개인/내국인조회'
        :param ref_type: (str) 'SQL'
        :return: (class) reference
        '''
        if key == 'id':
            index = next(idx for idx, ref_data_info in enumerate(self.ref_data_list) if ref_data_info.getId() == value and ref_data_info.getType() == ref_type)
        else:
            index = next(idx for idx, ref_data_info in enumerate(self.ref_data_list) if ref_data_info.get(key) == value and ref_data_info.getType() == ref_type)
        ref_data = self.ref_data_list[index]

        return ref_data

    # ============================ Excel ============================
    def setRefExcelInfo(self):
        '''
        Excel 참조 정보를 Setting
            - Combobox에서 선택 할 수 있도로 값을 Setting
        :param ref_data_list:
        :return:
        '''
        self.ref_data_list = self.case.getRefData()
        file_name_list = list(ref_data_info.get('name') for idx, ref_data_info in enumerate(self.ref_data_list) if ref_data_info.getType() == 'Excel')
        self.cb_excelFileNm.clear()
        self.cb_excelFileNm.addItems(file_name_list)

    def typeSetEnabled(self, bool):
        self.cb_variableType.setEnabled(bool)

    def getType(self):
        return self.cb_variableType.currentText()

    def getVariableId(self):
        return self.edt_variableId.text()

    def getTarget(self):
        return self.edt_target.text()

    def getSubId(self):
        return self.edt_subId.text()

    def getRowIndex(self):
        return self.sb_rowIndex.value()

    def getColumnId(self):
        return self.edt_columnId.text()

    def getRowMethod(self):
        return self.cb_rowMethod.currentText()

    def getRowIndexColumnId(self):
        return self.cb_rowIndexColumnId.currentText()

    def getRowIndexValue(self):
        return self.edt_rowIndexColumnValue.text()

    def getDesc(self):
        return self.edt_descripton.text()

    def getRefOption(self):
        return self.cb_refOption.currentText()

    def getRefAddOption(self):
        return self.edt_refAddOption.text()

    def getRefEvalOption(self):
        return self.edt_refEvalOption.text()

    def getDataListValue(self):
        return self.edt_dataListValue.text()

    def getRefOptionInfo(self):
        ref_option_info = ''
        #if self.variable.variable_type == 'Data List':
        ref_option = self.getRefOption()

        if ref_option == 'Substr':
            start_index = self.sb_refSubStrOption1.value()
            end_index = self.sb_refSubStrOption2.value()
            ref_option_info = '{ref_option} | {start_index}, {end_index}'.format(ref_option=ref_option, start_index=start_index, end_index=end_index)
        elif ref_option == 'Sum':
            add_option = self.getRefAddOption()
            ref_option_info = '{ref_option} | {add_option}'.format(ref_option=ref_option, add_option=add_option)
        elif ref_option == 'Eval':
            eval_option = self.getRefEvalOption()
            ref_option_info = '{ref_option} | {eval_option}'.format(ref_option=ref_option, eval_option=eval_option)

        return ref_option_info

    def getDateFormat(self):
        return self.cb_dateFormat.currentText()

    def getDateOption(self):
        return self.cb_dateOption.currentText()

    def getDesignatedDate(self):
        designated_date = self.de_designatedDate.date()
        return designated_date.toString("yyyyMMdd")

    def getExcelFileNm(self):
        return self.cb_excelFileNm.currentText()

    def getExcelSheet(self):
        return self.cb_excelSheet.currentText()

    def getExcelColumnId(self):
        return self.cb_excelColumnId.currentText()

    def getfixedValue(self):
        return self.edt_fixedValue.text()

    # ============================ SVC COMBO (Swing Only) ============================
    def setRefSvcComboInfo(self):
        '''
        SVC COMBO 참조 정보를 Setting
            - Combobox에서 선택 할 수 있도로 값을 Setting
        :param ref_data_list:
        :return:
        '''
        self.ref_data_list = self.case.getRefData()
        svc_combo_name_list = list(ref_data_info.get('name') for idx, ref_data_info in enumerate(self.ref_data_list) if ref_data_info.getType() == 'SVC COMBO (Swing Only)')
        self.cb_svcComboNm.clear()
        self.cb_svcComboNm.addItems(svc_combo_name_list)
        self.getOparamInfo('oparam1')

    def getSvcComboNm(self):
        return self.cb_svcComboNm.currentText()

    def getIparam1(self):
        return self.edt_iparam1.text()

    def getIparam2(self):
        return self.edt_iparam2.text()

    def getIparam3(self):
        return self.edt_iparam3.text()

    def getIparam4(self):
        return self.edt_iparam4.text()

    def getIparam5(self):
        return self.edt_iparam5.text()

    def getOparamColumnId(self):
        return self.cb_oparamColumnId.currentText()

    def getOparamRowMethod(self):
        return self.cb_oparamRowMethod.currentText()

    def getOparamRowIndex(self):
        return self.sb_oparamRowIndex.value()

    def getOparamRowIndexColumnId(self):
        return self.cb_oparamRowIndexColumnId.currentText()

    def getOparamRowIndexColumnValue(self):
        return self.edt_oparamRowIndexColumnValue.text()

    # ============================ SQL ============================
    def setRefSqlInfo(self):
        '''
        SQL 참조 정보를 Setting
            - Combobox에서 선택 할 수 있도로 값을 Setting
        :param ref_data_list:
        :return:
        '''
        self.ref_data_list = self.case.getRefData()
        sql_name_list = list(ref_data_info.get('name') for idx, ref_data_info in enumerate(self.ref_data_list) if ref_data_info.getType() == 'SQL')
        self.cb_sqlNm.clear()
        self.cb_sqlNm.addItems(sql_name_list)

    def setSqlRowIndex(self, row_index):
        if type(row_index) == int:
            self.sw_sqlRowIndex.setCurrentIndex(0)
            method_combo_idx = self.cb_sqlRowMethod.findText("Fix")
            self.cb_sqlRowMethod.setCurrentIndex(method_combo_idx)
            self.sb_sqlRowIndex.setValue(row_index)

            self.edt_sqlRowIndexColumnValue.setText("")

        else:
            self.sw_sqlRowIndex.setCurrentIndex(1)
            method_combo_idx = self.cb_sqlRowMethod.findText("By Value")
            self.cb_sqlRowMethod.setCurrentIndex(method_combo_idx)

            row_index_column_id = row_index["column_id"]
            row_index_value = row_index["value"]

            row_index_column_id_idx = self.cb_sqlRowIndexColumnId.findText(row_index_column_id)
            self.cb_sqlRowIndexColumnId.setCurrentIndex(row_index_column_id_idx)
            self.edt_sqlRowIndexColumnValue.setText(row_index_value)

    def getRefId(self):
        return self.edt_refId.text()

    def getVariable(self):
        '''
        입력값 기준으로 (Class) Variable 을 Return
        :return: (Class) Variable
        '''
        var = None
        variable_type = self.getType()
        variable_id = self.getVariableId()
        desc = self.getDesc()

        if variable_type == 'Data List':
            sub_id = self.getSubId()
            row_method = self.getRowMethod()
            column_id = self.getColumnId()

            if row_method == 'Fix':
                row_index = self.getRowIndex()
            else:
                row_index_column_id = self.getRowIndexColumnId()
                row_index_value = self.getRowIndexValue()
                row_index = {'column_id': row_index_column_id, 'value': row_index_value}

            var = Variable(case=self.case, variable_type=variable_type, variable_id=variable_id)
            var['description'] = desc
            var['target'] = self.target
            var['sub_id'] = sub_id
            var['row_index'] = row_index
            var['column_id'] = column_id
        elif variable_type == 'Date':
            date_option = self.getDateOption()
            format = self.getDateFormat()

            if date_option == "Today":
                designated_date = ""
            elif date_option == "Designated date":
                designated_date = self.getDesignatedDate()
            else:
                designated_date = ""

            var = Variable(case=self.case, variable_type=variable_type, variable_id=variable_id)
            var['description'] = desc
            var['date_option'] = date_option
            var['designated_date'] = designated_date
            var['format'] = format
        elif variable_type == 'Excel':
            file_nm = self.getExcelFileNm()
            sheet = self.getExcelSheet()
            column_id = self.getExcelColumnId()

            var = Variable(case=self.case, variable_type=variable_type, variable_id=variable_id)
            var['description'] = desc
            var['file_nm'] = file_nm
            var['sheet'] = sheet
            var['column_id'] = column_id
        elif variable_type == 'SQL':
            ref_sql_id = self.getRefId()
            column_id = self.cb_sqlColumnId.currentText()
            row_method = self.cb_sqlRowMethod.currentText()

            if row_method == 'Fix':
                row_index = self.sb_sqlRowIndex.value()
            else:
                row_index_column_id = self.cb_sqlRowIndexColumnId.currentText()
                row_index_value = self.edt_sqlRowIndexColumnValue.text()
                row_index = {'column_id': row_index_column_id, 'value': row_index_value}

            var = Variable(case=self.case, variable_type=variable_type, variable_id=variable_id)
            var['description'] = desc
            var['ref_sql_id'] = ref_sql_id
            var['column_id'] = column_id
            var['row_index'] = row_index

        elif variable_type == 'Fixed Value':
            value = self.getfixedValue()
            var = Variable(case=self.case, variable_type=variable_type, variable_id=variable_id)
            var['description'] = desc
            var['value'] = value
        elif variable_type == 'SVC COMBO (Swing Only)':
            svc_combo_nm = self.getSvcComboNm()
            column_id = self.getOparamColumnId()
            row_method = self.getOparamRowMethod()

            if row_method == 'Fix':
                row_index = self.getOparamRowIndex()
            else:
                row_index_column_id = self.getOparamRowIndexColumnId()
                row_index_value = self.getOparamRowIndexColumnValue()
                row_index = {'column_id': row_index_column_id, 'value': row_index_value}

            var = Variable(case=self.case, variable_type=variable_type, variable_id=variable_id)
            var['description'] = desc
            var['svc_combo_nm'] = svc_combo_nm
            var['column_id'] = column_id
            var['row_index'] = row_index

        return var

    def setComponent(self, variable):
        self.variable = variable

        self.setType(variable.variable_type)
        self.setVariableId(variable.variable_id)
        self.setDesc(variable.get('description'))

        if variable.variable_type == 'Data List':
            target_nm = variable.get('target').get('target')
            target_id = variable.get('target').id

            column_id_list = variable.get('target').getColumnList(variable.get('sub_id'))

            self.setTarget(variable.get('target'))
            self.setTargetNm(target_nm)
            self.setTargetId(target_id)
            self.setSubId(variable.get('sub_id'))
            self.setRowIndexColumnId(column_id_list)
            self.setRowIndex(variable.get('row_index'))
            self.setColumnId(variable.get('column_id'))
            self.setDataListValue(variable.getValue())
            self.typeSetEnabled(False)
        elif variable.variable_type == 'Date':
            self.setDateOption(variable.get('date_option'))
            self.setDesignatedDate(variable.get('designated_date'))
            self.setDateFormat(variable.get('format'))
            self.setDateValue(variable.getValue())
        elif variable.variable_type == 'Excel':
            self.setRefExcelInfo()
            self.setExcelFileNm(variable.get('file_nm'))
            self.setExcelSheet(variable.get('sheet'))
            self.setExcelColumnId(variable.get('column_id'))

            try:
                value = variable.getValue()
            except:
                value = ''
            self.setExcelValue(value)
        elif variable.variable_type == 'SQL':
            self.setRefSqlInfo()
            ref_sql_id = variable.get('ref_sql_id')
            ref_data = self.getRefData('id', ref_sql_id, 'SQL')
            sql_nm = ref_data.get('name')
            sql_nm_idx = self.cb_sqlNm.findText(sql_nm)
            self.cb_sqlNm.setCurrentIndex(sql_nm_idx)

            column_combo_idx = self.cb_sqlColumnId.findText(variable.get('column_id'))
            self.cb_sqlColumnId.setCurrentIndex(column_combo_idx)
            self.setSqlRowIndex(variable.get('row_index'))
            self.setSqlValue(variable.getValue())
        elif variable.variable_type == 'Fixed Value':
            self.setFixedValue(variable.get('value'))
        elif variable.variable_type == 'SVC COMBO (Swing Only)':
            self.setRefSvcComboInfo()

            svc_combo_nm_idx = self.cb_svcComboNm.findText(variable.get('svc_combo_nm'))
            self.cb_svcComboNm.setCurrentIndex(svc_combo_nm_idx)

            column_combo_idx = self.cb_oparamColumnId.findText(variable.get('column_id'))
            self.cb_oparamColumnId.setCurrentIndex(column_combo_idx)
            self.setOparamRowIndex(variable.get('row_index'))
            self.setSvcComboValue(variable.getValue())

