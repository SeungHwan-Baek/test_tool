from PyQt5.QtCore import QThread
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import pyqtSignal
import requests

class LogThread(QThread):
    exeCnt = 0
    logTreeFinished = pyqtSignal(dict, int, str)
    logViewFinished = pyqtSignal(dict, int)

    def __init__(self, ip, tp):
        QThread.__init__(self)
        self.cond = None
        self.mutex = None
        self._status = True
        self.ip = ip
        self.tp = tp
        self.guid = ''
        self.icnt = 0
        self.tot_cnt = 0
        self.max_line = 8000

    def __del__(self):
        self.wait()

    def run(self):
        log_tree = {}
        tot_line_cnt = 0
        guid = ''

        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.mutex.lock()

        # self.msleep(100)
        if not self._status:
            self.cond.wait(self.mutex)

        try:
            swgs_url = 'http://172.31.196.21:8060/websquare/Service/SVC?commonsvc=0&rtcode=0&Trx_code=ZORDSCOM06020_TR01&ScreenName=ZORDSCOM06020&fCloseAccount=0&LogLvlGbn=&G_BizCd=null&G_Biz_Start_Time=null&__smReqSeq=5&_useLayout=true'
            payload = {"input1": [{"fcnt": "0", "flag": "T", "guid": self.guid, "icnt": self.icnt, "ip_addr": self.ip, "rowStatus": "C", "tp_id": self.tp, "prod_skip": "N"}],
                         "HEAD":  {"Trx_Code": "ZORDSCOM06020_TR01",
                                   "Ngms_UserId": "1000852323",
                                   "Ngms_LogInId": "ENJOYHAN",
                                   "Ngms_EmpNum": "",
                                   "Ngms_OrgId": "A000700000",
                                   "Ngms_HrOrgCd": "",
                                   "Ngms_PostOrgCd": "A000700000",
                                   "Ngms_PostSaleOrgCd": "A000700000",
                                   "Ngms_SupSaleOrgCd": "A010890000",
                                   "Ngms_IpAddr": "150.28.65.76",
                                   "Ngms_BrTypCd": "450",
                                   "Ngms_AuthId": "",
                                   "Ngms_ConnOrgId": "A000700000",
                                   "Ngms_ConnOrgCd": "A000700000",
                                   "Ngms_ConnSaleOrgId": "A000700000",
                                   "Ngms_ConnSaleOrgCd": "A000700000",
                                   "Ngms_AuthTypPermCd": "EQ",
                                   "Ngms_PostSaleOrgId": "A000700000",
                                   "Ngms_SupSaleOrgId": "A010890000",
                                   "Term_Type": "0",
                                   "User_Term_Type": "",
                                   "St_Stop": "0",
                                   "St_Trace": "",
                                   "Stx_Dt": "",
                                   "Stx_Tm": "",
                                   "Etx_Dt": "",
                                   "Etx_Tm": "",
                                   "Rt_Cd": "",
                                   "Screen_Name": "ZORDSCOM06020",
                                   "Msg_Cnt": "0",
                                   "Handle_Id": "863017520 ",
                                   "Ngms_Filler1": "",
                                   "Ngms_CoClCd": "T",
                                   "Screen_Call_Trace": "Top-ZORDSCOM06020-ZORDSCOM06020_TR01",
                                   "rowStatus": "C"}}
            '''
            1. icnt 값이 0 인 경우 log tree 에 보여줄 값을 조회
            2. log view에 보여줄 상세 값을 조회
                2-1) tot_cnt 가 0 보다 크고 icnt 가 0인 경우 (최초 조회)
                2-2) rem_cnt 가 0 보다 큰 경우 (Append 하기 조회)
            '''
            if self.icnt == 0:
                log_tree_result = requests.get(swgs_url, json=payload)
                log_tree = log_tree_result.json()

                if log_tree:
                    if log_tree['output2']:
                        self.tot_line_cnt =int(log_tree['output2'][0]['total_cnt'])
                        self.guid = log_tree['output2'][0]['guid']

                        cnt = divmod(int(self.tot_line_cnt), int(self.max_line))
                        self.tot_cnt = cnt[0] + 1

                self.logTreeFinished.emit(log_tree, self.tot_cnt, self.guid)

            rem_cnt = self.tot_cnt - self.icnt

            if self.tot_cnt > 0 and self.icnt == 0:
                payload['input1'][0]['flag'] = 'L'
                payload['input1'][0]['guid'] = guid
                payload['input1'][0]['icnt'] = self.icnt

                log_view_result = requests.get(swgs_url, json=payload)
                log_view = log_view_result.json()

                self.icnt += 1

                self.logViewFinished.emit(log_view, self.icnt)
                print('{}번 조회완료'.format(self.icnt))
            elif rem_cnt > 0:
                log_view = {}
                for ix in range(0, rem_cnt):
                    payload['input1'][0]['flag'] = 'L'
                    payload['input1'][0]['guid'] = guid
                    payload['input1'][0]['icnt'] = self.icnt

                    log_view_result = requests.get(swgs_url, json=payload)

                    if ix == 0:
                        log_view = log_view_result.json()
                    else:
                        log_view_temp = log_view_result.json()
                        log_view['output1'].append(log_view_temp['output1'])

                    self.icnt += 1
                    print('{}번 조회완료'.format(self.icnt))

                self.logViewFinished.emit(log_view, self.icnt)
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


class LogMultiThread(QThread):
    logViewFinished = pyqtSignal(list)
    logPagingFinished = pyqtSignal()

    def __init__(self, ip, tp, guid='', icnt_list=[]):
        QThread.__init__(self)
        self.cond = None
        self.mutex = None
        self._status = True
        self.ip = ip
        self.tp = tp
        self.guid = guid
        self.icnt_list = icnt_list

    def __del__(self):
        self.wait()

    def run(self):
        self.cond = QWaitCondition()
        #self.mutex = QMutex()
        #self.mutex.lock()

        #if not self._status:
        #    self.cond.wait(self.mutex)

        try:
            log_view = []

            for ix, icnt in enumerate(self.icnt_list):
                swgs_url = 'http://172.31.196.21:8060/websquare/Service/SVC?commonsvc=0&rtcode=0&Trx_code=ZORDSCOM06020_TR01&ScreenName=ZORDSCOM06020&fCloseAccount=0&LogLvlGbn=&G_BizCd=null&G_Biz_Start_Time=null&__smReqSeq=5&_useLayout=true'
                payload = {"input1": [{"fcnt": "0", "flag": "L", "guid": self.guid, "icnt": icnt, "ip_addr": self.ip, "rowStatus": "C", "tp_id": self.tp, "prod_skip": "N"}],
                             "HEAD":  {"Trx_Code": "ZORDSCOM06020_TR01",
                                       "Ngms_UserId": "1000852323",
                                       "Ngms_LogInId": "ENJOYHAN",
                                       "Ngms_EmpNum": "",
                                       "Ngms_OrgId": "A000700000",
                                       "Ngms_HrOrgCd": "",
                                       "Ngms_PostOrgCd": "A000700000",
                                       "Ngms_PostSaleOrgCd": "A000700000",
                                       "Ngms_SupSaleOrgCd": "A010890000",
                                       "Ngms_IpAddr": "150.28.65.76",
                                       "Ngms_BrTypCd": "450",
                                       "Ngms_AuthId": "",
                                       "Ngms_ConnOrgId": "A000700000",
                                       "Ngms_ConnOrgCd": "A000700000",
                                       "Ngms_ConnSaleOrgId": "A000700000",
                                       "Ngms_ConnSaleOrgCd": "A000700000",
                                       "Ngms_AuthTypPermCd": "EQ",
                                       "Ngms_PostSaleOrgId": "A000700000",
                                       "Ngms_SupSaleOrgId": "A010890000",
                                       "Term_Type": "0",
                                       "User_Term_Type": "",
                                       "St_Stop": "0",
                                       "St_Trace": "",
                                       "Stx_Dt": "",
                                       "Stx_Tm": "",
                                       "Etx_Dt": "",
                                       "Etx_Tm": "",
                                       "Rt_Cd": "",
                                       "Screen_Name": "ZORDSCOM06020",
                                       "Msg_Cnt": "0",
                                       "Handle_Id": "863017520 ",
                                       "Ngms_Filler1": "",
                                       "Ngms_CoClCd": "T",
                                       "Screen_Call_Trace": "Top-ZORDSCOM06020-ZORDSCOM06020_TR01",
                                       "rowStatus": "C"}}

                log_view_result = requests.get(swgs_url, json=payload)
                log_view_temp = log_view_result.json()
                log_view.extend(log_view_temp['output1'])

                self.logPagingFinished.emit()
                print('{}번 조회완료'.format(icnt))

        except Exception as e:
            print('log woker error')
            print(e)
        finally:
            self.logViewFinished.emit(log_view)
            pass

    def toggle_status(self):
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status

    def stop(self):
        self.terminate()