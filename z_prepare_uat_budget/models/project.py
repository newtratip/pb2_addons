# -*- coding: utf-8 -*-
from openerp import api, models


class ResProject(models.Model):
    _inherit = 'res.project'

    @api.model
    def copy_project_program(self, suffix):
        """ Copy all project and put '-PH2' as suffix """
        if not suffix:
            suffix = '-PH2'

        # 1) Copy Program
        programs = self.env['res.program'].search([])
        for program in programs:
            program.copy({'code': program.code + suffix,
                          'name': program.name + suffix})
        # 2) Copy Project Group and set new Program
        project_groups = self.env['res.project.group'].search([])
        Program = self.env['res.program']
        for project_group in project_groups:
            pg_id = Program.name_search(
                project_group.program_id.code + suffix)[0][0]
            project_group.copy({'code': project_group.code + suffix,
                                'name': project_group.name + suffix,
                                'program_id': pg_id})

        # 3) Copy Project and set new Project Group
        projects = self.env['res.project'].search([])
        ProjectGroup = self.env['res.project.group']
        for project in projects:
            pg_id = ProjectGroup.\
                name_search(project.project_group_id.code + suffix)[0][0]
            project.copy({'code': project.code + suffix,
                          'name': project.name + suffix,
                          'project_group_id': pg_id, })

    @api.model
    def copy_project_plan_line_for_uat(self):
        """ This method copy project line from 1 project to others """
        source_project = 'P1550663'
        target_projects = [  # project = P1450891
            'P1650064',
            'P1650748',
            'P1650749',
            'P1650700',
            'P1650475',
            'P1650785',
            'P1350441',
            'P1650666',
            'P1551680',
            'P1350420',
            'P1451356',
            'P1350438',
            'P1450383',
            'P1630004',
            'P1350429',
            'P1551380',
            'P1550583',
            'P1650669',
            'P1650596',
            'P1650395',
            'P1450015',
            'P1550967',
            'P1550571',
            'P1300882',
            'P1450883',
            'P1450962',
            'P1551326',
            'P1450907',
            'P1450804',
            'P1551548',
            'P1551585',
            'P1450650',
            'P1551647',
            'P1551493',
            'P1551728',
            'P1551729',
            'P1650049',
            'P1650297',
            'P1550633',
            'P1301089',
            'P1550450',
            'P1551400',
            'P1451231',
            'P1550617',
            'P1550684',
            'P1201973',
            'P1201970',
            'P1300360',
            'P1450766',
            'P1201968',
            'P1201967',
            'P1550665',
            'P1551170',
            'P1301090',
            'P1300750',
            'P1450055',
            'P0040209',
            'P1650746',
            'P1551295',
            'P1551537',
            'P1451152',
            'P1451124',
            'P1451121',
            'P1451138',
            'P1202251',
            'P1101128',
            'P1101144',
            'P1300066',
            'P1551372',
            'P1551342',
            'P1551301',
            'P1551047',
            'P1450824',
            'P1350040',
            'P1350045',
            'P1551428',
            'P1650571',
            'P1551638',
            'P1650063',
            'P1650650',
            'P1451097',
            'P1550605',
            'P1650732',
            'P1551171',
            'P1551177',
            'P1650410',
            'M15014',
            'M15015',
            'M16007',
            'M15013',
            'P1551526',
            'P1550309',
            'P1551717',
            'P1010661',
            'P1650774',
            'P1300697',
            'P1650425',
            'P1551107',
            'P1450604',
            'P1451313',
            'P1650142',
            'P1650742',
            'P1650767',
            'P1350137',
            'P1450592',
            'P1551062',
            'P1651210',
            'P1450891-PH2',
            'P1650064-PH2',
            'P1550663-PH2',
            'P1650748-PH2',
            'P1650749-PH2',
            'P1650700-PH2',
            'P1650475-PH2',
            'P1650785-PH2',
            'P1350441-PH2',
            'P1650666-PH2',
            'P1551680-PH2',
            'P1350420-PH2',
            'P1451356-PH2',
            'P1350438-PH2',
            'P1450383-PH2',
            'P1630004-PH2',
            'P1350429-PH2',
            'P1551380-PH2',
            'P1550583-PH2',
            'P1650669-PH2',
            'P1650596-PH2',
            'P1650395-PH2',
            'P1450015-PH2',
            'P1550967-PH2',
            'P1550571-PH2',
            'P1300882-PH2',
            'P1450883-PH2',
            'P1450962-PH2',
            'P1551326-PH2',
            'P1450907-PH2',
            'P1450804-PH2',
            'P1551548-PH2',
            'P1551585-PH2',
            'P1450650-PH2',
            'P1551647-PH2',
            'P1551493-PH2',
            'P1551728-PH2',
            'P1551729-PH2',
            'P1650049-PH2',
            'P1650297-PH2',
            'P1550633-PH2',
            'P1301089-PH2',
            'P1550450-PH2',
            'P1551400-PH2',
            'P1451231-PH2',
            'P1550617-PH2',
            'P1550684-PH2',
            'P1201973-PH2',
            'P1201970-PH2',
            'P1300360-PH2',
            'P1450766-PH2',
            'P1201968-PH2',
            'P1201967-PH2',
            'P1550665-PH2',
            'P1551170-PH2',
            'P1301090-PH2',
            'P1300750-PH2',
            'P1450055-PH2',
            'P0040209-PH2',
            'P1650746-PH2',
            'P1551295-PH2',
            'P1551537-PH2',
            'P1451152-PH2',
            'P1451124-PH2',
            'P1451121-PH2',
            'P1451138-PH2',
            'P1202251-PH2',
            'P1101128-PH2',
            'P1101144-PH2',
            'P1300066-PH2',
            'P1551372-PH2',
            'P1551342-PH2',
            'P1551301-PH2',
            'P1551047-PH2',
            'P1450824-PH2',
            'P1350040-PH2',
            'P1350045-PH2',
            'P1551428-PH2',
            'P1650571-PH2',
            'P1551638-PH2',
            'P1650063-PH2',
            'P1650650-PH2',
            'P1451097-PH2',
            'P1550605-PH2',
            'P1650732-PH2',
            'P1551171-PH2',
            'P1551177-PH2',
            'P1650410-PH2',
            'M15014-PH2',
            'M15015-PH2',
            'M16007-PH2',
            'M15013-PH2',
            'P1551526-PH2',
            'P1550309-PH2',
            'P1551717-PH2',
            'P1010661-PH2',
            'P1650774-PH2',
            'P1300697-PH2',
            'P1650425-PH2',
            'P1551107-PH2',
            'P1450604-PH2',
            'P1451313-PH2',
            'P1650142-PH2',
            'P1650742-PH2',
            'P1650767-PH2',
            'P1350137-PH2',
            'P1450592-PH2',
            'P1551062-PH2',
            'P1651210-PH2',
        ]
        source = self.search([('code', '=', source_project)])
        targets = self.search([('code', 'in', target_projects)])
        if source and targets:
            for target in targets:
                target.budget_plan_ids.unlink()
                for line in source.budget_plan_ids:
                    line.copy({'project_id': target.id})
                print '======= %s =======' % target.code