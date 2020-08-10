#20200708 멀티쓰레드 성공 9초
# https://medium.com/@keyhyuk.kim/python-%ED%81%AC%EB%A1%A4%EB%9F%AC-%EB%A9%80%ED%8B%B0%ED%94%84%EB%A1%9C%EC%84%B8%EC%8A%A4-%EB%A9%80%ED%8B%B0%EC%8A%A4%EB%A0%88%EB%93%9C%EB%A1%9C-%EC%84%B1%EB%8A%A5-%EC%A5%90%EC%96%B4%EC%A7%9C%EA%B8%B0-a7712bcbaa4
from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import requests
import time


def do_html_crawl(url: str):
    global treelog, textlog
    swgs_url = 'http://172.31.196.21:8060/websquare/Service/SVC?commonsvc=0&rtcode=0&Trx_code=ZORDSCOM06020_TR01&ScreenName=ZORDSCOM06020&fCloseAccount=0&LogLvlGbn=&G_BizCd=null&G_Biz_Start_Time=null&__smReqSeq=5&_useLayout=true'

    for line in url["input1"]:
        ln = line["flag"]

    if ln == "T":
        log = requests.get(swgs_url, json=url)
        treelog = literal_eval(log.text)

    else :
        log = requests.get(swgs_url, json=url)
        textlog = literal_eval(log.text)

def tpcall(ip, tp) :
    start_time = time.time()
    data = []

    payload = {"input1": [
        {"fcnt": "0", "flag": "L", "guid": "", "icnt": "0", "ip_addr": ip, "rowStatus": "C", "tp_id": tp}],
        "HEAD": {"Trx_Code": "ZORDSCOM06020_TR01", "Ngms_UserId": "1000852323", "Ngms_LogInId": "ENJOYHAN", "Ngms_EmpNum": "", "Ngms_OrgId": "A000700000", "Ngms_HrOrgCd": "", "Ngms_PostOrgCd": "A000700000", "Ngms_PostSaleOrgCd": "A000700000",
                 "Ngms_SupSaleOrgCd": "A010890000", "Ngms_IpAddr": "150.28.65.76", "Ngms_BrTypCd": "450", "Ngms_AuthId": "", "Ngms_ConnOrgId": "A000700000", "Ngms_ConnOrgCd": "A000700000", "Ngms_ConnSaleOrgId": "A000700000", "Ngms_ConnSaleOrgCd": "A000700000",
                 "Ngms_AuthTypPermCd": "EQ", "Ngms_PostSaleOrgId": "A000700000", "Ngms_SupSaleOrgId": "A010890000", "Term_Type": "0", "User_Term_Type": "", "St_Stop": "0", "St_Trace": "", "Stx_Dt": "", "Stx_Tm": "",
                 "Etx_Dt": "", "Etx_Tm": "", "Rt_Cd": "", "Screen_Name": "ZORDSCOM06020", "Msg_Cnt": "0", "Handle_Id": "863017520 ", "Ngms_Filler1": "", "Ngms_CoClCd": "T",
                 "Screen_Call_Trace": "Top-ZORDSCOM06020-ZORDSCOM06020_TR01", "rowStatus": "C"}}
    data.append(payload)

    payload = {"input1": [
        {"fcnt": "0", "flag": "T", "guid": "", "icnt": "0", "ip_addr": ip, "rowStatus": "C", "tp_id": tp}],
        "HEAD": {"Trx_Code": "ZORDSCOM06020_TR01", "Ngms_UserId": "1000852323", "Ngms_LogInId": "ENJOYHAN", "Ngms_EmpNum": "", "Ngms_OrgId": "A000700000", "Ngms_HrOrgCd": "", "Ngms_PostOrgCd": "A000700000", "Ngms_PostSaleOrgCd": "A000700000",
                 "Ngms_SupSaleOrgCd": "A010890000", "Ngms_IpAddr": "150.28.65.76", "Ngms_BrTypCd": "450", "Ngms_AuthId": "", "Ngms_ConnOrgId": "A000700000", "Ngms_ConnOrgCd": "A000700000", "Ngms_ConnSaleOrgId": "A000700000", "Ngms_ConnSaleOrgCd": "A000700000",
                 "Ngms_AuthTypPermCd": "EQ", "Ngms_PostSaleOrgId": "A000700000", "Ngms_SupSaleOrgId": "A010890000", "Term_Type": "0", "User_Term_Type": "", "St_Stop": "0", "St_Trace": "", "Stx_Dt": "", "Stx_Tm": "",
                 "Etx_Dt": "", "Etx_Tm": "", "Rt_Cd": "", "Screen_Name": "ZORDSCOM06020", "Msg_Cnt": "0", "Handle_Id": "863017520 ", "Ngms_Filler1": "", "Ngms_CoClCd": "T",
                 "Screen_Call_Trace": "Top-ZORDSCOM06020-ZORDSCOM06020_TR01", "rowStatus": "C"}}
    data.append(payload)

    thread_list = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for url in data:
            thread_list.append(executor.submit(do_html_crawl, url))
        for execution in concurrent.futures.as_completed(thread_list):
            execution.result()

    print("--- elapsed time %s seconds ---" % (time.time() - start_time))
    return treelog, textlog