from odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry,Magic,Header,Record
import odoopb_pb2 as odoopb

import optparse
import os
import hashlib
import StringIO
import google.protobuf.json_format
import importlib
import json
import datetime
import dateutil.relativedelta
import sys
DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT)
MAGIC_SIZE=10
MAGIC_CONSTANT=437899321
LEN_SHA256_DIGEST=32 # len( hashlib.sha256('').digest() )
DATETIME_EPOCH = datetime.datetime(1970,1,1)
EPOCH_SECONDS=0

def str_to_seconds(t,f=DEFAULT_SERVER_DATETIME_FORMAT): #supports str type, datetime and date type
    if type(t) == datetime.date:
        ret = (t-datetime.date(1970,1,1)).total_seconds()
    elif type(t) == datetime.datetime:
        ret = (t-datetime.datetime(1970,1,1)).total_seconds()
    else:
        tt=t.split('.')
        t=datetime.strptime(tt[0], f)        
        ret = (t-DATETIME_EPOCH).total_seconds()
    return ret

def seconds_to_datetime(sec):
    return dateutil.relativedelta.relativedelta(seconds=sec) + DATETIME_EPOCH

def seconds_to_date(sec):
    x = seconds_to_datetime(sec)
    return datetime.date(x.year, x.month, x.day)
                   
PB2MYSQL_MAP = {FieldDef.BOOLEAN:'BOOLEAN',
                FieldDef.INTEGER:'INTEGER',
                FieldDef.CHAR:   'VARCHAR(255)',
                FieldDef.FLOAT:   'DECIMAL(10,2)',
                FieldDef.SELECTION:'VARCHAR(255)',
                FieldDef.MANY2ONE: 'VARCHAR(255)'}




FieldTypes = {'boolean':FieldDef.BOOLEAN,
              'integer':FieldDef.INTEGER,
              'reference':FieldDef.REFERENCE,
              'char':FieldDef.CHAR,
              'html':FieldDef.HTML,
              'float':FieldDef.FLOAT,
              'date':FieldDef.DATE,
              'datetime':FieldDef.DATETIME,
              'binary':FieldDef.BINARY,
              'selection':FieldDef.SELECTION,
              'many2one':FieldDef.MANY2ONE,
              'one2many':FieldDef.ONE2MANY,
              'many2many':FieldDef.MANY2MANY,
              'function':FieldDef.FUNCTION,
              'serialized':FieldDef.SERIALIZED,
              'property':FieldDef.PROPERTY,
              'text':FieldDef.TEXT,
              }
FieldTypesStr = {'boolean':'BOOLEAN',
                 'integer':'INTEGER',
                 'reference':'REFERENCE',
                 'char':'CHAR',
                 'html':'HTML',
                 'float':'FLOAT',
                 'date':'DATE',
                 'datetime':'DATETIME',
                 'binary':'BINARY',
                 'selection':'SELECTION',
                 'many2one':'MANY2ONE',
                 'one2many':'ONE2MANY',
                 'many2many':'MANY2MANY',
                 'function':'FUNCTION',
                 'serialized':'SERIALIZED',
                 'property':'PROPERTY',
                 'text':'TEXT',
              }
erp_type_to_pb = {
    FieldDef.BOOLEAN:'bool',
    FieldDef.INTEGER:'int64',
    FieldDef.REFERENCE:'Reference',
    FieldDef.CHAR:'string',
    FieldDef.HTML:'string',
    FieldDef.FLOAT:'uint64',
    #FieldDef.DATE:'google.protobuf.Timestamp',
    #FieldDef.DATETIME:'google.protobuf.Timestamp',
    FieldDef.DATE:'uint64',
    FieldDef.DATETIME:'uint64',
    FieldDef.BINARY:'Binary',
    FieldDef.SELECTION:'string',
    FieldDef.MANY2ONE:'Many2one',
    #FieldDef.ONE2MANY:,
    #FieldDef.MANY2MANY,
    #FieldDef.FUNCTION,
    #FieldDef.SERIALIZED,
    #FieldDef.PROPERTY,
    FieldDef.TEXT:'string',
}
odoo_custom_pbfields = [FieldDef.REFERENCE,FieldDef.BINARY,FieldDef.MANY2ONE]

HOMEDIR=os.environ['HOME']
PROTODIR='protodir'

REPOSDIR='codebasehq.com'
PRJDIR='pjbrefct'
PBDIR='pbdir'
PYDIR='pydir'

DEFAULT_PRJDIR=os.path.join(HOMEDIR,REPOSDIR,PRJDIR)

DEFAULT_PROTODIR=os.path.join(DEFAULT_PRJDIR, PROTODIR)
DEFAULT_PBDIR=os.path.join(DEFAULT_PRJDIR, PBDIR)
DEFAULT_PYDIR=os.path.join(DEFAULT_PRJDIR, PYDIR)

def add_OdooPB_group(parser):
    odoopb_group = optparse.OptionGroup(parser, "OdooPB")
    odoopb_group.add_option("--deployment-name",
                            dest='deployment_name',
                            help="Default: [%default]",
                            default='sales_actual'
    )
    odoopb_group.add_option("--homedir",
                            dest='homedir',
                            help="Default: [%default]",
                            default=HOMEDIR
    )    
    odoopb_group.add_option("--prjdir",
                            dest='prjdir',
                            help="<homedir>/<reposdir>/<prjdir> Default: [%default]",
                            default=DEFAULT_PRJDIR,
    )
    

    odoopb_group.add_option("--protodir",
                            dest='protodir',
                            help="Default: [%default]",
                            default=DEFAULT_PROTODIR
    )
    
    odoopb_group.add_option("--pbdir",
                            dest='pbdir',
                            help="Default: [%default]",
                            default=DEFAULT_PBDIR
    )
    odoopb_group.add_option("--pydir",
                            dest='pydir',
                            help="Default: [%default]",
                            default=DEFAULT_PYDIR
    )
    odoopb_group.add_option("--protoc",
                            dest='protoc',
                            help="Call protoc. Default: [%default]",
                            default='yes'
    )
    odoopb_group.add_option("--pbout",
                            dest='pbout',
                            help="File name of binary pb output file. Default: [%default]",
                            default='data.pb'
    )
    odoopb_group.add_option("--pbin",
                            dest='pbin',
                            help="File name of binary pb input file. Default: [%default]",
                            default='data.pb'
    )
    odoopb_group.add_option("--pbstd",
                            dest='pbstd',
                            help="Use stdin stdout for pb messages. Default: [%default]",
                            default='yes'
    )
    odoopb_group.add_option("--config",
                            dest='config_file',
                            help="Config file.  Default: [%default]",
                            default='/home/jan/projects/server_pjbrefct.conf'
    )
    
    return odoopb_group
def add_StreamOPS_group(parser):
    odoopb_group = optparse.OptionGroup(parser, "StreamOPS")
    odoopb_group.add_option("--init",
                            dest='init',
                            help="Default: [%default]",
                            default='no'
    )
    odoopb_group.add_option("--stack",
                            dest='stack',
                            help="Default: [%default]",
                            default='no'
    )
    odoopb_group.add_option("--limitjson",
                            dest='limitjson',
                            help="For Json output, how many messages to include. Default: [%default]",
                            default='all'
    )
    odoopb_group.add_option("--offsetjson",
                            dest='offsetjson',
                            help="Not implemented yet. Default: [%default]",
                            default='yes'
    )
    odoopb_group.add_option("--includeid",
                            dest='includeid',
                            help="Include id in snapshot. Default: [%default]",
                            default='no'
    )
    
    return odoopb_group

def get_output_file(opt):
    return os.path.join( opt.pbdir, opt.pbout )
def get_input_file(opt):
    return os.path.join( opt.pbdir, opt.pbin )

class TraversePreorder(dict):
    def __init__(self, d=None, parent_field='parent_id', parent_field_option=None):
        if d:
            dict.__init__(self, d)
        self._child_map = None
        self._parent_field = parent_field
        self._parent_field_option = parent_field_option
    def _build_child_map(self):
        _child_map = {}
        for _id, row in self.items():
            if self._parent_field_option:
                parent_id = row[self._parent_field][self._parent_field_option]
            else:
                parent_id = row[self._parent_field]
            #if parent_id:
            #    parent_id=parent_id[0]
            v = _child_map.setdefault(parent_id, [])
            v.append(_id)
        #print 50*'*'
        #print _child_map
        self._child_map = _child_map
    def traverse_preorder(self, test_id=None, depth=0):
        if not self._child_map:
            self._build_child_map()
        if test_id:
            yield test_id, depth
            children = self._child_map.get(test_id, [])
            #key=lambda x:(self[x].get('name',0), x)
            #children.sort(key=key)
            
            for ch in children:
                for tt, dd in self.traverse_preorder(ch, depth + 1):
                    yield tt, dd
        else:
            if self._parent_field_option:
                roots = [t for t in self.keys() if not self[t][self._parent_field][self._parent_field_option] ]
            else:
                roots = [t for t in self.keys() if not self[t][self._parent_field] ]

            #roots.sort(key=lambda x:(self[x].get('sort_order',0), x))
            #print 'roots',roots,   [self[t][self._parent_field] for t in self.keys() ]
            #  nt roots,len(roots)
            for root in roots:
                for tt, dd in self.traverse_preorder(root, depth):
                    yield tt, dd

#def traverse_preorder(records, parent_field = 'parent_id', key_field='id'):
def traverse_preorder(records, parent_field = 'parent_id', key_field='id',parent_field_option=None):
    
    recs2_map = dict( [(x[key_field],x) for x in records] )
    tp=TraversePreorder(d=recs2_map, parent_field=parent_field, parent_field_option=parent_field_option)
    ret= [ recs2_map[tt] for tt,dd in tp.traverse_preorder() ]
    return ret


def stream2pb(opt,stream, appname):
    out=[]
    def read_magic(stream): #TBD, EOF does not work?        
        try:
            magic_str = stream.read(MAGIC_SIZE)
            eof = False
        except EOFError:
            eof = True

        if not (len(magic_str)==MAGIC_SIZE):
            eof = True
        if not eof:
            magic = Magic()
            magic.ParseFromString( magic_str  )
            assert magic.magic==MAGIC_CONSTANT
            ret = eof, magic
        else:
            ret = eof, False
        return ret    
    eof,magic = read_magic(stream)
    while not eof:        
        header = Header()
        header.ParseFromString( stream.read(magic.header_size) )
        messages = []
        for record in header.record:
            msg_class = get_pb_class(opt, header._table, appname=appname )
            msg = msg_class()
            msg.ParseFromString( stream.read(record.size) )
            messages.append( msg )
        out.append( (header, messages) )
        assert header.records == len(messages)
        eof,magic = read_magic(stream)
    return out

def pb2op(segments, opt):
    class Stack(object):
        def __init__(self):
            self.items=[]
        def push(self, item):
            self.items.append(item)
        def pop(self):
            return self.items.pop()
        def isEmpty(self):
            return self.items==[]
        
    def copy_segment(segment, op, op_header_only=True):
        header,messages = segment
        header.operation=op
        #return header,messages
        header2=Header()
        header2.model = header.model
        header2._table = header._table
        header2._sequence = header._sequence
        header2.records = header.records
        header2.operation = op
        for record in header.record:
            record2 = header2.record.add()
            record2.sha256=record.sha256
            record2.size=record.size
            record2.code=record.code
            if not op_header_only:
                record2.operation=op
        return header2, messages
    #def add_stack_segment(segment):
    #    return copy_segment(segment, odoopb.STACK)
    def zip_records(segment):
        header,messages = segment
        x = [(rec.code,(rec.sha256,rec.size,msg)) for rec,msg in zip(header.record,messages)] 
        return x
    def diff(prev, current):
        if prev is None:
            ret = copy_segment(current, odoopb.CREATE, op_header_only=False)
            #hh,mm = ret
            #print ret[1]
        else:
            header_c,messages_c=current
            prev_items = zip_records(prev)
            current_items = zip_records(current)
            #print prev_items[0:2]
            prev_map = dict(prev_items)
            current_map = dict(current_items)
            
            header2=Header()
            header2.model=header_c.model
            header2._table = header_c._table
            header2._sequence = header_c._sequence
            messages = []
            for p_code,(p_h,p_s, p_m) in prev_items:
                if p_code in current_map:
                    c_h, c_s, c_m = current_map[p_code]
                    if p_h == c_h:
                        pass #SKIP
                        #print 'kocour', 'skip'
                    else:
                        #print 'KOCOUR', p_code
                        #UPDATE.append( (p_code, (p_h,p_m), (c_h,c_m) ) )
                        record = header2.record.add()
                        record.code = p_code
                        record.size = c_s
                        record.sha256 = c_h
                        record.prev_sha256 = p_h
                        record.operation = odoopb.UPDATE
                        messages.append( c_m)
                else:
                        record = header2.record.add()
                        record.code = p_code
                        record.size = p_s
                        record.sha256 = b''
                        record.prev_sha256 = p_h
                        record.operation = odoopb.DELETE
                        messages.append( p_m )
            for code, (h,s,m) in current_items:
                if code not in prev_map:
                    #CREATE.append( (code, (h,m)) )
                    #print 'KOCOUR', 'create'
                    record = header2.record.add()
                    #assert len(code)>0
                    record.code = code
                    record.size = s
                    record.sha256 = h
                    #record.prev_sha256
                    record.operation = odoopb.CREATE
                    messages.append( m )
            header2.records=len(messages) 
            ret = header2, messages
            #print 'bubak', ret
        return ret
    out=[]
    stack_map={}
    for segment in segments:
        header, messages = segment
        stack = stack_map.setdefault( header.model, Stack() )
        segment = header, messages
        if stack.isEmpty():
            if opt.init=='yes':
                ret = diff( None, segment)
                out.append( ret )
            stack.push( segment )
        else:
            previous_segment = stack.pop()
            ret = diff( previous_segment, segment)
            #print 'ret diff', ret
            out.append( ret )
            stack.push( segment) 
    #print out[3]
    for key,stack in stack_map.items():
        #print 'stack segment'
        #out.append( add_stack_segment(segment) )
        seg = stack.pop()
        if opt.stack=='yes':
            out.append( seg )
    for h,m in out:
        #print type(h.model)
        assert type(m)==list
    return out #list of segments + stack segment

def get_header(m, pb_messages): #including magic
    header = Header()
    header.model = m._name
    header._table = m._table
    header._sequence = m._sequence
    for rp_msg in pb_messages:
        pb_msg = rp_msg.SerializeToString()
        record=header.record.add()
        record.size= len(pb_msg)
        record.code= rp_msg.code
        sha256 = hashlib.sha256(pb_msg).digest()
        assert len(sha256) == LEN_SHA256_DIGEST
        record.sha256 = sha256
        record.prev_sha256 = sha256
        record.operation = odoopb.SNAPSHOT
        
    header.records=len(pb_messages)
    return header
def get_magic(header):
    header_str = header.SerializeToString()   
    magic=Magic()# the size of magic msg is fixed to 10
    magic.magic=MAGIC_CONSTANT
    magic.header_size = len(header_str)
    assert MAGIC_SIZE == len(magic.SerializeToString())
    return magic

def segment2stream(s, segment):
    #print type(segment)
    #print segment[0]
    header, messages = segment
    magic = get_magic(header)
    s.write( magic.SerializeToString() )
    s.write( header.SerializeToString() )
    for rp_msg in messages:
        pb_msg = rp_msg.SerializeToString()
        s.write( pb_msg )
    #return s.getvalue()
def segments2stream(segments):
    s=StringIO.StringIO()
    for seg in segments:
        #h,m = seg
        segment2stream(s, seg)
    return s.getvalue()
def segments2file(segments, fp):
    for seg in segments:
        segment2stream(fp, seg)

def pb2stream(m, pb_messages):
    header = get_header(m, pb_messages)
    #magic = get_magic(header)
    #print 'magic size: ', [magic.SerializeToString(), len(magic.SerializeToString()) ]
    s=StringIO.StringIO()
    segment = header, pb_messages
    segment2stream(s, segment )
    return s.getvalue()

def get_pb_class(opt,cl_name, appname='pjbrefct'):
    #print [opt.pydir]
    if opt.pydir not in sys.path:
        sys.path.append( opt.pydir )
    pjbrefct_module=importlib.import_module('%s_pb2'%(appname) )
    res_partner_class = getattr(pjbrefct_module,  cl_name)
    return res_partner_class

def get_pb_json(m, rec, opt, hash_map, id2code_map):
    out_dict = get_pb_dict(m, rec, opt, hash_map, id2code_map)
    if ('id' in out_dict) and (opt.includeid=='no'):
        out_dict.pop('id')
    ret_js=json.dumps( out_dict )
    return ret_js

def get_pb_dict(m, rec, opt, hash_map, id2code_map):
    field_map = dict( [ (f.name, f.field_def) for f in m._fields] )
    out=[]
    for k,v in rec.items():
        fd = field_map[k]
        if fd.type in [FieldDef.MANY2ONE]: #, FieldDef.INTEGER,FieldDef.FLOAT]:
            relation = fd.relation
            vvv = {'code':'', 'cnt_hash':''}
            if v in [None, False]:
                vvv = {'code':'', 'cnt_hash':''}
            elif type(v) in (int,long):
                if relation in id2code_map:
                    code = id2code_map[relation][v]
                    vvv = {'code':code, 'cnt_hash':''}
                    if relation in hash_map:
                        h = hash_map[relation][code]
                        vvv = {'code':code, 'cnt_hash': h}
            else:
                vvv = {'code':'', 'cnt_hash':''}
            vv=vvv
            out.append( (k,vv) )
        elif fd.type in [FieldDef.CHAR, FieldDef.TEXT]:
            if v:
                out.append( (k,v) )
        elif fd.type in [FieldDef.DATE]:
            #sys.stderr.write( str( [k,v] ) )
            #raise
            if v:
                vv=str_to_seconds(v,f=DEFAULT_SERVER_DATE_FORMAT)
            else:
                vv=EPOCH_SECONDS 
            #sys.stderr.write( str( [k,vv] ) )
            out.append( (k,vv) )
               
        elif fd.type in [FieldDef.DATETIME]:
            #sys.stderr.write( str( [k,v] ) )
            #vv=str_to_seconds(v,f=DEFAULT_SERVER_DATETIME_FORMAT)
            if v:
                vv=str_to_seconds(v,f=DEFAULT_SERVER_DATETIME_FORMAT)
                out.append( (k,vv) ) 
            else:
                vv=EPOCH_SECONDS 
            out.append( (k,vv) )                
        #elif fd.type in [FieldDef.BOOLEAN]:
        #    if type(v)==str and v in [u'', '']:
        #        vv=False
        #    else:
        #        vv=v
        #    out.append( (k, vv) )
        
        #elif fd.type in [FieldDef.BINARY]:
        #    if v:
        #        vv={'content':'','content_hash':''}
        #    else:
        #        vv={'content':'','content_hash':''}
        elif fd.type in [FieldDef.SELECTION]:
            if v:
                out.append( (k,v) )
        elif fd.type in [FieldDef.INTEGER, FieldDef.FLOAT]:
            out.append( (k,v) )
    out_dict = dict(out)
    return out_dict
def relation_map(pbr):
    out_map={}
    for m in pbr.models:
        v = out_map.setdefault( m._name, {} )
        for f in m._fields:
            fname, fd = f.name, f.field_def
            if fd.type in [FieldDef.MANY2ONE]:
                v[fname] = fd.relation
    return out_map
def pbdict2dbdict(m, rec, opt, code2id_map, field_relation_map):
    field_map = dict( [ (f.name, f.field_def) for f in m._fields] )
    out=[]
    for k,v in rec.items():
        fd = field_map[k]
        if fd.type in [FieldDef.MANY2ONE]:
            relation = field_relation_map[m._name][k]
            if relation in code2id_map:
                if v['code'] in code2id_map[relation]:
                    res_id = code2id_map[relation][v['code']]
                    out.append( (k,res_id)  )
        
        elif fd.type in [FieldDef.CHAR, FieldDef.TEXT]:
            if v == u'false': #TBD
                vv = False
            else:
                vv = v
                out.append( (k,vv) )
        elif fd.type in [FieldDef.DATE]:
            v=int(v)
            if v==EPOCH_SECONDS:
                vv=None
            else:
                vv = seconds_to_date(v)
            out.append( (k,vv) )
            
        elif fd.type in [FieldDef.DATETIME]:
            v=int(v)
            if v==EPOCH_SECONDS:
                vv=None
            else:
                vv = seconds_to_datetime(v)
            out.append( (k,vv) )
            
        elif fd.type in [FieldDef.SELECTION]:
            if v:
                out.append( (k,v) )
        elif fd.type in [FieldDef.INTEGER, FieldDef.FLOAT]:
            out.append( (k,int(v)) )
            
    out_dict = dict(out)
#    if 'code' in out_dict:
#        out_dict.pop('code')
#    if 'secret_key' in out_dict:
#        out_dict.pop('secret_key')
    if 'id' in out_dict:
        out_dict.pop('id')
    return out_dict
def next_id(cr, sequence):
    cr.execute("select nextval('%s') " % sequence)
    ret=[x[0] for x in cr.fetchall()]
    return ret[0]
def serialize_records(m, records, opt, hash_map, id2code_map, appname=''):
    _table = m._table
    res_partner_class = get_pb_class(opt,m._table, appname=appname)   
    out=[]
    for ret in records:
        ret_js = get_pb_json(m, ret, opt, hash_map, id2code_map)
        rp_msg = google.protobuf.json_format.Parse(ret_js, res_partner_class() )
        out.append( rp_msg  )
    return out

def segments2json(segments, fp, opt):
    for header, messages in segments:
        if opt.limitjson=='all':
            out = messages
        else:
            try:
                limit = int(opt.limitjson)
                out = messages[:limit]
            except:
                out = messages
        js=google.protobuf.json_format.MessageToJson(header, including_default_value_fields=True, preserving_proto_field_name=True)
        fp.write(js)
                
        for msg in out:
            
            js=google.protobuf.json_format.MessageToJson(msg, including_default_value_fields=True, preserving_proto_field_name=True)
            #d=google.protobuf.json_format.MessageToDict(msg, including_default_value_fields=True, preserving_proto_field_name=True)
            #sys.stderr.write( str(d) )
            fp.write(js)

def segments2dict(segments):
    seg = []
    for header, messages in segments:
        out = []
        for msg in messages:
            js=google.protobuf.json_format.MessageToJson(msg, including_default_value_fields=False, preserving_proto_field_name=True)
            #print [js]
            out_dict=google.protobuf.json_format.MessageToDict(msg, including_default_value_fields=True, preserving_proto_field_name=True)
            #out_dict = json.loads(js)
            #print out_dict
            out.append( out_dict )
        seg.append( (header, out) )
    return seg
