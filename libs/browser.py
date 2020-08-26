import time
from libs.step import Step
from utils.webBrowser import WebBrowser

class Browser(Step):
    sec = ''

    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)
        self.case = case
        self.web = None

    def __getstate__(self):
        state = self.__dict__.copy()
        try:
            del state['web']
        except KeyError:
            pass
        return state

    def getWeb(self):
        return self.web

    def setWeb(self, web=None):
        try:
            if self.web:
                pass
        except AttributeError:
            self.web = None

        if web:
            self.web = web

    def getDriver(self):
        try:
            return self.web.driver
        except AttributeError:
            self.startStep()
            return self.web.driver

    def setDriver(self, driver):
        self.web.driver = driver

    def startStep(self):
        try:
            activity = self.get('activity')

            if activity == 'Open Browser':
                try:
                    if self.web:
                        self.web.popUp()
                    else:
                        self.web = WebBrowser(sid=self.get('sid'), url=self.get('url'))
                        self.web.popUp()
                except AttributeError:
                    self.web = WebBrowser(sid=self.get('sid'), url=self.get('url'))
                    self.web.popUp()
            elif activity == 'Refresh Browser':
                browser_step_id = self.get('browser_step_id')
                browser_step = self.case.getStep(step_id=browser_step_id)
                web = browser_step.web
                web.get()

            self.setStatus(0, '정상적으로 처리가 완료되었습니다.')
        except Exception as e:
            self.setStatus(1, str(e))

    def makeStep(self, driver=None):
        self.info['step_type_group'] = 'Browser'
        self.info['group'] = 'Browser 시작'
        self.info['browser_nm'] = 'SWGS'
        self.info['sid'] = 'SWGS'
        self.info['description'] = 'URL 시작 및 탐색'
        self.info['activity'] = 'Open Browser'

        self.web = WebBrowser(sid=self.get('sid'))
        self.setDriver(driver)