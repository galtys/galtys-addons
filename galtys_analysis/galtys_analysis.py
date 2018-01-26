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

from openerp.osv import fields, osv
from openerp.report import report_sxw
import time
from pjb import setup_dates, analyse_so, analyse_phonecalls, analyse_sales, traverse_preorder, period2dates, ValueCalc
import pjb
import datetime
import calendar
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

class analysis_date(osv.osv):
    _name = "analysis.date"
    _rec_name="date"
    _log_access = False
    _order = "sequence"
    _columns = {
        'sequence':fields.integer("Sequence"),
        'date': fields.date('Date'),
        'd':fields.integer('Day'),
        'm':fields.integer('Month'),
        'y':fields.integer('Year'),
        'wk':fields.integer('Week'),
        'weekend':fields.boolean('Weekend'),
        'isoday':fields.integer('isoday'),
        'period_id':fields.many2one('account.period', 'Account Period'),
        'period_code':fields.char("Period Code"),
    }

def get_day_map(d1,d2,DAY):
    d=d1
    day_map={}
    while d <= d2:
        v=day_map.setdefault( d.month, [])
        v.append( d )
        d+=DAY
    return day_map


class analysis_week(osv.osv):
    _name = "analysis.week.forecast"
    #_order = "year,week desc"
    def _calc(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        DAY=datetime.timedelta(days=1)
        for r in self.browse(cr, uid, ids):
            d1 = datetime.datetime.strptime(r.date_start, DEFAULT_SERVER_DATE_FORMAT)
            d2 = datetime.datetime.strptime(r.date_stop, DEFAULT_SERVER_DATE_FORMAT)
            day_map=get_day_map(d1, d2, DAY)
            #print day_map
            if len(day_map)==2:
                m1,m2 = d1.month, d2.month
                dm1 = len( day_map[m1] )
                dm2 = len( day_map[m2] )
            elif len(day_map)==1:
                m1, = day_map.keys()
                dm1 = len(day_map[m1])
                m2 = m1
                dm2=0
            else:
                assert 0
            sfd=r.sale_forecast/(dm1+dm2)
            val={'month1': m1,
                 'daysmonth1':dm1,
                 'forecastmonth1':dm1*sfd,
                 'month2': m2,
                 'daysmonth2': dm2,
                 'forecastmonth2':dm2*sfd,
                 'wk_title': 'Week: %s, Start Date: %s, Stop Date: %s'%(r.wk,r.date_start,r.date_stop)
            }
            res[r.id] = val
        return res
    _columns = {
        'code':fields.char("Code Stored"),
        'secret_key':fields.text("Secret_Key"),        
        'year_id':fields.many2one("analysis.year", "Year"),
        'wk':fields.integer("Week"),
        "date_start":fields.date("Date Start"),
        "date_stop":fields.date("Date Stop"),
        "sale_forecast":fields.float("Sale Forecast"),
        "active":fields.boolean("Active"),
        'month1':fields.function(_calc, type='float', multi='calc',method=True,string='Month1'),
        'daysmonth1':fields.function(_calc, type='float', multi='calc',method=True,string='DaysMonth1'),
        'forecastmonth1':fields.function(_calc, type='float', multi='calc',method=True,string='forecastmonth1'),
        'month2':fields.function(_calc, type='float', multi='calc',method=True,string='Month2'),
        'daysmonth2':fields.function(_calc, type='float', multi='calc',method=True,string='DaysMonth2'),
        'forecastmonth2':fields.function(_calc, type='float', multi='calc',method=True,string='forecastmonth2'),
        'wk_title':fields.function(_calc, type='float', multi='calc',method=True,string='wk_title'),
    }
    _defaults = {
        "active":True,
        }

class analysis_year(osv.osv):
    _name = "analysis.year"
    _columns = {
        "y":fields.integer("Year"),
        "week_ids":fields.one2many("analysis.week.forecast","year_id","Weeks"),
        "month_ids":fields.one2many("analysis.month.target","year_id","Month"),
        'code':fields.char("Code Stored"),
        'secret_key':fields.text("Secret_Key"),        
    }
    def setup_weeks(self, cr, uid, ids, context=None):
        c=calendar.Calendar(0)
        for y in self.browse(cr, uid, ids):
            months=range(1,13)
            for m in months:
                a=[x for x in c.monthdatescalendar(y.y, m)]
                for w in a:
                    start=w[0]
                    stop=w[-1]
                    yy,wk,isoday=start.isocalendar()
                    val={'year_id':y.id,
                         'date_start':start,
                         'date_stop':stop,
                         'wk':wk}
                    self.pool.get("analysis.week.forecast").create(cr,uid,val)
    def setup_months(self, cr, uid, ids, context=None):
        for y in self.browse(cr, uid, ids):
            period_ids=self.pool.get("account.period").search(cr,uid,[('fiscalyear_id.code','=', str(y.y)), ('special','=',False) ])
            for p_id in self.pool.get("account.period").browse(cr,uid, period_ids):
                code=p_id.code
                assert '/' in code
                m,yy=code.split('/')
                val={'year_id':y.id,
                     'month':int(m),
                     'period_id':p_id.id,
                     'active':True}
                self.pool.get("analysis.month.target").create(cr,uid,val)
            
class analysis_month_target(osv.osv):
    _name = "analysis.month.target"
    _order = "month"
    _columns = {
        'year_id':fields.many2one("analysis.year", "Year"),
        'period_id':fields.many2one("account.period", "Period"),
        'month':fields.integer("Month"),
        'sale_target':fields.integer("Sale Target"),
        "active":fields.boolean("Active"),
        'code':fields.char("Code Stored"),
        'secret_key':fields.text("Secret_Key"),        
        
    }
    _defaults = {
        "active":True,
        }

            
class analysis_tag(osv.osv):
    _name = "analysis.tag"
    _order = "sequence"
    _columns = {
        'name':fields.char("Name", size=3000),
        'parent_id':fields.many2one("analysis.tag", "Parent Tag"),
        'model_id':fields.many2one("ir.model","ModelID"),
        'model':fields.char("Model",size=444),
        'type':fields.selection([('terminal','Terminal'),('formula','Formula')], "Type"),
        'axis':fields.selection([('x','x'),('y','y')],'Axis'),
        'var':fields.char("Var",size=30),
        'res_id':fields.integer("ResID"),
        'label':fields.char("Label",size=30),
        'formula':fields.text("Formula"),
        'sequence':fields.integer("Sequence"),
        'child_ids':fields.one2many("analysis.tag","parent_id","Child ids"),
    }
class analysis_phase(osv.osv):
    _name = "analysis.phase"
    _columns = {
        'name':fields.char("Name", size=444),
        'code':fields.char("Code", size=444),
        'relativedelta':fields.char("RelativeDelta"),
    }

class analysis_value(osv.osv):
    _name = "analysis.value"
    _log_access = False
    def _calc(self, cr, uid, ids,field_name,arg, context=None):
        res={}

        for r in self.browse(cr, uid, ids):
            val={'value_calc': r.value }
            res[r.id] = val
        return res
    _columns = {
        
        'phase_id':fields.many2one("analysis.phase", "Phase"),
        'date_id':fields.many2one("analysis.date", "Date"),
        'tag_id':fields.many2one("analysis.tag", "Tag"),
        'model':fields.char("Model", size=444),
        'res_id':fields.integer("ResID"),
        'value':fields.float("Value"),
        'value_calc':fields.function(_calc, type='float', multi='calc',method=True,string='Value Calc'),
        
        #'mkdir':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='mkdir'),
    }

class analysis_header(osv.osv):
    _name = "analysis.header"
    _log_access = False
    _columns = {
        'tag_ids':fields.many2many('analysis.tag', 'tag_header_tag_rel', 'header_id', 'tag_id', 'Tags'),
        'name':fields.char('Name', size=30),
    }

class analysis_table(osv.osv):
    _name = "analysis.table"
    _log_access = False
    _columns = {
        'header_id':fields.many2one('analysis.header', 'Header'),
        'start':fields.many2one('analysis.date', 'Start'),
        'delta':fields.char("delta", size=555),
        }


class analysis_sales_monthly(osv.osv):
    _name="analysis.sales.monthly"
    _log_access = False
    _columns = {
        #'shop_id':fields.many2one('sale.shop','Shop'),
        'categ_id':fields.many2one('product.category','Category'),
        'parent_id':fields.related('category_id', 'parent_id', string='Parent',type="many2one",relation='product.category'),
        'year_id':fields.many2one('account.fiscalyear','Year'),
        '01':fields.float("01"),
        '02':fields.float("02"),
        '03':fields.float("03"),
        '04':fields.float("04"),
        '05':fields.float("05"),
        '06':fields.float("06"),
        '07':fields.float("07"),
        '08':fields.float("08"),
        '09':fields.float("09"),
        '10':fields.float("10"),
        '11':fields.float("11"),
        '12':fields.float("12"),
        }

class analysis_wizard(osv.osv_memory):
    _name = 'analysis.wizard'
    _description="Analysis Wizard"
    _columns ={
        'name':fields.char('Name', size=444),
        'fiscal_year':fields.many2one('account.fiscalyear','Fiscal Year (Ignored now)', required=True),
        }
    def button_run_analysis(self,cr, uid, ids, *a, **kw):
        asa = self.browse(cr, uid, ids[0])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'generic_analysis_webkit',
            #'context':{'fiscal_year':'2015'},
            'context':{'fiscal_year':asa.fiscal_year.code},
#            'datas': {'fiscal_year':asa.fiscal_year.code},
        }
analysis_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
#SuperJack and InferJoe
#SuperJack makes Bread     2x fast than InferJoe
#SuperJack makes Garments  3x fast than InferJoe

#In 2 hours
#InferJoe:  1B,1G
#SuperJack: 2B,3G
#Total 3B, 4G

#OR
#InferJoe:  0B,2G
#SuperJack: 2B,3G
#Total 2B, 5G

