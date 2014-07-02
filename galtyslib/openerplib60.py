import os
import csv
import psycopg2
import sys
import pickle
import time
import base64

import pooler
import sql_db
import service
import tools

def create_empty_db(dbname):
    DB=dbname
    db=service.web_services.db(DB)
    #data = db.exp_dump('amdemo_template')
    db_id=db.exp_create(DB, False, 'en_GB','admin')
    done=False
    while not done:
        complete, info = db.exp_get_progress(db_id)
        time.sleep(2)
        if complete == 1.0:
            done=True
def copy_db(dbname1, dbname2):
    db1=service.web_services.db(dbname1)
    data = db1.exp_dump(dbname1)
    db2=service.web_services.db(dbname2)
    #db2._create_empty_database(dbname2)
    return db2.exp_restore(dbname2, data)
def drop_db(dbname):
    db1=service.web_services.db(dbname)
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
    obj_pool=pooler.get_pool(DB)
    pool=sql_db.ConnectionPool()
    cr = sql_db.Cursor(pool,DB)
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
def export_data(pool, cr, uid, model, fn, db_only=False, ext_ref=None):
    obj=pool.get(model)
    if db_only:
        fields = dict([x for x in obj.fields_get(cr, uid).items() if (x[0] in obj._columns)])
    else:
        fields = obj.fields_get(cr, uid)
    id_ref_ids = pool.get('ir.model.data').search(cr, uid, [('model','=',model)])   
    ref_ids = [x.res_id for x in pool.get('ir.model.data').browse(cr, uid, id_ref_ids)]

    ids = pool.get(model).search(cr, uid, [])
    if ext_ref is None:
        pass
    elif ext_ref is 'ref_only':
        ids=ref_ids
    elif ext_ref is 'noref':
        ids=list( set(ids) - set(ref_ids) )
    #if len(ids)>100:
    #    ids=ids[0:90]
    header=[]
    header_export=['id']
    for f, v in fields.items():
        if 'function' not in v:
            if v['type'] in ['many2one', 'many2many']:
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
    for row in data['datas']:
        out_row=[row[0]]
        for i,h in enumerate(header):
            v=row[i+1]
            t=header_types[i]
            if (v is False) and (t != 'boolean'):
                out_row.append('')
            else:
                if v in (True,False):
                    out_row.append(v)
                else:
                    out_row.append(v.encode('utf8'))
        out.append(out_row)
    import csv
    fp = open(fn, 'wb')
    csv_writer=csv.writer(fp)
    csv_writer.writerows( [header_export] )
    csv_writer.writerows( out )
    fp.close()
    return out


def generate_accounts_from_template_byname(obj_pool, cr, uid, name='corrected'):
    #x='l10n_uk_%s.l10n_uk_%s' (name,name)
    wizard_obj = obj_pool.get('wizard.multi.charts.accounts')
    install_obj = obj_pool.get('account.installer')
    bank_wizard_obj = obj_pool.get('account.bank.accounts.wizard')


    header = ['company_id/id','code_digits', 'sale_tax/id','purchase_tax/id','sale_tax_rate','purchase_tax_rate','currency_id', 'chart_template_id/id']
    row = ['base.main_company', 2, 'l10n_uk_%s.ST11'%name,'l10n_uk_%s.PT11'%name, 0.2, 0.2, 'GBP', 'l10n_uk_%s.l10n_uk_%s'% (name,name)]
    
    ret = wizard_obj.load(cr, uid, header, [row] )
    #print ret
    ids = ret['ids']
    if ids:
        wizard_obj.execute(cr, uid, ids)
    return
def dict2row(PCMRP,rec):
    out=[]
    for p in PCMRP:
        out.append(rec[p])
    return out

def save_csv(fn, data, HEADER=None):
    if len(data)>0:
        if HEADER is None:
            HEADER=data[0].keys()
    fp = open(fn, 'wb')
    out=[dict2row(HEADER, x) for x in data]
    csv_writer=csv.writer(fp)
    csv_writer.writerows( [HEADER]+out )
    fp.close()

def generate_periods(pool, cr, uid, year='2013'):
    install_obj = pool.get('account.installer')
    header = ['date_start', 'date_stop', 'period','company_id/id']
    data_row = [time.strftime('%s-01-01'%year), time.strftime('%s-12-31'%year), 'month', 'base.main_company']
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

def module_dep(dbname):
    pool, cr, uid = get_connection(dbname)
    dbname2=dbname+'_analyse2'
    import tools.config
    if db_exist(tools.config, dbname2):
        drop_db(dbname2)
    cr.execute("select name,id from ir_module_module")
    module_name_id_map=dict([x for x in cr.fetchall()])
    module_id_name_map=dict([ (x[1],x[0]) for x in module_name_id_map.items()])
    mod_dep_sql = "select name,module_id from ir_module_module_dependency"

    cr.execute(mod_dep_sql)
    recs2=cr.fetchall()
    #recs2_dicts=[{'id':x[0], 'name':x[1], 'module_id':x[2], 'parent':x[3]} for x in recs2]
    dep_map={}
    for name,module_id in recs2:
        v=dep_map.setdefault(name, [])
        v.append(module_id)
    dep_map2={}
    for name,module_id in recs2:
        v=dep_map2.setdefault(module_id, [])
        name_id=module_name_id_map[name]
        v.append(name_id)
    import galtyslib.topological_sorting as topological_sorting
    mod_dep_ids=topological_sorting.topological_sorting(dep_map2)
    mod_dep=[ x for x in pool.get('ir.module.module').browse(cr, uid, mod_dep_ids) if x.state=='installed']
    mod_dep_name=[(x.name,[module_id_name_map.get(y) for y in dep_map2.get(x.id,[]) ]) for x in mod_dep]
    cr.commit()
    cr.close()

    print 'new db', dbname2
    print 'to install %d modules.'% len(mod_dep_name)
    print mod_dep_name
    model_field_module_map = {}
    model_transient_map={}
    NEW_DB=True
    module_model_fields_map={}
    for module, deps in mod_dep_name:
        model_fields_map = module_model_fields_map.setdefault(module, {})
        if NEW_DB:
            print [module]
            ret  = create_and_init_db(dbname2, [module])
            NEW_DB=False
        #print 'installing module', module, deps
        pool, cr, uid = get_connection(dbname2)           
        ret = install_modules(pool,cr,uid, [module] )
        cr.commit()
        cr.close()

        pool, cr, uid = get_connection(dbname2)           
        #print 'getting new fields...'
        model_ids = pool.get('ir.model').search(cr, uid, [])
        
        for model in pool.get('ir.model').browse(cr, uid, model_ids):
            #print '   ',model.model
            obj=pool.get(model.model)
            if obj:
                all_fields = obj.fields_get(cr, uid)
                v=model_field_module_map.setdefault(model.model, {})
                model_transient_map[model.model]=False #pool.get(model.model).is_transient()
                if not model_transient_map[model.model]:
                    model_fields_map[model.model] = all_fields
                for kf in all_fields:
                    #fmodules=v.setdefault(kf, [])
                    if kf not in v:
                        v[kf]=module
                    #if mod not in fmodules:
                    #    fmodules.append(module)
            else:
                print '   module not in pool', model.model
        #print 
        cr.commit()
        cr.close()
    return model_field_module_map, model_transient_map, mod_dep_name, module_model_fields_map
def module_dep2(model_field_module_map, model_transient_map, mod_dep_name):
    mod_sorted = [x[0] for x in mod_dep_name]
#    if (not model_transient_map[ x[0] ] ) ]
    module_model_map={}
    for model,fields in model_field_module_map.items():
        for f,mod in fields.items():
            v=module_model_map.setdefault(mod, [])
            v.append(model)
    model_module_map={}
    for model,fields in model_field_module_map.items():
        for f,mod in fields.items():
            v=model_module_map.setdefault(model, [])
            v.append(mod)
    models_sorted=[]
    mm1_map=dict([(x[0],list(set(x[1]))) for x in module_model_map.items()])
    mm2_map=dict([(x[0],list(set(x[1]))) for x in model_module_map.items()])
    return mod_sorted, mm1_map, mm2_map

def list_models(obj_pool, cr, uid, model_ids, fnout='model2.html',  mfm_map=None, ms=None, mt_map=None):
    # mfm=model_field_module_map, ms=mod_sorted
    ir_model_obj=obj_pool.get('ir.model')
    #model_ids = ir_model_obj.search(cr, uid, [])
    #field_attrs=[]
    import galtyslib.HTML as HTML
    #model_field_module_map = {}
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
    def add_module_to_fields(fields, model_field_module_map, model_name):
        out={}
        for k,v in fields.items():
            v['module']=model_field_module_map.get(model_name, {}).get(k)
            if model_name not in model_field_module_map:
                print 'missing model', model_name
            elif k not in model_field_module_map[model_name]:
                print 'missing ', [model_name, k]
            out[k]=v
        return out
    fp=open(fnout,'wb')
    rel_map={}
    #mt_map
    transient_ids=[x.id for x in ir_model_obj.browse(cr, uid, model_ids) if mt_map.get(x.model)]
    db_ids=[x.id for x in ir_model_obj.browse(cr, uid, model_ids) if not mt_map.get(x.model)]
    tmodels= sorted(ir_model_obj.browse(cr, uid, transient_ids),key=lambda a:a.model)
    dmodels= sorted(ir_model_obj.browse(cr, uid, db_ids),key=lambda a:a.model)
    
    for model in dmodels+tmodels:
	#print 'model: ', model.model, model.name
        obj=obj_pool.get(model.model)
	if not obj:
	    #print "%s (%s)" % (model.model, model.name)
            #fields = obj.fields_get(cr, uid)
	    continue
        #db_fields = nonfunctional_fields(fields)
        #export_data(obj_pool, cr, uid, model.model, )
        
        all_fields = add_module_to_fields(obj.fields_get(cr, uid), mfm_map, model.model)

        fp.write('<h1> Model %s </h1>' % (model.model ))
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
    import tools.config
    import service.web_services

    conf = tools.config

    conf['db_user']='jan'
    conf['db_host']='localhost'
    conf['addons_path']='/home/jan/openerp6/server/6.1/openerp/addons,/home/jan/openerp6/addons/6.1,/home/jan/openerp6/web/6.1/addons,/home/jan/openerp6/addons/amaddons'

    modules = ['account', 'account_accountant']
    dbname='amdemo'
    obj_pool, cr, uid = create_and_init_db(dbname, modules)

    cr.commit()
    cr.close()
