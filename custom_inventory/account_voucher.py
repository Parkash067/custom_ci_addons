from openerp.osv import fields, osv
from openerp import api
from openerp.exceptions import except_orm, Warning, RedirectWarning


class account_voucher(osv.osv):
    _inherit = "account.voucher"

    _columns = {
        'cheque_date': fields.date('Cheque Date', store=True),
        'cheque_no': fields.char('Cheque No.', store=True),
    }


class account_invoice(osv.osv):
    _inherit = "account.invoice"

    @api.multi
    def account_head(self):
        if self.state == 'draft' and self.partner_id.supplier:
            self.account_id = self.partner_id.property_account_payable.id
            for line in self.invoice_line:
                if line.product_id.property_account_expense:
                    line.account_id = line.product_id.property_account_expense
                else:
                    raise except_orm(_('Error!'), _('Kindly configure expense head against this product'))

        if self.state == 'draft' and self.partner_id.customer:
            self.account_id = self.partner_id.property_account_receivable.id
            for line in self.invoice_line:
                if line.product_id.property_account_income:
                    line.account_id = line.product_id.property_account_income
                else:
                    raise except_orm(_('Error!'), _('Kindly configure expense head against this product'))
        else:
            raise except_orm(_('Error!'), _('You can reset accounts head of invoice only in draft state'))
