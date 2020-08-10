import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from libs.version import __version__
import qdarkstyle

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

class ReplayCaseSplash(QSplashScreen):

    def __init__(self):
        splash_pix = QPixmap(os.path.join(parentDir, 'UI/fetch_data.jpg'))
        self.splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.splash.setEnabled(False)

        self.lbl_desc = QTextEdit(self.splash)
        self.lbl_desc.setTextColor(Qt.white)
        self.lbl_desc.setStyleSheet("QTextEdit {background-color: rgb(48,48,48)}")
        self.lbl_desc.setText("<h2><font color='White'> Auto Test Tool {version} </font></h2> \n".format(version=__version__))
        self.lbl_desc.append("Build #{}, built on July 16, 2020".format(__version__))
        self.lbl_desc.append("Powered by open-source-software")
        self.lbl_desc.setGeometry(100, (splash_pix.height() / 2) - 50, splash_pix.width() - 200, 120)

        self.lbl_caseProcessDesc = QLabel(self.splash)
        self.lbl_caseProcessDesc.setText("<h4><font color='Orange'> Play Case... </font></h4>")
        self.lbl_caseProcessDesc.setStyleSheet("QLabel {background-color: rgb(48,48,48)}")
        self.lbl_caseProcessDesc.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_caseProcessDesc.setGeometry(20, splash_pix.height() - 130, splash_pix.width() - 150, 30)

        self.lbl_caseCnt = QLabel(self.splash)
        self.lbl_caseCnt.setText("<h4><font color='Orange'> [1/100] </font></h4>")
        self.lbl_caseCnt.setStyleSheet("QLabel {background-color: rgb(48,48,48)}")
        self.lbl_caseCnt.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_caseCnt.setGeometry(620, splash_pix.height() - 130, splash_pix.width() - 150, 30)

        self.caseProgressBar = QProgressBar(self.splash)
        self.caseProgressBar.setGeometry(20, splash_pix.height() - 100, splash_pix.width() - 50, 20)
        self.caseProgressBar.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        self.lbl_stepProcess = QLabel(self.splash)
        self.lbl_stepProcess.setText("<h4><font color='DarkSeaGreen'> Step Description... </font></h4>")
        self.lbl_stepProcess.setStyleSheet("QLabel {background-color: rgb(48,48,48)}")
        self.lbl_stepProcess.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_stepProcess.setGeometry(20, splash_pix.height() - 70, splash_pix.width() - 100, 30)

        self.stepProgressBar = QProgressBar(self.splash)
        self.stepProgressBar.setGeometry(20, splash_pix.height() - 40, splash_pix.width() - 50, 20)
        self.stepProgressBar.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def setMainText(self, text):
        self.lbl_desc.append(text)

    def setCaseProgressText(self, text):
        self.lbl_caseProcessDesc.setText("<h4><font color='Orange'> {text} </font></h4>".format(text=text))
        self.lbl_caseProcessDesc.setStyleSheet("QLabel {background-color: rgb(48,48,48)}")
        self.lbl_caseProcessDesc.setFont(QFont('Arial Rounded MT Bold'))

    def setCaseCnt(self, complete_cnt, total):
        self.lbl_caseCnt.setText("<h4><font color='Orange'> [{complete_cnt}/{total}] </font></h4>".format(complete_cnt=complete_cnt, total=total))
        self.lbl_caseCnt.setStyleSheet("QLabel {background-color: rgb(48,48,48)}")
        self.lbl_caseCnt.setFont(QFont('Arial Rounded MT Bold'))

    def setCaseProgressPer(self, per, text=''):
        self.caseProgressBar.setValue(per)

        if text:
            self.setCaseProgressText(text)

    def startCaseProgress(self, text=''):
        self.caseProgressBar.setRange(0, 0)

        if text:
            self.setCaseProgressText(text)

    def endCaseProgress(self):
        self.caseProgressBar.setRange(0, 100)

    def setStepProgressText(self, text):
        self.lbl_stepProcess.setText("<h4><font color='DarkSeaGreen'> {text} </font></h4>".format(text=text))
        self.lbl_stepProcess.setStyleSheet("QLabel {background-color: rgb(48,48,48)}")
        self.lbl_stepProcess.setFont(QFont('Arial Rounded MT Bold'))

    def setStepProgressPer(self, per, text=''):
        self.stepProgressBar.setValue(per)

        if text:
            self.setStepProgressText(text)

    def startStepProgress(self, text=''):
        self.stepProgressBar.setRange(0, 0)

        if text:
            self.setStepProgressText(text)

    def endStepProgress(self):
        self.stepProgressBar.setRange(0, 100)

    def popup(self):
        self.splash.show()

    def close(self):
        self.splash.hide()


class ProgressSplash(QSplashScreen):

    def __init__(self):
        splash_pix = QPixmap(os.path.join(parentDir, 'UI/splash_image.jpg'))
        self.splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.splash.setEnabled(False)

        # self.lbl_desc = QTextEdit(self.splash)
        # self.lbl_desc.setTextColor(Qt.white)
        # self.lbl_desc.setStyleSheet("QTextEdit {background-color: rgb(48,48,48)}")
        # self.lbl_desc.setText("<h2><font color='White'> Auto Test Tool {version} </font></h2> \n".format(version=__version__))
        # self.lbl_desc.append("Build #{}, built on July 16, 2020".format(__version__))
        # self.lbl_desc.append("Powered by open-source-software")
        # self.lbl_desc.setGeometry(100, (splash_pix.height() / 2) - 50, splash_pix.width() - 200, 120)

        self.lbl_version = QLabel(self.splash)
        self.lbl_version.setText("<font color='LightSkyBlue'> version {} </font>".format(__version__))
        self.lbl_version.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_version.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_version.setGeometry(5, 5, 90, 20)

        self.lbl_caseProcessDesc = QLabel(self.splash)
        self.lbl_caseProcessDesc.setText("<h4><font color='Orange'> Play Case... </font></h4>")
        self.lbl_caseProcessDesc.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_caseProcessDesc.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_caseProcessDesc.setGeometry(20, splash_pix.height() - 80, splash_pix.width() - 150, 30)

        self.lbl_cnt = QLabel(self.splash)
        # self.lbl_cnt.setText("<h4><font color='Orange'> [1/100] </font></h4>")
        self.lbl_cnt.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_cnt.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_cnt.setGeometry(splash_pix.width() - 80, splash_pix.height() - 80, splash_pix.width() - 150, 30)

        self.caseProgressBar = QProgressBar(self.splash)
        self.caseProgressBar.setGeometry(20, splash_pix.height() - 50, splash_pix.width() - 50, 20)
        self.caseProgressBar.setStyleSheet("QProgressBar::chunk { background-color: rgb(255,165,0); }")
        #self.caseProgressBar.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        #
        self.lbl_stepProcess = QLabel(self.splash)
        #self.lbl_stepProcess.setText("<h4><font color='DarkSeaGreen'> Step Description... </font></h4>")
        self.lbl_stepProcess.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_stepProcess.setFont(QFont('Arial Rounded MT Bold'))
        self.lbl_stepProcess.setGeometry(20, splash_pix.height() - 30, splash_pix.width() - 100, 30)
        #
        # self.stepProgressBar = QProgressBar(self.splash)
        # self.stepProgressBar.setGeometry(20, splash_pix.height() - 40, splash_pix.width() - 50, 20)
        # self.stepProgressBar.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def setMainText(self, text):
        self.lbl_desc.append(text)

    def setCaseProgressText(self, text):
        self.lbl_caseProcessDesc.setText("<h4><font color='Orange'> {text} </font></h4>".format(text=text))
        self.lbl_caseProcessDesc.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_caseProcessDesc.setFont(QFont('Arial Rounded MT Bold'))

    def setCnt(self, complete_cnt, total):
        self.lbl_cnt.setText("<h4><font color='Orange'> [{complete_cnt}/{total}] </font></h4>".format(complete_cnt=complete_cnt, total=total))
        self.lbl_cnt.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_cnt.setFont(QFont('Arial Rounded MT Bold'))

    def setCaseProgressPer(self, per, text=''):
        self.caseProgressBar.setValue(per)

        if text:
            self.setCaseProgressText(text)

    def startCaseProgress(self, text=''):
        self.caseProgressBar.setRange(0, 0)

        if text:
            self.setCaseProgressText(text)

    def endCaseProgress(self):
        self.caseProgressBar.setRange(0, 100)

    def setStepProgressText(self, text):
        self.lbl_stepProcess.setText("<h4><font color='DarkSeaGreen'> {text} </font></h4>".format(text=text))
        self.lbl_stepProcess.setStyleSheet("QLabel {background-color: rgb(0,125,197)}")
        self.lbl_stepProcess.setFont(QFont('Arial Rounded MT Bold'))

    def setStepProgressPer(self, per, text=''):
        self.caseProgressBar.setValue(per)

        if text:
            self.setStepProgressText(text)

    def startCaseProgress(self):
        self.caseProgressBar.setRange(0, 0)

    def endCaseProgress(self):
        self.caseProgressBar.setRange(0, 100)

    def startStepProgress(self, text=''):
        self.caseProgressBar.setRange(0, 0)

        if text:
            self.setStepProgressText(text)

    def endStepProgress(self):
        self.caseProgressBar.setRange(0, 100)

    def popup(self):
        self.splash.show()

    def close(self):
        self.splash.hide()