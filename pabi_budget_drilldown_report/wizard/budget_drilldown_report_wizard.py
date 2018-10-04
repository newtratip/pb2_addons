# -*- coding: utf-8 -*-
from openerp import models, fields, api
from ..models.common import SearchCommon, REPORT_GROUPBY


class BudgetDrilldownReportWizard(SearchCommon, models.TransientModel):
    _name = 'budget.drilldown.report.wizard'

    fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='Fiscal Year',
        default=lambda self: self.env['account.fiscalyear'].find(),
        required=True,
    )

    # Following onchange is required
    @api.onchange('charge_type', 'group_by_charge_type',
                  'activity_id', 'group_by_activity_id',
                  'activity_group_id', 'group_by_activity_group_id',
                  'section_id', 'group_by_section_id',
                  'org_id', 'group_by_org_id',
                  'project_id', 'group_by_project_id',
                  'invest_asset_id', 'group_by_invest_asset_id',
                  'invest_construction_id', 'group_by_invest_construction_id',
                  )
    def _onchange_helper(self):
        """ Ensure sure that, if some field is selected, so do some groupby """
        if self.charge_type:
            self.group_by_charge_type = True
        if self.activity_id:
            self.group_by_activity_id = True
        if self.activity_group_id:
            self.group_by_activity_group_id = True
        # --
        if self.section_id:
            self.group_by_section_id = True
        if self.org_id:
            self.group_by_org_id = True
        if self.project_id:
            self.group_by_project_id = True
        if self.invest_asset_id:
            self.group_by_invest_asset_id = True
        if self.invest_construction_id:
            self.group_by_invest_construction_id = True

    @api.onchange('report_type')
    def _onchange_report_type(self):
        super(BudgetDrilldownReportWizard, self)._onchange_report_type()
        # Clear Data
        for field in ['section_id', 'project_id', 'activity_group_id',
                      'charge_type', 'activity_id']:
            self['group_by_%s' % field] = False

        """ Default Group By to True - by Report Type """
        if self.report_type in REPORT_GROUPBY.keys():
            for field in REPORT_GROUPBY[self.report_type]:
                groupby_field = 'group_by_%s' % field
                self[groupby_field] = True
        return

    @api.multi
    def run_report(self):
        self.ensure_one()
        RPT = self.env['budget.drilldown.report']
        report_id, view_id = RPT.generate_report(self)
        action = self.env.ref('pabi_budget_drilldown_report.'
                              'action_budget_drilldown_report')
        result = action.read()[0]
        result.update({
            'res_id': report_id,
            'domain': [('id', '=', report_id)],
            'views': [(view_id, 'form')],
        })
        return result
