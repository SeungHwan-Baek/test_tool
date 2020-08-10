import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from utils.settings import Settings
from utils.lib import tnsnameParser, readConf, addTreeRoot, addTreeChild, defaultSetting
from libs.session import Session
import codecs
from configparser import ConfigParser

dig_class = uic.loadUiType("UI/db_session.ui")[0]

class SessionDialog(QDialog, dig_class):

    appname = 'DB Session'
    session = None

    HOME = os.path.expanduser("~")
    HOME_SAVE_PATH = os.path.join(HOME, '.test_tool')
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    SESSION_PATH = os.path.join(SAVE_PATH, 'session')
    SESSION_FILE = os.path.join(SESSION_PATH, 'db_con.ini')

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.appname)

        if not os.path.exists(self.SESSION_PATH):
            os.makedirs(self.SESSION_PATH)

        # Load setting in the main thread
        self.settings = Settings(self.HOME_SAVE_PATH)

        self.loadUiInit()
        self.loadSetting()
        self.componentSetting()

        # Button 클릭 이벤트
        self.btn_dbConnection.clicked.connect(self.btnDbConnectionClicked)  # DB Connection 버튼
        self.btn_cancel.clicked.connect(self.btnCancleClicked)              # Cancel 버튼

        # Tree Item Change 이벤트
        self.tw_dbList.itemPressed.connect(self.tw_dbListItemPressed)       # DB List - Tree Item Pressed 이벤트

        self.edt_user.textChanged.connect(self.componentSetting)            # User Edit 수정
        self.edt_password.textChanged.connect(self.componentSetting)        # Password Edit 수정

        # Table 더블클릭 이벤트
        self.tw_dbList.doubleClicked.connect(self.twDbDoubleClicked)        # DB Tableview 더블클릭 이벤트

        self.cb_dBName.currentIndexChanged['QString'].connect(self._cbDbNameCurrentIndexChanged)

    def loadUiInit(self):
        try:
            tns_path = os.environ['TNS_ADMIN']
        except:
            tns_path = ''
            print("TNS_ADMIN 시스템변수 추가필요")

        self.tnsList = tnsnameParser(tns_path)
        if self.tnsList == []:
            pass
        else:
            # os.environ['TNS_ADMIN']
            self.cb_dBName.clear()
            self.cb_dBName.addItems(self.tnsList)

        self.cb_dBName.insertItem(0, 'SWGS.JSD')

    def loadSetting(self):
        self.settings.load()

        db_save = self.settings.get("SETTING_DBSAVE", False)
        db = self.settings.get("SETTING_DB", False)
        user = self.settings.get("SETTING_USER", False)
        password = self.settings.get("SETTING_PASSWORD", False)

        if db_save:
            defaultSetting(self.chk_dbSave, db_save)

        if db:
            defaultSetting(self.cb_dBName, db)

        if user:
            defaultSetting(self.edt_user, user)

        if password:
            defaultSetting(self.edt_password, password)


    def componentSetting(self):
        if self.edt_user.text() == '' or self.edt_password.text() == '':
            self.btn_dbConnection.setEnabled(False)     # DB [Connection] 비활성화
        else:
            self.btn_dbConnection.setEnabled(True)      # DB [Connection] 활성화

        self.makeSessionList(self.tw_dbList, self.cb_dBName.currentText(), self.edt_user.text())

    def btnDbConnectionClicked(self):
        settings = self.settings
        settings.load()

        self.session = Session(self.cb_dBName.currentText(), self.edt_user.text(), self.edt_password.text())

        try:
            self.session.connection()
            self.existsDBSection(self.cb_dBName.currentText(), self.edt_user.text(), self.edt_password.text(), self.chk_dbSave.isChecked(), True)
            QMessageBox.information(self, "DB Connect","[{}] DB Connection Successful".format(self.session.sid))
            self.accept()
        except Exception as e:
            self.session = None
            self.existsDBSection(self.cb_dBName.currentText(), self.edt_user.text(), self.edt_password.text(), self.chk_dbSave.isChecked(), False)
            QMessageBox.information(self, "DB Connection Fail", str(e))

        settings["SETTING_DB"] = self.cb_dBName.currentText()
        settings["SETTING_USER"] = self.edt_user.text()
        settings["SETTING_PASSWORD"] = self.edt_password.text()
        settings["SETTING_DBSAVE"] = self.chk_dbSave.isChecked()

        settings.save()

    def twDbDoubleClicked(self):
        parentNode = None

        for item in self.tw_dbList.selectedItems():
            parentNode = item.parent()

        if parentNode is None:
            pass
        else:
            self.btn_dbConnection.click()


    def _cbDbNameCurrentIndexChanged(self, item):
        if item in ['demo.db', 'SWGS.JSD']:
            self.edt_user.setText('Test')
            self.edt_password.setText('Test')
            self.edt_user.setEnabled(False)
            self.edt_password.setEnabled(False)
        else:
            self.edt_user.setText('')
            self.edt_password.setText('')
            self.edt_user.setEnabled(True)
            self.edt_password.setEnabled(True)


    def btnCancleClicked(self):
        self.session = None
        self.reject()

    def popUp(self):
        self.exec_()

    def makeSessionList(self, tree_widget, db_sid, db_user):
        self.connectionList = []
        tree_widget.clear()

        con_group = []

        # Selected Tables Info
        try:
            if os.path.isfile(self.SESSION_FILE):
                pass
            else:
                f = open(self.SESSION_FILE, 'w')
                f.close

            connectionList = readConf(self.SESSION_FILE)
        except:
            self.statusbar.showMessage('db_con.ini 확인이 필요합니다.')
            return False

        for idx, con in enumerate(connectionList):
            con_group.append(con['group'])

            connectionInfo = {'sect' : con['sect'],
                              'group': con['group'],
                              'user_id': con['user_id'],
                              'password': con['password'],
                              'saved': con['saved']}

            self.connectionList.append(connectionInfo)

        con_group = list(set(con_group))

        # Source DB TreeWidget
        for idx, groupInfo in enumerate(con_group):
            parent_node = addTreeRoot(treeWidget=tree_widget, idx=0, text=groupInfo, check=False)

            child_tables = (item for item in connectionList if item['group'] == groupInfo)

            for idy, table in enumerate(child_tables):
                child_node = addTreeChild(parent=parent_node, text=table['user_id'], check=False)

                if table['sect'] == (db_sid + '_' + db_user):
                    tree_widget.setCurrentItem(child_node)

        tree_widget.sortByColumn(0, Qt.AscendingOrder)
        tree_widget.expandToDepth(0)

    def existsDBSection(self, db_sid, db_user, db_password, db_saved, db_connected):
        config = ConfigParser()

        try:
            if os.path.isfile(self.SESSION_FILE):
                pass
            else:
                f = open(self.SESSION_FILE, 'w')
                f.close
        except:
            self.logger.error("existsDBSection Fail")

        config.read_file(codecs.open(self.SESSION_FILE, "r", "utf8"))
        section_name = db_sid + '_' + db_user

        if db_connected:
            if config.has_section(section_name):
                pass
            else:
                config.add_section(section_name)

            config[section_name]['s_group'] = db_sid
            config[section_name]['s_user_id'] = db_user

            if db_saved:
                config[section_name]['s_password'] = db_password
            else:
                config[section_name]['s_password'] = ''

            config[section_name]['b_saved'] = str(db_saved)

            with open(self.SESSION_FILE, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
        else:
            if config.has_section(section_name):
                config[section_name]['s_group'] = db_sid
                config[section_name]['s_user_id'] = db_user

                if db_saved:
                    config[section_name]['s_password'] = db_password
                else:
                    config[section_name]['s_password'] = ''

                config[section_name]['b_saved'] = str(db_saved)

                with open(self.SESSION_FILE, 'w', encoding='utf-8') as configfile:
                    config.write(configfile)

    def tw_dbListItemPressed(self, item):
        parentNode = item.parent()
        selectedNode = item

        if parentNode is not None:
            find_con = parentNode.text(0) + '_' + selectedNode.text(0)
            selectedRow = next(idx for idx, item in enumerate(self.connectionList) if item['sect'] == find_con)

            db = self.connectionList[selectedRow]['group']
            user_id = self.connectionList[selectedRow]['user_id']
            password = self.connectionList[selectedRow]['password']
            saved = self.connectionList[selectedRow]['saved']

            self.edt_user.setText(user_id)
            self.edt_password.setText(password)
            self.chk_dbSave.setChecked(saved)

            combo_idx = self.cb_dBName.findText(db)
            self.cb_dBName.setCurrentIndex(combo_idx)
