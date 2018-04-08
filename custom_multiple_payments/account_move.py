from openerp.osv import fields, osv
from openerp import api,_
from openerp.exceptions import except_orm, Warning, RedirectWarning


class generalEntryCreate(osv.osv):
    _inherit = "account.move"
    _columns = {
       
    }

    def button_cancel(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        obj.count = obj.count +1
        for move in self.browse(cr, uid, ids, context=context):
            # check that all accounts have the same topmost ancestor
            top_common = None
            for line in move.line_id:
                invoice_status = "open"
                if (line.customer_invoice.residual == 0.0 and line.customer_invoice.id):
                    cr.execute(
                        'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                            line.customer_invoice.id))
                    cr.execute(
                        'UPDATE account_invoice SET residual =' + "'" + str(line.credit) + "'" + 'WHERE id =' + str(
                            line.customer_invoice.id))
                elif (line.customer_invoice.residual+line.credit == line.customer_invoice.amount_total and line.customer_invoice.id):
                    cr.execute(
                        'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                            line.customer_invoice.id))
                    cr.execute(
                        'UPDATE account_invoice SET residual =' + "'" + str(line.customer_invoice.residual+line.credit) + "'" + 'WHERE id =' + str(
                            line.customer_invoice.id))

        for line in self.browse(cr, uid, ids, context=context):
            if not line.journal_id.update_posted:
                raise osv.except_osv(_('Error!'), _(
                    'You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
        if ids:
            cr.execute('UPDATE account_move ' \
                       'SET state=%s ' \
                       'WHERE id IN %s', ('draft', tuple(ids),))
            self.invalidate_cache(cr, uid, context=context)
        return True

    def button_validate(self, cursor, user, ids, context=None):
        obj = self.browse(cursor, user, ids[0], context=context)
        if obj.parts_payment == 'Entered cheque from HMB':
            if obj.journal_id.name == 'Bank (BOP 1955-4)':
                if (obj.count > 0):
                    cursor.execute(
                        'UPDATE account_move_line SET ref =' + "'" + str(obj.ref) + "'" + 'WHERE move_id =' + str(
                            obj.id))
                for move in self.browse(cursor, user, ids, context=context):
                    # check that all accounts have the same topmost ancestor
                    top_common = None
                    for line in move.line_id:
                        if line.partner_id:
                            if obj.journal_id.company_id.name == obj.company_id.name == line.partner_id.company_id.name:
                                if (obj.parts_payment == 'Cheque Return'):
                                    if (line.customer_invoice.id != False):
                                        invoice_status = 'open'
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =FALSE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                else:
                                    if ((
                                                    line.credit == line.customer_invoice.grand_total or line.customer_invoice.amount_total == line.credit or line.customer_invoice.residual == line.credit) and line.customer_invoice.id):
                                        invoice_status = "paid"
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET residual =' + "'" + str(
                                                0.0) + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                    elif (
                                            line.credit > line.customer_invoice.amount_total and line.customer_invoice.id):
                                        invoice_status = "paid"
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET residual =' + "'" + str(
                                                line.credit - line.customer_invoice.amount_total) + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))

                                    elif (
                                            line.customer_invoice.amount_total > line.credit and line.customer_invoice.id):
                                        invoice_status = "open"
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET residual =' + "'" + str(
                                                line.customer_invoice.amount_total - line.credit) + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))

                                    account = line.account_id
                                    top_account = account
                                    while top_account.parent_id:
                                        top_account = top_account.parent_id
                                    if not top_common:
                                        top_common = top_account
                                    elif top_account.id != top_common.id:
                                        raise osv.except_osv(_('Error!'),
                                                             _(
                                                                 'You cannot validate this journal entry because account "%s" does not belong to chart of accounts "%s".') % (
                                                             account.name, top_common.name))
                            else:
                                raise except_orm(_('Error!'), _('All accounts must have same company.'))
                        else:
                            if line.account_id.company_id.name != obj.journal_id.company_id.name:
                                raise except_orm(_('Error!'), _('All accounts must have same company.'))

            else:
                raise except_orm(_('Error!'), _('Journal must be of bank BOP.'))

        if obj.parts_payment == 'Entered cheque from BOP':
            if obj.journal_id.name == 'Bank (HMB 13223)':
                if (obj.count > 0):
                    cursor.execute(
                        'UPDATE account_move_line SET ref =' + "'" + str(obj.ref) + "'" + 'WHERE move_id =' + str(
                            obj.id))
                for move in self.browse(cursor, user, ids, context=context):
                    # check that all accounts have the same topmost ancestor
                    top_common = None
                    for line in move.line_id:
                        if line.partner_id:
                            if obj.journal_id.company_id.name == obj.company_id.name == line.partner_id.company_id.name:
                                if (obj.parts_payment == 'Cheque Return'):
                                    if (line.customer_invoice.id != False):
                                        invoice_status = 'open'
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =FALSE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                else:
                                    if ((
                                                            line.credit == line.customer_invoice.grand_total or line.customer_invoice.amount_total == line.credit or line.customer_invoice.residual == line.credit) and line.customer_invoice.id):
                                        invoice_status = "paid"
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET residual =' + "'" + str(
                                                0.0) + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                    elif (
                                                    line.credit > line.customer_invoice.amount_total and line.customer_invoice.id):
                                        invoice_status = "paid"
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET residual =' + "'" + str(
                                                line.credit - line.customer_invoice.amount_total) + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))

                                    elif (
                                                    line.customer_invoice.amount_total > line.credit and line.customer_invoice.id):
                                        invoice_status = "open"
                                        cursor.execute(
                                            'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))
                                        cursor.execute(
                                            'UPDATE account_invoice SET residual =' + "'" + str(
                                                line.customer_invoice.amount_total - line.credit) + "'" + 'WHERE id =' + str(
                                                line.customer_invoice.id))

                                    account = line.account_id
                                    top_account = account
                                    while top_account.parent_id:
                                        top_account = top_account.parent_id
                                    if not top_common:
                                        top_common = top_account
                                    elif top_account.id != top_common.id:
                                        raise osv.except_osv(_('Error!'),
                                                             _(
                                                                 'You cannot validate this journal entry because account "%s" does not belong to chart of accounts "%s".') % (
                                                                 account.name, top_common.name))
                            else:
                                raise except_orm(_('Error!'), _('All accounts must have same company.'))
                        else:
                            if line.account_id.company_id.name != obj.journal_id.company_id.name:
                                raise except_orm(_('Error!'), _('All accounts must have same company.'))

            else:
                raise except_orm(_('Error!'), _('Journal must be of bank HMB.'))
        else:
            if(obj.count>0):
                cursor.execute('UPDATE account_move_line SET ref =' + "'" + str(obj.ref) + "'" + 'WHERE move_id =' + str(obj.id))
            for move in self.browse(cursor, user, ids, context=context):
                # check that all accounts have the same topmost ancestor
                top_common = None
                for line in move.line_id:
                    if line.partner_id:
                        if obj.journal_id.company_id.name == obj.company_id.name == line.partner_id.company_id.name:
                            if(obj.parts_payment == 'Cheque Return'):
                                if(line.customer_invoice.id != False):
                                    invoice_status = 'open'
                                    cursor.execute(
                                        'UPDATE account_invoice SET payment_received =FALSE ' + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute('UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(line.customer_invoice.id))
                            else:
                                if((line.credit == line.customer_invoice.grand_total or line.customer_invoice.amount_total == line.credit or line.customer_invoice.residual == line.credit) and line.customer_invoice.id):
                                    invoice_status = "paid"
                                    cursor.execute(
                                        'UPDATE account_invoice SET payment_received =TRUE '+ 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute(
                                        'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute(
                                        'UPDATE account_invoice SET residual =' + "'" + str(0.0) + "'" + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                elif(line.credit > line.customer_invoice.amount_total and line.customer_invoice.id):
                                    invoice_status = "paid"
                                    cursor.execute(
                                        'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute(
                                        'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute(
                                        'UPDATE account_invoice SET residual =' + "'" + str(line.credit-line.customer_invoice.amount_total) + "'" + 'WHERE id =' + str(
                                            line.customer_invoice.id))

                                elif(line.customer_invoice.amount_total > line.credit and line.customer_invoice.id):
                                    invoice_status = "open"
                                    cursor.execute(
                                        'UPDATE account_invoice SET payment_received =TRUE ' + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute(
                                        'UPDATE account_invoice SET state =' + "'" + invoice_status + "'" + 'WHERE id =' + str(
                                            line.customer_invoice.id))
                                    cursor.execute(
                                        'UPDATE account_invoice SET residual =' + "'" + str(line.customer_invoice.amount_total - line.credit) + "'" + 'WHERE id =' + str(
                                            line.customer_invoice.id))


                                account = line.account_id
                                top_account = account
                                while top_account.parent_id:
                                    top_account = top_account.parent_id
                                if not top_common:
                                    top_common = top_account
                                elif top_account.id != top_common.id:
                                    raise osv.except_osv(_('Error!'),
                                                         _('You cannot validate this journal entry because account "%s" does not belong to chart of accounts "%s".') % (account.name, top_common.name))
                        else:
                            raise except_orm(_('Error!'), _('All accounts must have same company.'))
                    else:
                        if line.account_id.company_id.name != obj.journal_id.company_id.name:
                            raise except_orm(_('Error!'), _('All accounts must have same company.'))

        return self.post(cursor, user, ids, context=context)


class mutual_account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _columns = {
        'customer_invoice': fields.many2one('account.invoice', 'Customer Invoice',store=True,domain=[('state','=', 'open')]),
    }
