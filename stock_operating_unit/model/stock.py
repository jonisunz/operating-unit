# © 2016-2017 Eficent Business and IT Consulting Services S.L.
# © 2016-2017 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    def _default_operating_unit(self):
        if self.company_id:
            company = self.company_id
        else:
            company = self.env['res.company']._company_default_get(self._name)
        for ou in self.env.user.operating_unit_ids:
            if company == self.company_id:
                self.operating_unit_id = ou
                return

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        default=_default_operating_unit,
        required=True
    )

    @api.multi
    @api.constrains('operating_unit_id', 'company_id')
    def _check_company_operating_unit(self):
        for rec in self:
            if (rec.operating_unit_id and
                    rec.company_id != rec.operating_unit_id.company_id):
                raise ValidationError(
                    _('Configuration error\n'
                      'The Company in the Stock Warehouse '
                      'and in the Operating Unit must be the same.')
                )


class StockLocation(models.Model):
    _inherit = 'stock.location'

    def _compute_operating_unit(self):
        for record in self:
            record.operating_unit_id = record.get_warehouse().operating_unit_id

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        compute='_compute_operating_unit',
        store=True,
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Requesting Operating Unit',
        readonly=1,
    )

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        if self.picking_type_id:
            unit = self.picking_type_id.warehouse_id.operating_unit_id
            self.operating_unit_id = unit
        return res

    @api.multi
    @api.constrains('operating_unit_id', 'company_id')
    def _check_company_operating_unit(self):
        for rec in self:
            if (rec.company_id and rec.operating_unit_id and
                    rec.company_id != rec.operating_unit_id.company_id):
                raise ValidationError(
                    _('Configuration error\n'
                      'The Company in the Stock Picking '
                      'and in the Operating Unit must be the same.')
                )


class StockMove(models.Model):
    _inherit = 'stock.move'

    operating_unit_id = fields.Many2one(
        related='location_id.operating_unit_id',
        string='Source Location Operating Unit',
        readonly=True,
    )
    operating_unit_dest_id = fields.Many2one(
        related='location_dest_id.operating_unit_id',
        string='Dest. Location Operating Unit',
        readonly=True,
    )

    @api.multi
    @api.constrains('location_id', 'picking_id', 'location_dest_id')
    def _check_stock_move_operating_unit(self):
        for stock_move in self:
            if not stock_move.operating_unit_id:
                return True
            operating_unit = stock_move.operating_unit_id
            operating_unit_dest = stock_move.operating_unit_dest_id
            if (stock_move.location_id and
                stock_move.location_id.operating_unit_id and
                stock_move.picking_id and
                operating_unit != stock_move.picking_id.operating_unit_id
                ) and (
                stock_move.location_dest_id and
                stock_move.location_dest_id.operating_unit_id and
                stock_move.picking_id and
                operating_unit_dest != stock_move.picking_id.operating_unit_id
            ):
                raise ValidationError(
                    _('Configuration error\n'
                      'The Stock moves must be related to a location '
                      '(source or destination) that belongs to the '
                      'requesting Operating Unit.')
                )
