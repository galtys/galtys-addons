from openerp import tools
from openerp.osv import fields,osv
from openerp.tools.misc import file_open

class budget_entries_wizard(osv.osv_memory):
    _name = "budget.entries.wizard"
    _description = "Open Entries Wizard"
    _columns = {
        'name': fields.char('Name'),
       }

    def action_open_entries(self, cr, uid, ids, context=None):
        print 'update pricelist', ids, context
        active_ids=context['active_ids']
        for w in self.browse(cr, uid, ids):
            br_items=self.pool.get('budget.entries.report').browse(cr, uid, active_ids)
            acc_ids=[br.account_id.id for br in br_items]
            gen_ids=[[x.id for x in br.general_budget_id.account_ids] for br in br_items]
            month_ids=[br.month for br in br_items]
            print acc_ids, gen_ids
            #['|',('create_date','>', self.delta),('write_date','>', self.delta),

            args=[('account_id','in',acc_ids),
                  ('general_account_id','in',reduce(lambda x,y:x+y,gen_ids))]
            
            line_ids=self.pool.get('account.analytic.line').search(cr, uid, args)
            line_str=','.join( map(str,line_ids))
            if line_str:
                cr.execute("select id,to_char(date::timestamp with time zone, 'MM'::text) AS month from account_analytic_line where id in (%s)"%(line_str))
                item_id_month=[x for x in cr.fetchall()]
            else:
                item_id_month=[]
            print 'filter months', item_id_month, month_ids
            out_ids=[]
            for line_id, month in item_id_month:
                print 'line, month', line_id, month
                if month in month_ids:
                    out_ids.append(line_id)
                else:
                    print 'not in selection', line_id, month, month_ids
            print 'out_ids', out_ids
            #open_lines= [x[0] for x in cr.fetchall() if x[1] in month_ids]
            #print 'open lines', open_lines
            #line_ids=self.pool.get('account.analytic.line').search(cr, uid, [])
            #print 'account line items', line_ids
        return {
            'domain': "[('id','in', [" + ','.join(map(str, out_ids)) + "])]",
            
            #'domain': str(args),
            'name': 'Analytic Items',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            #'view_id': False,
            'type': 'ir.actions.act_window',
            #'search_view_id': id['res_id']
        }

budget_entries_wizard()



class budget_entries_report(osv.osv):
    _name = "budget.entries.report_noa"
    _description = "Budget Entries Statistics"
    _auto = False
    _rec_name = 'month'
    _columns = {
        #'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        #'day': fields.char('Day', size=128, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        #'user_id': fields.many2one('res.users', 'User',readonly=True),
        #'name': fields.char('Description', size=64, readonly=True),
        #'partner_id': fields.many2one('res.partner', 'Partner'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        #'currency_id': fields.many2one('res.currency', 'Currency', required=True),
#        'account_id': fields.many2one('account.analytic.account', 'Account', required=False),
        #'general_account_id': fields.many2one('account.account', 'General Account', required=True),
        #'journal_id': fields.many2one('account.analytic.journal', 'Journal', required=True),
        #'move_id': fields.many2one('account.move.line', 'Move', required=True),
        #'product_id': fields.many2one('product.product', 'Product', required=True),
        #'product_uom_id': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'crossovered_budget_id': fields.many2one('crossovered.budget', 'Budget', required=False),
        'general_budget_id': fields.many2one('account.budget.post', 'Budget Position', required=False),
        'amount': fields.float('Amount', readonly=True),
        'planned_amount': fields.float('Planned Amount', readonly=True),
        'unit_amount': fields.float('Quantity', readonly=True),
        'variance': fields.float('Variance', readonly=True),
        'nbr': fields.integer('#Entries', readonly=True),
    }
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'budget_entries_report_noa')
        sql_fn='budget_entries_view_noanalytics.sql'
        fp=file_open('budget_report/%s'%sql_fn)
        query=fp.read()       
        fp.close()
        cr.execute(query)
budget_entries_report()

