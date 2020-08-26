import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

from utils.eventWorker import EventThread

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/sequential_step_dialog.ui"))[0]

class SequentialStepDialog(QDialog, dig_class):
    appname = 'Case 순차 진행'
    case = None
    step = None

    closed = pyqtSignal()
    stopped = pyqtSignal()
    runStep = pyqtSignal("PyQt_PyObject", int)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)
        # opacity_effect = QGraphicsOpacityEffect(self)
        # opacity_effect.setOpacity(0.3)
        # self.setGraphicsEffect(opacity_effect)
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.case = None
        self.mainWidget = None
        self.websocket_server = None

        self.cur_cnt = 0
        self.tot_cnt = 0
        self.skip_step_list = []

        self._loadUiInit()
        self._setEvent()


    def _loadUiInit(self):
        self.lbl_stepCnt.setText("")


    def _setEvent(self):
        # Button Click 이벤트
        self.btn_nextStepExec.clicked.connect(self.btnNextStepExecClicked)                  # 다음 Step 진행 버튼 클릭
        self.btn_stopCase.clicked.connect(self.btnStopCaseClicked)                          # Case 중지


    def setStepCnt(self, cur_cnt, tot_cnt):
        self.lbl_stepCnt.setText("<h4><font color='Orange'> {cur_cnt}/{tot_cnt} </font></h4>".format(cur_cnt=cur_cnt, tot_cnt=tot_cnt))


    def setProgressText(self, text):
        self.lbl_stepCnt.setText("<h4><font color='Orange'> {text} </font></h4>".format(text=text))


    def setDescriptionByStep(self, step):
        description = step.get('description')

        if description:
            pass
        else:
            description = step.get('group')
        self.edt_description.setText("<h4><font color='DodgerBlue'> {} </font></h4>".format(description))

    def setDescriptionText(self, text):
        self.edt_description.setText("<h4><font color='DodgerBlue'> {} </font></h4>".format(text))


    def accept(self):
        if self.checkValue():
            #step = Step(type=self.cb_type.currentText(), target=self.edt_target.text(), description=self.edt_description.text())
            #self.case.setStepList(step)
            self.step.setInputData(self.edt_dataInfo.toPlainText())
            self.close()

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()

    def popUp(self, case=None, mainWidget=None):
        self.case = case
        self.mainWidget = mainWidget
        self.websocket_server = self.mainWidget.websocket_server

        if self.case:
            self.cur_cnt = 0
            self.tot_cnt = self.case.getStepCount()
            self.setProgressText('= 시작 =')
            self.setDescriptionText('Case를 순차적으로 진행합니다.<br>하단의 [시작] 버튼을 클릭하시면 Step이 진행됩니다.')

        self.exec_()

    def checkValue(self):
        if self.edt_dataInfo.toPlainText() == '':
            QMessageBox.information(self, "Add Data Info", "입력된 값이 없습니다.")
            return False

        return True

    def btnNextStepExecClicked(self):
        self.btn_nextStepExec.setText('다음 Step 진행')
        self.setStepCnt(self.cur_cnt, self.tot_cnt)

        step = self.case.getStep(self.cur_cnt)

        try:
            if step.get('step_type_group') in ['Browser Command', 'Browser Command (Swing)']:
                step.removeTooltip()

            if step.get('step_type_group') in ['Browser', 'Browser Command', 'Browser Command (Swing)']:
                step.setWeb(self.mainWidget.web)

            self.setDescriptionByStep(step)

            try:
                self.websocket_server.receivedSignal.disconnect(self.websocketSeverReceived)
            except TypeError:
                pass

            self.grp_btnArea.setEnabled(False)
            self.pb_progress.setRange(0, 0)
            self.eventWorker = EventThread(step.startStep)
            self.eventWorker.finished.connect(self.stepFinished)
            self.eventWorker.start()
            self.runStep.emit(step, self.cur_cnt)
        except Exception as e:
            print('[step exception] 다음 Step으로 진행 - {}'.format(str(e)))
            self.stepFinished()

    def btnStopCaseClicked(self):
        self.stopped.emit()
        self.close()


    def stepFinished(self):
        self.cur_cnt += 1
        self.setStepCnt(self.cur_cnt, self.tot_cnt)
        self.pb_progress.setRange(0, 100)

        per = ((self.cur_cnt / self.tot_cnt) * 100)
        self.pb_progress.setValue(per)

        self.grp_btnArea.setEnabled(True)

        if self.cur_cnt < self.tot_cnt:
            step = self.case.getStep(self.cur_cnt)

            if step and step.get('step_type_group') in ['Browser Command', 'Browser Command (Swing)']:
                step.setTooltip()

            self.setDescriptionByStep(step)
            self.websocket_server.receivedSignal.connect(self.websocketSeverReceived)
        else:
            self.setProgressText('종료')
            self.btn_nextStepExec.setText('완료')
            self.setDescriptionText('Case 수행이 완료되었습니다.')
            self.btn_nextStepExec.setEnabled(False)


    def websocketSeverReceived(self, data):
        '''
        :websocket Server로부터 data를 받았을때 발생하는 이벤트
         data: (str) 'add_iframe'
        '''
        print('adfasddsafds' + data)

        parsingData = data.split(',')
        receive_type = parsingData[0]

        if receive_type == 'Event':
            receive_command = parsingData[1]
            receive_command_target = parsingData[2]

            step = self.case.getStep(self.cur_cnt)
            next_step = self.case.getStep(self.cur_cnt+1)

            command = step.get('command')
            command_target = step.get('command_target', '').replace("\\", "")

            if receive_command == command and receive_command_target == command_target:
                try:
                    if step.get('step_type_group') in ['Browser Command', 'Browser Command (Swing)']:
                        if next_step and next_step.get('command') == 'Alert':
                            self.skip_step_list.append(step)
                        else:
                            step.removeTooltip()

                            for skip_step in self.skip_step_list:
                                skip_step.removeTooltip()

                            self.skip_step_list = []
                except:
                    pass
                finally:
                    self.runStep.emit(step, self.cur_cnt)
                    self.stepFinished()
            elif receive_command == command and receive_command in ['Alert']:
                try:
                    if next_step and next_step.get('command') == 'Alert':
                        self.skip_step_list.append(step)
                    else:
                        step.removeTooltip()

                        for skip_step in self.skip_step_list:
                            skip_step.removeTooltip()

                        self.skip_step_list = []
                except:
                    pass
                finally:
                    self.runStep.emit(step, self.cur_cnt)
                    self.stepFinished()

