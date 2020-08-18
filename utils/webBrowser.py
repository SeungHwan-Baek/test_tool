import os, sys
import json
import shutil
import urllib.request

import re
import requests
from bs4 import BeautifulSoup
import zipfile

from win32com.client import Dispatch
from utils.config import Config
from utils.settings import Settings

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

    HOME = os.path.expanduser("~")
    SAVE_PATH = os.path.join(HOME, 'Test_Tool')
    HOME_SAVE_PATH = os.path.join(HOME, '.test_tool')

    def __init__(self, sid, url=''):
        self.sid = sid
        self.url = url
        self.driver = None
        self.recorder = None
        self.requestList = []
        self.eventList = []
        self.browser_log = []
        self.browser_log_hst = []

        self.chromedriver_version = ''

        self.recording = False
        self.web_iframe_list = []

        # Load setting in the main thread
        self.settings = Settings(self.HOME_SAVE_PATH)
        self.settings.load()
        self.settings.save()

        self._loadSetting()

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


    def _loadSetting(self):
        '''
        설정값으로 재설정
        :return: None
        '''
        self.chromedriver_version = self.settings.get("CHROMEDRIVER_VERSION", "")


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
        chromedriver_path = os.path.join(self.SAVE_PATH, 'chromedriver.exe')

        if not os.path.exists(chromedriver_path):
            print('chromedriver 파일 미존재 - 생성....')
            self.downloadChromedriver(version, chromedriver_path)
        elif version == self.chromedriver_version:
            print('동일한 Chrome / chromedriver 버전')
        else:
            print('Chrome / chromedriver 버전이 다른 경우')
            self.downloadChromedriver(version, chromedriver_path)

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
        self.driver = webdriver.Chrome(chromedriver_path, chrome_options=chrome_options, desired_capabilities=caps)

        #self.driver.implicitly_wait(3)  # 드라이버 초기화를 위해 3초 대기
        self.get()

    def get(self):
        self.driver.get(self.dic_url[self.sid])

        if self.sid == 'SWGS':
            try:
                self.driver.switch_to_alert()
                alert = WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                alert.accept()
            except NoAlertPresentException:
                pass
            finally:
                while True:
                    try:
                        WebDriverWait(self.driver, 0).until(EC.element_to_be_clickable((By.ID, 'bodyBlock')))
                    except:
                        break

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
        if self.driver:
            return self.driver.session_id
        else:
            return False

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


    def saveChromedriverVersion(self, version):
        '''
        chromedriver version 정보를 저장
        '''
        self.settings.load()
        settings = self.settings
        settings["CHROMEDRIVER_VERSION"] = version
        settings.save()


    def chromedriverWebOn(self):
        '''
        chromedriver site 접속 가능여부 체크
        '''
        url = "https://chromedriver.chromium.org/downloads"
        try:
            res = urllib.request.urlopen(url)

            if res.status == 200:
                return True
            else:
                return False
        except:
            return False


    def downloadChromedriver(self, version, chromedriver_path):
        '''
        chromedriver가 미존재하거나 버전이 다른 경우 발생하는 이벤트
            - 온라인 연결이 가능한 경우는 다운로드
            - 온라인 연결이 불가능한 경우 임시 파일 중 가능한 버전으로 대체
        :param version: (str) '81'
        :param chromedriver_path: (str)
        '''
        if self.chromedriverWebOn():
            print("Chromedriver Downloading...")
            download_url  = self.findDriverVersion(version)
            download_path = os.path.join(self.SAVE_PATH, "chromedriver.zip")
            urllib.request.urlretrieve(download_url, download_path)
            print("Download Complete!")

            try:
                with zipfile.ZipFile(download_path) as zf:
                    zf.extractall(path=self.SAVE_PATH)
                os.remove(download_path)
            except Exception as e:
                print(e)

        else:
            print('Online 연결 불가능 - 오프라인 파일 생성')

            try:
                if version == '81':
                    shutil.copy('chromedriver_tmp/chromedriver_81.exe', chromedriver_path)
                    self.saveChromedriverVersion(version)
                elif version == '79':
                    shutil.copy('chromedriver_tmp/chromedriver_79.exe', chromedriver_path)
                    self.saveChromedriverVersion(version)
                elif version == '80':
                    shutil.copy('chromedriver_tmp/chromedriver_80.exe', chromedriver_path)
                    self.saveChromedriverVersion(version)
                else:
                    print('Chrome Version Check : {} - 오프라인은 79, 80, 81 Version만 지원가능'.format(version))
                    return False
            except:
                pass
        pass


    def findDriverVersion(self, find_version):
        '''
        chromedriver를 다운로드 할 url를 찾아 string으로 Return
        :param find_version: (str) '81'
        :return: (str) https://chromedriver.storage.googleapis.com/81.0.4044.138/chromedriver_win32.zip
        '''
        download_url = ''

        base_url = "https://chromedriver.chromium.org/downloads"

        base_req = requests.get(base_url)
        base_soup = BeautifulSoup(base_req.content, "html.parser")

        atags = base_soup.select("a")

        for a in atags:
            m = re.compile("ChromeDriver (.*)")
            p = m.search(a.text)

            try:
                version = p.group(1)
                try:

                    m = re.compile("(\d*)\..*")
                    p = m.search(version)

                    if int(find_version) == int(p.group(1)):
                        download_url = "/".join(
                            [
                                "https://chromedriver.storage.googleapis.com",
                                version,
                                "chromedriver_win32.zip",
                            ]
                        )
                        break

                except:
                    pass
            except AttributeError:
                pass

        return download_url