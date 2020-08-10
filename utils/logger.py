import os
currentDir = os.path.dirname(os.path.realpath(__file__))
parentDir = os.path.normpath(os.path.join(currentDir, ".."))

import logging
#from logging.handlers import RotatingFileHandler
from logging.handlers import TimedRotatingFileHandler
import shutil
import time
from datetime import datetime
from utils.settings import Settings

HOME = os.path.expanduser("~")
HOME_SAVE_PATH = os.path.join(HOME, '.test_tool')

settings = Settings(HOME_SAVE_PATH)
settings.load()

LOG_FILE_FOLDER = settings.get("SETTING_LOG_PATH", "log")
LOG_PATH = os.path.join(HOME, 'Test_Tool', LOG_FILE_FOLDER)
LOG_ARCHIVING_CYCLE = settings.get("SETTING_LOG_ARCHIVING_CYCLE", 21)
BACKUP_COUNT = settings.get("SETTING_LOG_BACKUP_CNT", 5)


def CreateLogger(logger_name):
    # Create Logger
    logger = logging.getLogger(logger_name)

    # Check handler exists
    if len(logger.handlers) > 0:
        return logger  # Logger already exists
    '''
    로그레벨
        - DEBUG
        - INFO
        - WARNING (미사용)
        - ERROR
        - CRITICAL (미사용)
    '''
    logger.setLevel(logging.ERROR)

    # create formatter and add it to the handlers
    #formatter = logging.Formatter('[%(asctime)s] %(levelname)5s - %(message)s ' +
    #                              '(%(filename)s:%(lineno)s)', datefmt='%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('[%(asctime)s] %(levelname)8s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    day = time.strftime('%Y%m%d')

    if not os.path.exists(os.path.join(LOG_PATH, day)):
        os.makedirs(os.path.join(LOG_PATH, day))

    # create file handler which logs even debug messages
    logFilename = 'log_{day}.log'.format(day=time.strftime('%Y%m%d'))
    logFilePath = os.path.join(LOG_PATH, day, logFilename)

    # 보관주기 이후 폴더 삭제
    now = datetime.now()
    for f in os.listdir(LOG_PATH):
        path = os.path.join(LOG_PATH, f)
        dir_day = datetime.strptime(f, '%Y%m%d')
        if (now - dir_day).days > int(LOG_ARCHIVING_CYCLE):
            shutil.rmtree(path)

    # 동일한 로그파일 존재 시 삭제
    #if os.path.isfile(logFilePath):
    #    os.unlink(logFilePath)

    #fileHandler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1024*5, backupCount=5, mode='w', encoding='utf-8')
    #logFilename = LOG_FILE_PATH + 'log_' + process + '.log'
    #fileHandler = RotatingFileHandler(logFilename, mode='w', backupCount=BACKUP_COUNT, encoding='utf-8')
    fileHandler = TimedRotatingFileHandler(filename=logFilePath, when='midnight', interval=1, encoding='utf-8', backupCount=BACKUP_COUNT)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)

    # create console handler with a higher log level
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)

    return logger