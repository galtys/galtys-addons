import os
import csv
import psycopg2
import sys
import pickle
import time

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
