import openerplib
import sys

def input_qty(a,b, msg=None):
    done=False
    def get_msg(a,b):
        if (a is None) and (b is None):
            return "Type a whole number or done: "
        elif (a is None) and b:
            return "Type a number up to %d or done: " % b
        elif a and (b is None):
            return "Type a number bigger than %d or done: " % a
        else:
            return "Type a number between <%d, %d> or done: " % (a,b)
    while not done:
        try:
            if msg is None:
                msg=get_msg(a,b)
            op=raw_input( msg )
            if op=='done':
                return None
            op_int=int(op)
        except ValueError:
            print "Not a number"
            continue
        if (a is None) and (b is None):
            done=True
        elif (a is None) and b:
            if op_int >= a:
                print "Bigger number expected"
                continue
        elif a and (b is None):
            if op_int <= b:
                print "Smaller number expected"
                continue
        if a and  b:
            if (op_int < a) or (op_int > b ):
                continue
        done=True
    return op_int

def select_from_options(options):
    #options=[x[0] for x in options]
    done=False
    while not done:
        print "Select from the following options or type exit"
        for i,o in enumerate(options):
            print "%d) %s" % (i+1, o[0])
        op_int=input_qty(1, len(options) )
        done=True
    if op_int is None:
        return
    else:
        return options[op_int-1][1]
    
def scan_code_or_done(msg="Scan Code or type done."):
    code=raw_input(msg).strip()
    if code=='done':
        return None
    else:
        return code
def scan_validate(pool, cr, uid, model, field='name', name="Product SKU"):    
    done=False
    qty=0
    while not done:
        code=raw_input("Scan %s or type exit: "%name).strip()
        if code=='exit':
            return None
        ids=pool.get(model).search(cr, uid, [(field,'=',code)] )
        if len(ids)==0:
            print "Can not find %s in %s" % (code,model)
            continue
        elif len(ids)==1:
            done = True
        else:
            print "Multiple records found, try again or exit"
            continue
        done=True
    return ids

def stock_take(dbname):
    stock_take_done=False
    stock_take=[]
    while not stock_take_done:
        pool, cr, uid = openerplib.get_connection(dbname)        
        product_ids = scan_validate(pool, cr, uid, 'product.product', field='default_code', name='Product SKU')
        if product_ids is not None:
                qty_int=input_qty(1, None, msg="Enter qty: " )
                if qty_int is None:
                    stock_take_done=True
                stock_take.append( (product_ids[0], qty_int) )
        else:
            stock_take_done=True
        cr.commit()
        cr.close()        
    if len(stock_take)==0:
        return

    pool, cr, uid = openerplib.get_connection(dbname)        
    location_ids = pool.get('stock.location').search(cr, uid, [('usage','=','internal')] )
    locations = [(x.name,x.id) for x in pool.get('stock.location').browse(cr, uid, location_ids) ]
    location_id=select_from_options(locations)

    if location_id is not None:

        inventory_id=pool.get('stock.inventory').create(cr, uid, {'name':raw_input("Type Inventory Name: ")} )
        for product_id, qty in stock_take:
            prod=pool.get('product.product').browse(cr, uid, product_id)
            item_id=pool.get('stock.inventory.line').create(cr, uid, {'location_id':location_id,
                                                                      'inventory_id':inventory_id,
                                                                      'product_id':product_id,
                                                                      'product_uom': prod.uom_id.id,
                                                                      'product_qty':qty } )
    cr.commit()
    cr.close()

def get_product_qty(pool, cr, uid, prod_map, direction='out'):
    msg_map={"out":"Delivery",
             "in":"Incomming Shipment",
             "":"Internal Picking"}
    stock_take_done=False
    stock_take=[]
    #print 25*'_', ' PRODUCT QTY ENTRY ', 25*'_'
    stock_take_done=False
    stock_take=[]
    while not stock_take_done:
        product_ids = scan_validate(pool, cr, uid, 'product.product', field='default_code', name='Product SKU')
        
        if product_ids is not None:
            product_id=product_ids[0]
            if product_id not in prod_map:
                print "Scanned SKU not in %s" % msg_map[direction]
                continue
            qty_max=prod_map[product_id]
            qty_int=input_qty(1, qty_max, msg="Enter qty: " )
            if qty_int is None:
                stock_take_done=True
            else:
                stock_take.append( (product_id, qty_int) )
        else:
            stock_take_done=True
    if len(stock_take)==0:
        return
    prod_map={}
    for p,qty in stock_take:
        v=prod_map.setdefault(p, [])
        v.append(qty)
    for prod in pool.get('product.product').browse(cr, uid, prod_map.keys()):
        print prod.default_code, prod.name, '\t', prod_map[prod.id]
    return prod_map

def process_delivery(dbname):
    pool, cr, uid = openerplib.get_connection(dbname)        
    out_ids=scan_validate(pool, cr, uid, 'stock.picking.out', name="Document Number")
    if out_ids is not None:
        process_partial(pool, cr, uid, out_ids, direction='out')
        
    cr.commit()
    cr.close()
def process_incoming(dbname):
    pool, cr, uid = openerplib.get_connection(dbname)        
    in_ids=scan_validate(pool, cr, uid, 'stock.picking.in', name="Document Number")
    if in_ids is not None:
        process_partial(pool, cr, uid, in_ids, direction='in')
    cr.commit()
    cr.close()


def process_partial(pool, cr, uid, picking_ids, direction='in'):
    pp=pool.get('stock.partial.picking')
    fields=['date','move_ids','picking_id']
    #fields=['date','picking_id']
    #picking_ids=pool.get('stock.picking.'+direction).search(cr, uid, [('type','=',direction)])
    if direction=='in':
        print "Processing Incomming Shipment: "
        print "Products to book in: "
    elif direction=='out':
        print "Processing Outgoing Delivery: "
        print "Products to deliver: "
    else:
        print "Processing Internal Moves: "
        print "Products to move: "
    for p in pool.get('stock.picking.'+direction).browse(cr, uid, picking_ids):
        print "Number: ", p.name
        if p.type != direction:
            print "Wrong document. ", p.type
            continue
        product_qtys=[]
        for m in p.move_lines:
            if m.state not in ('done','cancel'):
                print m.product_id.default_code, m.product_id.name, '\t',m.product_qty
                product_qtys.append( (m.product_id.id, m.product_qty ) )
        prod_map={}
        for p_id,qty in product_qtys:
            v=prod_map.setdefault(p_id, [])
            v.append( qty )
        if not prod_map:
            print "Nothing to process. Done"
            continue
        ctx={'active_model':'stock.picking.'+direction,'active_ids':[p.id]}
        res = pp.default_get(cr, uid, fields, context=ctx)
        #print res
        move_lines=res.pop('move_ids')
        w_id=pp.create(cr, uid, res)
        qty_map=get_product_qty(pool, cr, uid, prod_map, direction=direction)
        for ml in move_lines: 
            #print ml
            #prodlot_id=pool.get('stock.production.lot').create(cr, uid,
             #                                                  {'product_id':ml['product_id'],
              #                                                  'prefix':'in'})
            if ml['product_id'] in qty_map:
                ml.update( {'wizard_id':w_id,
                            'quantity': sum( qty_map[ml['product_id'] ] )
                            } 
                           )
                               
            ml_id=pool.get('stock.partial.picking.line').create(cr, uid, ml)
        pp.do_partial(cr, uid, [w_id])

