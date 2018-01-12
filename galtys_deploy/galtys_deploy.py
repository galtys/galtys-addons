from odoo import fields, models, expression
import openerp.addons.decimal_precision as dp
import bitcoin
#Steps
#golive register
#golive pull

#Main menu: Deploy

def secret_random_key(a):
    return bitcoin.random_key()

#class SkynetCode(models.Model):
#    pass

    
class deploy_account(models.Model):
    _order = "name"
    _name = "deploy.account"  #Accounts


    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    name = fields.Char('Name', size=444)
        #'login':fields.Char('Login',size=444),
        #'host_ids':fields.Many2many('deploy.host', 'deploy_account_deploy_host_rel', 'host_id', 'account_id', 'Hosts'),
    user_ids = fields.Many2many('deploy.host.user', 'deploy_account_deploy_host_user_rel', 'user_id', 'account_id', 'Users')
    app_ids = fields.Many2many('deploy.application', 'deploy_account_deploy_application_rel', 'app_id', 'account_id', 'Apps')


class deploy_password(models.Model):
    _name = "deploy.password" #Passwords

    name = fields.Char('Name',size=1000)
        'password':fields.Text('Password'),#password encrypted
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
        }

class host(models.Model):
    _name = "deploy.host"   #Hosts

    name = fields.Char('Name',size=100)
    memory_total = fields.Integer('Memory Total Pages')
    memory_pagesize = fields.Integer('Memory PageSize')
    memory_buffer_percent = fields.Integer('Buffer Size Percent')
    user_ids = fields.One2many('deploy.host.user','host_id','Users')
    group_ids = fields.One2many('deploy.host.group','host_id','Groups')
    cluster_ids = fields.One2many('deploy.pg.cluster','host_id','PG Clusters')
    control = fields.Boolean('Control')
    ip_forward = fields.Boolean('ip_forward')
    ssmtp_root = fields.Char("ssmtp_root", size=444)
    ssmtp_mailhub = fields.Char("ssmtp_mailhub", size=444)
    ssmtp_rewritedomain = fields.Char("rewritedomain", size=444)
    ssmtp_authuser = fields.Char("authuser", size=444)
    ssmtp_authpass = fields.Char("authpass", size=444)
        #'deploy_ids':fields.One2many('deploy.deploy','host_id','Deployments'),
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    
    _defaults ={
        'ip_forward':False,
        'ssmtp_mailhub':'mailhub=smtp.deliverhq.com:2525',
        }
class pg_cluster(models.Model):
    _name = "deploy.pg.cluster" #Postgresql Clusters
#    _rec_name = 'host_id'

    host_id = fields.Many2one('deploy.host','Hostname')
    port = fields.Integer('Port')
    version = fields.Char('Version',size=10)
    name = fields.Char('Name', size=20)
    description = fields.Char('Description',size=4444)
    active = fields.Boolean('Active')

    listen_addresses = fields.Char('listen_addresses',size=444)
    shared_buffers = fields.Char('shared_buffers',size=444)
    fsync = fields.Char('fsync',size=444)
    synchronous_commit = fields.Char('synchronous_commit',size=444)
    full_page_writes = fields.Char('full_page_writes', size=444)
    checkpoint_segments = fields.Char('checkpoint_segments',size=444)
    checkpoint_timeout = fields.Char('checkpoint_timeout',size=444)

    user_ids = fields.One2many("deploy.pg.user",'cluster_id','PG Users')
       # 'database_ids':fields.One2many("deploy.pg.database",'cluster_id','Databases'),
    hba_ids = fields.One2many("deploy.pg.hba",'cluster_id','HBA')
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    
    _defaults = {
        'listen_addresses':'127.0.0.1',
        'shared_buffers':'24MB',
        'fsync': 'off',
        'synchronous_commit':'off',
        'full_page_writes':'off',
        'checkpoint_segments':7,
        'checkpoint_timeout':'15min',       
        }

class pg_user(models.Model):
    _name="deploy.pg.user"
    _rec_name='login'
    _columns ={
    cluster_id = fields.Many2one('deploy.pg.cluster','PG Cluster')
    account_id = fields.Many2one('res.users','Account')
    password_id = fields.Many2one('deploy.password','PG Password')
    superuser = fields.Boolean('Superuser')
    create_db = fields.Boolean('Create db')
    create_role = fields.Boolean('Create Role')
    login = fields.Char('Login',size=44)
    type = fields.Selection([('real','real'),('virtual','virtual'),('system','system')],'Type' )
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
        }

class pg_hba(models.Model):
    _name = "deploy.pg.hba"

    name = fields.Char('Description', size=444)
    type = fields.Selection([('local','local'),('host','host'),('hostssl','hostssl'),('hostnossl','hostnossl')], 'Type' )
    database_ids = fields.Many2one('deploy.pg.database','database')
    cluster_id = fields.Many2one('deploy.pg.cluster','PG Cluster')
    user = fields.Many2one('deploy.pg.user','PG USER')
    address = fields.Char('address',size=444)
    ip_address = fields.Char('ip_address',size=444)
    ip_mask = fields.Char('ip_mask',size=444)
    auth_method = fields.Selection([('peer','peer'),('trust','trust'),('md5','md5')], 'auth_method')
    auth_options = fields.Char('auth_options',size=444)
        
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
}

class host_group(models.Model):
    _name = "deploy.host.group" #Host Groups
    _rec_name='name'
    _columns = {
    name = fields.Char('Name',size=100)
    gid = fields.Integer('GID')
    host_id = fields.Many2one('deploy.host','Host')
        'sftp':fields.Boolean('Allow SFTP'),        
    type = fields.Selection([('user','user'),('system','system')],'Type')
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    

class host_user(models.Model):
    _name = 'deploy.host.user' #Host User
    _rec_name='login'

    name = fields.Char('Name',size=100)
    login = fields.Char('Login',size=100)
    group_id = fields.Many2one('deploy.host.group','Main Group')
    password_id = fields.Many2one('deploy.password','Password')
    account_id = fields.Many2one('res.users','Account')
        #'owner_id':fields.Many2one('res.users','Owner'),
    uid = fields.Integer('UID')
    ssh = fields.Boolean('Allow SSH')
        'sudo_x':fields.Boolean('sudo_x'),    
    host_id = fields.Many2one('deploy.host','Host')
    home = fields.Char('home',size=44)
    shell = fields.Char('shell',size=44)
    type = fields.Selection([('user','user'),('system','system')],'Type')
    deploy_ids = fields.One2many('deploy.deploy','user_id','Deployments')
    app_ids = fields.Many2many('deploy.application', 'host_user_application_rel', 'user_id', 'app_id', 'Apps')
    validated_root = fields.Char('Validated ROOT',size=444)
    backup_subdir = fields.Char('backup_subdir', size=444)

    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
        #'user_id':fields.Many2one('deploy.host.user','HostUser'),
    
    def name_get2(self,cr, uid, ids, context=None):
        ret={}
        for u in self.browse(cr, uid, ids):
            if u.host_id:
                ret[u.id]="%s@%s"%(u.login,u.host_id.name)
        return ret
    _defaults = {
        'backup_subdir':'backups',

#Submenu: Applications
class repository(models.Model):
    _name = 'deploy.repository' #Repositories

    name = fields.Char('Name',size=100)
    delete = fields.Boolean('Delete')
    pull = fields.Boolean('Pull')
    push = fields.Boolean('Push')
    type = fields.Selection([('git','git'),('bzr','bzr'),('rsync','RSYNC')],'Type')
    use = fields.Selection([('addon','addon'),('server','server'),('scripts','scripts'),('site','site')],'Use')

        #
    remote_id = fields.Many2one('deploy.repository','Parent Repository')
    validated_addon_path = fields.Char('Validated Addon Path',size=444)
    local_user_id = fields.Many2one('deploy.host.user','Local user')

    host_id = fields.Many2one('deploy.host','Host')
    version = fields.Char('Version',size=10)
        #'remote_account_id':fields.Many2one('res.users','Remote Account'),
    remote_login = fields.Char('Remote Login',size=122)
    remote_location = fields.Char('Remote Location',size=1111)
        'remote_proto':fields.Selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        'remote_name':fields.Char('Remote Name',size=122), #used in git

	'local_location':fields.Char('Local Location',size=1111),
       
    branch = fields.Char('Branch',size=100)
    addon_subdir = fields.Char('Addon Subdir',size=100)
    is_module_path = fields.Boolean('Is Module Path')

    root_directory = fields.Char('Root Directory',size=100)
        #'clone_ids':fields.One2many('deploy.repository.clone','remote_id','Reposisoty Clones'),
    clone_ids = fields.One2many('deploy.repository','remote_id','Reposisoty Clones')
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
        }
    _defaults = {
        'delete':False,
        'push':True,
        'pull':True,
        }
#[root_directory, remote_host_id.name, local_location, remote_location]
class repository_clone(models.Model): #will be likely deprecated
    _name ='deploy.repository.clone' #Repository clones
#    _inherits = {'deploy.repository':'remote_id'}

    name = fields.Char('Name',size=100)
    owner_id = fields.Many2one('res.users','Owner')
    remote_id = fields.Many2one('deploy.repository','Repository')
    validated_addon_path = fields.Char('Validated Addon Path',size=444)
        #remote_host_id > remote_id.host_id
        #'remote_account_id':fields.Many2one('res.users','Remote Account'),
        #'remote_login':fields.Char('Remote Login',size=122),
        #'remote_location':fields.Char('Remote Location',size=1111),
        #'remote_proto':fields.Selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        #'remote_name':fields.Char('Remote Name',size=122), #used in git
       
	 #'local_host_id':fields.Many2one('deploy.host','Local host'),
        #'local_host_ids':fields.Many2many('deploy.host','repository_clone_host_rel','clone_id','host_id','Hosts'), 
    local_user_id = fields.Many2one('deploy.host.user','Local user')
    local_location = fields.Char('Local Locationi',size=1111)
    branch_db = fields.Char('Branch',size=100)
    addon_subdir_db = fields.Char('Addon Subdir',size=100)
    is_module_path_db = fields.Boolean('Is Module Path')
    root_directory = fields.Char('Root Directory',size=100)
        #'URL':fnc
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    

class application(models.Model):
    _name = 'deploy.application' #Applications

    repository_ids = fields.Many2many('deploy.repository', 'application_repository_rel','app_id','repository_id', 'Repositories', domain=[('remote_id','=',False)])
    name = fields.Char('Name',size=444)
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    

class options(models.Model):
    _name='deploy.options' #Server options

    unaccent = fields.Boolean('Unaccent')
    xmlrpc_interface = fields.Char('xmlrpc_interface',size=100)
    xmlrpc_port = fields.Integer('xmlrpc_port')
        #'admin_password':fields.Many2one('deploy.password','Admin Password'),
    name = fields.Char('Name',size=444)
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
        #'logfile':
    
    
class deploy(models.Model):
    _name='deploy.deploy' #Deployments

    application_id = fields.Many2one('deploy.application', 'Application')
    pg_user_id = fields.Many2one('deploy.pg.user','PG USER')
    options_id = fields.Many2one('deploy.options','Options')
    account_id = fields.Many2one('res.users','Account')
    password_id = fields.Many2one('deploy.password','Admin Password')
        #'clone_ids':fields.Many2many('deploy.repository', 'application_repository','app_id','repository_id', 'Repositories'),
    name = fields.Char('Name',size=444)
        #'host_id':fields.Many2one('deploy.host','Host'),#hostname
    user_id = fields.Many2one('deploy.host.user','HostUser')
        #'host_id_depr':fields.Many2one('deploy.host','HostDepr'),
        #'host_id':fields.Many2one('deploy.host','Host'),
    host_id = fields.Related('user_id', 'host_id',  string="Host",type="many2one",relation="deploy.host")
        #'ROOT':fields.Char('site_name',size=444),
    site_name = fields.Char('site_name',size=444)
    daemon = fields.Boolean('daemon')
    vhost = fields.Boolean('vhost')
    wsgi = fields.Boolean('wsgi')
    parse_config = fields.Boolean('parse_config')
    ServerName = fields.Char('ServerName',size=444)
    IP = fields.Char('IP',size=100)
        'PORT':fields.Integer('PORT'), 
    IPSSL = fields.Char('IP',size=100)
        'PORTSSL':fields.Integer('PORT'), 

    SSLCertificateFile = fields.Char('SSLCertificateFile',size=111)
    SSLCertificateKeyFile = fields.Char('SSLCertificateKeyFile',size=111)
    SSLCACertificateFile = fields.Char('SSLCACertificateFile', size=111)
    ssl = fields.Boolean('ssl')
    Redirect = fields.Char('Redirect',size=444)
    ProxyPass = fields.Char('ProxyPass',size=444)
    mode = fields.Selection([('dev','dev'),('live','live')],'Mode')
    validated_server_path = fields.Char('Validated Server Path',size=444)
    validated_config_file = fields.Char('Validated Config File',size=444)
    validated_root = fields.Char('Validated ROOT',size=444)
    db_ids = fields.One2many('deploy.pg.database','deploy_id',"db_ids")
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    

class pg_database(models.Model):
    _name="deploy.pg.database"

        'name':fields.Char("name",size=444),        
    type = fields.Selection([('live','live'),('virtual','virtual'),('system','system'),('demo','demo'),('snapshot','snapshot'),('replicated','replicated')], 'type')
    date = fields.Date('date')
    backup = fields.Boolean('backup needed')
        #'pg_user_id':fields.Many2one('deploy.pg.user','PG USER'),
    deploy_id = fields.Many2one('deploy.deploy','Deployments')
    pg_user_id = fields.Related('deploy_id', 'pg_user_id',  string="PG USER",type="many2one",relation="deploy.pg.user")
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        


class mako_template(models.Model):
    _name = "deploy.mako.template"

    name = fields.Char('name',size=444)
    type = fields.Selection([('template','template'),('bash','bash'),('python','python')],'Type' )
    gl_command = fields.Char('GoLive Command',size=444)
    model = fields.Char('model',size=444)
        'module':fields.Char('module',size=444), #to locate template
        'path':fields.Char('path', size=444),    #to locate template
        'fn':fields.Char('fn',size=4444),        #to locate template

    domain = fields.Char('domain',size=444)
    out_fn = fields.Char('out_fn',size=444)

    sequence = fields.Integer('Sequence')
    python_function = fields.Char('python_function',size=444)
    subprocess_arg = fields.Char('subprocess_arg',size=444)
    chmod = fields.Char('chmod',size=444)
    user_id = fields.Many2one('deploy.host.user','HostUser')
    target_user = fields.Char('target_user',size=444)
    target_group = fields.Char('target_group',size=444)
        
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")



class deploy_file(models.Model):
    _name = "deploy.file"
    _name_rec = "command"
    _columns = {
    command = fields.Char('Last Command',size=444)
        #'model':fields.Char('model',size=444),
    res_id = fields.Integer('res_id')
    template_id = fields.Many2one('deploy.mako.template', 'Template Used')
    encrypted = fields.Boolean('Encrypted')
        'user_id':fields.Many2one('deploy.host.user','User'),        
    sequence = fields.Integer('Sequence')
    file_written = fields.Char('File Written', size=444)
    content_written = fields.Text('Content Written')
    cmd_exit_code = fields.Char('cmd_exit_code', size=444)
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    
class export_tag(models.Model):
    _name = "deploy.export.tag"
    _columns ={
    name = fields.Char("name", size=100)
    sequence = fields.Integer('sequence')
    parent_id = fields.Many2one("deploy.export.tag", "Parent Tag")
    field_ids = fields_rel', 'tag_id', 'field_id', 'Tags')
        
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
        }
    _default = {
        'sequence':100,
        }

class ir_model(models.Model):
    _inherit = "ir.model"
    _order = "sequence"

    sequence = fields.Integer('Sequence')
    export_domain = fields.Char("Export Domain", size=500)
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    
    def name_get2(self,cr, uid, ids, context=None):
        ret={}
        for m in self.browse(cr, uid, ids):
            ret[m.id]="%s[%s]"%(m.name,m.model)
        return ret
    _default = {
        'sequence':100,
        'export_domain':'[]',
        }

class ir_model_fields(models.Model):
    _inherit = "ir.model.fields"
    _order = "sequence"

    sequence = fields.Integer('Sequence')
        'export_tag_ids':fields.Many2many('deploy.export.tag', 'deploy_export_tag_ir_model_fields_rel', 'field_id', 'tag_id', 'Export Tags'),        
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    
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
    for f,v in fields.Items():
        if f in field_list:
            f_map[f]=v
    fields = f_map
    #id_ref_ids = pool.get('ir.model.data').search(cr, uid, [('model','=',model)])   
    #ref_ids = [x.res_id for x in pool.get('ir.model.data').browse(cr, uid, id_ref_ids)]

    ids = pool.get(model).search(cr, uid, arg)

    header=[]
    header_export=['id']
    for f, v in fields.Items():
        if 'function' not in v:            
            if v['type'] in ['many2one', 'many2many']:
                if v['relation'] in ['account.account', 'account.journal']:
                    header_export.append( "%s/code" % f )
                #elif v['relation'] in ['account.tax']:
                #    header_export.append( "%s/description" % f )
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

class exported_file(models.Model):
    _name = "deploy.exported.file"
    _order = "sequence"

    path = fields.Char('path')
    fn = fields.Char('fn')
    model_id = fields.Many2one('ir.model','Model')
    company_id = fields.Many2one('res.company','Company')
    tag_id = fields.Many2one('deploy.export.tag', 'Export Tag')
    sequence = fields.Integer('sequence')
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    

class res_company(models.Model):
    _inherit = "res.company"

    export_module_name = fields.Char('Export Module Name', size=100)
    export_module_repo = fields.Char('Export Module Repository', size=100)
    exported_file_ids = fields.One2many('deploy.exported.file','company_id','Exported Files')
    secret_key = fields.Char("Secret Key")
    code = fields.Char("Code Stored")
    signature = fields.Text("Signature")
        
    
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
                    print path
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

class tag_wizzard(models.TransientModel):
    _name = 'deploy.export.tag.wizzard'
    _description="Export Tag"
    _columns ={
    tag_ids = fields.Many2many('deploy.export.tag', 'tag_wizzard_tag_rel', 'wiz_id', 'tag_id', 'Export Tags')
        #'name':fields.Char('Name', size=444),
        #'start_period': fields.Many2one('account.period','Start Period', required=True),
        #'end_period': fields.Many2one('account.period','End Period', required=True),        
        }
    def set_tags(self, cr, uid, ids, context=None):
        active_ids = context.get('active_ids', [])
        print active_ids
        for w in self.browse(cr, uid, ids):
            val={'export_tag_ids':[(6,0,[t.id for t in w.tag_ids])]}
            self.pool.get('ir.model.fields').write(cr, uid, active_ids, val, context=context)
            
        return True


