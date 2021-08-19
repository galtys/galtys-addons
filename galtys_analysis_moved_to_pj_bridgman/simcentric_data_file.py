from openerp.osv import fields, osv
from openerp.report import report_sxw
import time
from pjb import setup_dates, analyse_so, analyse_phonecalls, analyse_sales, traverse_preorder, period2dates, ValueCalc
import pjb
import datetime
import calendar
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

from StringIO import StringIO
from mako.template import Template
from mako.runtime import Context
import os



import datetime as DT
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
from matplotlib.dates import YEARLY, DAILY,WEEKLY,MONTHLY,DateFormatter, rrulewrapper, RRuleLocator, drange
import numpy as np
import datetime
import calendar


import matplotlib.dates as mdates
from dateutil.relativedelta import relativedelta

