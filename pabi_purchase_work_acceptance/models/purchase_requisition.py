# -*- coding: utf-8 -*-

from openerp import fields, models, api


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    fine_condition = fields.Selection(
        selection=[
            ('day', 'Day'),
            ('date', 'Date'),
        ],
        string='Fine Condition',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    date_fine = fields.Date(
        string='Fine Date',
        default=lambda self: fields.Date.context_today(self),
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    fine_num_days = fields.Integer(
        string='No. of Days',
        default=15,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    fine_rate = fields.Float(
        string='Fine Rate',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.multi
    def make_purchase_order(self, partner_id):
        res = super(PurchaseRequisition, self).\
            make_purchase_order(partner_id)
        Order = self.env['purchase.order']
        for order_id in res.itervalues():
            orders = Order.search([('id', '=', order_id)])
            for order in orders:
                order.write({
                    'fine_rate': self.fine_rate,
                    'fine_condition': self.fine_condition,
                    'date_fine': self.date_fine,
                    'fine_num_days': self.fine_num_days,
                })
        return res
