# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#    Copyright (C) 2011-today Synconics Technologies Pvt. Ltd. (<http://www.synconics.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
from dateutil.relativedelta import relativedelta


def to_ascii(a):
    if a is None:
        return ''
    out=''
    for x in a:
        if ord(x)<=128:
            out+=x
    return out

def render_mako_file(template, context):
    if os.path.isfile(template):
        template=file(template).read()
        t=Template(template)
        buf=StringIO()
        ctx=Context(buf, **context)
        t.render_context(ctx)
        return buf.getvalue()
    else:
        return None

HTML1="""<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="5" >
</head>
<body>

<h1>My First Heading</h1>

<p>My first paragraph.</p>

<h1>Time</h1>
<p>
"""
HTML2="""
</p>

<table border="1" style="width:100%">
  <tr>
    <td>Jill</td>
    <td>Smith</td> 
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td> 
    <td>94</td>
  </tr>
</table>

</body>
</html>
"""

import time
phonecall_sql ="""
"""

#number of open/done sale orders per shop, per date
#select count(so.id),ss.name,ss.id,so.date_order from sale_order so, sale_shop ss where so.shop_id=ss.id and state in ('done','manual','progress') group by ss.name,so.date_order order by so.date_order desc

#total inbound calls
#select cpr.day,cpr.month,sum(nbr) from crm_phonecall_report cpr,crm_case_categ ccc where cpr.categ_id=ccc.id group by cpr.month,cpr.day order by cpr.day desc
def total_inbound_calls(cr, data_map=None, header=None, dates=None):
    if data_map is None:
        data_map={}
    if header is None:
        header=[]
    if dates is None:
        dates=[]
    cr.execute("select cpr.day,sum(nbr) from crm_phonecall_report cpr,crm_case_categ ccc where cpr.categ_id=ccc.id group by cpr.month,cpr.day order by cpr.day desc")
    for date, sum_calls in cr.fetchall():
        v=data_map.setdefault(date, {})
        key=('inbound_total','crm.phonecall',False)
        v[key]=sum_calls
        if key not in header:
            header.append(key)
        if date not in dates:
            dates.append(date)
    return data_map, header, dates
    
def orders_by_shop(cr, data_map=None,header=None,dates=None):
    if data_map is None:
        data_map={}
    if header is None:
        header=[]
    if dates is None:
        dates=[]
    cr.execute("select so.date_order, ss.name,ss.id, count(so.id) from sale_order so, sale_shop ss where so.shop_id=ss.id and state in ('done','manual','progress') group by ss.name,ss.id,so.date_order order by so.date_order desc")
    for date,shop_name,shop_id,count in cr.fetchall():
        v=data_map.setdefault(date, {})
        key = (shop_name,'sale.shop',shop_id)
        v[key]=count
        if key not in header:
            if 'Retail'  in shop_name:
                header.append(key)
        if date not in dates:
            dates.append(date)
    return data_map, header, dates

def calls_by_category(cr, data_map=None, header=None,dates=None):
    if data_map is None:
        data_map={}
    if header is None:
        header=[]
    if dates is None:
        dates=[]
    cr.execute("select cpr.day,cpr.month,ccc.name,ccc.id,sum(nbr) from crm_phonecall_report cpr,crm_case_categ ccc where cpr.categ_id=ccc.id group by cpr.month,ccc.name,ccc.id,cpr.day order by cpr.day desc")
    for day,month,name,categ_id,nbr in cr.fetchall():
        v=data_map.setdefault(day, {})
        key = (name,'crm.case.categ',categ_id)
        v[key]=nbr
        if key not in header:
            header.append(key)
        if day not in dates:
            dates.append(day)
    return data_map,header, dates

def calc_ratios(data_map,header,dates):
    for date in dates:
        total_inbound_key=('inbound_total','crm.phonecall',False)
        phone_sales_closed_key=('Retail Phone','sale.shop',2)
        service_issues_key=('Customer Services - Happy','crm.case.categ',17)
        sales_opportunity_key=('Sales Opportunity','crm.case.categ',17)
        
        total_inbound=data_map.get(date,{}).get(total_inbound_key,0.0)
        phone_sales_closed=data_map.get(date,{}).get(phone_sales_closed_key,0.0)
        service_issues = data_map.get(date,{}).get(service_issues_key,0.0)
        sales_opportunity=data_map.get(date,{}).get(sales_opportunity_key,0.0)

        closed_ratio=0.0
        if sales_opportunity>0.0:
            closed_ratio=phone_sales_closed/sales_opportunity
        key=('Closed Ratio','',False)
        if key not in header:
            header.append(key)
        data_map[date][key]=closed_ratio
        issues_ratio=0.0
        if total_inbound>0.0:
            issues_ratio=service_issues/total_inbound
        key=('Issues Ratio','',False)
        if key not in header:
            header.append(key)

        data_map[date][key]=issues_ratio
    return data_map,header,dates

def week_analysis(data_map,dates):
    week_map={}
    for date in dates:
        phone_sales_closed_key=('Retail Phone','sale.shop',2)
        phone_sales_closed=data_map.get(date,{}).get(phone_sales_closed_key,0.0)
        dtuple=tuple( map(int, date.split('-')) )
        d=datetime.date( *dtuple )
        y,wk,dd=d.isocalendar()
        v = week_map.setdefault( (y,wk), [] )
        v.append( phone_sales_closed )
    return week_map
        
def procurement_exceptions(cr):
    cr.execute("select date_planned,state,count(id) from procurement_order group by date_planned,state order by date_planned desc")
    header = ["Date Planned", "State", "Count"]
    table=[]
    for date_planned, state, count in cr.fetchall():
        table.append( [date_planned, state, count] )
    ctx={'header5':header,
         'data5':table,
         }
    return ctx

def total_deliveries_by_delivery_partner(cr):
    cr.execute("select count(sp.id),sp.delivery_partner_id,rp.name from stock_picking sp, res_partner rp where sp.delivery_partner_id=rp.id and sp.type='out' and sp.state='done' group by rp.name, sp.delivery_partner_id order by rp.name")

    header = ["Count", "Delivery Partner ID", "Delivery Partner Name"]
    table=[]
    for ret in cr.fetchall():
        table.append( ret )
    ctx={'header6':header,
         'data6':table,
         }
    return ctx

def deliveries_by_delivery_partner(cr):
    cr.execute("select to_char(sp.date_done::timestamp with time zone, 'YYYY-MM-DD'::text) AS date_done_day,sp.delivery_partner_id,rp.name,count(sp.id) from stock_picking sp, res_partner rp where sp.delivery_partner_id=rp.id and sp.type='out' and sp.state='done' group by rp.name, sp.delivery_partner_id, date_done_day  order by date_done_day desc,rp.name limit 80")

    header = ["Date Done", "Delivery Partner ID", "Partner Name", "Count"]
    table=[]
    for ret in cr.fetchall():
        table.append( ret )
    ctx={'header7':header,
         'data7':table,
         }
    return ctx

def get_image_url(req, name):
    return req.httprequest.url_root + 'html_images'+'?image=%s'%name

plt.ioff()

select_str_week="""select ai.date_invoice AS date,
to_char(ai.date_invoice::timestamp with time zone, 'YYYY'::text) AS year,
to_char(ai.date_invoice::timestamp with time zone, 'MM'::text) AS month, 
SUM(CASE
  WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text]) THEN -ai.amount_untaxed
  WHEN ai.type::text = ANY (ARRAY['in_invoice'::character varying::text]) THEN ai.amount_untaxed
    ELSE 0.0
  END) AS actual_amount_untaxed
from account_invoice ai where state in ('open','paid') group by date, year,month order by date desc
"""
def orders_total_week(cr):
    cr.execute(select_str_week)
    by_week={}
    for date,year,month,actual_amount_untaxed in cr.fetchall():
        d=datetime.datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        y,wk,wkd=d.isocalendar()
        v_wk = by_week.setdefault( (year,wk) , [] )
        v_wk.append( actual_amount_untaxed )
    out={}
    for (year,wk),actuals in by_week.items():
        out[ (int(year),wk) ] = sum(actuals)
    return out

def sale_Target_pie(pool, cr, uid):
    fn='sale_Target_pie.png'

    ctoday=time.gmtime()
    tm_year = ctoday.tm_year
    tm_mon = ctoday.tm_mon
    tm_mday = ctoday.tm_mday
    day=datetime.date(tm_year, tm_mon, tm_mday)
    y,wk,dwk=day.isocalendar()

    wk_Target_ids=pool.get('analysis.week.forecast').search(cr, uid, [('wk','=',wk),('year_id.y','=',y)])
    assert len(wk_Target_ids)==1
    wk_f = pool.get('analysis.week.forecast').browse(cr, uid, wk_Target_ids[0] )
    
    by_week= orders_total_week(cr)
#    keys=sorted( by_week.keys() )

    actual_week = by_week.get( (y,wk), 0.0)

    if wk_f.sale_forecast>0.0:
        actual_p=100*actual_week/wk_f.sale_forecast
    else:
        actual_p=0.0

    sizes = [100-actual_p, actual_p]

    labels = 'Target: %.02f'%wk_f.sale_forecast, 'Actual: %.02f'%actual_week
    colors = ['gold', 'yellowgreen']
    explode = (0, 0.1)
  
    fig, ax = plt.subplots()

    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%.1f%%', shadow=True)
    # Set aspect ratio to be equal so that pie is drawn as a circle.
    plt.axis('equal')
    plt.title( wk_f.wk_title )
    #plt.show()
    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
    
    plt.savefig(image_file, bbox_inches='tight')
    return fn

target='464c59'
act='009da5'



def orders_total_day_actual(cr,start_date='2015-01-01'):
    select_str_day="""select to_char(ai.date_invoice::timestamp with time zone, 'YYYY-MM-DD'::text) AS day,
SUM(CASE
  WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text]) THEN -ai.amount_untaxed
  WHEN ai.type::text = ANY (ARRAY['in_invoice'::character varying::text]) THEN ai.amount_untaxed
    ELSE 0.0
  END) AS actual_amount_untaxed
from account_invoice ai where state in ('open','paid') and ai.date_invoice>=%s group by day;
"""
    cr.execute(select_str_day, (start_date, ) )
    return dict( [ (day,actual_amount_untaxed ) for day,actual_amount_untaxed in cr.fetchall() ] )


select_str_month="""select to_char(ai.date_invoice::timestamp with time zone, 'YYYY'::text) AS year,
to_char(ai.date_invoice::timestamp with time zone, 'MM'::text) AS month,
SUM(CASE
  WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text]) THEN -ai.amount_untaxed
  WHEN ai.type::text = ANY (ARRAY['in_invoice'::character varying::text]) THEN ai.amount_untaxed
    ELSE 0.0
  END) AS actual_amount_untaxed
from account_invoice ai where state in ('open','paid') group by year,month;
"""



def orders_total_month_actual(cr):
    cr.execute(select_str_month)
    return dict( [ ((int(year),int(month)),actual_amount_untaxed ) for year,month,actual_amount_untaxed in cr.fetchall() ] )

def orders_total_month_Target(pool, cr, uid, y=None):
    if y is None:
        wk_Target_ids=pool.get('analysis.week.forecast').search(cr, uid, [])
    else:
        wk_Target_ids=pool.get('analysis.week.forecast').search(cr, uid, [('year_id.y','=',y)])
    
    Target_by_month={}
    for wk in pool.get('analysis.week.forecast').browse(cr, uid, wk_Target_ids):
        m1=int(wk.month1)
        y=int(wk.year_id.y)
        m2=int(wk.month2)
        fm1=wk.forecastmonth1
        fm2=wk.forecastmonth2
        v1=Target_by_month.setdefault( (y,m1), [] )
        v1.append( fm1 )
        v2=Target_by_month.setdefault( (y,m2), [] )
        v2.append( fm2 )
    out={}
    for (y,m),Targets in Target_by_month.items():
        out[ (y,m) ] = sum(Targets)
    return out

def sale_Target_pie_month(pool, cr, uid):
    fn='sale_Target_pie_monty.png'

    ctoday=time.gmtime()
    tm_year = ctoday.tm_year
    tm_mon = ctoday.tm_mon
    tm_mday = ctoday.tm_mday
    day=datetime.date(tm_year, tm_mon, tm_mday)
    y,wk,dwk=day.isocalendar()
   
    by_month= orders_total_month_actual(cr)
    Target_by_month= orders_total_month_Target(pool, cr, uid, y=y)

    actual_month = by_month.get( (y,tm_mon), 0.0)
    Target_month = Target_by_month.get( (tm_year,tm_mon), 0.0 )

    if Target_month>0.0:
        actual_p=100*actual_month/Target_month
    else:
        actual_p=0.0
    sizes = [actual_month/Target_month, actual_month]
    sizes = [100-actual_p, actual_p]

    labels = 'Target: %.02f'%Target_month, 'Actual: %.02f'%actual_month
    colors = ['gold', 'yellowgreen']
    explode = (0, 0.1)
  
    fig, ax = plt.subplots()

    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%.1f%%', shadow=True)
    # Set aspect ratio to be equal so that pie is drawn as a circle.
    plt.axis('equal')
    plt.title( "Month %s/%s"%(tm_mon, tm_year) )
    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
    
    plt.savefig(image_file, bbox_inches='tight')
    return fn

def plot_by_month(ax, by_month, line='k', label=''):
    dates=[]
    values=[]
    for y,m in sorted(by_month.keys() ):
        dates.append( datetime.date( y,m,1) )
        values.append( by_month[ (y,m) ] )
    ax.plot(dates, values, line, label=label)

def plot_data_map(ax, data_map, line='k', label=''):
    dates=[]
    values=[]
    for date in sorted(data_map.keys() ):
        d=datetime.datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        dates.append( d )
        values.append( data_map[date] )
    ax.plot(dates, values, line, label=label)

delivery_sql="""select to_char(sp.date_done::timestamp with time zone, 'YYYY-MM-DD'::text) AS date_done_day,
count(id) as delivered from stock_picking sp where type='out' and state='done' and sp.date_done>=%s group by date_done_day order by date_done_day desc;"""

returns_sql="""select to_char(sp.date_done::timestamp with time zone, 'YYYY-MM-DD'::text) AS date_done_day,
count(id) as returned from stock_picking sp where type='in' and state='done' and is_returned = True  and sp.date_done>=%s group by date_done_day order by date_done_day desc;"""

def delivery_and_returns_data(cr, start_date='2015-07-01'):
    cr.execute(delivery_sql, (start_date,) )
    delivery_map=dict( [(date_done_day,delivered) for date_done_day,delivered in cr.fetchall()] )
    cr.execute(returns_sql, (start_date,) )
    returned_map=dict( [(date_done_day,returned) for date_done_day,returned in cr.fetchall()] )
    return delivery_map, returned_map


def delivery_and_returns(pool, cr, uid):
    fn='delivery_and_returns.png'
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    weeks = mdates.WeekdayLocator()
    days = mdates.DayLocator()
    yearsFmt = mdates.DateFormatter('%W')

    ct=time.gmtime()
    today=datetime.date(ct.tm_year, ct.tm_mon, ct.tm_mday)
    weeks13 = relativedelta(weeks=13)
    start_date = today-weeks13
    delivery_map, returned_map = delivery_and_returns_data(cr, start_date=start_date)

    #formatter = DateFormatter('%a %m/%d/%y')
    #dates_x = drange(date1, date2, delta)
    fig, ax1 = plt.subplots(nrows=1,ncols=1)
    plot_data_map( ax1, delivery_map, line='k', label='Delivered')
    plot_data_map( ax1, returned_map, line='b', label='Returned')
    ax1.legend()
    ax1.grid()

    ax1.xaxis.set_major_formatter(yearsFmt)
    ax1.xaxis.set_major_locator(weeks)
    ax1.xaxis.set_minor_locator(days)

    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
    print image_file
    plt.savefig(image_file, bbox_inches='tight')
    #print data_map
    return fn
    

def sales_total_by_month(pool, cr, uid):
    fn='sales_total_by_month.png'
    import datetime
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.cbook as cbook
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%m')
    weeks = mdates.WeekdayLocator()

    #by_month= orders_total_month_actual(cr)
    by_day = orders_total_day_actual(cr)
    Target_by_month= orders_total_month_Target(pool, cr, uid)


    #formatter = DateFormatter('%a %m/%d/%y')
    #dates_x = drange(date1, date2, delta)
    fig, ax1 = plt.subplots(nrows=1,ncols=1)
    plot_data_map( ax1, by_day, line='k', label='Actual')
    plot_by_month( ax1, Target_by_month, line='b', label='Target')
    ax1.legend()
    ax1.grid()
#    ax1.title( 'Total Sales since Dec 2013 ' )


    #ax=ax1
    #ax1.xaxis_date()
    #ax1.xaxis.set_major_formatter(formatter)
    #labels = ax1.get_xticklabels()
    #plt.setp(labels, rotation=30, fontsize=10)
    #plt.title('Phone Calls, 7 days window')
    #ax1.grid()

    ax1.xaxis.set_major_locator(months)
    ax1.xaxis.set_major_formatter(yearsFmt)
    ax1.xaxis.set_minor_locator(weeks)

    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
    print image_file
    plt.savefig(image_file, bbox_inches='tight')
    #print data_map
    return fn


def plot_days(ax, data_map, dates, key, line='k', label='Inbound Calls', days=7):
    data = [ (DT.datetime.strptime(d,
                                   "%Y-%m-%d"),data_map.get(d,0).get(key,0)) for (i,d) in
             enumerate(dates[0:days]) ]
    x = [date2num(date) for (date, value) in data if value>0]
    y = [value for (date, value) in data if value>0]
    handler_inbound=ax.plot(x, y, line, label=label)

    return handler_inbound

def sales_by_month(data_map,header,dates):
    fn='sales_by_month.png'

    rule = rrulewrapper(DAILY, byeaster=1, interval=5)
    loc = RRuleLocator(rule)

    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    weeks = mdates.WeekdayLocator()
    days = mdates.DayLocator()
    weeks.MAXTICKS = 2000


    formatter = DateFormatter('%a %d/%m/%y')
    #dates_x = drange(date1, date2, delta)
    fig, ax1 = plt.subplots(nrows=1,ncols=1)    
    #ax=ax1
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(formatter)
    ax1.xaxis.set_major_locator(weeks)
    ax1.xaxis.set_minor_locator(days)

    labels = ax1.get_xticklabels()
    #labels = ax1.xaxis.get_major_ticks()

    plt.setp(labels, rotation=30, fontsize=10)
    plt.title('Phone Calls, 30 days window')
    ax1.grid()

    key_inbound=(u'Inbound', 'crm.case.categ', 18)
    plot_days(ax1, data_map, dates, key_inbound, line='k', label='Inbound Calls', days=30)

    key_sales= (u'Sales Opportunity', 'crm.case.categ', 15)
    plot_days(ax1, data_map, dates, key_sales, line='r', label='Sales Opportunity', days=30)

    key_phone= (u'Retail Phone', 'sale.shop', 2)
    plot_days(ax1, data_map, dates, key_phone, line='-', label='Closed Sales', days=30)

    ax1.legend()

    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
#    print image_file
    plt.savefig(image_file, bbox_inches='tight')
    #print data_map
    return fn

def weekly_calls(data_map, header, dates):
    key_inbound=(u'Inbound', 'crm.case.categ', 18)
    key_sales= (u'Sales Opportunity', 'crm.case.categ', 15)
    key_phone= (u'Retail Phone', 'sale.shop', 2)

#ing pribil, 505
#poverena zkusebna
#dekra.cz
#nebo tuv sud.cz
# rehacek vladimir: 724 533 918


#dekra klicany
#Ing. Petr Říha 
#+420 267 288 228
#petr.riha@dekra.cz

#284 00 12 11
#4000kc
#nabrezi ludvika svobody 12 22 , odbor provozu silnicnich vozidel, ing josef pribyl

    
def sales_by_7days(data_map,header,dates):
    fn='sales_by_7days.png'
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    weeks = mdates.WeekdayLocator()
    days = mdates.DayLocator()
    days.MAXTICKS = 2000

    formatter = DateFormatter('%a %d/%m/%y')
    
    fig, ax1 = plt.subplots(nrows=1,ncols=1)

    #rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)
    
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(formatter)
    ax1.xaxis.set_major_locator(days)
    #ax1.xaxis.set_minor_locator(days)

    labels = ax1.get_xticklabels()
    plt.setp(labels, rotation=30, fontsize=10)
    plt.title('Phone Calls, 7 days window')
    ax1.grid()

    key_inbound=(u'Inbound', 'crm.case.categ', 18)
    plot_days(ax1, data_map, dates, key_inbound, line='k', label='Inbound Calls', days=7)

    key_sales= (u'Sales Opportunity', 'crm.case.categ', 15)
    plot_days(ax1, data_map, dates, key_sales, line='r', label='Sales Opportunity', days=7)

    key_phone= (u'Retail Phone', 'sale.shop', 2)
    plot_days(ax1, data_map, dates, key_phone, line='-', label='Closed Sales', days=7)

    ax1.legend()

    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
    print image_file
    plt.savefig(image_file, bbox_inches='tight')
    #print data_map
    return fn

def sales_bar_chart():
    fn='sales_bar_chart.png'

    N = 5
    menMeans = (20, 35, 30, 35, 27)
    menStd = (2, 3, 4, 1, 2)

    ind = np.arange(N)  # the x locations for the groups
    width = 0.35       # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)

    womenMeans = (25, 32, 34, 20, 25)
    womenStd = (3, 5, 2, 3, 3)
    rects2 = ax.bar(ind + width, womenMeans, width, color='y', yerr=womenStd)

    # add some text for labels, title and axes ticks
    ax.set_ylabel('Scores')
    ax.set_title('Scores by group and gender')
    print "ind + width ", ind, width, ind+width
    ax.set_xticks(ind + width)
    ax.set_xticklabels(('G1', 'G2', 'G3', 'G4', 'G5'))

    ax.legend((rects1[0], rects2[0]), ('Men', 'Women'))

    def autolabel(rects):
        # attach some text labels
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                    '%d' % int(height),
                    ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    image_path=get_module_path('html_reports')
    image_file=os.path.join(image_path,fn)
    plt.savefig(image_file, bbox_inches='tight')
    #print data_map
    return fn

def get_image_url(req, name): 
    return req.httprequest.url_root +'html_images'+'?image=%s'%name

def get_query_url(req, q,dbname):
    return req.httprequest.url_root + 'sql_query'+'?query_id=%s&db=%s'%(q.id,dbname)

def get_query_list_url(req, dbname):
    return req.httprequest.url_root + 'sql_query_list'+'?db=%s'%dbname

class web_sql_query_list(oeweb.Controller):
    _cp_path = "/sql_query"
    
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        if req.httprequest.remote_addr in ['127.0.0.1']:
            pass
        else:
            return Response('Not authorized', mimetype='text/html')
        if 'db' in kw:
            dbname=kw['db']
        else:
            dbname='pjb_live'
        html_ret=""
        uid=1
        registry = openerp.modules.registry.Registry(dbname)
        with registry.cursor() as cr:
            pool = pooler.get_pool(dbname)
            if 'query_id' in kw:
                query_id=int( kw['query_id'] )
                template_path = get_module_resource('html_reports', '', 'sql_query.html')
                url_ctx={'req':req,
                         'dbname':dbname,
                         'get_query_list_url':get_query_list_url
                         }
                ctx = pool.get("analysis.sql.query").get_html_context(cr,uid,query_id)
                ctx.update( url_ctx )
                html_ret = render_mako_file(template_path, ctx)
            else:
                pass
        return Response(html_ret, mimetype='text/html')


#class SaleReport(openerp.http.Controller):
#    @openerp.http.route('/sale_report', auth='public')
#    def handler(self):
#        r='hovno'
#        return r


class web_sql_query_list(oeweb.Controller):
    _cp_path = "/sql_query_list"
    
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        if 'db' in kw:
            dbname=kw['db']
        else:
            dbname='pjb_live'
        html_ret=""
        uid=1
        registry = openerp.modules.registry.Registry(dbname)
        with registry.cursor() as cr:
            pool = pooler.get_pool(dbname)
            query_ids=pool.get("analysis.sql.query").search(cr,uid,[])
            queries = pool.get("analysis.sql.query").browse(cr,uid,query_ids)
            
            ctx={'title' : "List of SQL Queries",
                 'sql_queries': queries,
                 'get_query_url': get_query_url,
                 'req':req,
                 'dbname':dbname,
            }
            template_path = get_module_resource('html_reports', '', 'sql_query_list.html')
            html_ret = render_mako_file(template_path, ctx)
        return Response(html_ret, mimetype='text/html')

class web_sql_query_list(oeweb.Controller):
    _cp_path = "/chart_list"
    
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        if 'db' in kw:
            dbname=kw['db']
        else:
            dbname='pjb_live'
        html_ret=""
        uid=1
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        registry = openerp.modules.registry.Registry(dbname)
        with registry.cursor() as cr:
            pool = pooler.get_pool(dbname)
            chart_ids=pool.get("analysis.chart").search(cr,uid,[])
            charts = pool.get("analysis.chart").browse(cr,uid,chart_ids)
            image_path=get_module_path('html_reports')

            for chart in charts:
                fn="%d.png" % chart.id
                image_file=os.path.join(image_path,fn)
                chart.write({"image_file":image_file})
                
                #pool.get('analysis.chart').generate_bar_charts(cr, uid, chart_ids)
                pool.get('analysis.chart').generate_chart(cr, uid, chart.id)

            ctx={'title' : "List of Charts",
                 'charts': charts,
                 'fn':fn,
                 'get_image_url': get_image_url,
                 'req':req,
                 'dbname':dbname,
            }
            template_path = get_module_resource('html_reports', '', 'chart_list.html')
            html_ret = render_mako_file(template_path, ctx)
        return Response(html_ret, mimetype='text/html')

class image(object):
    def __init__(self, req, dbname, pool, cr, uid):
        self.req=req
        self.dbname=dbname
        self.pool=pool
        self.cr=cr
        self.uid=uid
    def get(self, ref):
        chart_ids=self.pool.get("analysis.chart").search(self.cr,self.uid,[('ref','=',ref)])
        if len(chart_ids)==1:
            chart_id = chart_ids[0]
            image=self.pool.get('analysis.chart').browse(self.cr, self.uid, chart_id)
            return image
        return None

    def render(self, ref):
        ret='<img src="1.png" alt="IMAGE NOT FOUND"/>'
        image=self.get(ref)
        if image:
            self.pool.get('analysis.chart').generate_chart(self.cr, self.uid, image.id)
            image=self.pool.get('analysis.chart').browse(self.cr, self.uid, image.id)
            image_url=get_image_url(self.req,'%d.png'%image.id )
            ret='<img src="%s" alt="%s"/>' % (image_url, image.name)
        return ret


class table(object):
    def __init__(self, req, dbname, pool, cr, uid):
        self.req=req
        self.dbname=dbname
        self.pool=pool
        self.cr=cr
        self.uid=uid
    def get(self, ref):
        query_ids=self.pool.get("analysis.sql.query").search(self.cr,self.uid,[('ref','=',ref)])
        if len(query_ids)==1:
            query_id = query_ids[0]
            query=self.pool.get('analysis.sql.query').browse(self.cr, self.uid, query_id)
            return query
        return None

    def render(self, ref,mako_template,template_module='html_reports'):
        query=self.get(ref)
        template_path = get_module_resource(template_module, '', mako_template)
        html_ret=""
        if query:
            #self.pool.get('analysis.chart').generate_chart(self.cr, self.uid, image.id)
            #cr.execute( query.query )
            #data=[x for x in cr.fetchall()]
            ctx=self.pool.get('analysis.sql.query').get_html_context(self.cr, self.uid,query.id)
            html_ret = render_mako_file(template_path, ctx)
            #image=self.pool.get('analysis.chart').browse(self.cr, self.uid, image.id)
            #image_url=get_image_url(self.req,'%d.png'%image.id )
            #ret='<img src="%s" alt="%s"/>' % (image_url, image.name)
        return html_ret

class web_sql_query_list(oeweb.Controller):
    _cp_path = "/kpi"
    
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        if 'db' in kw:
            dbname=kw['db']
        else:
            dbname='pjb_live'
        html_ret=""
        uid=1
        registry = openerp.modules.registry.Registry(dbname)
        with registry.cursor() as cr:
            pool = pooler.get_pool(dbname)
            ctx={'image':image(  req, dbname, pool, cr, uid ),
            'table':table( req, dbname, pool, cr, uid ),
            }

            template_path = get_module_resource('html_reports', '', 'kpi.html')
            html_ret = render_mako_file(template_path, ctx)
        return Response(html_ret, mimetype='text/html')


class web_redirect_url_new(oeweb.Controller):
    _cp_path = "/html_reports"
    
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        #dbname='pjb-2015-09-03_2253'
        #bname='pjb_live'
        if 'db' in kw:
            dbname=kw['db']
        else:
            dbname='pjb_live'
        html_ret=""
        uid=1
        registry = openerp.modules.registry.Registry(dbname)
        with registry.cursor() as cr:
            pool = pooler.get_pool(dbname)
            data_map,header,dates = orders_by_shop(cr)
            data_map, header,dates = calls_by_category(cr, data_map,header,dates)
            data_map, header,dates = total_inbound_calls(cr, data_map, header,dates)
            data_map, header,dates = calc_ratios(data_map, header,dates)
            table = []
            for date in sorted(dates,reverse=True):
                row=[]
                for h in header:
                    v=data_map.get(date, {})
                    row.append( v.get(h,0.0) )
                table.append( (date,row) )
            by_month_fn=sales_by_month(data_map,header,dates)
            by_7days_fn=sales_by_7days(data_map,header,dates)

            by_pie_fn=sale_Target_pie(pool, cr, 1)
            by_pie_month_fn=sale_Target_pie_month(pool, cr, 1)

            sales_total_by_month_fn = sales_total_by_month(pool, cr, uid)
            delivery_and_returns_fn = delivery_and_returns(pool, cr, uid)
            sales_bar_chart_fn = sales_bar_chart()
            
            ctx3={'header3' : [('','','')]+header,
                  'sales_by_month_url': get_image_url(req, by_month_fn ),
                  'sales_by_7days_url': get_image_url(req, by_7days_fn ),
                  'sale_Target_pie_url': get_image_url(req,by_pie_fn),
                  'sale_Target_pie_month_url': get_image_url(req,by_pie_month_fn),
                  'sales_total_by_month_url': get_image_url(req,sales_total_by_month_fn),
                  'delivery_and_returns_url': get_image_url(req,delivery_and_returns_fn),
                  'sales_bar_chart_url': get_image_url(req,sales_bar_chart_fn),

                  'data3':table}
            #time_now = 
            #html_ret=HTML1+time_now+HTML2

            week_map = week_analysis(data_map, dates)
            header4 = ['Year','Week','Date Start', 'Date Stop', 'Target', 'Actual']
            table4=[]
            y_ids=pool.get('analysis.year').search(cr, uid, [])
            for y in pool.get('analysis.year').browse(cr, uid, y_ids):
                for wk in y.week_ids:
                    key=(y.y, wk.wk)
                    actual = sum( week_map.get(key, []) )
                    row = [y.y, wk.wk, wk.date_start, wk.date_stop, wk.sale_forecast, actual]
                    table4.append(row)
            ctx4={'header4':header4,
                  'data4':table4
                  }

            header = ['%02d'%x for x in range(1,13)]
            cr.execute("select cpr.month,ccc.id,sum(nbr) from crm_phonecall_report cpr,crm_case_categ ccc where cpr.categ_id=ccc.id group by cpr.month,ccc.id;")
            data_map = dict( [( (m,c),nbr) for m,c,nbr in cr.fetchall() ] )
            categ_ids = pool.get("crm.case.categ").search(cr, uid, [])
            categ_map= dict( [(c.id,c) for c in pool.get("crm.case.categ").browse(cr, uid, categ_ids) ] )
           
            table = []
            for c_id in categ_ids:
                row=[]
                for hh in header:
                    row.append( data_map.get( (hh,c_id), 0.0) )
                table.append( (categ_map[c_id], row) )
            template_path = get_module_resource('html_reports', '', 't2.html')
            ctx={'time_now':time.asctime(),
                 'header':['']+header,
                 'data':table}

            cr.execute("select cpr.day,cpr.month,ccc.name,sum(nbr) from crm_phonecall_report cpr,crm_case_categ ccc where cpr.categ_id=ccc.id group by cpr.month,ccc.name,cpr.day order by cpr.day desc")
            table2=[(day,month,name,nbr) for day,month,name,nbr in cr.fetchall()]
            header2=['Day','Month','Category','Calls']
            ctx2 ={'header2':header2,
                   'data2':table2}

            ctx5=procurement_exceptions(cr)
            ctx6=total_deliveries_by_delivery_partner(cr)
            ctx7=deliveries_by_delivery_partner(cr)
            ctx.update(ctx2)
            ctx.update(ctx3)
            ctx.update(ctx4)
            ctx.update(ctx5)
            ctx.update(ctx6)
            ctx.update(ctx7)

            html_ret = render_mako_file(template_path, ctx)

        return Response(html_ret, mimetype='text/html')



# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:



