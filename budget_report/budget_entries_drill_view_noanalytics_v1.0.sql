CREATE OR REPLACE VIEW budget_entries_drill AS 
 SELECT a.id,
        to_char(a.date::timestamp with time zone, 'YYYY'::text) AS year,
        to_char(a.date::timestamp with time zone, 'MM'::text) AS month,
        a.company_id,
        cbl.crossovered_budget_id,
        cbl.general_budget_id
   FROM account_move_line a, crossovered_budget_lines cbl, account_budget_post abp
  WHERE abp.id = cbl.general_budget_id 
    AND a.date >= cbl.date_from
	AND a.date <= cbl.date_to
    AND (EXISTS ( SELECT 'X'
           FROM account_budget_rel abr
          WHERE abr.budget_id = abp.id AND a.account_id = abr.account_id))
  
  
