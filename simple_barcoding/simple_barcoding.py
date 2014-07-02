from datetime import datetime, timedelta
import time
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import math
import base64
from openerp import netsvc
import openerp.addons.decimal_precision as dp

def print_barcode(code):
    import barcodes
    from barcodes import code128
    from barcodes.write import CairoRender

    def get_geometry(s):
        spl = s.split("x", 1)
        if len(spl) == 2:
            try:
                return int(spl[0]), int(spl[1])
            except ValueError:
                pass
        raise ValueError("invalid geometry")

    barcode = code128.Code128.from_unicode(code)
    #width, height = get_geometry("2000x442")
    width, height = get_geometry("708x342")

    data = CairoRender(barcode, margin=8).get_png(width, height)
    from subprocess import call
    fn='barcode_image_data.png'
    fp=open(fn,'wb')
    fp.write(data)
    fp.close()
    call(['lpr', fn])
    import os
    os.unlink(fn)

class product_product(osv.osv):
    _inherit="product.product"
    def print_barcode_label(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids):
            print_barcode(p.default_code)
product_product()

class sale_order(osv.osv):
    _inherit="sale.order"
    def print_barcode_label(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids):
            print_barcode(p.name)
sale_order()

class purchase_order(osv.osv):
    _inherit="purchase.order"
    def print_barcode_label(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids):
            print_barcode(p.name)
purchase_order()


class stock_picking(osv.osv):
    _inherit="stock.picking"
    def print_barcode_label(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids):
            print_barcode(p.name)
stock_picking()

class stock_picking_out(osv.osv):
    _inherit="stock.picking.out"
    def print_barcode_label(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids):
            print_barcode(p.name)
stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit="stock.picking.in"
    def print_barcode_label(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids):
            print_barcode(p.name)
stock_picking_in()
