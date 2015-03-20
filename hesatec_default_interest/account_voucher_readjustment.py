# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import pooler
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import time
import dateutil
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from openerp import netsvc
import calendar


#------------- HERENCIA EN ACCOUNT INVOICE PARA PODER VALIDAR UNA VES  HECHA LA READECUACION -------------#

class account_invoice(osv.osv):
    _inherit ='account.invoice'
    _columns = {
        'readecuacion': fields.boolean('Se creo una readecuacion'),
    }
    

account_invoice()



#------------- ASISTENTE PARA LAS READECUACIONES DE PAGOS -------------#

class invoice_readjustment(osv.osv_memory):

    _name = 'invoice.readjustment'
    _description = 'Readecuacion de Adeudo de Clientes'

    _columns = {
        'name': fields.char('Folio', size=64, ondelete='cascade', readonly=True),
        'date': fields.datetime('Fecha'),
        'session_ids': fields.many2one('account.invoice', 'Factura', ondelete='cascade', readonly=True),
        'order_line'     : fields.one2many('account.invoice.simulation.line_', 'order_id', 'Líneas de Venta'),
        'detail_line'    : fields.one2many('account.invoice.simulation.detail_', 'order_id', 'Tabla de Amortización'),
        'annual_interest_rate': fields.float('Tasa Interés Anual (%)', required=True, digits_compute= dp.get_precision('Account')),
        'comission_adm': fields.float('Comision Administrativa (%)', required=True, digits_compute= dp.get_precision('Account')),
        'terms'          : fields.integer('Plazo (Meses)', required=True),
        'amount_r': fields.float('Monto Readecuacion ', readonly=True, digits_compute= dp.get_precision('Account')),
        # 'amount_r': fields.float('Monto Readecuacion $ ',  digits_compute= dp.get_precision('Account')),
        'intrest_admtvo': fields.float('Interes Administrativo ', readonly=True, digits_compute= dp.get_precision('Account')),
        'subtotal': fields.float('Subtotal ', readonly=True, digits_compute= dp.get_precision('Account')),
        'annual_interest': fields.float('Taza Anual ', readonly=True, digits_compute= dp.get_precision('Account')),
        'total': fields.float('Total a Financiar ', readonly=True, digits_compute= dp.get_precision('Account')),
        'termns': fields.float('Cuotas ', readonly=True, digits_compute= dp.get_precision('Account')),
        'payment_term': fields.many2one('account.payment.term', 'Terminos de Pago', required=True),
        'journal_id': fields.many2one('account.journal', 'Refund Journal', help='You can select here the journal to use for the credit note that will be created. If you leave that field empty, it will use the same journal as the current invoice.'),

        }

    def _get_active_session(self,cr,uid,context=None): # esta funcion en el wizard le va agregar por defecto la session en la que estamos
        res = {}
        active_id = context and context.get('active_id', False)
        acc_obj = self.pool.get('account.invoice')
        acc = acc_obj.browse(cr, uid, active_id, context=context)
        return acc.id


    # def _get_payment(self,cr,uid,context=None): # esta funcion en el wizard le va agregar por defecto la session en la que estamos
    #     res = {}
    #     active_id = context and context.get('active_id', False)
    #     acc_obj = self.pool.get('account.invoice')
    #     acc = acc_obj.browse(cr, uid, active_id, context=context)
    #     print "################################## ACTIVE ID", active_id
    #     print "################################# TERMINOS DE PAGO", acc.name
    #     print "################################# TERMINOS DE PAGO", acc.id
    #     print "################################# TERMINOS DE PAGO", acc
    #     print "################################# TERMINOS DE PAGO", acc
    #     print "################################# TERMINOS DE PAGO", acc.payment_term
    #     print "################################# TERMINOS DE PAGO", acc.payment_term.name
    #     print "################################# TERMINOS DE PAGO", acc.payment_term.id
    #     return acc.payment_term.id


    def _get_journal(self, cr, uid, context=None):
        obj_journal = self.pool.get('account.journal')
        user_obj = self.pool.get('res.users')
        if context is None:
            context = {}
        inv_type = context.get('type', 'out_invoice')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        type = (inv_type == 'out_invoice') and 'sale_refund' or \
               (inv_type == 'out_refund') and 'sale' or \
               (inv_type == 'in_invoice') and 'purchase_refund' or \
               (inv_type == 'in_refund') and 'purchase'
        journal = obj_journal.search(cr, uid, [('type', '=', type), ('company_id','=',company_id)], limit=1, context=context)
        return journal and journal[0] or False


    _defaults = {
        'date': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'session_ids' : _get_active_session,
        'journal_id': _get_journal,
        # 'payment_term': _get_payment,
        'terms'                : 12,
        'annual_interest_rate' : 0.40,
        'comission_adm'         : 0.03,
        }

    def action_calculate(self, cr, uid, ids, context=None):
        return True

    def verify_lines(self, cr, uid, ids, context=None):
        for prueba in self.browse(cr, uid, ids, context=context):
            res = 0
            for invoice_act in account_invoice_obj.browse(cr, uid, [prueba.session_ids.id], context=context):
                for lines in prueba.order_line:
                    res += 1
            print "############################################################# RESSSSS", res
        return res

    def action_create_invoice(self, cr, uid, ids, context=None):
        res = {}
        products_list = []
        active_id = context and context.get('active_id', False)
        print "####################################3 ACTIVE ID", active_id
        total_result = 0.0
        account_invoice_obj = self.pool.get('account.invoice')
        invoice_lines = []
        # invoice_refund_list = []
        account_invoice_refund_obj = self.pool.get('account.invoice.refund')
        for prueba in self.browse(cr, uid, ids, context=context):
            comission_admtva = 0.0
            subtotal_0 = 0.0
            annual_interest = 0.0
            subtotal = 0.0
            pago_01 = 0.0
            amount = 0.0
            for invoice_act in account_invoice_obj.browse(cr, uid, [prueba.session_ids.id], context=context):
                account_reconcile_id = [invoice_act.account_id.id]
                if invoice_act.readecuacion == False:
                    "############################################### PRUEBA DE SELF", prueba
                    "############################################### PRUEBA DE SELF SESSION IDS", prueba.session_ids
                    total = 0.0
                    print "############################################### PRUEBA DE SELF", prueba.amount_r
                    print "############################################### PRUEBA DE SELF", prueba.intrest_admtvo
                    print "############################################### PRUEBA DE SELF", prueba.subtotal
                    print "############################################### PRUEBA DE SELF", prueba.annual_interest
                    print "############################################### PRUEBA DE SELF", prueba.total
                    print "############################################### PRUEBA DE SELF", prueba.termns
                    print "############################################### PRUEBA DE SELF", prueba.session_ids
                    print "############################################### PRUEBA DE SELF", prueba.annual_interest_rate
                    print "############################################### PRUEBA DE SELF", prueba.terms
                    print "############################################### PRUEBA DE SELF", prueba.comission_adm
                    for lines in prueba.order_line:
                        tax_factor = 0.0
                        prod_obj = self.pool.get('product.product')
                        print "##################### LINEAS"
                        print "##################### LINEAS", lines.id
                        print "##################### LINEAS", lines.product_id.name
                        for tax in prod_obj.browse(cr, uid, [lines.product_id.id], context=None)[0].taxes_id:
                            tax_factor = (tax_factor + tax.amount) if tax.amount <> 0.0 else tax_factor
                        subtotal = lines.price_unit * lines.product_uom_qty
                        print "##################### SUBTOTAL", subtotal
                        tax_amount = subtotal * tax_factor
                        print "########################## TAX AMOUNT", tax_amount
                        total = subtotal + tax_amount
                        print "################ TOTAL ==", total
                        total_result += total
                        name = "Readecuacion de Adeudo"
                        # origin = invoice_line.
                        if lines.product_id.property_account_income:
                            account_id = lines.product_id.property_account_income.id
                        else:
                            account_id = lines.product_id.categ_id.property_account_income_categ.id
                        # uos_id = invoice_line.
                        print "##################### ", total
                        origin = ''
                        # for account in account_invoice_obj.browse(cr, uid, [active_id], context=context):
                        #     origin= account.name

                        amount = prueba.session_ids.residual
                        comission_admtva = amount * prueba.comission_adm
                        print "################# COMISION ADMINISTRATIVA", comission_admtva
                        subtotal_0 = amount + comission_admtva
                        print "############################# SUBTOTAL 0 ", subtotal_0
                        annual_interest =  subtotal_0 * prueba.annual_interest_rate
                        print "############################ COMISION ANUAL ==", annual_interest
                        subtotal = subtotal_0 + annual_interest
                        print "######################## EL TOTAL CON COMISION + INTERES ANUAL", subtotal
                        # ###### PAGOS
                        pago_01 =  subtotal / prueba.terms
                        print "####################### LOS PAGOS SERIAN DE ", pago_01

                        inv_line = (0,0,{
                        #'name': activity['product_id']['name_template'],
                        'name': name, #Descripcion
                        # 'origin': origin,
                        'account_id': account_id,
                        'price_unit': subtotal,
                        'quantity': 1,
                        # 'uos_id': activity['product_id'].uos_id.id,
                        'product_id': lines.product_id.id ,
                        # 'invoice_line_tax_id': [(6, 0, [x.id for x in lines['product_id'].supplier_taxes_id])],
                        # 'note': 'Notasss',
                        'account_analytic_id': False,
                        })
                        invoice_lines.append(inv_line)

                    # terms_obj = self.pool.get('account.payment.term')
                    # res_id = terms_obj.search(cr, uid, [('terms' , '=', prueba.terms),
                    #                                     ('annual_interest_rate', '=', prueba.annual_interest_rate),
                    #                                     ('advance_percent', '=', rec.advance_percent),
                    #                                     ('tipo_interes', '=', rec.tipo_interes)])
                    # term_id = res_id[0] if (res_id and res_id[0]) else terms_obj.create_payment_term(cr, uid, rec.advance_percent, rec.terms, rec.annual_interest_rate, rec.tipo_interes)
                    vals = {
                            'name'              : 'Readecuacion de Adeudo para '+str(prueba.session_ids.partner_id.name),
                            'origin'            : prueba.session_ids.number,
                            'type'              : 'out_invoice',
                            'journal_id'        : prueba.session_ids.journal_id.id,
                            'reference'         : prueba.session_ids.reference,
                            'account_id'        : prueba.session_ids.partner_id.property_account_receivable.id,
                            'partner_id'        : prueba.session_ids.partner_id.id,
                            'address_invoice_id': self.pool.get('res.partner').address_get(cr, uid, [prueba.session_ids.partner_id.id], ['default'])['default'] or False,
                            'address_contact_id': self.pool.get('res.partner').address_get(cr, uid, [prueba.session_ids.partner_id.id], ['default'])['default'] or False,
                            'invoice_line'      : [x for x in invoice_lines],                      #account.invoice.line
                            #'currency_id'       : data[1],                                     #res.currency
                            'comment'           : 'Sin Comentarios',
                            'payment_term'      : prueba.payment_term.id,                                    #account.payment.term
                            'fiscal_position'   : prueba.session_ids.partner_id.property_account_position.id,
                            'date_invoice'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'state'             : 'draft',

                            'advance'           : 0.0,
                            'terms'             : prueba.terms,
                            'monthly_amount'    : pago_01,
                            'intereses'         : comission_admtva + annual_interest,
                            'financiado'        : amount,
                            'total_financiado'  : subtotal,
                            'subtotal'          : subtotal_0,
                #           invoice_vals_02['tax_amount'] = order.amount_tax
                            'tax_amount'        : 0.0,
                            'total'             : subtotal,
                            'total_factura'     : subtotal,
                    }
                    account_invoice_created_id = account_invoice_obj.create(cr, uid, vals, context=context)

                    ##### Rompiendo Conciliacion de la factura para crear nota de credito

                    # refund_vals = {
                    #         'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    #         #'period': ,
                    #         'journal_id': prueba.journal_id.id,
                    #         'description': str('Readecuacion de Pago al cliente ')+prueba.session_ids.partner_id.name,
                    #         'filter_refund': 'cancel',
                    # }


                    #account_invoice_refund_created_id = account_invoice_refund_obj.create(cr, uid, refund_vals, context=context)
                    # account_invoice_refund_browse = account_invoice_refund_obj.browse(cr, uid, [account_invoice_refund_created_id], context=context)
                    # print "################################ BROWSE REFUND", account_invoice_refund_browse['filter_refund']

                    journal_id = 0
                    # if account_invoice_refund_created_id:
                    #     date_refund = ""
                    #     for refund in account_invoice_refund_obj.browse(cr, uid, [account_invoice_refund_created_id], context=context):                   
                    #         # refund.invoice_refund(cr, uid, ids, context=context)
                    #         # account_invoice_refund_obj.compute_refund(cr, uid, [account_invoice_refund_created_id], 'cancel', context=context)
                    #         data_refund = refund.read(['filter_refund'])[0]['filter_refund']
                    #         print "################################## dict refund", data_refund

                    #         refund.compute_refund(mode='cancel')
                    #         # refund.compute_refund(data_refund)
                    #         date_refund = refund.date
                    #         print "#################### refund", refund.date
                    #         print "#################### refund", refund.journal_id.id
                    #         print "#################### refund", refund.description
                    #         print "#################### refund", refund.filter_refund
                    ##### COMIENZA LA CONCILIACION AUTOMATICA
                    credit_note_lines = []
                    prod_obj_2 = self.pool.get('product.product')
                    prod_2_id = prod_obj_2.search(cr, uid, [('readjustment','=',True)])
                    prod_browse = prod_obj_2.browse(cr, uid, prod_2_id, context=None)[0]
                    
                    credit_line = (0,0,{
                    'name': prod_browse.name, #Descripcion
                    'account_id': prod_browse.property_account_income.id if prod_browse.property_account_income.id else prod_browse.categ_id.property_account_income_categ.id,
                    'price_unit': invoice_act.residual,
                    'quantity': 1,
                    'product_id': prod_browse.id ,
                    'account_analytic_id': False,
                    'invoice_line_tax_id': False,
                    #'invoice_line_tax_id':  [(6, 0, [x.id for x in prod_browse.taxes_id])],
                    })
                    credit_note_lines.append(credit_line)
                    credit_note_vals = {
                                        'type': 'out_refund',
                                        'partner_id': invoice_act.partner_id.id,
                                        'fiscal_position': invoice_act.fiscal_position.id,
                                        'journal_id': invoice_act.journal_id.id,
                                        'account_id': invoice_act.account_id.id,
                                        'invoice_line': [x for x in credit_note_lines],

                                        }
                    credit_note_id = self.pool.get('account.invoice').create(cr, uid, credit_note_vals, context=None)
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(uid, 'account.invoice', credit_note_id, 'invoice_open', cr)

                    credit_browse = self.pool.get('account.invoice').browse(cr, uid, [credit_note_id], context=None)[0]

                    move_line_obj = self.pool.get('account.move.line')
                    period_obj = self.pool.get('account.period')
                    #date_now = date.now().strftime('%Y-%m-%d')
                    #date_strp = date.strptime(date_now, '%Y-%m-%d')
                    date_replace = credit_browse.date_invoice.replace('-',' ')
                    print "####### DATE REPLACE", date_replace
                    date_split = date_replace.split()
                    print "###### DATE SPLIT", date_split
                    reconciled = unreconciled = 0
                    period_id = period_obj.search(cr, uid, [('code','=',date_split[1]+"/"+date_split[0])])
                    print "##### PERIODOS", period_id
                    cr.execute("""SELECT id
                            FROM account_move_line
                            WHERE account_id = %s
                            AND partner_id=%s
                            AND state <> 'draft'
                            AND reconcile_id IS NULL""",
                            (invoice_act.account_id.id, invoice_act.partner_id.id))
                    line_ids = [id for (id,) in cr.fetchall()]
                    if period_id:
                        move_line_obj.reconcile(cr, uid, line_ids, 'auto', invoice_act.account_id.id, period_id[0], invoice_act.journal_id.id, context)
                    elif not period_id:
                        move_line_obj.reconcile_partial(cr, uid, line_ids, 'manual', context=context)
                    automatic_reconcile_obj = self.pool.get('account.automatic.reconcile')
                    vals_reconcile = {
                                    'account_ids': [(6, 0, [x for x in account_reconcile_id])],
                                    'power': 4,
                                    }
                    automatic_reconcile_id = automatic_reconcile_obj.create(cr, uid, vals_reconcile, context=None)
                    if automatic_reconcile_id:
                        print "#### SI TENEMOS CREADO UN REGISTRO DEL WIZARD DE CONCILIACION AUTOMATICA", automatic_reconcile_id
                        for reconcile_b in automatic_reconcile_obj.browse(cr, uid, [automatic_reconcile_id], context=None):
                            print "###### RECONCILE POWER", reconcile_b.power
                            print "###### RECONCILE POWER", reconcile_b.power
                            print "###### RECONCILE POWER", reconcile_b.power
                            for account_b in reconcile_b.account_ids:
                                print "######## CUENTA", account_b.name
                                print "######## CUENTA", account_b.name
                                print "######## CUENTA", account_b.name
                                print "######## CUENTA", account_b.name
                            reconcile_b.reconcile()
                    cr.execute(
                        "SELECT id, debit " \
                        "FROM account_move_line " \
                        "WHERE account_id=%s " \
                        "AND partner_id=%s " \
                        "AND reconcile_id IS NULL " \
                        "AND state <> 'draft' " \
                        "AND debit > 0 " \
                        "ORDER BY date_maturity",
                        (invoice_act.account_id.id, invoice_act.partner_id.id))
                    debits = cr.fetchall()

                    # get the list of unreconciled 'credit transactions' for this partner
                    cr.execute(
                        "SELECT id, credit " \
                        "FROM account_move_line " \
                        "WHERE account_id=%s " \
                        "AND partner_id=%s " \
                        "AND reconcile_id IS NULL " \
                        "AND state <> 'draft' " \
                        "AND credit > 0 " \
                        "ORDER BY date_maturity",
                        (invoice_act.account_id.id, invoice_act.partner_id.id))
                    credits = cr.fetchall()
                    max_amount = 0.0
                    power = 4
                    (rec, unrec) = self.pool.get('account.automatic.reconcile').do_reconcile(cr, uid, credits, debits, max_amount, power, invoice_act.account_id.id, period_id[0], invoice_act.journal_id.id, context=None)
                    reconciled += rec
                    unreconciled += unrec
                    #### AQUI FINALIZA LA CONCILIACION AUTOMATICA


                        # voucher_obj = self.pool.get('account.voucher')
                        # voucher_ids = voucher_obj.search(cr, uid, [('partner_id','=',prueba.session_ids.partner_id.id)])
                        # voucher_browse = voucher_obj.browse(cr, uid, voucher_ids, context)[-1]
                        # print "########################### VOUCHER BROWSE", voucher_browse.journal_id
                        # print "########################### VOUCHER BROWSE", voucher_browse.journal_id.id
                        # voucher_vals = {
                        #                 'type': 'receipt',
                        #                 'reference': prueba.session_ids.number,
                        #                 'name': 'Readecuacion de Cliente '+prueba.session_ids.partner_id.name,
                        #                 'partner_id': prueba.session_ids.partner_id.id,
                        #                 'date': datetime.now().strftime('%Y-%m-%d'),
                        #                 'amount': 0.0,
                        #                 'journal_id': voucher_browse.journal_id.id if voucher_ids else journal_id,
                        #                 'account_id': prueba.session_ids.partner_id.property_account_receivable.id,
                        #                 }
                        # voucher_id = voucher_obj.create(cr, uid, voucher_vals, context)
                        # user_obj = self.pool.get('res.users')
                        # user_browse = user_obj.browse(cr, uid, [uid], context=context)[0]
                        # print "################################################# COMPAÑIA", user_browse
                        # print "################################################# COMPAÑIA", user_browse.name
                        # print "################################################# COMPAÑIA", user_browse.company_id
                        # print "################################################# COMPAÑIA", user_browse.company_id.id
                        # currency_id = user_browse.company_id.currency_id.id
                        # print "#################################################### CURRENCY ID", currency_id
                        # print "#################################################### CURRENCY ID", currency_id
                        # for voucher_b in voucher_obj.browse(cr, uid, [voucher_id], context=context):
                        #     voucher_b.onchange_partner_id(prueba.session_ids.partner_id.id,  voucher_browse.journal_id.id, 0.0, currency_id, 'receipt', datetime.now().strftime('%Y-%m-%d'))
                        #     voucher_b.write({'name':voucher_b.name})
                        #     # voucher_b.write({'default_interest': False})
                        #     voucher_b.write({'partner_id':prueba.session_ids.partner_id.id})
                        #     # voucher_b.write({'default_interest':True})
                        #     voucher_b.onchange_partner_id(prueba.session_ids.partner_id.id,  voucher_browse.journal_id.id, 0.0, currency_id, 'receipt', datetime.now().strftime('%Y-%m-%d'))
                        #     #voucher_b.obtain_values_interest()
                        # print "############################ SE CREO EL PAGOOOOOOOOOOOOOOOO", voucher_id
                        # print "############################ SE CREO EL PAGOOOOOOOOOOOOOOOO", voucher_id
                        # print "############################ SE CREO EL PAGOOOOOOOOOOOOOOOO", voucher_id
                        # print "############################ SE CREO EL PAGOOOOOOOOOOOOOOOO", voucher_id
                    invoice_act.write({'readecuacion': True})
                else:
                    raise osv.except_osv(
                                        _('Error !'),
                                        _('La Factura ya fue readecuada para el cliente %s'  % (invoice_act.partner_id.name)))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura por Readecuacion'),
            'res_model': 'account.invoice',
            'res_id': account_invoice_created_id ,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'current',
            'nodestroy': True,
        }

        # return True


    def on_change_products(self, cr, uid, ids, session_ids, annual_interest_rate, comission_adm, terms, context=None):
        res = {}
        products_list = []
        active_id = context and context.get('active_id', False)
        prod_obj = self.pool.get('product.product')
        prod_id = prod_obj.search(cr, uid, [('readjustment','=',True)])
        account_invoice_obj = self.pool.get('account.invoice')

        amount = 0.0
        for account in account_invoice_obj.browse(cr, uid, [session_ids], context=context):
            amount += account.residual
        comission_admtva = amount * comission_adm
        print "################# COMISION ADMINISTRATIVA", comission_admtva
        subtotal_0 = amount + comission_admtva
        print "############################# SUBTOTAL 0 ", subtotal_0
        annual_interest =  subtotal_0 * annual_interest_rate
        print "############################ COMISION ANUAL ==", annual_interest
        subtotal = subtotal_0 + annual_interest
        print "######################## EL TOTAL CON COMISION + INTERES ANUAL", subtotal
        # ###### PAGOS
        pago_01 =  subtotal / terms
        print "####################### LOS PAGOS SERIAN DE ", pago_01

        if not prod_id:
            return {}

        xline = (0 ,0,{
            'product_id': prod_id[0],
            'product_uom_qty': 1,
            'price_unit': subtotal,
            'xsubtotal': subtotal,
            'xtotal': subtotal,
            'xtax_amount': 0.0,
            'total': subtotal,
            'subtotal': subtotal,
            'sequence': 01,
            })
        products_list.append(xline)
        advance_percent = 0.0
        tipo_interes = False
        terms_obj = self.pool.get('account.payment.term')
        res_id = terms_obj.search(cr, uid, [('terms' , '=', terms),
                                            ('annual_interest_rate', '=', annual_interest_rate),
                                            ('advance_percent', '=', advance_percent),
                                            ('tipo_interes', '=', tipo_interes)])
        term_id = res_id[0] if (res_id and res_id[0]) else terms_obj.create_payment_term(cr, uid, advance_percent, terms, annual_interest_rate, tipo_interes)

        if term_id:
            print "########################### TERM ID", term_id
            for term in terms_obj.browse(cr, uid, [term_id], context=context):
                print "##################### TERMINOS", term.name
                for term_line in term.line_ids:
                    print "##################### TERMINOS LINEAS", term_line.value_amount
                    if term_line.value_amount == 0.0:
                        term_line.unlink()

        return {'value' : {'order_line' : [x for x in products_list], 'amount_r': amount, 'intrest_admtvo': comission_admtva, 'subtotal': subtotal_0, 'annual_interest':annual_interest, 'total': subtotal, 'termns':pago_01, 'payment_term': term_id}}

    # def create(self, cr, uid, vals, context=None):
    #     print "Si entra aqui..."
    #     seq_obj = self.pool.get('ir.sequence')
    #     seq_id = seq_obj.search(cr, uid, [('name', '=', 'SIMULA')])
    #     if seq_id:
    #         seq_number = seq_obj.get_id(cr, uid, seq_id)
    #         vals['name'] = seq_number
    #     res = super(sale_order_simulation_, self).create(cr, uid, vals, context=context)
    #     self.calculate_amortization(cr, uid, [res])
    #     return res

    def write(self, cr, uid, ids, vals, context=None):
        super(invoice_readjustment, self).write(cr, uid, ids, vals, context=context)
        self.calculate_amortization(cr, uid, ids)
        return True

    def calculate_amortization(self, cr, uid, ids, context=None):
        cr.execute("delete from invoice_readjustment where order_id in %s",(tuple(ids),))
        for rec in self.browse(cr, uid, ids):
            details = []
            amount = rec.monthly_amount * rec.terms
            detail = {
                'order_id'       : rec.id,
                'name'           : ('Prima %s') % (rec.advance_percent),
                'date'           : rec.date,        
                'initial_balance': rec.advance + (rec.monthly_amount * rec.terms), 
                'monthly_amount' : rec.advance,
                'ending_balance' : amount,
                'sequence'       : 0,                    
                }
            detail_id = self.pool.get('sale.order.simulation.detail_').create(cr, uid, detail)
            
            for x in range(rec.terms):
                y = x+1
                detail = {
                    'order_id'       : rec.id,
                    'name'           : ('Mensualidad %s') % (y),
                    'date'           : (dateutil.parser.parse(rec.date) + relativedelta( months = +y )).isoformat(),
                    'initial_balance': amount,
                    'monthly_amount' : rec.monthly_amount,
                    'ending_balance' : amount - rec.monthly_amount if y < rec.terms else 0.0,
                    'sequence'       : y,
                    }
                amount -= rec.monthly_amount
                detail_id = self.pool.get('sale.order.simulation.detail_').create(cr, uid, detail)

        return


invoice_readjustment()




class account_invoice_simulation_line_(osv.osv_memory):

    """ Account Invoice Simulation Line"""

    _name = 'account.invoice.simulation.line_'
    _rec_name = 'product_id'
    _columns = {
        'order_id'       : fields.many2one('invoice.readjustment', 'Invoice Reference', required=True),
        'sequence'       : fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'product_id'     : fields.many2one('product.product', 'Producto', domain=[('sale_ok', '=', True)], required=True),
        'product_uom_qty': fields.float('Cantidad', digits_compute= dp.get_precision('Product UoS'), required=True),
        # 'product_uom'    : fields.many2one('product.uom', 'Unidad de Medida', required=True),
        'price_unit'     : fields.float('Precio Unit.', required=True, digits_compute= dp.get_precision('Product Price')),
        'subtotal'       : fields.float('Subtotal', required=True, digits_compute= dp.get_precision('Product Price')),
        'tax_amount'     : fields.float('Impuestos', required=False, digits_compute= dp.get_precision('Product Price')),
        'total'          : fields.float('Total', required=True, digits_compute= dp.get_precision('Product Price')),
        'xsubtotal'      : fields.float('Subtotal', digits_compute= dp.get_precision('Product Price')),
        'xtax_amount'    : fields.float('Impuestos', digits_compute= dp.get_precision('Product Price')),
        'xtotal'         : fields.float('Total', digits_compute= dp.get_precision('Product Price')),
        # 'partner_id'     : fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', string='Cliente'),
        'pricelist_id'   : fields.many2one('product.pricelist', 'Lista de Precios'),
        }

    _defaults ={
        'xsubtotal'       : 0.0,
        'xtax_amount'     : 0.0,
        'xtotal'          : 0.0,
        'product_uom_qty' : 1.0,
        } 


    def on_change_product_id(self, cr, uid, ids, product_id, product_uom_qty, partner_id, pricelist_id, context=None):
        result = {}
        for product in self.pool.get('product.product').browse(cr, uid, [product_id]):
            # result.update({'product_uom' : product.uom_id.id})
            # get unit price
            
            if not pricelist_id:
                raise osv.except_osv(_('Error!'),
                                     _('Debe seleccionar primero un cliente en el formulario !\n'
                                       'Por favor seleccione un cliente antes de seleccionar algún producto.'))
                
            else:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
                                                                     product_id, product_uom_qty or 1.0, partner_id, {
                        # 'uom': product_uom or False,
                        'date': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        })[pricelist_id]
                if price is False:
                    raise osv.except_osv(_('Error!'),
                                         _('No se pudo obtener el precio para este producto y cantidad.\n'
                                           'Cambie el producto, la cantidad o la lista de precios.'))
                else:
                    result.update({'price_unit': price})
        return {'value' : result}

    def on_change_values(self, cr, uid, ids, product_id, product_uom_qty=False, price_unit=False, context=None):
        if not (product_uom_qty and price_unit and product_id):
            return {}
        tax_factor = 0.00
        prod_obj = self.pool.get('product.product')
        for tax in prod_obj.browse(cr, uid, [product_id], context=None)[0].taxes_id:
            tax_factor = (tax_factor + tax.amount) if tax.amount <> 0.0 else tax_factor
        subtotal = price_unit * product_uom_qty
        tax_amount = subtotal * tax_factor
        total = subtotal + tax_amount
        return {'value' : 
                {
                'subtotal'   : subtotal,
                'tax_amount' : tax_amount,
                'total'      : total,
                'xsubtotal'   : subtotal,
                'xtax_amount' : tax_amount,
                'xtotal'      : total,
                 }
                }


class account_invoice_simulation_detail_(osv.osv_memory):

    """ Account Invoice Simulation Line"""

    _name = 'account.invoice.simulation.detail_'
    _description = 'Sale Order Simulation Payments Detail _'

    _columns = {
        'order_id'       : fields.many2one('invoice.readjustment', 'Order Reference', required=True),
        'name'           : fields.text('Description'),
        'date'           : fields.date('Fecha'),        
        'monthly_amount' : fields.float('Pago Mensual', required=True, digits_compute= dp.get_precision('Account')),
        'initial_balance': fields.float('Saldo Inicial', required=True, digits_compute= dp.get_precision('Account')),
        'ending_balance' : fields.float('Saldo Final', required=True, digits_compute= dp.get_precision('Account')),
        'sequence'       : fields.integer('Sequence'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
