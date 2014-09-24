from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp

#Main menu: Deploy

#Sub menu: Configuration
class deploy_account(osv.osv):
    _order = "name"
    _name = "deploy.account"  #Accounts
    _columns = {
        'name':fields.char('Name', size=444),
        #'app_ids':fields.many2many('appinstance.app', 'appinstance_app_host_rel', 'host_id', 'app_id', 'Apps'),
}
class deploy_password(osv.osv):
    _name = "deploy.password" #Passwords
    _name_rec='password'
    _columns = {
        'name':fields.char('Name',size=1000),
        'password':fields.char('Password',size=1000),#password encrypted
        }

class host(osv.osv):
    _name = "deploy.host"   #Hosts
    _columns = {
        'name':fields.char('Name',size=100),
        }

class pg_cluster(osv.osv):
    _name = "deploy.pg.cluster" #Postgresql Clusters
    _columns = {
        'host_id':fields.many2one('deploy.host','Hostname'),
        'port':fields.integer('Port'),
        'version':fields.char('Version',size=10),
        'name':fields.char('Name', size=20),
        }
class pg_user(osv.osv):
    _name="deploy.pg.user"
    _name_rec='login'
    _columns ={
        'cluster_id':fields.many2one('deploy.pg.cluster','PG Cluster'),
        'account_id':fields.many2one('deploy.account','Account'),
        'password_id':fields.many2one('deploy.password','PG Password'),
        'superuser':fields.boolean('Superuser'),
        'create_db':fields.boolean('Create db'),
        'create_role':fields.boolean('Create Role'),
        'login':fields.char('Login',size=44),
        }

class host_group(osv.osv):
    _name = "deploy.host.group" #Host Groups
    _columns = {
        'name':fields.char('Name',size=100),
        'gid':fields.integer('GID'),
        'host_id':fields.many2one('deploy.host','Host'),
        'sftp':fields.boolean('Allow SFTP'),        
        }

class host_user(osv.osv):
    _name = 'deploy.host.user' #Host User
    _columns = {
        'name':fields.char('Name',size=100),
        'login':fields.char('Login',size=100),
        'group_id':fields.many2one('deploy.host.group','Main Group'),
        'password_id':fields.many2one('deploy.password','Password'),
        'account_id':fields.many2one('deploy.account','Account'),
        'uid':fields.integer('UID'),
        'ssh':fields.boolean('Allow SSH'),
        'sudo':fields.boolean('Allow SFTP'),    
        'host_id':fields.many2one('deploy.host'),
        'home':fields.char('home',size=44),
        'shell':fields.char('shell',size=44),
        }

#Submenu: Applications
class repository(osv.osv):
    _name = 'deploy.repository' #Repositories
    _columns = {
        'name':fields.char('Name',size=100),
        'type':fields.selection([('git','git'),('bzr','bzr')],'Type'),
        'host_id':fields.many2one('deploy.host','Host'),
        'version':fields.char('Version',size=10),
        }
#[root_directory, remote_host_id.name, local_location, remote_location]
class repository_clone(osv.osv):
    _name ='deploy.repository.clone' #Repository clones
    _columns = {
        'name':fields.char('Name',size=100),
        'owner_id':fields.many2one('deploy.account','Owner'),
        'remote_id':fields.many2one('deploy.repository','Repository'),
        #remote_host_id > remote_id.host_id
        'remote_account_id':fields.many2one('deploy.account','Remote Account'),
        'remote_login':fields.char('Remote Login',size=122),
        'remote_location':fields.char('Remote Location',size=1111),
        'remote_proto':fields.selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https'),('ssh','ssh'),('lp','lp')],'Remote_Proto'),#not all supported
        'remote_name':fields.char('Remote Name',size=122), #used in git

        'local_host_id':fields.many2one('deploy.host','Local host'),
        'local_user_id':fields.many2one('deploy.host.user','Local user'),
        'local_location':fields.char('Local Locationi',size=1111),
        'branch':fields.char('Branch',size=100),
        'addon_subdir':fields.char('Addon Subdir',size=100),
        'is_module_path':fields.boolean('Is Module Path'),
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
        #'logfile':
        }
    
class deploy(osv.osv):
    _name='deploy.deploy' #Deployments
    _columns = {
        'application_id':fields.many2one('deploy.application'),
        'account_id':fields.many2one('deploy.account'),#not needed now
        'clone_ids':fields.many2many('deploy.repository.clone', 'application_repository_clone','app_id','clone_id', 'Repository Clones'),
        'name':fields.char('Name',size=444),
        'host_id':fields.many2one('deploy.host'),#hostname
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
        'mode':fields.selection([('dev','dev'),('live','live')]),

        }


