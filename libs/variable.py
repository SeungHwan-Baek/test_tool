import os
import pickle
from datetime import date
from libs.xhr import Xhr

class Variable(object):
    variable_id = ''
    def __init__(self, case, variable_type, variable_id):
        self.info = {}
        self.case = case
        self.variable_type = variable_type
        self.variable_id = '{}'.format(variable_id.upper())
        #self.target = target
        # self.info['target_nm'] = target.get('target') if target is not None else ""
        # self.info['sub_id'] = sub_id
        # self.info['column_id'] = column_id
        # self.info['row_index'] = row_index
        # self.info['description'] = description

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError from e

        #print("Variable Not Found: {}".format(name))
        #print(self.variable_id)
        #pass

    def __setitem__(self, key, value):
        if key == 'target':
            self.info[key] = value
            self.info['target_nm'] = value.get('target') if value is not None else ""

        else:
            self.info[key] = value

    def __getitem__(self, key):
        return self.info[key]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def setCase(self, case):
        self.case = case

    def get(self, key, default=''):
        if key in self.info:
            if self.info[key] == '':
                return default
            else:
                return self.info[key]
        else:
            return default

    def getId(self):
        return self.variable_id

    def getType(self):
        return self.variable_type

    def getValue(self):
        value = ""

        if self.variable_type == 'Data List':
            target = self.get('target')
            sub_id = self.get('sub_id')
            column_id = self.get('column_id')
            row_index = self.getRowIndex()

            if row_index > -1:
                value = target.getRowInfoValue(sub_id, row_index, column_id, 'value')
            else:
                value = ""
        elif self.variable_type == 'Date':
            format = self.get('format')
            date_option = self.get('date_option')
            designated_date = self.get('designated_date')

            if date_option == 'Today':
                today = date.today()
                value = today.strftime(format)
            elif date_option == 'Designated date':
                value = designated_date
        elif self.variable_type == 'Excel':
            ref_data_list = self.case.getRefData()
            file_nm = self.get('file_nm')
            sheet = self.get('sheet')
            column_id = self.get('column_id')

            file_index = next(idx for idx, refDataInfo in enumerate(ref_data_list) if refDataInfo.get('name') == file_nm)

            ref_file = ref_data_list[file_index]
            sheet_index = next(idx for idx, sheetData in enumerate(ref_file.get('data')) if sheetData['sheet'] == sheet)
            ref_sheet = ref_file.get('data')[sheet_index]

            if column_id in ref_sheet['columns']:
                # 기 사용된 데이타는 Skip
                row_index = next(idx for idx, rowData in enumerate(ref_sheet['value']) if rowData['Used'] == 0)
                value = ref_sheet['value'][row_index][column_id]
                self.case.usedData.append(ref_sheet['value'][row_index])
        elif self.variable_type == 'SQL':
            ref_data_list = self.case.getRefData()

            ref_sql_id = self.get('ref_sql_id')
            column_id = self.get('column_id')
            row_index = self.get('row_index')

            index = next(idx for idx, ref_data_info in enumerate(ref_data_list) if ref_data_info.getId() == ref_sql_id and ref_data_info.getType() == self.variable_type)
            ref_data = ref_data_list[index]

            if type(row_index) == int:
                pass
            elif type(row_index) == dict:
                row_index = ref_data.getRowIndexByValue(row_index['column_id'], row_index['value'])
            else:
                row_index = -1

            value = ref_data.getRefValue(row_index, column_id)

        elif self.variable_type == 'Fixed Value':
            value = self.get('value')
        elif self.variable_type == 'SVC COMBO (Swing Only)':
            '''
            ref_data_list = self.case.getRefData()
            svc_combo_nm = self.get('svc_combo_nm')

            svc_combo_index = next(idx for idx, refDataInfo in enumerate(ref_data_list) if refDataInfo.get('name') == svc_combo_nm)

            ref_data = ref_data_list[svc_combo_index]
            #print(self.case.usedData)
            #print(ref_data.get('name'))
            if ref_data.get('name') in self.case.usedData:
                #print('Skip')
                step = ref_data.get('target')
            else:
                step = ref_data.getXhrSvcCombo()
                self.case.usedData.append(svc_combo_nm)

            #print(step)
            '''
            ref_data_list = self.case.getRefData()
            svc_combo_nm = self.get('svc_combo_nm')

            try:
                svc_combo_index = next(idx for idx, refDataInfo in enumerate(ref_data_list) if refDataInfo.get('name') == svc_combo_nm)

                ref_data = ref_data_list[svc_combo_index]

                step = ref_data.get('target')
                column_id = self.get('column_id')
                row_index = self.get('row_index')
                worker_index = self.case.getWorkerIndex()

                if worker_index > 0:
                    row_index = worker_index
                elif type(row_index) == int:
                    pass
                elif type(row_index) == dict:
                    row_index = ref_data.getRowIndexByValue(row_index['column_id'], row_index['value'])
                else:
                    row_index = -1

                value = ref_data.getRefValue(row_index, column_id)
            except StopIteration:
                pass
            #print(value)

        return value

    def getKeys(self):
        return list(self.info.keys())

    def getRowIndex(self):
        target = self.get('target')
        sub_id = self.get('sub_id')
        row_index = self.get('row_index')

        if type(row_index) == int:
            pass
        elif type(row_index) == dict:
            row_index = target.getRowIndexByValue(sub_id, row_index['column_id'], row_index['value'])
        else:
            row_index = -1

        return row_index

    def getStepId(self):
        id = ''

        if self.variable_type == 'Data List':
            target = self.get('target')
            id = target.getId()
        else:
            pass

        return id
