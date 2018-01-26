# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp.osv import fields, osv
from lxml import etree

import datetime
    
class SkynetSettings(osv.osv):
    _name = "skynet.settings"
    _description = "Skynet Settings"
    
    _columns={
        'name':fields.char("Name"),
    }

class SkynetModel(osv.osv):
    _name = "skynet.schema.model"
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
        'model_ids':fields.one2many("skynet.schema.model","schema_id","Schema Model"),
    }


