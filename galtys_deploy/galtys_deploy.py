from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp

class deploy_account(osv.osv):
    _order = "name"
    _name = "deploy.account"
    _columns = {
        'name':fields.char('Name', size=444),
        #'app_ids':fields.many2many('appinstance.app', 'appinstance_app_host_rel', 'host_id', 'app_id', 'Apps'),
}
class deploy_password(osv.osv):
    _name = "deploy.password"
    _name_rec='password'
    _columns = {
        'name':fields.char('Name',size=1000),
        'password':fields.char('Password',size=1000),#password encrypted
        }

class host(osv.osv):
    _name = "deploy.host"
    _columns = {
        'name':fields.char('Name',size=100),
        }

class pg_cluster(osv.osv):
    _name = "deploy.pg.cluster"
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
    _name = "deploy.host.group"
    _columns = {
        'name':fields.char('Name',size=100),
        'gid':fields.integer('GID'),
        'host_id':fields.many2one('deploy.host','Host'),
        'sftp':fields.boolean('Allow SFTP'),        
        }

class host_user(osv.osv):
    _name = 'deploy.host.user'
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

class repository(osv.osv):
    _name = 'deploy.repository'
    _columns = {
        'name':fields.char('Name',size=100),
        'type':fields.selection([('git','git'),('bzr','bzr')],'Type'),
        'version':fields.char('Version',size=10),
        }
#[root_directory, remote_host_id.name, local_location, remote_location]
class repository_clone(osv.osv):
    _name ='deploy.repository.clone'
    _columns = {
        'name':fields.char('Name',size=100),
        'owner_id':fields.many2one('deploy.account','Owner'),
        'remote_id':fields.many2one('deploy.repository','Repository'),

        'remote_host_id':fields.many2one('deploy.host','Remote Host'),
        'remote_account_id':fields.many2one('deploy.account','Remote Account'),
        'remote_login':fields.char('Remote Login',size=122),
        'remote_location':fields.char('Remote Location',size=1111),
        'proto':fields.selection([('git','git'),('bzr+ssh','bzr+ssh'),('http','http'),('https','https')],'Proto'),
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
    _name = 'deploy.application'
    _columns = {
        'repository_ids':fields.many2many('deploy.repository', 'application_repository_rel','app_id','repository_id', 'Repositories'),
        'name':fields.char('Name',size=444),
        }

class options(osv.osv):
    _name='deploy.options'
    _columns = {
        'pg_user_id':fields.many2one('deploy.pg.user','PG USER'),
        'unaccent':fields.boolean('Unaccent'),
        'xmlrpc_interface':fields.char('xmlrpc_interface',size=100),
        'xmlrpc_port':fields.integer('xmlrpc_port'),
        'admin_password':fields.many2one('deploy.password','Admin Password'),
        #'logfile':
        }
    
class deploy(osv.osv):
    _name='deploy.deploy'
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

            res[d.id]={'options':str(OPTIONS),
                       'db_password':d.options_id.pg_user_id.password_id.password,
                       'admin_password':d.options_id.admin_password.password,
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
        'db_password':fields.function(_get, type='char', size=1000,multi='options',method=True),
        'admin_password':fields.function(_get, type='char', size=1000,multi='options',method=True),
        #'git_clone':fields.function(_get_url, type='char', size=1000,multi='url',method=True),
        #'mkdir':fields.function(_get_url, type='char', size=1000,multi='url',method=True),
        #'type':fields.function(_get_url, type='char', size=1000,multi='url',method=True),
        #'local_location_fnc':fields.function(_get_url, type='char', size=1000,multi='url',method=True),
        }
