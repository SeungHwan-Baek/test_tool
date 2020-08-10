import uuid
from libs.xhr import Xhr
from utils.config import Config

class Reference:
    info = {}

    def __init__(self, ref_type):
        self.ref_type = ref_type
        self.id = str(uuid.uuid4())
        self.info = {}

    def __setitem__(self, key, value):
        self.info[key] = value

    def __getitem__(self, key):
        return self.info[key]

    def get(self, key, default=''):
        if key in self.info:
            if self.info[key] == '':
                return default
            else:
                return self.info[key]
        else:
            if key == 'target':
                self.getXhrSvcCombo()
                return self.info[key]
            else:
                return default

    def getKey(self):
        return list(self.info.keys())

    def initKey(self, key, value):
        if key in self.info:
            pass
        else:
            self.info[key] = value

    def getType(self):
        return self.ref_type

    def getId(self):
        return self.id

    def getXhrSvcCombo(self, paging=1):
        inputData = '{"HEAD":{"Trx_Code":"ZNGMSCOD00010_TR02","Ngms_UserId":"1000495877","Ngms_LogInId":"YUNWOONG","Ngms_EmpNum":"","Ngms_OrgId":"A000700000","Ngms_HrOrgCd":"","Ngms_PostOrgCd":"A000700000","Ngms_PostSaleOrgCd":"A000700000","Ngms_SupSaleOrgCd":"A010890000","Ngms_IpAddr":"150.28.79.196","Ngms_BrTypCd":"450","Ngms_AuthId":"","Ngms_ConnOrgId":"A000700000","Ngms_ConnOrgCd":"A000700000","Ngms_ConnSaleOrgId":"A000700000","Ngms_ConnSaleOrgCd":"A000700000","Ngms_AuthTypPermCd":"EQ","Ngms_PostSaleOrgId":"A000700000","Ngms_SupSaleOrgId":"A010890000","Term_Type":"0","User_Term_Type":"","St_Stop":"0","St_Trace":"","Stx_Dt":"","Stx_Tm":"","Etx_Dt":"","Etx_Tm":"","Rt_Cd":"","Screen_Name":"ZORDSUDCS0040","Msg_Cnt":"0","Handle_Id":"194902345 ","Ngms_Filler1":"","Ngms_CoClCd":"T","Screen_Call_Trace":"Top-ZORDSS03S0000-ZNGMSCOD00010_TR02","rowStatus":"C"},"input1":{"map_id":"zngm_pgm_f0042","iparam1":"ZORDSS03S0000","iparam2":"","iparam3":"","iparam4":"","iparam5":"","iparam6":"","iparam7":"","rowStatus":"C"}}'
        step = Xhr(None)
        map_id = self.get('map_id')
        iparam1 = self.get('iparam1')
        iparam2 = self.get('iparam2')
        iparam3 = self.get('iparam3')
        iparam4 = self.get('iparam4')
        iparam5 = self.get('iparam5')

        # Data Info 추가
        step.setInputData(inputData)
        step.setInputDataValue('input1', 0, 'map_id', map_id)
        step.setInputDataValue('input1', 0, 'iparam1', iparam1)
        step.setInputDataValue('input1', 0, 'iparam2', iparam2)
        step.setInputDataValue('input1', 0, 'iparam3', iparam3)
        step.setInputDataValue('input1', 0, 'iparam4', iparam4)
        step.setInputDataValue('input1', 0, 'iparam5', iparam5)

        step.setInputDataValue('input1', 0, 'iparam6', paging)
        step.setInputDataValue('input1', 0, 'iparam7', 1)
        step.startStep()

        #print(paging, step.getDataList(data_list_id='output1'))

        config = Config()
        replay_cnt = int(config.get('section_reference', 'REPLAY_CNT'))

        # SVC COMBO Load 시 Timeout 또는 값이 없는 경우가 발생하면 2회까지는 재수행
        if step.getParamsCode() > 0 or step.getDataList(data_list_id='output1') == []:
            for i in range(1, replay_cnt+1):
                print('SVC COMBO 재수행')
                step.startStep()

                if step.getParamsCode() == 0 and step.getDataList(data_list_id='output1'):
                    break

        self.info['target'] = step

        return step

    def getSql(self):
        query = self.get('query')
        query.execute()
        query.fetchAll()

    def getRowIndexByValue(self, column_id, value):
        row_index = -1

        if self.ref_type == 'SVC COMBO (Swing Only)':
            step = self.get('target')
            row_index = step.getRowIndexByValue('output1', column_id, value)
        elif self.ref_type == 'SQL':
            query = self.get('query')
            column_index = query.headers.index(column_id)

            for idx, data_row in enumerate(query.data):
                if str(data_row[column_index]) == value:
                    row_index = idx
                    break

        return row_index

    def getRefValue(self, row_index, column_id):
        value = ''

        if self.ref_type == 'SVC COMBO (Swing Only)':
            step = self.get('target')
            try:
                value = step.getRowInfoValue('output1', row_index, column_id, 'value')
            except IndexError:
                pass
        elif self.ref_type == 'SQL':
            query = self.get('query')
            column_index = query.headers.index(column_id)

            try:
                value = query.data[row_index][column_index]
            except IndexError:
                pass

        return value


    def getValue(self, paging=1):
        if self.ref_type == 'SVC COMBO (Swing Only)':
            value = self.getXhrSvcCombo(paging)
        elif self.ref_type == 'SQL':
            query = self.get('query')
            value = query.getSql()

        return value
