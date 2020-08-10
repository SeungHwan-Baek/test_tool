import os, sys
import json
from win32com.client import Dispatch
from utils.config import Config

from utils.lib import makeDataInfo
from utils.recorder import Recorder
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import JavascriptException, WebDriverException, NoAlertPresentException
from win10toast import ToastNotifier

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(parentDir)


class WebBrowser(object):
    dic_url = {'SWGS': 'http://172.31.196.21:8060/websquare/websquare.html?w2xPath=/SWING/lib/xml/ZLIBSMAN90010.xml&coClCd=T&svrLocation=SWGS'}
    browser_log = []
    requestList = []
    eventList = []
    browser_log_hst = []

    def __init__(self, sid, url=''):
        self.sid = sid
        self.url = url
        self.driver = None
        self.recorder = None
        self.requestList = []
        self.eventList = []
        self.browser_log = []
        self.browser_log_hst = []

        self.recording = False
        self.web_iframe_list = []

        self.config = Config()
        self.paths = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
        self.paths.extend(self.config.getlist("section_browser", "BROWSER_PATH"))

        self.browser_version = self.config.get('section_browser', 'BROWSER_VER')

        if self.sid in self.dic_url.keys():
            print(self.dic_url[self.sid])
        elif self.sid == 'URL':
            print(self.url)
            self.dic_url[self.sid] = self.url
        else:
            print('미존재 SID')

    def getVersionViaCom(self):
        version_info = []
        paths = self.paths

        try:
            parser = Dispatch("Scripting.FileSystemObject")
        except:
            if self.browser_version:
                result_verion= self.browser_version
            else:
                result_verion = ''
            return result_verion

        for file_name in paths:
            try:
                version = parser.GetFileVersion(file_name)
                version_info.append(version)
            except:
                pass
        try:
            result_verion = version_info[0].split('.')[0]
        except:
            result_verion = ''
        return result_verion

    def processBrowserLogEntry(self, entry):
        response = json.loads(entry['message'])['message']
        return response

    def findEventLog(self, type, evets):
        requestList = []

        xhr_events = [event for event in evets if 'type' in event['params'].keys() and event['params']['type'] == type]
        xhr_events = [event for event in xhr_events if event['params']['request']['method'] == 'POST' and 'postData' in event['params']['request'].keys()]

        #print('==== XHR List ====')
        for idx, xhr in enumerate(xhr_events):
            post_data = xhr['params']['request']['postData']

            try:
                trx_code = json.loads(post_data)['HEAD']['Trx_Code']
            except json.JSONDecodeError as e:
                print(e)
                print(post_data)

            request_id = xhr['params']['requestId']
            #print('{index} - {trxCode} - {requestId}'.format(index=idx, trxCode=trx_code, requestId=request_id))

            inputData = {}
            outputData = {}

            # request결과가 없는 경우가 있음 (ZNGMSATH10060_TR03) 결과가 없으면 제외

            try:
                inputData = json.loads(self.driver.execute_cdp_cmd('Network.getRequestPostData', {'requestId': str(request_id)})['postData'])
                outputData = json.loads(self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': str(request_id)})['body'])

                if 'dataInfo' not in list(outputData.keys()):
                    outputData = makeDataInfo(outputData)

                requestDtl = {'trx_code': trx_code,
                              'request_id': request_id,
                              'input_data': inputData,
                              'output_data': outputData}

                requestList.append(requestDtl)
            except:
                pass

        return requestList

    def getInputDataset(self, events, idx):
        return json.loads(events[idx]['params']['request']['postData'])

    def popUp(self):
        version = self.getVersionViaCom()

        if version == '81':
            chromedriver = 'chromedriver_81'
        elif version == '79':
            chromedriver = 'chromedriver_79'
        elif version == '80':
            chromedriver = 'chromedriver_80'
        else:
            print('Chrome Version Check : {} - 79, 80, 81 Version만 지원가능'.format(version))
            return False

        print(version)

        self.web_iframe_list = []

        chrome_options = Options()
        #chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("window-size=1920x1080")  # 가져올 크기를 결정

        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}

        # 드라이버 객체 생성
        self.driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options, desired_capabilities=caps)

        #self.driver.implicitly_wait(3)  # 드라이버 초기화를 위해 3초 대기
        self.get()

    def get(self):
        self.driver.get(self.dic_url[self.sid])

        if self.sid == 'SWGS':
            try:
                WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.ID, 'mdi01_subWindow0_iframe')))
            finally:
                print('Page is ready!')
                self.driver.execute_script('''top.document.title = "(FOR AUTO TEST TOOL)"''')
                # Recorder 선언
                self.recorder = Recorder(self.driver)
                self.recorder.addEventListener()
                #threading.Timer(3, self.getBrowserEvents).start()

    def getRequest(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException:
            log = self.driver.get_log('performance')
            self.browser_log.extend(log)
            self.browser_log_hst.extend(log)
            events = [self.processBrowserLogEntry(entry) for entry in self.browser_log]

            # response_events = [event for event in events if 'Network.response' in event['method']]
            request_events = [event for event in events if 'Network.requestWillBeSent' in event['method']]
            self.requestList = self.findEventLog('XHR', request_events)

        return self.requestList

    def getRequestHst(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException:
            log = self.driver.get_log('performance')
            self.browser_log.extend(log)
            self.browser_log_hst.extend(log)
            events = [self.processBrowserLogEntry(entry) for entry in self.browser_log_hst]

            # response_events = [event for event in events if 'Network.response' in event['method']]
            request_events = [event for event in events if 'Network.requestWillBeSent' in event['method']]
            self.requestHst = self.findEventLog('XHR', request_events)

        return self.requestHst

    def clear(self):
        self.browser_log_hst.extend(self.driver.get_log('performance'))
        self.browser_log = []
        self.requestList = []

        print('Request Clear Successful')

    def clearUiEventList(self):
        self.recorder.clearEventList()

    def recordUiEvent(self):
        if not self.recording:
            self.recorder.clearEventList()
            self.recorder.addEventListener()

            threading.Timer(1, self.checkIframe).start()

        self.recording = not self.recording


    def checkIframe(self):
        while True:
            if self.recording:
                iframeIdList = []

                try:
                    try:
                        self.driver.switch_to_alert()
                    except NoAlertPresentException:
                        iframeIdList = self.driver.execute_script('''
                                        var iframeIdList = []
                                        iframeList = Array.prototype.slice.call(top.document.getElementsByTagName('iframe'))
                                        for (var i in iframeList ) {
                                            if (iframeList[i]['id'] != '') {
                                                iframeIdList.push(iframeList[i]['id'])
                                            }
                                        }
                                        return iframeIdList
                                        ''')
                except:
                    pass

                if iframeIdList:
                    self.web_iframe_list.sort()
                    iframeIdList.sort()

                    if self.web_iframe_list == iframeIdList:
                        #print(self.web_iframe_list)
                        pass
                    else:
                        #print(iframeIdList)
                        #print('Add EventLister 재수행')
                        self.recorder.addEventListener()
                        self.web_iframe_list = iframeIdList
            else:
                break

    def getBrowserEvents(self):
        events = []

        try:
            events = self.recorder.getEventList()
            #threading.Timer(3, self.getBrowserEvents).start()
        except JavascriptException:
            self.recorder.addEventListener()
            events = self.recorder.getEventList()
            #threading.Timer(3, self.getBrowserEvents).start()
        except WebDriverException:
            print('Browser 종료')
        finally:
            #print(events)
            self.recorder.addEventListener()
            return events

        # if events:
        #     print(events)
        #     self.eventList.extend(events)
            #self.recorder.clearEventList()

            # for event in events:
            #     # One-time initialization
            #     toaster = ToastNotifier()
            #
            #     # Show notification whenever needed
            #     toaster.show_toast(title="Command Record",
            #                        msg="Command:{command}\nTarget:{target}\nValue:{value}".format(command=event[1], target=event[3], value=event[5]),
            #                        threaded=True,
            #                        icon_path='auto_test_main.ico',
            #                        duration=1)
                # notification.notify(
                #     title='Command Record',
                #     ticker='A',
                #     message="Command:{command}\nTarget:{target}\nValue:{value}".format(command=event[1], target=event[3], value=event[5]),
                #     app_name="Auto Test Tool 0.0.4",
                #     app_icon='auto_test_main.ico',
                #     timeout=5,  # seconds
                # )

    def getDriver(self):
        return self.driver

    def getEventList(self):
        return self.eventList

    def getSessionId(self):
        return self.driver.session_id

    def setSessionId(self, session_id):
        self.driver.session_id = session_id

    def getStatus(self):
        try:
            self.driver.window_handles
            return True
        except:
            return False

    def setFocus(self):
        self.driver.switch_to_window(self.driver.current_window_handle)




