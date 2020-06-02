import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import praw
import re
import time
import os
import logging
import logging.config

# Logging allows replacing print statements to show more information
# This config outputs human-readable time, the log level, the log message and the line number this originated from
logging.basicConfig(
    format='%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)', level=logging.DEBUG)

# PRAW seems to have its own logging which clutters up console output, so this disables everything but Python's logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True
})


class CPUbot():

    def __init__(self):
        self.passmark_page = 'https://www.cpubenchmark.net/cpu_list.php'
        self.github_link = 'https://github.com/Pixxel123/PCSX2-CPU-Bot'
        self.latest_build = 'https://buildbot.orphis.net/pcsx2/'
        self.pcsx2_page = 'https://pcsx2.net/getting-started.html'
        self.str_minimum = 1600
        self.str_recommended = 2100
