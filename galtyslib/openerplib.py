import os
import csv
import psycopg2
import sys
import pickle
import time
import base64

try:
    import openerp
    #import openerp.tools.config
    import openerp.service.web_services
except ImportError:
    pass

def create_empty_db(dbname):
    DB=dbname
    db=openerp.service.web_services.db(DB)
    #data = db.exp_dump('amdemo_template')
    db_id=db.exp_create(DB, False, 'en_GB','admin')
    done=False
    while not done:
        complete, info = db.exp_get_progress(db_id)
        time.sleep(2)
        if complete == 1.0:
            done=True
def copy_db(dbname1, dbname2):
    db1=openerp.service.web_services.db(dbname1)
    data = db1.exp_dump(dbname1)
    db2=openerp.service.web_services.db(dbname2)
    #db2._create_empty_database(dbname2)
    return db2.exp_restore(dbname2, data)
def drop_db(dbname):
    db1=openerp.service.web_services.db(dbname)
    return db1.exp_drop(dbname)
    
def install_modules(obj_pool, cr, uid,  modules):
    user_obj = obj_pool.get('res.users')
    module_obj = obj_pool.get('ir.module.module')
    mod_upgrade_obj = obj_pool.get('base.module.upgrade')
    
    install_ids = module_obj.search(cr, uid, [('name','in',modules) ] )
    
    ret=module_obj.button_install(cr, uid, install_ids)
    ids = mod_upgrade_obj.get_module_list(cr, uid)
    ret=  mod_upgrade_obj.upgrade_module(cr, uid, ids)
    return ret

def get_connection(dbname):
    DB=dbname
    obj_pool=openerp.pooler.get_pool(DB)
    pool=openerp.sql_db.ConnectionPool()
    cr = openerp.sql_db.Cursor(pool,DB)
    uid=1
    return obj_pool, cr, uid

def pickle_fn(dbname):
    return '%s.pickle'%dbname

def save_ns(dbname, ns):
    fp=file( pickle_fn(dbname), 'wb')
    #ns = (product_map, product_map_inv)
    pickle.dump( ns, fp)
    fp.close()
    return ns
def drop_ns(dbname):
    os.unlink( pickle_fn(dbname) )

def load_ns(dbname):
    if os.path.isfile( pickle_fn(dbname) ):
        fp=file('%s.pickle'%dbname)
        ns = pickle.load(fp)
        fp.close()
        return ns
    else:
        return False

def create_and_init_db(dbname, modules=None):


    create_empty_db(dbname)
    obj_pool, cr, uid = get_connection(dbname)
    if modules:
        ret = install_modules(obj_pool, cr, uid, modules)
    cr.commit()
    cr.close()

    return ret

def db_exist(c, dbname):
    import psycopg2
    import psycopg2.extras
    conn_string = "host='%s' dbname='%s' port='%s' user='%s' password='%s'" % (c['db_host'],dbname,c['db_port'], c['db_user'],c['db_password'] )
    try:
        conn = psycopg2.connect(conn_string)
        conn.commit()
        return True
    except psycopg2.OperationalError:
        return False
def load_csv(fn):
    fp=open(os.path.join(fn))
    data=[x for x in csv.DictReader(fp)]
    fp.close()
    return data
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
            #if parent_id:
            #    parent_id=parent_id[0]
            v = _child_map.setdefault(parent_id, [])
            v.append(_id)
        #print 50*'*'
        #print _child_map
        self._child_map = _child_map
    def traverse_preorder(self, test_id=None, depth=0):

        if not self._child_map:
            self._build_child_map()
        if test_id:
            yield test_id, depth
            children = self._child_map.get(test_id, [])
            #key=lambda x:(self[x].get('name',0), x)
            #children.sort(key=key)
            
            for ch in children:
                for tt, dd in self.traverse_preorder(ch, depth + 1):
                    yield tt, dd
        else:
            roots = [t for t in self.keys() if not self[t][self._parent_field] ]
            #roots.sort(key=lambda x:(self[x].get('sort_order',0), x))
            #print 'roots',roots,   [self[t][self._parent_field] for t in self.keys() ]
            #  nt roots,len(roots)
            for root in roots:
                for tt, dd in self.traverse_preorder(root, depth):
                    yield tt, dd

def traverse_preorder(records, parent_field = 'parent_id', key_field='id'):
    recs2_map = dict( [(x[key_field],x) for x in records] )
    tp=TraversePreorder(d=recs2_map, parent_field=parent_field)
    ret= [ recs2_map[tt] for tt,dd in tp.traverse_preorder() ]
    #print [x for x in tp.traverse_preorder()]
    #print len(ret)
    return ret


def f64(header, data, fields64):
    out=[]
    for row in data:
        for f64 in fields64:
            i=header.index(f64)
            fn=row[i]
            if os.path.isfile(fn):
                row[i] = base64.encodestring(file(fn).read())
            else:
                try:
                    bin=base64.decodestring(fn)
                    row[i]=fn
                except:
                    pass
    return data

def load_data(pool, cr, uid, fn, model):
    lines = [x for x in csv.reader( file(fn).readlines() )]
    header = lines[0]
    data=lines[1:]
    fields = pool.get(model).fields_get(cr, uid)
    binary_fields = [f for f in fields if fields[f]['type']=='binary']
    fields64 = list( set(binary_fields).intersection( set(header) ) )
    return pool.get(model).load(cr, uid, header, f64(header, data, fields64) )
def export_data(pool, cr, uid, model, fn):
    fields = pool.get(model).fields_get(cr, uid)
    ids = pool.get(model).search(cr, uid, [])
    #header = ['id']
    header=[]
    header_export=['id']
    for f, v in fields.items():
        if 'function' not in v:
            if v['type']=='many2one':
                header_export.append( "%s/id" % f )
                header.append(f)
            elif v['type']=='one2many':
                pass
            else:
                header.append(f)
                header_export.append(f)
    header_types = [fields[x]['type'] for x in header]
    data = pool.get(model).export_data(cr, uid, ids,  header_export)
    out=[]
    #print header_export
    #print header
    #print header_types
    for row in data['datas']:
        out_row=[row[0]]
        for i,h in enumerate(header):
            v=row[i+1]
            t=header_types[i]
            if (v is False) and (t != 'boolean'):
                out_row.append('')
            else:
                out_row.append(v.encode('utf8'))
        #print out_row
        out.append(out_row)
    import csv
    fp = open(fn, 'wb')
    csv_writer=csv.writer(fp)
    csv_writer.writerows( [header_export] )
    csv_writer.writerows( out )
    fp.close()
    return out


def generate_accounts_from_template_byname(obj_pool, cr, uid, name='l10n_uk_corrected.l10n_uk_corrected'):
    wizard_obj = obj_pool.get('wizard.multi.charts.accounts')
    install_obj = obj_pool.get('account.installer')
    bank_wizard_obj = obj_pool.get('account.bank.accounts.wizard')

    #header = ['date_start', 'date_stop', 'period','company_id/id']
    #data_row = [time.strftime('%Y-01-01'), time.strftime('%Y-12-31'), 'month', 'base.main_company']
    
    #ret = install_obj.load(cr, uid, header, [data_row] )
    #ids = ret['ids']
    #if ids:
    #    install_obj.execute(cr, uid, ids)

    header = ['company_id/id','code_digits', 'sale_tax/id','purchase_tax/id','sale_tax_rate','purchase_tax_rate','currency_id', 'chart_template_id/id']
    row = ['base.main_company', 2, 'l10n_uk_corrected.ST11','l10n_uk_corrected.PT11', 0.2, 0.2, 'GBP', name]

    ret = wizard_obj.load(cr, uid, header, [row] )
    print ret
    ids = ret['ids']
    if ids:
        wizard_obj.execute(cr, uid, ids)
    return
def generate_periods(pool, cr, uid):
    install_obj = pool.get('account.installer')
    header = ['date_start', 'date_stop', 'period','company_id/id']
    data_row = [time.strftime('%Y-01-01'), time.strftime('%Y-12-31'), 'month', 'base.main_company']
    
    ret = install_obj.load(cr, uid, header, [data_row] )
    ids = ret['ids']
    if ids:
        install_obj.execute(cr, uid, ids)
    return

def generate_accounts_from_template(obj_pool, cr, uid):
    wizard_obj = obj_pool.get('wizard.multi.charts.accounts')
    install_obj = obj_pool.get('account.installer')
    bank_wizard_obj = obj_pool.get('account.bank.accounts.wizard')

    header = ['date_start', 'date_stop', 'period','company_id/id']
    data_row = [time.strftime('%Y-01-01'), time.strftime('%Y-12-31'), 'month', 'base.main_company']
    
    ret = install_obj.load(cr, uid, header, [data_row] )
    ids = ret['ids']
    if ids:
        install_obj.execute(cr, uid, ids)

    header = ['company_id/id','code_digits', 'sale_tax/id','purchase_tax/id','sale_tax_rate','purchase_tax_rate','currency_id', 'chart_template_id/id']
    row = ['base.main_company', 2, 'l10n_uk.ST11','l10n_uk.PT11', 0.2, 0.2, 'GBP', 'l10n_uk.l10n_uk']

    ret = wizard_obj.load(cr, uid, header, [row] )
    ids = ret['ids']
    if ids:
        wizard_obj.execute(cr, uid, ids)
    return
def set_product_pricelist(pool, cr, uid):
    header = ['id', 'currency_id']
    row = ['product.list0', 'GBP']
    ret = pool.get('product.pricelist').load(cr, uid, header, [row] )
    return


def list_models(obj_pool, cr, uid, model_ids):
    ir_model_obj=obj_pool.get('ir.model')
    #model_ids = ir_model_obj.search(cr, uid, [])
    #field_attrs=[]
    import HTML
    def get_row(header, data_map):
        out=[]
        for h in header:
            if h in ['selection','help']:
                out.append('')
            else:
                out.append( data_map.get(h,'') )
        return out
    def get_model_attrs(fields):
        field_attrs=[]
        for k,v in fields.items():
            for fa in v.keys():
                if fa not in field_attrs:
                    field_attrs.append(fa)
        return field_attrs
    def get_model_html(fields):
        rows=[]
        headers = get_model_attrs(fields)
        for k,v in sorted(fields.items(),key=lambda a:(a[1]['type'],a[0])):
            row = [k]+get_row(headers, v)
            rows.append(row)
        headers = ['FieldName']+headers
        return HTML.table(rows, header_row=headers)
    def functional_fields(fields):
        return dict( [(x,fields[x]) for x in fields if fields[x].get('function',False)] )
    def nonfunctional_fields(fields):
        return dict( [(x,fields[x]) for x in fields if not fields[x].get('function',False)] )

    def simple_fields(fields):
        SIMPLE_FIELDS=['binary','boolean','char','date','datetime','float','integer','integer_big','text']
        return dict( [(x,fields[x]) for x in fields if fields[x]['type'] in SIMPLE_FIELDS] )
    def nonsimple_fields(fields):
        SIMPLE_FIELDS=['binary','boolean','char','date','datetime','float','integer','integer_big','text']
        return dict( [(x,fields[x]) for x in fields if fields[x]['type'] not in SIMPLE_FIELDS] )

    def many2one_rels(fields):
        out=[]
        for k,v in fields.items():
            if v['type']=='many2one':
                req=v.get('required',False)
                if (v['relation'] not in out) and req:
                    out.append(v['relation'])
        return out
    
    fp=open('model2.html','wb')
    rel_map={}
    for model in sorted(ir_model_obj.browse(cr, uid, model_ids),key=lambda a:a.model):
        obj=obj_pool.get(model.model)
        all_fields = obj.fields_get(cr, uid)

        fp.write('<h1> %s </h1>' % (model.model ))
        fp.write('<h2> Nonfunctional Fields</h2>')
        fields = nonfunctional_fields(all_fields)
        fp.write('<h3> Simple fields </h3>')
        s_fields = simple_fields(fields)
        fp.write(get_model_html(s_fields))
        fp.write('<p>')
        fp.write('<h3> Relational fields </h3>')
        ns_fields = nonsimple_fields(fields)
        fp.write(get_model_html(ns_fields))
        fp.write('<p>')
        fp.write('<h2> Functional Fields</h2>')
        fields = functional_fields(all_fields)
        fp.write('<h3> Simple fields </h3>')
        s_fields = simple_fields(fields)
        fp.write(get_model_html(s_fields))
        fp.write('<p>')
        fp.write('<h3> Relational fields </h3>')
        ns_fields = nonsimple_fields(fields)
        fp.write(get_model_html(ns_fields))
        fp.write('<p>')


        rels = many2one_rels(nonfunctional_fields(all_fields))
        rel_map[model.model] = rels
        #rels_str  = ', '.join( rels )

    fp.close()
    return rel_map




if __name__ == '__main__':
    sys.path.append('/home/jan/openerp6/server/6.1/')
    import openerp
    import openerp.tools.config
    import openerp.service.web_services

    conf = openerp.tools.config

    conf['db_user']='jan'
    conf['db_host']='localhost'
    conf['addons_path']='/home/jan/openerp6/server/6.1/openerp/addons,/home/jan/openerp6/addons/6.1,/home/jan/openerp6/web/6.1/addons,/home/jan/openerp6/addons/amaddons'

    modules = ['account', 'account_accountant']
    dbname='amdemo'
    obj_pool, cr, uid = create_and_init_db(dbname, modules)

    cr.commit()
    cr.close()
