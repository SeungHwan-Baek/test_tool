from PyQt5.QtCore import QThread
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import pyqtSignal

import uuid


class SuitesThread(QThread):
    exeCnt = 0
    terminated = pyqtSignal(str, str)
    change_value = pyqtSignal(int, "PyQt_PyObject")
    send_step_start_signal = pyqtSignal("PyQt_PyObject")
    send_step_finish_signal = pyqtSignal(int, int, "PyQt_PyObject", "PyQt_PyObject")
    send_case_signal = pyqtSignal("PyQt_PyObject", int, list)
    send_start_get_variable = pyqtSignal()
    send_get_variable_signal = pyqtSignal(str)
    send_end_get_variable = pyqtSignal()

    suite = None
    error = False

    def __init__(self, suite, case_list=[], worker_index=1, variable_skip=True):
        QThread.__init__(self)
        self.cond = None
        self.mutex =None
        self._status = True
        self.kill = False
        self.error = False
        self.suite = suite
        self.case_list = case_list
        self.worker_index = worker_index
        self.variable_skip = variable_skip

    def __del__(self):
        self.wait()

    def run(self):
        #self.cond = QWaitCondition()
        # self.mutex = QMutex()

        exeCnt = 0

        if self.case_list:
            pass
        else:
            self.case_list = self.suite.caseList

        for idx, case in enumerate(self.case_list):
            case_marking_data = []

            if self.kill:
                case.setStatus(-1)
                break

            # self.mutex.lock()

            # if not self._status:
            #     self.cond.wait(self.mutex)

            # case의 step 상태를 초기화
            case.initStepStatus()

            exeCnt += 1
            self.change_value.emit((((exeCnt)/(len(self.case_list))) * 100), case)

            '''
            Suites Multi Thread 수행 시에는 Skip, 예약 수행 시에는 조회 후 진행
            '''
            if self.variable_skip:
                pass
            else:
                self.send_start_get_variable.emit()
                svc_combo_list = case.getVariableValueList()

                for svc_combo_nm in svc_combo_list:
                    self.send_get_variable_signal.emit(svc_combo_nm)
                    case.getVariableValue(ref_data=svc_combo_nm, paging=1, row_cnt=1)

                    if self.kill:
                        case.setStatus(-1)
                        break

                self.send_end_get_variable.emit()

            worker_id = str(uuid.uuid4())
            case.setStatus(0)

            for idy, step in enumerate(case.stepList):
                if self.kill:
                    case.setStatus(-1)
                    break

                self.send_step_start_signal.emit(step)
                case.setSelectedStepRow(idy)

                try:
                    step.getValueByRef()

                    # Marking Data
                    if step.getType() == 'XHR':
                        step_marking_data = case.getMarkingData(worker_id, step=step, load=False)
                        case_marking_data.extend(step_marking_data)

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
                    self.send_step_finish_signal.emit((((idy+1)/(len(case.stepList))) * 100), idy, case, step)


                    # Return 값이 0 이 아니고 Error 발생 옵션인 경우 중지
                    if code > 0 and code != 999 and err_option == 'Stop':
                        case.setStatus(1)
                        self.setError()
                        break
                    elif self.kill:
                        case.setStatus(-1)
                        break

            case.setWorkerIndex(0)
            case_marking_data = case.setMarkingDataResult(worker_id, 0, "Successful", case_marking_data)
            self.send_case_signal.emit(case, idx, case_marking_data)
            # self.mutex.unlock()

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



class SuitesRefThread(QThread):
    exeCnt = 0
    terminated = pyqtSignal(str, str)
    send_start_get_variable = pyqtSignal(int)
    send_get_variable_signal = pyqtSignal(str)
    send_end_get_variable = pyqtSignal(int, int)

    suite = None
    error = False

    def __init__(self, suite, case_list=[], thread_cnt=1):
        QThread.__init__(self)
        self.cond = None
        self.mutex = None
        self._status = True
        self.kill = False
        self.error = False
        self.suite = suite
        self.case_list = case_list
        self.thread_cnt = thread_cnt

    def __del__(self):
        self.wait()

    def run(self):
        all_ref_data_list = []
        finished_ref_data = []

        #self.cond = QWaitCondition()

        exeCnt = 0

        if self.case_list:
            pass
        else:
            self.case_list = self.suite.caseList

        for idx, case in enumerate(self.case_list):
            case_marking_data = []

            if self.kill:
                case.setStatus(-1)
                break

            # case의 step 상태를 초기화
            case.initStepStatus()
            case.setWorkerIndex(idx)

            exeCnt += 1

            ref_data_list = case.getVariableValueList()
            all_ref_data_list.extend(ref_data_list)

        #print(all_ref_data_list)
        tot_cnt = len(list(set(all_ref_data_list)))
        self.send_start_get_variable.emit(tot_cnt)

        for ref_data_nm in all_ref_data_list:
            if ref_data_nm in finished_ref_data:
                pass
            else:
                self.send_get_variable_signal.emit(ref_data_nm)
                case.getVariableValue(ref_data_nm, 1, len(self.case_list))
                finished_ref_data.append(ref_data_nm)
                self.send_end_get_variable.emit(tot_cnt, len(finished_ref_data))

            if self.kill:
                break


        # for svc_combo_nm in svc_combo_list:
        #     self.send_get_variable_signal.emit(svc_combo_nm)
        #     case.getVariableValue(svc_combo_nm, self.worker_index + (idx * self.total_thread_cnt), False)
        #
        #     if self.kill:
        #         case.setStatus(-1)
        #         break



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
