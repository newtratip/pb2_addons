# -*- coding: utf-8 -*
from openerp import models, fields, api


class PabiLongTermInvestmentReportWizard(models.TransientModel):
    _name = 'pabi.long.term.investment.report.wizard'

    account_id = fields.Many2one(
        'account.account',
        string='Account Name',
        domain=[('type', 'not in', ['view'])],
        required=True,
        readonly=True,
        default=234,
    )
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='Fiscal Year',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
    )

    @api.multi
    def _print_report(self, data):
        context = self._context.copy()
        if context.get('xls_export', False):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'pabi_long_term_investment_report_xls',
                'datas': data,
            }

    @api.multi
    def _check_report(self):
        context = self._context.copy()
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['account_id',  'fiscalyear_id',  'partner_id'])[0]
        for field in ['account_id', 'fiscalyear_id', 'partner_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        return self._print_report(data)

    @api.multi
    def xls_export(self):
        return self._check_report()
