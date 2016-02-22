import datetime
import calendar


def period2dates(p, m, y):
    c=calendar.Calendar(0)
    #m,y=p.code.split('/')
    #if isinstance(y,str):
    y=int(y)
    #if isinstance(m, str):
    m=int(m)
    out=[]
    print [m,y]
    for week in c.monthdatescalendar(y,m):
        for day in week:
            if day.year==y and day.month==m:
                out.append( (p,day) )#print day.isocalendar()
    return out

def setup_dates(pool, cr, uid, fy, start=0):
    period_ids = pool.get('account.period').search(cr, uid, [('fiscalyear_id.code','in',fy), ('special','=',False)] )
    ids = reversed(period_ids)
    days=[]
    for p in pool.get('account.period').browse(cr, uid, [x for x in ids] ):
        period_code=p.code
        m,y=period_code.split('/')
        print [m,y]
        days += period2dates(p,m,y)

    #print DEFAULT_SERVER_DATE_FORMAT
    date_ids = pool.get('analysis.date').search(cr, uid, [('y','in', map(int,fy) )] )
    if date_ids:
        print 'Dates already created'
        days = []
    for i,(p,day) in enumerate(days):
        #isoday=day.isoweekday()
        sequence = start + i
        yy,wk,isoday=day.isocalendar()
        val={'sequence':sequence,
             'date': day,
             'd': day.day,
             'm': day.month,
             'y': day.year,
             'wk': wk,
             'weekend': isoday in [5,6],
             'isoday': isoday,
             'period_id':p.id,
             'period_code': p.code,
             }
        #print val
        ret=pool.get('analysis.date').create(cr, uid, val)
    #print len(days)

def to_ascii(a):
    if a is None:
        return ''
    out=''
    for x in a:
        if ord(x)<=128:
            out+=x
    return out

def write_count_map(pool, cr, uid, tag, count_map):
    tag_ids=pool.get('analysis.tag').search(cr, uid, [('name','=', tag)])
    if not tag_ids:
        tag_id = pool.get('analysis.tag').create(cr, uid, {'name':tag} )
    else:
        tag_id=tag_ids[0]
        assert len(tag_ids)==1
    for d, v in count_map.items():
        date_ids=pool.get('analysis.date').search(cr, uid, [('date','=', d)] )
        date_id=date_ids[0]
        assert len(date_ids)==1

        val_ids=pool.get('analysis.value').search(cr, uid, [('tag_id','=',tag_id),
                                                           ('date_id','=', date_id),
                                                           ])
        if val_ids:
            pool.get('analysis.value').write(cr,uid, val_ids, {'value':len(v)})
        else:
            val={'tag_id':tag_id,
                 'date_id':date_id,
                 'value': len(v),
             }
            pool.get('analysis.value').create(cr, uid, val) 

def analyse_so(pool, cr, uid, shop_id, tag):
    cr.execute("select id from sale_order where shop_id=%s and state not in ('cancel','draft') and date_order between '2014-01-01' and '2015-12-31'", (shop_id,) )
    sale_ids = [so[0] for so in cr.fetchall()]
    so_map={}
    for so in pool.get('sale.order').browse(cr, uid, sale_ids):
        v=so_map.setdefault(so.date_order, [])
        v.append(so.id)
    write_count_map(pool, cr, uid, tag, so_map)

def analyse_phonecalls(pool, cr, uid, categ_id, tag):
    cr.execute("select id from crm_phonecall where categ_id=%s", (categ_id,) )
    call_ids = [so[0] for so in cr.fetchall()]
    call_map={}
    for call in pool.get('crm.phonecall').browse(cr, uid, call_ids):
        dt = datetime.datetime.strptime(call.date, DEFAULT_SERVER_DATETIME_FORMAT)
        v=call_map.setdefault(dt.date(), [])
        v.append(call.id)
    write_count_map(pool, cr, uid, tag, call_map)

class ValueCalc(dict):
    def __init__(self, d=None, data_map=None):
        if d:
            dict.__init__(self, d)
        self._child_map = None
        self._value_map= {}
        self._data_map = data_map
    def _build_child_map(self):
        _child_map = {}
        for _id, row in self.items():
            parent_id=self.get(_id)
            v = _child_map.setdefault(parent_id, [])
            v.append(_id)
        self._child_map = _child_map
    def calc_val(self, tag_id, phase_id, date_id):
        if (tag_id, phase_id, date_id) in self._value_map:
            return self._value_map[(tag_id, phase_id, date_id)]
        else:
            val=self._data_map.get((tag_id,phase_id,date_id), 0.0)
            if not self._child_map:
                self._build_child_map()
            children=self._child_map.get(tag_id, [])
            for ch in children:
                val+=self.calc_val( ch, phase_id, date_id)
            #print children
            self._value_map[ (tag_id, phase_id, date_id ) ]=val #remember calc value
            return val
    def traverse_preorder(self, phase_id,date_id, test_id=None, depth=0):
        if not self._child_map:
            self._build_child_map()
        if test_id:
            yield test_id, depth, 
            children = self._child_map.get(test_id, [])
            for ch in sorted(children, key=lambda x:self.calc_val(x,phase_id,date_id), reverse=True):
                ret=[]
                for tt, dd in self.traverse_preorder(phase_id, date_id, ch, depth + 1):
                    val=self.calc_val(tt, phase_id, date_id)
                    ret.append( (val, tt, dd) )
                    #yield tt, dd
                ret_sorted=sorted(ret, key=lambda a:a[0], reverse=True )
                for val, tt, dd in ret:
                    yield tt, dd
        else:
            roots = [t for t,p in self.items() if not p ]
            for root in roots:
                for tt, dd in self.traverse_preorder(phase_id, date_id, root, depth):
                    yield tt, dd

class ValueCalcShopCateg(dict):
    def __init__(self, d, data_map_year, data_map_month):
        if d:
            dict.__init__(self, d)
        self._child_map = None
        self._data_map_year = data_map_year
        self._data_map_month = data_map_month
        self._value_map_year={}
        self._value_map_month={}
    def _build_child_map(self):
        _child_map = {}
        for _id, row in self.items():
            parent_id=self.get(_id)
            v = _child_map.setdefault(parent_id, [])
            v.append(_id)
        self._child_map = _child_map
    def calc_val(self, categ_id, shop_id, month=None):
        if not self._child_map:
            self._build_child_map()

        if month:
            if (categ_id, shop_id, month) in self._value_map_month:
                return self._value_map_month[ (categ_id, shop_id, month) ]
            else:
                val=self._data_map_month.get((shop_id, categ_id, month), 0.0)
                children=self._child_map.get(categ_id, [])
                for ch in children:
                    val+=self.calc_val( ch, shop_id, month=month)
                self._value_map_month[ (categ_id, shop_id,month ) ]=val #remember calc value    
                return val
        else:
            if (categ_id, shop_id) in self._value_map_year:
                return self._value_map_year[(categ_id, shop_id)]
            else:
                val=self._data_map_year.get((shop_id, categ_id), 0.0)

                children=self._child_map.get(categ_id, [])
                for ch in children:
                    val+=self.calc_val( ch, shop_id)
                self._value_map_year[ (categ_id, shop_id ) ]=val #remember calc value
                return val

    def traverse_preorder(self, shop_id,categ_id=None, depth=0):
        if not self._child_map:
            self._build_child_map()
        if categ_id:
            yield categ_id, depth, 
            children = self._child_map.get(categ_id, [])
            for ch in sorted(children, key=lambda x:self.calc_val(x,shop_id), reverse=True):
                ret=[]
                for tt, dd in self.traverse_preorder(shop_id, ch, depth + 1):
                    val=self.calc_val(tt, shop_id)
                    ret.append( (val, tt, dd) )
                    #yield tt, dd
                #ret_sorted=sorted(ret, key=lambda a:a[0], reverse=True )
                for val, tt, dd in ret:
                    yield tt, dd
        else:
            roots = [t for t,p in self.items() if not p ]
            for root in roots:
                for tt, dd in self.traverse_preorder(shop_id, root, depth):
                    yield tt, dd



class ValueCalcDelivery(dict):
    def __init__(self, d, data_map_year, data_map_month):
        if d:
            dict.__init__(self, d)
        self._child_map = None
        self._data_map_year = data_map_year
        self._data_map_month = data_map_month
        self._value_map_year={}
        self._value_map_month={}
    def _build_child_map(self):
        _child_map = {}
        for _id, row in self.items():
            parent_id=self.get(_id)
            v = _child_map.setdefault(parent_id, [])
            v.append(_id)
        self._child_map = _child_map
    def calc_val(self, node_id, month=None):
        if not self._child_map:
            self._build_child_map()

        if month:
            if (node_id, month) in self._value_map_month:
                return self._value_map_month[ (node_id, month) ]
            else:
                val=self._data_map_month.get((node_id, month), 0.0)
                children=self._child_map.get(node_id, [])
                for ch in children:
                    val+=self.calc_val( ch, month=month)
                self._value_map_month[ (node_id, month ) ]=val #remember calc value    
                return val
        else:
            if node_id in self._value_map_year:
                return self._value_map_year[node_id]
            else:
                val=self._data_map_year.get(node_id, 0.0)

                children=self._child_map.get(node_id, [])
                for ch in children:
                    val+=self.calc_val( ch)
                self._value_map_year[ node_id ]=val #remember calc value
                return val

    def traverse_preorder(self,node_id=None, depth=0):
        if not self._child_map:
            self._build_child_map()
        #print self._child_map
        if node_id:
            yield node_id, depth, 
            children = self._child_map.get(node_id, [])
            for ch in sorted(children, key=lambda x:self.calc_val(x), reverse=True):
                #ret=[]
                for tt, dd in self.traverse_preorder(ch, depth + 1):
                    val=self.calc_val(tt)
                    #ret.append( (val, tt, dd) )
                    yield tt, dd
                #ret_sorted=sorted(ret, key=lambda a:a[0], reverse=True )
                #for val, tt, dd in ret:
                #    yield tt, dd
        else:
            roots=[]
            #for node_id,parent_node_id in self.items():
            #    print node_id, parent_node_id
            roots = [ (1,None) ]
            #roots = [t for t,p in self.items() if not p==(None,None) ]
            #print roots
            for root in roots:
                for tt, dd in self.traverse_preorder(root, depth):
                    yield tt, dd

class TraversePreorder(dict):
    def __init__(self, d=None, parent_field='parent_id'):
        if d:
            dict.__init__(self, d)
        self._child_map = None
        self._parent_field = parent_field
    def _build_child_map(self):
        _child_map = {}
        for _id, row in self.items():
            parent_id = row[self._parent_field]
            v = _child_map.setdefault(parent_id, [])
            v.append(_id)
        self._child_map = _child_map
    def traverse_preorder(self, test_id=None, depth=0):
        if not self._child_map:
            self._build_child_map()
        if test_id:
            yield test_id, depth
            children = self._child_map.get(test_id, [])
            for ch in children:
                for tt, dd in self.traverse_preorder(ch, depth + 1):
                    yield tt, dd
        else:
            roots = [t for t in self.keys() if not self[t][self._parent_field] ]
            for root in roots:
                for tt, dd in self.traverse_preorder(root, depth):
                    yield tt, dd

def traverse_preorder(records, parent_field = 'parent_id', key_field='id'):
    recs2_map = dict( [(x[key_field],x) for x in records] )
    tp=TraversePreorder(d=recs2_map, parent_field=parent_field)
    out=tp.traverse_preorder()
    #print [x for x in out]
    ret= [ (recs2_map[tt],dd) for tt,dd in out ]
#    print ret
    #print [x for x in tp.traverse_preorder()]
    #print len(ret)
    return ret

def analyse_sales(pool, cr, uid):
    data_map={}
    invoice_ids = pool.get('account.invoice').search(cr, uid, [('type','in',['out_invoice','out_refund']), ('state','in',['paid','open'])] )

    for inv in pool.get('account.invoice').browse(cr, uid, invoice_ids):
        Y,m,d=inv.date_invoice.split('-')
        if inv.shop_id:
            shop_id=inv.shop_id.id

            for l in inv.invoice_line:

                if l.product_id.categ_id:
                    categ_id=l.product_id.categ_id.id
                else:
                    continue
                    categ_id=False
                
                v = data_map.setdefault( (Y, shop_id, categ_id) , {} )
                price = l.price_unit * l.quantity * (100-l.discount)/100.0
                if not inv.fiscal_position:
                    price = price / 1.2
                if inv.type=='out_invoice':
                    pass                        
                elif inv.type=='out_refund':
                    price = (-1)* price
                
                vv = v.setdefault( m, [] )
                vv.append( price )
                
    monthly_sum = {}
    cr.execute("select code,id from account_fiscalyear")
    year_map = dict( [x for x in cr.fetchall()] )
    for key,v in data_map.items():
        Y, shop_id, categ_id = key
        val = {}
        for k,prices in v.items():
            val[k]=sum(prices)
        val.update( {'shop_id':shop_id,
                     'categ_id':categ_id,
                     'year_id': year_map[Y],
                     } )
        pool.get('analysis.sales.monthly').create(cr, uid, val) 
    
def analyse_product_sales(pool, cr, uid):
    cr.execute("delete from analysis_tag")
    categ_model_id = pool.get('ir.model').search(cr, uid, [('model','=','product.category')])[0]
    phase_sales_raw_id = pool.get("analysis.phase").create(cr, uid, {'name':'Sales Day Data', 'code':'sales_day'})
    phase_product_sales_raw_id = pool.get("analysis.phase").create(cr, uid, {'name':'Product Sales Delivered - Returned', 'code':'product_sales_day'})
    phase_sales = pool.get("analysis.phase").browse(cr, uid, phase_sales_raw_id)
    phase_product_sales = pool.get("analysis.phase").browse(cr, uid, phase_product_sales_raw_id)


    categ_ids=pool.get('product.category').search(cr, uid, [])
    categs = [{'name':c.name, 'id':c.id, 'parent_id':c.parent_id.id,'categ':c} for c in 
              pool.get('product.category').browse(cr, uid, categ_ids)]
    categs_sorted=traverse_preorder(categs)
    categ_tag_map={}
    count=0
    for categ,dd in categs_sorted:
        categ_id = categ['id']
        parent_id = categ['parent_id']
        c=categ['categ']
        tag_id = pool.get('analysis.tag').create(cr, uid, {'name':categ['name'],
                                                           'parent_id': categ_tag_map.get(parent_id,False),
                                                           'model_id':categ_model_id,
                                                           'model':'product.category',
                                                           'type':'formula',
                                                           'res_id':categ_id,
                                                           'label':'Categ%03d'%count,
                                                           'axis':'y',
                                                           
                                                           'formula':'sum([x.value for x in categ.child_ids])',
                                                           #'sequence':count,
                                                       } )
        categ_tag_map[categ_id]=tag_id
        count+=10
        
    invoice_ids = pool.get('account.invoice').search(cr, uid, [('type','in',['out_invoice','out_refund']), ('state','in',['paid','open'])] )

    shop_tag_map={}
    cr.execute("select id,name from sale_shop")
    shop_map=dict( [x for x in cr.fetchall()] ) 
    for inv in pool.get('account.invoice').browse(cr, uid, invoice_ids):
        #Y,m,d=inv.date_invoice.split('-')
        if inv.shop_id:
            date_ids=pool.get('analysis.date').search(cr, uid, [('date','=', inv.date_invoice)] )
            shop_id=inv.shop_id.id
            shop_name=shop_map[shop_id]
            if len(date_ids)!=1:
                #print date_ids
                #print inv.date_invoice
                assert False
            else:
                date_id=date_ids[0]

            for l in inv.invoice_line:
                if l.product_id.categ_id:
                    categ_id=l.product_id.categ_id.id
                else:
                    continue
                    categ_id=False
                parent_categ_tag_id=categ_tag_map[categ_id]

                tag_id = shop_tag_map.get( (categ_id, shop_id), False) 
                if not tag_id:
                    tag_id = pool.get('analysis.tag').create(cr, uid, {'name':shop_name,
                                                                       'parent_id': parent_categ_tag_id,
                                                                       #'model_id':categ_model_id,
                                                                       'model':'sale.shop',
                                                                       'type':'terminal',
                                                                       'res_id':shop_id,
                                                                       #'label':'Categ%03d'%count,
                                                                       'axis':'y',
                                                                       #'formula':'sum([x.value for x in categ.child_ids])',
                                                                       #'sequence':count,
                                                                   } )
                    shop_tag_map[ (categ_id, shop_id) ] = tag_id

                price = l.price_unit * l.quantity * (100-l.discount)/100.0
                if not inv.fiscal_position:
                    price = price / 1.2
                if inv.type=='out_invoice':
                    pass                        
                elif inv.type=='out_refund':
                    price = (-1)* price
                
                val={'tag_id':tag_id,
                     'date_id':date_id,
                     'value': price,
                     'model':'account.invoice.line',
                     'res_id':l.id,
                     'phase_id':phase_sales.id,
                 }
                pool.get('analysis.value').create(cr, uid, val) 

    picking_ids = pool.get('stock.picking').search(cr, uid, [('state','=','done') ] )
    by_prod={}
    by_prod_in={}
    prod_tag_map={}
            
    for picking in pool.get('stock.picking').browse(cr, uid, picking_ids):
        Y,m,d=picking.date_done.split(' ')[0].split('-')
        date_ids=pool.get('analysis.date').search(cr, uid, [('date','=', picking.date_done)] )
        if len(date_ids)!=1:
            assert False
        else:
            date_id=date_ids[0]
        #print [Y,m,d]
        if 1:#Y==fy:
            for move in picking.move_lines:
                prod_id=move.product_id.id
                categ_id=move.product_id.categ_id.id
                parent_categ_tag_id=categ_tag_map[categ_id]

                if (picking.is_returned):
                    product_qty = (-1)*move.product_qty
                elif picking.type == 'out':
                    product_qty = move.product_qty
                else:
                    product_qty=0
                tag_id = prod_tag_map.get( prod_id, False) 
                if not tag_id:
                    prod_name = "[%s] %s" % (move.product_id.default_code, move.product_id.name)
                    tag_id = pool.get('analysis.tag').create(cr, uid, {'name': prod_name,
                                                                       'parent_id': parent_categ_tag_id,
                                                                       'model':'product.product',
                                                                       'type':'terminal',
                                                                       'res_id':prod_id,
                                                                       #'label':'Categ%03d'%count,
                                                                       'axis':'y',
                                                                       #'formula':'sum([x.value for x in categ.child_ids])',
                                                                       #'sequence':count,
                                                                   } )
                    prod_tag_map[ prod_id ] = tag_id
                
                val={'tag_id':tag_id,
                     'date_id':date_id,
                     'value': product_qty,
                     'model':'stock.move',
                     'res_id':move.id,
                     'phase_id':phase_product_sales.id,
                 }
                pool.get('analysis.value').create(cr, uid, val) 
    tag_ids = pool.get('analysis.tag').search(cr, uid, [])
    tags=[]
    for t in pool.get('analysis.tag').browse(cr, uid, tag_ids):
        if t.parent_id:
            tags.append( {'id':t.id,'parent_id':t.parent_id.id, 'tag':t} )
        else:
            tags.append( {'id':t.id,'parent_id':False, 'tag':t} )

    tags_sorted=traverse_preorder(tags)
    count=0
    for tag,dd in tags_sorted:
        t=tag['tag']
        t.write({'sequence':count})
        count+=10
