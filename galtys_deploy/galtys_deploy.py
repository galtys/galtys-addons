from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp

#Steps
#golive register
#golive pull

#Main menu: Deploy

#Sub menu: Configuration

class deploy_account(osv.osv):
    _order = "name"
    _name = "deploy.account"  #Accounts
    _columns = {
        'name':fields.char('Name', size=444),
        #'login':fields.char('Login',size=444),
        #'host_ids':fields.many2many('deploy.host', 'deploy_account_deploy_host_rel', 'host_id', 'account_id', 'Hosts'),
        'user_ids':fields.many2many('deploy.host.user', 'deploy_account_deploy_host_user_rel', 'user_id', 'account_id', 'Users'),
        'app_ids':fields.many2many('deploy.application', 'deploy_account_deploy_application_rel', 'app_id', 'account_id', 'Apps'),
    }

class deploy_password(osv.osv):
    _name = "deploy.password" #Passwords
    _columns = {
        'name':fields.char('Name',size=1000),
        'password':fields.text('Password'),#password encrypted
        }

class host(osv.osv):
    _name = "deploy.host"   #Hosts
    _columns = {
        'name':fields.char('Name',size=100),
        'memory_total':fields.integer('Memory Total Pages'),
        'memory_pagesize':fields.integer('Memory PageSize'),
        'memory_buffer_percent':fields.integer('Buffer Size Percent'),
        'user_ids':fields.one2many('deploy.host.user','host_id','Users'),
        'group_ids':fields.one2many('deploy.host.group','host_id','Groups'),
        'cluster_ids':fields.one2many('deploy.pg.cluster','host_id','PG Clusters'),
        'control':fields.boolean('Control'),
        #'deploy_ids':fields.one2many('deploy.deploy','host_id','Deployments'),
        }

class pg_cluster(osv.osv):
    _name = "deploy.pg.cluster" #Postgresql Clusters
#    _rec_name = 'host_id'
    _columns = {
        'host_id':fields.many2one('deploy.host','Hostname'),
        'port':fields.integer('Port'),
        'version':fields.char('Version',size=10),
        'name':fields.char('Name', size=20),
        'description':fields.char('Description',size=4444),
        'active':fields.boolean('Active'),

        'listen_addresses':fields.char('listen_addresses',size=444),
        'shared_buffers':fields.char('shared_buffers',size=444),
        'fsync':fields.char('fsync',size=444),
        'synchronous_commit':fields.char('synchronous_commit',size=444),
        'full_page_writes':fields.char('full_page_writes', size=444),
        'checkpoint_segments':fields.char('checkpoint_segments',size=444),
        'checkpoint_timeout':fields.char('checkpoint_timeout',size=444),

        'user_ids':fields.one2many("deploy.pg.user",'cluster_id','PG Users'),
        'database_ids':fields.one2many("deploy.pg.database",'cluster_id','Databases'),
        'hba_ids':fields.one2many("deploy.pg.hba",'cluster_id','HBA'),
        }
    _defaults = {
        'listen_addresses':'127.0.0.1',
        'shared_buffers':'24MB',
        'fsync': 'off',
        'synchronous_commit':'off',
        'full_page_writes':'off',
        'checkpoint_segments':7,
        'checkpoint_timeout':'15min',       
        }

class pg_user(osv.osv):
    _name="deploy.pg.user"
    _rec_name='login'
    _columns ={
        'cluster_id':fields.many2one('deploy.pg.cluster','PG Cluster'),
        'account_id':fields.many2one('res.users','Account'),
        'password_id':fields.many2one('deploy.password','PG Password'),
        'superuser':fields.boolean('Superuser'),
        'create_db':fields.boolean('Create db'),
        'create_role':fields.boolean('Create Role'),
        'login':fields.char('Login',size=44),
        'type':fields.selection([('real','real'),('virtual','virtual'),('system','system')],'Type' ),
        }

class pg_database(osv.osv):
    _name="deploy.pg.database"
    _columns = {
        'name':fields.char("name",size=444),
        'cluster_id':fields.many2one('deploy.pg.cluster','PG Cluster'),
        'type':fields.selection([('live','live'),('virtual','virtual'),('system','system'),('demo','demo'),('snapshot','snapshot'),('replicated','replicated')]),
        'date':fields.date('date'),
        'backup':fields.boolean('backup needed'),
        }

class pg_hba(osv.osv):
    _name = "deploy.pg.hba"
    _columns = {
        'name':fields.char('Description', size=444),
        'type':fields.selection([('local','local'),('host','host'),('hostssl','hostssl'),('hostnossl','hostnossl')], 'Type' ),
        'database_ids':fields.many2one('deploy.pg.database','database'),
        'cluster_id':fields.many2one('deploy.pg.cluster','PG Cluster'),
        'user':fields.many2one('deploy.pg.user','PG USER'),
        'address':fields.char('address',size=444),
        'ip_address':fields.char('ip_address',size=444),
        'ip_mask':fields.char('ip_mask',size=444),
        'auth_method':fields.selection([('peer','peer'),('trust','trust'),('md5','md5')], 'auth_method'),
        'auth_options':fields.char('auth_options',size=444),       
}

class host_group(osv.osv):
    _name = "deploy.host.group" #Host Groups
    _rec_name='name'
    _columns = {
        'name':fields.char('Name',size=100),
        'gid':fields.integer('GID'),
        'host_id':fields.many2one('deploy.host','Host'),
        'sftp':fields.boolean('Allow SFTP'),        
        'type':fields.selection([('user','user'),('system','system')],'Type'),
        }

class host_user(osv.osv):
    _name = 'deploy.host.user' #Host User
#    _rec_name='login'
    _columns = {
        'name':fields.char('Name',size=100),
        'login':fields.char('Login',size=100),
        'group_id':fields.many2one('deploy.host.group','Main Group'),
        'password_id':fields.many2one('deploy.password','Password'),
        'account_id':fields.many2one('res.users','Account'),
        #'owner_id':fields.many2one('res.users','Owner'),
        'uid':fields.integer('UID'),
        'ssh':fields.boolean('Allow SSH'),
        'sudo':fields.boolean('Allow SFTP'),    
        'host_id':fields.many2one('deploy.host','Host'),
        'home':fields.char('home',size=44),
        'shell':fields.char('shell',size=44),
        'type':fields.selection([('user','user'),('system','system')],'Type'),
        'deploy_ids':fields.one2many('deploy.deploy','user_id','Deployments'),
        'app_ids':fields.many2many('deploy.application', 'host_user_application_rel', 'user_id', 'app_id', 'Apps'),
        #'user_id':fields.many2one('deploy.host.user','HostUser'),
        }

#Submenu: Applications
class repository(osv.osv):
    _name = 'deploy.repository' #Repositories
    _columns = {
        'name':fields.char('Name',size=100),
        'type':fields.selection([('git','git'),('bzr','bzr'),('rsync','RSYNC')],'Type'),
        'use':fields.selection([('addon','addon'),('server','server'),('scripts','scripts'),('site','site')],'Use'),

        #
        'remote_id':fields.many2one('deploy.repository','Parent Repository'),
        'validated_addon_path':fields.char('Validated Addon Path',size=444),
        'local_user_id':fields.many2one('deploy.host.user','Local user'),

        'host_id':fields.many2one('deploy.host','Host'),
        'version':fields.char('Version',size=10),
        #'remote_account_id':fields.many2one('res.users','Remote Account'),
        'remote_login':fields.char('Remote Login',size=122),
        'remote_location':fields.char('Remote Location',size=1111),
        'remote_proto':fields.selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        'remote_name':fields.char('Remote Name',size=122), #used in git

	'local_location':fields.char('Local Location',size=1111),
       
        'branch':fields.char('Branch',size=100),
        'addon_subdir':fields.char('Addon Subdir',size=100),
        'is_module_path':fields.boolean('Is Module Path'),
        'root_directory':fields.char('Root Directory',size=100),
        #'clone_ids':fields.one2many('deploy.repository.clone','remote_id','Reposisoty Clones'),
        'clone_ids':fields.one2many('deploy.repository','remote_id','Reposisoty Clones'),
        }
#[root_directory, remote_host_id.name, local_location, remote_location]
class repository_clone(osv.osv): #will be likely deprecated
    _name ='deploy.repository.clone' #Repository clones
#    _inherits = {'deploy.repository':'remote_id'}
    _columns = {
        'name':fields.char('Name',size=100),
        'owner_id':fields.many2one('res.users','Owner'),
        'remote_id':fields.many2one('deploy.repository','Repository'),
        'validated_addon_path':fields.char('Validated Addon Path',size=444),
        #remote_host_id > remote_id.host_id
        #'remote_account_id':fields.many2one('res.users','Remote Account'),
        #'remote_login':fields.char('Remote Login',size=122),
        #'remote_location':fields.char('Remote Location',size=1111),
        #'remote_proto':fields.selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        #'remote_name':fields.char('Remote Name',size=122), #used in git
       
	 #'local_host_id':fields.many2one('deploy.host','Local host'),
        #'local_host_ids':fields.many2many('deploy.host','repository_clone_host_rel','clone_id','host_id','Hosts'), 
        'local_user_id':fields.many2one('deploy.host.user','Local user'),
        'local_location':fields.char('Local Locationi',size=1111),
        'branch_db':fields.char('Branch',size=100),
        'addon_subdir_db':fields.char('Addon Subdir',size=100),
        'is_module_path_db':fields.boolean('Is Module Path'),
        'root_directory':fields.char('Root Directory',size=100),
        #'URL':fnc
        }

class application(osv.osv):
    _name = 'deploy.application' #Applications
    _columns = {
        'repository_ids':fields.many2many('deploy.repository', 'application_repository_rel','app_id','repository_id', 'Repositories', domain=[('remote_id','=',False)]),
        'name':fields.char('Name',size=444),
        }

class options(osv.osv):
    _name='deploy.options' #Server options
    _columns = {
        'unaccent':fields.boolean('Unaccent'),
        'xmlrpc_interface':fields.char('xmlrpc_interface',size=100),
        'xmlrpc_port':fields.integer('xmlrpc_port'),
        #'admin_password':fields.many2one('deploy.password','Admin Password'),
        'name':fields.char('Name',size=444),
        #'logfile':
        }
    
class deploy(osv.osv):
    _name='deploy.deploy' #Deployments
    _columns = {
        'application_id':fields.many2one('deploy.application', 'Application'),
        'pg_user_id':fields.many2one('deploy.pg.user','PG USER'),
        'options_id':fields.many2one('deploy.options','Options'),
        'account_id':fields.many2one('res.users','Account'),
        'password_id':fields.many2one('deploy.password','Admin Password'),
        #'clone_ids':fields.many2many('deploy.repository', 'application_repository','app_id','repository_id', 'Repositories'),
        'name':fields.char('Name',size=444),
        #'host_id':fields.many2one('deploy.host','Host'),#hostname
        'user_id':fields.many2one('deploy.host.user','HostUser'),
        #'host_id_depr':fields.many2one('deploy.host','HostDepr'),
        #'host_id':fields.many2one('deploy.host','Host'),
        'host_id':fields.related('user_id', 'host_id',  string="Host",type="many2one",relation="deploy.host"),
        #'ROOT':fields.char('site_name',size=444),
        'site_name':fields.char('site_name',size=444),
        'daemon':fields.boolean('daemon'),
        'vhost':fields.boolean('vhost'),
        'parse_config':fields.boolean('parse_config'),
        'ServerName':fields.char('ServerName',size=444),
        'IP':fields.char('IP',size=100),
        'PORT':fields.integer('PORT'), 
        'IPSSL':fields.char('IP',size=100),
        'PORTSSL':fields.integer('PORT'), 

        'SSLCertificateFile':fields.char('SSLCertificateFile',size=111),
        'SSLCertificateKeyFile':fields.char('SSLCertificateKeyFile',size=111),
        'SSLCACertificateFile':fields.char('SSLCACertificateFile', size=111),
        'ssl':fields.boolean('ssl'),
        'Redirect':fields.char('Redirect',size=444),
        'mode':fields.selection([('dev','dev'),('live','live')],'Mode'),
        'validated_server_path':fields.char('Validated Server Path',size=444),
        'validated_config_file':fields.char('Validated Config File',size=444),
        'validated_root':fields.char('Validated ROOT',size=444),
        }

class mako_template(osv.osv):
    _name = "deploy.mako.template"
    _columns = {
        'name':fields.char('name',size=444),
        'type':fields.selection([('template','template'),('bash','bash'),('python','python')],'Type' ),
        'gl_command':fields.char('GoLive Command',size=444),
        'model':fields.char('model',size=444),
        'module':fields.char('module',size=444), #to locate template
        'path':fields.char('path', size=444),    #to locate template
        'fn':fields.char('fn',size=4444),        #to locate template

        'domain':fields.char('domain',size=444),
        'out_fn':fields.char('out_fn',size=444),

        'sequence':fields.integer('Sequence'),
        'python_function':fields.char('python_function',size=444),
        'subprocess_arg':fields.char('subprocess_arg',size=444),
        'chmod':fields.char('chmod',size=444),
        'user_id':fields.many2one('deploy.host.user','HostUser'),
        'target_user':fields.char('target_user',size=444),
        'target_group':fields.char('target_group',size=444),

    }

class deploy_file(osv.osv):
    _name = "deploy.file"
    _name_rec = "command"
    _columns = {
        'command':fields.char('Last Command',size=444),
        #'model':fields.char('model',size=444),
        'res_id':fields.integer('res_id'),
        'template_id':fields.many2one('deploy.mako.template', 'Template Used'),
        'encrypted':fields.boolean('Encrypted'),
        'user_id':fields.many2one('deploy.host.user','User'),        
        'sequence':fields.integer('Sequence'),
        'file_written':fields.char('File Written', size=444),
        'content_written':fields.text('Content Written'),
        'cmd_exit_code':fields.char('cmd_exit_code', size=444),
        }
class export_tag(osv.osv):
    _name = "deploy.export.tag"
    _columns ={
        "name":fields.char("name", size=100),
        "sequence":fields.integer('sequence'),
        "parent_id":fields.many2one("deploy.export.tag", "Parent Tag"),
        'field_ids':fields.many2many('ir.model.fields', 'deploy_export_tag_ir_model_fields_rel', 'tag_id', 'field_id', 'Tags'),        
        }
    _default = {
        'sequence':100,
        }

class ir_model(osv.osv):
    _inherit = "ir.model"
    _order = "sequence"
    _columns = {
        'sequence':fields.integer('Sequence'),
        'export_domain':fields.char("Export Domain", size=500),
        }
    def name_get2(self,cr, uid, ids, context=None):
        ret={}
        for m in self.browse(cr, uid, ids):
            ret[m.id]="%s[%s]"%(m.name,m.model)
        return ret
    _default = {
        'sequence':100,
        'export_domain':'[]',
        }

class ir_model_fields(osv.osv):
    _inherit = "ir.model.fields"
    _order = "sequence"
    _columns = {
        'sequence':fields.integer('Sequence'),
        'export_tag_ids':fields.many2many('deploy.export.tag', 'deploy_export_tag_ir_model_fields_rel', 'field_id', 'tag_id', 'Export Tags'),        
        
        }
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        context['manual']='manual'
        prev={}
        for f in self.browse(cr, uid, ids):
            prev[f.id]=f.state
            cr.execute("update ir_model_fields set state='manual' where id=%s", (f.id, ) )
        #    f.write({'state':'manual'})
        res = super(ir_model_fields,self).write(cr, uid, ids, vals, context=context)
        for f in self.browse(cr, uid, ids):
            cr.execute("update ir_model_fields set state=%s where id=%s", (prev[f.id], f.id, ) )
        return res
    _default = {
        'sequence':100,        
        }

#import galtyslib.openerplib as openerplib
def export_data(pool, cr, uid, model, fn, field_list, arg):
    if arg:
        arg=eval(arg)
    else:
        arg=[]
    obj=pool.get(model)

    fields = obj.fields_get(cr, uid)
    f_map={}
    for f,v in fields.items():
        if f in field_list:
            f_map[f]=v
    fields = f_map
    #id_ref_ids = pool.get('ir.model.data').search(cr, uid, [('model','=',model)])   
    #ref_ids = [x.res_id for x in pool.get('ir.model.data').browse(cr, uid, id_ref_ids)]

    ids = pool.get(model).search(cr, uid, arg)

    header=[]
    header_export=['id']
    for f, v in fields.items():
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
                out_row.append(v.encode('utf8'))
        out.append(out_row)
    import csv
    fp = open(fn, 'wb')
    csv_writer=csv.writer(fp)
    csv_writer.writerows( [header_export] )
    csv_writer.writerows( out )
    fp.close()
    return out
import os

class exported_file(osv.osv):
    _name = "deploy.exported.file"
    _order = "sequence"
    _columns = {
        'path':fields.char('path'),
        'fn':fields.char('fn'),
        'model_id':fields.many2one('ir.model','Model'),
        'company_id':fields.many2one('res.company','Company'),
        'tag_id':fields.many2one('deploy.export.tag', 'Export Tag'),
        'sequence': fields.integer('sequence'),
        }

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'export_module_name':fields.char('Export Module Name', size=100),
        'export_module_repo':fields.char('Export Module Repository', size=100),
        'exported_file_ids':fields.one2many('deploy.exported.file','company_id','Exported Files'),
        }
    def set_external_ids(self, cr, uid, ids, context=None):
        for c in self.browse(cr, uid, ids):
            tag_ids = self.pool.get('deploy.export.tag').search(cr, uid, [])
            model_ids = []
            tag_id_map={}
            for tag in self.pool.get('deploy.export.tag').browse(cr, uid, tag_ids):
                tag_id_map[tag.name]=tag
                for f in tag.field_ids:
                    model_ids.append( f.model_id.id )

            for m in self.pool.get('ir.model').browse(cr, uid, model_ids):
                fields = m.field_id
                tag_map = {}
                for f in fields:
                    for t in f.export_tag_ids:
                        v=tag_map.setdefault(t.name, [])
                        v.append(f.name)
                for tag,flds in tag_map.items():
                    path = os.path.join(c.export_module_repo)
                    if not os.path.isdir(path):
                        os.makedirs(path)
                   
                    tag_inst=tag_id_map[tag]
                    sq = m.sequence * tag_inst.sequence
                    fn="%s_%d_%s"%(tag, sq, m.model+'_.csv')
                    
                    file_path=os.path.join(path, fn)
                    arg=[('path','=',path ),
                         ('fn','=',fn),
                         ('model_id','=',m.id),
                         ('company_id','=',c.id),                         
                         ('tag_id','=',tag_inst.id),
                         ]
                    val=dict( [(x[0],x[2]) for x in arg] )
                    val['sequence']=sq
                    ef_id = self.pool.get('deploy.exported.file').search(cr, uid,arg)
                    if not ef_id:
                        ef_id = self.pool.get('deploy.exported.file').create(cr, uid, val)
                    export_data(self.pool, cr, uid, m.model, file_path, flds, m.export_domain)
                
        return True

class tag_wizzard(osv.osv_memory):
    _name = 'deploy.export.tag.wizzard'
    _description="Export Tag"
    _columns ={
        'tag_ids':fields.many2many('deploy.export.tag', 'tag_wizzard_tag_rel', 'wiz_id', 'tag_id', 'Export Tags'),
        #'name':fields.char('Name', size=444),
        #'start_period': fields.many2one('account.period','Start Period', required=True),
        #'end_period': fields.many2one('account.period','End Period', required=True),        
        }
    def set_tags(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids', [])
        print active_ids
        for w in self.browse(cr, uid, ids):
            val={'export_tag_ids':[(6,0,[t.id for t in w.tag_ids])]}
            self.pool.get('ir.model.fields').write(cr, uid, active_ids, val, context=context)
            
        return True


