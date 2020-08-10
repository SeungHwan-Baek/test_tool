import os
import sys
import codecs
import ast
from configparser import ConfigParser

class Config(object):
    def __init__(self):
        parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.path = os.path.join(parentDir, "config.ini")

        # instantiate
        self.config = ConfigParser()

        if os.path.exists(self.path):
            pass
        else:
            f = open(self.path, 'w')
            f.close()

        # parse existing file
        self.config.read_file(codecs.open(self.path, "r", "utf8"))

    def getlist(self, section, option):
        result_list = []

        if self.config.has_option(section, option):
            result_list = ast.literal_eval(self.config.get(section, option))

        return result_list

    def get(self, section, option):
        return self.config.get(section, option)

    def getInt(self, section, option):
        return self.config.getint(section, option)

    def getBoolean(self, section, option):
        return self.config.getboolean(section, option)