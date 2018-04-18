from openerp.osv import fields, osv
from openerp import api
from datetime import date,time
from openerp.tools import amount_to_text_en


class account_voucher(osv.osv):
    _inherit = "account.voucher"

    _columns = {
        'cheque_date': fields.date('Cheque Date', store=True),
        'cheque_no': fields.char('Cheque No.', store=True),
    }