import time

from report import report_sxw
import pooler
from dateutil.parser import parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.init_bal_sum = 0.0
        self.total = []
        self.headings = []
        self.headings = self._headings()
        self.localcontext.update( {
            'adr_get': self._adr_get,
            'lines': self._lines,
            'total': self._get_total,
            'initial': self._get_initial,
            'total_heading': self._get_headings,
        })
    
    def _get_total(self, key):
        """
        Returns float value of list at position key
        @param key: an int
        """ 
        return self.total[key]
   
    def _get_initial(self):
        """
        @return: float initial balance
        """
        return self.init_bal_sum
    
    def _headings(self):
        """
        @return: a list of headings for aging
        """
        if self.localcontext['form']['aging'] == 'months':
            return ['Current', '1 Month', '2 Month', '3 Months +', 'Total']
        else:
            days = self.localcontext['form']['days']
            return [('0-'+str(days)+' days'), (str(days+1)+'-'+str(days*2)+' days'), str(days*2+1)+'-'+str(days*3)+' days', str(days*3+1)+' days+', 'Total']
 
    def _get_headings(self, key):
        """
        @return: value of list at position key
        @param key: an int
        """ 
        return self.headings[key]
  
    def _adr_get(self, partner, type):
        """
        @return: a res.partner.address browse record of partner and type
        @param partner: usually latest partner browse record - 'o'
        @param type: the type of address e.g. 'invoice' 
        """
        res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
        addresses = res_partner.address_get(self.cr, self.uid, [partner.id], [type])
        
        print 'ADDRESS', addresses
        if addresses:
            #res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner').browse(self.cr, self.uid, [addresses[type]])
            res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner').browse(self.cr, self.uid, [partner.id])
        return res_partner_address or False

    def _get_index(self, date, base_date):  
        """
        This function provides an index for aging and inclusion purposes.
        @return: int which can be used to select/update an item in a list.
        @param date: the date of an invoice
        @param base_date: the date the report is based on
        """    
        inv_date = parse(date)
        if self.localcontext['form']['aging'] == 'months':
            base_month = base_date.month
            base_year = base_date.year
            inv_month = inv_date.month
            inv_year = inv_date.year
            if base_year < inv_year: return 0
            if base_year > inv_year: base_month+=12*(base_year-inv_year)
            if inv_month > base_month: return 0
            return min((base_month - inv_month),3)
        else:
            days = self.localcontext['form']['days']
            delta = base_date-inv_date
            index = 0
            index = max(delta.days / days, 0)
            return min(index,3)

    def _lines(self, partner):
        """
        @return: list of dictionaries based on account.move.lines. To
        reduce search calls move_ids are calculated once in wizard and
        accessed via localcontext rather than param.
        @param partner: usually latest partner browse record - 'o' 
        """
        self.total = [0.0 for i in range(5)]
        self.init_bal_sum = 0.0
        result = []
        print self.localcontext.keys(), self.localcontext['date']
        ids = self.localcontext['move_ids'][str(partner.id)]
        move_line_pool = pooler.get_pool(self.cr.dbname).get('account.move.line')
        moves = move_line_pool.browse(self.cr, self.uid, ids)
        base_date = parse(self.localcontext['date'])
        
        for line in moves:
            if line.credit and line.reconcile_partial_id:
                continue
            if parse(line.date) > base_date:
                continue
            original_amount = line.credit or line.debit or 0.0
            amount_unreconciled = line.amount_residual_currency
            rs = {
                'name':line.move_id.name,
                'description': line.ref,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': line.credit and original_amount*-1 or original_amount,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': line.credit and amount_unreconciled*-1 or amount_unreconciled,
            }

            if self.localcontext['form']['statement_type'] == 'open' or self._get_index(line.date, base_date) == 0:
                if rs['amount_unreconciled']>0.0001:
                    result.append(rs)
            else:
                self.init_bal_sum+=rs['amount_unreconciled']
            self.total[4]+=rs['amount_unreconciled']
            self.total[self._get_index(line.date, base_date)]+=rs['amount_unreconciled']
        return result

class Overdue(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Overdue, self).__init__(cr, uid, name, context=context)
        self.init_bal_sum = 0.0
        self.total = []
        self.headings = []
        self.headings = self._headings()
        form = {'statement_type': 'open' }
        self.localcontext.update( {
            'time': time,
            'adr_get': self._adr_get,
            'getLines': self._lines_get,
            'tel_get': self._tel_get,
            'message': self._message,
            'total': self._get_total,
            'initial': self._get_initial,
            'total_heading': self._get_headings,
            #'form': form,

        })
        print 100*'_'
        print self.localcontext
        self.context = context
    def _get_total(self, key):
        """
        Returns float value of list at position key
        @param key: an int
        """ 
        return self.total[key]
   
    def _get_initial(self):
        """
        @return: float initial balance
        """
        return self.init_bal_sum
    
    def _headings(self):
        """
        @return: a list of headings for aging
        """
        if 1:#self.localcontext['form']['aging'] == 'months':
            return ['Current', '1 Month', '2 Month', '3 Months +', 'Total']
        else:
            days = self.localcontext['form']['days']
            return [('0-'+str(days)+' days'), (str(days+1)+'-'+str(days*2)+' days'), str(days*2+1)+'-'+str(days*3)+' days', str(days*3+1)+' days+', 'Total']
 
    def _get_headings(self, key):
        """
        @return: value of list at position key
        @param key: an int
        """ 
        return self.headings[key]

    def _adr_get(self, partner, type):
        res = []
        res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
        res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner.address')
        addresses = res_partner.address_get(self.cr, self.uid, [partner.id], [type])
        adr_id = addresses and addresses[type] or False
        result = {
                  'name': False,
                  'street': False,
                  'street2': False,
                  'city': False,
                  'zip': False,
                  'state_id':False,
                  'country_id': False,
                 }
        if adr_id:
            result = res_partner_address.read(self.cr, self.uid, [adr_id], context=self.context.copy())
            result[0]['country_id'] = result[0]['country_id'] and result[0]['country_id'][1] or False
            result[0]['state_id'] = result[0]['state_id'] and result[0]['state_id'][1] or False
            return result

        res.append(result)
        return res

    def _tel_get(self,partner):
        if not partner:
            return False
        res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner.address')
        res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
        addresses = res_partner.address_get(self.cr, self.uid, [partner.id], ['invoice'])
        adr_id = addresses and addresses['invoice'] or False
        if adr_id:
            adr=res_partner_address.read(self.cr, self.uid, [adr_id])[0]
            return adr['phone']
        else:
            return partner.address and partner.address[0].phone or False
        return False
    def _get_index(self, date, base_date):  
        """
        This function provides an index for aging and inclusion purposes.
        @return: int which can be used to select/update an item in a list.
        @param date: the date of an invoice
        @param base_date: the date the report is based on
        """    
        inv_date = parse(date)
        if 1:#self.localcontext['form']['aging'] == 'months':
            base_month = base_date.month
            base_year = base_date.year
            inv_month = inv_date.month
            inv_year = inv_date.year
            if base_year < inv_year: return 0
            if base_year > inv_year: base_month+=12*(base_year-inv_year)
            if inv_month > base_month: return 0
            return min((base_month - inv_month),3)
        else:
            days = self.localcontext['form']['days']
            delta = base_date-inv_date
            index = 0
            index = max(delta.days / days, 0)
            return min(index,3)

    def _lines_get(self, partner):
        moveline_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
        movelines = moveline_obj.search(self.cr, self.uid,
                [('partner_id', '=', partner.id),
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), ('reconcile_id', '=', False)])
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        base_date = parse(time.strftime('%Y-%m-%d'))
        #base_date = parse('2012-09-12')
        result = []
        self.total = [0.0 for i in range(5)]
        for line in movelines:
            #print [line.date]
            #amount_unreconciled = line.amount_residual_currency
            #xx = line.credit and amount_unreconciled*-1 or amount_unreconciled

            original_amount = line.credit or line.debit or 0.0
            amount_unreconciled = line.amount_residual#_currency
            account_id = {'type': line.account_id.type }
            rs = {
                'name':line.move_id.name,
                'description': line.ref,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': line.credit and original_amount*-1 or original_amount,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': line.credit and amount_unreconciled*-1 or amount_unreconciled,
                'debit': line.debit,
                'credit': line.credit,
                'account_id': account_id,
                'reconcile_partial_id': line.reconcile_partial_id,

            }
            rs['invoice_total'] = rs['amount_original']
            rs['amount_paid'] = rs['amount_original'] - rs['amount_unreconciled']
            rs['outstanding_balance'] = rs['amount_unreconciled']
            #print rs['name'], rs['amount_original'], amount_unreconciled, rs['amount_unreconciled']
            #print rs['name'], rs['reconcile_partial_id']
            result.append( rs  )
            self.total[4]+=rs['amount_unreconciled']
            self.total[self._get_index(line.date, base_date)]+= rs['amount_unreconciled']
            #return result
            
        return result#movelines

    def _message(self, obj, company):
        company_pool = pooler.get_pool(self.cr.dbname).get('res.company')
        message = company_pool.browse(self.cr, self.uid, company.id, {'lang':obj.lang}).overdue_msg


#from netsvc import Service
#del Service._services['report.account.overdue']

#report_sxw.report_sxw('report.account.overdue', 'res.partner',
#                      'addons/account/report/account_print_overdue.rml', parser=Parser)
report_sxw.report_sxw('report.account.overdue2', 'res.partner',
                      'addons/partner_statement/statement.rml', parser=Parser)
