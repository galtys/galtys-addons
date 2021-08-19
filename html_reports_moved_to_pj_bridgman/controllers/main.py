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
from openerp import pooler

import werkzeug.utils
import werkzeug.wrappers

import openerp
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
import datetime
import calendar
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

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

def get_image_url(req, name):
    return req.httprequest.url_root + 'get_image'+'?image=%s'%name

def get_query_url(req, q,dbname):
    return req.httprequest.url_root + 'sql_query'+'?query_id=%s&db=%s'%(q.id,dbname)

def get_query_list_url(req, dbname):
    return req.httprequest.url_root + 'sql_query_list'+'?db=%s'%dbname

class web_sql_query_list(oeweb.Controller):
    _cp_path = "/sql_query"
    
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

class html_reports_images(oeweb.Controller):
    _cp_path = "/get_image"
    @oeweb.httprequest
    def index(self, req, s_action=None, data=None, **kw):
        image=kw['image']
        #if 'db' in kw:
        #    dbname=kw['db']
        #else:
        #    dbname='pjb_live'
        #
        #print '/get_image', image
        #uid=1
        #registry = openerp.modules.registry.Registry(dbname)
        #with registry.cursor() as cr:
        #    pool = pooler.get_pool(dbname)
        #    img_content = pool.get('analysis.chart').generate_chart(cr, uid, int(image) )
        image_file=get_module_resource('galtys_analysis', '', image+'.png')
        print 'image_file', image_file
        img_content=file(image_file).read()
        return Response(img_content, mimetype='image/png')

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
        assert len(chart_ids)==1
        #if len(chart_ids)==1:
        chart_id = chart_ids[0]
        image=self.pool.get('analysis.chart').browse(self.cr, self.uid, chart_id)
        return image
        #return None

    def render(self, ref):
        #ret='<img src="1.png" alt="IMAGE NOT FOUND"/>'
        image=self.get(ref)
        #if image:
        self.pool.get('analysis.chart').generate_chart(self.cr, self.uid, image.id)
        #image=self.pool.get('analysis.chart').browse(self.cr, self.uid, image.id)
        image_url=get_image_url(self.req,'%d'%image.id )
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
            #self.pool.get('analysis.chart').generate_chart(self.cr, self.uid, query.id)
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
            #cr.commit()
            #cr.close()
        return Response(html_ret, mimetype='text/html')


# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:



