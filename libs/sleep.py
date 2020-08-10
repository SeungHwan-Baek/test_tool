import time
from libs.step import Step

class Sleep(Step):
    sec = ''

    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)
        self.case = case

    def startStep(self):
        if self.getCondRst():
            sec = self.get('sec')
            time.sleep(sec)
            code = 0
            msg = '정상적으로 처리가 완료되었습니다.'
            self.setStatus(code, msg)
        else:
            code = 999
            msg = 'Skip'
            self.setStatus(code, msg)
            print('Pass')