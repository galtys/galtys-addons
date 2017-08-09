# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

#import base58
#import ecdsa 

#from ecdsa import SECP256k1, SigningKey, VerifyingKey, BadSignatureError
import datetime
import bitcoin #bitcoin tools

#DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
#DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
#DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
#    DEFAULT_SERVER_DATE_FORMAT,
#    DEFAULT_SERVER_TIME_FORMAT)

def secret_random_key(a):
    return bitcoin.random_key()

class SkynetCode(models.Model):
    _name = "skynet.code"
    _description = "Skynet Code"
    _rec_name = 'code'

    @api.depends('secret_key')    
    def _compute_keys(self):
        for c in self:
            c.public_key=bitcoin.privtopub(c.secret_key)
            c.code=bitcoin.pubtoaddr( c.public_key )

    secret_key=fields.Char("Secret Key", default=secret_random_key)
    public_key=fields.Char("Public Key", compute='_compute_keys', store=True)
    code=fields.Char("Code", compute='_compute_keys', store=True)

    #signature=fields.Text("Signature")
    prev_msg=fields.Many2one('skynet.code')
    next_msg=fields.Many2one('skynet.code')

class SkynetTransition(models.Model):
    _name = "skynet.transition"
    _description = "Skynet transition"
    _rec_name = ''

    code=fields.Many2one("skynet.code")
    public_key_copy=fields.Char("Public Key (copy)")
    message=fields.Text("Message")
    signature=fields.Text("Signature")
    signature_required=fields.Selection([('record','Record Level'),
                                         ('user', 'User Level'),
                                         ('admin', 'Admin'),
                                         ('group', 'Group'),
                                         ('model', 'Model'),] )
    action = fields.Selection( [('create','Create'),
                                ('update','Update'),
                                ('delete','Delete'),
                                ('merge','Merge')] )
    
