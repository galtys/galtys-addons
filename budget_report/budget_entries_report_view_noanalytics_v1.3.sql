-- View: budget_entries_report

-- DROP VIEW budget_entries_report;

CREATE OR REPLACE VIEW budget_entries_report AS 
 SELECT min(a.id) AS id,
        count(DISTINCT a.id) AS nbr,
        to_char(a.date::timestamp with time zone, 'YYYY'::text) AS year,
        to_char(a.date::timestamp with time zone, 'MM'::text) AS month,
        a.company_id,
        rc.currency_id,
        cbl.crossovered_budget_id,
        cbl.general_budget_id,
        sum(a.debit - a.credit) AS amount,
        sum(a.quantity) AS unit_amount,
        round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) AS planned_amount,
        sum(a.debit - a.credit) - round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) AS variance
   FROM account_move_line a, crossovered_budget cb, crossovered_budget_lines cbl, account_budget_post abp, res_company rc
  WHERE abp.id = cbl.general_budget_id AND cb.id = cbl.crossovered_budget_id
    AND a.date >= cbl.date_from AND a.date <= cbl.date_to AND rc.id = cbl.company_id 
    AND (EXISTS ( SELECT 'X'
           FROM account_budget_rel abr
          WHERE abr.budget_id = abp.id AND a.account_id = abr.account_id))
  GROUP BY to_char(a.date::timestamp with time zone, 'YYYY'::text), to_char(a.date::timestamp with time zone, 'MM'::text), a.company_id, rc.currency_id, a.account_id, cbl.crossovered_budget_id, cbl.general_budget_id

UNION
 SELECT min(cbl.id) AS id,
        0 AS nbr,
        to_char(cbl.date_from::timestamp with time zone, 'YYYY'::text) AS year,
        to_char(cbl.date_from::timestamp with time zone, 'MM'::text) AS month,
        cbl.company_id,
        rc.currency_id,
        cbl.crossovered_budget_id,
        cbl.general_budget_id,
        0 AS amount,
        0 AS unit_amount,
        sum(cbl.planned_amount) AS planned_amount, 
        0 - sum(cbl.planned_amount) AS variance
   FROM crossovered_budget cb, crossovered_budget_lines cbl, account_budget_post abp, res_company rc
  WHERE abp.id = cbl.general_budget_id AND cb.id = cbl.crossovered_budget_id AND rc.id = cbl.company_id
    AND (not EXISTS ( SELECT 'X'
           FROM account_move_line aml, account_budget_rel abr
          WHERE abr.budget_id = abp.id AND aml.account_id = abr.account_id AND aml.date >= cbl.date_from AND aml.date <= cbl.date_to))
  GROUP BY to_char(cbl.date_from::timestamp with time zone, 'YYYY'::text), to_char(cbl.date_from::timestamp with time zone, 'MM'::text),
           cbl.company_id, rc.currency_id, cbl.crossovered_budget_id, cbl.general_budget_id;

ALTER TABLE budget_entries_report
  OWNER TO ???????;
