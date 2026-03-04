# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools


class MitsuTaskAllocation(models.Model):
    _name = 'mitsu.task.allocation'
    _description = 'Analyse de Rentabilité Projet (Basé sur le Planning)'
    _auto = False  # Vue SQL

    # --- IDENTITÉ ---
    project_id = fields.Many2one('project.project', string='Projet', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employé', readonly=True)
    task_id = fields.Many2one('project.task', string='Tâche', readonly=True)
    sale_line_id = fields.Many2one('sale.order.line', string='Article de bon de commande', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Compte Analytique', readonly=True)

    # --- PÉRIODE ---
    year = fields.Integer(string='Année', readonly=True)
    month = fields.Char(string='Mois', readonly=True)

    # --- TEMPS ---
    unit_price = fields.Float(string='Prix unitaire', readonly=True)
    time_allocated = fields.Float(string='Temps alloué (SO)', readonly=True)
    time_planned = fields.Float(string='Temps planifié', readonly=True)
    time_realized = fields.Float(string='Temps réalisé', readonly=True)
    time_to_plan = fields.Float(string='Temps à planifier', readonly=True)
    time_to_realize = fields.Float(string='Temps à réaliser', readonly=True)

    # --- FINANCES ---
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True)
    ca_previsionnel = fields.Monetary(string='CA Prévisionnel', readonly=True)
    cout_previsionnel = fields.Monetary(string='Coût Prévisionnel', readonly=True)
    marge_previsionnelle = fields.Monetary(string='Marge Prévisionnelle', readonly=True)

    ca_realise = fields.Monetary(string='CA Réalisé', readonly=True)
    cout_realise = fields.Monetary(string='Coût Réalisé', readonly=True)
    marge_realisee = fields.Monetary(string='Marge Réalisée', readonly=True)

    boni_mali = fields.Monetary(string='Boni / Mali', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH planning_summary AS (
                    -- Agrégation du planning
                    SELECT
                        s.project_id,
                        s.task_id,
                        s.employee_id,
                        TO_CHAR(s.start_datetime, 'YYYY')::integer AS year,
                        TO_CHAR(s.start_datetime, 'YYYY-MM') AS month,
                        SUM(s.allocated_hours) AS time_planned
                    FROM planning_slot s
                    WHERE s.project_id IS NOT NULL
                      AND s.employee_id IS NOT NULL
                    GROUP BY s.project_id, s.task_id, s.employee_id, year, month
                ),
                timesheet_summary AS (
                    -- Agrégation des feuilles de temps
                    SELECT
                        project_id,
                        task_id,
                        employee_id,
                        TO_CHAR(date, 'YYYY')::integer AS year,
                        TO_CHAR(date, 'YYYY-MM') AS month,
                        SUM(unit_amount) AS time_realized
                    FROM account_analytic_line
                    GROUP BY project_id, task_id, employee_id, year, month
                )
                SELECT
                    row_number() OVER () AS id,

                    COALESCE(p.project_id, t.project_id) AS project_id,
                    COALESCE(p.task_id, t.task_id) AS task_id,
                    COALESCE(p.employee_id, t.employee_id) AS employee_id,
                    COALESCE(p.year, t.year) AS year,
                    COALESCE(p.month, t.month) AS month,

                    -- Liens projet / vente
                    task.sale_line_id AS sale_line_id,
                    prj.account_id AS analytic_account_id,
                    sol.price_unit AS unit_price,
                    sol.product_uom_qty AS time_allocated,

                    -- Temps
                    COALESCE(p.time_planned, 0) AS time_planned,
                    COALESCE(t.time_realized, 0) AS time_realized,
                    (COALESCE(sol.product_uom_qty, 0) - COALESCE(p.time_planned, 0)) AS time_to_plan,
                    (COALESCE(p.time_planned, 0) - COALESCE(t.time_realized, 0)) AS time_to_realize,

                    -- Devise
                    cmp.currency_id AS currency_id,

                    -- =========================
                    -- PRÉVISIONNEL (basé sur SO)
                    -- =========================
                    (COALESCE(sol.product_uom_qty, 0) * COALESCE(sol.price_unit, 0)) AS ca_previsionnel,
                    (COALESCE(sol.product_uom_qty, 0) * COALESCE(emp.hourly_cost, 0)) AS cout_previsionnel,
                    (
                        (COALESCE(sol.product_uom_qty, 0) * COALESCE(sol.price_unit, 0))
                        - (COALESCE(sol.product_uom_qty, 0) * COALESCE(emp.hourly_cost, 0))
                    ) AS marge_previsionnelle,

                    -- =========================
                    -- RÉALISÉ
                    -- =========================
                    (COALESCE(t.time_realized, 0) * COALESCE(sol.price_unit, 0)) AS ca_realise,
                    (COALESCE(t.time_realized, 0) * COALESCE(emp.hourly_cost, 0)) AS cout_realise,
                    (
                        COALESCE(t.time_realized, 0)
                        * (COALESCE(sol.price_unit, 0) - COALESCE(emp.hourly_cost, 0))
                    ) AS marge_realisee,

                    -- =========================
                    -- BONI / MALI
                    -- =========================
                    (
                        -- Marge réalisée
                        (COALESCE(t.time_realized, 0)
                            * (COALESCE(sol.price_unit, 0) - COALESCE(emp.hourly_cost, 0))
                        )
                        -- Moins marge prévisionnelle
                        - (
                            (COALESCE(sol.product_uom_qty, 0) * COALESCE(sol.price_unit, 0))
                            - (COALESCE(sol.product_uom_qty, 0) * COALESCE(emp.hourly_cost, 0))
                        )
                    ) AS boni_mali

                FROM planning_summary p
                FULL OUTER JOIN timesheet_summary t
                    ON p.project_id = t.project_id
                   AND p.task_id = t.task_id
                   AND p.employee_id = t.employee_id
                   AND p.month = t.month

                LEFT JOIN project_project prj
                    ON prj.id = COALESCE(p.project_id, t.project_id)

                LEFT JOIN res_company cmp
                    ON cmp.id = prj.company_id

                LEFT JOIN project_task task
                    ON task.id = COALESCE(p.task_id, t.task_id)

                LEFT JOIN sale_order_line sol
                    ON sol.id = task.sale_line_id

                LEFT JOIN hr_employee emp
                    ON emp.id = COALESCE(p.employee_id, t.employee_id)
            )
        """)
