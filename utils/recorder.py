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
        self._setWindowEvent()
        self._setIframeAddEvent()
        self._setUiEvent()
        self._setTooltipEvnet()


    def _setWindowEvent(self):
        ### IFrame Add Event
        '''
        Native Window 이벤트
            - Window Close 시 통신
        '''
        self.driver.execute_script('''
        $(window).bind('unload', function() {
            var socket = new WebSocket('ws://localhost:8089');
            socket.onopen = function () {
                socket.send('window close');
            };
        });
                ''')

    def _setIframeAddEvent(self):
        ### IFrame Add Event
        '''
        iframe이 추가되는 경우 통신하기 위한 이벤트
            - GLV.allWindows에 iframe으로 존재하는 화면의 목록이 array로 존재하고
              array에 push(추가)가 발생하는 경우 호출됨
            - 통신은 websocket을 이용함
        '''
        self.driver.execute_script('''
                top.parent.eventify = function(arr, callback) {
                    arr.push = function(e) {
                        Array.prototype.push.call(arr, e);
                        callback(arr);
                    };
                };
                ''')

        self.driver.execute_script('''
                top.parent.eventify(GLV.allWindows, function(updatedArr) {
                  //alert(updatedArr.length);
                    var socket = new WebSocket('ws://localhost:8089');
                    socket.onopen = function () {
                        //socket.send(updatedArr);
                        socket.send('add_iframe');
                    };
                });
                ''')


    def _setUiEvent(self):
        ### UI Event
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

                var ifs = window.top.document.getElementsByTagName("iframe");
                var iframe_id = 'top'

                for(var i = 0, len = ifs.length; i < len; i++)  {
                    var f = ifs[i];
                    if(e.target.ownerDocument === ifs[i].contentDocument)   {
                        iframe_id = ifs[i].id
                    }
                }

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
                else if (['button', 'checkbox'].indexOf(element_type) > -1 || ['A', 'IMG'].indexOf(element_tag) > -1){
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
                        if (['wfm_findLayer_gen_items'].indexOf(e.target.parentElement.id) > -1 ){
                            element_option['auto_enter']='True'
                            top.parent._events.push([+new Date(), 'Type', 'Input', 'wfm_findLayer_edt_keyword', 'top', e.target.textContent, element_option]);
                            
                            var socket = new WebSocket('ws://localhost:8089');
                            socket.onopen = function () {
                                socket.send(['Event', 'Type', 'wfm_findLayer_edt_keyword']);
                            };
                        }
                        else {
                            ;
                        }
                    }
                    else if (['TD', 'TR', 'TH', 'H3'].indexOf(e.target.tagName) > -1 && e.target.getAttribute('role') == null){
                        ;
                    }
                    else if (element_target_type=='' && element_id==''){
                        debugger;
                    }
                    else
                    {
                        top.parent._events.push([+new Date(), event_type, element_target_type, element_id, iframe_id, element_value, element_option]);
                        var socket = new WebSocket('ws://localhost:8089');
                        socket.onopen = function () {
                            socket.send(['Event', event_type, element_id]);
                        };
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
                            top.parent._events.push([+new Date(), 'Type', element_target_type, element_id, iframe_id, element_value, element_option]);
                            var socket = new WebSocket('ws://localhost:8089');
                            socket.onopen = function () {
                                socket.send(['Event', 'Type', element_id]);
                            };
                        }
                        else{
                            element_option['auto_enter']='False'
                            top.parent._events.push([+new Date(), 'Type', element_target_type, element_id, iframe_id, element_value, element_option]);
                            var socket = new WebSocket('ws://localhost:8089');
                            socket.onopen = function () {
                                socket.send(['Event', 'Type', element_id]);
                            };
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
                        top.parent._events.push([+new Date(), 'Grid Type', 'Grid', element_id, iframe_id, element_value, element_option]);
                        var socket = new WebSocket('ws://localhost:8089');
                        socket.onopen = function () {
                            socket.send(['Event', 'Grid Type', element_id]);
                        };
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

                        top.parent._events.push([+new Date(), 'Grid Double Click', element_target_type, element_id, iframe_id, element_value, element_option]);
                        var socket = new WebSocket('ws://localhost:8089');
                        socket.onopen = function () {
                            socket.send(['Event', 'Grid Double Click', element_id]);
                        };
                    }
                }
            };''')


    def _setTooltipEvnet(self):
        ### Tooltip Event
        '''
        UI의 Tooltip을 제어하기 위한 이벤트
            - top.parent.setTooltip: Component에 Tooltip 삭제
            - top.parent.removeTooltip : Component에 Tooltip 제거
        '''
        self.driver.execute_script('''
        top.parent.setTooltip = function(element_id, txt, full_frame) {
            //debugger;
            var d = ngmf.object(element_id);
            var z_index = 8100;
            
            var jbSplit = full_frame.split('-');
            var frame_contents = '';
            var find_element = '';
            var find_document = '';
            
            for ( var i in jbSplit ) {
                if (jbSplit[i] == 'top') {
                    ;
                }
                else {
                    frame_contents = $("#" + jbSplit[i]).contents();
                }
            }
            
            if (frame_contents == '') {
                find_element = $("#" + element_id);
                find_document = document;
                frame_contents = $(document).contents();
            }
            else {
                find_element = frame_contents.find('#' + element_id);
                find_document = frame_contents[0];
            }
            
            
            if ("N" !== ngmf.isNull(find_document.getElementById("stepTooltip"))) {
                var f = find_document.createElement("div");
                f.setAttribute("id", "stepTooltipDiv"),
                f.setAttribute("class", "w2group tip_ov "),
                f.setAttribute("style", "position:absolute; max-width:400px; top:0; left:0; z-index:" + z_index + "; word-break: break-all;");
                var g = find_document.createElement("div");
                g.setAttribute("id", "stepTooltip"),
                g.setAttribute("class", "w2textbox"),
                g.innerHTML = txt,
                f.appendChild(g),
                find_document.body.appendChild(f)
            } else {
                var g = find_document.getElementById("stepTooltip");
                g.innerHTML = txt
            }
            var h = 0
              , i = 0
              , j = 1
              , k = find_document.body.style.transform || "";
            k = ngmf.toNumber(k.slice(k.indexOf("(") + 1, k.indexOf(")"))),
            "" != k && k > 0 && (j = k);
            var l = ""
              , m = find_element.offset().top / j
              , n = frame_contents.find('#stepTooltipDiv').outerHeight()
              , o = (find_element.offset().left / j + find_element.outerWidth() / 2,
            frame_contents.find('#stepTooltipDiv').outerWidth() / 2,
            find_element.offset().top / j + find_element.outerHeight() / 2)
              , p = frame_contents.find('#stepTooltipDiv').outerHeight() / 2
              , q = $("body").outerWidth() - find_element.offset().left / j - find_element.outerWidth()
              , r = frame_contents.find('#stepTooltipDiv').outerWidth();
            if (l = m < n ? o > p && q > r ? "right" : q < r && o > p ? "left" : "bottom" : o > p && q > r ? "right" : q < r && o > p ? "left" : "top",
            "undefined" != typeof c)
                switch (c.toLowerCase()) {
                case "left":
                    l = "left";
                    break;
                case "right":
                    l = "right";
                    break;
                case "top":
                    l = "top";
                    break;
                case "bottom":
                    l = "bottom"
                }
            if ("left" == l || "right" == l ? (h = find_element.offset().top / j - frame_contents.find('#stepTooltipDiv').outerHeight() / 2 + find_element.outerHeight() / 2,
            "left" == l ? (frame_contents.find('#stepTooltipDiv').addClass("left mr20"),
            i = find_element.offset().left / j - frame_contents.find('#stepTooltipDiv').outerWidth() - 20) : (frame_contents.find('#stepTooltipDiv').addClass("right ml20"),
            i = find_element.offset().left / j + find_element.outerWidth() - 20)) : "bottom" == l || "top" == l ? (i = find_element.offset().left / j - frame_contents.find('#stepTooltipDiv').outerWidth() / 2 + find_element.outerWidth() / 2 - 10,
            "top" == l ? (frame_contents.find('#stepTooltipDiv').addClass("top mb20"),
            h = find_element.offset().top / j - frame_contents.find('#stepTooltipDiv').outerHeight() - 20) : (frame_contents.find('#stepTooltipDiv').addClass("bottom mt20"),
            h = find_element.offset().top / j + find_element.outerHeight())) : (i = find_element.offset().left / j - frame_contents.find('#stepTooltipDiv').outerWidth() / 2 + find_element.outerWidth() / 2 - 10,
            h = find_element.offset().top / j + find_element.outerHeight()),
            element_id.indexOf("txt_footStatusMsg") > -1) {
                var d = ngmf.object("txt_footStatusMsg");
                "undefined" != typeof d && "type1" === d.page && (h -= 20)
            }
            frame_contents.find('#stepTooltipDiv').css({
                top: h,
                left: i
            })
        }
        ''')

        self.driver.execute_script('''
        top.parent.removeTooltip = function() {
            var ifs = window.top.document.getElementsByTagName("iframe");

            for(var i = 0, len = ifs.length; i < len; i++)  {
                var f = ifs[i];
                iframe_document = f.contentDocument;
                iframe_contents = $(iframe_document).contents()
            
                iframe_contents.find('#tooltip').remove(),
                iframe_contents.find("#tooltipDiv").remove();
            }
        }
        ''')

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
                temp_confirm = temp_confirm.replace('c=window.confirm(a);', "c=window.confirm(a); if (c == true) {top.parent._events.push([+new Date(), 'Alert', 'Confirm', 'window_confirm', '', 'Accept', {}]);var socket = new WebSocket('ws://localhost:8089'); socket.onopen = function () {socket.send(['Event', 'Alert', 'window_confirm']);};} else {top.parent._events.push([+new Date(), 'Alert', 'Confirm', 'window_confirm', '', 'Dismiss', {}]);var socket = new WebSocket('ws://localhost:8089'); socket.onopen = function () {socket.send(['Event', 'Alert', 'window_confirm']);};}")
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
                temp_alert = temp_alert.replace("else b()", "else { b(); } top.parent._events.push([+new Date(), 'Alert', 'Alert', 'window_alert', '', 'Accept', {}]);var socket = new WebSocket('ws://localhost:8089'); socket.onopen = function () {socket.send(['Event', 'Alert', 'window_alert']);};")
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
                    WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))
                    try:
                        self.driver.execute_script("$('.cont_wrap').css('background', 'pink')")
                    except:
                        pass
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
