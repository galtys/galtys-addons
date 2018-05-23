# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp.osv import fields, osv
from lxml import etree
import datetime
#import pydir
import StringIO

import base64
import json
import pprint
if 0:
  import google.protobuf.json_format
  from skynetlib.odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry
  from skynetlib.protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,odoo_custom_pbfields
  import skynetlib.odoo2proto as odoo2proto
#from odoo2proto import odoo2pbmsg

#for v8,v7
  from openerp.modules.module import get_module_resource
  from skynetlib.odoo2proto import pbmsg2proto, get_proto_for_model, get_pb_fields_to_store, odoo2pbmsg_dict, erpmodel2dict

class SkynetSettings(osv.osv):
    _name = "skynet.settings"
    _description = "Skynet Settings"
    
    _columns={
        'name':fields.char("Name"),
        'odoopb_proto':fields.text("odoopb proto"),
    }
    def load_odoopb_proto(self, cr, uid, ids, context=None):
        
        for settings in self.browse(cr, uid, ids):
            fn=get_module_resource('galtys_skynet','models/protodir','odoopb.proto')
            settings.write( {'odoopb_proto': file(fn).read() } )
            
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
        'model_ids':fields.one2many("skynet.schema.model","schema_id","Schema Model"),

        'settings_id':fields.many2one("skynet.settings",string="Settings"),
        'registry_json':fields.text("Registry Json"),
        'registry_dict':fields.text("Registry dict"),
        'registry_pb':fields.binary("Registry PB"),
        'registry_proto':fields.text("Registry Proto"),

        'schema_json':fields.text("Schema Json"),
        'schema_dict':fields.text("Schema dict"),
        'schema_pb':fields.binary("Schema PB"),
        'schema_proto':fields.text("Schema Proto"),

    }

    def store_registry_json(self, cr, uid, ids, context=None):

        for schema in self.browse(cr, uid, ids):
            models = []
            for sm in schema.model_ids:
                models.append( sm.model_id.model )
            print models
            registry_dict = odoo2proto.odoo2pbmsg_dict(self.pool, cr, uid, models)

            fp=StringIO.StringIO()
            pprint.pprint(registry_dict, stream=fp)            
            registry_dict_pprint=fp.getvalue()

            schema_dict = {'registry':registry_dict,
                           'schema_name': str(schema.name),
                           'app_name': str(schema.settings_id.name)}

            fp=StringIO.StringIO()
            pprint.pprint(schema_dict, stream=fp)            
            schema_dict_pprint=fp.getvalue()

            registry_json = json.dumps( registry_dict )
            schema_json = json.dumps( schema_dict )

            
            
            #print 'ocas', registry_dict_pprint, registry_dict
            schema.write( {"registry_json":registry_json,
                           "registry_dict":registry_dict_pprint,
                           "schema_dict":schema_dict_pprint,
                           "schema_json":schema_json} )
        
    def store_pb(self, cr, uid, ids, context=None):
        for schema in self.browse(cr, uid, ids):
            
            pbmsg=google.protobuf.json_format.Parse(schema.registry_json, Registry() )
            
            x=base64.b64encode( pbmsg.SerializeToString() )
            schema.write( {"registry_pb":x})
    
    def store_proto(self, cr, uid, ids, context=None):
        for schema in self.browse(cr, uid, ids):
            x=schema.registry_pb
            pbmsg=base64.b64decode( x )

            pbr = Registry()
            pbr.ParseFromString( pbmsg )
            
            registry_proto = pbmsg2proto(pbr, schema.settings_id.name)
            schema.write( {"registry_proto":registry_proto})
    def add_code_column(self, cr, uid, ids, context=None):
        
        for schema in self.browse(cr, uid, ids):
            x=schema.registry_pb
            pbmsg=base64.b64decode( x )

            pbr = Registry()
            pbr.ParseFromString( pbmsg )

            for m in pbr.models:
                cols=odoo2proto.get_columns_from_db(cr, m._table)

                if 'code' not in cols:
                    cr.execute("ALTER TABLE %s ADD COLUMN code varchar"%m._table)
                    #print cols
                #else:
                #    cr.execute("alter table %s drop column %s"%(m._table, 'code'))
                               
                if 'secret_key' not in cols:
                    cr.execute("ALTER TABLE %s ADD COLUMN secret_key varchar"%m._table)
                #else:
                #    cr.execute("alter table %s drop column %s"%(m._table, 'secret_key') )
        
    def init_code(self, cr, uid, ids, context=None):
        import bitcoin
        for schema in self.browse(cr, uid, ids):
            x=schema.registry_pb
            pbmsg=base64.b64decode( x )

            pbr = Registry()
            pbr.ParseFromString( pbmsg )

            for m in pbr.models:
                cr.execute("select id from %s where code is Null"%m._table)
                for rec in cr.fetchall():
                    id_=rec[0]
                    secret_key = bitcoin.random_key()
                    pub_key = bitcoin.privtopub(secret_key)
                    code = bitcoin.pubtoaddr( pub_key )
                    sql_update="update %s set " % m._table
                    cr.execute( sql_update+"code=%s,secret_key=%s where id=%s", (code,secret_key,id_) )
