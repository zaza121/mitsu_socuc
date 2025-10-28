# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MultiWarehouseSupplyLine(models.TransientModel):
    _name = 'multi.warehouse.supply.line'
    _description = 'Ligne : destination / produit / quantité'

    wizard_id = fields.Many2one(
        'multi.warehouse.supply.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Emplacement destination',
        required=True,
        domain="[('usage','=','internal')]",
    )
    product_id = fields.Many2one(
        'product.product',
        string='Produit',
        required=True
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unité',
        required=True
    )
    qty = fields.Float(
        string='Quantité',
        required=True,
        default=0.0
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Met automatiquement l’UoM par défaut du produit."""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id


class MultiWarehouseSupplyWizard(models.TransientModel):
    _name = 'multi.warehouse.supply.wizard'
    _description = 'Approvisionner plusieurs entrepôts'

    source_location_id = fields.Many2one(
        'stock.location',
        string='Emplacement source',
        required=True,
        domain="[('usage','=','internal')]",
    )
    line_ids = fields.One2many(
        'multi.warehouse.supply.line',
        'wizard_id',
        string='Lignes'
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string="Type d'opération",
        help="Type de picking utilisé pour les transferts internes"
    )
    group_into_single_picking = fields.Boolean(
        string="Regrouper en 1 transfert (attention si règles différentes)",
        default=False,
    )
    auto_confirm = fields.Boolean(
        string="Confirmer automatiquement les picking(s)",
        default=True,
    )

    @api.model
    def default_get(self, fields_list):
        """Met automatiquement un type d’opération interne par défaut."""
        res = super().default_get(fields_list)
        company = self.env.company
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', company.id)
        ], limit=1)
        if picking_type:
            res['picking_type_id'] = picking_type.id
        return res

    def action_create_transfers(self):
        """Crée les transferts internes pour chaque ligne."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Ajoutez au moins une ligne avec une destination, un produit et une quantité."))

        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        StockMoveLine = self.env['stock.move.line']
        created_pickings = self.env['stock.picking']

        # Vérification des quantités
        for ln in self.line_ids:
            if ln.qty <= 0:
                raise UserError(_("La quantité doit être > 0 pour %s") % (ln.product_id.display_name,))

        # Cas regroupé en un seul picking
        if self.group_into_single_picking:
            picking_vals = {
                'picking_type_id': self.picking_type_id.id if self.picking_type_id else False,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.line_ids[0].dest_location_id.id,
                'origin': _('Approvisionnement multi-entrepôts'),
            }
            picking = StockPicking.create(picking_vals)

            for ln in self.line_ids:
                move_vals = {
                    'name': ln.product_id.display_name,
                    'product_id': ln.product_id.id,
                    'product_uom_qty': ln.qty,
                    'product_uom': ln.product_uom_id.id,
                    'picking_id': picking.id,
                    'location_id': self.source_location_id.id,
                    'location_dest_id': ln.dest_location_id.id,
                    'company_id': self.env.company.id,
                }
                StockMove.create(move_vals)
            created_pickings += picking

        # Cas un picking par destination
        else:
            grouped = {}
            for ln in self.line_ids:
                grouped.setdefault(ln.dest_location_id.id, []).append(ln)

            for dest_id, lines in grouped.items():
                dest_loc = self.env['stock.location'].browse(dest_id)
                picking_vals = {
                    'picking_type_id': self.picking_type_id.id if self.picking_type_id else False,
                    'location_id': self.source_location_id.id,
                    'location_dest_id': dest_loc.id,
                    'origin': _('Approvisionnement vers %s') % dest_loc.display_name,
                }
                picking = StockPicking.create(picking_vals)

                for ln in lines:
                    move_vals = {
                        'name': ln.product_id.display_name,
                        'product_id': ln.product_id.id,
                        'product_uom_qty': ln.qty,
                        'product_uom': ln.product_uom_id.id,
                        'picking_id': picking.id,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': dest_loc.id,
                        'company_id': self.env.company.id,
                    }
                    StockMove.create(move_vals)
                created_pickings += picking

        # Auto-confirmation + assignation
        if self.auto_confirm and created_pickings:
            created_pickings.action_confirm()
            try:
                created_pickings.action_assign()
            except Exception:
                pass

            # Préparer les move lines pour les produits traçables
            for picking in created_pickings:
                for move in picking.move_ids:
                    product = move.product_id
                    if product.tracking != 'none' and move.product_uom_qty > 0:
                        StockMoveLine.create({
                            'move_id': move.id,
                            'picking_id': picking.id,
                            'product_id': product.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'qty_done': 0.0,  # à remplir par l'utilisateur
                        })

        # Retourne une vue sur les transferts créés
        return {
            'name': _('Transferts créés'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_pickings.ids)],
            'context': dict(self.env.context),
            'target': 'current',
        }
