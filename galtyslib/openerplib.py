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
    
    user_obj.write(cr, uid, 1, {'in_group_5':True,
                                'in_group_6':True,
                                #'in_group_10':True,
                                } )
    #install_ids = module_obj.search(cr, uid, [('name','in',['account', 'account_accountant']) ] )
    #modules = [x.strip() for x in file('modules.txt').readlines() ]
    install_ids = module_obj.search(cr, uid, [('name','in',modules) ] )
    
    ret=module_obj.button_install(cr, uid, install_ids)
    #print ret
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

def create_and_init_db(dbname, modules):


    create_empty_db(dbname)
    obj_pool, cr, uid = get_connection(dbname)
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

def f64(header, data, fields64):
    out=[]
    for row in data:
        for f64 in fields64:
            i=header.index(f64)
            fn=row[i]
            row[i] = base64.encodestring(file(fn).read())
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
                out_row.append(v)
        out.append(out_row)
    import csv
    fp = open(fn, 'wb')
    csv_writer=csv.writer(fp)
    csv_writer.writerows( [header_export] )
    csv_writer.writerows( out )
    fp.close()
    return out

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
