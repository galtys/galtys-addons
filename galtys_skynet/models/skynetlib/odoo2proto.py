import json
#from protolib import add_OdooPB_group
#ssl._create_default_https_context = ssl._create_unverified_context

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT)
from protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,odoo_custom_pbfields

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
        else:
            fieldDef['selectable']=False
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
                fieldDef[fa]=fv
        f['fieldDef'] = fieldDef #dict2pbdict(fieldDef)
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

