from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp

class repository_clone(osv.osv):
    _inherit = "deploy.repository.clone"
    def _get_url(self, cr, uid, ids,field_name,arg, context=None):
        res={}
        for clone in self.browse(cr, uid, ids):
            print [clone.name, clone.owner_id.name]
            res[clone.id]={'url':'blabla'}
        return res
    _columns = {
        'url':fields.function(_get_url, type='char', multi='url'),
        }
