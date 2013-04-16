from openerp import tools
from openerp.osv import fields,osv

class budget_entries_report(osv.osv):
    _name = "budget.entries.report"
    _description = "Budget Entries Statistics"
    _auto = False
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
        'account_id': fields.many2one('account.analytic.account', 'Account', required=False),
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
        tools.drop_view_if_exists(cr, 'budget_entries_report')
        cr.execute("""
CREATE OR REPLACE VIEW budget_entries_report AS 
 SELECT min(a.id) AS id, count(DISTINCT a.id) AS nbr, to_char(a.date::timestamp with time zone, 'YYYY'::text) AS year, to_char(a.date::timestamp with time zone, 'MM'::text) AS month, a.company_id, a.currency_id, a.account_id, cbl.crossovered_budget_id, cbl.general_budget_id, sum(a.amount) AS amount, sum(a.unit_amount) AS unit_amount, round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) AS planned_amount, round(sum(a.amount) / (round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) / 100::numeric), 0) AS variance
   FROM account_analytic_line a, account_analytic_account analytic, crossovered_budget cb, crossovered_budget_lines cbl, account_budget_post abp
  WHERE analytic.id = a.account_id AND abp.id = cbl.general_budget_id AND cb.id = cbl.crossovered_budget_id AND cbl.analytic_account_id = a.account_id AND a.date >= cbl.date_from AND a.date <= cbl.date_to AND (EXISTS ( SELECT 'X'
           FROM account_budget_rel abr
          WHERE abr.budget_id = abp.id AND a.general_account_id = abr.account_id))
  GROUP BY to_char(a.date::timestamp with time zone, 'YYYY'::text), to_char(a.date::timestamp with time zone, 'MM'::text), a.company_id, a.currency_id, a.account_id, cbl.crossovered_budget_id, cbl.general_budget_id;
            """)

budget_entries_report()

