import uuid
import re
from utils.lib import refOption

class Step:
    def __init__(self, case=None, step_type=''):
        self.case = case
        self.id = str(uuid.uuid4())
        self.type = step_type
        self.seq = 0
        self.status = -1
        self.msg = ''
        self.info = {}
        self.history = {}

    def __setitem__(self, key, value):
        self.info[key] = value

    def __getitem__(self, key):
        return self.info[key]

    def setSeq(self, seq):
        self.seq = seq

    def setType(self, step_type):
        self.type = step_type

    def setStatus(self, status, msg):
        self.status = status
        self.msg = msg

    def setCase(self, case):
        self.case = case

    def initStatus(self):
        self.status = -1
        self.msg = ''

    def remove(self, key):
        if key in self.info:
            del self.info[key]

    def get(self, key, default=None):
        if key in self.info:
            if self.info[key] == '':
                return default
            else:
                return self.info[key]
        return default

    def getId(self):
        return self.id

    def getSeq(self):
        return self.seq

    def getType(self):
        return self.type

    def getGroup(self):
        return self.get('group')

    def getErrOption(self):
        return self.get('error_option', 'Stop')

    def getKey(self):
        return list(self.info.keys())

    def getParamsMsg(self):
        return self.msg

    def getParamsCode(self):
        return self.status

    def getCondRst(self):
        condition_step_id = self.get('condition_step_id')
        if condition_step_id:
            condition_step = self.case.getStep(step_id=condition_step_id)

            return condition_step.checkCond()
        else:
            return True

    def getCase(self):
        return self.case

    def applyRefOption(self, value, ref_option):
        '''
        참조 옵션이 존재하는 경우 옵션을 적용한 값을 Return
        :param value: (str) '01041262003'
        :param ref_option: (str) 'Substr | 0, 3'
        :return: (unknown-type) '010'
        '''
        return refOption(self.case, value, ref_option)

    def startStep(self):
        print('Start Step')
        pass

    def getRowByValue(self, key, value, data_list_type, exact_match=False):
        return []

    def getValueByRef(self):
        pass

    def getDataListId(self, data_list_type=''):
        return []

    def checkAllRefVariable(self):
        return True

    def getIsRef(self):
        pass

    def getIsVar(self):
        pass

    def getVariables(self):
        return []

    def getRowByText(self, text, step_index, find_data_list_id, data_list_type):
        return []

    def getMarkingRow(self, data_list_type=''):
        return []

    def resetRowInfo(self):
        pass
