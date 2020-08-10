import uuid
import uuid
import json
from libs.xhr import Xhr
from utils.lib import refOption

class Query:
    def __init__(self, sql='', bind={}):
        self.id = str(uuid.uuid4())
        self.session = None
        self.cur = None
        self.case = None
        self.sql = sql
        self.bind = bind
        self.bind_info_list = []
        self.output_info_list = []

        self.headers = []
        self.data = []
        self.row_count = 0
        self.column_count = 0

    def __getstate__(self):
        state = self.__dict__.copy()
        try:
            del state['cur']
        except KeyError:
            pass
        return state

    def getSql(self):
        return self.sql

    def getBind(self, case=None):
        bind = {}

        if case:
            for bind_variable in list(self.bind.keys()):
                bind_info = self.getBindInfoByVariable(bind_variable)
                bind_value = bind_info['value']
                bind_ref_option = bind_info['ref_option']
                variable = case.getVariable(bind_value)

                if variable:
                    value = variable.getValue()
                    if bind_ref_option:
                        value = refOption(case, value, bind_ref_option)
                else:
                    value = bind_value

                bind[bind_variable] = value
        else:
            bind = self.bind

        print(bind)
        return bind

    def setSql(self, sql):
        self.sql = sql

    def setQueryModel(self, model):
        '''
        QueryModel의 값을 저장
            - QueryModel(QAbstractTableModel) 값을 query 내부에 저장
            - query 내용을 다시 Setting하는 경우에 사용하기 위해 저장
        :param model: (class) model
        :return: None
        '''
        self.headers = model._headers
        self.data = model._data
        self.row_count = model._row_count
        self.column_count = model._column_count

    def setSession(self, session):
        self.session = session

    def setBindInfo(self, bind_info_list):
        '''
        input 변수 정보가 List형태로 들어오면 dictionary 형태의 bind 값으로 저장
        :param bind_info_list: (list) [{'bind_variable':'iparam1', 'db_type':'String', 'comment':'서비스번호', 'value': '01012345678'}, {}...]
        :return: None
        '''
        self.bind_info_list = bind_info_list
        self.bind = {}

        for bind_info in bind_info_list:
            var = bind_info['bind_variable']
            val = bind_info['value']

            self.bind[var] = val

    def setOutputInfo(self, output_info_list):
        '''
        output 정보를 저장
            - query가 다시 Load 되면 출력정보를 Setting하기 위함
        :param output_info_list: (list) [{'column':'svc_mgmt_num', 'variable_id':'$SVC_MGMT_NUM$', 'comment':'서비스관리번호'}, {}...]
        :return: None
        '''
        self.output_info_list = output_info_list

    def getOutputInfo(self):
        '''
        output정보를 리스트 형태로 Return
        :return: (list) [{'column':'svc_mgmt_num', 'variable_id':'$SVC_MGMT_NUM$', 'comment':'서비스관리번호'}, {}...]
        '''
        return self.output_info_list

    def getBindInfoByVariable(self, bind_variable):
        '''
        변수명에 해당하는 변수정보를 Return 함
        :param bind_variable: (str) 'iparam1'
        :return: (dict) {'bind_variable':'iparam1', 'db_type':'String', 'comment':'서비스번호', 'value': '01012345678'}
        '''

        bind_info = {}

        try:
            index = next(idx for idx, bind_info_tmp in enumerate(self.bind_info_list) if bind_info_tmp['bind_variable'] == bind_variable)
        except StopIteration:
            index = -1
        except KeyError:
            index = -1

        if index > -1:
            bind_info = self.bind_info_list[index]

        return bind_info


    def getOutputInfoByColumn(self, column):
        '''
        Column에 해당하는 Output정보를 Return 함
        :param bind_variable: (str) 'iparam1'
        :return: (dict) {'column':'svc_mgmt_num', 'variable_id':'$SVC_MGMT_NUM$', 'comment':'서비스관리번호'}
        '''

        output_info = {}

        try:
            index = next(idx for idx, output_info_tmp in enumerate(self.output_info_list) if output_info_tmp['column'] == column)
        except StopIteration:
            index = -1
        except KeyError:
            index = -1

        if index > -1:
            output_info = self.output_info_list[index]

        return output_info


    def getHeaders(self):
        return self.headers


    def connect(self):
        '''
        Session 연결
        :return:
        '''
        self.disconnect()

        if self.session:
            self.session.connection()
            self.connected.emit(self.session.getSid())


    def disconnect(self):
        '''
        Session 연결종료
        :return:
        '''
        if self.session:
            self.session.disconnection()
            self.disconnected.emit()

    def execute(self, case=None):
        '''
        SQL 수행
        :return:
        '''
        if self.session.getSid() == 'SWGS.JSD':
            print('수행')
        else:
            self.cur = self.session.getCursor()
            sql = self.getSql()

            if case:
                self.case = case

            bind = self.getBind(self.case)

            try:
                if bind:
                    self.cur.execute(sql, bind)
                else:
                    self.cur.execute(sql)

                print(self.cur.description)
                cursor_description = self.cur.description
                self.headers = [h[0] for h in cursor_description]
                self.column_count = len(self.headers)
                self.row_count = 0
                self.data = []
            except Exception as e:
                raise Exception(e)

    def fetchOne(self):
        '''
        첫번째 Row 조회
        :return: (tuple) ('700000001', '01012345678', 'C', 'AC')
        '''
        if self.session.getSid() == 'SWGS.JSD':
            self.data = []
            rows = self.fetchJsd(limit=1)
            if rows:
                first_row = rows[0]
            else:
                first_row = {}
        else:
            first_row = self.cur.fetchone()
            #print(first_row)
            self.data = [first_row]
            self.row_count = 1

        return first_row

    def fetchMore(self, limit=100):
        '''
        limit 만큼 추가로 조회
        :param limit: (int) 100
        :return: (list) [('700000002', '01011112222', 'C', 'AC'), ('700000003', '01033334444', 'C', 'AC')...]
        '''
        if self.session.getSid() == 'SWGS.JSD':
            more_row = self.fetchJsd(limit=limit)
        else:
            more_row = self.cur.fetchmany(limit)
            count = self.row_count + len(more_row)
            self.data.extend(more_row)
            self.row_count = count

        return more_row

    def fetchAll(self):
        '''
        전체 조회
            - JSD로 전체 조회하는 경우는 100개의 Row로 한정
        :return: (list) [('700000002', '01011112222', 'C', 'AC'), ('700000003', '01033334444', 'C', 'AC')...]
        '''
        if self.session.getSid() == 'SWGS.JSD':
            self.data = []
            all_row = self.fetchJsd(limit=100)
        else:
            all_row = self.cur.fetchall()
            self.data.extend(all_row)
            self.row_count = len(self.data)

        return all_row

    def getDescription(self):
        return self.cur.description


    def fetchJsd(self, limit=1):
        bind = self.getBind(self.case)
        jsd_bind = ''
        #print(bind)
        if bind:
            for idx, row in enumerate(bind):
                if idx == 0:
                    jsd_bind += ('\n                    "' + row + '": "' + bind[row] + '"')
                else:
                    jsd_bind += (',\n                    "' + row + '": "' + bind[row] + '"')
            jsd_bind += '\n                '

        inputData = "{'input1': [{'test_object_id': 'SQL', 'rollback_yn': '', 'skip_prod_log_yn': '', 'svc_proc_yn': '', 'rowStatus': 'C'}], 'input2': [{'json_string': '', 'rowStatus': 'C'}], 'HEAD': {'Trx_Code': 'ZORDSCOM06010_TR01', 'Ngms_UserId': '1000495877', 'Ngms_LogInId': 'YUNWOONG', 'Ngms_EmpNum': '', 'Ngms_OrgId': 'A000700000', 'Ngms_HrOrgCd': '', 'Ngms_PostOrgCd': 'A000700000', 'Ngms_PostSaleOrgCd': 'A000700000', 'Ngms_SupSaleOrgCd': 'A010890000', 'Ngms_IpAddr': '150.28.79.196', 'Ngms_BrTypCd': '450', 'Ngms_AuthId': '', 'Ngms_ConnOrgId': 'A000700000', 'Ngms_ConnOrgCd': 'A000700000', 'Ngms_ConnSaleOrgId': 'A000700000', 'Ngms_ConnSaleOrgCd': 'A000700000', 'Ngms_AuthTypPermCd': 'EQ', 'Ngms_PostSaleOrgId': 'A000700000', 'Ngms_SupSaleOrgId': 'A010890000', 'Term_Type': '0', 'User_Term_Type': '', 'St_Stop': '0', 'St_Trace': '', 'Stx_Dt': '', 'Stx_Tm': '', 'Etx_Dt': '', 'Etx_Tm': '', 'Rt_Cd': '', 'Screen_Name': 'ZORDSCOM06010', 'Msg_Cnt': '0', 'Handle_Id': '62617279  ', 'Ngms_Filler1': '', 'Ngms_CoClCd': 'T', 'Screen_Call_Trace': 'Top-ZORDSCOM06010-ZORDSCOM06010_TR01', 'rowStatus': 'C'}}"
        json_string = '\x01\x0c{\n    "io": {\n        "ordscom06010t01": {\n            "in": {\n                "sql": "%s",\n                "exe_sql": true,\n                "variables": {%s},\n                "offset": %d,\n                "fetch_count": %d\n            }\n        }\n    }\n}\x01\x0c'%(self.sql.lstrip().replace('\n', '\\n').replace('\r', '').replace("\'", "'").replace('"', '\\"'), str(jsd_bind).replace('\'', '\"'), len(self.data)+1, limit)
        #print(json_string)
        step = Xhr(None)
        step.setInputData(inputData)
        step.setInputDataValue('input2', 0, 'json_string', json_string)
        step.resetDataListBySize('input2', 0, 'json_string', 512)

        #step['log_enable'] = True
        step.startStep()

        code = step.getParamsCode()
        msg = step.getParamsMsg()

        if code > 0:
            raise Exception(msg)
        else:
            cursor_description_tmp = ''

            # Column Header정보
            output1 = step.getDataList('output1')
            for row in output1:
                cursor_description_tmp += (row['json_string'])

            cursor_description_tmp = cursor_description_tmp.replace('\x01\x0c', '')
            cursor_description = json.loads(cursor_description_tmp)

            if cursor_description['sqlcode'] < 0 :
                raise Exception(cursor_description['sqlerrmc'])
            else:
                self.headers = [h['id'] for h in cursor_description['columns']]
                self.column_count = len(self.headers)

                if cursor_description['sqlcode'] > 0:
                    return []
                else:
                    # Data 정보
                    output2 = step.getDataList('output2')
                    data_tmp = ''
                    for row in output2:
                        data_tmp += (row['json_string'])

                    data_tmp = data_tmp.replace('\x01\x0c', '')
                    data_list = json.loads(data_tmp)

                    for row_data in data_list:
                        self.data.append(tuple(row_data.values()))

                    self.row_count = len(self.data)

                return self.data
