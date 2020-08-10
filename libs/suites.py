import uuid
import os, pickle

__version_info__ = ('0', '1', '0')
__version__ = '.'.join(__version_info__)

class Suites:
    category = []
    suiteId = ''
    suiteNm = ''
    refDataList = []
    caseList = []

    excludedTrList = []

    selectedCaseId = ''

    refPath = ''
    fileNm = ''

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    REF_SAVE_PATH = os.path.join(SAVE_PATH, 'ref', 'ref.ref_info')
    MARKING_SAVE_FILE_PATH = os.path.join(SAVE_PATH, 'marking', '.marking_info')

    def __init__(self, suite_nm='Test Suite'):
        self.suiteId = ''
        self.suiteNm = ''
        self.refDataList = []
        self.category = []
        self.caseList = []
        self.excludedTrList = []

        self.suiteId = str(uuid.uuid4())
        self.suiteNm = suite_nm
        self.modified_time = ''

    def version(self):
        return __version__

    def getId(self):
        return self.suiteId

    def getCaseCount(self, case_type=''):
        if case_type:
            filterList = list(filter(lambda case: case.getCaseType() == case_type, self.caseList))
            case_cnt = len(filterList)
        else:
            case_cnt = len(self.caseList)

        return case_cnt

    def getRefDataList(self):
        return self.refDataList

    def getFileNm(self):
        return self.fileNm

    def getExcludedTrList(self):
        return self.excludedTrList

    def getSuitesNm(self):
        return self.suiteNm

    def getModifiedTime(self):
        return self.modified_time

    def getSelectedCaseId(self):
        return self.selectedCaseId

    def setRefDataList(self, ref_data_list):
        self.refDataList = ref_data_list

    def setCaseList(self, case):
        if case:
            case.openCase(self)
            self.caseList.append(case)

    def setFileNm(self, file_nm):
        self.fileNm = file_nm

    def setExcludedTrList(self, excluded_tr_list):
        self.excludedTrList = excluded_tr_list

    def setModifiedTime(self, time):
        self.modified_time = time

    def initCaseStatus(self):
        for idx, case in enumerate(self.caseList):
            case.initStatus()

    def findCaseIndex(self, case_id):
        try :
            index = next(idx for idx, case in enumerate(self.caseList) if case.caseId == case_id)
        except:
            index = -1
        return index

    def findCase(self, case_id, selected=True):
        if selected:
            self.selectedCaseId = case_id

        index = self.findCaseIndex(case_id)

        if index > -1:
            case = self.caseList[index]
        else:
            case = None

        return case

    def selectedCase(self):
        index = self.findCaseIndex(self.selectedCaseId)

        if index > -1:
            case = self.caseList[index]
        else:
            case = None
        return case

    def removeCase(self, case):
        self.caseList.remove(case)
        self.selectedCaseId = ''


    def getCategoryInfo(self, category, key, default=None):
        category_info = self.findCategory(category)

        if category_info:
            if key in category_info:
                if category_info[key] == '':
                    return default
                else:
                    return category_info[key]
        return default


    def getCategory(self, copy=False):
        '''
        suites category정보 조회
        :return: (list) [{'category_id' : 'xxxx-xxxx-xxxx-xxxx',
                         'category_name' : 신규가입
                         'parent_category_id' : ''}, ...
                         ]
        '''
        if copy:
            return self.category.copy()
        else:
            return self.category


    def findStepByTrxCode(self, trx_code):
        '''
        XHR Step 중 동일한 Trx_Code의 Step을 List 형태로 Return
        :param trx_code: (str) ZORDSS0100090_TR01
        :return: [ (class) step1, (class) step2 ... ]
        '''
        step_list = []

        for case in self.caseList:
            tmp_step_list = list(filter(lambda step: step.getType() == 'XHR' and trx_code == step.getTrxCode(), case.stepList))
            step_list.extend(tmp_step_list)

        return step_list


    def findCategory(self, category, parent_category_id='', pop=False):
        '''
        category의 ID 또는 Name으로 category 정보를 찾아 Dictionary형태로 Return
        :param category: ('str) category ID 또는 category Name
        :return: (dict) {'category_id' : 'xxxx-xxxx-xxxx-xxxx',
                         'category_name' : 신규가입
                         'parent_category_id' : ''}
        '''
        category_info = {}

        try:
            index = next(idx for idx, suites_category_info in enumerate(self.category) if suites_category_info['category_id'] == category or (suites_category_info['parent_category_id'] == parent_category_id and suites_category_info['category_name'] == category))
        except StopIteration:
            index = -1

        if index > -1:
            if pop:
                category_info = self.category.pop(index)
            else:
                category_info = self.category[index]

        return category_info


    def addCategory(self, category_name, parent_category_id=''):
        '''
        category 추가
        :param category_name:
        :param parent_category_id:
        :return:
        '''

        category_info = {}
        category_info['category_id'] = str(uuid.uuid4())
        category_info['category_name'] = category_name
        category_info['parent_category_id'] = parent_category_id

        try:
            self.category.append(category_info)
        except AttributeError:
            self.category = []
            self.category.append(category_info)

        return category_info

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