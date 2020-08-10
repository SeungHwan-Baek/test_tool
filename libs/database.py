from libs.step import Step
from utils.queryModel import QueryModel
from utils.config import Config

class Database(Step):
    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)
        self.case = case

    def startStep(self):
        step_type = self.getType()

        if step_type == 'Validation':
            query = self.get('query')
            validation_chk = self.get('validation_chk')

            try:
                query.execute(self.case)
                query.fetchAll()

                model = QueryModel()
                model.setQuery(query)
                #model.execute(self.case)

                row_cnt = model.getRowCount()

                if validation_chk == 'Data Exists' and row_cnt > 0:
                    isOk = True
                elif validation_chk == 'Data Not Exists' and row_cnt == 0:
                    isOk = True
                else:
                    isOk = False

                if isOk:
                    code = 0
                    msg = '정상적으로 처리가 완료되었습니다.'
                    self.setStatus(code, msg)
                else:
                    code = 1
                    msg = '검증결과 오류가 존재합니다.'
                    self.setStatus(code, msg)
            except Exception as e:
                config = Config()
                error_skip = config.getBoolean('section_database', 'ERROR_SKIP')

                if self.getErrOption() == 'Skip':
                    self.setStatus(999, str(e))
                elif error_skip:
                    self.setStatus(999, str(e))
                else:
                    self.setStatus(1, str(e))
            finally:
                self['query'] = query