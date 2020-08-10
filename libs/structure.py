import datetime
from utils.lib import findDictIndexByValue, remove_dupe_dicts, parsingRef

def inputDataInfo(data):
    ''' [list] inputDataInfo ((list or dict) data)

            inputData의 정보를 [{dict}] 형태로 Return
            Reference Data를 찾기 위해 최초 설계함

            [{'id': 'eqp_mdl_cd', 'column_nm': '단말기모델코드', 'ref_method': 'Fixed Value', 'ref': 'ZORDSCOM20010_TR01.input1.new_eqp_mdl_cd.6fd74e22-3292-4afc-a18a-ef08c1a98bb1', 'desc': '...', 'exist:' True, 'marking': False, 'isInputValue': True},
             {'id': 'usim_mdl_cd', 'column_nm': 'USIM모델코드', 'ref_method': 'Excel', 'ref': 'test_data.usim.usim_mdl_cd.69ca0f3b-a51c-4bf4-b2b0-1064a93af7d9', 'desc': '...', 'exist:' True, 'marking': True, 'isInputValue': False}
             ...
            ]

        '''
    inputDataList = []
    inputDataListInfo = []

    for dataId in list(data.keys()):
        dataInfo = {}
        dataColumnInfo = []

        if data[dataId]:
            if type(data[dataId]) == list:
                dataIdList = list(data[dataId][0].keys())
            elif type(data[dataId]) == dict:
                dataIdList = list(data[dataId].keys())

            for columId in dataIdList:
                columnInfo = {}
                columnInfo['id'] = columId
                columnInfo['column_nm'] = ''
                columnInfo['ref_method'] = 'Fixed Value'
                columnInfo['ref'] = ''
                columnInfo['desc'] = ''
                columnInfo['exist'] = True
                columnInfo['marking'] = False
                columnInfo['isInputValue'] = False
                dataColumnInfo.append(columnInfo)

        dataInfo['id'] = dataId
        #dataInfo['ref_type'] = 'column'  # Default (Column)
        dataInfo['columns'] = dataColumnInfo

        inputDataList.append(dataId)
        inputDataList = sorted(inputDataList)

        inputDataListInfo.append(dataInfo)

    return inputDataList, inputDataListInfo

def outputDataInfo(data):
    ''' [list] outputDataInfo ((list or dict) data)

            outputData의 정보를 [{dict}] 형태로 Return
            output Data의 형태를 확인하기 위해 최초 설꼐함

            [{'id': 'acnt_num', 'type': 'number', 'length': 10, 'desc': '...'},
             {'id': 'appr_dt', 'type': 'text', 'length': 8, 'desc': '...'}
             ...
            ]

        '''
    outputDataList = []
    outputDataListInfo = []

    try:
        if 'dataInfo' in list(data.keys()):
            for output in data['dataInfo']:
                dataInfo = {}
                dataColumnInfo = []

                for column in output['columns']['column']:
                    columnInfo = {}
                    columnInfo['id'] = column['id']
                    columnInfo['type'] = column['type']
                    columnInfo['length'] = column['length']
                    columnInfo['desc'] = ''

                    dataColumnInfo.append(columnInfo)

                dataInfo['id'] = output['id']
                dataInfo['columns'] = dataColumnInfo

                outputDataList.append(output['id'])
                outputDataList = sorted(outputDataList)

                outputDataListInfo.append(dataInfo)
        # dataInfo가 없는 경우
        else:
            for dataList in list(data.keys()):
                dataInfo = {}
                dataColumnInfo = []

                if dataList in ['HEAD', 'params']:
                    pass
                else:
                    for column in data[dataList][0]:
                        columnInfo = {}
                        columnInfo['id'] = column
                        columnInfo['type'] = ''
                        columnInfo['length'] = ''
                        columnInfo['desc'] = ''

                        dataColumnInfo.append(columnInfo)

                    dataInfo['id'] = dataList
                    dataInfo['columns'] = dataColumnInfo

                    outputDataList.append(dataList)
                    outputDataList = sorted(outputDataList)

                    outputDataListInfo.append(dataInfo)
                    print(data[dataList])
    except KeyError:
        print('SKIP: OutputData datainfo 미존재')

    return outputDataList, outputDataListInfo


def findRefColumn(step, data, find_value, find_option='value'):
    ''' [list] find_column ((Class) Step, (list or dict) data, (str) find_value)

        find_column 기준으로 Step의 Column을 찾아 Return [list]

        [{'target': 'ZORDSS01S0010_TR01', 'description': '신규가입 처리서비스목록 조회', 'step_id': 'xxxx-xxxx-xxxx-xxxx', 'dataList_id': 'output1', 'column': 'svc_num', 'row': 0},
         {'target': 'ZORDSS01S0010_TR05', 'description': 'B2C가입 I/F 송신', 'step_id': 'xxxx-xxxx-xxxx-xxxx', 'dataList_id': 'input1', 'column': 'svc_num', 'row': 0}
         ...
        ]

    '''
    findRefData = []

    for dataList in data:
        key_list = []
        if find_option == 'value':
            if type(data[dataList]) == list:
                for idx, row in enumerate(data[dataList]):
                    tmp_key_list = [{'column': key, 'row': str(idx)} for key, value in row.items() if value == find_value]
                    key_list.extend(tmp_key_list)
            elif type(data[dataList]) == dict:
                tmp_key_list = [{'column': key, 'row': '0'} for key, value in data[dataList].items() if value == find_value]
                key_list.extend(tmp_key_list)
        elif find_option == 'key':
            if type(data[dataList]) == list:
                for row in data[dataList]:
                    key_list = [{'column': key, 'row': '0'} for key in list(row.keys()) if key == find_value]
            elif type(data[dataList]) == dict:
                key_list = [{'column': key, 'row': '0'} for key in list(data[dataList].keys()) if key == find_value]

        if key_list:
            for ref_key in key_list:
                ref_info = {'target': step.target, 'description': step.description, 'step_id': step.stepId, 'dataList_id': dataList, 'column': ref_key['column'],'row': ref_key['row']}
                findRefData.append(ref_info)

    return findRefData

def displayMarking(step, data, input_marking_data, worker_id):
    ''' [list] displayMarking ((Class) Step, (Class) Data)
    request 이후 marking 된 column의 값을 화면에 노출하기 위함
    [ {'test_data_name': 'DATA #1',
       'test_data_id': 'xxxx-xxxx-xxxx-xxxx',
       'result_msg': '',
       'marking_data': [{'target': 'ZORDSS01S0010_TR01', 'description': '신규가입 처리서비스목록 조회', 'column_id': ''svc_num', 'value': '01012341234', 'step_id: 'xxxx-xxxx-xxxx-xxxx'},
                        {'target': 'ZORDSS01S0010_TR05', 'description': 'B2C가입 I/F 송신', 'column_id': ''svc_mgmt_num', 'value': '711111111', 'step_id: 'xxxx-xxxx-xxxx-xxxx'}
                       ]
      },
      {'test_data_name': 'DATA #2',
       .....}
    ]
    '''

    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

    index = findDictIndexByValue(input_marking_data, 'test_data_id', worker_id)

    markingData = []

    for dataListId in step.getInputDataList():
        for columInfo in step.getMarkingColumn(dataListId):
            value = data.getInputDataValue(columInfo['id'], 0, columInfo['column'])
            markingDataDtl = {'target': step.target,
                              'dataList_id': dataListId,
                              'column_id': columInfo['column'],
                              'value': value,
                              'step_id': step.stepId}

            if index > -1:
                try:
                    marking_data_index = next(idx for idx, row in enumerate(input_marking_data[index]['marking_data']) if row['step_id'] == step.stepId and row['column_id'] == columInfo['column'])
                except StopIteration:
                    marking_data_index = -1

                # 동일한 Working ID, Step ID 인 경우 값을 대체함
                if marking_data_index > -1:
                    input_marking_data[index]['marking_data'][marking_data_index] = markingDataDtl
                else:
                    markingData.append(markingDataDtl)
            else:
                markingData.append(markingDataDtl)

    if index > -1:
        input_marking_data[index]['execution_time'] = nowDatetime
        input_marking_data[index]['marking_data'].extend(markingData)
    else:
        # Seq채번
        tmp_seq = []

        for testDataName in input_marking_data:
            tmp_seq.append(testDataName['test_data_name'].split('#')[1])

        if tmp_seq:
            seq = int(max(tmp_seq)) + 1
        else:
            seq = 1

        test_data_name = 'DATA #{}'.format(seq)

        markingInfo = {'test_data_name': test_data_name,
                       'test_data_id': worker_id,
                       'execution_time': nowDatetime,
                       'result': 0,
                       'result_msg': '',
                       'marking_data': markingData}

        input_marking_data.append(markingInfo)

def excludedTrList(exclude_tr_list, tr_id, tr_name):
    ''' [list] excludedTrList ((List) exclude_tr_list, (str) tr_id, (str) tr_name)
        제외 할 Transaction 목록을 관리하기 위함
        [ {'tr_id': 'ZNGMSCOD00010_TR02', 'tr_name': '업무용 COMBO'},
          {'tr_id': 'ZNGMSDET10090_TR10', 'tr_name': '상세권한별 화면항목조회'},
           ...
        ]
        '''
    tr_info = {'tr_id': tr_id,
               'tr_name': tr_name}

    if tr_info in exclude_tr_list:
        pass
    else:
        exclude_tr_list.append(tr_info)


def stepRefRelListAll(step_list):
    ''' [list] stepRefRelListAll ((List) step_list)
        Case의 존재하는 Step들의 참조 관계를 관리하기 위함
        해당 정보를 저장하여 다른 Case에 적용 가능함
        [ {'seq': 1, 'ref_method': 'DataList', 'refed_step_column': 'ZORDSACT00010_TR01.input1.acnt_num', 'ref_count': 1, 'ref_step_columns':[ZORDSCOM20010_TR01.input1.new_eqp_mdl_cd.47b114ca-d027-4fff-aa78-e905304b8864]},
          {'seq': 2, 'ref_method': 'DataList', 'refed_step_column': 'ZNGMSLOV00010_TR01.input1.iparam1', 'ref_count': 1, 'ref_step_columns':[ZORDSS01S0010_TR01.output1.cust_nm.097456b6-726f-4494-a731-ff9ed6afe083]},

           - refed_step_column : 참조되는 Column
           - ref_step_columns : 참조하는 Column List
           ...
        ]
    '''
    refList = []
    seq = 1

    for step in step_list:
        for dataInfo in step.inputDataListInfo:
            inputRefList = list(filter(lambda data: data['ref_method'] in ['DataList', 'SQL', 'Excel', 'Row Level', 'Today'],dataInfo['columns']))

            if inputRefList:
                for ref in inputRefList:
                    refDtl = {}
                    Referencing_Info = '.'.join([step.target, dataInfo['id'], ref['id'], step.stepId])

                    refDtl['ref_method'] = ref['ref_method']

                    if ref['ref'] and ref['ref_method'] not in ['Row Level']:
                        # print('{refed} - {ref}'.format(refed=ReferencedInfo, ref=ref['ref']))
                        target, dataListId, column, row, stepId = parsingRef(ref['ref'])
                        refDtl['refed_step_column'] = '.'.join([target, dataListId, column, str(row)])
                    #elif ref['ref_method'] in ['Today', 'Row Level']:
                    #    refDtl['refed_step_column'] = Referencing_Info
                    else:
                        refDtl['refed_step_column'] = ''

                    refList.append(refDtl)
                    seq += 1

    #print(len(refList))

    #dstinct_refList = remove_dupe_dicts(refList)

    # 순서는 유지하면서 중복제거
    dstinct_refList = list({v['ref_method']+v['refed_step_column']:v for v in refList}.values())

    #print(dstinct_refList)
    #print(len(dstinct_refList))

    for distinct_ref in dstinct_refList:
        refedStepColumns = getRefedStepColumnList(step_list, distinct_ref['ref_method'], distinct_ref['refed_step_column'])
        distinct_ref['ref_count'] = len(refedStepColumns)
        distinct_ref['ref_step_columns'] = refedStepColumns

    return dstinct_refList

def getRefedStepColumnList(step_list, ref_method, ref):
    ''' [list] getRefedStepColumnList ((List) step_list, (str) ref)
            ref 값을 참조하는 Step의 정보를 관리하기 위함
            [ZORDSCOM20010_TR01.input1.new_eqp_mdl_cd.47b114ca-d027-4fff-aa78-e905304b8864,
            ZORDSS01S0010_TR01.output1.cust_nm.097456b6-726f-4494-a731-ff9ed6afe083
            ]
        '''
    refList = []

    for step in step_list:
        for dataInfo in step.inputDataListInfo:
            refDtl = {}
            inputRefList = list(filter(lambda data: data['ref_method'] in ['DataList', 'SQL', 'Excel', 'Row Level', 'Today'],dataInfo['columns']))

            if inputRefList:
                for inputRef in inputRefList:
                    if inputRef['ref'] and inputRef['ref_method'] not in ['Row Level']:
                        target, dataListId, column, row, stepId = parsingRef(inputRef['ref'])
                        parsingInputRef = '.'.join([target, dataListId, column, str(row)])

                        if ref:
                            target, dataListId, column, row, stepId = parsingRef(ref)
                            parsing_ref = '.'.join([target, dataListId, column, str(row)])
                        else:
                            parsing_ref = ''

                        if parsingInputRef == parsing_ref:
                            ReferencedInfo = '.'.join([step.target, dataInfo['id'], inputRef['id'], "0", step.stepId])
                            refList.append(ReferencedInfo)
                    elif inputRef['ref_method'] in ['Today', 'Row Level', 'Excel']:
                        if ref_method == inputRef['ref_method']:
                            ReferencedInfo = '.'.join([step.target, dataInfo['id'], inputRef['id'], "0", step.stepId])
                            refList.append(ReferencedInfo)
                            if inputRef['ref_method'] == 'Excel':
                                print('==========')

    return refList