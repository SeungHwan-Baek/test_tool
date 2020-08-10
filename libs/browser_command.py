# -*- coding: utf-8 -*-

import time
from libs.step import Step
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, NoSuchElementException, NoAlertPresentException, NoSuchWindowException

class BrowserCommand(Step):
    sec = ''

    def __init__(self, case=None, step_type=''):
        Step.__init__(self, case=case, step_type=step_type)
        self.case = case
        self.find_element_list = []

    def __getstate__(self):
        state = self.__dict__.copy()
        try:
            del state['find_element_list']
        except KeyError:
            pass
        return state

    def startStep(self):
        try:
            self.find_element_list = []
            browser_step_id = self.get('browser_step_id')
            browser_step = self.case.getStep(step_id=browser_step_id)
            driver = browser_step.getDriver()
            command = self.get('command')
            frame = self.get('frame')
            wait = self.get('wait')
            enter = self.get('auto_enter')
            command_target = self.get('command_target', '').replace("\\", "")
            value = self.get('value')

            if value:
                ref_option = 'Eval | {}'.format(value)
                value = self.applyRefOption(value, ref_option)

            if command == 'Alert':
                try:
                    activity = self.get('activity')
                    #time.sleep(1)
                    #alert = driver.switch_to.alert
                    alert = WebDriverWait(driver, 1).until(EC.alert_is_present())

                    if activity == 'Accept':
                        alert.accept()
                    else:
                        alert.dismiss()
                except NoAlertPresentException:
                    pass
            elif command == 'Switch to Frame':

                self.findElements(driver, command_target)
                self.switchFrame(driver, frame)
            elif command == 'Switch to Default':
                driver.switch_to_default_content()
            else:
                while True:
                    try:
                        WebDriverWait(driver, 0).until(EC.element_to_be_clickable((By.ID, '___processbar2_i')))
                    except:
                        break

                driver.switch_to.default_content()

                self.findElements(driver, command_target)
                self.find_element_list = sorted(self.find_element_list, key=lambda k: k['full_frame'], reverse=True)
                self.switchFrame(driver, frame)

                role = driver.execute_script("return {}.getAttribute('role')".format(command_target))

                if command in ['Click', 'Type', 'find', 'Grid Click']:
                    target = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, command_target)))
                    target_style = driver.execute_script("return document.getElementById('{id}').getAttribute('style')".format(id=command_target))
                    driver.execute_script("document.getElementById('{target}').setAttribute('style', '{add_style}' + 'border: 2px solid red !important; text-shadow: 2px 2px 10px yellow;')".format(target=command_target, add_style=target_style))
                    #driver.implicitly_wait(1.5)
                    driver.execute_script("document.getElementById('{target}').setAttribute('style', '{add_style}')".format(target=command_target, add_style=target_style))

                # Swing Grid를 Access 하기 위한 정보 조회
                if command in ['Grid Type', 'Grid Click', 'Grid Double Click']:
                    row_index = self.get('row_index')
                    col = self.get('column')

                    col_index = driver.execute_script('''
                    var headerList = %s.getDomList("head_tds", "th", %s.getElementById(%s.id + "_head_table"));
                    var arr = Array.prototype.slice.call(headerList)
                    var find_arr = arr.find(event => event.getAttribute('value').replace(/ /gi, "").toUpperCase() === %s.replace(/ /gi, "").toUpperCase())
                    var index = -1

                    if (find_arr != null){
                        index = find_arr.getAttribute('colindex')
                    }

                    return index
                    ''' % (command_target, command_target, command_target, '''"{}"'''.format(col)))

                    if type(row_index) == int:
                        pass
                    else:
                        row_index_column = row_index["column"]
                        row_index_value = row_index["value"]
                        column_id = driver.execute_script("return {target}.getColumnID({col})".format(target=command_target, col=row_index_column))
                        row_index = driver.execute_script("return {target}.getMatchedIndex('{column_id}', '{value}', 'Y')[0]".format(target=command_target, column_id=column_id, value=row_index_value))

                    if int(col_index) > -1 and row_index:
                        grid_element_id = driver.execute_script('''
                        var headerList = %s.getDomList("body_trs", "tr", %s.getElementById(%s.id + "_body_tbody"));
                        var arr = Array.prototype.slice.call(headerList[%ld].children)
                        var find_arr = arr.find(event => event.getAttribute('colindex')=== %s)
                        var id = ''
                        
                        if (find_arr != null){
                            id = find_arr.getAttribute('id')
                        }
                        
                        return id
                        ''' % (command_target, command_target, command_target, row_index, '''"{}"'''.format(col_index)))
                    else:
                        grid_element_id = '{target}_cell_{row}_{col}'.format(target=command_target, row=row_index, col=col)

                if role == "gridcell":
                    command_target = "{}.firstElementChild".format(command_target)

                if command == 'Click':
                    driver.execute_script('{}.click()'.format(command_target))
                elif command == 'Type':
                    driver.execute_script("document.getElementById('{id}').value='{value}'".format(id=command_target, value=value))
                    if enter:
                        target.send_keys(Keys.ENTER)
                elif command == 'Execute Script':
                    script = self.get('value').replace("\\", "")
                    if script:
                        script = self.getVariableValue(script)

                    driver.execute_script(script)

                elif command == 'Grid Click':
                    try:
                        child_type = driver.execute_script("return {target}.firstElementChild.getAttribute('type')".format(target=grid_element_id))

                        if child_type == 'button':
                            driver.execute_script("{target}.firstElementChild.click()".format(target=grid_element_id))
                        else:
                            driver.execute_script('{target}.click()'.format(target=grid_element_id))
                    except:
                        driver.execute_script('{target}.click()'.format(target=grid_element_id))

                elif command == 'Grid Double Click':
                    cell_dblclick_event_info = driver.execute_script("return {target}.userEventList.find(event => event.name === 'oncelldblclick')".format(target=command_target))

                    if cell_dblclick_event_info:
                        cell_dblclick_event = cell_dblclick_event_info["param"]["handler"]
                        scope_id = driver.execute_script("return {target}.scope_id".format(target=command_target))

                        if scope_id:
                            cell_dblclick_event = scope_id + '_' + cell_dblclick_event

                        driver.execute_script('eval({event}({row}, {col}))'.format(event=cell_dblclick_event, row=row_index, col=col_index))
                    else:
                        driver.execute_script('{target}.click()'.format(target=grid_element_id))

                elif command == 'Grid Type':
                    value = self.get('value')

                    driver.execute_script('{target}.firstElementChild.click()'.format(target=grid_element_id))

                    if value:
                        set_row = grid_element_id.split('_')[2]
                        set_col = grid_element_id.split('_')[3]

                        driver.execute_script("ngmf.setGridCellData({target}, {row}, {col}, '{value}')".format(target=command_target, row=set_row, col=set_col, value=value))

                elif command == 'Combo Click':
                    value = self.get('value')
                    item_list = driver.execute_script("return {}.itemArr".format(command_target))
                    index = next(idx for idx, item in enumerate(item_list) if item['label'] == value)
                    driver.execute_script('{target}_button.click()'.format(target=command_target, index=index))
                    driver.execute_script('{target}_itemTable_{index}.click()'.format(target=command_target, index=index))
                elif command == 'find':
                    pass


            '''
            # Frame 자동 스위칭
            if frame:
                WebDriverWait(driver, self.get('wait_sec')).until(EC.frame_to_be_available_and_switch_to_it((By.ID, frame)))

            # lacator
            if self.get('locator') == 'id':
                locator = By.ID
            elif self.get('locator') == 'name':
                locator = By.NAME
            elif self.get('locator') == 'xpath':
                locator = By.XPATH
            elif self.get('locator') == 'class':
                locator = By.CLASS_NAME
            elif self.get('locator') == 'css_selector':
                locator = By.CSS_SELECTOR
            elif self.get('locator') == 'link_text':
                locator = By.LINK_TEXT

            if command == 'open':
                url = self.get('url')
                driver.get(url)
            elif command in ['Type', 'Click', 'find']:
                #time.sleep(0.5)
                # wait

                while True:
                    try:
                        WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.ID, '___processbar2_i')))
                    except:
                        break

                if wait == 'Explicit Waits':
                    target = WebDriverWait(driver, self.get('wait_sec')).until(EC.element_to_be_clickable((locator, command_target)))
                else:
                    if self.get('locator') == 'id':
                        target = driver.find_element_by_id(command_target)
                    elif self.get('locator') == 'name':
                        target = driver.find_element_by_name(command_target)
                    elif self.get('locator') == 'xpath':
                        target = driver.find_element_by_xpath(command_target)
                    elif self.get('locator') == 'class':
                        target = driver.find_element_by_class_name(command_target)
                    elif self.get('locator') == 'css_selector':
                        target = driver.find_element_by_css_selector(command_target)
                    elif self.get('locator') == 'link_text':
                        target = driver.find_element_by_link_text(command_target)

                if command == 'Type':
                    value = self.get('value')

                    if value:
                        value = self.getVariableValue(value)

                    target.clear()
                    target.send_keys(value)
                    target.send_keys(Keys.ENTER)
                elif command == 'Click':
                    try:
                        target.click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", target)
            elif command == 'find':
                WebDriverWait(driver, self.get('wait_sec')).until(EC.element_to_be_clickable((locator, command_target)))
            elif command == 'execute_script':
                script = self.get('value').replace("\\", "")
                if script:
                    script = self.getVariableValue(script)

                driver.execute_script(script)
            elif command == 'switch_to_frame':
                if wait == 'Explicit Waits':
                    WebDriverWait(driver, self.get('wait_sec')).until(EC.frame_to_be_available_and_switch_to_it((locator, command_target)))
                else:
                    driver.switch_to_frame(command_target)
            elif command == 'switch_to_default_content':
                driver.switch_to_default_content()
            elif command == 'alert_accept':
                alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
                alert.accept()
                #driver.switch_to.alert.accept()

            driver.switch_to_default_content()
            '''
            #time.sleep(1)
            self.setStatus(0, '정상적으로 처리가 완료되었습니다.')
        except UnexpectedAlertPresentException:
            self.setStatus(0, '정상적으로 처리가 완료되었습니다.')
        except NoSuchWindowException as e:
            if command == 'Click':
                self.setStatus(0, '정상적으로 처리가 완료되었습니다.')
            else:
                self.setStatus(1, str(e))
        except Exception as e:
            if self.getErrOption() == 'Skip':
                self.setStatus(999, str(e))
            else:
                self.setStatus(1, str(e))


    def getVariableValue(self, value):
        if str(value[0]) == '$' and str(value[-1]) == '$':
            variable = self.case.getVariable(value)

            if variable is None:
                pass
            else:
                value = variable.getValue()
        else:
            pass

        return value


    def findElements(self, driver, element, frame='top', full_frame='top'):
        '''
        iframe에 속한 element를 찾아 List 형태로 Return
            - 다건의 iframe에 동일한 element id를 가지고 있는 경우가 존재하는 경우에 원하는 element를 핸들링하기 위해 사용함
        :param driver: webdriver
        :param element: (str) 'btn_serach'
        :param frame: (str) 'top'
        :param full_frame: 'top-mdi01_subWindow0_iframe'
        :return: [{'frame':'mdi01_subWindow0_iframe', 'full_frame':'top-mdi01_subWindow0_iframe', 'element': (class)WebElement} ...]
        '''
        find_element = driver.find_elements_by_id(element)

        if find_element:
            #print(frame + ' 존재')
            element_info = {'frame': frame, 'full_frame': full_frame, 'element': find_element}
            self.find_element_list.append(element_info)
        else:
            pass
            #print(frame + ' 미존재')

        iframes = driver.find_elements_by_tag_name('iframe')

        for iframe in iframes:
            iframe_id = iframe.get_attribute('id')

            if iframe_id:
                WebDriverWait(driver, 0).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))
                tmp_full_frame = full_frame + '-' + iframe_id
                self.findElements(driver, element, iframe_id, tmp_full_frame)
                driver.switch_to.parent_frame()


    def switchFrame(self, driver, find_frame=''):
        '''
        다건의 element 중 원하는 frame으로 전환하기 위해 사용
            - full_frame을 parsing하여 N번 전환함
            - find_frame이 없는 경우 첫번째 element로 전환함
        :param driver: webdriver
        :param find_frame: (str) ZORDSCUS00010_iframe
        :return: None
        '''
        if find_frame:
            try :
                index = next(idx for idx, element in enumerate(self.find_element_list) if element['frame'] == find_frame)
            except:
                index = -1
        else:
            if len(self.find_element_list) > 0:
                index = 0
            else:
                index = -1

        if index > -1:
            element_info = self.find_element_list[index]
            full_frame = element_info['full_frame'].split('-')

            for frame in full_frame:
                if frame == 'top':
                    driver.switch_to.default_content()
                else:
                    WebDriverWait(driver, 0).until(EC.frame_to_be_available_and_switch_to_it((By.ID, frame)))


    def isIncludeVariable(self, variable_id):
        '''
        variable_id를 value에 포함하는 경우 Return
            - variable값을 사용하는 여부를 확인하기 위함
        :param variable_id: '$SVC_NUM$'
        :return: (bool) True
        '''
        step_value = self.get('value')

        if variable_id in str(step_value):
            return True
        else:
            return False

    def makeStep(self, browser_nm, step_info):
        event_type = step_info[1]
        element_target_type = step_info[2]
        element_id = step_info[3]
        element_value = step_info[4]
        element_option = step_info[5]

        self.setType(event_type)

        self.info['error_option'] = 'Stop'
        self.info['condition_step_id'] = ''
        self.info['description'] = ''

        browser_step = self.case.findStepByType('Open Browser', key='browser_nm', value=browser_nm)[0]
        self.info['browser_step_id'] = browser_step.getId()
        self.info['command'] = event_type

        if event_type == 'Alert':
            self.info['description'] = '알림창 확인'
            self.info['activity'] = element_value
        else:
            self.info['locator'] = 'id'
            self.info['command_target'] = element_id
            self.info['wait_sec'] = 3

            if event_type in ['Grid Click', 'Grid Type', 'Grid Double Click']:
                self.info['column'] = int(element_option['column'])
                self.info['row_index'] = int(element_option['row'])

            if event_type in ['Type', 'Grid Type', 'Combo Click']:
                self.info['value'] = element_value

            if event_type in ['Type', 'Grid Type']:
                self.info['auto_enter'] = bool(eval(element_option['auto_enter']))

