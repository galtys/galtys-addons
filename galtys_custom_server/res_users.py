# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

def concat(ls):
    """ return the concatenation of a list of iterables """
    res = []
    for l in ls: res.extend(l)
    return res

class users_implied(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'
    
    _columns = {
        'password': fields.char('Password', size=64, 
            help="Keep empty if you don't want the user to be able to connect on the system."),
     }
    def write(self, cr, uid, ids, values, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        res = super(users_implied, self).write(cr, uid, ids, values, context)
        if values.get('groups_id'):
            # add implied groups for all users
            for user in self.browse(cr, uid, ids):
                gs = set(concat([g.trans_implied_ids for g in user.groups_id]))
                vals = {'groups_id': [(4, g.id) for g in gs]}
                if not self.has_group(cr, user.id, 'portal.group_portal'):
                    super(users_implied, self).write(cr, uid, [user.id], vals, context)
        return res
users_implied()