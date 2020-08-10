#-*- coding: utf-8 -*-
import sys, os
import threading
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pynput import mouse
from pynput import keyboard

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
dig_class = uic.loadUiType(os.path.join(parentDir, "UI/record_dialog.ui"))[0]

class RecordDialog(QMainWindow, dig_class):
    closed = pyqtSignal()
    endRecord = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.web = None
        self.key_listener = None
        self.mouse_listener = None
        self.request_event_list = []
        self.move(1540, 790)
        self.btn_record.clicked.connect(self.btnRecordClicked)

    def popUp(self, web):
        self.web = web
        self.btn_record.setChecked(True)
        #self.key_listener = keyboard.Listener(on_release=self.on_press)
        #self.mouse_listener = mouse.Listener(on_click=self.on_click)
        #self.key_listener.start()
        #self.mouse_listener.start()
        self.show()

    def on_press(self, key):
        try:
            self.getEvent()
        except AttributeError:
            self.getEvent()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.getEvent()


    def getEvent(self):
        while True:
            try:
                WebDriverWait(self.web.driver, 0).until(EC.element_to_be_clickable((By.ID, '___processbar2_i')))
            except:
                break

        requestList = self.web.getRequest()
        self.request_event_list.extend(requestList)

        print(len(self.request_event_list))


    def btnRecordClicked(self):
        if self.btn_record.isChecked():
            print(self.pos())
        else:
            #self.key_listener.stop()
            #self.mouse_listener.stop()
            self.close()

            if self.rb_trEvent.isChecked():
                record_type = 'TR'
            elif self.rb_uiEvent.isChecked():
                record_type = 'UI'
            else:
                record_type = 'TR + UI'
            self.endRecord.emit(record_type)

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = RecordDialog()
    myWindow.show()
    app.exec_()