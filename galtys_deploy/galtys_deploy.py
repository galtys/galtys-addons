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

class pg_user(osv.osv):
    _name="deploy.pg.user"
    _rec_name='login'
    _columns ={
        'cluster_id':fields.many2one('deploy.pg.cluster','PG Cluster'),
        'account_id':fields.many2one('deploy.account','Account'),
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
        'account_id':fields.many2one('deploy.account','Account'),
        'uid':fields.integer('UID'),
        'ssh':fields.boolean('Allow SSH'),
        'sudo':fields.boolean('Allow SFTP'),    
        'host_id':fields.many2one('deploy.host','Host'),
        'home':fields.char('home',size=44),
        'shell':fields.char('shell',size=44),
        'type':fields.selection([('user','user'),('system','system')],'Type'),
        'deploy_ids':fields.one2many('deploy.deploy','user_id','Deployments'),
        #'user_id':fields.many2one('deploy.host.user','HostUser'),
        }

#Submenu: Applications
class repository(osv.osv):
    _name = 'deploy.repository' #Repositories
    _columns = {
        'name':fields.char('Name',size=100),
        'type':fields.selection([('git','git'),('bzr','bzr'),('rsync','RSYNC')],'Type'),
        'host_id':fields.many2one('deploy.host','Host'),
        'version':fields.char('Version',size=10),
        'remote_account_id':fields.many2one('deploy.account','Remote Account'),
        'remote_login':fields.char('Remote Login',size=122),
        'remote_location':fields.char('Remote Location',size=1111),
        'remote_proto':fields.selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        'remote_name':fields.char('Remote Name',size=122), #used in git

	'local_location':fields.char('Local Location',size=1111),
       
        'branch':fields.char('Branch',size=100),
        'addon_subdir':fields.char('Addon Subdir',size=100),
        'is_module_path':fields.boolean('Is Module Path'),
        'root_directory':fields.char('Root Directory',size=100),
        'clone_ids':fields.one2many('deploy.repository.clone','remote_id','Reposisoty Clones'),
        }
#[root_directory, remote_host_id.name, local_location, remote_location]
class repository_clone(osv.osv):
    _name ='deploy.repository.clone' #Repository clones
    _columns = {
        'name':fields.char('Name',size=100),
        #'owner_id':fields.many2one('deploy.account','Owner'),
        'remote_id':fields.many2one('deploy.repository','Repository'),
        'validated_addon_path':fields.char('Validated Addon Path',size=444),
        #remote_host_id > remote_id.host_id
        'remote_account_id':fields.many2one('deploy.account','Remote Account'),
        'remote_login':fields.char('Remote Login',size=122),
        'remote_location':fields.char('Remote Location',size=1111),
        'remote_proto':fields.selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        'remote_name':fields.char('Remote Name',size=122), #used in git
       
	 #'local_host_id':fields.many2one('deploy.host','Local host'),
        'local_host_ids':fields.many2many('deploy.host','repository_clone_host_rel','clone_id','host_id','Hosts'), 
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
        'repository_ids':fields.many2many('deploy.repository', 'application_repository_rel','app_id','repository_id', 'Repositories'),
        'name':fields.char('Name',size=444),
        }

class options(osv.osv):
    _name='deploy.options' #Server options
    _columns = {
        'pg_user_id':fields.many2one('deploy.pg.user','PG USER'),
        'unaccent':fields.boolean('Unaccent'),
        'xmlrpc_interface':fields.char('xmlrpc_interface',size=100),
        'xmlrpc_port':fields.integer('xmlrpc_port'),
        'admin_password':fields.many2one('deploy.password','Admin Password'),
        'name':fields.char('Name',size=444),
        #'logfile':
        }
    
class deploy(osv.osv):
    _name='deploy.deploy' #Deployments
    _columns = {
        'application_id':fields.many2one('deploy.application', 'Application'),
        'account_id':fields.many2one('deploy.account','Account'),#not needed now
        'clone_ids':fields.many2many('deploy.repository.clone', 'application_repository_clone','app_id','clone_id', 'Repository Clones'),
        'name':fields.char('Name',size=444),
        #'host_id':fields.many2one('deploy.host','Host'),#hostname
        'user_id':fields.many2one('deploy.host.user','HostUser'),
        'host_id_depr':fields.many2one('deploy.host','HostDepr'),
        #'host_id':fields.many2one('deploy.host','Host'),
        'host_id':fields.related('user_id', 'host_id',  string="Host",type="many2one",relation="deploy.host"),
        'site_name':fields.char('site_name',size=444),
        'daemon':fields.boolean('daemon'),
        'vhost':fields.boolean('vhost'),
        'parse_config':fields.boolean('parse_config'),
        'options_id':fields.many2one('deploy.options','Options'),
        'ServerName':fields.char('ServerName',size=444),
        'IP':fields.char('IP',size=100), #get it from options ?
        'PORT':fields.integer('PORT'), #get it from options!
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
    }

class deploy_file(osv.osv):
    _name = "deploy.file"
    _columns = {
        'gl_command':fields.char('GoLive Command',size=444),
        'model':fields.char('model',size=444),
        'res_id':fields.integer('res_id'),
        'template_id':fields.many2one('deploy.mako.template', 'Template Used'),
        'encrypted':fields.boolean('Encrypted'),
        'user_id':fields.many2one('deploy.host.user','User'),        
    }

