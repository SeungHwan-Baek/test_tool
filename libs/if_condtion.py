import time
from libs.step import Step
from libs.condition import Condition

class If(Step):
    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)
        self.case = case
        self.type = step_type
        self.condition_list = []
        self.step_list = []

    def getStepList(self):
        return self.step_list

    def clearCondition(self):
        self.condition_list = []

    def setCondition(self, variable, operator, value):
        condition = Condition(self.case)
        condition.setTargetVariable(variable)
        condition.setOperator(operator)
        condition.setValue(value)

        self.condition_list.append(condition)

    def setStep(self, step):
        self.step_list.append(step)

    def checkCond(self):
        for cond in self.condition_list:
            if cond.getResult():
                pass
            else:
                return False

        return True

    def startStep(self):
        if self.checkCond():
            self.setStatus(0, '정상적으로 처리가 완료되었습니다.')
            for step in self.step_list:
                step.startStep()
        else:
            self.setStatus(999, '조건을 만족하지 않음')
            print('Skip Step')