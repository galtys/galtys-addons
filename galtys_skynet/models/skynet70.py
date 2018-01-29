# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp.osv import fields, osv
from lxml import etree
import datetime
#import pydir

import google.protobuf.json_format
import base64
import json
import pprint
from skynetlib.odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry
from skynetlib.protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,odoo_custom_pbfields
import skynetlib.odoo2proto as odoo2proto
#from odoo2proto import odoo2pbmsg

#for v8,v7
from openerp.modules.module import get_module_resource

def get_pb_fields_to_store(m):
    out=[]
    for f in m._fields:
        #fname, fd = f.name, f.field_def
        #fnct_field = has_att_list(fd, ['function', 'fnct_inv'])
        #r_field = fd.type in [FieldDef.SERIALIZED,FieldDef.FUNCTION,
        #                      FieldDef.MANY2MANY,FieldDef.ONE2MANY,
        #                      FieldDef.PROPERTY]
        #if (not fnct_field) and (not r_field):
        #        out.append(fname)
        if f.indb:
            out.append(f.name)
    return out
def get_proto_for_model(m, pb_fields_to_store=None):
    pb_model_name = m._table
    if pb_fields_to_store is None:
        pb_fields_to_store = []
    out="message %s {\n" % pb_model_name
    count=1
    for f in m._fields:
        fname, fd = f.name, f.field_def
        if fname in pb_fields_to_store:
                pb_type=erp_type_to_pb[fd.type]
                if fd.type in odoo_custom_pbfields:
                    pb_item = "   odoopb.%s %s = %d;\n" % (pb_type, fname, count)
                else:
                    pb_item = "   %s %s = %d;\n" % (pb_type, fname, count)
                out+=pb_item
                count+=1
    out+='} \n'
    return out


def pbmsg2proto(pbmsg, appname):
    out="""syntax = "proto3";
package %s;

import "odoopb.proto";

""" % appname
    for m in pbmsg.models:
        cols_pb = get_pb_fields_to_store(m)
        out = out +  get_proto_for_model(m, cols_pb)
    return out

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
        'settings_id':fields.many2one("skynet.settings",string="Settings"),
        'registry_json':fields.text("Registry Json"),
        'registry_dict':fields.text("Registry dict"),
        'model_ids':fields.one2many("skynet.schema.model","schema_id","Schema Model"),
        'registry_pb':fields.binary("Registry PB"),
        'registry_proto':fields.text("Registry Proto"),
    }

    def store_registry_json(self, cr, uid, ids, context=None):

        for schema in self.browse(cr, uid, ids):
            models = []
            for sm in schema.model_ids:
                models.append( sm.model_id.model )
            print models
            registry_dict = odoo2proto.odoo2pbmsg_dict(self.pool, cr, uid, models)
            registry_json = json.dumps( registry_dict )
            import StringIO
            fp=StringIO.StringIO()
            pprint.pprint(registry_dict, stream=fp)
            
            registry_dict_pprint=fp.getvalue()
            
            print 'ocas', registry_dict_pprint, registry_dict
            schema.write( {"registry_json":registry_json,
                           "registry_dict":registry_dict_pprint} )
        
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
