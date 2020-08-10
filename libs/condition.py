class Condition:
    def __init__(self, case):
        self.case = case
        self.target_variable = ''  # $TARGET_SVC_MGMT_NUM$
        self.operator = ''
        '''
        # Equal To(=), Not Equal To(<>), 
          Includes(in), Dose Not Include(non in), 
          Greater Than(>), Greater Than or Equal To(>=)
          Less Than(<), Less Than or Equal To(<=)
        '''
        self.value = ''  # 71234568 or $SVC_MGMT_NUM$

        # If $TARGET_SVC_MGMT_NUM$ = $SVC_MGMT_NUM$ Then

    def setTargetVariable(self, target_variable):
        self.target_variable = target_variable

    def setOperator(self, operator):
        self.operator = operator

    def setValue(self, value):
        self.value = value

    def getResult(self):
        target_variable = self.getVariableValue(self.target_variable)
        value = self.getVariableValue(self.value)

        if self.operator == '=':
            return target_variable == value
        elif self.operator == '<>':
            return target_variable != value
        elif self.operator == '>':
            return target_variable > value
        elif self.operator == '>=':
            return target_variable >= value
        elif self.operator == '<':
            return target_variable < value
        elif self.operator == '<=':
            return target_variable <= value
        elif self.operator in ['in', 'not in']:
            if type(value) != list:
                value_list = []
                value_list.append(value)
            else:
                value_list = value

            if self.operator == 'in':
                return target_variable in value_list
            elif self.operator == 'not in':
                return target_variable not in value_list


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
