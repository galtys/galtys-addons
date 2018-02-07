import sys
import optparse
import os
import subprocess
import smtplib
#from gtclib import golive
#DEPLOYMENT_NAME='pjbrefct'
#DEPLOYMENT_NAME='app_deployments'
import datetime
import hashlib
import ssl
import json
import StringIO
import google.protobuf.json_format
import hashlib
import base64
import time
import psycopg2
import logging

from skynetlib.protolib import add_OdooPB_group
import lsb_release_ex
lsb_info = lsb_release_ex.get_lsb_information()
if lsb_info['RELEASE'] in ['16.04']:
    ssl._create_default_https_context = ssl._create_unverified_context

from skynetlib.protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,traverse_preorder,get_output_file,get_input_file
import skynetlib.protolib as protolib
from skynetlib.odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry,Magic,Header, Schema
import skynetlib.odoopb_pb2 as odoopb    

from skynetlib.odoo2proto import pbmsg2proto

def has_att_list(fd, att_list=None): #OR
    if att_list is None:
        att_list = []
    ret=False
    for f,no in fd.ListFields():
        if f.name in att_list:
            ret=True
            break
    return ret

def get_pb_fields_to_hash(m):
    out=[]
    for f in m._fields:
        fname, fd = f.name, f.field_def
        #print [fname, f.indb]
        fnct_field = has_att_list(fd, ['function', 'fnct_inv'])
        r_field = fd.type in [FieldDef.SERIALIZED,FieldDef.FUNCTION,
                              FieldDef.MANY2MANY,FieldDef.ONE2MANY,
                              FieldDef.PROPERTY]
        if (not fnct_field) and (not r_field):
            if f.indb:
                out.append(fname)
    #print 'parent_id' in out, out
    return out
def get_parent_fields(m): #ie fields that point toitself as many2one rel
    out=[]
    for f in m._fields:
        fname, fd = f.name, f.field_def
        if fd.type in [FieldDef.MANY2ONE]:
            #print fd
            relation=fd.relation
            if m._name == relation:
                out.append(fname)
    return out


def read_by_code(cr, _table, cols, code):
    cols_sql = ','.join(cols)
    sql = "select %s from %s where code = '%s'" % (cols_sql, _table, code )
    cr.execute(sql)
    ret = [x for x in cr.fetchall()]
    assert len(ret)==1
    return ret
def update_record(cr, _table, val, code, mysql=True):
    sql_update = "update %s " % _table
    sql_set = []
    par=[]
    
    for k,v in val.items():
        if not mysql:
            s = ' "%s" = '%k +  " %s "
        else:
            s = ' %s = '%k +  " %s "
        sql_set.append( s )
        par.append(v)
    where = " where code = %s "
    sql = sql_update + "set "+ ",".join(sql_set) +where
    arg = par + [code]
    #print sql, arg
    #print [sql, arg]
    cr.execute(sql, arg)
    
    #b=google.protobuf.json_format.MessageToJson(r, including_default_value_fields=True, preserving_proto_field_name=True)
    #c=json.loads(b)
    #msg=google.protobuf.json_format.Parse(xxjson, Registry() )
def insert_record(cr, _table, val):
    sql_insert = "insert into %s " % _table
    sql_set = []
    par=[]
  
    cols, vals = zip(*val.items())
    cols_quote=['"%s"'%c for c in cols]
    cols_sql = ','.join(cols_quote)

    vals_sql = ",".join( [ '%s' for i in range( len(vals) ) ] )
#        s = ' "%s" = '%k +  " %s "
 #       sql_set.append( s )
  #      par.append(v)
#    where = " where code = %s "
    sql = sql_insert + " (%s) "%cols_sql + "values (%s) " % vals_sql 
    arg = vals
    #print sql
    cr.execute(sql, arg)
    
    #b=google.protobuf.json_format.MessageToJson(r, including_default_value_fields=True, preserving_proto_field_name=True)
    #c=json.loads(b)
    #msg=google.protobuf.json_format.Parse(xxjson, Registry() )

def read_sql(cr, _table, cols, ids=None, limit='', offset='', mysql=False):
    #print _table, cols
    if ids is None:
        where = ''
    elif isinstance(ids, list):
        where = " where id in (%s)" % ",".join(ids)
    else:
        where = " where id=%s" % ids
    if not mysql:
        cols_quote=['"%s"'%c for c in cols]
    else:
        cols_quote=['%s'%c for c in cols]
    cols_sql = ','.join(cols_quote)
    #print [cols_sql]
    sql="select %s from %s"%(cols_sql,_table) + where + offset + limit
    #print sql
    cr.execute(sql)
    ret = [x for x in cr.fetchall()]
    records=[]
    for r in ret:
        records.append( dict(zip(cols,r)) )
    return records

def read_from_db(cr, m, limit=' limit 80', mysql=True):
    cols_hash = get_pb_fields_to_hash(m)
    retsql = read_sql(cr, m._table, cols_hash, limit=limit, mysql=True)
    return retsql

import mysql.connector
def get_connection(opt,dbname):
    _logger = logging.getLogger(__name__)
    import ConfigParser
    Config=ConfigParser.ConfigParser()
    _logger.debug("get database connection")
    _logger.debug("  reading hashsync config file: %s", opt.config)
    Config.read(opt.config)
    sections = Config.sections()
    def split_dbname(dbname):
        ret=dbname.split('.')
        if len(ret)==1:
            return 'pg', dbname
        else:
            return ret
    def get_conn(cfg, section, tp=None, dbname=None):
        db_host = Config.get(section,'db_host')
        db_port = Config.get(section,'db_port')
        db_user = Config.get(section,'db_user')
        db_password = Config.get(section,'db_password')
        if tp is None:
            db_type=Config.get(section,'type')
        else:
            db_type=tp
            
        if dbname is None:
            database=Config.get(section, 'database')
        else:
            database=dbname
            
        if (db_type == 'mysql'):
            conn = mysql.connector.connect(user=db_user,password=db_password,
                                           host=db_host, database=database)
        else:
            dsn="dbname='%s' user='%s' port='%s' host='%s' password='%s'"%(database,db_user,db_port,db_host,db_password)
            _logger.debug("  psycopg2.connect, dsn: %s", dsn)
            conn = psycopg2.connect(dsn)
        return conn
    
    tp,db=split_dbname(dbname)
    _logger.debug("  sections in config file: %s", sections)
    _logger.debug("  split_dbname, tp: %s, db: %s", tp, db)
    if db in sections:
        _logger.debug("    db_in_sections")
        conn=get_conn(Config, dbname)
    elif tp=='mysql':
        conn=get_conn(Config, 'mysql', tp='mysql', dbname=dbname)
    elif tp=='pg':
        conn=get_conn(Config, 'pg', tp='pg', dbname=dbname)
    return conn, tp

def get_connection_mysql():
    import mysql.connector
    conn = mysql.connector.connect(user='root',password='mysql123',
                                   host='127.0.0.1',
                                   database='pjb_no_tr_data')
    return conn

def next_id(cr, sequence):
    cr.execute("select nextval('%s') " % sequence)
    ret=[x[0] for x in cr.fetchall()]
    return ret[0]

def op_diff(opt, stack):
    #DEPLOYMENT_NAME=opt.deployment_name
    _logger = logging.getLogger(__name__)
    schema = parse_schema_stack_arg(opt,stack)    
    schema_name=schema.schema_name

    _logger.debug("op_diff, schema_name: %s", schema_name)
    #fp=sys.stdin
    a1=stack.pop()
    _logger.debug("  read %s bytes from stack", len(a1) )
    a2=stack.pop()
    _logger.debug("  read %s bytes from stack", len(a2) )
    
    fp=StringIO.StringIO(a1+a2)   
    segments = protolib.stream2pb(opt,fp, schema_name)
    fp.close()
    
    seg=protolib.pb2op(segments, opt)
    _logger.debug("  converted to seg, len: %s", len(seg) )
    fp=StringIO.StringIO()
    protolib.segments2file(seg, fp)
    ret=fp.getvalue()
    _logger.debug("  push %s bytest to stack", len(ret) )
    stack.push(ret)
    fp.close()
    push_schema_stack(opt, stack, schema)
    #sys.stdout.close()    
    
def op_json(opt, stack):
    _logger = logging.getLogger(__name__)

    #DEPLOYMENT_NAME=opt.deployment_name
    schema = parse_schema_stack_arg(opt, stack)    
    schema_name=schema.schema_name

    data_in = stack.pop()


    fp=StringIO.StringIO( data_in )

    _logger.debug("running op_json with %s bytes in, schema_name: %s", len(data_in), schema_name)
    
    segments = protolib.stream2pb(opt,fp, schema_name)
    fp.close()

    fp=StringIO.StringIO()
    protolib.segments2json(segments, fp, opt)
    ret=fp.getvalue()
    stack.push( ret  )
    #push_schema_stack(opt, stack, schema)
    _logger.debug("  converted to json, bytes to stack: %s", len(ret) )

def op_proto(opt, stack):
    _logger = logging.getLogger(__name__)
    
    dbname=stack.pop()
    appname=stack.pop()
    _logger.debug("op_proto(dbname: %s, appname: %s)", dbname, appname)
    conn,tp=get_connection(opt, dbname)
    assert tp=='pg'
    #appname='pjbrefct'
    cr=conn.cursor()

    if not os.path.isdir(opt.protodir):
        _logger.debug("   os.makedirs %s", opt.protodir )
        os.makedirs(opt.protodir)
    if not os.path.isdir(opt.pydir):
        os.makedirs(opt.pydir)
    if not os.path.isdir(opt.pbdir):
        os.makedirs(opt.pbdir)

    odoo_proto_fn = os.path.join( opt.protodir, 'odoopb.proto' ) 

    cr.execute("select id,odoopb_proto from skynet_settings where name=%s",(appname,) )
    ret=[x for x in cr.fetchall()]
    _logger.debug("project name %s, number of skynet_settings records in db %s",appname,len(ret))
    assert len(ret)==1
    settings_id,odoopb_proto = ret[0]
    #if not os.path.isfile( odoo_proto_fn):
    if odoopb_proto:
        file( odoo_proto_fn, 'wb').write( odoopb_proto )
        arg=['protoc', '--proto_path=%s'%opt.protodir, '--python_out=%s'%opt.pydir, odoo_proto_fn]
        subprocess.call(arg)

    cr.execute("select ss.name,ss.registry_proto,ss.registry_pb from skynet_schema ss,skynet_settings sset where ss.settings_id=sset.id and sset.id=%s", (settings_id,) )
    ret = [x for x in cr.fetchall()]

    for name,registry_proto,registry_pb in ret:
        fn = os.path.join( opt.protodir, name+'.proto' )
        _logger.debug("schema: %s, writing proto file: %s", name, fn)
        file(fn,'wb').write(registry_proto)

        arg=['protoc', '--proto_path=%s'%opt.protodir, '--python_out=%s'%opt.pydir, fn]
        
        if opt.protoc=='yes':
            #print
            #print 'Running:'
            #print " ".join(arg)
            _logger.debug("running: %s", ' '.join(arg)) 
            subprocess.call(arg)

            py_init_fn=os.path.join( opt.pydir, '__init__.py' )
            if not os.path.isfile(py_init_fn):
                file(py_init_fn, 'wb').write('')

        fn = os.path.join( opt.pbdir, name+'.pb' )
        pbmsg=base64.b64decode( registry_pb )
        file(fn,'wb').write(pbmsg)
    
def op_init(opt, stack):
    #schema_name=opt.deployment_name
    
    dbname=stack.pop()
    conn,tp=get_connection(opt, dbname)
    assert tp=='pg'
    cr=conn.cursor()

    pb_fn = os.path.join(opt.pbdir, schema_name + '.pb' )
    pbr = Registry()
    pbr.ParseFromString( file(pb_fn).read() )
    import bitcoin

    for m in pbr.models:
        cr.execute("select id from %s where code is Null"%m._table)
        for rec in cr.fetchall():
            id_=rec[0]
            secret_key = bitcoin.random_key()
            pub_key = bitcoin.privtopub(secret_key)
            code = bitcoin.pubtoaddr( pub_key )
            sql_update="update %s set " % m._table
            cr.execute( sql_update+"code=%s,secret_key=%s where id=%s", (code,secret_key,id_) )
    cr.close()
    conn.commit()

def get_local_file_names(opt, schema_name ):
    proto_path, odoopb_proto=get_odoopb_proto()
    schema_proto = os.path.join(opt.protodir, schema_name + '.proto' )
    local_odoopb_proto = os.path.join(opt.protodir, ODOOPB_PROTO )
    schema_pb = os.path.join(opt.pbdir, schema_name + '.pbs' )    
    return odoopb_proto, local_odoopb_proto, schema_proto, schema_pb

def schemaseg2local(opt, schemaseg):
    _logger = logging.getLogger(__name__)
    schema = protolib.stream2schema(opt, StringIO.StringIO(schemaseg) )
    schema_name = schema.schema_name
    _logger.debug("schemaseg2local: schema_name: %s", schema_name )
    
    reg_proto = pbmsg2proto(schema.registry, schema_name)
    odoopb_proto, local_odoopb_proto, schema_proto, schema_pb = get_local_file_names(opt, schema_name )
    _logger.debug("  odoopb_proto: %s", odoopb_proto)
    _logger.debug("  local_odoopb_proto (copy of odoopb_proto): %s", local_odoopb_proto)
    _logger.debug("  schema_proto: %s", schema_proto)
    _logger.debug("  schema_pb: %s", schema_pb)
    #
    arg=['cat', schema_pb,'|', 'protoc','--proto_path=%s'%opt.protodir,  '--decode=Schema', local_odoopb_proto]    
    _logger.debug(" ".join(arg))
             
    file(local_odoopb_proto,'wb').write(  file(odoopb_proto).read() )

    arg=['protoc', '--proto_path=%s'%opt.protodir, '--python_out=%s'%opt.pydir, local_odoopb_proto]
    _logger.debug(" ".join(arg))
    subprocess.call(arg)

    arg=['protoc', '--proto_path=%s'%opt.protodir, '--python_out=%s'%opt.pydir, schema_proto]
    _logger.debug(" ".join(arg))
    subprocess.call(arg)

    _logger.debug(" writing schema_pb")
    file( schema_pb,'wb').write( schema.SerializeToString() )

def parse_schema_stack_arg(opt,stack):
    _logger = logging.getLogger(__name__)
    if opt.localschema in ['no']:
        _logger.debug("  expecting schema_segment on stack")
        schema_seg = stack.pop()
        schema = protolib.stream2schema(opt, StringIO.StringIO(schema_seg) )
    else:
        _logger.debug("  expecting schema_name on stack")
        schema_name = stack.pop()
        odoopb_proto, local_odoopb_proto, schema_proto, schema_pb = get_local_file_names(opt, schema_name )
        if os.path.isfile(schema_pb):
            schema_data = file(schema_pb).read()
            schema= Schema()
            schema.ParseFromString(schema_data)
        else:
            _logger.error("  could not read schema_pb: %s", schema_pb)
            _logger.error("  can not continue, sys.exit(1)")
            sys.exit(1)
    return schema
def push_schema_stack(opt, stack, schema):
    _logger = logging.getLogger(__name__)
    schema_data = schema.SerializeToString()
    schema_name = schema.schema_name
    if opt.localschema in ['no']:    
        _logger.debug("pushing schema back to stack, %s bytes", len(schema_data) )
        stack.push(schema_data)
    else:
        _logger.debug("pusching schema_name %s to stack", schema_name )
        stack.push(schema_name)
    
def op_snapshot(opt, stack):
    _logger = logging.getLogger(__name__)
    dbname=stack.pop()
    _logger.debug("running op_snapshot dbname:%s", dbname)
    schema = parse_schema_stack_arg(opt,stack)    
    schema_name=schema.schema_name
    
    conn,tp=get_connection(opt, dbname)
    cr=conn.cursor()
    pbr = schema.registry
    hash_map = {}
    id2code_map = {}
    data=[]
    fp=StringIO.StringIO()
    for m in pbr.models:
        id_map=id2code_map.setdefault(m._name, {})
        if tp=='mysql':
            mysql=True
        else:
            mysql=False
        records=read_from_db(cr, m, limit='', mysql=mysql)
        for r in records:
            id_map[ r['id'] ] = r['code']
        #if len(parents)>0:
        #    records2 = traverse_preorder(records, parent_field = parents[0], key_field='id')
        #    pb_messages2=protolib.serialize_records(m, records2, opt, hash_map, id2code_map)
        #    #for pb_m2 in pb_messages2: 
        #print records[0]['parent_id']
        #sys.stderr.write( str(records) )
        pb_messages=protolib.serialize_records(m, records,opt, hash_map, id2code_map, appname=schema_name)
        #data.append(pb_messages)
        pbstream = protolib.pb2stream(m, pb_messages, schema_name=schema_name)
        fp.write( pbstream )   
    
    cr.close()
    conn.commit()
    ret=fp.getvalue()
    fp.close()
    _logger.debug("pushing data segments, %s bytes onto stack", len(ret) )
    stack.push(ret)
    push_schema_stack(opt, stack, schema)
    
def op_deleteall(opt, stack):
    dbname=stack.pop()
    schema_name=opt.deployment_name
                
    conn,tp=get_connection(opt, dbname)
    cr=conn.cursor()
    pb_fn = os.path.join(opt.pbdir, schema_name + '.pb' )
    pbr = Registry()
    pbr.ParseFromString( file(pb_fn).read() )
    #pbr_map = dict( [ (m._name, m) for m in pbr.models] )
    for m in pbr.models:
        #print [header.model, header._sequence]
        sql = "delete from %s" % m._table
        if m._name == 'res.company':
            continue
        cr.execute(sql )
    cr.close()
    conn.commit()
    
def op_apply(opt, stack):
    dbname=stack.pop()
    schema_name=opt.deployment_name
                
    conn,tp=get_connection(opt, dbname)
    cr=conn.cursor()
    pb_fn = os.path.join(opt.pbdir, schema_name + '.pb' )
    pbr = Registry()
    pbr.ParseFromString( file(pb_fn).read() )
    pbr_map = dict( [ (m._name, m) for m in pbr.models] )

    field_relation_map = protolib.relation_map(pbr)
                
    fp=StringIO.StringIO( stack.pop() )
    segments = protolib.stream2pb(opt,fp, schema_name)
    fp.close()
    #print segments
    ret = protolib.segments2dict(segments)
    #print ret
    import pprint
    code2id_map = {}
    for m in pbr.models:
        #print [header.model, header._sequence]
        v = code2id_map.setdefault( m._name, {})
        cr.execute("select code,id from %s" % m._table)
        vout=dict( [x for x in cr.fetchall()] )
        v.update( vout )
    #print code2id_map
    #print ret
    for header, msg_dicts in ret:
        m=pbr_map[ header.model ]
        #print 'update', msg_dicts
        #print [header.model, header._sequence]
        v = code2id_map.setdefault( header.model, {})
        if m._name == 'res.company':
            continue
        parents = get_parent_fields(m)
        if parents:
            #assert len(parents)==1
            out=[]
            parent_field = parents[0]
            records2 = traverse_preorder(msg_dicts, parent_field = parent_field,
                                         key_field='code',parent_field_option='code')
        else:
            records2 = msg_dicts
        op_map={}
        for record in header.record:
            op_map[record.code] = record.operation

        for msg in records2:                
        #for record,msg in zip(header.record, records2):
            code=msg['code']
            secret_key=msg['secret_key']
            if op_map[code] == odoopb.CREATE:
                if tp=='mysql':
                    ret = protolib.pbdict2dbdict(m, msg, opt, code2id_map, field_relation_map)
                    insert_record(cr, m._table, ret)
                    cr.execute("select last_insert_id()")
                    ret_id = [x[0] for x in cr.fetchall()]
                    v[code] = ret_id
                else:
                    ret_id = next_id(cr, header._sequence)
                    val = { 'id':ret_id }
                    v[code] = ret_id
                    ret = protolib.pbdict2dbdict(m, msg, opt, code2id_map, field_relation_map)
                    ret.update(val)
                    insert_record(cr, m._table, ret)

            elif op_map[code] == odoopb.UPDATE:
                ret = protolib.pbdict2dbdict(m, msg, opt, code2id_map, field_relation_map)
                mysql = tp=='mysql'
                update_record(cr, m._table, ret, code, mysql=mysql)
            elif op_map[code] == odoopb.DELETE:
                ret_id = code2id_map[ header.model ] [code]
                sql = "delete from %s " % m._table
                cr.execute( sql + "where id=%s", (ret_id, ))
    cr.close()
    conn.commit()
    
def op_in(opt, stack):
    #schema_name=opt.deployment_name
    fp=sys.stdin
    #segments = protolib.stream2pb(opt,fp, schema_name)
    #fp.close()
    stack.push( fp.read() )
    fp.close()
def op_out(opt, stack):
    _logger = logging.getLogger(__name__)
    
    fp=sys.stdout
    while not stack.isEmpty():
        data = stack.pop()
        _logger.debug("op_out, writing %s bytes from stack to stdout", len(data) )
        fp.write(data)
    fp.close()
def op_dict2json(opt, stack):
    _logger = logging.getLogger(__name__)
    _logger.debug("op_dict2json, reading str(dict) schema from stack and writing json back to stack")
    schema_dict=stack.pop()
    schema_json = json.dumps( eval(schema_dict) )
    stack.push( schema_json )

def op_json2dict(opt, stack):
    _logger = logging.getLogger(__name__)
    _logger.debug("op_json2dict, reading json schema from stack and writing str(dict) back to stack")
    schema_json=stack.pop()
    schema_dict = json.loads( schema_json )
    stack.push( str(schema_dict) )

def op_json2pb(opt, stack):
    _logger = logging.getLogger(__name__)
    _logger.debug("op_json2pb, reading json schema from stack and writing serialized Schema() message back to stack")
    schema_json = stack.pop()
    pbmsg=google.protobuf.json_format.Parse(schema_json, Schema() )
            
    #x=base64.b64encode( pbmsg.SerializeToString() )
    #schema.write( {"registry_pb":x})
    #schema_json=stack.pop()
    #schema_dict = json.loads( schema_json )
    stack.push(pbmsg.SerializeToString() )

def op_pb2schemaseg(opt, stack):
    _logger = logging.getLogger(__name__)
    _logger.debug("op_pb2schemaseg, read pb Schema() from stack, convert it into schemasegment and put it back to stack")
    data=stack.pop()
    schema = Schema()
    schema.ParseFromString( data )

    schema_data=schema.SerializeToString()
    fp=StringIO.StringIO()
    magic, magic_descriptor = protolib.get_magic_schema(schema_data)
    fp.write( magic.SerializeToString() )
    fp.write( magic_descriptor.SerializeToString() )
    fp.write( schema_data )
    ret=fp.getvalue()
    _logger.debug("  putting schemasegment to stack, %s bytes", len(ret))
    stack.push(ret)
    
def op_pb2proto(opt, stack):
    _logger = logging.getLogger(__name__)
    _logger.debug("op_pb2proto, reading binary Schema() message from stack and writing proto definition back to stack")
    pbmsg = stack.pop()
    
    schema = Schema()
    _logger.debug("  op_pb2proto, len(pbmsg): %s", len(pbmsg))
    schema.ParseFromString( pbmsg )
    reg_proto = pbmsg2proto(schema.registry, schema.schema_name)   

    stack.push( reg_proto )
    
def op_add(opt, stack):
    _logger = logging.getLogger(__name__)
    arg1=stack.pop()
    arg2=stack.pop()
    res=int(arg1)+int(arg2)
    _logger.debug("op_add arg1: %s, arg2: %s, result back to stack:%s", arg1,arg2,res)
    stack.push(str(res))
    
def op_sub(opt, stack):
    _logger = logging.getLogger(__name__)
    #_logger.debug("")
    arg1=stack.pop()
    arg2=stack.pop()
    res=int(arg1)-int(arg2)
    _logger.debug("op_sub arg1: %s, arg2: %s, result back to stack:%s", arg1,arg2,res)
    stack.push(str(res))

ODOOPB_PROTO='odoopb.proto'


def op_schemaseg2local(opt, stack):
    _logger = logging.getLogger(__name__)
    _logger.debug("op_test")
    schemaseg = stack.pop()
    schemaseg2local(opt, schemaseg)    
    
OP=[('diff',op_diff),
    ('d',op_diff),
    ('json',op_json),
    ('j',op_json),
    ('proto',op_proto),
    ('init',op_init),
    ('snapshot',op_snapshot),
    ('s',op_snapshot),
    ('deleteall',op_deleteall),
    ('apply',op_apply),
    ('a',op_apply),
    ('in',op_in),
    ('out', op_out),
    ('dict2json', op_dict2json),
    ('json2dict', op_json2dict),
    ('json2pb', op_json2pb),
    ('pb2proto', op_pb2proto),
    ('pb2schemaseg', op_pb2schemaseg),
    ('add', op_add),
    ('sub', op_sub),
    ('schemaseg2local',op_schemaseg2local),
]
OP_MAP=dict(OP)

def main():
    usage = "usage: python %prog [options] dbname csv_fn\n"
    parser = optparse.OptionParser(version='0.1', usage=usage)

    odoopb_group = add_OdooPB_group(parser)
    parser.add_option_group(odoopb_group)    

    streamops_group = protolib.add_StreamOPS_group(parser)
    parser.add_option_group(streamops_group)
    
    opt, args = parser.parse_args(sys.argv)
    
    #schema_name=opt.deployment_name
    import logging
    _logger = logging.getLogger(__name__)
    logging.basicConfig()
    #logging.getLogger(__name__).setLevel(logging.INFO )
    logging.getLogger(__name__).setLevel(logging.DEBUG )
    
    _logger.info("HashSync Started")
    
    arg_stack=protolib.Stack()
    
    for a in args[1:]:
        if a in OP_MAP.keys():
            _logger.debug("Add operand %s to stack", a)
            OP_MAP[a](opt, arg_stack )
        else:
            _logger.debug("Add argument %s to stack", a)
            arg_stack.push(a)

#cat sale_actual_dict.py |hsync in dict2json json2pb pb2schemaseg out > sale_act.seg
