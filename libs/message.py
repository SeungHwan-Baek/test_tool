from libs.step import Step
import requests

class Message(Step):
    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)
        self.case = case

    def startStep(self):
        step_type = self.getType()

        if step_type == 'SMS':
            ''' param, mobile_num, callback_num, text
               mobile_num : 받는사람 번호
               callback_num : 발신번호
               text : SMS내용
            '''
            param = self.get('param', {})
            mobile_num_list = self.get('mobile_num_list')
            callback_num = self.get('callback_num')
            text = self.get('text')
            ref_option = 'Eval | {}'.format(text)
            text = self.applyRefOption(text, ref_option)

            if param == {}:
                param['cmn'] = '377271'
                param['id'] = 'skt.p069295@partner.sk.com'
                param['ticket'] = '2EE647D3BB790A51A9D229372C982F0A49FD677EE12841BC5CE1EBAF3DE2774CB37ABB16F76F3E281936935DB077EBD991C114030BE829ADFF28614A840AD53D05B685E12F89FC90D9733B7A75791003A8FF37F22F98AAA627BD13C70F4328815371E6A91C35A03993E59D4EFB0A3929BB94E8F0155642D8'
            param['callback'] = callback_num
            param['sender_company_id'] = 'SK'
            param['body'] = text

            url = 'http://imwas.sk.com/Sms/Send'

            for mobile_num in mobile_num_list:
                param['mobile'] = mobile_num
                r = requests.post(url, data=param)