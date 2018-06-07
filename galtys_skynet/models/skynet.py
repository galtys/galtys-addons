# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import StringIO
from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

#import base58
#import ecdsa 

#from ecdsa import SECP256k1, SigningKey, VerifyingKey, BadSignatureError
import datetime
import bitcoin #bitcoin tools

#DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
#DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
#DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
#    DEFAULT_SERVER_DATE_FORMAT,
#    DEFAULT_SERVER_TIME_FORMAT)

import google.protobuf.json_format
import base64
import json
import pprint
from skynetlib.odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry
from skynetlib.protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,odoo_custom_pbfields
import skynetlib.odoo2proto as odoo2proto
from skynetlib.odoo2proto import get_odoopb_proto
#from odoo2proto import odoo2pbmsg

#for v8,v7
from odoo.modules.module import get_module_resource

from skynetlib.odoo2proto import pbmsg2proto, get_proto_for_model, get_pb_fields_to_store, odoo2pbmsg_dict10, erpmodel2dict10
   

class SkynetSettings(models.Model):
    _name = "skynet.settings"
    _description = "Skynet Settings"

    name = fields.Char("Name")
    odoopb_proto = fields.Text("odoopb proto")

    def load_odoopb_proto(self):        
        for settings in self:
            #fn=get_module_resource('galtys_skynet','models/protodir','odoopb.proto')
            proto_path, odoopb_proto=get_odoopb_proto()    
            settings.odoopb_proto = file(odoopb_proto).read()
            
class SkynetModel(models.Model):
    _name = "skynet.schema.model"
    _order = "sequence"

    name = fields.Char("name")
    sequence = fields.Integer("sequence")
    model_id = fields.Many2one("ir.model", "ERP MODEL")
    schema_id = fields.Many2one("skynet.schema", "Schema")
    skip = fields.Boolean("Skip")
    
class SkynetSchema(models.Model):
    _name = "skynet.schema"
    _description = "skynet.schema"

    name = fields.Char("Name")
    
    model_ids = fields.One2many("skynet.schema.model","schema_id","Schema Model")    
    settings_id = fields.Many2one("skynet.settings",string="Settings")
    
    registry_json = fields.Text("Registry Json")
    registry_dict = fields.Text("Registry dict")
    registry_pb = fields.Binary("Registry PB")
    registry_proto = fields.Text("Registry Proto")

    schema_json = fields.Text("Schema Json")
    schema_dict = fields.Text("Schema dict")
    schema_pb = fields.Binary("Schema PB")
    schema_proto = fields.Text("Schema Proto")

    def store_registry_json(self):
        mmf_map=odoo2proto.get_module_for_model_and_field()
        for schema in self:
            models = []
            for sm in schema.model_ids:
                models.append( sm.model_id.model )
            #print models
            uid = 1
            registry_dict = odoo2proto.odoo2pbmsg_dict10(self.env, models, mmf_map)
            registry_json = json.dumps( registry_dict )

            fp=StringIO.StringIO()
            pprint.pprint(registry_dict, stream=fp)
            
            registry_dict_pprint=fp.getvalue()            
            schema.registry_json = registry_json
            schema.registry_dict = registry_dict_pprint

            
            schema_dict = {'registry':registry_dict,
                           'schema_name': str(schema.name),
                           'app_name': str(schema.settings_id.name)}

            fp=StringIO.StringIO()
            pprint.pprint(schema_dict, stream=fp)            
            schema_dict_pprint=fp.getvalue()

            schema_json = json.dumps( schema_dict )
            schema.schema_dict = schema_dict_pprint
            schema.schema_json = schema_json
        
    def store_pb(self):
        for schema in self:
            pbmsg=google.protobuf.json_format.Parse(schema.registry_json, Registry() )           
            x=base64.b64encode( pbmsg.SerializeToString() )
            schema.registry_pb=x
    
    def store_proto(self):
        for schema in self:
            x=schema.registry_pb
            pbmsg=base64.b64decode( x )

            pbr = Registry()
            pbr.ParseFromString( pbmsg )
            
            registry_proto = pbmsg2proto(pbr, schema.settings_id.name)
            schema.registry_proto= registry_proto
            
    def add_code_column(self):
        
        for schema in self:
            x=schema.registry_pb
            pbmsg=base64.b64decode( x )

            pbr = Registry()
            pbr.ParseFromString( pbmsg )

            for m in pbr.models:
                cols=odoo2proto.get_columns_from_db(self.env.cr, m._table)

                if 'code' not in cols:
                    self.env.cr.execute("ALTER TABLE %s ADD COLUMN code varchar"%m._table)
                    #print cols
                #else:
                #    cr.execute("alter table %s drop column %s"%(m._table, 'code'))
                               
                if 'secret_key' not in cols:
                    self.env.cr.execute("ALTER TABLE %s ADD COLUMN secret_key varchar"%m._table)
                #else:
                #    cr.execute("alter table %s drop column %s"%(m._table, 'secret_key') )
        
    def init_code(self):
        import bitcoin
        import hashlib
        for schema in self:
            x=schema.registry_pb
            pbmsg=base64.b64decode( x )

            pbr = Registry()
            pbr.ParseFromString( pbmsg )
            if m._name not in ['res.country']:
                for m in pbr.models:
                    self.env.cr.execute("select res_id,name from ir_model_data where model=%s", (m._name,) )
                    ext_id_map=dict([x for x in self.env.cr.fetchall()])

                    self.env.cr.execute("select id from %s where code is Null"%m._table)
                    for rec in self.env.cr.fetchall():
                        id_=rec[0]
                        print 44*'_'
                        #print ext_id_map,[id_]
                        print ext_id_map,[id_, id_ in ext_id_map ]
                        if id_ in ext_id_map:
                            xml_name=ext_id_map[id_]
                            secret_key = hashlib.sha256(xml_name).hexdigest()
                        else:
                            secret_key = bitcoin.random_key()

                        pub_key = bitcoin.privtopub(secret_key)
                        code = bitcoin.pubtoaddr( pub_key )
                        sql_update="update %s set " % m._table

                        self.env.cr.execute( sql_update+"code=%s,secret_key=%s where id=%s", (code,secret_key,id_) )
                        
