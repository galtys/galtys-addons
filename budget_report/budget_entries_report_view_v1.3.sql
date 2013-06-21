-- View: budget_entries_report

-- DROP VIEW budget_entries_report;

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
        case when round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) = 0 then 0 else round(sum(a.amount) / (round(sum(cbl.planned_amount) / count(DISTINCT a.id)::numeric, 2) / 100::numeric), 0) end AS variance
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

ALTER TABLE budget_entries_report
  OWNER TO jan;
