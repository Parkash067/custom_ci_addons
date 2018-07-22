import time
from lxml import etree
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp
from openerp import api


class writeoff_amount(osv.osv):
    _inherit = "account.voucher"
    _columns = {
        "tax_amount": fields.float('Base Amount', store=True),
        "write_off_line": fields.one2many('multiple.writeoff.part', 'voucher', 'Write-Off', store=True),
        "multi_counter_parts": fields.boolean('Multiple Counter Part', store=True),
        "payment_method": fields.selection([('with_writeoff', 'Reconcile Payment Balance'), ], 'Payment Method',
                                           help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s)"),

    }

    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency,
                                 context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        tot_line = line_total
        tot_amount = 0.0
        move_line_obj = self.pool.get('account.move.line')
        obj = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        for line in obj.write_off_line:
            tot_amount += line.writeoff_amount

        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=context)
        rec_lst_ids = []
        if obj.multi_counter_parts == True:
            for line in voucher.line_ids:
                move_line = {
                    'journal_id': voucher.journal_id.id,
                    'period_id': voucher.period_id.id,
                    'name': line.name or '/',
                    'account_id': voucher.partner_id.property_account_payable.id,
                    'move_id': move_id,
                    'partner_id': voucher.partner_id.id,
                    'currency_id': line.move_line_id and (
                            company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': tot_amount,
                    'date': voucher.date
                }
                voucher_line = move_line_obj.create(cr, uid, move_line)
                rec_lst_ids = [voucher_line, line.move_line_id.id]
            return (tot_line, rec_lst_ids)
        else:
            return super(writeoff_amount, self).voucher_move_line_create(cr, uid, voucher_id, line_total, move_id,
                                                                         company_currency, current_currency,
                                                                         context=None)

    def writeoff_move_line_get(self, cr, uid, voucher_id, account, line_total, comment, payment_method, move_id, name,
                               company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        obj = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        if obj.multi_counter_parts == True:
            currency_obj = self.pool.get('res.currency')
            move_line = {}

            voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
            current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

            if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
                diff = line_total
                account_id = False
                print account_id
                write_off_name = ''
                if voucher.payment_method == 'with_writeoff':
                    account_id = account
                    write_off_name = comment  # voucher.comment
                elif voucher.partner_id:
                    if voucher.type in ('sale', 'receipt'):
                        account_id = voucher.partner_id.property_account_receivable.id
                        print account_id
                    else:
                        account_id = voucher.partner_id.property_account_payable.id
                else:
                    # fallback on account of voucher
                    account_id = voucher.account_id.id
                sign = voucher.type == 'payment' and -1 or 1
                move_line = {
                    'name': write_off_name or name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': voucher.partner_id.id,
                    'date': voucher.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    'amount_currency': company_currency <> current_currency and (sign * -1 * line_total) or 0.0,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
                }

            return move_line

        else:
            '''
                   Set a dict to be use to create the writeoff move line.

                   :param voucher_id: Id of voucher what we are creating account_move.
                   :param line_total: Amount remaining to be allocated on lines.
                   :param move_id: Id of account move where this line will be added.
                   :param name: Description of account move line.
                   :param company_currency: id of currency of the company to which the voucher belong
                   :param current_currency: id of currency of the voucher
                   :return: mapping between fieldname and value of account move line to create
                   :rtype: dict
                   '''
            currency_obj = self.pool.get('res.currency')
            move_line = {}

            voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
            current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

            if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
                diff = line_total
                account_id = False
                write_off_name = ''
                if voucher.payment_option == 'with_writeoff':
                    account_id = voucher.writeoff_acc_id.id
                    write_off_name = voucher.comment
                elif voucher.partner_id:
                    if voucher.type in ('sale', 'receipt'):
                        account_id = voucher.partner_id.property_account_receivable.id
                    else:
                        account_id = voucher.partner_id.property_account_payable.id
                else:
                    # fallback on account of voucher
                    account_id = voucher.account_id.id
                sign = voucher.type == 'payment' and -1 or 1
                move_line = {
                    'name': write_off_name or name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': voucher.partner_id.id,
                    'date': voucher.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    'amount_currency': company_currency <> current_currency and (
                            sign * -1 * voucher.writeoff_amount) or 0.0,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
                }

            return move_line

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.multi_counter_parts == True:
            if context is None:
                context = {}
            move_pool = self.pool.get('account.move')
            move_line_pool = self.pool.get('account.move.line')
            for voucher in self.browse(cr, uid, ids, context=context):
                local_context = dict(context, force_company=voucher.journal_id.company_id.id)
                if voucher.move_id:
                    continue
                company_currency = self._get_company_currency(cr, uid, voucher.id, context)
                current_currency = self._get_current_currency(cr, uid, voucher.id, context)
                # we select the context to use accordingly if it's a multicurrency case or not
                context = self._sel_context(cr, uid, voucher.id, context)
                # But for the operations made by _convert_amount, we always need to give the date in the context
                ctx = context.copy()
                ctx.update({'date': voucher.date})
                # Create the account move record.
                move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context),
                                           context=context)
                # Get the name of the account_move just created
                name = move_pool.browse(cr, uid, move_id, context=context).name
                # Create the first line of the voucher
                move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr, uid, voucher.id, move_id,
                                                                                       company_currency,
                                                                                       current_currency, local_context)
                                                     , local_context)
                move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
                line_total = move_line_brw.debit - move_line_brw.credit
                rec_list_ids = []
                if voucher.type == 'sale':
                    line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
                elif voucher.type == 'purchase':
                    line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
                # Create one move line per voucher line where amount is not 0.0
                line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id,
                                                                         company_currency, current_currency, context)

                # Create the writeoff line if needed  voucher.writeoff_acc_id.id
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.total>>>>>>>>>>>>>>>>>>>>>>>>>>>>", line_total)

                for multipart_line in obj.write_off_line:
                    ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, multipart_line.account.id,
                                                              multipart_line.writeoff_amount, multipart_line.comment,
                                                              obj.payment_method, move_id, name,
                                                              company_currency, current_currency, local_context)

                    if ml_writeoff:
                        move_line_pool.create(cr, uid, ml_writeoff, local_context)

                # We post the voucher.
                self.write(cr, uid, [voucher.id], {
                    'move_id': move_id,
                    'state': 'posted',
                    'number': name,
                })
                if voucher.journal_id.entry_posted:
                    move_pool.post(cr, uid, [move_id], context={})
                # We automatically reconcile the account move lines.
                _rec_ids = []
                reconcile = False
                for dr_id in obj.line_dr_ids:
                    c_move_id = move_line_pool.search(cr, uid, [('id', '=', dr_id.move_line_id.id)])[0]
                    _rec_ids.append(c_move_id)
                _rec_ids.append(move_line_pool.search(cr, uid, [('move_id', '=', move_id), ('debit', '>', 0)])[0])
                if len(_rec_ids) >= 2:
                    print(">>>>>>>>>>>>>>>>>>>>>>>Rec_ids>>>>>>>>>>>>>>>>>>>>>>>>>>", _rec_ids)
                    reconcile = move_line_pool.reconcile_partial(cr, uid, _rec_ids,
                                                                 writeoff_acc_id=voucher.writeoff_acc_id.id,
                                                                 writeoff_period_id=voucher.period_id.id,
                                                                 writeoff_journal_id=voucher.journal_id.id)

            return True
        else:
            if context is None:
                context = {}
            move_pool = self.pool.get('account.move')
            move_line_pool = self.pool.get('account.move.line')
            for voucher in self.browse(cr, uid, ids, context=context):
                local_context = dict(context, force_company=voucher.journal_id.company_id.id)
                if voucher.move_id:
                    continue
                company_currency = self._get_company_currency(cr, uid, voucher.id, context)
                current_currency = self._get_current_currency(cr, uid, voucher.id, context)
                # we select the context to use accordingly if it's a multicurrency case or not
                context = self._sel_context(cr, uid, voucher.id, context)
                # But for the operations made by _convert_amount, we always need to give the date in the context
                ctx = context.copy()
                ctx.update({'date': voucher.date})
                # Create the account move record.
                move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context),
                                           context=context)
                # Get the name of the account_move just created
                name = move_pool.browse(cr, uid, move_id, context=context).name
                # Create the first line of the voucher
                move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr, uid, voucher.id, move_id,
                                                                                       company_currency,
                                                                                       current_currency, local_context),
                                                     local_context)
                move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
                line_total = move_line_brw.debit - move_line_brw.credit
                rec_list_ids = []
                if voucher.type == 'sale':
                    line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
                elif voucher.type == 'purchase':
                    line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
                # Create one move line per voucher line where amount is not 0.0
                line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id,
                                                                         company_currency, current_currency, context)

                # Create the writeoff line if needed
                ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, 0, line_total, '', '', move_id, name,
                                                          company_currency, current_currency, local_context)

                if ml_writeoff:
                    move_line_pool.create(cr, uid, ml_writeoff, local_context)
                # We post the voucher.
                self.write(cr, uid, [voucher.id], {
                    'move_id': move_id,
                    'state': 'posted',
                    'number': name,
                })
                if voucher.journal_id.entry_posted:
                    move_pool.post(cr, uid, [move_id], context={})
                # We automatically reconcile the account move lines.
                reconcile = False
                for rec_ids in rec_list_ids:
                    if len(rec_ids) >= 2:
                        print(">>>>>>>>>>>>>>>>>>>>>>>Rec_ids>>>>>>>>>>>>>>>>>>>>>>>>>>", rec_ids)
                        reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids,
                                                                     writeoff_acc_id=voucher.writeoff_acc_id.id,
                                                                     writeoff_period_id=voucher.period_id.id,
                                                                     writeoff_journal_id=voucher.journal_id.id)
            return True


class multiple_writeoff_parts(osv.osv):
    _name = "multiple.writeoff.part"
    _columns = {
        'voucher': fields.many2one('account.voucher', 'Voucher'),
        'account': fields.many2one('account.account', 'Counterpart Account', store=True,
                                   domain="['|',('type','=','other'),('type','=','liquidity')]"),
        "writeoff_amount": fields.float('Amount', store=True),
        "comment": fields.char('Cheque No.', store=True, default='Write-Off'),
        "taxes": fields.many2one('account.tax', 'Taxes', store=True),
    }

    @api.onchange('account')
    def cal_taxes(self):
        if len(self.account.tax_ids) > 0:
            for tax in self.account.tax_ids:
                self.writeoff_amount = self.voucher.tax_amount * tax.amount
