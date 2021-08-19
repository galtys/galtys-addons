import datetime
import calendar


def period2dates(pool,cr, uid, p):
    c=calendar.Calendar(0)
    m,y=p.code.split('/')
    y=int(y)
    m=int(m)
    out=[]
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
        days += period2dates(pool, cr, uid, p)
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
        print val
        #ret=pool.get('analysis.date').create(cr, uid, val)
    #print len(days)

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
