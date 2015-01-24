from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import os

class repository2(osv.osv):
    _inherit = "deploy.repository"
    def _get_url(self, cr, uid, ids,field_name,arg, context=None):
        #print 'BAFFF'
        res={}
  #      models_data = self.pool.get('ir.model.data')
   #     cr.execute("select res_id,name,module from ir_model_data where model='deploy.repository.clone' and res_id in (%s)" % ",".join(map(str,ids)) )
    #    ext_map=dict([(x[0],'%s.%s'%(x[2],x[1])) for x in cr.fetchall()])
        
        for c in self.browse(cr, uid, ids):
            #print [clone.name, clone.owner_id.name]
            
            #dummy, form_view = models_data.get_object_reference(cr, uid, 'postcode_address_search', 'view_address_finder_form')
            
            if c.remote_proto=='ssh':
                url="%s@%s:/%s"%(c.remote_login,c.host_id.name,c.remote_location)
            else: #bzr or launchapd?
                url="%s://%s@%s/%s"%(c.remote_proto,c.remote_login,c.host_id.name,c.remote_location)

            if c.root_directory:
                local=c.root_directory
            else:
                local=''
            if c.host_id:
                local=os.path.join(local, c.host_id.name)

            if c.local_location:
                local=os.path.join(local, c.local_location)
            if c.remote_location and (not c.local_location):
                local=os.path.join(local, c.remote_location)

            res[c.id]={'url':url,
                       #'type':c.e_id.type,
 #                      'extid': ext_map.get( c.id, ''),
                       'local_location_fnc':local,
                       'git_clone':"git clone --branch %s %s %s"%(c.branch,
                                                                  url,
                                                                  local),
                       #'bzr_branch':"bzr branch %s"%url,
                       'mkdir':"mkdir -p %s" % local}

        return res
    _columns = {
        'url':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='URL'),
#        'extid':fields.function(_get_url, type="char",size=333,multi='url',method=True,string='EXTID'),
        'git_clone':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='GIT CLONE'),
        'mkdir':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='mkdir'),
        #'type':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='type'),
        'local_location_fnc':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='llf'),
        }

class repository_clone2(osv.osv):
    _inherit = "deploy.repository.clone"
    def _get_url(self, cr, uid, ids,field_name,arg, context=None):
        #print 'BAFFF'
        res={}
        models_data = self.pool.get('ir.model.data')
        cr.execute("select res_id,name,module from ir_model_data where model='deploy.repository.clone' and res_id in (%s)" % ",".join(map(str,ids)) )
        ext_map=dict([(x[0],'%s.%s'%(x[2],x[1])) for x in cr.fetchall()])
        
        for c in self.browse(cr, uid, ids):
            #print [clone.name, clone.owner_id.name]
            
            #dummy, form_view = models_data.get_object_reference(cr, uid, 'postcode_address_search', 'view_address_finder_form')
            res[c.id]={'url':c.remote_id.url,
                       'type':c.remote_id.type,
                       'extid': ext_map.get( c.id, ''),
                       'local_location_fnc':c.remote_id.local_location_fnc,
                       'git_clone':c.remote_id.git_clone,
                       'local_host_id':c.local_user_id.host_id.id,
                       'addon_subdir':c.remote_id.addon_subdir,
                       'is_module_path':c.remote_id.is_module_path,
                       'branch':c.remote_id.branch,
                       'mkdir':c.remote_id.mkdir}
            if 0: #no local changes for start
                if c.remote_proto=='ssh':
                    url="%s@%s:/%s"%(c.remote_login,c.remote_id.host_id.name,c.remote_location)
                else: #bzr or launchapd?
                    url="%s://%s@%s/%s"%(c.remote_proto,c.remote_login,c.remote_id.host_id.name,c.remote_location)

                if c.root_directory:
                    local=c.root_directory
                else:
                    local=''
                if c.remote_id.host_id:
                    local=os.path.join(local, c.remote_id.host_id.name)

                if c.local_location:
                    local=os.path.join(local, c.local_location)
                if c.remote_location and (not c.local_location):
                    local=os.path.join(local, c.remote_location)
                if url != remote_id.url:
                    res[c.id]['url'] = url

                if local != remote_id.local_location_fnc:
                    res[c.id]['local_location_fnc'] = local

                git_clone = "git clone --branch %s %s %s"%(c.branch,
                                                           url,
                                                           local)
                if git_clone != remote_id.git_clone:
                    res[c.id]['git_clone']==git_clone

                mkdir = "mkdir -p %s" % local

                if mkdir != remote_id.mkdir:
                    res[c.id]['mkdir'] = mkdir

        return res
    _columns = {
        'url':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='URL'),
        'addon_subdir':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='addon_subdir'),
        'is_module_path':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='is_module_path'),
        'branch':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='branch'),

        'local_host_id':fields.function(_get_url, type='many2one', relation='deploy.host',multi='url',method=True,string='LocalHost'),
        'extid':fields.function(_get_url, type="char",size=333,multi='url',method=True,string='EXTID'),
        'git_clone':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='GIT CLONE'),
        'mkdir':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='mkdir'),
        'type':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='type'),
        'local_location_fnc':fields.function(_get_url, type='char', size=1000,multi='url',method=True,string='llf'),
        }


class deploy2(osv.osv):
    _inherit = "deploy.deploy"
    def _get(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        for d in self.browse(cr, uid, ids):
            OPTIONS=[('db_host', '127.0.0.1'),
                     ('db_port', str(d.options_id.pg_user_id.cluster_id.port)),
                     ('db_user', d.options_id.pg_user_id.login),
                     ('unaccent',d.options_id.unaccent),
                     #('db_password', 'glot_U43!!a33'),
                     #('db_filter', 'galtys_website'),
                     ('xmlrpc_interface',d.options_id.xmlrpc_interface),
                     ('xmlrpc_port',str(d.options_id.xmlrpc_port)),
                      ]
            clone_ids=[]
            for reps in [r for r in d.application_id.repository_ids]:
                for r in reps:
                    for c in r.clone_ids:
                        if (d.host_id.id in [h.id for h in c.local_host_ids]):
                            clone_ids.append( c.id )
            if d.user_id:
                who="%s@%s"%(d.user_id.login,d.user_id.host_id.name)
            else:
                who='N/A'
            res[d.id]={'options':str(OPTIONS),
                       'db_password':d.options_id.pg_user_id.password_id.password,
                       'admin_password':d.options_id.admin_password.password,
                       'implicit_clone_ids':clone_ids,
                       'config_clone_ids':clone_ids+[x.id for x in d.clone_ids],
                       'who':who,
                       }
                       #'type':c.repository_id.type,
                       #'local_location_fnc':local,
                       #'git_clone':"git clone --branch %s %s %s"%(c.branch,
            #                                                      url,
             #                                                     local),
                       #'bzr_branch':"bzr branch %s"%url,
                       #'mkdir':"mkdir -p %s" % local,
        return res
    _columns = {
        'options':fields.function(_get, type='char', size=1000,multi='options',method=True),
        'implicit_clone_ids':fields.function(_get, type='one2many',relation='deploy.repository.clone',method=True,multi='options',string='Implicit Clones'),
        'config_clone_ids':fields.function(_get, type='one2many',relation='deploy.repository.clone',method=True,multi='options',string='Config Clones'),

        'db_password':fields.function(_get, type='char', size=1000,multi='options',method=True),
        'admin_password':fields.function(_get, type='char', size=1000,multi='options',method=True),
        'who':fields.function(_get, type='char', size=1000,multi='options',method=True,string='ByWho'),
        }
from openerp.modules.module import get_module_resource
from mako.template import Template
from mako.runtime import Context
import os
def to_ascii(a):
    if a is None:
        return ''
    out=''
    for x in a:
        if ord(x)<=128:
            out+=x
    return out
def html_indent(level):
    return '&nbsp;'*(level+1)
def value(v):
    if v is None:
        return ''
    else:
        return v

from StringIO import StringIO
def render_mako_str(template, context):
    t=Template(template)
    buf=StringIO()
    ctx=Context(buf, **context)
    t.render_context(ctx)
    return buf.getvalue()
def render_mako_file(template, context, fn=None):
    if os.path.isfile(template):
        template=file(template).read()
        t=Template(template)
        buf=StringIO()

        ctx=Context(buf, **context)
        t.render_context(ctx)
        return buf.getvalue()
    else:
        return None

class deploy_password(osv.osv):
    _inherit = "deploy.password"
    def _get(self, cr, uid, ids, field_name,arg,context=None):
        res={}
        for p in self.browse(cr, uid, ids):
            tag="__PASS_%s_ID__%d__"%(self._name.replace('.','_'), p.id)
            res[p.id]={'pass_tag':tag}
        return res
    _columns = {
        'pass_tag':fields.function(_get,type='char',size=4444,multi='pass_tag',method=True,string='pass_tag'),
        }

class mako_template(osv.osv):
    _inherit = "deploy.mako.template"
    _order = "sequence"
    def _get(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        for t in self.browse(cr, uid, ids):
            #path = get_module_resource('hr', 'static/src/img', 'default_image.png')
            path = get_module_resource(t.module, t.path, t.fn)
            if 'active_id' in context:
                obj=self.pool.get(t.model).browse(cr, uid, context['active_id'])
                if t.type in ['template','bash']:
                    ctx={#'context':context,
                         'o':obj,
                         't':t,
                         'to_ascii':to_ascii,
                         'value':value,
                         'to_ascii':to_ascii,
                         'html_indent':html_indent,                                  
                         }
                    #print ctx
                    ret=render_mako_file(path,ctx)
                elif t.type in ['python']:
                    ret=file(path).read()
                ctx2={'o':obj }
                out_file=render_mako_str(str(t.out_fn),ctx2)
                res[t.id] = {'out_content':ret,'source_fn':path,'out_file':out_file}
            else:
                res[t.id] = {'out_content':file(path).read(),'source_fn':path,'out_file':''}

            #fp = misc.file_open(pathname)
        return res
    _columns = {
        #'model_id':fields.many2one('ir.model', 'Model Link')
        'out_file':fields.function(_get,type='text',multi='content',method=True,string='out_file'),       
        'out_content':fields.function(_get,type='text',multi='content',method=True,string='out_content'),
        'source_fn':fields.function(_get,type='char',size=4444,multi='content',method=True,string='source_fn'),
        }

class deploy_pg_cluster(osv.osv):
    _inherit = "deploy.pg.cluster"
    def _get_template(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        template_ids = self.pool.get('deploy.mako.template').search(cr, uid, [('model','=',self._name)])
        for c in self.browse(cr, uid, ids):
            
            res[c.id] = {'template_ids':template_ids}
        return res
    _columns = {
        'template_ids':fields.function(_get_template, type='one2many',relation='deploy.mako.template',multi='template',method=True),
        }

import csv
def read_csv(fn):
    out=[]
    with open(fn,'rb') as csvfile:
        for row in csv.reader(csvfile):
            out.append(row)
    return out
def export_data(pool, cr, uid, model, fn, db_only=True, ext_ref=None,module=None):
    obj=pool.get(model)
    def db_field(obj, fn):
        #print fn, obj._columns[fn]
        if fn in obj._columns:
            f=obj._columns[fn]
            #print f.__class__.__dict__.keys()
            if f._type in ['boolean','char','text','many2one','integer','float']:
                if '_fnct' not in f.__dict__:
                    return True
        else:
            return False

    #print obj._columns

    if db_only:
        fields = dict([x for x in obj.fields_get(cr, uid).items() if db_field(obj, x[0])])
    else:
        fields = obj.fields_get(cr, uid)
    id_ref_ids = pool.get('ir.model.data').search(cr, uid, [('model','=',model),('module','=',module)])   
    ref_ids = [x.res_id for x in pool.get('ir.model.data').browse(cr, uid, id_ref_ids)]
    #print fields.keys()
    ids = pool.get(model).search(cr, uid, [])
    if ext_ref is None:
        pass
    elif ext_ref is 'ref_only':
        ids=ref_ids
    elif ext_ref is 'noref':
        ids=list( set(ids) - set(ref_ids) )
    #if len(ids)>100:
    #    ids=ids[0:90]
    if os.path.isfile(fn):
        header_export=read_csv(fn)[0]
        data = pool.get(model).export_data(cr, uid, ids,  header_export)
        out=[]
        for row in data['datas']:
            if 0:
                out_row=[row[0]]
                for i,h in enumerate(header):
                    v=row[i+1]
                    t=header_types[i]
                    if (v is False) and (t != 'boolean'):
                        out_row.append('')
                    else:
                        out_row.append(v.encode('utf8'))
                out.append(out_row)
            else:
                row_t=[]
                for c in row:
                    if c in ['FALSE','False',0]:
                        row_t.append('')
                    else:
                        row_t.append(c)
                out.append(row_t)
        
        fp = open(fn, 'wb')
        csv_writer=csv.writer(fp)
        csv_writer.writerows( [header_export] )
        csv_writer.writerows( out )
        fp.close()
        return out

    else:

        header=[]
        header_export=['id']
        #print model
        for f, v in fields.items():
            #print '  ',f,v
            if 'function' not in v:            
                if v['type'] in ['many2one', 'many2many']:
                    if v['relation'] in ['account.account', 'account.journal']:
                        header_export.append( "%s/code" % f )
                    elif v['relation'] in ['account.tax']:
                        header_export.append( "%s/description" % f )
                    else:
                        header_export.append( "%s/id" % f )
                    header.append(f)
                elif v['type']=='one2many':
                    pass
                else:
                    header.append(f)
                    header_export.append(f)
    #if 1:
        header_types = [fields[x]['type'] for x in header]
        #print [ids, header_export]
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
                    out_row.append(v.encode('utf8'))
            out.append(out_row)
        
        fp = open(fn, 'wb')
        csv_writer=csv.writer(fp)
        csv_writer.writerows( [header_export] )
        csv_writer.writerows( out )
        fp.close()
        return out
import os
class ir_module_module(osv.osv):
    _inherit = "ir.module.module"
    def master_data_export(self, cr, uid, ids, context=None):
        for m in self.browse(cr, uid, ids):
            path = get_module_resource(m.name, '', '__openerp__.py')
            mod_meta=eval(file(path).read())
            files=mod_meta['update_xml']
            for f in files:
                p,fn=os.path.split(f)
                #fn.split('.')
                model = fn[:-4]#.split('.')
                dest_fn=get_module_resource(m.name,p, fn)
                export_data(self.pool, cr, uid, model, dest_fn, db_only=True, module=m.name)
                #print p,fn
            
        return {'ok':'done'}
    
class host(osv.osv):
    _inherit = 'deploy.host'
    def render(self, cr, uid, ids, context=None):
        ret=self.render_files(cr, uid, ids, [], [] ,context=context)
        out=[]
        for h,ret_h in ret.items():
            files=ret_h['files']
            for k,v in files.items():
                #print k,v
                model,t_id,r_id=k
                out_fn,content,user,group,_type,name,python_function,subprocess_arg,chmod,sequence=v
                out.append( (h,model,t_id,r_id,out_fn,content,user,group,_type,name,python_function,subprocess_arg,chmod,sequence) )
        
        return sorted(out, key=lambda a:a[-1] )

    def render_files(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        #field_ids = self.pool.get('ir.model.fields').search(cr, uid, [('relation','=','deploy.host')] )
        #models=[]
        active_hostname=context['hostname']
        #for f in self.pool.get('ir.model.fields').browse(cr, uid, field_ids):
        #    if f.model not in models:
        #        models.append(f.model)
        models = [u'deploy.host.user', u'deploy.host.group', u'deploy.repository', u'deploy.pg.cluster', u'deploy.deploy', u'deploy.repository.clone']
        print models, context
        t_h_ids = self.pool.get('deploy.mako.template').search(cr, uid, [('model','=','deploy.host')])            
        template_ids = self.pool.get('deploy.mako.template').search(cr, uid, [('model','in',models)])
        t_ids = template_ids+t_h_ids
        for h in self.browse(cr, uid, ids):
            files={}
            for t in self.pool.get('deploy.mako.template').browse(cr, uid, t_ids):
                eval_arg = t.domain%active_hostname
                print t.name, eval_arg, t.model
                rec_ids = self.pool.get(t.model).search(cr, uid, eval(eval_arg) ) #!!!! find safe eval
                for r_id in rec_ids:
                    o=self.pool.get('deploy.mako.template').browse(cr, uid, t.id,context={'active_id':r_id})
                    key=(str(t.model),t.id,r_id)
                    user=t.user_id.login
                    group=t.user_id.group_id.name
                    #print 'key:', key
                    files[key]=(o.out_file,o.out_content,user,group,t.type,t.name,t.python_function,t.subprocess_arg,t.chmod,t.sequence )
                
            res[h.id] = {'template_ids':template_ids,'files':files}
            
        return res
    def _host(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for h in self.browse(cr, uid, ids):
            b=int( h.memory_total*h.memory_pagesize*(h.memory_buffer_percent/100.0) )#BYTES
            #print [h.memory_total, h.memory_pagesize, h.memory_buffer_percent ]
            mb=2**20
            shmall = h.memory_total/2
            shmmax = shmall * h.memory_pagesize
            if b>0:
                b_mb=shmmax/mb
            else:
                b_mb=0
            res[h.id]={'memory_buffer_calc':b,
                       'memory_buffer_calc_mb':b_mb,
                       'kernel_shmall':shmall,
                       'kernel_shmmax':shmmax}
        return res
    _columns = {
        'template_ids':fields.function(render_files, type='one2many',relation='deploy.mako.template',multi='template',method=True),
        'files':fields.function(render_files, type='text',multi='template',method=True),
        'memory_buffer_calc':fields.function(_host,type='integer',multi='host',method=True,string="Calc buff size"),
        'memory_buffer_calc_mb':fields.function(_host,type='integer',multi='host',method=True,string="Calc buff size MB"),
        'kernel_shmall':fields.function(_host,type='integer',multi='host',method=True,string="shmall"),
        'kernel_shmmax':fields.function(_host,type='integer',multi='host',method=True,string="shmmax"),
        }
