from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class Recorder:
    def __init__(self, driver):
        self.driver = driver
        self._addUiVariable()
        self._addUiEvent()

    def _addUiVariable(self):
        # Dom 변수 선언
        self.driver.execute_script('top.parent._events = []; top.parent._gridInfo = {}')

    def _addUiEvent(self):
        # Dom Function 선언
        '''
        이벤트는 click, keyup, foucusout 에만 동작
            - 입력값이 발생하는 keyup의 경우 입력되었다는 표시만 true 변경하고
              focusout 되는 시점에 input 입력창의 값으로 type 이벤트로 추가함
            - type 이벤트 입력 시점 이전에 동일한 component의 click이나 type이 발생한 경우
              이전 이벤트는 삭제함
        '''
        self.driver.execute_script('''
        top.parent.add_event = function(e) {
        //debugger;
        
        var element_target_type = '';
        var event_type = e.type.charAt(0).toUpperCase() + e.type.slice(1);
        var element = e.target;
        
        if (e.target.tagName == 'NOBR') {
            element = e.target.parentElement;
        }
    
        var element_id = element.id;
        var element_type = element.type;
        var element_tag = element.tagName;
        var element_value = element.value;
        var element_option = {};
        
        if (['text', 'password'].indexOf(element_type) > -1 ){
            if (element.parentElement.className.includes('grid_01') == true){
                element_target_type = 'Grid';
                if (element_id.includes('__Value') == true || element_id.includes('__Desc') == true){
                    // Grid__Value, Grid__Desc
                    event_type = 'Grid Click';
                    element_id = top.parent._gridInfo['element_id']
                    element_option = top.parent._gridInfo['element_option']
                } 
            }
            else{
                element_target_type = 'Input';
                element_id = element_id.replace('___input', '');
            }
        }
        else if (['button'].indexOf(element_type) > -1 || ['A', 'IMG'].indexOf(element_tag) > -1){
            if (element.parentElement.getAttribute('role') == 'gridcell'){
                element_target_type = 'Grid';
                event_type = element_target_type + ' ' + event_type ;
                element_id = element.parentElement.id;
                element_value = element.textContent;
                element_option['row'] = element_id.split('_cell_')[1].split('_')[0];
                element_option['column'] = element_id.split('_cell_')[1].split('_')[1];
                element_id = element_id.split('_cell_')[0];
            }
            else if (element.parentElement.className.includes('w2grid_textImage_image')){
                event_type = 'Grid Click';
                element_id = top.parent._gridInfo['element_id']
                element_option = top.parent._gridInfo['element_option']
            }
            else{
                element_target_type = 'Button';
            }
        }
        else if (['DIV'].indexOf(element_tag) > -1 && element.parentElement.className.includes('tabcontrol') == true){
            element_target_type = 'Button';
            element_tag = 'Tab';
        }
        else if (['checkbox'].indexOf(element_type) > -1){
            element_target_type = 'Checkbox';
        }
        else if (element.getAttribute('role') == 'gridcell'){
            element_target_type = 'Grid';
            event_type = element_target_type + ' ' + event_type ;
            element_value = element.textContent;
            element_option['row'] = element_id.split('_cell_')[1].split('_')[0];
            element_option['column'] = element_id.split('_cell_')[1].split('_')[1];
            element_id = element_id.split('_cell_')[0];
            
            top.parent._gridInfo['element_id'] = element_id;
            top.parent._gridInfo['element_option'] = element_option;
        }
        else if (element.getAttribute('role') == 'listitem option'){
            element_target_type = 'Combo';
            event_type = element_target_type + ' ' + event_type;
            element_value = element.textContent;
            element_option['row'] = element_id.split('_itemTable_')[1].split('_')[0];
            element_id = element_id.split('_itemTable_')[0];
        }
        else if (['LABEL'].indexOf(element_tag) > -1 ){
            element_target_type = 'Checkbox';
            element_id = element.htmlFor;
        }
        
        if (e.type == 'click') {
            if (['DIV', 'group', 'HTML', 'FONT', 'TBODY'].indexOf(e.target.tagName) > -1 ){
                ;
            }
            else if (['TD', 'TR', 'TH', 'H3'].indexOf(e.target.tagName) > -1 && e.target.getAttribute('role') == null){
                ;
            }
            else if (element_target_type=='' && element_id==''){
                debugger;
            }
            else
            {
                top.parent._events.push([+new Date(), event_type, element_target_type, element_id, element_value, element_option]);
            }
        }
        else if (e.type == 'keyup') {
            debugger;
            
            if (['Input'].indexOf(element_target_type) > -1){
                remove_cnt = 0;
                top.parent._events.reverse()
                for (var i in top.parent._events) {
                    if (top.parent._events[i][3] == element_id){
                        if (['Click', 'Type'].indexOf(top.parent._events[i][1]) > -1 ) {
                            remove_cnt++;
                        }
                    }
                    else {
                        break;
                    }
                }
    
                top.parent._events.splice(0, remove_cnt)
                top.parent._events.reverse()
    
                if (e.key == 'Enter'){
                    element_option['auto_enter']='True'
                    top.parent._events.push([+new Date(), 'Type', element_target_type, element_id, element_value, element_option]);
                }
                else{
                    element_option['auto_enter']='False'
                    top.parent._events.push([+new Date(), 'Type', element_target_type, element_id, element_value, element_option]);
                }
            }
            else if (['Grid'].indexOf(element_target_type) > -1){
                remove_cnt = 0;
                
                element_id = top.parent._gridInfo['element_id']
                element_option = top.parent._gridInfo['element_option']
                element_option['auto_enter']='True'
                
                top.parent._events.reverse();
                
                for (var i in top.parent._events) {
                    if (top.parent._events[i][3] == element_id &&
                        top.parent._events[i][5]['row'] == element_option['row'] &&
                        top.parent._events[i][5]['column'] == element_option['column']){
                        if (['Grid Click', 'Grid Type', 'Click'].indexOf(top.parent._events[i][1]) > -1) {
                            remove_cnt++;
                        }
                    }
                }
                top.parent._events.splice(0, remove_cnt);
                top.parent._events.reverse();
                top.parent._events.push([+new Date(), 'Grid Type', 'Grid', element_id, element_value, element_option]);
            }
        }
        else if (e.type == 'focusout') {
            if (element_target_type == 'Grid' && element_id.includes('__Value') == true){
                //top.parent._gridInfo = {};
            }
        }
        else if (e.type == 'dblclick') {
            debugger;
            if (element_target_type == 'Grid'){
                remove_cnt = 0;
                element_id = top.parent._gridInfo['element_id']
                element_option = top.parent._gridInfo['element_option']
                
                top.parent._events.reverse();
                
                for (var i in top.parent._events) {
                    if (top.parent._events[i][3] == element_id &&
                        top.parent._events[i][5]['row'] == element_option['row'] &&
                        top.parent._events[i][5]['column'] == element_option['column']){
                        if (['Grid Click'].indexOf(top.parent._events[i][1]) > -1) {
                            remove_cnt++;
                        }
                    }
                }
                top.parent._events.splice(0, remove_cnt);
                top.parent._events.reverse();
                
                top.parent._events.push([+new Date(), 'Grid Double Click', element_target_type, element_id, element_value, element_option]);
            }
        }
    };''')


    def _addUiGetEvent(self):
        self.driver.execute_script('''
        window._getEvents = function() { return top.parent._events; };
        window._clearEvents = function() { top.parent._events = []; };
        ''')


    def _addUiEventListener(self):
        '''
        Dom Event Add Listener
            - Dom Event Listener 초기화
            - Dom event Add listener
            - window confirm/alert Add listener
        :return:
        '''
        # Dom event listener 초기화
        self.driver.execute_script('''
        window.document.removeEventListener('click', top.parent.add_event, true);
        window.document.removeEventListener('keyup', top.parent.add_event, true);
        window.document.removeEventListener('focusout', top.parent.add_event, true);
        window.document.removeEventListener('dblclick', top.parent.add_event, true);
        ''')

        # Dom event Add listener
        self.driver.execute_script('''
        (function() {
        window.document.addEventListener('click', top.parent.add_event, true);
        window.document.addEventListener('keyup', top.parent.add_event, true);
        window.document.addEventListener('focusout', top.parent.add_event, true);
        window.document.addEventListener('dblclick', top.parent.add_event, true);
        })();
        ''')

        # window confirm/alert Add listener
        self.driver.execute_script('''
        try {
            temp_confirm = ngmf.confirm.toString()
            if (temp_confirm.includes('top.parent._events.push')==true){
                ;
            }
            else{
                temp_confirm = temp_confirm.replace('c=window.confirm(a);', "c=window.confirm(a); if (c == true) {top.parent._events.push([+new Date(), 'Alert', 'Confirm', 'window_confirm', 'Accept', {}]);} else {top.parent._events.push([+new Date(), 'dismiss', 'Confirm', 'window_confirm', 'Dismiss', {}]);}")
                temp_confirm = temp_confirm.replace("function", "ngmf.confirm = function")
                eval(temp_confirm)
            }     
        } catch (e) {
            ;
        }

        try {
            temp_alert = ngmf.alert.toString()
            if (temp_alert.includes('top.parent._events.push')==true){
                ;
            }
            else{
                temp_alert = temp_alert.replace("else b()", "else { b(); } top.parent._events.push([+new Date(), 'Alert', 'Alert', 'window_alert', 'Accept', {}]);")
                temp_alert = temp_alert.replace("function", "ngmf.alert = function")
                eval(temp_alert)
            }
        } catch (e) {
            ;
        }
        ''')


    def addEventListener(self, iframe_id=''):
        '''
        모든 Frame에 event listener를 추가함
        :return: None
        '''
        if self.driver:
            if iframe_id:
                pass
            else:
                self.driver.switch_to.default_content()

            # Top Add Listerner
            self._addUiEventListener()

            # IFrame Add Listerner
            iframes = self.driver.find_elements_by_tag_name('iframe')

            for iframe in iframes:
                iframe_id = iframe.get_attribute('id')

                if iframe_id:
                    #print(iframe_id)
                    WebDriverWait(self.driver, 0).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))
                    self.addEventListener(iframe_id)
                    self.driver.switch_to.parent_frame()

            self._addUiGetEvent()

    def getEventList(self):
        '''
        JavaScript로 선언된 event List 를 가져와 List형태로 Return
        :return: [[[1594016864012, 'type', 'input', 'ipt_loginId', 'YUNWOONG', {'clientX': None, 'clientY': None}],
                   [1594016864113, 'click', 'button', 'btn_search','로그인정보 조회',{'clientX': 1019, 'clientY': 91}] ... ]
        '''
        return self.driver.execute_script('return window._getEvents();')


    def clearEventList(self):
        '''
        JavaScript로 선언된 event List 를 초기화
        :return: None
        '''
        self.driver.execute_script('return window._clearEvents();')
