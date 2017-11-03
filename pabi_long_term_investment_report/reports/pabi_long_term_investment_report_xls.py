# -*- coding: utf-8 -*
from .pabi_long_term_investment_report import PabiLongTermInvestmentReport
from openerp.addons.report_xls.report_xls import report_xls
import xlwt
import datetime
from openerp.tools.translate import _
import locale

_column_sizes = [
    ('name', 20),
    ('date_approve', 20),
    ('description', 20),
    ('total_captial', 25),
    ('total_share', 25),
    ('nstda_share', 20),
    ('price_unit', 20),
    ('total_amount', 20),
    ('invoice_number', 20),
    ('date_invoice', 20),
    ('invoice_desc', 20),
    ('amount_invoice', 20),
    ('ref_payment', 20),
]


class PabiLongTermInvestmentReportXLS(report_xls):
    column_sizes = [x[1] for x in _column_sizes]

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        # Set Locale
        locale.setlocale(locale.LC_TIME, 'th_TH.utf8')

        ws = wb.add_sheet(_p.report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Header
        cell_format = _xs['bold'] + _xs['center']
        cell_style_center = xlwt.easyxf(cell_format)
        header_specs = [
            ('company', 10, 5, 'text',
                _('สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ')),
            ('account_detail', 10, 0, 'text',
                _('รายละเอียด เลขที่บัญชี %s ชื่อบัญชี %s'
                  % (str(_p.account.code), _p.account.name.encode('utf-8')))),
            ('current_date', 10, 0, 'text',
                _('ณ วันที่ %s'
                    % (datetime.datetime.today().strftime('%-d %B %Ey'))))
        ]
        for header in header_specs:
            row_data = self.xls_row_template([header], [header[0]])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=cell_style_center)

        partner_ids = []
        for move_line in _p['long_term_investment_lines']:
            partner_ids.append(move_line.get('partner_id'))

        partner_ids = sorted(list(set(partner_ids)))

        Partner = self.pool.get('res.partner')
        for partner in Partner.browse(self.cr, self.uid, partner_ids):
            # write empty row to define column sizes
            c_sizes = self.column_sizes
            c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                       for i in range(0, len(c_sizes))]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, set_column_size=True)

            cell_format = _xs['bold'] + _xs['fill_blue']
            cell_style_blue = xlwt.easyxf(cell_format)
            c_specs = [
                ('partner_name', 4, 0, 'text',
                    _('%s %s' % (partner.search_key, partner.name))),
                ('percent_invest', 9, 0, 'text',
                    _('สวทช ถือทุนร้อยละ %s'
                        % str("{:.2f}".format(partner.percent_invest))))
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=cell_style_blue)

            # Column Header
            cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
            c_hdr_cell_style = xlwt.easyxf(cell_format)
            c_specs = [
                ('name', 1, 0, 'text', _('อนุมัติโดยกวทช. ครั้งที่'), None,
                    c_hdr_cell_style),
                ('date_approve', 1, 0, 'text', _('วันที่อนุมัติ'), None,
                    c_hdr_cell_style),
                ('description', 1, 0, 'text', _('รายการ'), None,
                    c_hdr_cell_style),
                ('total_capital', 1, 0, 'text', _('ทุนจดทะเบียน (ล้านบาท)'),
                    None, c_hdr_cell_style),
                ('total_share', 1, 0, 'text', _('ทุนจดทะเบียน (จำนวนหุ้น)'),
                    None, c_hdr_cell_style),
                ('nstda_share', 1, 0, 'text', _('จำนวนหุ้น (สวทช.)'), None,
                    c_hdr_cell_style),
                ('price_unit', 1, 0, 'text', _('ราคา/หุ้น'), None,
                    c_hdr_cell_style),
                ('total_amount', 1, 0, 'text', _('ยอดรวม'), None,
                    c_hdr_cell_style),
                ('invoice_number', 1, 0, 'text', _('เลขที่เอกสารใบตั้งหนี้'),
                    None, c_hdr_cell_style),
                ('date_invoice', 1, 0, 'text', _('วันที่ตั้งหนี้'), None,
                    c_hdr_cell_style),
                ('invoice_desc', 1, 0, 'text', _('รายละเอียด'), None,
                    c_hdr_cell_style),
                ('amount_invoice', 1, 0, 'text', _('ยอดเงิน'), None,
                    c_hdr_cell_style),
                ('ref_payment', 1, 0, 'text', _('อ้างถึงการจ่าย'), None,
                    c_hdr_cell_style),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data)

            long_term_investment_line = \
                [line for line in _p['long_term_investment_lines']
                    if line['partner_id'] == partner.id]
            long_term_investment_line = sorted(
                long_term_investment_line, key=lambda k: k['investment_id'])

            c_hdr_cell_style_decimal = xlwt.easyxf(
                _xs['borders_all'] + _xs['right'],
                num_format_str=report_xls.decimal_format)

            investment_tmp_ids = 0
            sum_total_capital = 0
            sum_total_share = 0
            sum_nstda_share = 0
            sum_total_amount = 0
            sum_amount_invoice = 0
            for line in long_term_investment_line:
                name = None
                date_approve = None
                description = None
                total_capital = None
                total_share = None
                nstda_share = None
                price_unit = None
                total_amount = None
                type_amount = 'text'
                style_amount = None
                if investment_tmp_ids != line.get('investment_id'):
                    name = line.get('name', None)
                    date_approve = datetime.datetime.strptime(
                        line.get('date_approve'), '%Y-%m-%d') \
                        .strftime('%-d %b %Ey')
                    description = line.get('description', None)
                    total_capital = line.get('total_capital', 0.0)
                    total_share = line.get('total_share', 0.0)
                    nstda_share = line.get('nstda_share', 0.0)
                    price_unit = line.get('price_unit', 0.0)
                    total_amount = line.get('price_subtotal', 0.0)
                    type_amount = 'number'
                    style_amount = c_hdr_cell_style_decimal
                    sum_total_capital += total_capital
                    sum_total_share += total_share
                    sum_nstda_share += nstda_share
                    sum_total_amount += total_amount

                sum_amount_invoice += line.get('amount_invoice', 0.0)
                c_specs = [
                    ('name', 1, 0, 'text', name),
                    ('date_approve', 1, 0, 'text', date_approve or None),
                    ('description', 1, 0, 'text', description),
                    ('total_capital', 1, 0, type_amount, total_capital, None,
                        style_amount),
                    ('total_share', 1, 0, type_amount, total_share, None,
                        style_amount),
                    ('nstda_share', 1, 0, type_amount, nstda_share, None,
                        style_amount),
                    ('price_unit', 1, 0, type_amount, price_unit, None,
                        style_amount),
                    ('total_amount', 1, 0, type_amount, total_amount, None,
                        style_amount),
                    ('invoice_number', 1, 0, 'text',
                        line.get('invoice_number', None)),
                    ('date_invoice', 1, 0, 'text',
                        datetime.datetime.strptime(line.get('date_approve'),
                                                   '%Y-%m-%d')
                        .strftime('%-d %b %Ey') or None),
                    ('invoice_desc', 1, 0, 'text',
                        line.get('invoice_desc', None)),
                    ('amount_invoice', 1, 0, 'number',
                        line.get('amount_invoice', 0.0), None,
                        c_hdr_cell_style_decimal),
                    ('ref_payment', 1, 0, 'text', _('ref_payment')),
                ]
                investment_tmp_ids = line.get('investment_id')
                row_data = self.xls_row_template(c_specs,
                                                 [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    ws, row_pos, row_data)

            # Footer
            c_ftr_cell_style_decimal = xlwt.easyxf(
                _xs['borders_all'] + _xs['right'] + _xs['fill'],
                num_format_str=report_xls.decimal_format)
            c_ftr_cell_style = xlwt.easyxf(
                _xs['bold'] + _xs['fill'] + _xs['borders_all'])
            c_specs = [
                ('col_footer_1', 1, 0, 'text', None, None, c_ftr_cell_style),
                ('col_footer_2', 1, 0, 'text', None, None, c_ftr_cell_style),
                ('col_footer_3', 1, 0, 'text', None, None, c_ftr_cell_style),
                ('col_footer_4', 1, 0, 'number', sum_total_capital, None,
                    c_ftr_cell_style_decimal),
                ('col_footer_5', 1, 0, 'number', sum_total_share, None,
                    c_ftr_cell_style_decimal),
                ('col_footer_6', 1, 0, 'number', sum_nstda_share, None,
                    c_ftr_cell_style_decimal),
                ('col_footer_7', 1, 0, 'text', None, None,
                    c_ftr_cell_style),
                ('col_footer_8', 1, 0, 'number', sum_total_amount, None,
                    c_ftr_cell_style_decimal),
                ('col_footer_9', 1, 0, 'text', None, None, c_ftr_cell_style),
                ('col_footer_10', 1, 0, 'text', None, None, c_ftr_cell_style),
                ('col_footer_11', 1, 0, 'text', None, None, c_ftr_cell_style),
                ('col_footer_12', 1, 0, 'number', sum_amount_invoice, None,
                    c_ftr_cell_style_decimal),
                ('col_footer_13', 1, 0, 'text', _('ref_payment'))
            ]

            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data)


PabiLongTermInvestmentReportXLS(
    'report.pabi_long_term_investment_report_xls',
    'account.account',
    parser=PabiLongTermInvestmentReport)
