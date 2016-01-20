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

import matplotlib
matplotlib.use('Agg')


import datetime as DT
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
from matplotlib.dates import YEARLY, DAILY,WEEKLY,MONTHLY,DateFormatter, rrulewrapper, RRuleLocator, drange
import numpy as np
import datetime
import calendar


import matplotlib.dates as mdates
from dateutil.relativedelta import relativedelta



def render_mako_str(template, context):
    t=Template(template)
    buf=StringIO()
    ctx=Context(buf, **context)
    t.render_context(ctx)
    return buf.getvalue()

class sql_query(osv.osv):
    _name = "analysis.sql.query"
    def define_view(self, cr, uid, ids, ctx):
        for q in self.browse(cr, uid, ids):
            if q.type=='view':
                cr.execute("create or replace view %s as %s"%(q.ref,q.query) )
    def drop_view(self, cr, uid, ids, ctx):
        for q in self.browse(cr, uid, ids):
            if q.type=='view':
                cr.execute("drop view %s"%q.ref )

    def get_query_columns(self, cr, uid, query):
        if query:
            try:
                cr.execute(query+" LIMIT 0")
                cols=[desc[0] for desc in cr.description]
            except:
                cols=[]
        else:
            cols=[]
        return cols
    def table_to_dict(self, cr, uid, query_id,columns, data):
        dict_data=[]
        for row in data:
            val=dict( zip(columns, row) )
            dict_data.append(val)
        return dict_data
    def get_html_context(self, cr, uid, query_id):
        query = self.browse(cr,uid,query_id)
        columns = self.get_query_columns(cr,uid,query.query)
        cr.execute( query.query )
        data = [d for d in cr.fetchall()]
        ctx={'query' : query,
             'columns': columns,
             'data': data,
        }
        return ctx

    def _get(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        for r in self.browse(cr, uid, ids):
            cols = self.get_query_columns(cr, uid, r.query)
            val={'sql_columns': ",".join(cols),
            }
            res[r.id] = val
        return res

    def _query(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        for qt in self.browse(cr, uid, ids):
            ctx={'qt':qt}
            if qt.query_template:
                val={'query': render_mako_str(qt.query_template, ctx),
                 }
            else:
                val={'query':''}
            res[qt.id] = val
        return res

    def _today(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        for r in self.browse(cr, uid, ids):
            ctoday=time.gmtime()
            tm_year = ctoday.tm_year
            tm_mon = ctoday.tm_mon
            tm_mday = ctoday.tm_mday
            day=datetime.date(tm_year, tm_mon, tm_mday)
            y,wk,dwk=day.isocalendar()
            
            val={'date_today': day.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 'year_today': tm_year,
                 'week_today': wk,
                 'month_today': tm_mon,
            }
            res[r.id] = val

        return res
    _columns = {
        'date_start_type':fields.selection([('fixed_date','Fixed Date'),('date_delta','Date Delta'),('today','Today')], 'Data Start Type' ),

        "date_start":fields.date("Date Start"),
        "date_end":fields.date("Date End"),
        "type":fields.selection([('view','SQL View'),('query','SQL Query')],'Type'),
        "query_template":fields.text("Query"),
        'query':fields.function(_query, type='text', multi='query',method=True,string='Rendered Query'),

        "active":fields.boolean("Active"),
        'sql_columns':fields.function(_get, type='char', multi='get',method=True,string='SQL Columns'),
        'date_today':fields.function(_today, type='date', multi='today',method=True,string='Date Today'),
        'year_today':fields.function(_today, type='integer', multi='today',method=True,string='Year Today', size=44),
        'week_today':fields.function(_today, type='integer', multi='today',method=True,string='Week Today'),
        'month_today':fields.function(_today, type='integer', multi='today',method=True,string='Month Today'),

        "name":fields.char("Title", size=444),
        "ref":fields.char("ref", size=444),
        "description":fields.char("Description", size=444),
    }
    _defaults = {
        "active":True,
        }


class analysis_chart(osv.osv):
    _name = "analysis.chart"
    _columns = {
        'name':fields.char("Title", size=444),
        'ref':fields.char("ref", size=444),
        'xlabel':fields.char("X Label", size=444),
        'ylabel':fields.char("Y Label", size=444),
        'figxsize':fields.integer('Figure X Size'),
        'figysize':fields.integer('Figure Y Size'),
        'figdpi':fields.integer('Figure DPI'),
        'slice':fields.char('Slice',size=44),
        'colors':fields.char("Colors",size=4444),
        'image_file':fields.char("image_file", size=444),
        'xdata':fields.selection([('week','Week'),('month','Month'),('day','Day')],'xdata'),
        'xtickstrftime':fields.char("xtickstrftime",size=44, help="see strftime.org"),
        'type':fields.selection([('bar','Bar Chart'),('pie','Pie Chart'),('pie2','Pie2'),('pie3','Pie3'),('line','Line Chart')],'Type'),
        'query_ids':fields.many2many('analysis.sql.query','sql_query_chart_rel','query_id','chart_id'),
        }
    _defaults = {
        'figxsize':9,
        'slice': "slice(None, None, 1)",
        'figysize':6,
        'figdpi':45,
        'xtickstrftime':'%B',
        'xdata':'month',
        'colors':"['b','g','r','c','m','y','k']",
    }

    def generate_chart(self, cr, uid, image_id):
        image = self.browse(cr, uid, image_id)
        if image.type=='bar':
            self.generate_bar_chart(cr, uid, image )
        elif image.type=='pie':
            self.generate_pie_chart(cr, uid,  image )
        elif image.type=='pie2':
            self.generate_pie2_chart(cr, uid,  image )
        elif image.type=='pie3':
            self.generate_pie3_chart(cr, uid,  image )

    def generate_pie3_chart(self, cr, uid, image):
        COLOR_MAP={'picking_error':'#ff7865',
                   'faulty': '#fdaa66',
                   'damaged': '#fdbf66',
                   'not_wanted': '#fde666',
                   'repair':'#d8fd66',
                   'missing': 'r',
                   }

        ctoday=time.gmtime()
        tm_year = ctoday.tm_year
        tm_mon = ctoday.tm_mon
        tm_mday = ctoday.tm_mday
        day=datetime.date(tm_year, tm_mon, tm_mday)
        y,wk,dwk=day.isocalendar()
        if image.colors:
            COLORS=eval(image.colors)
        else:
            COLORS=['b','g','r','c','m','y','k']

        assert len(image.query_ids)==1
        q = image.query_ids[0]
        ctx=self.pool.get("analysis.sql.query").get_html_context(cr,uid,q.id)
        dd=np.array(ctx['data']).transpose()
       
        reason=dd[0]
        count=[int(x) for x in dd[1] ]
         
        print reason, count

        sizes = count #[100-actual_p, actual_p]

        #labels = 'Target: %.02f'%Target_month, 'Actual: %.02f'%actual_month
        labels = ["%s: %.02f"%(r,c) for r,c in zip(reason,count)]

        #colors = ['gold', 'yellowgreen']
        #colors = COLORS
        colors = [COLOR_MAP.get(r,'r') for r in reason]
        #explode = (0, 0.1)
        N=len(count)
        explode = [0.0 for x in range(N) ]
        if image.figxsize:
            figxsize=image.figxsize
        else:
            figxsize=20
        if image.figysize:
            figysize=image.figysize
        else:
            figysize=10
        if image.figdpi:
            figdpi=image.figdpi
        else:
            figdpi=45
        #print (figxsize, figysize), figdpi
        fig, ax = plt.subplots( figsize=(figxsize, figysize), dpi=figdpi )
        #fig, ax = plt.subplots()
        #plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%.1f%%', shadow=True)
        plt.pie(sizes, labels=labels, explode=explode, colors=colors, autopct='%.1f%%',shadow=True)

        # Set aspect ratio to be equal so that pie is drawn as a circle.
        plt.axis('equal')
        d=datetime.date(tm_year, tm_mon, tm_mday)
        plt.title( d.strftime(image.xtickstrftime ) )
        #image_path=get_module_path('html_reports')
        #image_file=os.path.join(image_path,fn)

        plt.savefig(image.image_file, bbox_inches='tight',dpi=figdpi)

    def generate_pie2_chart(self, cr, uid, image):
        ctoday=time.gmtime()
        tm_year = ctoday.tm_year
        tm_mon = ctoday.tm_mon
        tm_mday = ctoday.tm_mday
        day=datetime.date(tm_year, tm_mon, tm_mday)
        y,wk,dwk=day.isocalendar()
        if image.colors:
            COLORS=eval(image.colors)
        else:
            COLORS=['b','g','r','c','m','y','k']


        assert len(image.query_ids)==1
        q = image.query_ids[0]
        ctx=self.pool.get("analysis.sql.query").get_html_context(cr,uid,q.id)
        dd=np.array(ctx['data']).transpose()
        s=eval(image.slice)

        month=dd[0][0]
        #print dd[2][s]
        #print dd[3][s]

        Target_month=sum(dd[2][s])
        actual_month=sum(dd[3][s])

        #print [Target_month, actual_month]
        #by_month= orders_total_month_actual(cr)
        #Target_by_month= orders_total_month_Target(pool, cr, uid, y='2015')

        #actual_month = by_month.get( (y,tm_mon), 0.0)
        #Target_month = Target_by_month.get( (tm_year,tm_mon), 0.0 )

        if Target_month>0.0:
            actual_p=100*actual_month/Target_month
        else:
            actual_p=0.0

        sizes = [100-actual_p, actual_p]

        #labels = 'Target: %.02f'%Target_month, 'Actual: %.02f'%actual_month
        labels = "%s: %.02f"%(image.xlabel,Target_month), "%s: %.02f"%(image.ylabel,actual_month)
        #colors = ['gold', 'yellowgreen']
        colors = COLORS
        explode = (0, 0.1)


        if image.figxsize:
            figxsize=image.figxsize
        else:
            figxsize=20
        if image.figysize:
            figysize=image.figysize
        else:
            figysize=10
        if image.figdpi:
            figdpi=image.figdpi
        else:
            figdpi=45

        fig, ax = plt.subplots( figsize=(figxsize, figysize) , dpi=figdpi)

        #fig, ax = plt.subplots()

        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%.1f%%', shadow=True)
        # Set aspect ratio to be equal so that pie is drawn as a circle.
        plt.axis('equal')
        d=datetime.date(tm_year, tm_mon, tm_mday)
        plt.title( d.strftime(image.xtickstrftime ) )
        #image_path=get_module_path('html_reports')
        #image_file=os.path.join(image_path,fn)

        plt.savefig(image.image_file, bbox_inches='tight',dpi=figdpi)

    def generate_pie_chart(self, cr, uid, image):
        ctoday=time.gmtime()
        tm_year = ctoday.tm_year
        tm_mon = ctoday.tm_mon
        tm_mday = ctoday.tm_mday
        day=datetime.date(tm_year, tm_mon, tm_mday)
        y,wk,dwk=day.isocalendar()
        if image.colors:
            COLORS=eval(image.colors)
        else:
            COLORS=['b','g','r','c','m','y','k']


        assert len(image.query_ids)==1
        q = image.query_ids[0]
        ctx=self.pool.get("analysis.sql.query").get_html_context(cr,uid,q.id)
        dd=np.array(ctx['data']).transpose()
        s=eval(image.slice)

        month=dd[0][0]
        Target_month=sum(dd[1][s])
        actual_month=sum(dd[2][s])

        #print [Target_month, actual_month]
        #by_month= orders_total_month_actual(cr)
        #Target_by_month= orders_total_month_Target(pool, cr, uid, y='2015')

        #actual_month = by_month.get( (y,tm_mon), 0.0)
        #Target_month = Target_by_month.get( (tm_year,tm_mon), 0.0 )

        if Target_month>0.0:
            actual_p=100*actual_month/Target_month
        else:
            actual_p=0.0

        sizes = [100-actual_p, actual_p]

        #labels = 'Target: %.02f'%Target_month, 'Actual: %.02f'%actual_month
        labels = "%s: %.02f"%(image.xlabel,Target_month), "%s: %.02f"%(image.ylabel,actual_month)
        #colors = ['gold', 'yellowgreen']
        colors = COLORS
        explode = (0, 0.1)


        if image.figxsize:
            figxsize=image.figxsize
        else:
            figxsize=20
        if image.figysize:
            figysize=image.figysize
        else:
            figysize=10
        if image.figdpi:
            figdpi=image.figdpi
        else:
            figdpi=45

        fig, ax = plt.subplots( figsize=(figxsize, figysize), dpi=figdpi )

        #fig, ax = plt.subplots()

        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%.1f%%', shadow=True)
        # Set aspect ratio to be equal so that pie is drawn as a circle.
        plt.axis('equal')
        d=datetime.date(tm_year, tm_mon, tm_mday)
        plt.title( d.strftime(image.xtickstrftime ) )
        #image_path=get_module_path('html_reports')
        #image_file=os.path.join(image_path,fn)

        plt.savefig(image.image_file, bbox_inches='tight',dpi=figdpi)


    def generate_bar_chart(self, cr, uid, image):
        #N=0
        #data_map={}
        assert len(image.query_ids)==1
        q = image.query_ids[0]
        ctx=self.pool.get("analysis.sql.query").get_html_context(cr,uid,q.id)
        dd=np.array(ctx['data']).transpose()
        #print dd
        columns=ctx['columns']
        #assert len(d)==4
        s=eval(image.slice)
        #y1=dd[2][s]
        #y2=dd[3][s]
        if image.colors:
            COLORS=eval(image.colors)
        else:
            COLORS=['b','g','r','c','m','y','k']

        if image.figxsize:
            figxsize=image.figxsize
        else:
            figxsize=20
        if image.figysize:
            figysize=image.figysize
        else:
            figysize=10
        if image.figdpi:
            figdpi=image.figdpi
        else:
            figdpi=45

        fig, ax = plt.subplots( figsize=(figxsize, figysize), dpi=figdpi )

        rects=[]
        if image.xdata == 'day':
            #year=dd[0][s]
            x=dd[0][s]
            week=dd[1][s]

            N = len(x)
            ind = np.arange(N)  # the x locations for the groups

            M=len(dd)-2
            #width = 1.0/(M+1) #0.25       # the width of the bars
            width = (1.0 - 1.0/(3*M) )/M #0.25       # the width of the bars
            #print width,M,44*'x',image.name
            MAX_Y=0
            for i in range(M):
                y=dd[i+2][s]
                y=map(int, y)
                r = ax.bar(ind + i*width, y, width, color=COLORS[i])
                #rects2 = ax.bar(ind + width, y2, width, color='y')
                rects.append(r)
                if max(y)>=MAX_Y:
                    MAX_Y=max(y)
        else:
            year=dd[0][s]
            x=dd[1][s]
            N = len(x)
            ind = np.arange(N)  # the x locations for the groups

            M=len(dd)-2
            width = (1.0 - 1.0/(3*M) )/M #0.25       # the width of the bars
            #print width,M,44*'x',image.name
            MAX_Y=0
            for i in range(M):
                y=dd[i+2][s]

                r = ax.bar(ind + i*width, y, width, color=COLORS[i])
                #rects2 = ax.bar(ind + width, y2, width, color='y')
                rects.append(r)
                if max(y)>=MAX_Y:
                    MAX_Y=max(y)

        ax.set_ylabel(image.ylabel)
        ax.set_xlabel(image.xlabel)
        ax.set_title(image.name)
        ax.set_ylim( (0.0, MAX_Y*1.2) )
        #ax.set_xticks(ind + width)
        ax.set_xticks(ind )
        r0=[]
        for r in rects:
            r0.append( r[0] )
        if image.xdata=='week':
            ax.set_xticklabels( ["%d"%xx for xx in x] )
            ax.legend( tuple(r0), tuple( columns[2:] ) )
        elif image.xdata=='day':
            xticks=[]
            for day in x:
                d=datetime.datetime.strptime(day, DEFAULT_SERVER_DATE_FORMAT)
                xticks.append( d.strftime(image.xtickstrftime) )
            ax.set_xticklabels( xticks )
            ax.legend( tuple(r0), tuple( columns[2:] ) )
        else: #month
            xticks=[]
            for y,m in zip(year,x):
                d=datetime.date(int(y),int(m),1)
                xticks.append( d.strftime(image.xtickstrftime) )
            ax.set_xticklabels( xticks )
            ax.legend( tuple(r0), tuple( columns[2:] ) )      

        #ax.legend((rects1[0], rects2[0]), (columns[2], columns[3] ) )
        ax.grid()
        def autolabel(rects):
            # attach some text labels
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                        '%d' % int(height),
                        ha='center', va='bottom')
        for r in rects:
            autolabel(r)
            #autolabel(rects2)

        plt.savefig(image.image_file, bbox_inches='tight',dpi=figdpi)
