import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from utils.lib import newIcon

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
widget_class = uic.loadUiType(os.path.join(parentDir, "UI/step_dtl_widget.ui"))[0]

class StepDtlWidget(QWidget, widget_class):
    def __init__(self, parent=None):
        super(StepDtlWidget, self).__init__(parent)
        self.setupUi(self)

        self.step = None

        self.setStyleSheet("background-color: rgba(47,79,79,30%)")

        # setStyleSheet
        self.lbl_target.setStyleSheet("color: rgb(255, 255, 255)")
        self.lbl_description.setStyleSheet("color: rgb(255, 0, 0)")

        # 모든 Label을 투명하게 변경
        label_list = self.findChildren(QLabel)

        for item in label_list:
            item.setStyleSheet("background-color: rgba(0,0,0,0%)")

        # 모든 Checkbox를 투명하게 변경
        check_list = self.findChildren(QCheckBox)

        for item in check_list:
            item.setStyleSheet("background-color: rgba(0,0,0,0%)")

        self.chk_log.toggled.connect(self._setLogEnabled)

    def setStepDtl(self, step):
        self.step = step
        self.setType(step.getType())
        self.setTarget(step.get('target'))
        #self.setDesc(step.get('description'))
        self.setErrOption(step.get('error_option'))
        self.setRefChkRst()
        self.setVarChkRst()
        self.setStatus()

        # Step Class Seq변경
        self.step.setSeq(self.getSeq())

    def setSeq(self, text):
        self.lbl_seq.setText(text)

    def setType(self, text):
        self.chk_log.setEnabled(False)

        if text == 'XHR':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'xhr.png'))
            self.chk_log.setEnabled(True)
        elif text == 'Sleep':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'sleep.png'))
        elif text == 'Open Browser':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'browser.png'))
        elif text == 'Refresh Browser':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'refresh.png'))
        elif text == 'Type':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'type.png'))
        elif text in ['Click', 'Alert']:
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'component.png'))
        elif text == 'Execute Script':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'execute_script.png'))
        elif text in ['Switch to Frame', 'Switch to Default']:
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'switch_frame.png'))
        elif text in ['Grid Click', 'Grid Double Click', 'Grid Type']:
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'grid.png'))
        elif text == 'Combo Click':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'combo.png'))
        elif text == 'IF':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'if.png'))
        elif text == 'Validation':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'validation.png'))
        elif text == 'SMS':
            self.lbl_type.setPixmap(QPixmap(':/step/' + 'send.png'))

    def setTarget(self, text):
        step_type = self.step.getType()
        if step_type == 'XHR':
            #self.lbl_target.setText("<h4><font color='MediumSlateBlue'> {target} </font> ({desc}) </h4>".format(target=text, desc=self.step.get('description')))
            self.lbl_target.setText("<span style=' font-size:9pt; font-weight:600; color:LightSkyBlue;'>{target}  </span><span style=' font-size:9pt;'>({desc})</span>".format(target=text, desc=self.step.get('target_nm')))
        elif step_type == 'Sleep':
            self.lbl_target.setText("<h4><font color='Thistle'> {} </font></h4>".format(text))
        elif step_type == 'Open Browser':
            browser_nm = self.step.get('browser_nm')
            self.lbl_target.setText("<h4><font color='PaleGreen'> {} </font></h4>".format(browser_nm))
        elif step_type == 'Refresh Browser':
            browser_step_id = self.step.get('browser_step_id')
            browser_step = self.step.case.getStep(step_id=browser_step_id)
            browser = browser_step.get('browser_nm')
            self.lbl_target.setText("<h4><font color='OliveDrab'> [</font> {browser}<font color='OliveDrab'> ] {step_type} </font></h4>".format(browser=browser, step_type=step_type))
        elif step_type == 'Click':
            self.lbl_target.setText("<h4><font color='OliveDrab'> {command} </font> ({locator}={target}) </h4>".format(command=step_type, locator=self.step.get('locator'), target=self.step.get('command_target')))
        elif step_type in ['Type', 'Grid Type', 'Combo Click']:
            self.lbl_target.setText("<h4><font color='OliveDrab'> {command} [</font> {value}<font color='OliveDrab'> ]</font> </font> ({locator}={target}) </h4>".format(command=step_type, value=self.step.get('value'), locator=self.step.get('locator'), target=self.step.get('command_target')))
        elif step_type == 'Alert':
            self.lbl_target.setText("<h4><font color='OliveDrab'> {command} [</font> {activity}<font color='OliveDrab'> ]</font> </font> </h4>".format(command=step_type, activity=self.step.get('activity')))
        elif step_type == 'Execute Script':
            self.lbl_target.setText("<h4><font color='OliveDrab'> {command} [</font> {value}<font color='OliveDrab'> ]</font> </font> </h4>".format(command=step_type, value=self.step.get('value')))
        elif step_type == 'Switch to Frame':
            self.lbl_target.setText("<h4><font color='OliveDrab'> {command} [</font> {target}<font color='OliveDrab'> ]</font> </font> </h4>".format(command=step_type, target=self.step.get('command_target')))
        elif step_type == 'Switch to Default':
            self.lbl_target.setText("<h4><font color='OliveDrab'> {} </font></h4>".format(step_type))
        elif step_type in ['Grid Click', 'Grid Double Click']:
            self.lbl_target.setText("<h4><font color='OliveDrab'> {command} </font> ({locator}={target}) </h4>".format(command=step_type, locator=self.step.get('locator'), target=self.step.get('command_target')))
        elif step_type == 'IF':
            self.lbl_target.setText("<h4><font color='LightSkyBlue'> {} </font></h4>".format(text))
        elif step_type == 'Validation':
            sql_name = self.step.get('sql_name')
            self.lbl_target.setText("<h4><font color='SandyBrown'> {sql_name} </font> ({sid}) </h4>".format(sql_name=sql_name, sid=self.step.get('sid')))
        elif step_type == 'SMS':
            mobile_num_list = self.step.get('mobile_num_list')
            self.lbl_target.setText("<h4><font color='Chocolate'> [{mobile_num_cnt}] 건 SMS 전송 </font></h4>".format(mobile_num_cnt=len(mobile_num_list)))
        else:
            self.lbl_target.setText(text)

    def setDesc(self, text):
        self.lbl_description.setText(text)

    def setStatus(self):
        msg = self.step.msg
        code = self.step.status

        if code == 999:
            self.lbl_status.setPixmap(QPixmap(':/step/skip.png'))
            self.lbl_status.setToolTip("<h4><font color='Orange'> {} </font></h4>".format(msg))
            self.setStyleSheet("background-color: rgba(47,79,79,30%)")
        elif code > 0:
            self.lbl_status.setPixmap(QPixmap(':/step/error.png'))
            self.lbl_status.setToolTip("<h4><font color='Orange'> {} </font></h4>".format(msg))
            self.setStyleSheet("background-color: rgba(178,34,34,10%)")
        elif code < 0:
            self.lbl_status.clear()
            self.setStyleSheet("background-color: rgba(0,0,0,0%)")
        else:
            self.lbl_status.setPixmap(QPixmap(':/step/correct.png'))
            self.lbl_status.setToolTip("<h4><font color='Sky Blue'> {} </font></h4>".format(msg))
            self.setStyleSheet("background-color: rgba(47,79,79,30%)")

        self.setLog()

    def setErrOption(self, text):
        self.lbl_errOption.setText(text)

    def setRefChkRst(self):
        ref_check = self.step.getIsRef()

        if ref_check == 'Link':
            self.lbl_link.setPixmap(QPixmap(':/ref/link.png'))
        elif ref_check == 'Unlink':
            self.lbl_link.setPixmap(QPixmap(':/ref/unlink.png'))
        else:
            self.lbl_link.clear()

    def setVarChkRst(self):
        var_check = self.step.getIsVar()

        if var_check == 'Link':
            self.lbl_var.setPixmap(QPixmap(':/variable/var.png'))
        elif var_check == 'Unlink':
            self.lbl_var.setPixmap(QPixmap(':/variable/unvar.png'))
        else:
            self.lbl_var.clear()

    def setLog(self):
        if self.step.get('log_enable'):
            self.chk_log.setChecked(True)
        else:
            self.chk_log.setChecked(False)

    def setAddInfo(self, add_info_type):
        if add_info_type == '설명':
            add_info = self.step.get('description')
        elif add_info_type == '수행시간':
            add_info = self.step.get('exec_time')
        elif add_info_type == '타입':
            add_info = self.step.getType()
        else:
            add_info = ''

        self.setDesc(add_info)

    def getStep(self):
        return self.step

    def getTaget(self):
        return self.step.get('target')

    def getDesc(self):
        return self.lbl_description.text()

    def getSeq(self):
        return int(self.lbl_seq.text())

    def getGroup(self):
        return self.step.getGroup()

    def _setLogEnabled(self, enabled):
        self.step['log_enable'] = enabled