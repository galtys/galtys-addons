from osv import fields, osv
from openerp import netsvc
import openerp.addons.decimal_precision as dp


class host(osv.osv):
    _order = "name"
    _name = "appinstance.host"
    _columns = {
        'name':fields.char('Name', size=444),
        'app_ids':fields.many2many('appinstance.app', 'appinstance_app_host_rel', 'host_id', 'app_id', 'Apps'),
}
host()
class component_group(osv.osv):
    _order = "name"
    _name = "appinstance.component_group"
    _columns = {
        'name':fields.char('Name', size=444),
        'type':fields.selection([('openerp_server','OpenERP Server'),('openerp_addons','OpenERP Addons'), ('project', 'Project')],'Type'),
        }
component_group()

class app(osv.osv):
    _order = "name"
    _name = "appinstance.app"
    _columns = {
        'name':fields.char('Name', size=444),
        'description':fields.char('Description', size=444),
        #'parent_id': fields.many2one('appinstance.app', 'Parent App'),
        'host_ids':fields.many2many('appinstance.host', 'appinstance_app_host_rel', 'app_id','host_id', 'Hosts'),
        'component_ids':fields.many2many('appinstance.component', 'appinstance_component_app_rel', 'app_id', 'component_id', 'Components'),
        }
app()

class transport(osv.osv):
    _order = "name"
    _name = "appinstance.transport"
    _columns = {
        'name':fields.char('Name', size=444),
        'prot':fields.char('Prot', size=444),
        'user':fields.char('User', size=444),
        'host':fields.char('Host', size=444),
        'port':fields.char('Port', size=444),
        }
transport()

class component(osv.osv):
    _order = "name"
    _name = "appinstance.component"
    _columns = {
        'name':fields.char('Name', size=444),
        'path':fields.char('Path', size=444),
        'url_read':fields.char('URL Read', size=444),
        'vcs':fields.selection([('bzr','Bazaar')],'VCS'),
        'group_id':fields.many2one('appinstance.component_group', 'Component Group'),
        'transport_id':fields.many2one('appinstance.transport', 'Transport'),
        'transport_alt_id':fields.many2one('appinstance.transport', 'Transport'),
        'location':fields.char('Llocation',size=444),
        'app_ids':fields.many2many('appinstance.app', 'appinstance_component_app_rel', 'component_id', 'app_id', 'Apps'),       
        }
    _defaults = {
        'vcs': lambda obj, cr ,uid, context: 'bzr',
        'path': lambda obj, cr ,uid, context: '',

        }
component()
