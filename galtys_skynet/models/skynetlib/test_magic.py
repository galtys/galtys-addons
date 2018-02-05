from odoopb_pb2 import Digits, SelectionOption, FieldDef, Field, Model,Registry,Magic,Header,Record,Schema
import odoopb_pb2 as odoopb
from odoopb_pb2 import MagicDescriptor
import protolib 
header = Header()
schema= Schema()

#m,md = protolib.get_magic(header)

#m,md = protolib.get_magic_schema( schema.SerializeToString() )

m=Magic()

m.magic=protolib.MAGIC_CONSTANT
m.magic_descriptor_size=1
m.schema_size=1
m.header_size=1
m.version=01
m.timestamp=1

ret=m.SerializeToString()
print [len(ret), ret]
