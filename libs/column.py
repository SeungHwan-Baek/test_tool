class Column:
    info = {}

    def __init__(self, step=None):
        self.step = step
        self.info = {}

    def __setitem__(self, key, value):
        self.info[key] = value

    def __getitem__(self, key):
        return self.info[key]

    def get(self, key, default=None):
        if key in self.info:
            if self.info[key] == '':
                return default
            else:
                return self.info[key]
        else:
            return default

    def getKeys(self):
        return list(self.info.keys())