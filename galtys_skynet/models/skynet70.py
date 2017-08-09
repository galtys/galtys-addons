# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp.osv import fields, osv
from lxml import etree

import datetime
import bitcoin #bitcoin tools


def secret_random_key(a):
    return bitcoin.random_key()

class SkynetCode(osv.osv):
    _name = "skynet.code"
    _description = "Skynet Code"
    _rec_name = 'code'

    def _default_secret_key(self, cr, uid, context=None):
        return bitcoin.random_key()

    def _compute_keys(self, cr, uid, ids, name, args, context=None):
        res={}
        for c in self.browse(cr, uid, ids, context=context):
            val={'public_key':bitcoin.privtopub(c.secret_key),
                 'code':bitcoin.pubtoaddr( c.public_key ),
                 }
            res[o.id]=val
        return res

    _columns={
        'secret_key':fields.char("Secret Key"),
        'public_key':fields.function(_compute_keys,
                                     string="Public Key", 
                                     type='char',
                                     size=444),
        'code':fields.function(_compute_keys,
                               string="code", 
                               type='char',
                               size=444),
        'signature':fields.text("Signature"),
        'prev_msg':fields.many2one('skynet.code'),
        'next_msg':fields.many2one('skynet.code'),
    }

    _defaults = {

        'secret_key':_default_secret_key,

    }
