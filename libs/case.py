import os
import pickle
import datetime
from datetime import date
import uuid
import libs.structure as structure
from libs.variable import Variable
from libs.browser_command import BrowserCommand
from utils.lib import findDictIndexByValue, findDictListByValue, remove_dupe_dicts, parsingRef, change_key, makeVariableId, make_marking_seq, findTrName
__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)

class Case(object):
    category = ''
    caseType = ''
    caseSeq = ''
    caseNm = ''
    caseDesc = ''
    stepList = []
    variableList = {}

    usedData = []

    # Unique ID
    caseId = ''

    selectedStepRow = -1

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    MARKING_SAVE_FILE_PATH = os.path.join(SAVE_PATH, 'marking', '.marking_info')

    def __init__(self, category='Test', case_type='', case_seq='', case_nm=''):
        self.suites = None
        self.category = ''
        self.caseType = ''
        self.caseId = ''
        self.caseNm = ''
        self.caseDesc = ''
        self.stepList = []
        self.variables = {}
        self.selectedStepRow = 0
        self.status = -1
        self.caseId = str(uuid.uuid4())

        self.setCategory(category)
        self.setCaseType(case_type)
        self.setCaseSeq(case_seq)
        self.setCaseNm(case_nm)

    def version(self):
        return __version__

    def openCase(self, suites):
        ##print('Case Verion [{}]'.format(__version__))
        self.suites = suites
        self.caseId = str(uuid.uuid4())

    def setCategory(self, category):
        self.category = category

    def setCaseType(self, case_type):
        self.caseType = case_type

    def setCaseSeq(self, case_seq):
        self.caseSeq = case_seq

    def setCaseNm(self, case_nm):
        self.caseNm = case_nm

    def setCaseDesc(self, case_desc):
        self.caseDesc = case_desc

    def setStepList(self, step, index=-1):
        step.setCase(self)

        if index > -1:
            self.stepList.insert(index, step)
        else:
            self.stepList.append(step)

    def setVariableList(self, variable):
        self.variables[variable.variable_id] = variable

    def setSelectedStepRow(self, row):
        self.selectedStepRow = row

    def setStatus(self, status):
        self.status = status

    def getCaseId(self):
        return self.caseId

    def getCaseNm(self):
        return self.caseNm

    def getCaseDesc(self):
        return self.caseDesc

    def getStatus(self):
        return self.status

    def getCaseType(self):
        return self.caseType

    def getCategory(self):
        return self.category

    def getCategoryNm(self):
        return self.suites.getCategoryInfo(category=self.category, key='category_name', default='')

    def initStatus(self):
        self.status = -1

    def getSuites(self):
        return self.suites

    # ============================ Variable ============================
    def getApplicableVariables(self, step=None, row_index=-1, column_id='', seq=-1):
        '''
        적용가능한 Variable 을 Dictionary형태로 Return
            - 현재 Step의 이전 Step까지 선언된 Variable만 대상
            - 동일 Step의 Output은 불가하고 Input은 가능
            - 동일 Step의 Column, Row가 같은 경우는 불가
            - seq값이 -1보다 큰 경우 step의 seq가 아닌 seq값과 비교함 (seq 에 + 1 함)
        :param step: (class) step
        :param row_index: (int) 0
        :param column_id: (str) 'svc_num'
        :param seq: (int) 13
        :return: {'$SVC_NUM$': (class) variable, ...}
        '''
        step_type = ''
        varialble_dict = {}

        if seq > -1:
            step_seq = seq + 1
        else:
            step_seq = step.getSeq()
            step_type = step.getType()
            print(step_type)

        for variable_id in self.variables:
            variable = self.variables[variable_id]
            variable_target = variable.get('target')

            if variable_target:
                variable_seq = variable_target.getSeq()
            else:
                variable_seq = -1
            variable_sub_id = variable.get('sub_id')
            variable_row_index = variable.get('row_index')
            variable_column_id = variable.get('column_id')

            if variable_seq < step_seq:
                varialble_dict[variable_id] = variable
            elif variable_seq > step_seq:
                pass
            elif variable_seq == step_seq:
                # Seq가 같은 경우 XHR에 대해서만 datalist 순번을 계산하여 추가함
                if step_type == 'XHR':
                    # 동일 Step의 output은 불가
                    if variable_sub_id in variable_target.getDataListId('output'):
                        pass
                    # 동일 Step, Column, Row인 경우 불가
                    elif variable_column_id == column_id and variable_row_index == row_index:
                        pass
                    else:
                        varialble_dict[variable_id] = variable
                else:
                    pass

        return varialble_dict


    def getVariables(self):
        '''
        Case에 포함되어 있는 variable List를 Return
        :return: (list) [{$SVC_MGMT_NUM$:(class) variable}, {...} ... ]
        '''
        return self.variables


    def getVariable(self, variable_id, default=None):
        '''
        variable_id 에 해당하는 (class) variable 을 Return
        :param variable_id: (str) $SVC_MGMT_NUM$
        :param default:
        :return: (class) variable
        '''
        if variable_id in self.variables:
            if self.variables[variable_id] == '':
                return default
            else:
                return self.variables[variable_id]
        else:
            return default


    def getVariableId(self):
        '''
        Case에 포함된 variable의 ID를 List형태로 Return
        :return: (list) [$SVC_MGMT_NUM$, $SVC_NUM$ ...]
        '''
        return list(self.variables.keys())


    def getVariableByType(self, input_variable_type):
        '''
        Case의 variable 중 input_variable_type 해당하는 variable을 List 형태로 Return
        :param variable_type: (str|list) SVC COMBO (Swing Only)
        :return: [ (class) variable1, (class) variable2, ...]
        '''
        find_variables = {}
        variable_type_list = []

        if type(input_variable_type) == list:
            variable_type_list = input_variable_type
        elif type(input_variable_type) == str:
            variable_type_list.append(input_variable_type)

        for variable_type in variable_type_list:
            variable_list_tmp = []

            for variable_id in self.variables:
                variable = self.variables[variable_id]

                if variable.getType() == variable_type:
                    variable_list_tmp.append(variable)

            if variable_list_tmp:
                find_variables[variable_type] = variable_list_tmp

        return find_variables


    def removeVariable(self, variable_id):
        '''
        variable_id에 해당하는 Variable을 Case에서 삭제
            - Step 삭제 시에도 호출함
        :param variable_id: (str) '$SVC_MGMT_NUM$'
        :return: None
        '''
        variable = self.variables[variable_id]

        if variable.getType() == 'Data List':
            step = variable.get('target')

            sub_id = variable.get('sub_id')
            column_id = variable.get('column_id')
            row_index = variable.get('row_index')
            #step.setRowInfoValue(sub_id, row_index, column_id, 'variable', '')
            step.removeRowVariableInfo(sub_id, variable_id)

        del self.variables[variable_id]


    def removeAllVariable(self):
        '''
        case에 포함된 변수를 모두 삭제
        :return: (list) [$variable1$, $variable2$...]
        '''
        variable_id_list = self.getVariableId()

        for variable_id in variable_id_list:
            self.removeVariable(variable_id)

        return variable_id_list


    def loadVariable(self, variables, apply=False, match_index_info={}):
        '''
        Variable Load 시 발생하는 이벤트
        :param variables: (dict) {$SVC_MGMT_NUM1$:...}
        :param apply: True
        :return: (dict) {'$SVC_MGMT_NUM1$': [(class) Row,..], '$SVC_NUM$':[...]}
        '''
        match_variable = {}
        for variable_id in list(variables.keys()):
            row_info = None
            variable = variables[variable_id]

            if variable.variable_type == 'Data List':
                variable_step = variable.get('target')
                sub_id = variable.get('sub_id')
                row_index = variable.get('row_index')
                column_id = variable.get('column_id')
                value = variable_step.getRowInfoValue(sub_id, row_index, column_id, 'value')
                row_info_list = self.findRowByStep(variable_step, variable_step.getTrxCode(), sub_id, row_index, column_id, value)

                if row_info_list:
                    match_variable[variable_id] = row_info_list

                    if apply:
                        try:
                            index = match_index_info[variable_id]
                        except KeyError:
                            index = -1

                        if index > -1:
                            row_info = row_info_list[index]
                            step = row_info.getStep()
                            ref_target_list = variable.get('ref_option_list')

                            try:
                                del variable['ref_target_list']
                                del variable['ref_option_list']
                            except AttributeError:
                                pass

                            variable.setCase(self)
                            variable['target'] = step
                            row_info['variable'] = variable_id
                            value = variable.getValue()

                            # Case에 variable 추가
                            self.setVariableList(variable)

                            # 동일한 값을 가진 Step의 참조 정보를 variable id로 변경
                            self.setStepRefByValue(value, variable.variable_id, min_row=self.findStepIndexByStep(step), exact_match=True, apply=True)

                            # 참조 옵션정보에 포함된 동일한 Variable ID에 대해서도 적용
                            for row in ref_target_list:
                                ref_target_step = row.getStep()
                                sub_id = row.get('data_list_id')
                                row_index = row.get('row_index')
                                column_id = row.get('column_id')
                                value = ref_target_step.getRowInfoValue(sub_id, row_index, column_id, 'value')
                                find_row_info_list = self.findRowByStep(ref_target_step, ref_target_step.getTrxCode(), sub_id, row_index, column_id, value)

                                for find_row_info in find_row_info_list:
                                    find_row_step = find_row_info.getStep()
                                    find_row_info['ref_target'] = row.get('ref_target')
                                    find_row_info['ref_option'] = row.get('ref_option')

                            #print(row_info.get('value'))
            else:
                ref_target_list = variable.get('ref_target_list')

                for row in ref_target_list:
                    step = row.getStep()
                    sub_id = row.get('data_list_id')
                    row_index = row.get('row_index')
                    column_id = row.get('column_id')
                    value = step.getRowInfoValue(sub_id, row_index, column_id, 'value')
                    find_row_info_list = self.findRowByStep(step, step.getTrxCode(), sub_id, row_index, column_id, value)

                    if apply:
                        variable.setCase(self)
                        if find_row_info_list:
                            try:
                                del variable['ref_target_list']
                                del variable['ref_option_list']
                            except AttributeError:
                                pass

                            self.setVariableList(variable)

                            for find_row_info in find_row_info_list:
                                find_row_info['ref_target'] = variable_id
                    else:
                        if find_row_info_list:
                            break

                if find_row_info_list:
                    match_variable[variable_id] = ''

        return match_variable


    def changeVariable(self, new_id, old_id, variable):
        '''
        variable 변경 시 호촐되는 이벤트
            - key값(variable_id) 변경 시 dictionary의 순서는 유지하고 key값과 value값을 변경함
        :param new_id: '$SVC_MGMT_NUM2$'
        :param old_id: '$SVC_MGMT_NUM1$'
        :param variable: (class) variable
        :return: None
        '''
        if new_id == old_id:
            self.variables[variable.variable_id] = variable
        else:
            self.variables = change_key(self.variables, new_id, old_id)
            self.variables[new_id] = variable

            if variable.variable_type == 'Data List':
                step = variable.get('target')
                step.setRowInfoValue(variable.get('sub_id'), variable.get('row_index'), variable.get('column_id'), 'variable', new_id)


    def setStepRefByVariableId(self, new_variable_id, old_variable_id, apply=False):
        '''
        Case의 Step 전체에서 old_variable_id 값과 동일한 Row의 참조 정보를 new_variable_id 로 변경함
        :param new_variable_id: '$SVC_MGMT_NUM2$'
        :param old_variable_id: '$SVC_MGMT_NUM1$'
        :param apply: True
        :return: (int) 3
        '''
        find_rows = self.getStepRowsByRef(key='ref_target', variable_id=old_variable_id)

        if apply:
            for row in find_rows:
                row['ref_target'] = new_variable_id

        return len(find_rows)


    def setStepRefOptionByVariableId(self, new_variable_id, old_variable_id, apply=False):
        '''
        Case의 Step 전체에서 old_variable_id 값과 동일한 Row의 참조 Option 정보를 new_variable_id 로 변경함
        :param new_variable_id: '$SVC_MGMT_NUM2$'
        :param old_variable_id: '$SVC_MGMT_NUM1$'
        :param apply: True
        :return: (int) 3
        '''
        find_rows = self.getStepRowsByRef(key='ref_option', variable_id=old_variable_id)

        if apply:
            for row in find_rows:
                if new_variable_id:
                    row['ref_option'] = row.get('ref_option').replace(old_variable_id, new_variable_id)
                else:
                    row['ref_option'] = ''

        return len(find_rows)


    def getVariableValueList(self):
        '''
        Reference Data를 참조하는 variable 중 선수행하여 값의 조회가 필요한 대상을 List로 Return
            - 중복을 제거하여 SQL, SVC COMBO는 CASE 수행 시 1회만 수행 할 수 있도록 List를 만듬
            - 값의 가져오는 수행은 getVariableValue() Function을 이용
        :return: (list) ['개인/내국인 고객', '단말기모델']
        '''
        ref_data_list = []

        for variable_id in list(self.variables.keys()):
            variable = self.variables[variable_id]

            if variable.getType() in ['SVC COMBO (Swing Only)', 'SQL']:
                refRows = self.getStepRowsByRef(key='ref_target', variable_id=variable.variable_id)
                refOptionRows = self.getStepRowsByRef(key='ref_option', variable_id=variable.variable_id)
                variableInclude = False

                for step in self.stepList:
                    if type(step) == BrowserCommand:
                        variableInclude = step.isIncludeVariable(variable_id)

                        if variableInclude:
                            break

                if refRows or refOptionRows or variableInclude:
                    if variable.getType() == 'SVC COMBO (Swing Only)':
                        svc_combo_nm_temp = variable.get('svc_combo_nm')

                        if svc_combo_nm_temp in ref_data_list:
                            pass
                        else:
                            ref_data_list.append(svc_combo_nm_temp)
                    elif variable.getType() == 'SQL':
                        ref_sql_id = variable.get('ref_sql_id')

                        if ref_sql_id in ref_data_list:
                            pass
                        else:
                            ref_data_list.append(ref_sql_id)

        return ref_data_list

    def getVariableValue(self, ref_data, paging=1):
        '''
        Reference Data를 참조하는 variable 중 선수행하여 값의 조회가 필요한 경우 수행
            - SQL, SVC COMBO는 CASE 수행 시 1회만 수행
            - paging 에 해당하는 Row 출력 (Multi Thread로 수행 시 Worker Index별로 데이타를 가져오기 위함)
        :return:
        '''
        ref_data_list = self.getRefData()

        try:
            ref_data_index = next(idx for idx, refDataInfo in enumerate(ref_data_list) if refDataInfo.get('name') == ref_data)
        except StopIteration:
            ref_data_index = -1

        if ref_data_index == -1:
            try:
                ref_data_index = next(idx for idx, refDataInfo in enumerate(ref_data_list) if refDataInfo.getId() == ref_data)
            except StopIteration:
                ref_data_index = -1

        ref_data = ref_data_list[ref_data_index]

        if ref_data:
            ref_data.getValue(paging)

    def getAutoVariableDataList(self):
        '''
        Case에 자동으로 Variable을 생성하기 위해 특정 Length 이상이고 현재 Step 이후에 동일값이 존재하는 경우
        해당 Row를 Dictionary 형태로 Return
        :return: [{value: '9132493609', row: (class) Row, row_list:[(class) Row, ...]}, {}]
        '''
        auto_variable_list = []

        for step in self.stepList:
            if step.getType() == 'XHR':
                row_list = step.getRowByLen('value', 3)

                for row in row_list:
                    row_step = row.getStep()
                    data_list_id = row.get('data_list_id')
                    row_index = row.get('row_index')
                    column_id = row.get('column_id')
                    value = row.get('value')

                    # HEAD정보는 SKIP
                    if data_list_id in ['HEAD', 'params', 'dataInfo']:
                        pass
                    else:
                        #row_info_list = self.findRowByStep(row_step, row_step.getTrxCode(), data_list_id, row_index, column_id, value)

                        # Case의 Step의 Row Data에서 해당 값의 참조가 필요한 대상 Count (Input에서만 검색)
                        row_list = self.getStepRefCntByRowInfo(std_row=row, data_list_type='input', return_type='list')

                        if len(row_list) > 0:
                            try:
                                index = next(idx for idx, info in enumerate(auto_variable_list) if info['value'] == value)
                            except:
                                index = -1

                            if index > -1:
                                pass
                            else:
                                variable_id = makeVariableId(row.get('column_id'))
                                variable_desc = step.getColumnValue(row.get('data_list_id'), row.get('column_id'),'description')

                                # Case의 Step의 Row Data 기준으로 변수로 선언 가능한 대상 리스트를 다시 조회 (Input, Output)
                                variable_row_list = self.getStepRefCntByRowInfo(std_row=row, data_list_type='', return_type='list')
                                variable_row_list.insert(0, row)

                                auto_variable_info = {}
                                auto_variable_info['variable_id'] = variable_id
                                auto_variable_info['variable_desc'] = variable_desc
                                auto_variable_info['value'] = value
                                auto_variable_info['row'] = row
                                auto_variable_info['row_list'] = variable_row_list
                                auto_variable_info['index'] = 0
                                auto_variable_info['variable_row_index'] = 0

                                auto_variable_list.append(auto_variable_info)
                                #print(row_step.getTrxCode(), data_list_id, row_index, column_id, value, str(len(row_list)))

        return auto_variable_list


    def setAutoVariableDataList(self, variable_list):
        '''
        자동으로 변수를 설정함
        :param variable_list: (list) [{value: '9132493609', row: (class) Row, row_list:[(class) Row, ...]}, {}]
        :return: None
        '''
        for variable_info in variable_list:
            variable_index = variable_info['index']
            variable_row_index = variable_info['variable_row_index']
            variable_id = variable_info['variable_id']
            row = variable_info['row_list'][variable_index]
            if variable_index > -1:
                row_step = row.getStep()
                data_list_id = row.get('data_list_id')
                row_index = row.get('row_index')
                column_id = row.get('column_id')
                value = row.get('value')

                var = Variable(case=self, variable_type='Data List', variable_id=variable_id)
                var['description'] = variable_info['variable_desc']
                var['target'] = row_step
                var['sub_id'] = data_list_id
                var['row_index'] = variable_row_index
                var['column_id'] = column_id

                row['variable'] = variable_id
                row['marking'] = True

                self.setVariableList(var)
                self.setStepRefByValue(value, variable_id, min_row=self.findStepIndexByStep(row_step), exact_match=True, apply=True)

    def getAutoVariableSvcCombo(self):
        auto_svc_combo_variable_list = []
        # Date
        date_list = ['%Y', '%Y%m', '%Y%m%d', '%Y%m%d%H%M%S']

        for idx, ref_date_format in enumerate(date_list):
            today = date.today()
            ref_date = today.strftime(ref_date_format)

            count = self.setStepRefByValue(ref_date, '', min_row=-1, exact_match=True, apply=False)

            if count > 0:
                variable_id = 'DATE_{}'.format(len(auto_svc_combo_variable_list) + 1)
                variable_id = makeVariableId(variable_id)

                var = Variable(case=self, variable_type='Date', variable_id=variable_id)
                var['description'] = "날짜"
                var['date_option'] = "Today"
                var['designated_date'] = ""
                var['format'] = ref_date_format
                var['value'] = ref_date

                auto_svc_combo_variable_list.append(var)

        ref_data_list = self.getRefData()

        for idx, ref_data in enumerate(ref_data_list):
            if ref_data.getType() == 'SVC COMBO (Swing Only)':
                step = ref_data.get('target')
                row_list = step.getRowByLen('value', 2, data_list_type='output')

                for row in row_list:
                    row_step = row.getStep()
                    data_list_id = row.get('data_list_id')
                    row_index = row.get('row_index')
                    column_id = row.get('column_id')
                    value = row.get('value')

                    if data_list_id == 'output1':
                        # row_info_list = self.findRowByStep(row_step, row_step.getTrxCode(), data_list_id, row_index, column_id, value)

                        # Case의 Step의 Row Data에서 해당 값의 참조가 필요한 대상 Count (Input에서만 검색)
                        variable_row_list = self.getStepRefCntByRowInfo(std_row=row, data_list_type='input', return_type='list')

                        if len(variable_row_list) > 0:
                            #print(ref_data.get('name'), column_id, row_index, value)

                            variable_id = ref_data.get('{}_variable_id'.format(column_id))
                            variable_desc = ref_data.get('{}_desc'.format(column_id))

                            if variable_id:
                                pass
                            else:
                                variable_id = 'TEST_{}'.format(len(auto_svc_combo_variable_list)+1)
                                variable_id = makeVariableId(variable_id)

                            if variable_desc:
                                pass
                            else:
                                variable_desc = ref_data.get('name')

                            var = Variable(case=self, variable_type='SVC COMBO (Swing Only)', variable_id=variable_id)
                            var['description'] = variable_desc
                            var['svc_combo_nm'] = ref_data.get('name')
                            var['ref_data_id'] = ref_data.getId()
                            var['column_id'] = column_id
                            var['row_index'] = row_index
                            var['value'] = value

                            auto_svc_combo_variable_list.append(var)

            elif ref_data.getType() == 'SQL':
                find_ref_data_list = []

                query = ref_data.get('query')
                query_data = query.data
                query_headers = query.headers
                ref_sql_id = ref_data.getId()

                for row_index, row_data in enumerate(query_data):
                    for column_index, value in enumerate(row_data):
                        if len(str(value)) > 2:
                            column_info = query.getOutputInfoByColumn(query_headers[column_index])
                            ref_data_info = {'ref_sql_id': ref_sql_id, 'row_index': row_index, 'column_id': column_info['column'], 'variable_id': column_info['variable_id'], 'desc': column_info['comment'], 'value': str(value)}
                            find_ref_data_list.append(ref_data_info)

                for find_ref_data in find_ref_data_list:
                    value = find_ref_data['value']
                    count = self.setStepRefByValue(value, '', min_row=-1, exact_match=True, apply=False)

                    if count > 0:
                        variable_id = find_ref_data['variable_id']

                        if variable_id:
                            pass
                        else:
                            variable_id = 'TEST_{}'.format(len(auto_svc_combo_variable_list) + 1)
                            variable_id = makeVariableId(variable_id)

                        var = Variable(case=self, variable_type='SQL', variable_id=variable_id)
                        var['description'] = find_ref_data['desc']
                        var['ref_sql_id'] = find_ref_data['ref_sql_id']
                        var['column_id'] = find_ref_data['column_id']
                        var['row_index'] = find_ref_data['row_index']
                        var['value'] = find_ref_data['value']

                        auto_svc_combo_variable_list.append(var)

        return auto_svc_combo_variable_list

    def setAutoVariableSvcCombo(self, variable_list):
        for variable in variable_list:
            self.setVariableList(variable)
            value = variable.getValue()
            setCount = self.setStepRefByValue(value, variable.variable_id, exact_match=True, apply=True)

    # ============================ Step ============================
    def getStep(self, idx=-1, step_id=''):
        if idx > -1:
            self.setSelectedStepRow(idx)
        elif step_id:
            idx = self.findStepIndexByStepId(step_id)
            self.setSelectedStepRow(idx)
        try:
            step = self.stepList[idx]
        except:
            step = None

        return step

    def findStepIndexByStep(self, input_step):
        '''
        Step Id에 해당하는 Step Index를 Return
        :param input_step: (class) step
        :return: (int) 3
        '''
        try :
            index = next(idx for idx, step in enumerate(self.stepList) if step.getId() == input_step.getId())
        except:
            index = -1

        return index

    def findStepIndexByStepId(self, step_id):
        '''
        Step Id에 해당하는 Step Index를 Return
        :param step_id: (str) '643c744a-eda2-4e40-9b52-7a3981785801'
        :return: (int) 3
        '''
        try :
            index = next(idx for idx, step in enumerate(self.stepList) if step.getId() == step_id)
        except:
            index = -1

        return index

    def findStepIndexByTarget(self, target):
        '''
        Target에 해당하는 Step Index를 Return
        :param target: (str) 'ZORDSS03S0100_TR81'
        :return: (int) 3
        '''
        try :
            index = next(idx for idx, step in enumerate(self.stepList) if step.get('target') == target)
        except:
            index = -1

        return index

    def findStepByType(self, step_type, key='', value=''):
        '''
        Case에 step_type과 동일한 Step을 list형태로 Return
            - key 값이 존재하는 경우 key에 해당 정보만 Return
            - key, value 값이 존재하는 경우 key, value에 해당 Step만 Return
        :param step_type: (str) 'Browser'
        :param key: (str) 'target'
        :param value: (str) 'Browser_Name'
        :return: (list) ['Browser1', 'Browser2'..]
        '''
        rst_list = []
        step_list = list(filter(lambda step: step.getType() == step_type, self.stepList))

        if key and value:
            for step in step_list:
                if step.get(key) == value:
                    rst_list.append(step)
        elif key:
            for step in step_list:
                rst_list.append(step.get(key))
        else:
            rst_list = step_list

        return rst_list


    def findStepByText(self, text, step_index=0):
        '''
        text 를 포함하고 있는 Step을 검색하여 index를 Return
            - step의 target, description 내용에서 검색
        :param text: (str) 'ZORD01S'
        :param step_index: 1
        :return: 2
        '''
        try:
            index = next(idx for idx, step in enumerate(self.stepList) if (text.upper() in step.get('target').upper() or text.upper() in step.get('description').upper()) and idx >= step_index)
        except:
            index = -1

        return index


    def findStepByTrxCode(self, trx_code):
        '''
        XHR Step 중 동일한 Trx_Code의 Step을 List 형태로 Return
        :param trx_code: (str) ZORDSS0100090_TR01
        :return: [ (class) step1, (class) step2 ... ]
        '''
        step_list = list(filter(lambda step: step.getType() == 'XHR' and trx_code == step.getTrxCode(), self.stepList))
        return step_list


    def findRowByStep(self, target, trx_code, data_list_id, row, column_id, value):
        '''
        input_step과 동일한 Target, data_list_id, column, row를 가진 Step의 Row를 Return
            - variable을 불러와서 저장 시 사용하기 위함
        :param input_step: (class) step
        :return: (list)[(class) Row, (class) Row....]
        '''
        row_info = None
        row_info_list = []

        try:
            for idx, step in enumerate(self.stepList):
                if step.getType() == 'XHR':
                    step_trx_code = step.getTrxCode()
                    if step_trx_code == trx_code:
                        row_info = step.getRowInfo(data_list_id, row, column_id)

                        if row_info:
                            # 공통으로 사용하는 LOV Transaction의 경우 map_id가 동일하면 설정하도록 함
                            if trx_code == 'ZNGMSLOV00010_TR01':
                                target_map_id = target.getRowInfoValue('input1', 0, 'map_id', 'value')
                                step_map_id = step.getRowInfoValue('input1', 0, 'map_id', 'value')

                                if target_map_id == step_map_id:
                                    row_info_list.append(row_info)
                                else:
                                    row_info = None
                            else:
                                row_info_list.append(row_info)
                            # value의 문자열 길이도 같아야 하도록 설정 (동일한 TR을 호출하는 경우가 존재하기때문에 Ex)LOV)
                            # 길이로 하는 경우 요금제명과 같이 변경되면 제외됨
                            #if len(row_info.get('value').encode('utf-8')) == len(value.encode('utf-8')):
                            #    break
                else:
                    pass
        except Exception as e:
            print(e)
            pass

        return row_info_list


    def findDataByText(self, text, step_index, data_list_id, row_index, column_index):
        '''
        Case 내에서 text에 해당하는 값을 검색
        :param text: (str) 'NGM'
        :param step_index: (int) 3
        :param data_list_id: (str) 'input1'
        :param row_index: 0
        :param column_index: 2
        :return: (int) find_step_index, (str) find_data_list_id, (int) find_row_index, (int) find_column_index, (str) find_column_id
        '''
        find_rows = []
        for idx, step in enumerate(self.stepList):
            if idx < step_index:
                continue

            step_find_rows = step.getRowByText(text=text, step_index=step_index, find_data_list_id=data_list_id, data_list_type='')

            find_rows.extend(step_find_rows)

        if find_rows:
            try:
                find_row = None
                for idx, row in enumerate(find_rows):

                    if self.findStepIndexByStepId(row.getStepId()) == step_index and row.get('row_index') >= row_index and row.get('column_index') >= column_index:
                        find_row = row
                        break
                    elif self.findStepIndexByStepId(row.getStepId()) > step_index and row.get('row_index') >= 0 and row.get('column_index') >= 0:
                        find_row = row
                        break
                if find_row:
                    find_step_index = self.findStepIndexByStepId(find_row.getStepId())
                    find_data_list_id = find_row.get('data_list_id')
                    find_row_index = find_row.get('row_index')
                    find_column_index = find_row.get('column_index')
                    find_column_id = find_row.get('column_id')
                else:
                    find_step_index = -1
                    find_data_list_id = ''
                    find_row_index = -1
                    find_column_index = -1
                    find_column_id = ''
            except Exception as e:
                print(str(e))
                find_step_index = -1
                find_data_list_id = ''
                find_row_index = -1
                find_column_index = -1
                find_column_id = ''
        else:
            find_step_index = -1
            find_data_list_id = ''
            find_row_index = -1
            find_column_index = - 1
            find_column_id = ''
        #print(find_step_index, find_data_list_id, find_row_index, find_column_index, find_column_id)
        return find_step_index, find_data_list_id, find_row_index, find_column_index, find_column_id


    def findMaxElapsedTimeStep(self, rank=1):
        '''
        XHR Step 중 수행시간이 가장 Step을 List 형태로 Return
        :param rank: (int) 1
        :return:
        '''
        step_list = list(filter(lambda step: step.getType() == 'XHR', self.stepList))
        elapsed_time_list = []

        for step in step_list:
            #elapsed_time = datetime.datetime.strptime(step.get('exec_time', '0:00:00.0')) - datetime.datetime.strptime('1900-01-01', '%Y-%m-%d')
            elapsed_time = step.get('exec_time')

            if elapsed_time:
                elapsed_time_list.append(elapsed_time)

        elapsed_time_list = sorted(set(elapsed_time_list), reverse=True)

        elapsed_max_time_step_list = list(filter(lambda xhr_step: xhr_step.get('exec_time') in elapsed_time_list[0:rank], step_list))

        return elapsed_max_time_step_list


    def getStepCount(self):
        return len(self.stepList)

    def getSelectedStepRow(self):
        return self.selectedStepRow

    def removeStep(self, step):
        remove_variable_list = step.getVariables()
        self.stepList.remove(step)
        self.selectedStepRow = -1

        for variable_id in remove_variable_list:
            self.removeVariable(variable_id)


    def removeStepByExcludeTrList(self, excluded_tr_list, apply=False):
        '''
        excluded_tr_list 에 존재하는 TR은 Step에서 삭제
        :param excluded_tr_list:
        :param apply: True
        :return: (int) 1
        '''
        remove_list = []

        if excluded_tr_list:
            for idx, step in enumerate(self.stepList):
                try:
                    inputData = step.input_data
                    trId = inputData['HEAD']['Trx_Code']

                    index = findDictIndexByValue(excluded_tr_list, 'tr_id', trId)

                    if index > -1:
                        remove_list.append(step)
                except KeyError:
                    pass

            if apply:
                for remove_step in remove_list:
                    self.removeStep(remove_step)

        return len(remove_list)

    def removeAllStep(self):
        self.stepList = []
        self.selectedStepRow = -1

    def initStepStatus(self):
        for idx, step in enumerate(self.stepList):
            step.initStatus()


    def resetStepRowInfo(self):
        '''
        Case에 포함된 모든 Step의 RowInfo를 재설정함
        :return:
        '''
        for idx, step in enumerate(self.stepList):
            step.resetRowInfo()


    def getStepRefCntByRowInfo(self, std_row, data_list_type='input', return_type='count'):
        '''
        Case의 Step 전체에서 (class)Row값과 동일한 Row의 Count를 Return
            - Row의 value를 기준으로 검색
            - 동일한 Step의 동일한 DataList의 Column은 제외
            - 동일한 Step의 Output 은 Input의 값이 될 수 없기때문에 제외
        :param std_row: (class) Row
        :param data_list_type: 'input'
        :param return_type: 'count'
        :return: (int) or (list)
        '''
        find_rows = []
        resultList = []

        std_row_step = std_row.getStep()
        data_list_id = std_row.get('data_list_id')
        row_index = std_row.get('row_index')
        column_id = std_row.get('column_id')
        find_value = std_row.get('value')
        minRow = self.findStepIndexByStep(std_row_step)

        if find_value and find_value != "0":
            for idx, step in enumerate(self.stepList):
                if idx < minRow:
                    continue

                step_find_rows = step.getRowByValue(key='value', value=find_value, data_list_type=data_list_type, exact_match=True)

                find_rows.extend(step_find_rows)

            for row in find_rows:
                # 동일 Step의 경우
                if row.getStepId() == std_row.getStepId():
                    # 동일한 DataList의 Column은 제외
                    if row.get('data_list_id') == data_list_id and row.get('column_id') == column_id:
                        skip = True
                    # 동일한 Step의 Output 은 Input의 값이 될 수 없음 (Input 체크인 경우만)
                    elif data_list_type=='input' and row.get('data_list_id') == data_list_id and row.get('data_list_id') in step.getDataListId('output'):
                        skip = True
                    else:
                        resultList.append(row)

                else:
                    resultList.append(row)

        if return_type == 'count':
            return len(resultList)
        elif return_type == 'list':
            return resultList


    def setStepRefByValue(self, find_value, variable_id, min_row=-1, return_type='count', exact_match=False, apply=False):
        '''
        Case의 Step 전체에서 find_value 값과 동일한 Row의 참조 정보를 variable_id 로 변경함
        :param find_value: 7011858411
        :param variable_id: $SVC_MGMT_NUM$
        :param return_type: 'count'
        :param apply: True
        :return: (int) or (list)
        '''
        find_rows = []
        resultList = []
        variable = self.getVariable(variable_id)

        if min_row > -1:
            minRow = min_row
        else:
            minRow = 0

        if find_value and find_value != "0":
            for idx, step in enumerate(self.stepList):
                if idx < minRow:
                    continue

                step_find_rows = step.getRowByValue(key='value', value=find_value, data_list_type='input', exact_match=exact_match)

                find_rows.extend(step_find_rows)

            for row in find_rows:
                # 변수값이 없는 경우
                if variable is None:
                    resultList.append(row)

                    if apply:
                        row['ref_target'] = variable_id
                # 동일 Step의 경우
                elif row.getStepId() == variable.getStepId():
                    # 동일한 DataList의 Column은 제외
                    if row.get('data_list_id') == variable.get('sub_id') and row.get('column_id') == variable.get('column_id'):
                        skip = True
                    # 동일한 Step의 Output 은 Input의 값이 될 수 없음
                    elif row.get('data_list_id') == variable.get('sub_id') and row.get('data_list_id') in step.getDataListId('output'):
                        skip = True
                    else:
                        resultList.append(row)

                        if apply:
                            row['ref_target'] = variable_id
                else:
                    resultList.append(row)

                    if apply:
                        row['ref_target'] = variable_id

        if return_type == 'count':
            return len(resultList)
        elif return_type == 'list':
            return resultList


    def getRefData(self):
        return self.suites.getRefDataList()


    def setRefExcelUsed(self):
        for refData in self.usedData:

            if type(refData) == str:
                pass
            else:
                refData['Used'] = 1

        self.usedData = []

    def getStepRowsByRef(self, key, variable_id):
        '''
        Case의 Step 전체에서 old_variable_id 값과 동일한 Row의 참조 정보를 가지고 있는 Row를 List 형태로 Return
        :param variable_id: '$SVC_MGMT_NUM2$'
        :return: (list) [(class) Row1, Row2...]
        '''

        find_rows = []
        for idx, step in enumerate(self.stepList):
            step_find_rows = step.getRowByValue(key=key, value=variable_id, data_list_type='input', exact_match=True)

            find_rows.extend(step_find_rows)

        return find_rows

    def clearMarkingData(self):
        '''
        case id가 동일한 Marking Data 삭제
        :return: None
        '''
        marking_data = self.loadMaringData()
        save_marking_data = []

        for data in marking_data:
            if data['case_id'] == self.caseId:
                pass
            else:
                save_marking_data.append(data)

        self.saveMarkingData(save_marking_data)


    def getMarkingData(self, worker_id, step, load=True):
        '''
        Marking Data를 생성함
        :param worker_id:
        :return:
        '''

        if load:
            marking_data = self.loadMaringData()
        else:
            marking_data = []


        selectedStep = step

        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

        index = findDictIndexByValue(marking_data, 'test_data_id', worker_id)

        tmp_marking_data = []

        maring_row_list = selectedStep.getMarkingRow()

        for marking_row in maring_row_list:
            markingDataDtl = {'target': selectedStep.get('target'),
                              'dataList_id': marking_row.get('data_list_id'),
                              'row_index': marking_row.get('row_index'),
                              'column_id': marking_row.get('column_id'),
                              'value': marking_row.get('value'),
                              'step_id': marking_row.getStepId()}

            if index > -1:
                try:
                    marking_data_index = next(idx for idx, row in enumerate(marking_data[index]['marking_data']) if
                                              row['step_id'] == selectedStep.getId() and row['row_index'] == marking_row.get('row_index') and row['column_id'] == marking_row.get('column_id'))
                except StopIteration:
                    marking_data_index = -1

                if marking_data_index > -1:
                    marking_data[index]['marking_data'][marking_data_index] = markingDataDtl
                else:
                    tmp_marking_data.append(markingDataDtl)
            else:
                tmp_marking_data.append(markingDataDtl)

        if index > -1:
            #marking_data[index]['start_time'] = nowDatetime
            marking_data[index]['marking_data'].extend(tmp_marking_data)
        else:
            # Seq채번
            test_data_name = make_marking_seq(marking_data, self.caseId)

            markingInfo = {'suites_id' : self.suites.getId(),
                           'case_id': self.caseId,
                           'test_data_name': test_data_name,
                           'test_data_id': worker_id,
                           'start_time': nowDatetime,
                           'end_time': '',
                           'result': 0,
                           'result_msg': '',
                           'marking_data': tmp_marking_data}

            marking_data.append(markingInfo)

        if load:
             self.saveMarkingData(marking_data)
        else:
            return marking_data


    def setMarkingDataResult(self, worker_id, result, msg, input_marking_data=None):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

        if input_marking_data:
            marking_data = input_marking_data
        else:
            marking_data = self.loadMaringData()

        index = findDictIndexByValue(marking_data, 'test_data_id', worker_id)

        if index > -1:
            marking_data[index]['result'] = result
            marking_data[index]['result_msg'] = msg
            marking_data[index]['end_time'] = nowDatetime

        if input_marking_data:
            return marking_data
        else:
            self.saveMarkingData(marking_data)


    def loadMaringData(self, case_id=''):
        marking_data = []

        if os.path.exists(self.MARKING_SAVE_FILE_PATH):
            with open(self.MARKING_SAVE_FILE_PATH, 'rb') as f:
                marking_data = pickle.load(f)

                if case_id:
                    marking_data = list(filter(lambda data: data['case_id'] == case_id, marking_data))

        return marking_data


    def saveMarkingData(self, marking_data):
        with open(self.MARKING_SAVE_FILE_PATH, 'wb') as f:
            pickle.dump(marking_data, f, pickle.HIGHEST_PROTOCOL)


    def resetTransactionNm(self):
        '''
        Transaction 명을 현행화
        :return: None
        '''
        for step in self.stepList:
            if step.getType() == 'XHR':
                target = step.get('target')
                tx_name = findTrName(target)
                step['target_nm'] = tx_name


    def getRefStepByValue(self, find_value):
        findRefData = []

        for idx, step in enumerate(self.stepList):
            if idx >= self.selectedStepRow:
                break

            inputData = step.getSelectedInputData()
            outputData = step.getSelectedOutputData()

            findRefInputData = structure.findRefColumn(step, inputData, find_value, find_option='value')
            findRefOutputData = structure.findRefColumn(step, outputData, find_value, find_option='value')

            findRefData.extend(findRefInputData)
            findRefData.extend(findRefOutputData)
        return findRefData


    def getRefStepByColumn(self, find_column):
        findRefData = []

        for idx, step in enumerate(self.stepList):
            if idx >= self.selectedStepRow:
                break

            inputData = step.getSelectedInputData()
            outputData = step.getSelectedOutputData()

            findRefInputData = structure.findRefColumn(step, inputData, find_column, find_option='key')
            findRefOutputData = structure.findRefColumn(step, outputData, find_column, find_option='key')

            findRefData.extend(findRefInputData)
            findRefData.extend(findRefOutputData)
        return findRefData


    def setStepRefByExcelToday(self, ref_method, ref, ref_target):
        target, dataListId, column, row, stepId = parsingRef(ref_target)

        step_index = self.findStepIndexByStepId(stepId)
        step = self.stepList[step_index]
        step_column_index = step.getDataInfoColumnIndex(dataListId, column)

        step.setInputDataInfoValue(dataListId, step_column_index, 'ref_method', ref_method)
        step.setInputDataInfoValue(dataListId, step_column_index, 'ref', ref)

    def getAllStepRefList(self):
        return structure.stepRefRelListAll(self.stepList)

    def getRefedStepColumnList(self, ref):
        return structure.getRefedStepColumnList(self.stepList, ref)