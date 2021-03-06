# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
import datetime
import openerp.addons.decimal_precision as dp
from openerp.addons.l10n_th_amount_text.amount_to_text_th \
    import amount_to_text_th
from openerp.exceptions import ValidationError


class PurchaseWorkAcceptance(models.Model):
    _name = 'purchase.work.acceptance'
    _description = 'Purchase Work Acceptance'

    _STATES = [
        ('draft', 'Draft'),
        ('evaluation', 'Evaluation'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
    ]

    @api.model
    @api.depends('date_receive', 'date_scheduled_end')
    def _compute_fine_amount_to_word_th(self):
        res = {}
        minus = False
        for acceptance in self:
            order = acceptance.order_id
            amount_total = acceptance.total_fine
            if amount_total < 0:
                minus = True
                amount_total = -amount_total
            amount_text = amount_to_text_th(amount_total,
                                            order.currency_id.name)
            acceptance.amount_total_fine_text_th = minus and\
                'ลบ' + amount_text or amount_text
        return res

    @api.model
    @api.depends('date_receive', 'date_contract_end')
    def _compute_fine_per_day_to_word_th(self):
        res = {}
        minus = False
        for acceptance in self:
            order = acceptance.order_id
            fine_per_day = acceptance.fine_per_day
            if fine_per_day < 0:
                minus = True
                fine_per_day = -fine_per_day
            amount_text = amount_to_text_th(fine_per_day,
                                            order.currency_id.name)
            acceptance.amount_fine_per_day_text_th = minus and\
                'ลบ' + amount_text or amount_text
        return res

    @api.onchange('manual_fine')
    def _onchange_manual_fine(self):
        self.total_fine_cal = self.manual_fine
        self.total_fine = self.manual_fine

    @api.onchange('date_scheduled_end')
    def _onchange_date_scheduled_end(self):
        THHoliday = self.env['thai.holiday']
        next_working_end_date = THHoliday.\
            find_next_working_day(self.date_scheduled_end)
        self.date_contract_end = next_working_end_date

    @api.onchange('is_manual_fine')
    def _onchange_is_manual_fine(self):
        if not self.is_manual_fine:
            self._compute_total_fine()
            self.manual_fine = 0.0
            self.manual_days = 0

    @api.onchange('date_invoice')
    def _onchange_date_invoice(self):
        Invoice = self.env['account.invoice']
        InvoiceLine = self.env['account.invoice.line']
        self.write_to_invoice = True
        invoice = []
        sup_inv = self.supplier_invoice
        if len(self.acceptance_line_ids) > 0 and self.date_invoice:
            for accept_line in self.acceptance_line_ids:
                if accept_line.product_id.type == 'service':
                    # inv plan case
                    if accept_line.inv_line_id:
                        invoice = Invoice.search([
                            ('id', '=', accept_line.inv_line_id.invoice_id.id),
                        ])
                    # service case
                    else:
                        invoice_line = InvoiceLine.search([
                            ('purchase_line_id', '=', accept_line.line_id.id),
                        ])
                        for inv_line in invoice_line:
                            invoice = Invoice.search([
                                ('id', '=', inv_line.invoice_id.id),
                            ])
                elif accept_line.product_id.type == 'product':
                    invoice = Invoice.search([
                        ('origin', 'like', self.order_id.name),
                    ])
                days = 0
                term = self.order_id.partner_id.\
                    property_supplier_payment_term.id or False
                if term:
                    PTLine = self.env['account.payment.term.line']
                    term_line = PTLine.search([
                        ('id', '=', term),
                    ])
                    for line in term_line:
                        days = line.days
                inv_date = datetime.datetime.strptime(
                    self.date_invoice,
                    "%Y-%m-%d",
                )
                due_date = inv_date + datetime.timedelta(days=days)
                if len(invoice) > 0:
                    for inv in invoice:
                        inv.write({
                            'date_invoice': self.date_invoice,
                            'date_due': due_date,
                            'supplier_invoice_number': sup_inv,
                            'reference': self.order_id.name,
                        })

    @api.model
    def _check_product_type(self):
        type = False
        is_consumable = False
        for acceptance in self:
            for line in acceptance.acceptance_line_ids:
                type = line.product_id.type
                is_consumable = line.product_id.categ_id.is_consumable
                break
                # if check_type != line.product_id.type:
                #     raise ValidationError(
                #         _("All products must have the same type. %s"
                #           % (self.name,)))
        return type, is_consumable

    #  Invoice Plan Fine : Calculate from total amount
    @api.model
    def _calculate_last_invoice_plan_fine(self, invoice):
        total_fine = 0.0
        today = fields.Date.context_today(self)
        THHoliday = self.env['thai.holiday']
        for acceptance in self:
            if not acceptance.date_receive:
                acceptance.date_receive = today
            received = THHoliday.find_next_working_day(acceptance.date_receive)
            received = datetime.datetime.strptime(
                received,
                "%Y-%m-%d",
            )
            if not acceptance.date_contract_end:
                acceptance.date_contract_end = today
            end_date = datetime.datetime.strptime(
                acceptance.date_contract_end,
                "%Y-%m-%d",
            )
            delta = end_date - received
            overdue_day = delta.days
            total_fine_per_day = 0.0
            if overdue_day < 0:
                for line in invoice.invoice_line:
                    line_tax = 0.0
                    fine_rate = acceptance.order_id.fine_rate
                    unit_price = line.price_unit
                    to_receive_qty = line.quantity
                    taxes = line.invoice_line_tax_id.compute_all(
                        unit_price,
                        to_receive_qty,
                        product=line.product_id,
                    )
                    line_tax += sum([tax['amount'] for tax in taxes['taxes']])
                    fine_per_day = (fine_rate * 0.01) * \
                                   ((to_receive_qty * unit_price) + line_tax)
                    total_fine_per_day += fine_per_day
                    total_fine += -1 * overdue_day * fine_per_day
                acceptance.total_fine_cal = 100.0 if 0 < total_fine < 100.0 \
                    else total_fine
                acceptance.total_fine = acceptance.total_fine_cal
                acceptance.fine_per_day = total_fine_per_day
                acceptance.overdue_day = -1 * overdue_day
            else:
                acceptance.total_fine_cal = 0
                acceptance.total_fine = 0
                acceptance.fine_per_day = 0
                acceptance.overdue_day = 0

    @api.model
    def _calculate_service_fine(self):
        for acceptance in self:
            if acceptance.order_id.use_invoice_plan:  # invoice plan
                order_plan = acceptance.order_id.invoice_plan_ids
                last_installment = 0
                select_line = False
                for plan_line in order_plan:
                    if plan_line.installment >= last_installment:
                        select_line = plan_line
                        last_installment = plan_line.installment
                if select_line:
                    invoice = select_line.ref_invoice_id
                    acceptance._calculate_last_invoice_plan_fine(invoice)
            else:  # normal service
                acceptance._calculate_normal_service_fine()

    @api.model
    def _calculate_incoming_fine(self):
        total_fine = 0.0
        today = fields.Date.context_today(self)
        THHoliday = self.env['thai.holiday']
        for acceptance in self:
            if not acceptance.date_receive:
                acceptance.date_receive = today
            received = THHoliday.find_next_working_day(acceptance.date_receive)
            received = datetime.datetime.strptime(
                received,
                "%Y-%m-%d",
            )
            if not acceptance.date_contract_end:
                acceptance.date_contract_end = today
            end_date = datetime.datetime.strptime(
                acceptance.date_contract_end,
                "%Y-%m-%d",
            )
            delta = end_date - received
            overdue_day = delta.days
            total_fine_per_day = 0.0
            if overdue_day < 0:
                for line in acceptance.acceptance_line_ids:
                    line_tax = 0.0
                    fine_rate = self.order_id.fine_rate
                    unit_price = line.line_id.price_unit
                    to_receive_qty = line.to_receive_qty
                    taxes = line.line_id.taxes_id.compute_all(
                        unit_price,
                        to_receive_qty,
                        product=line.product_id,
                    )
                    line_tax += sum([tax['amount'] for tax in taxes['taxes']])
                    fine_per_day = (fine_rate * 0.01) * \
                                   ((to_receive_qty * unit_price) + line_tax)
                    total_fine_per_day += fine_per_day
                    total_fine += -1 * overdue_day * fine_per_day
                acceptance.total_fine_cal = total_fine
                acceptance.total_fine = acceptance.total_fine_cal
                acceptance.fine_per_day = total_fine_per_day
                acceptance.overdue_day = -1 * overdue_day
            else:
                acceptance.total_fine_cal = 0
                acceptance.total_fine = 0
                acceptance.fine_per_day = 0
                acceptance.overdue_day = 0

    @api.model
    def _calculate_normal_service_fine(self):
        total_fine = 0.0
        today = fields.Date.context_today(self)
        THHoliday = self.env['thai.holiday']
        for acceptance in self:
            if not acceptance.date_receive:
                acceptance.date_receive = today
            received = THHoliday.find_next_working_day(acceptance.date_receive)
            received = datetime.datetime.strptime(
                received,
                "%Y-%m-%d",
            )
            if not acceptance.date_contract_end:
                acceptance.date_contract_end = today
            end_date = datetime.datetime.strptime(
                acceptance.date_contract_end,
                "%Y-%m-%d",
            )
            delta = end_date - received
            overdue_day = delta.days
            total_fine_per_day = 0.0
            if overdue_day < 0:
                for line in acceptance.acceptance_line_ids:
                    line_tax = 0.0
                    fine_rate = self.order_id.fine_rate
                    unit_price = line.line_id.price_unit
                    to_receive_qty = line.to_receive_qty
                    taxes = line.line_id.taxes_id.compute_all(
                        unit_price,
                        to_receive_qty,
                        product=line.product_id,
                    )
                    line_tax += sum([tax['amount'] for tax in taxes['taxes']])
                    fine_per_day = (fine_rate * 0.01) * \
                                   ((to_receive_qty * unit_price) + line_tax)
                    fine_per_day = 100.0 if 0 < fine_per_day < 100.0 \
                        else fine_per_day
                    total_fine_per_day += fine_per_day
                    total_fine += -1 * overdue_day * fine_per_day
                acceptance.total_fine_cal = total_fine
                acceptance.total_fine = acceptance.total_fine_cal
                acceptance.fine_per_day = total_fine_per_day
                acceptance.overdue_day = -1 * overdue_day
            else:
                acceptance.total_fine_cal = 0
                acceptance.total_fine = 0
                acceptance.fine_per_day = 0
                acceptance.overdue_day = 0

    @api.model
    @api.depends('date_receive', 'date_contract_end', 'acceptance_line_ids')
    def _compute_total_fine(self):
        for acceptance in self:
            product_type, is_consumable = acceptance._check_product_type()
            if product_type == 'service' and not is_consumable:
                acceptance._calculate_service_fine()
            else:
                acceptance._calculate_incoming_fine()
            if acceptance.manual_fine > 0:
                acceptance.total_fine_cal = acceptance.manual_fine
                acceptance.total_fine = acceptance.manual_fine

    name = fields.Char(
        string="Acceptance No.",
        default=lambda self:
        self.env['ir.sequence'].get('purchase.work.acceptance'),
        readonly=True,
    )
    date_contract_start = fields.Date(
        string="Contract Start Date",
        default=lambda self: fields.Date.context_today(self),
    )
    date_scheduled_end = fields.Date(
        string="Scheduled End Date",
        default=lambda self: fields.Date.context_today(self),
    )
    date_contract_end = fields.Date(
        string="Contract End Date",
        default=lambda self: fields.Date.context_today(self),
    )
    date_receive = fields.Date(
        string="Receive Date",
        default=lambda self: fields.Date.context_today(self),
    )
    date_accept = fields.Date(
        string="Acceptance Date",
    )
    is_manual_fine = fields.Boolean(
        string="Use Manual Fine",
    )
    manual_fine = fields.Float(
        string="Manual Fine",
        default=0.0,
    )
    manual_days = fields.Integer(
        string="No. of Days",
        default=1,
    )
    fine_per_day = fields.Float(
        string="Fine per Day",
        default=0.0,
    )
    amount_fine_per_day_text_th = fields.Char(
        string='Fine per Day TH Text',
        compute='_compute_fine_per_day_to_word_th',
        store=True,
    )
    overdue_day = fields.Integer(
        string="Overdue Days",
        default=0,
    )
    total_fine_cal = fields.Float(
        string="Total Fine Calculation",
        compute="_compute_total_fine",
        store=True,
    )
    total_fine = fields.Float(
        string="Total Fine",
    )
    amount_total_fine_text_th = fields.Char(
        string='Total Fine TH Text',
        compute='_compute_fine_amount_to_word_th',
        store=True,
    )
    supplier_invoice = fields.Char(
        string="Invoice No.",
        required=True,
    )
    date_invoice = fields.Date(
        string="Invoice Date",
        required=True,
    )
    write_to_invoice = fields.Boolean(
        string="Write to invoice date",
    )
    invoice_created = fields.Boolean(
        string="Invoice created",
    )
    acceptance_line_ids = fields.One2many(
        'purchase.work.acceptance.line',
        'acceptance_id',
        string='Work Acceptance Line',
        required=True,
    )
    order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        related='order_id.partner_id',
        store=True,
    )
    order_method = fields.Selection(
        string='Order Method',
        store=True,
        related='order_id.invoice_method',
    )
    eval_receiving = fields.Selection(
        selection=[
            ('3', 'On time [3]'),
            ('2', 'Late for 1-7 days [2]'),
            ('1', 'Late for 8-14 days [1]'),
            ('0', 'Late more than 15 days [0]'),
        ],
        string='Rate - Receiving',
    )
    eval_quality = fields.Selection(
        selection=[
            ('2', 'Better than expectation [2]'),
            ('1', 'As expectation [1]'),
        ],
        string='Rate - Quality',
    )
    eval_service = fields.Selection(
        selection=[
            ('3', 'Excellent [3]'),
            ('2', 'Good [2]'),
            ('1', 'Satisfactory [1]'),
            ('0', 'Needs Improvement [0]'),
        ],
        string='Rate - Service',
    )
    state = fields.Selection(
        selection=_STATES,
        copy=False,
        default='draft',
    )
    amount_untaxed = fields.Float(
        string='Untaxed Amount',
        compute='_compute_amount',
        store=True,
        readonly=True,
        default=0.0,
    )
    amount_tax = fields.Float(
        string='Taxes',
        compute='_compute_amount',
        store=True,
        readonly=True,
        default=0.0,
    )
    amount_total = fields.Float(
        string='Total',
        compute='_compute_amount',
        store=True,
        readonly=True,
        default=0.0,
    )
    invoiced = fields.Boolean(
        string='Invoiced',
        compute='_compute_invoiced',
        store=True,
        help="Fine is invoiced if it is referenced by an open invioce",
    )
    invoice_ids = fields.One2many(
        'account.invoice',
        'late_delivery_work_acceptance_id',
        string='Referred Invoices',
        readonly=True,
        help="Invoice that reference to this WA for panalty",
    )

    @api.multi
    @api.depends('invoice_ids', 'invoice_ids.state')
    def _compute_invoiced(self):
        for rec in self:
            if not rec.invoice_ids:
                rec.invoiced = False
            else:
                # If referenced with invoice and invoice > open
                states = rec.invoice_ids.mapped('state')
                rec.invoiced = set(states) <= set(['open', 'paid'])

    @api.multi
    def write(self, vals):
        res = super(PurchaseWorkAcceptance, self).write(vals)
        self.change_invoice_detail()
        return res

    @api.model
    def change_invoice_detail(self):
        for wa in self:
            for wa_line in wa.acceptance_line_ids:
                if wa_line.inv_line_id.invoice_id and \
                        wa_line.inv_line_id.invoice_id.state == 'draft':
                    wa_line.inv_line_id.quantity = wa_line.to_receive_qty
                    wa_line.inv_line_id.price_unit = wa_line.price_unit
                    wa_line.inv_line_id.invoice_id.button_reset_taxes()

    @api.one
    @api.depends(
        'acceptance_line_ids.price_subtotal',
        'acceptance_line_ids.tax_ids',
    )
    def _compute_amount(self):
        amount_untaxed = 0.0
        amount_tax = 0.0
        for line in self.acceptance_line_ids:
            taxes = line.tax_ids.compute_all(
                line.price_unit,
                line.to_receive_qty,
                product=line.product_id
            )
            amount_tax += sum([tax['amount'] for tax in taxes['taxes']])
            amount_untaxed += taxes['total']
        self.amount_untaxed = amount_untaxed
        self.amount_tax = amount_tax
        self.amount_total = amount_untaxed + amount_tax

    @api.multi
    def validate_amount_total_with_order(self):
        if self.state == 'draft' and self.order_id.use_invoice_plan:
            wa_total_payment = 0
            order = self.order_id
            paid_accpts = self.search(
                [
                    ('order_id', '=', order.id),
                    ('state', 'in', ('evaluation', 'done')),
                ]
            )
            for accpt in paid_accpts:
                wa_total_payment += accpt.amount_total
            if wa_total_payment + self.amount_total > order.amount_total:
                raise ValidationError(
                    _("""Can't evaluate this acceptance.
                         This WA's total amount is over PO's total amount.""")
                )

    @api.multi
    def action_evaluate(self):
        self.ensure_one()
        if len(self.acceptance_line_ids) == 0:
            raise ValidationError(
                _("Can't evaluate the acceptance with no line.")
            )
        no_qty_lines = self.acceptance_line_ids.filtered(lambda l:
                                                         l.to_receive_qty <= 0)
        if no_qty_lines:
            raise ValidationError(
                _('To Receive Quantity must greater than zero!'))
        self.validate_amount_total_with_order()
        self.state = 'evaluation'

    @api.multi
    def action_done(self):
        self.ensure_one()
        self.state = 'done'

    @api.multi
    def action_set_draft(self):
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    @api.model
    def open_order_line(self, ids):
        Model = self.env['ir.model.data']
        POLine = self.env['purchase.order.line']
        view_id = Model.get_object_reference(
            'purchase',
            'view_purchase_line_invoice'
        )
        wa = self.browse(ids)
        lines = POLine.search([('order_id', '=', wa.order_id.id)])
        return {
            'name': "Create Invoices",
            'view_mode': 'form',
            'view_id': view_id[1],
            'view_type': 'form',
            'res_model': 'purchase.order.line_invoice',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'active_ids': lines.ids,
            }
        }


class PurchaseWorkAcceptanceLine(models.Model):
    _name = 'purchase.work.acceptance.line'
    _description = 'Purchase Work Acceptance Line'

    @api.model
    @api.depends('acceptance_id', 'line_id')
    def _compute_get_balance_qty(self):
        for acc_line in self:
            if acc_line.line_id.order_id.invoice_method == 'invoice_plan':
                acc_line.balance_qty = acc_line.line_id.product_qty
            else:
                acc_line.balance_qty = (acc_line.line_id.product_qty -
                                        acc_line.line_id.invoiced_qty)

    acceptance_id = fields.Many2one(
        'purchase.work.acceptance',
        string='Acceptance Reference',
        ondelete='cascade',
    )
    line_id = fields.Many2one(
        'purchase.order.line',
        string='Purchase Order Line',
        required=True,
        readonly=True,
    )
    inv_line_id = fields.Many2one(
        'account.invoice.line',
        string='Account Invoice Line',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        readonly=True,
    )
    name = fields.Char(
        string='Description',
        required=True,
    )
    balance_qty = fields.Float(
        string='Balance Quantity',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        compute='_compute_get_balance_qty',
        store=True,
    )
    to_receive_qty = fields.Float(
        string='To Receive Quantity',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True,
    )
    product_uom = fields.Many2one(
        'product.uom',
        string='UoM',
    )
    price_unit = fields.Float(
        string='Unit Price',
    )
    price_subtotal = fields.Float(
        string='Sub Total',
        compute="_compute_price_subtotal",
        store=True,
    )
    tax_ids = fields.Many2many(
        'account.tax',
        'purchase_work_acceptance_taxes_rel',
        'acceptance_line_id',
        'tax_id',
        string='Taxes',
        readonly=True,
    )

    @api.multi
    @api.depends('to_receive_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        for rec in self:
            taxes = rec.tax_ids.compute_all(rec.price_unit, rec.to_receive_qty,
                                            product=rec.product_id)
            rec.price_subtotal = taxes['total']
            if rec.line_id:
                po_currency = rec.line_id.order_id.currency_id
                rec.price_subtotal = po_currency.round(rec.price_subtotal)

    @api.constrains('to_receive_qty')
    def _check_over_qty(self):
        if self.to_receive_qty > self.balance_qty:
            raise ValidationError(
                _("To receive quantity can't be over than "
                  "balance quantity.")
            )
