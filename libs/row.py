class Row:
    info = {}

    def __init__(self, step=None):
        self.step = step
        self.info = {}

    def __setitem__(self, key, value):
        self.info[key] = value

    def __getitem__(self, key):
        return self.info[key]

    def get(self, key, default=''):
        if key in self.info:
            if self.info[key] == '':
                return default
            else:
                return self.info[key]
        else:
            return default

    def getKey(self):
        return list(self.info.keys())

    def initKey(self, key, value):
        if key in self.info:
            pass
        else:
            self.info[key] = value

    def getStep(self):
        return self.step

    def getStepId(self):
        return self.step.getId()