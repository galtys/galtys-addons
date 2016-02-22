import openerp.addons.web.http as oeweb
import werkzeug.utils
import werkzeug.wrappers

import openerp
from openerp import pooler
from openerp import SUPERUSER_ID
from werkzeug.wrappers import Response
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO

from openerp.modules.module import get_module_resource
from openerp.modules.module import get_module_path
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import datetime

import datetime as DT
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
from matplotlib.dates import YEARLY, DAILY,WEEKLY,MONTHLY,DateFormatter, rrulewrapper, RRuleLocator, drange
import numpy as np
import datetime
import calendar
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

import matplotlib.dates as mdates



class html_reports_images(oeweb.Controller):
    _cp_path = "/html_images"
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        if 'image' in kw:
            image=kw['image']
        else:
            image='pie.png'
        image_file=get_module_resource('html_reports', '', image)

        return Response(file(image_file).read(), mimetype='image/png')

# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:


