# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning as UserError


class ChequeLot(models.Model):
    _name = 'cheque.lot'
    _description = 'Cheque Lot'
    _order = 'id desc'

    name = fields.Char(
        string='Lot',
        required=True,
        copy=False,
    )
    bank_id = fields.Many2one(
        'res.partner.bank',
        string='Bank',
        required=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Payment Method',
        required=True,
        domain="[('bank_id', '=', bank_id)]",
    )
    cheque_number_from = fields.Char(
        string='Cheque Number From',
        size=10,
        required=True,
    )
    cheque_number_to = fields.Char(
        string='Cheque Number To',
        size=10,
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        required=False,
    )
    next_number = fields.Char(
        string='Next Cheque Number',
        size=10,
        compute='_compute_next_number',
    )
    remaining = fields.Integer(
        string='Next Cheque Number',
        compute='_compute_state',
        store=True,
        readonly=True,
        help="This field show the remaining valid cheque to use",
    )
    state = fields.Selection(
        [('active', 'Active'),
         ('inactive', 'Inactive'),
         ],
        string='Status',
        compute='_compute_state',
        store=True,
        readonly=True,
        help="Active means this lot is in used. "
        "Inactive means this lot has been used up",
    )
    line_ids = fields.One2many(
        'cheque.register',
        'cheque_lot_id',
        string='Cheque Registers',
    )

    @api.onchange('bank_id')
    def _onchange_bank_id(self):
        self.journal_id = False

    @api.multi
    @api.depends('line_ids', 'line_ids.void', 'line_ids.voucher_id')
    def _compute_state(self):
        Cheque = self.env['cheque.register']
        for lot in self:
            num = Cheque.search_count([('cheque_lot_id', '=', lot.id),
                                       ('voucher_id', '=', False),
                                       ('void', '=', False)])
            lot.remaining = num
            if num > 0:
                lot.state = 'active'
            else:
                lot.state = 'inactive'

    @api.multi
    @api.constrains('cheque_number_from', 'cheque_number_to')
    def _check_cheque_number(self):
        for rec in self:
            if not rec.cheque_number_from.isdigit() or \
                    not rec.cheque_number_to.isdigit():
                raise ValidationError(
                    _('Cheque Number must not contain any character!'))
            if int(rec.cheque_number_from) >= int(rec.cheque_number_to):
                raise ValidationError(
                    _('Cheque Number From - To must be a valid number range!'))
            if len(rec.cheque_number_from) != len(rec.cheque_number_to):
                raise ValidationError(
                    _('Cheque Number From - To must be in same digit length!'))

    @api.multi
    @api.depends()
    def _compute_next_number(self):
        for rec in self:
            self._cr.execute("""
                select min(number) from cheque_register
                where cheque_lot_id = %s
                and voucher_id is null
                and void = false
            """, (rec.id,))
            rec.next_number = self._cr.fetchone()[0] or False

    @api.multi
    def _generate_cheque_register(self):
        ChequeRegister = self.env['cheque.register']
        for rec in self:
            a = int(rec.cheque_number_from)
            b = int(rec.cheque_number_to) + 1
            if (b - a) > 1000:  # Not allow > 1000 cheques
                raise ValidationError(
                    _('Creating more than 1,000 number is not allowed!'))
            padding = len(rec.cheque_number_from)
            for i in range(a, b):
                cheque_number = str(i).zfill(padding)
                ChequeRegister.create({'cheque_lot_id': rec.id,
                                       'number': cheque_number})

    @api.model
    def create(self, vals):
        cheque_lot = super(ChequeLot, self).create(vals)
        cheque_lot._generate_cheque_register()
        return cheque_lot

    @api.multi
    def open_cheque_register(self):
        self.ensure_one()
        action = self.env.ref('payment_export.action_cheque_register')
        result = action.read()[0]
        dom = [('cheque_lot_id', '=', self.id)]
        result.update({'domain': dom})
        return result

    @api.model
    def get_draft_cheque_register_range(self, cheque_lot_id, limit):
        self._cr.execute("""
            select id from cheque_register
            where cheque_lot_id = %s
            and voucher_id is null
            and void = false
            order by number
            limit %s
        """, (cheque_lot_id, limit,))
        res = [x[0] for x in self._cr.fetchall()]
        if len(res) < limit:
            raise UserError(_('Not enough draft Cheque on this lot'))
        return res


class ChequeRegister(models.Model):
    _name = 'cheque.register'
    _description = 'Cheque Register'
    _rec_name = 'number'
    _order = 'number'

    number = fields.Char(
        string='Cheque Number',
        size=10,
        readonly=True,
    )
    cheque_lot_id = fields.Many2one(
        'cheque.lot',
        string='Cheque Lot',
        ondelete='cascade',
        readonly=True,
        index=True,
    )
    bank_id = fields.Many2one(
        'res.partner.bank',
        string='Bank Account',
        related='cheque_lot_id.bank_id',
        store=True,
        readonly=True,
    )
    voucher_id = fields.Many2one(
        'account.voucher',
        string='Supplier Payment',
        readonly=True,
    )
    amount = fields.Float(
        string='Amount',
        related='voucher_id.amount',
        readonly=True,
    )
    void = fields.Boolean(
        string='Void',
        default=False,
    )
    note = fields.Text(
        string='Cancellation Reasons',
    )
    payment_export_id = fields.Many2one(
        'payment.export',
        string='Payment Export',
        readonly=True,
    )
