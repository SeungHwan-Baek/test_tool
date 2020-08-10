# 다음페이지 넘기면 쓰레드로 한꺼번에 페이지 정보 가져온다.
from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import requests
import time

def do_html_crawl(url: str):
    global totlog
    totlog = {}
    swgs_url = 'http://172.31.196.21:8060/websquare/Service/SVC?commonsvc=0&rtcode=0&Trx_code=ZORDSCOM06020_TR01&ScreenName=ZORDSCOM06020&fCloseAccount=0&LogLvlGbn=&G_BizCd=null&G_Biz_Start_Time=null&__smReqSeq=5&_useLayout=true'
    log = requests.get(swgs_url, json=url)
    a = literal_eval(log.text)

    for line in url["input1"]:
        ln = int(line["icnt"])

    for tree in a["output1"]:
        totlog[ln] = tree
        ln = ln + 1

def tpcall(tot_cnt, cur_cnt,ip,tp) :
    start_time = time.time()
    global a
    sta = int(cur_cnt)
    cnt = divmod(int(tot_cnt), int(cur_cnt))

    if cnt[1] == 0:
        line = cnt[0]
    else:
        line = cnt[0] + 1

    para = list(range(1, line))

    data = []
    for i in para:
        tot_cnt = str(tot_cnt)
        cur_cnt = str(sta * int(i))

        payload = {"input1": [
            {"fcnt": tot_cnt, "flag": "L", "guid": "", "icnt": cur_cnt, "ip_addr": ip, "rowStatus": "C", "tp_id": tp}],
            "HEAD": {"Trx_Code": "ZORDSCOM06020_TR01", "Ngms_UserId": "1000852323", "Ngms_LogInId": "ENJOYHAN", "Ngms_EmpNum": "", "Ngms_OrgId": "A000700000", "Ngms_HrOrgCd": "", "Ngms_PostOrgCd": "A000700000",
                     "Ngms_PostSaleOrgCd": "A000700000", "Ngms_SupSaleOrgCd": "A010890000", "Ngms_IpAddr": "150.28.65.76", "Ngms_BrTypCd": "450", "Ngms_AuthId": "",
                     "Ngms_ConnOrgId": "A000700000", "Ngms_ConnOrgCd": "A000700000", "Ngms_ConnSaleOrgId": "A000700000", "Ngms_ConnSaleOrgCd": "A000700000",
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
    return totlog