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



class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    _columns = {
        'retail':fields.boolean("Retail",select=True),
        'contract':fields.boolean("Contract",select=True),
        'customer_relationship':fields.selection([('trade','Trade'),('retail','Retail'),('contract','Contract')], 'Customer Relationship'),
        'helpscout':fields.char("Helpscout",size=444),
        'helpscout_state':fields.char("Helpscout_state",size=444),
        'trustpilot':fields.char("Trustpilot"),        
    }

    def _default_category(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('category_id'):
            return [context['category_id']]
        return False

    _defaults = {
        'active': True,
        'customer_relationship': 'trade',
        'lang':'',
#        'lang': lambda self, cr, uid, ctx: 'en_US',#ctx.get('lang', 'en_US'),
        'tz': lambda self, cr, uid, ctx: ctx.get('tz', False),
        'customer': True,
        'category_id': _default_category,
        'company_id': lambda self, cr, uid, ctx: self.pool.get('res.company')._company_default_get(cr, uid, 'res.partner', context=ctx),
        'color': 0,
        'is_company': False,
        'type': 'contact', # type 'default' is wildcard and thus inappropriate
        'use_parent_address': False,
        'image': False,
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if (not view_id) and (view_type=='form') and context and context.get('force_email', False):
            view_id = self.pool.get('ir.model.data').get_object_reference(cr, user, 'base', 'view_partner_simple_form')[1]
        res = super(res_partner,self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
 #       if view_type == 'form':
  #          res['arch'] = self.fields_view_get_address(cr, user, res['arch'], context=context)
        return res
    def onchange_type(self, cr, uid, ids, is_company, context=None):
        value = {}
        value['title'] = False
        if is_company:
            domain = {'title': [('domain', '=', 'partner')]}
        else:
            domain = {'title': [('domain', '=', 'contact')]}
        return {'value': value, 'domain': domain}

    def onchange_address(self, cr, uid, ids, use_parent_address, parent_id, context=None):
        def value_or_id(val):
            """ return val or val.id if val is a browse record """
            return val if isinstance(val, (bool, int, long, float, basestring)) else val.id
        result = {}
        if parent_id:
            if ids:
                partner = self.browse(cr, uid, ids[0], context=context)
                if partner.parent_id and partner.parent_id.id != parent_id:
                    result['warning'] = {'title': _('Warning'),
                                         'message': _('Changing the company of a contact should only be done if it '
                                                      'was never correctly set. If an existing contact starts working for a new '
                                                      'company then a new contact should be created under that new '
                                                      'company. You can use the "Discard" button to abandon this change.')}
            parent = self.browse(cr, uid, parent_id, context=context)
            address_fields = self._address_fields(cr, uid, context=context)
            result['value'] = dict((key, value_or_id(parent[key])) for key in address_fields)
        else:
            result['value'] = {'use_parent_address': False}
        return result
    def _commercial_sync_from_company(self, cr, uid, partner, context=None):
        """ Handle sync of commercial fields when a new parent commercial entity is set,
        as if they were related fields """
        if partner.commercial_partner_id != partner:
            commercial_fields = self._commercial_fields(cr, uid, context=context)
            sync_vals = self._update_fields_values(cr, uid, partner.commercial_partner_id,
                                                        commercial_fields, context=context)
            partner.write(sync_vals)

    def _commercial_sync_to_children(self, cr, uid, partner, context=None):
        """ Handle sync of commercial fields to descendants """
        commercial_fields = self._commercial_fields(cr, uid, context=context)
        sync_vals = self._update_fields_values(cr, uid, partner.commercial_partner_id,
                                                   commercial_fields, context=context)
        sync_children = [c for c in partner.child_ids if not c.is_company]
        for child in sync_children:
            self._commercial_sync_to_children(cr, uid, child, context=context)
        return self.write(cr, uid, [c.id for c in sync_children], sync_vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        #res.partner must only allow to set the company_id of a partner if it
        #is the same as the company of all users that inherit from this partner
        #(this is to allow the code from res_users to write to the partner!) or
        #if setting the company_id to False (this is compatible with any user company)
        #if 'lang' in vals:
        #TODO!!!!!
        vals['lang']=''
        if vals.get('company_id'):
            for partner in self.browse(cr, uid, ids, context=context):
                if partner.user_ids:
                    user_companies = set([user.company_id.id for user in partner.user_ids])
                    if len(user_companies) > 1 or vals['company_id'] not in user_companies:
                        raise osv.except_osv(_("Warning"),_("You can not change the company as the partner/user has multiple user linked with different companies."))
        result = super(res_partner,self).write(cr, uid, ids, vals, context=context)
        for partner in self.browse(cr, uid, ids, context=context):
            self._fields_sync(cr, uid, partner, vals, context)
        return result

    def create(self, cr, uid, vals, context=None):
        print vals
       # if 'lang' in vals:
        vals['lang']=''
        new_id = super(res_partner, self).create(cr, uid, vals, context=context)
        partner = self.browse(cr, uid, new_id, context=context)

        self._fields_sync(cr, uid, partner, vals, context)
        self._handle_first_contact_creation(cr, uid, partner, context)
        return new_id

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]
            query_args = {'name': search_name}
            # TODO: simplify this in trunk with `display_name`, once it is stored
            # Perf note: a CTE expression (WITH ...) seems to have an even higher cost
            #            than this query with duplicated CASE expressions. The bulk of
            #            the cost is the ORDER BY, and it is inevitable if we want
            #            relevant results for the next step, otherwise we'd return
            #            a random selection of `limit` results.
            query = ('''SELECT partner.id FROM res_partner partner
                                          LEFT JOIN res_partner company
                                               ON partner.parent_id = company.id
                        WHERE partner.email ''' + operator + ''' %(name)s OR
                              CASE
                                   WHEN company.id IS NULL OR partner.is_company
                                       THEN partner.name
                                   ELSE company.name || ', ' || partner.name
                              END ''' + operator + ''' %(name)s
                        ORDER BY
                              CASE
                                   WHEN company.id IS NULL OR partner.is_company
                                       THEN partner.name
                                   ELSE company.name || ', ' || partner.name
                              END''')
            if limit:
                query += ' limit %(limit)s'
                query_args['limit'] = limit
            cr.execute(query, query_args)
            ids = map(lambda x: x[0], cr.fetchall())
            ids = self.search(cr, uid, [('id', 'in', ids)] + args, limit=limit, context=context)
            if ids:
                return self.name_get(cr, uid, ids, context)
        return super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)


    def _display_address(self, cr, uid, address, without_company=False, context=None):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = address.country_id and address.country_id.address_format or \
              "%(street)s\n%(street2)s\n%(city)s %(state_name)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code': address.country_id and address.country_id.code or '',
            'country_name': address.country_id and address.country_id.name or '',
            'company_name': address.parent_id and address.parent_id.name or '',
        }
        for field in self._address_fields(cr, uid, context=context):
            args[field] = getattr(address, field) or ''
#         if without_company:
#             args['company_name'] = ''
#         elif address.parent_id:
#             address_format = '%(company_name)s\n' + address_format
        return address_format % args
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
