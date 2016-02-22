from openerp.osv import fields, osv
from openerp.report import report_sxw

import pjb
from pjb import traverse_preorder, period2dates, ValueCalc, ValueCalcDelivery, ValueCalcShopCateg

def sale_shop_categ_analysis(pool, cr, uid, context):
    fy=context['fiscal_year']
    print 'fiscal year', fy
#    fy='2015'
    cr.execute("select pjb_shop_id,categ_id,sum(price_total) from account_invoice_report where year='%s' group by pjb_shop_id,categ_id;"%fy)
    data_map_year=dict( [ ((pjb_shop_id,categ_id),price) for pjb_shop_id,categ_id,price in cr.fetchall()] )
    cr.execute("select pjb_shop_id,categ_id,month,sum(price_total) from account_invoice_report where year='%s' group by pjb_shop_id,categ_id,month;"%fy)
    data_map_month=dict( [ ((pjb_shop_id,categ_id,month),price) for pjb_shop_id,categ_id,month,price in cr.fetchall()] )

    #cr.execute("select id,name from sale_shop")
    sale_shop_ids=pool.get('sale.shop').search(cr, uid, [])
    sale_shops=pool.get('sale.shop').browse(cr, uid, sale_shop_ids)

    categ_ids=pool.get('product.category').search(cr, uid, [])
    categories = pool.get('product.category').browse(cr, uid, categ_ids )
    categ_map=dict( [(c.id,c) for c in categories] )

    cr.execute("select id,parent_id from product_category")
    categ_parent_map=[(c_id,parent_id) for c_id,parent_id in cr.fetchall()]
    vc=ValueCalcShopCateg(categ_parent_map, data_map_year, data_map_month)
    tables=[]
    header_cols = ["%02d"%x for x in range(1,13)]
    header = [''] + header_cols + [fy]
    all_products_categ_id = 1
    for shop in sorted(sale_shops, key=lambda s:vc.calc_val(all_products_categ_id,s.id), reverse=True):
        shop_id=shop.id
        table=[]
        categ_ids=vc.traverse_preorder(shop.id)
        for categ_id,dd in categ_ids:
            row=[]
            for month in header_cols:
                val=vc.calc_val( categ_id, shop_id, month=month)
                row.append(val)
            val=vc.calc_val( categ_id, shop_id)
            row.append( val )
            if val>0.0:
                table.append( (categ_map[categ_id], dd, row) )
        #print [x for x in categ_ids]
        tables.append( (shop, table) )
    ctx={#'header': header, 
         'tables' : tables,
         #'to_ascii':to_ascii,
         #'title': "Sales Analysis: By Shop, By Category",
    }
    return ctx

def prod_categ_delivery_analysis(pool, cr, uid, context):
    fy=context['fiscal_year']
    #print ['fiscal year', fy]
    #cr.execute("select pjb_shop_id,categ_id,sum(price_total) from account_invoice_report where year='2015' group by pjb_shop_id,categ_id;")
    cr.execute("select categ_id,product_id,sum(product_qty_delivered_less_returned) from report_stock_move_pjb where year='%s' and state='done' group by product_id,categ_id"%fy)
    data_year=[x for x in cr.fetchall()]
    data_map_year=dict( [ ((None, product_id),qty_delivered) for categ_id,product_id,qty_delivered in data_year] )

    parent_map={}
    for categ_id,product_id,qty_delivered in data_year:
        parent_map[ (None,product_id) ] = (categ_id, None)

    cr.execute("select categ_id,product_id,month,sum(product_qty_delivered_less_returned) from report_stock_move_pjb where year='%s' and state='done' group by product_id,categ_id,month;"%fy)
    data_month=[x for x in cr.fetchall()]
    data_map_month=dict( [ (( (None, product_id),month),price) for categ_id,product_id,month,price in data_month] )

#    cr.execute("
    #cr.execute("select id,name from sale_shop")
 
    categ_ids=pool.get('product.category').search(cr, uid, [])
    categories = pool.get('product.category').browse(cr, uid, categ_ids )
    categ_map=dict( [(c.id,c) for c in categories] )

    product_ids=pool.get('product.product').search(cr, uid, [])
    products = pool.get('product.product').browse(cr, uid, product_ids )
    prod_map=dict( [(p.id,p) for p in products] )

    cr.execute("select id,parent_id from product_category")
    for categ_id, parent_id in cr.fetchall():
        parent_map[ (categ_id,None) ] = (parent_id, None)
    #categ_parent_map=[(c_id,parent_id) for c_id,parent_id in cr.fetchall()]

    vc=ValueCalcDelivery(parent_map, data_map_year, data_map_month)
    tables=[]
    header_cols = ["%02d"%x for x in range(1,13)]
    header = [''] + header_cols + [fy]
    all_products_categ_id = 1
    
    #print vc.calc_val( (all_products_categ_id, None), month='03' )
    #return {}

    node_ids=vc.traverse_preorder()
    #print [x for x in node_ids]
    table=[]
    for node_id,dd in node_ids:
        row=[]
        for month in header_cols:
            val=vc.calc_val( node_id, month=month)
            row.append(val)

        val=vc.calc_val(node_id)
        row.append( val )
        categ_id,product_id = node_id
        categ=categ_map.get(categ_id)
        prod=prod_map.get(product_id)
        if val>0.0:
            table.append( (categ_id,product_id,categ,prod, dd, row) )

    ctx={'delivery_header': header, 
         'delivery_table' : table,
         #'to_ascii':to_ascii,
         #'title': "Sales Analysis: By Shop, By Category",
    }
    return ctx

def product_sale_analysis(pool, cr, uid, context):
        fy=context['fiscal_year']

        phase_product_sale_year_id=pool.get("analysis.phase").search(cr, uid, [('code','=','product_sales_year')]) [0]
        phase_product_sale_month_id=pool.get("analysis.phase").search(cr, uid, [('code','=','product_sales_month')]) [0]

        data_ids = pool.get("analysis.value").search(cr, uid, [('phase_id.code','in',['product_sales_year'])] )
        data = pool.get("analysis.value").browse(cr, uid, data_ids)
        header_year=[]
        for d in data:
            if d.date_id not in header_year:
                header_year.append( d.date_id )

        data_ids = pool.get("analysis.value").search(cr, uid, [('phase_id.code','in',['product_sales_month'])] )
        data = pool.get("analysis.value").browse(cr, uid, data_ids)
        data_map = {}
        data_map2= {}
        header_tags=[]
        header_dates=[]
        for d in data:            
            if d.tag_id not in header_tags:
                header_tags.append( d.tag_id )
            if d.date_id not in header_dates:
                header_dates.append( d.date_id )
        header_dates = sorted( header_dates, key=lambda a:a.m) 

        all_tag_ids = pool.get('analysis.tag').search(cr, uid, [('model','in',['product.category','product.product'] ) ])
        used_tag_ids = [t.id for t in header_tags]
        tag_ids=[]
        for tag_id in all_tag_ids:
            if tag_id in used_tag_ids:
                tag_ids.append( tag_id )
        tag_ids = all_tag_ids
        tags=[]
        for t in pool.get('analysis.tag').browse(cr, uid, tag_ids):
            if t.parent_id:
                tags.append( {'id':t.id,'parent_id':t.parent_id.id, 'tag':t} )
            else:
                tags.append( {'id':t.id,'parent_id':False, 'tag':t} )
        
        cr.execute("select id,parent_id from analysis_tag")
        tag_parent_map=dict( [(tag_id,parent_tag_id) for tag_id,parent_tag_id in cr.fetchall()] )

        cr.execute("select av.tag_id,av.phase_id,av.date_id,av.value from analysis_value av, analysis_tag at where av.tag_id=at.id")
        value_map=dict( [( (tag_id,phase_id,date_id), value ) for tag_id,phase_id,date_id,value in cr.fetchall()] )

        tc = ValueCalc( tag_parent_map, value_map )
        
        tags_sorted=traverse_preorder(tags)
        table=[]
        for tagrec,dd in tags_sorted:
            #dd=0
            t_id=tagrec['tag'].id
            t_name=tagrec['tag'].name
            t=tagrec['tag']
            row=[]
            for h in header_dates:
                key=(t,h)
                tag_id=t.id
                phase_id=phase_product_sale_month_id
                date_id=h.id
                value=tc.calc_val( tag_id, phase_id, date_id )
                row.append( value )
            for h in header_year:
                key=(t,h)
                tag_id=t.id
                phase_id=phase_product_sale_year_id
                date_year_id=h.id
                value=tc.calc_val( tag_id, phase_id, date_year_id ) / 2.0
                row.append( value )
            #print row, t, data_map2
            if sum(row)>0.01 or t.type=='formula':
                table.append( ( t,dd, row) )
        value_sorted=tc.traverse_preorder(phase_product_sale_year_id, date_year_id)
        value_sorted=[ (tt,dd) for tt,dd in value_sorted]
        value_sorted_map = dict(value_sorted)
        value_sorted_ids =  [ tt for tt,dd in value_sorted]

        tags=[]
        for t in pool.get('analysis.tag').browse(cr, uid, value_sorted_ids):
            if t.parent_id:
                tags.append( {'id':t.id,'parent_id':t.parent_id.id, 'tag':t} )
            else:
                tags.append( {'id':t.id,'parent_id':False, 'tag':t} )

        table=[]
        for tagrec in tags:
            t_id=tagrec['tag'].id
            dd = value_sorted_map[t_id]
            t_name=tagrec['tag'].name
            t=tagrec['tag']
            row=[]
            for h in header_dates:
                key=(t,h)
                tag_id=t.id
                phase_id=phase_product_sale_month_id
                date_id=h.id
                value=tc.calc_val( tag_id, phase_id, date_id )
                row.append( value )
            for h in header_year:
                key=(t,h)
                tag_id=t.id
                phase_id=phase_product_sale_year_id
                date_year_id=h.id
                value=tc.calc_val( tag_id, phase_id, date_year_id ) / 2.0
                row.append( value )
            #print row, t, data_map2
            if sum(row)>0.01 or t.type=='formula':
                table.append( ( t,dd, row) )
        ctx={'header': [''] + [h.m for h in header_dates]+[h.y for h in header_year], 
             'rows' : table,
             'to_ascii': pjb.to_ascii,
             'title': "Sale Analysis: Products Delivered - Returned By Category",
         }
        return ctx
    
class analysis_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(analysis_report, self).__init__(cr, uid, name, context=context)

        pool=self.pool

        ctx = product_sale_analysis(pool, cr, uid, context)
        self.localcontext.update(ctx)

        ctx = sale_shop_categ_analysis(pool, cr, uid, context)
        self.localcontext.update(ctx)

        ctx = prod_categ_delivery_analysis(pool, cr, uid, context)
        self.localcontext.update(ctx)

report_sxw.report_sxw('report.generic_analysis_webkit',
                      'analysis.value',
                      'report/analysis.mako',
                      parser=analysis_report)
