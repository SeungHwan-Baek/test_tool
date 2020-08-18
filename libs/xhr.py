import pandas as pd
import json
import re
import requests
import socket
import datetime
from libs.step import Step
from libs.column import Column
from libs.row import Row

class Xhr(Step):

    input_data = {}
    output_data = {}

    data_column_info = {}
    data_row_info = {}

    selected_data_list_id = ''

    url = ''
    trx_code = ''

    tr_info = {}

    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)

        self.input_data = {}
        self.output_data = {}

        self.data_column_info = {}
        self.data_row_info = {}
        self.selected_data_list_id = ''

    # ============================ Set ============================
    def setInputData(self, data):
        '''
        Input Data Setting
        :param data: (dict) or (str)
        :return:
        '''
        if type(data) == str:
            data = data.replace("'", "\"")
            data = json.loads(data)

        self.input_data = data
        self.setColumnInfo(self.input_data)
        self.setRowInfo()

        try:
            self.trx_code = data['HEAD']['Trx_Code']
        except:
            print('Error : setInputDataInfo (Trx_Code)')


    def setOutputData(self, data):
        '''
        Output Data Setting
        :param data: (dict) or (str)
        :return:
        '''
        if type(data) == str:
            data = data.replace("'", "\"")
            data = json.loads(data)

        self.output_data = data
        self.setColumnInfo(self.output_data)
        self.setRowInfo()


    def setColumnInfo(self, data):
        '''
        Column의 정보를 (class) Column 로 Setting
            - Column ID와 Description을 관리하기 위함
            - (class) Column 을 Dict로 관리 {'input1' : [ (class) Column1,  (class) Column2, ... ]}
            - Column 정보 추가 시 이미 존재하는 경우 Skip
            - 결과값이 존재하지 않는 Output의 경우 output dataInfo 에서 column값을 찾아 추가함
        :param data: (list) or (dict) [input_data, output_data]
        :return: None
        '''
        for data_list_id in data:
            data_list = []

            try:
                columns = self.data_column_info[data_list_id]
            except KeyError:
                columns = []

            if type(data[data_list_id]) == list:
                if data[data_list_id]:
                    data_list = data[data_list_id][0]
            elif type(data[data_list_id]) == dict:
                data_list = data[data_list_id]

            if data_list:
                for column_id in data_list:
                    column = self.getColumnInfoById(data_list_id, column_id)

                    if column:
                        pass
                    else:
                        column = Column(self)
                        column['column_id'] = column_id
                        column['variable'] = ''
                        columns.append(column)
            else:
                if self.getDataListType(data_list_id) == 'output':
                    dataList = list(filter(lambda datalist: datalist['id'] == data_list_id, self.output_data['dataInfo']))

                    if dataList:
                        output_columns = [column['id'] for column in dataList[0]['columns']['column']]

                        for column_id in output_columns:
                            column = self.getColumnInfoById(data_list_id, column_id)

                            if column:
                                pass
                            else:
                                column = Column(self)
                                column['column_id'] = column_id
                                column['variable'] = ''
                                columns.append(column)

            self.data_column_info[data_list_id] = columns


    def setColumnValue(self, data_list_id, column_id, key, value):
        '''
        Column Info를 변경함
        :param data_list_id: (str) 'input1'
        :param column_id: (str) 'svc_mgmt_num'
        :param key: (str) 'description'
        :param value: (str) '서비스관리번호'
        :return: None
        '''
        column = self.getColumnInfoById(data_list_id, column_id)

        if column:
            column[key] = value
        else:
            pass
            #print('Xhr Class : Nonexistent column')


    def addColumn(self, data_list_id, new_column_id, column_index):
        '''
        Column 추가
        :param data_list_id: (str) 'input1'
        :param new_column_id: (str) 'esim_cl_cd'
        :return: (bool) True
        '''
        column_info_index = -1
        column_list = self.getColumnList(data_list_id)

        if new_column_id in column_list:
            return False
        else:
            try:
                index = column_list.index('rowStatus')
            except ValueError:
                index = -1

            data_list_type = self.getDataListType(data_list_id)

            if data_list_type == 'input':
                data_list = self.input_data
            elif data_list_type == 'output':
                data_list = self.output_data

            for data in data_list[data_list_id]:
                data[new_column_id] = ''

                # Column 추가 시 Insert하기 위한 로직
                if column_index > -1:
                    data_tmp = data.copy()
                    column_info_index = column_index
                    for column_id in data_tmp:
                        try:
                            pop_column_index = column_list.index(column_id)
                            if pop_column_index < column_index:
                                pass
                            else:
                                pop_item = data.pop(column_id)
                                print(column_id)
                                data[column_id] = pop_item
                        except ValueError:
                            pass
                else:
                    column_info_index = index
                    if index > -1:
                        pop_item = data.pop('rowStatus')
                        data['rowStatus'] = pop_item

            # Column 정보 추가
            column = Column(self)
            column['column_id'] = new_column_id
            column['variable'] = ''
            self.data_column_info[data_list_id].insert(column_info_index, column)

            # Row정보 변경
            self.setRowInfo()
            return True


    def deleteColumn(self, data_list_id, column_id):
        '''
        Column 삭제
        :param data_list_id: (str) 'input1'
        :param new_column_id: (str) 'esim_cl_cd'
        :return: None
        '''
        column_list = self.getColumnList(data_list_id)

        if column_id in column_list:
            try:
                index = column_list.index(column_id)
            except ValueError:
                index = -1
                return False

            for data in self.input_data[data_list_id]:
                if index > -1:
                    data.pop(column_id)

            self.data_column_info[data_list_id].pop(index)

            # Row정보 변경
            self.setRowInfo()

            return True
        else:
            return False



    def setRowInfo(self):
        '''
        Row의 정보를 (class) Row 로 Setting
            - Row별로 참조값, input_value여부, marking여부 등을 관리하기 위함
            - input_data 를 setting하거나 output_data 를 Setting 하는 경우 호출됨
            - (class) Row 를 Dict로 관리 {'input1' : [ { 'svc_mgmt_num' : (class) Row,  'svc_chg_cd' : (class) Row, ... }          <-- index : 0
                                                      { 'svc_mgmt_num' : (class) Row,  'svc_chg_cd' : (class) Row, ... },         <-- index : 1
                                                    ],
                                        'input2' : ...}
        :return: None
        '''
        for data in self.input_data:
            tmp_data = []
            data_row = []
            if type(self.input_data[data]) == dict:
                tmp_data.append(self.input_data[data])
            else:
                tmp_data = self.input_data[data]

            for row_index, data_list in enumerate(tmp_data):
                row_dict = {}
                for col_index, col in enumerate(data_list):
                    row = self.getRowInfo(data, row_index, col)

                    if row is None:
                        row = Row(self)

                    row['data_list_id'] = data
                    row['row_index'] = row_index
                    row['column_id'] = col
                    row['column_index'] = col_index
                    row['value'] = data_list[col]
                    row.initKey('marking', False)
                    row.initKey('input_value', False)
                    row.initKey('variable', '')
                    row.initKey('ref_target', '')
                    row.initKey('ref_option', '')

                    row_dict[col] = row

                data_row.append(row_dict)
            self.data_row_info[data] = data_row

        for data in self.output_data:
            tmp_data = []
            data_row = []
            if type(self.output_data[data]) == dict:
                tmp_data == list(self.output_data[data])
            else:
                tmp_data = self.output_data[data]
            for row_index, data_list in enumerate(tmp_data):
                row_dict = {}
                for col_index, col in enumerate(data_list):
                    row = self.getRowInfo(data, row_index, col)

                    if row is None:
                        row = Row(self)

                    row['data_list_id'] = data
                    row['row_index'] = row_index
                    row['column_id'] = col
                    row['column_index'] = col_index
                    row['value'] = data_list[col]
                    row.initKey('marking', False)
                    row.initKey('variable', '')

                    row_dict[col] = row

                data_row.append(row_dict)
            self.data_row_info[data] = data_row


    def setRowInfoValue(self, data_list_id, row, column_id, key, value):
        '''
        Row Info를 변경함
        :param data_list_id: (str) 'input1'
        :param row: (int) or (dict) 0, {'column_id:'svc_mgmt_num', 'value':712345678}
        :param column_id: (str) 'svc_mgmt_num'
        :param key: 'ref_target'
        :param value: '$SVC_MGMT_NUM$
        :return: None
        '''
        if type(row) == int:
            row_index = row
        elif type(row) == dict:
            row_index = self.getRowIndexByValue(data_list_id, row['column_id'], row['value'])

        if len(self.data_row_info[data_list_id]) > row_index:
            row_data = self.data_row_info[data_list_id][row_index][column_id]
        else:
            row_data = Row(self)
            row_data['data_list_id'] = data_list_id
            row_data['row_index'] = row_index
            row_data['column_id'] = column_id
            row_data['value'] = ''
            row_data.initKey('marking', False)
            row_data.initKey('variable', '')
            self.data_row_info[data_list_id].append(row_data)

        if row_data:
            row_data[key] = value
        else:
            print('Xhr Class : Nonexistent row')


    def addRow(self, data_list_id, row_cnt = 1):
        '''
        Row 추가
        :param data_list_id: (str) 'input1'
        :param row_cnt: (int) 1
        :return: None
        '''
        data = {}
        column_list = self.getColumnList(data_list_id)

        for column in column_list:
            data[column] = ''

        data_list_type = self.getDataListType(data_list_id)

        if data_list_type == 'input':
            data_list = self.input_data
        elif data_list_type == 'output':
            data_list = self.output_data

        for ix in range(0, row_cnt):
            data_list[data_list_id].append(data)

        # Row정보 변경
        self.setRowInfo()


    def deleteRow(self, data_list_id, row_index):
        '''
        Row 삭제
        :param data_list_id: (str) 'input1'
        :param row_index: (int) 0
        :return: None
        '''
        self.input_data[data_list_id].pop(row_index)
        # Row정보 변경
        self.setRowInfo()


    def resetRowInfo(self):
        '''
        Row Info를 재설정함
        :return:
        '''
        self.data_row_info = {}
        self.setRowInfo()

    def resetDataListBySize(self, data_list_id, row=0, column_id='json_string', size=512):
        '''
        size에 맞게 Parsing해서 Row로 추가
            JSD SQL 수행을 위해서 size에 맞게 Row로 잘라서 추가
        :param data_list_id: (str) 'output1'
        :param row: (int) 0
        :param column_id: (str) 'json_string'
        :param size: (int) 512
        :return: None
        '''
        input_data = self.input_data[data_list_id][row][column_id]
        input_data = input_data.replace('\x01\x0c', '')
        chunks_list = [input_data[i:i+size] for i in range(0, len(input_data), size)]

        for idx, row_data in enumerate(chunks_list):
            self.setInputDataValue(data_list_id, idx, column_id, '\x01\x0c' + row_data.replace('\x01\x0c', '') + '\x01\x0c')
        #print(self.input_data[data_list_id])

    # ============================ Get ============================
    def getDataListId(self, data_list_type=''):
        '''
        Data List Id를 List로 Return
        :param data_list_type: 'intput', 'output'
        :return: (list) ['input1', 'HEAD' ...]
        '''
        data_list = list(self.input_data.keys())
        input_data_list = sorted(data_list)

        # HEAD를 밑으로 이동
        try:
            head_index = input_data_list.index('HEAD')
            pop_data = input_data_list.pop(head_index)
            input_data_list.append(pop_data)
        except ValueError:
            pass

        data_list = list(self.output_data.keys())
        remove_data_list = ['HEAD', 'dataInfo']
        output_data_list = [x for x in data_list if x not in remove_data_list]
        output_data_list = sorted(output_data_list)

        if data_list_type == 'input':
            data_list = input_data_list
        elif data_list_type == 'output':
            data_list = output_data_list
        else:
            data_list = input_data_list + output_data_list

        return data_list


    def getDataList(self, data_list_id, return_type='dict'):
        '''
        Data를 dict 또는 dataframe 형태로 Return
            - UI Table view에 pandas model로 Setting 하기 위함
        :param data_list_id: (str) 'input1'
        :param return_type: (str) 'dict' or 'dataframe'
        :return: (dict) or (dataframe)
        '''
        if return_type == 'dict':
            if data_list_id in list(self.input_data.keys()):
                return self.input_data[data_list_id]
            elif data_list_id in list(self.output_data.keys()):
                return self.output_data[data_list_id]
            else:
                print('getDataList: Not Exists DataList [{}]'.format(data_list_id))
                return {}
        elif return_type == 'dataframe':
            self.selected_data_list_id = data_list_id

            if data_list_id in list(self.input_data.keys()):
                try:
                    return pd.DataFrame(self.input_data[data_list_id], index=[0])
                except KeyError:
                    return pd.DataFrame()
                except:
                    return pd.DataFrame(self.input_data[data_list_id], columns=list(self.input_data[data_list_id][0].keys()))
            elif data_list_id in list(self.output_data.keys()):
                outputDataFrame = pd.DataFrame()

                if data_list_id == 'params':
                    outputDataFrame = self.getResponseParamsData(return_type=return_type)
                else:
                    if self.output_data:
                        dataList = list(filter(lambda datalist: datalist['id'] == data_list_id, self.output_data['dataInfo']))
                        if dataList:
                            columns = [column['id'] for column in dataList[0]['columns']['column']]

                            outputDataFrame = pd.DataFrame(self.output_data[data_list_id], columns=columns)

                return outputDataFrame
        else:
            print('Xhr Class : Return Type Error')

    def getTrxCode(self):
        '''
        Step의 Trx_Code 값을 Return
            - Step의 target은 변경이 가능하여 Request Head의 trx_code값을 사용하기 위함
        :return: (str) ZORDSCUS00700_TR01
        '''
        return self.trx_code


    def getSelectedDataList(self):
        '''
        최종으로 선택했던 data list id를 Return
            - Step 선택 시 최종 선택했던 data list를 재선택하기 위함
        :return: (str) 'input1'
        '''
        return self.selected_data_list_id

    def getColumnList(self, data_list_id):
        '''
        data_list_id에 해당하는 (class) Column의 column id를 List 형태로 Return
        :param data_list_id: 'input1'
        :return: ['call_chnl',
                  'svc_mgmt_num',
                  'svc_chg_cd',
                  'svc_chg_rsn_cd',
                  'eqp_agrmt_allot_cl_cd',
                  'rowStatus']
        '''

        try:
            column_list = [column.get('column_id') for column in self.data_column_info[data_list_id]]
        except KeyError:
            column_list = []

        return column_list


    def getColumnCount(self, data_list_id):
        '''
        data_list_id에 해당하는 (class) Column 건수를 Return
        :param data_list_id: (str) 'input1'
        :return: (int) 3
        '''

        try:
            column_list = [column.get('column_id') for column in self.data_column_info[data_list_id]]
        except KeyError:
            column_list = []

        return len(column_list)


    def getColumnInfoById(self, data_list_id, column_id):
        '''
        data_list_id, column_id 에 해당하는 (class) Column를 Return
        :param data_list_id: 'intput1'
        :param column_id: 'svc_mgmt_num'
        :return: (class) Column
        '''

        try:
            self.data_column_info[data_list_id][0].get('description')
        except:
            pass
            #print(data_list_id, column_id)

        try:
            index = next(idx for idx, row in enumerate(self.data_column_info[data_list_id]) if row['column_id'] == column_id)
        except StopIteration:
            index = -1
        except KeyError:
            index = -1

        if index > -1:
            return self.data_column_info[data_list_id][index]
        else:
            return None


    def getColumnValues(self, data_list_id, key):
        '''
        data_list_id 의 (class) Column의 정보 중 key에 해당하는 정보 전체를 Dict 형태로 Return
        :param data_list_id: 'input1'
        :param key: 'description'
        :return: (dict) {'svc_mgmt_num' : '서비스관리번호',
                         'svc_num' : '서비스번호'}
        '''
        column_values = {}

        for column in self.data_column_info[data_list_id]:
            id = column.get('column_id')
            value = column.get(key, '')

            column_values[id] = value

        return column_values


    def getColumnValue(self, data_list_id, column_id, key):
        '''
        data_list_id, column_id 에 해당하는 (class) Column의 정보 중 key의 Value 값을 Return
        :param data_list_id: 'input1'
        :param column_id: 'svc_mgmt_num'
        :param key: 'description'
        :return: (str) '서비스관리번호'
        '''
        col = self.getColumnInfoById(data_list_id, column_id)

        if col:
            col_value = col.get(key, '')
        else:
            col_value = ''

        return col_value

    def getRowIndexByValue(self, data_list_id, column_id, value):
        '''
        data_list_id, column_id, value 에 해당하는 Row Index 를 Return
        :param data_list_id: 'input2'
        :param column_id: 'dtl_itm_nm'
        :param value: 'allot_appr_amt'
        :return: (int) 8
        '''
        result_list = []
        row_index = -1

        for index, data in enumerate(self.data_row_info[data_list_id]):
            for row_data in data:
                if row_data == column_id and data[row_data].get('value') == value:
                    result_list.append(index)

        if result_list:
            row_index = result_list[0]
        else:
            pass

        return row_index


    def getRowInfo(self, data_list_id, row, column_id):
        '''
        data_list_id, row, column_id 에 해당하는 (class) Row를 Return
        :param data_list_id: 'intput1'
        :param row: 0
        :param column_id: 'svc_mgmt_num'
        :return: (class) Row
        '''
        try:
            if type(row) == int:
                row_index = row
            elif type(row) == dict:
                row_index = self.getRowIndexByValue(data_list_id, row['column_id'], row['value'])

            row_info = self.data_row_info[data_list_id][row_index][column_id]
        except IndexError:
            row_info = None
        except KeyError:
            row_info = None

        return row_info


    def getRowInfoValue(self, data_list_id, row, column_id, key):
        '''
        data_list_id, row, column_id 의 (class) Row의 정보 중 key의 Value 값을 Return
        :param data_list_id: 'input1'
        :param row: 0
        :param column_id: 'svc_chg_cd'
        :param key: 'value'
        :return: (unknown-type) 'A1'
        '''
        try:
            if type(row) == int:
                row_index = row
            elif type(row) == dict:
                row_index = self.getRowIndexByValue(data_list_id, row['column_id'], row['value'])

            row_data = self.data_row_info[data_list_id][row_index][column_id]
            row_value = row_data.get(key)
        except IndexError:
            row_value = ''
        except KeyError:
            row_value = ''

        return row_value


    def getRowInfoValues(self, data_list_id, key):
        '''
        data_list_id 의 (class) Row의 정보 중 key에 해당하는 정보 전체를 list [{Dict}] 형태로 Return
        :param data_list_id: 'input2'
        :param key: 'value'
        :return: [{'dtl_ser_num': '', 'dtl_itm_nm': 'eqp_dc_cl_cd', 'dtl_itm_val': '7', 'rowStatus': 'C'},
                  {'dtl_ser_num': '', 'dtl_itm_nm': 'agrmt_mth_cnt', 'dtl_itm_val': '24','rowStatus': 'C'},
                 ...
                 ]
        '''
        row_values = []

        for data in self.data_row_info[data_list_id]:
            row_dict = {}
            for row_data in data:
                row_dict[row_data] = data[row_data].get(key)
            row_values.append(row_dict)

        return row_values


    def getRowByValue(self, key, value, data_list_type='', exact_match=False):
        '''
        value에 해당하는 Row를 List 형태로 Return
            - 값에 의한 참조 자동 셋팅 시 사용하기 위함
        :param key: 'value'
        :param value: '24'
        :param data_list_type: 'input'
        :return: [(Class) Row, (Class) Row]
        '''
        row_list = []

        if data_list_type == 'input':
            target_data = list(self.input_data.keys())
        elif data_list_type == 'output':
            target_data = list(self.output_data.keys())
        else:
            target_data = list(self.data_row_info.keys())

        for data_list_id in target_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:
                    if exact_match:
                        if str(value) == str(data[row_data].get(key)):
                            row_list.append(data[row_data])
                    else:
                        if str(value) in str(data[row_data].get(key)):
                            row_list.append(data[row_data])

        return row_list


    def getRowByLen(self, key, length, data_list_type=''):
        '''
        length보다 큰 value length를 가지고 있는 Row를 List 형태로 Return
        :param key: 'value'
        :param length: 3
        :param data_list_type: 'input'
        :return: [(Class) Row, (Class) Row]
        '''
        row_list = []

        if data_list_type == 'input':
            target_data = list(self.input_data.keys())
        elif data_list_type == 'output':
            target_data = list(self.output_data.keys())
        else:
            target_data = list(self.data_row_info.keys())

        for data_list_id in target_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:
                    if len(str(data[row_data].get(key))) >= length:
                        row_list.append(data[row_data])

        return row_list


    def getRowByText(self, text, step_index=-1, find_data_list_id='', data_list_type=''):
        '''
        text를 value나 column_id에 포함하고 있는 Row 중 row_index, column_index 보다 크거나 같은 Row를 찾아 List 형태로 Return
            - 검색 시 사용하기 위함
            - data_list_id 값이 있을 겨우 입력값인 data_list_id index 보다 크거나 같은 Row만 포함
        :param text: '24'
        :param find_data_list_id: (str) 'input1'
        :param data_list_type: 'input'
        :return: [(Class) Row, (Class) Row]
        '''
        row_list = []

        if data_list_type == 'input':
            target_data = list(self.input_data.keys())
        elif data_list_type == 'output':
            target_data = list(self.output_data.keys())
        else:
            target_data = list(self.data_row_info.keys())

        for data_list_id in target_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:

                    if text in str(data[row_data].get('value')) or text in str(data[row_data].get('column_id')):
                        if self.getSeq == step_index and find_data_list_id:
                            data_lists = self.getDataListId()

                            try:
                                if data_lists.index(find_data_list_id) >= data_lists.index(data[row_data].get('data_list_id')):
                                    pass
                                else:
                                    row_list.append(data[row_data])
                            except ValueError:
                                row_list.append(data[row_data])
                        else:
                            row_list.append(data[row_data])

        return row_list


    def getMarkingRow(self, data_list_type=''):
        '''
        marking이 True인 Row를 List 형태로 Return
            - 값에 의한 참조 자동 셋팅 시 사용하기 위함
        :param data_list_id: 'input2'
        :return: [(Class) Row, (Class) Row]
        '''
        row_list = []

        if data_list_type == 'input':
            target_data = list(self.input_data.keys())
        elif data_list_type == 'output':
            target_data = list(self.output_data.keys())
        else:
            target_data = list(self.data_row_info.keys())

        for data_list_id in target_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:
                    if data[row_data].get('marking') == True:
                        row_list.append(data[row_data])

        return row_list


    def getRowIndexByValue(self, data_list_id, key, value):
        '''
        data_list_id, column_id에 해당하는 (class) Row의 정보 중 value에 해당하는 Row Index를 Return
            - 참조 시 Row Index를 Value에 의해 찾고자 하기위함
        :param data_list_id: 'input2'
        :param key: 'dtl_itm_nm'
        :param value: 'cust_ppay_amt'
        :return: 8
        '''
        try:
            index = next(idx for idx, row in enumerate(self.data_row_info[data_list_id]) if row[key].get('value') == value)
        except StopIteration:
            index = -1
        except KeyError:
            index = -1

        return index

    def getVariable(self, data_list_id, row, column_id):
        '''
        (class) Row 에서 (class) variable
            - 이미 선언된 variable을 값을 수정하기 위함 (declareVariableDialog)
        :param data_list_id:
        :param row:
        :param column_id:
        :return: (class) variable
        '''
        variable_id = self.getRowInfoValue(data_list_id, row, column_id, 'variable')
        variable = self.case.getVariable(variable_id)

        return variable


    def getVariables(self):
        '''
        Step 에 선언된 variable_id를 List형태로 Return
            - Case에서 Step 삭제 시 선언된 Variable도 삭제하기 위함
        :return: ['$SVC_NUM$', '$SVC_MGMT_NUM$'..]
        '''
        variable_list = []
        for data_list_id in self.input_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:
                    variable_id = data[row_data].get('variable')

                    if variable_id:
                        variable_list.append(variable_id)

        for data_list_id in self.output_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:
                    variable_id = data[row_data].get('variable')

                    if variable_id:
                        variable_list.append(variable_id)

        return variable_list


    def getRefVariables(self):
        '''
        Step 에서 참조하는 variable_id를 List형태로 Return
            - Step이 참조하는 variable을 체크하기 위함
        :return: ['$SVC_NUM$', '$SVC_MGMT_NUM$'..]
        '''
        variable_list = []
        for data_list_id in self.input_data:
            for data in self.data_row_info[data_list_id]:
                for row_data in data:
                    variable_id = data[row_data].get('ref_target')

                    if variable_id:
                        variable_list.append(variable_id)

        return variable_list


    def getIsRef(self, data_list_id='', row=-1, column_id=''):
        '''
        Row값이 참조하는 대상이 있는지 여부
            - Tableview, step dtl widget 에서 노출하기 위함
        :param data_list_id: 'input1'
        :param row: 0
        :param column_id: 'svc_mgmt_num'
        :return: (str) 'Link' Or 'Unlink' Or ''
        '''
        rst = ''
        # Step 전체에 대해서 체크
        if data_list_id == '':
            for data_list_id in self.input_data:
                for row_index, row in enumerate(self.data_row_info[data_list_id]):
                    for col in row:
                        row_data = self.data_row_info[data_list_id][row_index][col]
                        ref_target = row_data.get('ref_target')

                        if ref_target:
                            if self.checkRefVariable(ref_target):
                                rst = 'Link'
                            else:
                                rst = 'Unlink'
                                return rst
                        else:
                            pass
        # Data List Id 기준으로 체크
        elif row == -1:
            for row_index, row in enumerate(self.data_row_info[data_list_id]):
                for col in row:
                    row_data = self.data_row_info[data_list_id][row_index][col]
                    ref_target = row_data.get('ref_target')

                    if ref_target:
                        if self.checkRefVariable(ref_target):
                            rst = 'Link'
                        else:
                            rst = 'Unlink'
                            return rst
                    else:
                        pass
        else:
            ref_target = self.getRowInfoValue(data_list_id, row, column_id, 'ref_target')

            if ref_target:
                if self.checkRefVariable(ref_target):
                    rst = 'Link'
                else:
                    rst = 'Unlink'

        return rst


    def getIsVar(self, data_list_id='', row=-1, column_id=''):
        '''
        Row값이 Variable인지 여부
            - Tableview에서 노출하기 위함
        :param data_list_id: 'input1'
        :param row: 0
        :param column_id: 'svc_mgmt_num'
        :return: (str) 'Link' Or 'Unlink' Or ''
        '''
        rst = ''

        # Step 기준
        if data_list_id == '':
            for data_list_id in self.input_data:
                for row_index, row in enumerate(self.data_row_info[data_list_id]):
                    for col in row:
                        row_data = self.data_row_info[data_list_id][row_index][col]
                        variable_id = row_data.get('variable')
                        if variable_id:
                            variable = self.case.getVariable(variable_id)

                            if variable:
                                variable_step_id = variable.getStepId()
                                variable_column_id = variable.get('column_id')

                                if self.getId() == variable_step_id and col == variable_column_id:
                                    rst = 'Link'
                                else:
                                    rst = 'Unlink'
                            else:
                                rst = 'Unlink'
                                return rst
            for data_list_id in self.output_data:
                for row_index, row in enumerate(self.data_row_info[data_list_id]):
                    for col in row:
                        row_data = self.data_row_info[data_list_id][row_index][col]
                        variable_id = row_data.get('variable')
                        if variable_id:
                            variable = self.case.getVariable(variable_id)

                            if variable:
                                variable_step_id = variable.getStepId()
                                variable_column_id = variable.get('column_id')

                                if self.getId() == variable_step_id and col == variable_column_id:
                                    rst = 'Link'
                                else:
                                    rst = 'Unlink'
                            else:
                                rst = 'Unlink'
                                return rst
        # Data List Id 기준으로 체크
        elif row == -1:
            for row_index, row in enumerate(self.data_row_info[data_list_id]):
                for col in row:
                    row_data = self.data_row_info[data_list_id][row_index][col]
                    variable_id = row_data.get('variable')

                    if variable_id:
                        variable = self.case.getVariable(variable_id)

                        if variable:
                            variable_step_id = variable.getStepId()
                            variable_column_id = variable.get('column_id')

                            if self.getId() == variable_step_id and col == variable_column_id:
                                rst = 'Link'
                            else:
                                rst = 'Unlink'
                        else:
                            rst = 'Unlink'
                            return rst
        # Data Row 기준
        else:
            variable_id = self.getRowInfoValue(data_list_id, row, column_id, 'variable')
            if variable_id:
                variable = self.case.getVariable(variable_id)
                if variable:
                    variable_step_id = variable.getStepId()
                    variable_column_id = variable.get('column_id')

                    if self.getId() == variable_step_id and column_id == variable_column_id:
                        rst = 'Link'
                    else:
                        rst = 'Unlink'
                else:
                    rst = 'Unlink'

        return rst

    def getIsColVar(self, data_list_id='', column_id=''):
        '''
        Column에 Variable가 설정되어 있는지 여부
            - Tableview에서 노출하기 위함
        '''
        rst = ''
        variable_id = self.getColumnValue(data_list_id, column_id, 'variable')

        if variable_id:
            variable = self.case.getVariable(variable_id)
            if variable:
                variable_step_id = variable.getStepId()
                variable_column_id = variable.get('column_id')

                if self.getId() == variable_step_id and column_id == variable_column_id:
                    rst = 'Link'
                else:
                    rst = 'Unlink'
            else:
                rst = 'Unlink'

        return rst


    def getValueByRef(self):
        '''
        참조 변수에 해당하는 값을 찾아 input_data에 Setting
        :return: None
        '''
        variables = self.case.getVariables()

        for data_list_id in self.input_data:

            for row_index, row in enumerate(self.data_row_info[data_list_id]):
                #self.data_row_info[input_data_id][row]
                for col in row:
                    row_data = self.data_row_info[data_list_id][row_index][col]
                    ref = row_data.get('ref_target')
                    ref_option = row_data.get('ref_option')
                    if ref:
                        #print(data_list_id, row_index, col, ref)
                        try:
                            variable = variables[ref]
                        except KeyError:
                            raise KeyError

                        try:
                            value = variable.getValue()

                            if ref_option:
                                value = self.applyRefOption(value, ref_option)
                            self.setInputDataValue(data_list_id, row_index, col, value)
                        except:
                            self.setStatus(1, "참조값을 확인하세요")
                            raise


    def removeRowVariableInfo(self, data_list_id, variable_id):
        '''
        data_list_id 의 (class) Row의 정보 중 variable_id에 해당하는 Row의 Variable 정보를 초기화
            - Case에서 Variable 삭제 시 (class) Row 에서 정보 초기화
        :param data_list_id: 'input1'
        :param variable: '$SVC_MGMT_NUM$'
        :return: None
        '''
        for index, data in enumerate(self.data_row_info[data_list_id]):
            for row_data in data:
                if data[row_data].get('variable') == variable_id:
                    data[row_data]['variable'] = ''


    def checkRefVariable(self, variable_id):
        '''
        Row에서 참조하는 variable 존재여부 체크
            - Table View Widget에 노출하기 위함
        :return: (bool) True
        '''
        if variable_id in self.case.getVariableId():
            pass
        else:
            return False

        return True


    def getRefValue(self, data_list_id, row, column_id):
        ref_value = ''

        try:
            row_data = self.data_row_info[data_list_id][row][column_id]
            ref = row_data.get('ref_target')
            ref_value = ref.getValue()
        except IndexError:
            ref_value = ''
        except KeyError:
            ref_value = ''

        return ref_value


    def getResponseParamsData(self, return_type='dict'):
        if return_type == 'dict':
            return self.output_data['params']
        elif return_type == 'dataframe':
            paramsDataFrame = pd.DataFrame()

            if self.output_data:
                paramsDataFrame = pd.DataFrame(self.output_data['params'])

            return paramsDataFrame
        else:
            print('Xhr Class : Return Type Error'
                  )

    def getParamsMsgByRequest(self):
        msg = ''
        if self.output_data:
            msg = self.output_data['params'][0]['ErrorMsg'].split('^^')[4].strip()
        return msg

    def getParamsCodeByRequest(self):
        code = -1
        if self.output_data:
            code = int(self.output_data['params'][0]['ErrorCode'])
        return code

    def getInputDataValue(self, dataListId, row, column):
        data = self.findData(dataListId, row)

        if data:
            if column in list(data.keys()):
                return data[column]
            else:
                print('[{dataListId}] Data has no column {column}'.format(dataListId=dataListId, column=column))

    def setInputDataValue(self, data_list_id, row, column, value):
        data = self.findData(data_list_id, row)

        if data:
            if column in list(data.keys()):
                data[column] = value
                self.setRowInfoValue(data_list_id, row, column, 'value', value)
            else:
                print('[{dataListId}] Data has no column {column}'.format(dataListId=data_list_id, column=column))
        else:
            data = {}
            data[column] = value
            self.input_data[data_list_id].append(data)
            self.setRowInfoValue(data_list_id, row, column, 'value', value)


    def setInputDataFrame(self, data_list_id, dataFrame):
        if type(dataFrame) == pd.core.frame.DataFrame:
            if data_list_id == 'HEAD':
                input_data = dataFrame.to_dict('records')[0]
            else:
                input_data = dataFrame.to_dict('records')

            self.input_data[data_list_id] = input_data
            self.setRowInfo()
        else:
            print('setInputDataFrame Log : Mismatch Type')


    def getInputDataRow(self, data_list_id):
        return len(self.input_data[data_list_id])


    def findData(self, data_list_id, row=0):
        data = {}
        if type(self.input_data[data_list_id]) == dict:
            data = self.input_data[data_list_id]
        elif type(self.input_data[data_list_id]) == list:
            if len(self.input_data[data_list_id]) > row:
                data = self.input_data[data_list_id][row]
            else:
                print('List index out of range : Check row')
                return False
        return data

    def getDataListType(self, data_list_id):
        '''
        data list type을 Return
        :param data_list_id: (str) 'input1'
        :return: (str) 'input'
        '''
        data_list_type = ''

        if data_list_id in self.input_data:
            data_list_type = 'input'
        elif data_list_id in self.output_data:
            data_list_type = 'output'
        elif data_list_id == 'params':
            data_list_type = 'params'

        return data_list_type

    def getTrIO(self):
        try:
            request_url = 'http://172.31.196.21:8060/websquare/Service/layout?TrxCode={}&Action=UDetail'.format(self.trx_code)
            r = requests.post(request_url)

            tmp_tr_info = r.json()
            error_code = int(tmp_tr_info['params'][0]['ErrorCode'])

            if error_code > 0:
                pass
                return False
            else:
                self.tr_info = tmp_tr_info
                return True
        except:
            print('Error : getTrIO')
            return False

    def mergeTrInfo(self, method):
        for data_list_id in self.getDataListId():
            data_type = " ".join(re.findall("[a-zA-Z]+", data_list_id))
            rec_Index = " ".join(re.findall("\d+", data_list_id))

            if data_type == 'input':
                # print(data['InFormat'])
                filterList = list(filter(lambda row: row['RecIndex'] == rec_Index, self.tr_info['InFormat']))

                for fieldInfo in filterList:
                    self.setColumnValue(data_list_id, fieldInfo['FieldName'], 'description', fieldInfo['FieldDesc'])
            elif data_type == 'output':
                filterList = list(filter(lambda row: row['RecIndex'] == rec_Index, self.tr_info['OutFormat']))
                for fieldInfo in filterList:
                    self.setColumnValue(data_list_id, fieldInfo['FieldName'], 'description', fieldInfo['FieldDesc'])


    def startStep(self):
        start = datetime.datetime.now()

        # GET방식
        log_enable = self.get('log_enable')

        if log_enable:
            self.url = 'http://172.31.196.21:8060/websquare/Service/SVC?commonsvc=0&rtcode=0&fCloseAccount=0&LogLvlGbn=9&G_BizCd=null&G_Biz_Start_Time=null&__smReqSeq=4&_useLayout=true'
        else:
            self.url = 'http://172.31.196.21:8060/websquare/Service/SVC?commonsvc=0&rtcode=0&fCloseAccount=0&LogLvlGbn=&G_BizCd=null&G_Biz_Start_Time=null&__smReqSeq=4&_useLayout=true'

        try:
            ip_addr = socket.gethostbyname(socket.getfqdn())
            self.setInputDataValue('HEAD', 0, 'Ngms_IpAddr', ip_addr)

            if self.getCondRst():
                err_option = self.getErrOption()
                r = requests.get(self.url, json=self.input_data)
                #print(self.input_data)
                self.statusCode = r.status_code

                # Request 수행 이후 값 변경
                self.setOutputData(r.json())

                code = self.getParamsCodeByRequest()
                msg = self.getParamsMsgByRequest()

                if code > 0 and err_option == 'Skip':
                    code = 999

                self.setStatus(code, msg)

                end = datetime.datetime.now()
                time_delta = end - start

                self.info['exec_time'] = str(time_delta)

                # print(r.text)
            else:
                code = 999
                msg = 'Skip'
                self.setStatus(code, msg)
        except Exception as e:
            print(e)
        finally:
            self.remove('log_enable')
