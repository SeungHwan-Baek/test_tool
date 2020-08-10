import os
import datetime
import uuid

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/schedule_dialog.ui"))[0]

class ScheduleDialog(QDialog, dig_class):
    addSchedule = pyqtSignal(dict)

    appname = '스케줄'

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)

    def accept(self):
        if self._checkValue():
            q_sta_time = self.te_staTime.dateTime()
            sta_time = q_sta_time.toPyDateTime()

            schedule = {}
            schedule['schedule_id'] = str(uuid.uuid4())
            schedule['schedule_name'] = self.edt_scheduleNm.text()
            schedule['schedule_date_time'] = sta_time
            schedule['cycle_yn'] = self.cb_cycleYn.isChecked()
            schedule['expanded'] = False

            if self.cb_cycleYn.isChecked():
                schedule['cycle_value'] = self.sb_cycleValue.value()
                schedule['cycle_time_type'] = self.cb_cycleTimeType.currentText()
                schedule['max_cycle_count'] = self.sb_maxCycleCnt.value()
                schedule['remaining_count'] = self.sb_maxCycleCnt.value()
                schedule['description'] = '{cycle_value}{cycle_time_type} 마다 반복 수행 (최대 {max_cycle_count} 회)'.format(cycle_value=schedule['cycle_value'], cycle_time_type=schedule['cycle_time_type'], max_cycle_count=schedule['max_cycle_count'])
            else:
                schedule['remaining_count'] = 1
                schedule['description'] = '일회성'

            self.addSchedule.emit(schedule)
            super(ScheduleDialog, self).accept()

    def reject(self):
        super(ScheduleDialog, self).reject()

    def popUp(self):
        now = QDateTime(datetime.datetime.now())
        default_time = now.addSecs(20)
        self.te_staTime.setDateTime(default_time)
        self.exec_()

    def _checkValue(self):
        if self.edt_scheduleNm.text() == '':
            QMessageBox.information(self, "스케줄명", "스케줄명을 입력하세요")
            self.edt_scheduleNm.setFocus()
            return False
        elif self.te_staTime.dateTime() <= QDateTime(datetime.datetime.now()):
            QMessageBox.information(self, "실행시간", "현재시간 이후로 실행시간을 설정하세요")
            self.te_staTime.setFocus()
            return False

        return True
