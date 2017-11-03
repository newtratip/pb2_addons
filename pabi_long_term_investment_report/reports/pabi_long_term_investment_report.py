# -*- coding: utf-8 -*
from openerp.report import report_sxw
from openerp import pooler
from openerp.tools.translate import _


class PabiLongTermInvestmentReport(report_sxw.rml_parse):

    def __init__(self, cursor, uid, name, context):
        super(PabiLongTermInvestmentReport, self).__init__(
            cursor, uid, name, context=context,
        )
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('Long Term Investment'),
        })

    def _get_info(self, data, field, model):
        info = data.get('form', {}).get(field)
        if info:
            return self.pool.get(model).browse(self.cursor, self.uid, info)
        return False

    def _get_account(self, data):
        return self._get_info(data, 'account_id', 'account.account')

    def _get_fiscalyear(self, data):
        return self._get_info(data, 'fiscalyear_id', 'account.fiscalyear')

    def _get_partner(self, data):
        return self._get_info(data, 'partner_id', 'res.partner')

    def set_context(self, objects, data, ids, report_type=None):
        """
        Populate a long_term_investment_line on each browse record
        """
        # Reading form
        account = self._get_account(data)
        fiscalyear = self._get_fiscalyear(data)
        partner = self._get_partner(data)

        account_id = account.id
        fiscalyear_id = fiscalyear and fiscalyear.id or False
        partner_id = partner and partner.id or False

        long_term_investment_lines = self \
            ._compute_long_term_investment_line(account_id, fiscalyear_id,
                                                partner_id)
        objects = self.pool.get('account.account').browse(self.cursor,
                                                          self.uid,
                                                          account_id)
        self.localcontext.update({
            'account': account,
            'fiscalyear': fiscalyear,
            'partner': partner,
            'long_term_investment_lines': long_term_investment_lines,
        })

        return super(PabiLongTermInvestmentReport, self).set_context(
            objects, data, account.id, report_type=report_type)

    def _compute_long_term_investment_line(self, account_id, fiscalyear_id,
                                           partner_id):
        move_line_obj = self.pool.get('account.move.line')
        fiscalyear = self.pool.get('account.fiscalyear').browse(
            self.cursor, self.uid, fiscalyear_id)
        domain = [('account_id', '=', account_id)]
        if fiscalyear_id:
            domain += [('period_id', 'in', fiscalyear.period_ids.ids)]
        if partner_id:
            domain += [('partner_id', '=', partner_id)]
        move_line_ids = move_line_obj.search(self.cursor, self.uid, domain)
        if not move_line_ids:
            return []
        res = self._get_long_term_investment_line_datas(move_line_ids)
        return res

    def _get_long_term_investment_line_datas(self, move_line_ids,
                                             order='ml.partner_id, i.id'):
        if not isinstance(move_line_ids, list):
            move_line_ids = [move_line_ids]
        sql = """
            SELECT ml.partner_id,
                i.id AS investment_id,
                i.name,
                i.date_approve,
                i.description,
                i.total_capital,
                i.total_share,
                i.nstda_share,
                i.price_unit,
                i.price_subtotal,
                ml.name AS invoice_desc,
                ml.date AS date_invoice,
                ml.debit - ml.credit AS amount_invoice,
                ml.id AS move_line_id,
                ml.ref as invoice_number
            FROM account_move_line AS ml
            JOIN res_partner_investment i ON ml.investment_id = i.id
            JOIN account_period p on ml.period_id = p.id
            WHERE ml.id IN %s"""
        sql += (" ORDER BY %s" % (order,))
        try:
            self.cursor.execute(sql, (tuple(move_line_ids),))
            res = self.cursor.dictfetchall()
        except:
            self.cursor.rollback()
            raise
        return res or []
