import json
import csv
import StringIO
import os

#from protolib import add_OdooPB_group
#ssl._create_default_https_context = ssl._create_unverified_context

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT)
from protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,odoo_custom_pbfields
import protolib
#import pydir.odoopb_pb2

ODOOPB_PROTO='odoopb.proto'
SKIP_FIELDS=['create_uid','display_name','__last_update','write_uid','write_date','create_date']
def convert_fields(fields7, columns7):
    if 'id' not in fields7:
        id_def = {'readonly': True, 'type': 'integer', 'string': 'Id'}
        fields7['id'] = id_def
    #print 'erpmodel2dict', 'id' in fields7, fields7['id']
#    columns7=get_columns_from_db(env.cr, p._table)
    fields=[]
    for f_name, fdef in fields7.items():
        f_type=fdef.pop('type')
        f={'name':f_name,
           'indb': f_name in columns7,
           }
        fieldDef={}
        fieldDef['type'] = FieldTypesStr[f_type]
        if 'digits' in fdef:
            digits = fdef.pop('digits')
            if digits:
                precision,scale=digits
                fieldDef['digits']={'precision':precision,'scale':scale}
        if 'selection' in fdef:
            selection = fdef.pop('selection')
            sel=[]
            for s_name, s_label in selection:
                sel.append( {'label':s_label,'name':s_name} )
            fieldDef['selection']=sel
            fieldDef['selectable']=True
        #else:
        #    fieldDef['selectable']=False
        for fa,fv in fdef.items():
            if isinstance(fv, list) or isinstance(fv, dict) or isinstance(fv,tuple):
                fv=str(fv)
                
            if fa in ['store']: #TBD, does not work now
                if not fv:
                    fv=False
                elif isinstance(fv,str) and len(fv)>0:
                    fv=True                    
                elif isinstance(fv,str) and (not eval(fv)):
                    fv=False
                #print 'store: ', [fa,fv]
            #    if not fv:
            #        fv=''
                
            if fa not in ['readonly','required','invisible','selectable','change_default',
                          'translate','searchable','sortable','manual']:
                if fv in [False]:
                    fv=''
            elif isinstance(fv, int) and fv in [1,0]:
                if fv==1:
                    fv=True
                else:
                    fv=False
            if fa not in ['store']: #TBD, store does not work
                if fv not in [False, '']:
                    fieldDef[fa]=fv
        f['fieldDef'] = fieldDef #dict2pbdict(fieldDef)
        if f_name not in SKIP_FIELDS:
            fields.append(f)
    return fields

def get_columns_from_db(cr, table):
    cr.execute("select * from %s"%table+" LIMIT 0")
    cols=[desc[0] for desc in cr.description]
    return cols

def erpmodel2dict(p, cr, uid):
    m={'_name': p._name,
       '_description': p._description,
       '_transient': p._transient,
       '_table': p._table,
       '_sequence': p._sequence,
       #'_inherit' : str(p._inherit),
       #'_inherits':str(p._inherits),
    }
    fields7=p.fields_get(cr, uid)
    columns7=get_columns_from_db(cr, p._table)
    fields = convert_fields(fields7, columns7)
    m['_fields']=fields
    return m

def odoo2pbmsg_dict(pool, cr, uid, models):
    out=[]
    for model in models:
        model=pool.get(model)
        model_dict=erpmodel2dict(model,cr,uid)
        import pprint
        #pprint.pprint(model_dict)
        out.append( model_dict )
    out_dict = {'models':out}
    return out_dict

def odoo2pbmsg(pool, cr, uid, models):
    out_dict = odoo2pbmsg_dict(pool, cr, uid, models)
    registry_json = json.dumps( out_dict )
    return registry_json

def erpmodel2dict10(p, env):
    m={'_name': p._name,
       '_description': p._description,
       '_transient': p._transient,
       '_table': p._table,
       '_sequence': p._sequence,
       #'_inherit' : str(p._inherit),
       #'_inherits':str(p._inherits),
    }
    fields7=p.fields_get()
    columns7=get_columns_from_db(env.cr, p._table)
    fields = convert_fields(fields7, columns7)
    m['_fields']=fields
    return m

def odoo2pbmsg_dict10(env, models):
    out=[]
    for model in models:
        model=env[model] #pool.get(model)
        model_dict=erpmodel2dict10(model,env)
        #import pprint
        #pprint.pprint(model_dict)
        out.append( model_dict )
    out_dict = {'models':out}
    #import pprint
    #pprint.pprint(out_dict)
    return out_dict

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

def m2csv(m):
    header = ['name', 'string','type','relation','relation_field','required']
    data=[]
    #data.append(header)
    for f in m._fields:
        fname, fd = f.name, f.field_def
        row=[]
        row.append(fname)
        for h in header[1:]:
            if h == 'type':
                row.append( protolib.FieldDef_to_text[getattr( fd, h ) ] )
            elif getattr( fd, h ) in [False]:
                row.append( '' )
            else:
                row.append( getattr( fd, h )  )
        data.append(row)
    return header, data

ADOC_CSV_TABLE="""%s
[%%header,format=csv]
|===
%s|===
"""

def adoc_csv_table(csv_str,title=None, ref=None):
    def get_header(title,ref):
        out=[]
        if ref is not None:
            out.append('[[%s]]' % ref)
        elif title is not None:
            out.append('.%s'%title)
        return '\n'.join(out)
    h=get_header(title,ref)
    return ADOC_CSV_TABLE%(h, csv_str)

def csv_to_str(header, data):
    fp=StringIO.StringIO()
    wr=csv.writer(fp)
    wr.writerow(header)
    wr.writerows(data)
    val=fp.getvalue()
    fp.close()
    return val

def dict2row(HEADER,rec):
    out=[]
    for p in HEADER:
        #if p in rec:
        out.append(rec[p])
    return out

def records2table(records, HEADER=None):
    data=records
    #print data
    if len(data)>0:
        if HEADER is None:
            HEADER=data[0].keys()
    out=[dict2row(HEADER, x) for x in data]
    return HEADER,out

#def segment2csv(data, schema)
import google.protobuf.json_format
import importlib
import sys
import base64
def import_odoopb(opt):
    if opt.pydir not in sys.path:
        sys.path.append( opt.pydir )
    odoopb_module=importlib.import_module('odoopb_pb2')
    return odoopb_module
    
def segments2adoc(segments, fp, opt, schema):
    field_relation_map = protolib.relation_map(schema.registry)
    code2id_map={}
    odoopb = import_odoopb(opt)
    ODOO_OPS = [odoopb.UPDATE, odoopb.DELETE, odoopb.CREATE]
    ODOO_OPS_str = ['UPDATE','DELETE','CREATE']
    odoo_ops_map= dict( zip(ODOO_OPS,ODOO_OPS_str) )
    for (header, messages),model in zip(segments, schema.registry.models):
        js=google.protobuf.json_format.MessageToJson(header, including_default_value_fields=True, preserving_proto_field_name=True)
        #fp.write(js)
        out=[]
        operation=[]
        for (segh,msg) in zip(header.record,messages):
            
            js=google.protobuf.json_format.MessageToDict(msg, including_default_value_fields=True, preserving_proto_field_name=True)
            #d=google.protobuf.json_format.MessageToDict(msg, including_default_value_fields=True, preserving_proto_field_name=True)
            #sys.stderr.write( str(d) )
            #print js
            #fp.write(js)
            #print segh

            ret = protolib.pbdict2dbdict(model, js, opt, code2id_map, field_relation_map,fkcode=True)
            operation.append( segh.operation )
            if segh.operation==odoopb.SNAPSHOT:
                s256=base64.b64encode(segh.sha256)
                #print [ret]
                ret.update( {'sha256':s256} )
            elif segh.operation in ODOO_OPS:
                s256=base64.b64encode(segh.sha256)
                prev_s256=base64.b64encode(segh.prev_sha256)
                #print [ret]
                op_str=odoo_ops_map[segh.operation]
                ret.update( {'sha256':s256, 'prevsha256':prev_s256, 'OP':op_str} )
                
            out.append( ret )
        operation = set( operation )
        #print operation
        if len(operation)==1 and list(operation)[0]==odoopb.SNAPSHOT:
            header = get_pb_fields_to_store(model) + ['sha256']
        elif set(ODOO_OPS).intersection( operation ):
            header = get_pb_fields_to_store(model) + ['prevsha256','sha256','OP']
        else:
            header = get_pb_fields_to_store(model)
            
        if 'id' in header:
            header.pop( header.index('id') )
        if 'secret_key' in header:
            header.pop( header.index('secret_key') )
            
        header, data = records2table(out, HEADER=header)
        csv_str = csv_to_str(header, data)
        x = adoc_csv_table(csv_str, title='%s (%s)'%(model._description,model._name) )
        fp.write(x)
        fp.write('\n')
        #print header
        
        #print header
        #print out
    

def pbmsg2adoc(pbmsg, appname):
    out = StringIO.StringIO()
    
    for m in pbmsg.models:
        #cols_pb = get_pb_fields_to_store(m)
        #out = out +  get_proto_for_model(m, cols_pb)
        header, data = m2csv(m)
        csv_str = csv_to_str(header, data)
        x = adoc_csv_table(csv_str, title='%s (%s)'%(m._description,m._name) )
        out.write(x)
    return out.getvalue()

def get_odoopb_proto():
    path, fnxxx = os.path.split(__file__)
    proto_path = os.path.join(path, 'protodir')
    odoopb_proto = os.path.join(proto_path,  ODOOPB_PROTO)
    return proto_path, odoopb_proto
