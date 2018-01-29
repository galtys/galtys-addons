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
from skynetlib.protolib import add_OdooPB_group

ssl._create_default_https_context = ssl._create_unverified_context

from skynetlib.protolib import FieldTypes, FieldTypesStr,erp_type_to_pb,traverse_preorder,get_output_file,get_input_file
import skynetlib.protolib as protolib
from skynetlib.odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry,Magic,Header
import skynetlib.odoopb_pb2 as odoopb    

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


def read_sql(cr, _table, cols, ids=None, limit='', offset=''):
    #print _table, cols
    if ids is None:
        where = ''
    elif isinstance(ids, list):
        where = " where id in (%s)" % ",".join(ids)
    else:
        where = " where id=%s" % ids
    cols_quote=['"%s"'%c for c in cols]
    cols_sql = ','.join(cols_quote)
    #print [cols_sql]
    sql="select %s from %s"%(cols_sql,_table) + where + offset + limit
    #print sql
    cr.execute(sql)
    records=[]
    for r in cr.fetchall():
        records.append( dict(zip(cols,r)) )
    return records
def read_by_code(cr, _table, cols, code):
    cols_sql = ','.join(cols)
    sql = "select %s from %s where code = '%s'" % (cols_sql, _table, code )
    cr.execute(sql)
    ret = [x for x in cr.fetchall()]
    assert len(ret)==1
    return ret
def update_record(cr, _table, val, code):
    sql_update = "update %s " % _table
    sql_set = []
    par=[]
    
    for k,v in val.items():
        s = ' "%s" = '%k +  " %s "
        sql_set.append( s )
        par.append(v)
    where = " where code = %s "
    sql = sql_update + "set "+ ",".join(sql_set) +where
    arg = par + [code]
    #print sql, arg
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

def read_from_db(cr, m, limit=' limit 80'):
    cols_hash = get_pb_fields_to_hash(m)
    retsql = read_sql(cr, m._table, cols_hash, limit=limit)
    return retsql


def get_connection(config_file,dbname):
    import ConfigParser
    Config=ConfigParser.ConfigParser()
    Config.read(config_file)
    db_host = Config.get('options','db_host')
    db_port = Config.get('options','db_port')
    db_user = Config.get('options','db_user')
    db_password = Config.get('options','db_password')
    dsn="dbname='%s' user='%s' port='%s' host='%s' password='%s'"%(dbname,db_user,db_port,db_host,db_password)
    conn = psycopg2.connect(dsn)
    return conn

def parse_argv(parser, argv):
    opt, args = parser.parse_args(argv)

    if 'DBNAME' in os.environ:
        dbname = os.environ['DBNAME']
    else:
        dbname=''
        
    if len(args) == 2:
        cmd = args[1]  
    elif len(args) == 3:
        cmd = args[1]
        dbname = args[2]
    else:
        cmd = ''
    return opt, cmd, dbname

def main():
    usage = "usage: python %prog [options] dbname csv_fn\n"
    parser = optparse.OptionParser(version='0.1', usage=usage)

    odoopb_group = add_OdooPB_group(parser)
    parser.add_option_group(odoopb_group)    

    streamops_group = protolib.add_StreamOPS_group(parser)
    parser.add_option_group(streamops_group)
    
    opt, cmd, dbname = parse_argv(parser, sys.argv)

    DEPLOYMENT_NAME=opt.deployment_name

    if cmd in ['diff', 'd']:
        
        fp=sys.stdin
        segments = protolib.stream2pb(fp, DEPLOYMENT_NAME)
        fp.close()
        seg=protolib.pb2op(segments, opt)
        protolib.segments2file(seg, sys.stdout)
        sys.stdout.close()    
    elif cmd in ['json','j']:
        fp=sys.stdin
        segments = protolib.stream2pb(fp, DEPLOYMENT_NAME)
        fp.close()
        protolib.segments2json(segments, sys.stdout, opt)
        sys.stdout.close()

    elif cmd in ['proto', 'p']:
        conn=get_connection(opt.config_file, dbname)
        appname='pjbrefct'
        cr=conn.cursor()

        if not os.path.isdir(opt.protodir):
            os.makedirs(opt.protodir)
        if not os.path.isdir(opt.pydir):
            os.makedirs(opt.pydir)
        if not os.path.isdir(opt.pbdir):
            os.makedirs(opt.pbdir)
            
        odoo_proto_fn = os.path.join( opt.protodir, 'odoopb.proto' ) 
        

        cr.execute("select id,odoopb_proto from skynet_settings where name=%s",(appname,) )
        ret=[x for x in cr.fetchall()]
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
            file(fn,'wb').write(registry_proto)
            
            arg=['protoc', '--proto_path=%s'%opt.protodir, '--python_out=%s'%opt.pydir, fn]
       
            if opt.protoc=='yes':
                print
                print 'Running:'
                print " ".join(arg)
                subprocess.call(arg)
                
                py_init_fn=os.path.join( opt.pydir, '__init__.py' )
                if not os.path.isfile(py_init_fn):
                    file(py_init_fn, 'wb').write('')
                    
            fn = os.path.join( opt.pbdir, name+'.pb' )
            pbmsg=base64.b64decode( registry_pb )
            file(fn,'wb').write(pbmsg)

            
        #print odoopb_proto
        #pb_fn = os.path.join(opt.pbdir, DEPLOYMENT_NAME + '.pb' )
        #pbr = Registry()
        #pbr.ParseFromString( file(pb_fn).read() )
        
        #import bitcoin
        
        #for m in pbr.models:
#            cr.execute("select id from %s where code is Null"%m._table)
 #           for rec in cr.fetchall():
  #              id_=rec[0]
   #             secret_key = bitcoin.random_key()
    #            pub_key = bitcoin.privtopub(secret_key)
     #           code = bitcoin.pubtoaddr( pub_key )
      #          sql_update="update %s set " % m._table
       #         cr.execute( sql_update+"code=%s,secret_key=%s where id=%s", (code,secret_key,id_) )
        cr.close()
        conn.commit()
        
    elif cmd in ['init', 'i']:
        conn=get_connection(opt.config_file, dbname)
        cr=conn.cursor()

        pb_fn = os.path.join(opt.pbdir, DEPLOYMENT_NAME + '.pb' )
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
        
    elif cmd in ['snapshot','s', 'is']:
        conn=get_connection(opt.config_file, dbname)
        cr=conn.cursor()

        pb_fn = os.path.join(opt.pbdir, DEPLOYMENT_NAME + '.pb' )
        pbr = Registry()
        pbr.ParseFromString( file(pb_fn).read() )
        
        fp=sys.stdout
        if cmd=='is':
            fp.write( sys.stdin.read() )
        hash_map = {}
        id2code_map = {}
        for m in pbr.models:
            id_map=id2code_map.setdefault(m._name, {})
            records=read_from_db(cr, m, limit='')
            for r in records:
                id_map[ r['id'] ] = r['code']
            #if len(parents)>0:
            #    records2 = traverse_preorder(records, parent_field = parents[0], key_field='id')
            #    pb_messages2=protolib.serialize_records(m, records2, opt, hash_map, id2code_map)
            #    #for pb_m2 in pb_messages2: 
            #print records[0]['parent_id']
            pb_messages=protolib.serialize_records(m, records,opt, hash_map, id2code_map, appname=DEPLOYMENT_NAME)
            pbstream = protolib.pb2stream(m, pb_messages)
            fp.write( pbstream )
        fp.close()
        cr.close()
        conn.commit()
    elif cmd in ['deleteall','da']:
        conn=get_connection(opt.config_file, dbname)
        cr=conn.cursor()
        pb_fn = os.path.join(opt.pbdir, DEPLOYMENT_NAME + '.pb' )
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
    elif cmd in ['apply','a']:
        conn=get_connection(opt.config_file, dbname)
        cr=conn.cursor()
        pb_fn = os.path.join(opt.pbdir, DEPLOYMENT_NAME + '.pb' )
        pbr = Registry()
        pbr.ParseFromString( file(pb_fn).read() )
        pbr_map = dict( [ (m._name, m) for m in pbr.models] )

        field_relation_map = protolib.relation_map(pbr)
        fp=sys.stdin
        segments = protolib.stream2pb(fp, DEPLOYMENT_NAME)
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
                    ret_id = protolib.next_id(cr, header._sequence)
                    val = { 'id':ret_id }
                    v[code] = ret_id
                    #val['code'] = code
                    #val['secret_key']=secret_key
                    ret = protolib.pbdict2dbdict(m, msg, opt, code2id_map, field_relation_map)
                    ret.update(val)
                    #if m._name == 'deploy.deploy':

                    
                    pprint.pprint(ret)
                    insert_record(cr, m._table, ret)


                    #cr.execute("select nextval('deploy_account_id_seq') ")
                    #print 
                    #print ret
                elif op_map[code] == odoopb.UPDATE:
                    ret = protolib.pbdict2dbdict(m, msg, opt, code2id_map, field_relation_map)
                    update_record(cr, m._table, ret, code)
                elif op_map[code] == odoopb.DELETE:
                    ret_id = code2id_map[ header.model ] [code]
                    sql = "delete from %s " % m._table
                    cr.execute( sql + "where id=%s", (ret_id, ))
        cr.close()
        conn.commit()
        
