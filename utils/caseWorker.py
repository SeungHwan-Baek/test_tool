from PyQt5.QtCore import QThread
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import pyqtSignal

import uuid

class CaseThread(QThread):
    exeCnt = 0
    terminated = pyqtSignal(str, str)
    send_start_step_signal = pyqtSignal("PyQt_PyObject")
    send_end_step_signal = pyqtSignal(int, "PyQt_PyObject", "PyQt_PyObject", int)
    send_start_get_variable = pyqtSignal()
    send_get_variable_signal = pyqtSignal(str)
    send_end_get_variable = pyqtSignal()

    suite = None
    case = None
    error = False
    worker_id = ''

    def __init__(self, suite, case, start_row=0, worker_id='', mainWidget=None):
        QThread.__init__(self)
        self.cond = None
        self.mutex = None
        self._status = True
        self.kill = False
        self.error = False
        self.suite = suite
        self.case = case
        self.mainWidget = mainWidget

        if worker_id == '':
            self.worker_id = str(uuid.uuid4())
            self.case.usedData = []
        else:
            self.worker_id = worker_id

        self.startRow = start_row
        #self.case.setSelectedStepRow(0)

    def __del__(self):
        self.wait()

    def run(self):
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        exeCnt = 0
        usedData = 0

        #self.case.clearMarkingData()
        #ref_data = self.suite.getRefDataList()

        '''
        0번째 Row에서 시작한 경우만 참조데이타를 조회회
       '''
        if self.startRow == 0:
            self.send_start_get_variable.emit()
            ref_data_list = self.case.getVariableValueList()
            self.case.setStatus(0)

            for ref_data in ref_data_list:
                self.send_get_variable_signal.emit(ref_data)
                self.case.getVariableValue(ref_data)

                if self.kill:
                    self.case.setStatus(-1)
                    break

            self.send_end_get_variable.emit()

        for idx, step in enumerate(self.case.stepList):
            if self.kill:
                self.case.setStatus(-1)
                break

            if idx >= self.startRow:
                self.mutex.lock()

                # self.msleep(100)
                if not self._status:
                    self.cond.wait(self.mutex)

                self.case.setSelectedStepRow(idx)

                exeCnt += 1
                self.send_start_step_signal.emit(step)

                try:
                    step.getValueByRef()

                    # Marking Data
                    if step.getType() == 'XHR':
                        self.case.getMarkingData(self.worker_id, step=step)

                    if step.get('step_type_group') in ['Browser', 'Browser Command', 'Browser Command (Swing)']:
                        step.setWeb(self.mainWidget.web)

                    step.startStep()

                    code = step.getParamsCode()
                    msg = step.getParamsMsg()
                except KeyError:
                    code = 1
                    msg = "변수값이 없습니다."
                except StopIteration:
                    code = 1
                    msg = "변수값이 없습니다."
                finally:
                    err_option = step.getErrOption()
                    self.send_end_step_signal.emit((((exeCnt)/(len(self.case.stepList) - self.startRow)) * 100), self.case, step, idx)
                    self.mutex.unlock()

                    # Return 값이 0 이 아니고 Error 발생 옵션인 경우 중지
                    if code > 0 and code != 999 and err_option == 'Stop':
                        self.case.setStatus(1)
                        self.setError()

                        if step.getType() == 'XHR':
                            msg = '({target}) {msg}'.format(target=step.get('target'), msg=msg)

                        self.terminated.emit(self.worker_id, msg)
                        break
                    elif self.kill:
                        self.case.setStatus(-1)
                        break

    def toggle_status(self):
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status

    def stop(self):
        self.kill = True

    def setError(self):
        self.error = True

    def getError(self):
        return self.error