from openerp import tools
from openerp.osv import fields,osv


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
            cr.execute("select id,to_char(date::timestamp with time zone, 'MM'::text) AS month from account_analytic_line where id in (%s)"%(line_str))
            item_id_month=[x for x in cr.fetchall()]
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

 SELECT min(a.id) AS id,

        count(DISTINCT a.id) AS nbr,

        to_char(a.date::timestamp with time zone, 'YYYY'::text) AS year,

        to_char(a.date::timestamp with time zone, 'MM'::text) AS month,

        a.company_id,

        rc.currency_id,

        a.account_id,

        cbl.crossovered_budget_id,

        cbl.general_budget_id,

        sum(a.amount) AS amount,

        sum(a.unit_amount) AS unit_amount,

        round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) AS planned_amount,

        round(sum(a.amount) / (round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) / 100::numeric), 0) AS variance

   FROM account_analytic_line a, account_analytic_account analytic, crossovered_budget cb, crossovered_budget_lines cbl, account_budget_post abp, res_company rc

  WHERE analytic.id = a.account_id AND abp.id = cbl.general_budget_id AND cb.id = cbl.crossovered_budget_id AND cbl.analytic_account_id = a.account_id

    AND a.date >= cbl.date_from AND a.date <= cbl.date_to AND rc.id = cbl.company_id 

    AND (EXISTS ( SELECT 'X'

           FROM account_budget_rel abr

          WHERE abr.budget_id = abp.id AND a.general_account_id = abr.account_id))

  GROUP BY to_char(a.date::timestamp with time zone, 'YYYY'::text), to_char(a.date::timestamp with time zone, 'MM'::text), a.company_id, rc.currency_id, a.account_id, cbl.crossovered_budget_id, cbl.general_budget_id

UNION

 SELECT min(cbl.id) AS id,

        0 AS nbr,

        to_char(cbl.date_from::timestamp with time zone, 'YYYY'::text) AS year,

        to_char(cbl.date_from::timestamp with time zone, 'MM'::text) AS month,

        cbl.company_id,

        rc.currency_id,

        cbl.analytic_account_id,

        cbl.crossovered_budget_id,

        cbl.general_budget_id,

        0 AS amount,

        0 AS unit_amount,

        sum(cbl.planned_amount) AS planned_amount, 

        0 AS variance

   FROM account_analytic_account analytic, crossovered_budget cb, crossovered_budget_lines cbl, account_budget_post abp, res_company rc

  WHERE analytic.id = cbl.analytic_account_id AND abp.id = cbl.general_budget_id AND cb.id = cbl.crossovered_budget_id AND rc.id = cbl.company_id

    AND (not EXISTS ( SELECT 'X'

           FROM account_analytic_line aal, account_budget_rel abr

          WHERE aal.account_id = cbl.analytic_account_id AND abr.budget_id = abp.id AND aal.general_account_id = abr.account_id AND aal.date >= cbl.date_from AND aal.date <= cbl.date_to))

  GROUP BY to_char(cbl.date_from::timestamp with time zone, 'YYYY'::text), to_char(cbl.date_from::timestamp with time zone, 'MM'::text),

           cbl.company_id, rc.currency_id, cbl.analytic_account_id, cbl.crossovered_budget_id, cbl.general_budget_id;
            """)

budget_entries_report()

