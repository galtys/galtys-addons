# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp.osv import fields, osv
from lxml import etree

import datetime
import odoo2proto
from odoo2proto import odoo2pbmsg

class SkynetSettings(osv.osv):
    _name = "skynet.settings"
    _description = "Skynet Settings"
    
    _columns={
        'name':fields.char("Name"),
    }

class SkynetModel(osv.osv):
    _name = "skynet.schema.model"
    _order = "sequence"
    _columns = {
        'name':fields.char("name"),
        'sequence':fields.integer("sequence"),
        'model_id':fields.many2one("ir.model", "ERP MODEL"),
        'schema_id':fields.many2one("skynet.schema"),
        }
    
class SkynetSchema(osv.osv):
    _name = "skynet.schema"
    _description = "skynet.schema"

    _columns={
        'name':fields.char("Name"),
        'registry_json':fields.text("Registry Json"),
        'model_ids':fields.one2many("skynet.schema.model","schema_id","Schema Model"),
    }

    def store_registry_json(self, cr, uid, ids, context=None):

        for schema in self.browse(cr, uid, ids):
            models = []
            for sm in schema.model_ids:
                models.append( sm.model_id.model )
            registry_json = odoo2pbmsg(self.pool, cr, uid, models)
            schema.write( {"registry_json":registry_json} )
        

