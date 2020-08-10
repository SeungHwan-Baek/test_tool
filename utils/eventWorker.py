from PyQt5.QtCore import QThread
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt

class EventThread(QThread):
    exeCnt = 0
    event = None

    def __init__(self, event):
        QThread.__init__(self)
        self.cond = None
        self.mutex = None
        self._status = True
        self.event = event

    def __del__(self):
        self.wait()

    def run(self):
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.mutex.lock()

        # self.msleep(100)
        if not self._status:
            self.cond.wait(self.mutex)

        try:
            self.event()
        except Exception as e:
            print(e)
        finally:
            self.mutex.unlock()

    def toggle_status(self):
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status

    def stop(self):
        self.terminate()