import os
import re
import codecs
import pickle
import json
from configparser import ConfigParser
from operator import itemgetter
import sqlparse
from sqlparse.tokens import Keyword, DML
from collections import OrderedDict
from itertools import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from configparser import ConfigParser

config = ConfigParser()
config.read_file(codecs.open("config.ini", "r", "utf8"))

parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

def makeList(split_str):
    resultList = []

    try:
        resultList = (split_str.split(','))
        resultList = list(map(str.strip, resultList))
    except KeyError:
        resultList = []

    if '' in resultList:
        resultList = resultList.remove('')

    if resultList is None:
        resultList = []

    return resultList

def chunkList(case_list, thread_cnt):
    resultList = [case_list[i::thread_cnt] for i in range(thread_cnt)]
    # 빈리스트는 삭제
    resultList = [x for x in resultList if x]
    return resultList

def newIcon(icon):
    return QIcon(':/simulation/' + icon)

def remove_dupe_dicts(l):
  list_of_strings = [json.dumps(d) for d in l ]
  list_of_strings = set(list_of_strings)
  return [json.loads(s)for s in list_of_strings]

def split_seq(input_list):
    '''

    :param input_list: [1, 2, 4, 5, 6, 8, 9, 10]
    :return: [[1, 2], [4, 5, 6], [8, 9, 10]]
    '''
    return [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(input_list), lambda x: x[0] - x[1])]

def make_marking_seq(marking_data, case_id):
    # Seq채번
    tmp_seq = []

    for testDataName in marking_data:
        if testDataName['case_id'] == case_id:
            tmp_seq.append(int(testDataName['test_data_name'].split('#')[1]))

    if tmp_seq:
        seq = int(max(tmp_seq)) + 1
    else:
        seq = 1

    test_data_name = 'DATA #{}'.format(seq)

    return test_data_name


def change_key(d, new, old):
    new_dict = {}
    for key in d:
        new_dict[new if old == key else key] = d[key]

    return new_dict

def parsingRef(ref):
    target = ''
    dataListId = ''
    column = ''
    row = 0
    stepId = ''

    if ref:
        try:
            parsingStr = ref.split('.')
            target = parsingStr[0]
            dataListId = parsingStr[1]
            column = parsingStr[2]
            row = int(parsingStr[3])
        except ValueError:
            print('parsingRef Error : {}'.format(ref))
            row = 0

        try:
            stepId = parsingStr[4]
        except IndexError:
            stepId = ''

    return target, dataListId, column, row, stepId


def addTreeRoot(treeWidget, idx, text, check=False):
    textList = []

    if type(text) == list:
        textList = text
    else:
        textList.append(text)

    for ix, text in enumerate(textList):
        item = QTreeWidgetItem(treeWidget)
        item.setText(idx, text)

        if check:
            item.setFlags(item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

    return item


def addTreeChild(parent, text, check=True, checked=False):
    textList = []

    if type(text) == list:
        textList = text
    else:
        textList.append(text)

    item = QTreeWidgetItem(parent)
    item.setFlags(item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

    for idx, text in enumerate(textList):
        item.setText(idx, text)

    if check:
        if checked:
            ''' Default Unchecked '''
            #item.setCheckState(0, Qt.Checked)
            item.setCheckState(0, Qt.Unchecked)
        else:
            item.setCheckState(0, Qt.Unchecked)
           # item.setForeground(0, Qt.darkGray)

    #parent.addChild(item)
    return item

def horizontalLayout(widget_list):
    cell_widget = QWidget()
    layout = QHBoxLayout(cell_widget)

    for widget in widget_list:
        layout.addWidget(widget)

    layout.setContentsMargins(5, 0, 5, 0)
    cell_widget.setLayout(layout)

    return cell_widget

def findDictIndexByValue(data_list, key, value):
    index = -1

    if type(data_list) == list:
        '''
        [{key1:value1}, {key1:value2}]
        '''
        if data_list:
            try:
                index = next(idx for idx, row in enumerate(data_list) if row[key] == value)
            except StopIteration:
                index = -1
    else:
        print('Type Error : {}'.format(type(data_list)))

    return index

def findDictListByValue(data_list, key, value):
    resultList = []

    if type(data_list) == list:
        '''
        [{key1:value1}, {key1:value2}]
        '''
        if data_list:
            resultList = list(filter(lambda data: data[key] == value, data_list))
    else:
        print('Type Error : {}'.format(type(data_list)))

    return resultList


def makeDataInfo(data):
    mainColumnList = []

    for dataList in list((data.keys())):
        mainColumns = {}
        subColumns = {}
        tmpColumnList = []
        if dataList in ['HEAD', 'params']:
            pass
        else:
            if data[dataList]:
                for column in data[dataList][0]:
                    columnInfo = {}
                    columnInfo['id'] = column
                    columnInfo['type'] = ''
                    columnInfo['length'] = ''

                    tmpColumnList.append(columnInfo)
                subColumns['column'] = tmpColumnList

                mainColumns['id'] = dataList
                mainColumns['columns'] = subColumns
            else:
                subColumns['column'] = {}

                mainColumns['id'] = dataList
                mainColumns['columns'] = subColumns

            mainColumnList.append(mainColumns)

    data['dataInfo'] = mainColumnList
    return data

def findTrName(trxCode):
    tx_name = ''
    TR_INFO_SAVE_PATH = config.get('section_tr', 'TR_INFO_FILE_PATH')

    # Transaction Info Load
    if os.path.exists(TR_INFO_SAVE_PATH):
        with open(TR_INFO_SAVE_PATH, 'rb') as f:
            tr_info = pickle.load(f)

            try:
                index = findDictIndexByValue(tr_info, 'TX_CODE', trxCode)
                tx_name = tr_info[index]['TX_NAME']
            except StopIteration:
                pass
    else:
        print('TR_INFO_FILE NOT EXIST')

    return tx_name

def makeVariableId(variable_id):

    if variable_id:
        variable_id = variable_id.strip()
        variable_id = variable_id.replace('$', '')
        variable_id = '${}$'.format(variable_id)
        variable_id = variable_id.upper()

    return variable_id


def tnsnameParser(file_path, file_name='tnsnames.ora'):
    easy_connects = []

    try:
        f = codecs.open(os.path.join(file_path, file_name), 'r')
        full_tnsnames = f.read()

        # Removing commented text
        new_tnsnames = re.sub('^\s*#.*\n?', '', full_tnsnames, flags=re.MULTILINE)

        tnsnames = re.split(r"\n\n", new_tnsnames)
        # Regex matches
        tns_name = '^(.+?)\s?\=\s+\(DESCRIPTION.*'
        tns_host = '.*?HOST\s?=\s?(.+?)\)'
        tns_port = '.*?PORT\s?=\s?(\d+?)\)'
        tns_sname = '.*?SERVICE_NAME\s?=\s?(.+?)\)'
        tns_sid = '.*?SID\s?=\s?(.+?)\)'
        '''
        for y in tnsnames: 
            y = '%s))' % y
            l = [find_match(x, y) for x in [tns_name, tns_host, tns_port, tns_sname, tns_sid]]
            d = { 'name': l[0], 'host': l[1], 'port': l[2], 'service_name': l[3], 'sid': l[4] }
    
            easy_connects.append(d)
        '''
        easy_connects = sorted(set([x for x in re.findall(r'(.+?)\s?\=\s+\(DESCRIPTION.*', new_tnsnames)]))
    except FileNotFoundError:
        print('tnsnames.ora 파일 미존재')
    return easy_connects

def readConf(path):
    resultList = []

    config_list = ConfigParser()
    config_list.read_file(codecs.open(path, "r", "utf8"))

    for sect in config_list.sections():
        option = {}
        option['sect'] = sect

        for name, value in config_list.items(sect):
            type_tag = name[:2]
            if type_tag == "s_":
                option[name[2:]] = value
            elif type_tag == "i_":
                if value == '':
                    value = 99999999999999
                option[name[2:]] = int(value)
            elif type_tag == "f_":
                option[name[2:]] = float(value)
            elif type_tag == "b_":
                option[name[2:]] = True if (value == 'True') else False

        resultList.append(option)

    return resultList

def defaultSetting(component, val):
    if type(component) == QLineEdit:
        component.setText(val)
    elif type(component) == QCheckBox:
        component.setChecked(True)
    elif type(component) == QComboBox:
        combo_idx = component.findText(val)
        component.setCurrentIndex(combo_idx)
    elif type(component) == QSpinBox:
        component.setValue(val)

def sqlCommnetFilter(sql):
    new_sql = re.sub('^\s*--.*\n?', '', sql, flags=re.MULTILINE)
    new_sql = sqlparse.format(new_sql, strip_comments=True).strip()
    return new_sql

def sqlFindBindVar(sql):
    filter_sql = sqlCommnetFilter(sql)
    bind_list = list([x.replace(":", "") for x in re.findall(r'\:\w+', filter_sql)])
    bind_list = list(OrderedDict.fromkeys(bind_list).keys())
    return bind_list

def sqlFindDml(sql):
    dml_type = ''

    parsed = sqlparse.parse(sql)
    for token in parsed[0].tokens:
        if DML == token.ttype:
            dml_type = str(token).upper()

    return dml_type

def refOption(case, value, ref_option):
    ref_option_split = [x.strip() for x in ref_option.split('|')]
    ref_option_type = ref_option_split[0]
    ref_option_info = ref_option_split[1]

    if ref_option_type == 'Substr':
        index_list = [x.strip() for x in ref_option_info.split(',')]
        start_index = int(index_list[0])
        end_index = int(index_list[1])
        value = value[start_index:end_index]
    elif ref_option_type == 'Sum':
        try:
            value = int(value)
            option_variables = [x.strip() for x in ref_option_info.split(',')]

            for variable_id in option_variables:
                variable = case.getVariable(variable_id)

                if variable is None:
                    pass
                else:
                    try:
                        add_value = int(variable.getValue())
                        value += add_value
                    except ValueError:
                        pass
        except ValueError:
            value = variable.getValue()
    elif ref_option_type == 'Eval':
        evalOption = ref_option_info
        try:
            find_variables = re.findall(r"(?:[^\$]+[\$$])", evalOption, flags=re.MULTILINE | re.DOTALL)
            if find_variables:
                for tmp_variable_id in find_variables:
                    variable_id = "${}$".format(tmp_variable_id.replace('$', ''))
                    variable = case.getVariable(variable_id)

                    if variable:
                        value = variable.getValue()
                        evalOption = evalOption.replace(variable_id, "'{}'".format(value))

            # print(evalOption)
            value = eval(evalOption)
        except NameError:
            value = evalOption
        except SyntaxError:
            value = evalOption
        except TypeError:
            value = ''

    return value