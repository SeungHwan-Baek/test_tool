import os
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QModelIndex
from PyQt5 import uic

from dialogs.declareVariableDialog import DeclareVariableDialog

from utils.tableModel import CheckPandasModel
from utils.tableviewDelegate import CheckBoxDelegate

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/ref_excel_data.ui"))[0]

class RefExcelDataWidget(QDialog, dig_class):
    dataChanged = pyqtSignal(str, list)

    appname = 'Reference Excel'
    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')

    def __init__(self, sheet_name, df):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)

        self.sheetName = sheet_name

        delegate = CheckBoxDelegate(None)
        self.tw_excelData.setItemDelegateForColumn(0, delegate)

        cols = list(df)
        cols.insert(0, cols.pop(cols.index('Used')))
        df = df.loc[:, cols]

        self.ref_excel_model = CheckPandasModel(df)
        self.ref_excel_model.setting(chk_enable=True)
        self.ref_excel_model.dataChanged.connect(self.excelDataChanged)
        self.tw_excelData.setModel(self.ref_excel_model)

    def excelDataChanged(self):
        df = self.ref_excel_model._data
        data = df.to_dict('records')
        self.dataChanged.emit(self.sheetName, data)

    def addRow(self):
        df2 = self.ref_excel_model._data

        new_row = {}
        for col in list(df2.columns):
            if col == 'Used':
                new_row[col] = 0
            else:
                new_row[col] = ''

        df1 = pd.DataFrame(new_row, index=[0])

        df_result = pd.concat([df1, df2], ignore_index=True)

        self.ref_excel_model = CheckPandasModel(df_result)
        self.ref_excel_model.dataChanged.connect(self.excelDataChanged)
        self.tw_excelData.setModel(self.ref_excel_model)

        df = self.ref_excel_model._data
        data = df.to_dict('records')
        self.dataChanged.emit(self.sheetName, data)

    def accept(self):
        self.close()

    def popUp(self):
        self.exec_()

    def setValue(self):
        self.edt_target.setText(self.step.target)
        self.edt_description.setText(self.step.description)

        combo_idx = self.cb_type.findText(self.step.stepType)
        self.cb_type.setCurrentIndex(combo_idx)

        err_option_combo_idx = self.cb_errOption.findText(self.step.errOption)
        self.cb_errOption.setCurrentIndex(err_option_combo_idx)

    def checkValue(self):
        if self.edt_target.text() == '':
            QMessageBox.information(self, "Add Step", "Target을 입력하세요")
            return False

        if self.edt_description.text() == '':
            QMessageBox.information(self, "Add Step", "Description을 입력하세요")
            return False

        return True

    def getIndex(self):
        return self.tw_excelData.currentIndex()

    def setDataFrame(self, df):
        self.ref_excel_model = CheckPandasModel(df)
        self.ref_excel_model.dataChanged.connect(self.excelDataChanged)
        self.tw_excelData.setModel(self.ref_excel_model)
