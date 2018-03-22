# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Custom Module",
  "summary"              :  "Customization from HCS (Pvt.) Ltd",
  "category"             :  "Custom",
  "version"              :  "1.0",
  "sequence"             :  1,
  "author"               :  "M. Faizan | +923322676365 | Senior Odoo Techno-Functional Consultant | Karachi, Pakistan",
  "website"              :  "mfaizan@outlook.com",
  "description"          :  """""",
  "live_test_url"        :  "",
  "depends"              :  [
                             'base',
                             'sale',
                             'stock',
                             'jasper_reports',
                            ],
  "data"                 :  ['views/view.xml',
			     'views/report.xml',
			     'wizard/customer_ledger_view.xml',
			     'wizard/supplier_ledger_view.xml',
			     'wizard/partner_trial_view.xml',
			     'wizard/aging_report_view.xml',
			     'wizard/aging_report_supplier_view.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}
