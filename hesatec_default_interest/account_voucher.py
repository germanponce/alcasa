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
import os
import shutil
import time
from datetime import date, datetime, time, timedelta
import pytz


#--------------- HERENCIA A FACTURAS --------------#

class account_invoice(osv.osv):
    _inherit ='account.invoice'
    _columns = {
        'voucher_boolean_note': fields.boolean('Nota de Credito por Voucher'),
        'voucher_generated_id': fields.many2one('account.voucher', 'Voucher que lo genero'),
        'voucher_amount'      : fields.float('Monto para el Voucher', digits=(8,2)),
        'ref_voucher_id'      : fields.many2one('account.voucher', 'Ref Voucher que genero la Nota')
    }

    def invoice_validate(self, cr, uid, ids, context=None):
        result =  super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        account_voucher_obj = self.pool.get('account.voucher')
        for rec in self.browse(cr, uid, ids, context=context):

            if rec.ref_voucher_id:
                for account in account_voucher_obj.browse(cr, uid, [rec.ref_voucher_id.id], context=context):
                    account.write({'liquidation': False, 'default_interest': False, 'create_credit_note': False})
                    # print "####################################################"
                    # print "####################################################"
                    # print "####################################################", account.partner_id.name
                    # print "####################################################", account.partner_id.name
                    # print "####################################################", account.amount
                    # print "####################################################"
                    
                    # vals = {
                    #         'partner_id': account.partner_id.id,
                    #         'amount': account.amount,
                    #         'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    #         'default_interest': False,
                    #         'account_id': rec.account_id.id,
                    #         'journal_id': account.journal_id.id,
                    #         'default_interest': False,
                    # }
                    # account_voucher_id = account_voucher_obj.create(cr, uid, vals, context=context)
                    # print "################################## VOUCHER CREADO", account_voucher_id
                    # account.unlink()

        return result



account_invoice()


#------------- HERENCIA A PAGOS DE CLIENTES -------------#

class account_voucher(osv.osv):
    _inherit ='account.voucher'


    def _get_result(self, cr, uid, ids, field_name, arg, context=None):
        promd = 0.0
        i= 0
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            total = (rec.percent*12/365)*rec.days*rec.month_payment
            if total == 0.0:
               res[rec.id] = 0.0
            else:
                res[rec.id] = total
        return res

    # def _get_journal(self, cr, uid, context=None):
    #     if context is None:
    #         context = {}
    #     type_inv = context.get('type', 'out_invoice')
    #     user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
    #     company_id = context.get('company_id', user.company_id.id)
    #     type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
    #     refund_journal = {'out_invoice': False, 'in_invoice': False, 'out_refund': True, 'in_refund': True}
    #     journal_obj = self.pool.get('account.journal')
    #     res = journal_obj.search(cr, uid, [('type', '=', type2journal.get(type_inv, 'sale')),
    #                                         ('company_id', '=', company_id),
    #                                         ('refund_journal', '=', refund_journal.get(type_inv, False))],
    #                                             limit=1)
    #     print "#############################33 RESSSSSSssss", res
    #     return res and res[0] or False

    _columns = {
        'default_interest': fields.boolean('Interes Moratorio', help="Activa la casilla si el cliente tiene un restraso de pago"),
        'liquidation': fields.boolean('Liquidacion Total', help="Activa la casilla para calcular el Pago Total del Cliente"),
        'liquidation_payment': fields.float('Descuento por Liquidacion', digits=(8,2), readonly=True),
        'advanced_payment': fields.float('Descuento por Pago Adelantado', digits=(8,2), readonly=True),
        'create_credit_note': fields.boolean('Crear Nota de Credito', readonly=True),
        'default_advanced': fields.boolean('Pagos Adelantados', help="Activa la casilla si el cliente quiere realizar un pago Adelantado"),
        'days': fields.integer('Dias de Retraso', readonly=True),
        'month_payment': fields.float('Monto de Pago', digits=(8,2), readonly=True, help="""Este campo seria la sumatoria de los montos de pago seleccionados, ejemplo:
        - Pago Abril $ 850.00 + Pago Mayo $ 150.00 = Monto de Pago $ 1,000.00
        """),
        # 'customer_fee': fields.function(_get_result, string="Cargo al Cliente", method=True, type='float', digits=(18,2), store=True),
        'customer_fee': fields.float('Cargo al Cliente', digits=(8,2), readonly=True),
        'percent': fields.float('Porcentaje Extra', digits=(1,3), help="""Define el porcentaje extra para aplicar al pago el numero 1 representa el 100%, si deseamos un porcentaje menor al 100 de tendria que definir de la siguiente manera:
        - 0.20 seria igual al 20%
        - 0.30 serial igual al 30%
        - 0.03 seria igual al 3%
        - ETC...

        Nota: El porcentaje a aplicar es mensualy se aplicara al numero de dias de atraso.
        """),
        'journal_invoice_id': fields.many2one('account.journal', 'Journal', readonly=True),
        'month_ant': fields.float('Saldo Anterior', digits=(8,2), readonly=True),

    }

    def on_change_values(self, cr, uid, ids, percent, days, month_payment, context=None):
        if not (days,month_payment):
            return {}
        total = (percent*12/365)*days*month_payment
        return {'value' :
                {
                'customer_fee'      : total,
                 }
                }

    def verify_check(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            i = 0
            for rec_line in rec.line_ids:
                if rec_line.reconcile == True:
                    i = i + 1
            if i==0:
                res = True
            else:
                res = False
        return res

    def obtain_values_check(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):

            if rec.default_interest:
                self.obtain_values_interest(cr, uid, ids, context=context)
            # elif rec.default_advanced:
            #     self.obtain_values_advanced_write(cr, uid, ids, context=context)
            elif rec.liquidation:
                self.liquidation_total_write(cr, uid, ids, context=context)
            elif rec.liquidation == False and rec.default_interest == False:
            # elif rec.default_advanced == False and rec.default_interest == False:
                self.obtain_values_normal(cr, uid, ids, context=context)
        return True

    def obtain_values_check_credit_note(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.liquidation:
                account_invoice_id = self.liquidation_total(cr, uid, ids, context=context)
                return {
                        'type': 'ir.actions.act_window',
                        'name': _('Notas de Credito para Pago Adelantado'),
                        'res_model': 'account.invoice',
                        'res_id': account_invoice_id,
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': False,
                        'target': 'current',
                        'nodestroy': True,
                        }
            # elif rec.default_advanced:
            #     account_invoice_id = self.obtain_values_advanced(cr, uid, ids, context=context)

            #     return {
            #             'type': 'ir.actions.act_window',
            #             'name': _('Notas de Credito para Pago Adelantado'),
            #             'res_model': 'account.invoice',
            #             'res_id': account_invoice_id,
            #             'view_type': 'form',
            #             'view_mode': 'form',
            #             'view_id': False,
            #             'target': 'current',
            #             'nodestroy': True,
            #             }

        return True


    def pre_validate(self, cr, uid, ids, context=None):
        for r in self.browse(cr, uid, ids, context=context):
                name = ''
                i = 0
                if i == 0:
                    for line in r.line_ids:
                        name = line.name
                        move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                        terms = invoice.terms
                                        financiado = invoice.financiado
                                    i=i+1
                for l in r.line_ids:
                    if l.name == name:
                        l.write({'reconcile':True})
                        term_rest += 1
        return True

    def obtain_values_normal(self, cr, uid, ids, context=None):
        resp = self.verify_check(cr, uid, ids, context=context)
        if resp == False:
            amount_global = 0.0
            for rec in self.browse(cr, uid, ids, context=context):
                for rec_line in rec.line_ids:
                    if rec_line.reconcile == True:
                        month_payment = rec_line.amount_unreconciled
                        amount_global = amount_global + month_payment
                rec.write({'amount': amount_global,'create_credit_note': False})
        else :
            for r in self.browse(cr, uid, ids, context=context):
                i=0
                for line in r.line_ids:
                    if i == 0:
                        line.write({'reconcile':True})
                        i=i+1
                    else:
                        self.obtain_values_normal(cr, uid, ids, context=context)       
        return True

    def obtain_values_normal_lines(self, cr, uid, ids, context=None):
        resp = self.verify_check(cr, uid, ids, context=context)
        resp = self.verify_check(cr, uid, ids, context=context)
        move_line_obj =  self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        account_invoice_obj = self.pool.get('account.invoice')
        month_ant = 0.0

        if resp == False:
            amount_global = 0.0
            for rec in self.browse(cr, uid, ids, context=context):
                for rec_line in rec.line_ids:
                    if rec_line.reconcile == True:
                        month_payment = rec_line.amount_unreconciled

                        move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                        invoice_total = invoice.amount_total # Es el monto total de la factura
                                        financiado = invoice.financiado
                                        terms = invoice.terms
                                        month_ant = invoice.residual

                rec.write({'amount': amount_global,'create_credit_note': False,'month_ant': month_ant})
        else :
            for r in self.browse(cr, uid, ids, context=context):
                for line in r.line_ids:
                    line.write({'reconcile':True})
                self.obtain_values_normal_lines(cr, uid, ids, context=context)       
        return True

    def liquidation_total_write(self, cr, uid, ids, context=None):
        # resp = self.verify_check(cr, uid, ids, context=context)
        move_line_obj =  self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        account_invoice_obj = self.pool.get('account.invoice')
        month_ant = 0.0
        # if resp == False:
        term_rest = 0
        for r in self.browse(cr, uid, ids, context=context):
            name = ''
            i = 0
            if i == 0:
                for line in r.line_ids:
                    name = line.name
                    move_line_id = line.move_line_id.id
                    for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                        account_move_id = move_line.move_id.id
                        for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                            account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                            account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                            if account_invoice_id:
                                for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                    terms = invoice.terms
                                    financiado = invoice.financiado
                                i=i+1
        for l in r.line_ids:
            if l.name == name:
                l.write({'reconcile':True})
                term_rest += 1

        line_account_number = 0.0
        invoice_lines = []
        amount_unreconciled_line = 0.0
        create_write = False
        term_rest = 0
        terms = 0
        financiado = 0
        # for rec in self.browse(cr, uid, ids, context=context):
        #     interest_product_amount_abonated_global = 0.0
        #     account_id = 0
        #     move_id = 0
        #     for line in rec.line_ids:
        #         if line.reconcile == True:
        #             move_line_id = line.move_line_id.id
        #             for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
        #                 account_move_id = move_line.move_id.id
        #                 for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
        #                     account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
        #                     account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
        #                     if account_invoice_id:
        #                         for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
        #                             invoice_total = invoice.amount_total # Es el monto total de la factura
        #                             for invoice_line in invoice.invoice_line:
        #                                 if invoice_line.product_id.interest_product:
        #                                     interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
        #                                     interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
        #                                     interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
        #                                     interest_product_amount_abonated_global += interest_product_amount_abonated
        #                                     amount_unreconciled_line += line.amount_unreconciled


        for rec in self.browse(cr, uid, ids, context=context):
            interest_product_amount_abonated_global = 0.0
            account_id = 0
            move_id = 0
            for line in rec.line_ids:
                if line.reconcile == True:
                    term_rest += 1
                    move_line_id = line.move_line_id.id
                    for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                        account_move_id = move_line.move_id.id
                        for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                            account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                            account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                            if account_invoice_id:
                                for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                    invoice_total = invoice.amount_total # Es el monto total de la factura
                                    financiado = invoice.financiado
                                    terms = invoice.terms
                                    month_ant = invoice.residual
                                    for invoice_line in invoice.invoice_line:
                                        if invoice_line.product_id.interest_product:
                                            account_id = invoice_line.product_id.property_account_reclasif.id
                                            financiado =  invoice.financiado
                                            name = "Nota de Credito por Pago Adelantado cargado al producto " + invoice_line.product_id.name
                                            # origin = invoice_line.
                                            if invoice_line.product_id.property_account_income:
                                                account_id = invoice_line.product_id.property_account_income.id
                                            else:
                                                account_id = invoice_line.product_id.categ_id.property_account_income_categ.id
                                            price_unit = invoice_line.price_unit
                                            quantity = invoice_line.quantity
                                            product_id = invoice_line.product_id.id
                                            # uos_id = invoice_line.
                                            amount_unreconciled_line += line.amount_unreconciled
                                            if invoice.financiado:
                                                create_write = True


                    line.write({'amount':line.amount_unreconciled})

                                    

            if create_write == True:
                amount_payment = (financiado/terms)*term_rest
                result_amount = amount_unreconciled_line - amount_payment
                rec.write({'liquidation_payment': result_amount,'amount': amount_payment,'create_credit_note':True, 'month_ant': month_ant})
            elif create_write == False:
                self.obtain_values_normal_lines(cr, uid, ids, context=context)
        # else:
        #     term_rest = 0
        #     for r in self.browse(cr, uid, ids, context=context):
        #         name = ''
        #         i = 0
        #         if i == 0:
        #             for line in r.line_ids:
        #                 name = line.name
        #                 move_line_id = line.move_line_id.id
        #                 for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
        #                     account_move_id = move_line.move_id.id
        #                     for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
        #                         account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
        #                         account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
        #                         if account_invoice_id:
        #                             for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
        #                                 terms = invoice.terms
        #                                 financiado = invoice.financiado
        #                             i=i+1
        #     for l in r.line_ids:
        #         if l.name == name:
        #             l.write({'reconcile':True})
        #             term_rest += 1
        #     self.liquidation_total_write(cr, uid, ids, context=context)
            # print "################################### INICIANDO LA FUNCION MARCANDO LAS CASILLAS"
            # move_line_obj =  self.pool.get('account.move.line')
            # account_move_obj = self.pool.get('account.move')
            # account_invoice_obj = self.pool.get('account.invoice')
            # line_account_number = 0.0
            # invoice_lines = []
            # amount_unreconciled_line = 0.0
            # create_write = False
            # for rec in self.browse(cr, uid, ids, context=context):
            #     interest_product_amount_abonated_global = 0.0
            #     account_id = 0
            #     move_id = 0
            #     i = 0
            #     for line in rec.line_ids:
            #         move_line_id = line.move_line_id.id
            #         for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
            #             account_move_id = move_line.move_id.id
            #             for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
            #                 account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
            #                 account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
            #                 if account_invoice_id:
            #                     for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
            #                         invoice_total = invoice.amount_total # Es el monto total de la factura
            #                         for invoice_line in invoice.invoice_line:
            #                             if invoice_line.product_id.interest_product:
                                            # for r in self.browse(cr, uid, ids, context=context):
                                            #     for line in r.line_ids:
                                            #         line.write({'reconcile':True})
                                            # self.liquidation_total_write(cr, uid, ids, context=context)
        # else:
            # rec._get_writeoff_amount(cr, uid, ids, name, args, context=context)
        # else :
        #     for r in self.browse(cr, uid, ids, context=context):
        #         for line in r.line_ids:
        #             line.write({'reconcile':True})
        #         self.liquidation_total(cr, uid, ids, context=context)

        return True



    def liquidation_total(self, cr, uid, ids, context=None):
        term_rest = 0
        move_line_obj =  self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        account_invoice_obj = self.pool.get('account.invoice')
        line_account_number = 0.0
        invoice_lines = []
        amount_unreconciled_line = 0.0
        terms = 0
        financiado = 0.0

        for r in self.browse(cr, uid, ids, context=context):
            name = ''
            i = 0
            h = 0
            for line in r.line_ids:
                if line.reconcile == True:
                    h+=1

            if h == 0:
                if i == 0:
                    for line in r.line_ids:
                        name = line.name
                        move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                        terms = invoice.terms
                                        financiado = invoice.financiado
                                    i=i+1
                for l in r.line_ids:
                    if l.name == name:
                        l.write({'reconcile':True})
                        term_rest += 1
            else:
                for line in r.line_ids:
                    if line.reconcile == True:
                        term_rest += 1
                if i == 0:
                    for line in r.line_ids:
                        name = line.name
                        move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                        terms = invoice.terms
                                        financiado = invoice.financiado
                                    i=i+1




        for rec in self.browse(cr, uid, ids, context=context):
            interest_product_amount_abonated_global = 0.0
            account_id = 0
            move_id = 0
            used_form = False
            for line in rec.line_ids:
                if line.reconcile == True:
                    move_line_id = line.move_line_id.id
                    for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                        account_move_id = move_line.move_id.id
                        for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                            account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                            account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                            if account_invoice_id:
                                for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                    invoice_total = invoice.amount_total # Es el monto total de la factura
                                    for invoice_line in invoice.invoice_line:
                                        if invoice_line.product_id.interest_product:
                                            account_id = invoice_line.product_id.property_account_reclasif.id
                                            financiado =  invoice.financiado
                                            name = "Nota de Credito por Pago Adelantado cargado al producto " + invoice_line.product_id.name
                                            # origin = invoice_line.
                                            if invoice_line.product_id.property_account_income:
                                                account_id = invoice_line.product_id.property_account_income.id
                                            else:
                                                account_id = invoice_line.product_id.categ_id.property_account_income_categ.id
                                            price_unit = invoice_line.price_unit
                                            quantity = invoice_line.quantity
                                            product_id = invoice_line.product_id.id
                                            # uos_id = invoice_line.
                                            # print "########################################## amount credit abonated global", interest_product_amount_abonated_global
                                            # print "############################ FINANCIADO", financiado
                                            # print "############################ term_rest", term_rest
                                            # print "############################ terms", terms
                                            amount_unreconciled_line += line.amount_unreconciled
                                            line.write({'amount':line.amount_unreconciled})
                                            used_form = True
                ########### LAS SIGUIENTES LINEAS SE ELIMINAN PARA PODER GENERAR UN MEJOR REPORTE ##########
                else:
                    rec_line.unlink()
            if used_form == True:
                amount_payment = (financiado/terms)*term_rest
                result_amount = amount_unreconciled_line - amount_payment
            else:
                return True

            # print "############################ FINANCIADO", financiado
            # print "############################ TERMS", terms
            # print "############################ TERMS REST", term_rest
            # print "############################# EL RESULTADO DEL PAGO ES ", amount_payment
            # rec.write({'liquidation_payment': interest_product_amount_abonated_global,'amount': amount_payment})
            # rec._get_writeoff_amount(cr, uid, ids, name, args, context=context)


            inv_line = (0,0,{
            #'name': activity['product_id']['name_template'],
            'name': name, #Descripcion
            # 'origin': activity['maintenance_order_id']['product_id']['name_template'],
            'account_id': account_id,
            'price_unit': result_amount,
            'quantity': 1,
            # 'uos_id': activity['product_id'].uos_id.id,
            'product_id': product_id ,
            # 'invoice_line_tax_id': [(6, 0, [x.id for x in activity['product_id'].supplier_taxes_id])],
            # 'note': 'Notasss',
            'account_analytic_id': False,
            })
            invoice_lines.append(inv_line)
            vals = {
                    'name'              : 'Nota de Credito para '+str(rec.partner_id.name),
                    'origin'            : 'Pago Adelantado de Clientes '+str(rec.partner_id.name)+' '+str(rec.reference),
                    'type'              : 'out_refund',
                    'journal_id'        : rec.journal_id.id,
                    'reference'         : rec.reference,
                    'account_id'        : rec.partner_id.property_account_receivable.id,
                    'partner_id'        : rec.partner_id.id,
                    'address_invoice_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                    'address_contact_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                    'invoice_line'      : [x for x in invoice_lines],                      #account.invoice.line
                    #'currency_id'       : data[1],                                     #res.currency
                    'comment'           : 'Sin Comentarios',
                    #'payment_term'      : pay_term,                                    #account.payment.term
                    'fiscal_position'   : rec.partner_id.property_account_position.id,
                    'date_invoice'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'state'             : 'draft',
                    'voucher_boolean_note': True,
                    'voucher_generated_id': rec.id,
                    'voucher_amount'    : amount_payment,
                    'ref_voucher_id'    : rec.id,
            }
            account_invoice_created_id = account_invoice_obj.create(cr, uid, vals, context=context)
        
        # self.action_move_line_create(cr, uid, ids, context=context)
        return account_invoice_created_id


    def insert_payment(self, cr, uid, ids, context=None):
        move_line_obj =  self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        account_invoice_obj = self.pool.get('account.invoice')
        line_account_number = 0.0
        invoice_lines = []
        amount_unreconciled_line = 0.0
        for rec in self.browse(cr, uid, ids, context=context):
            interest_product_amount_abonated_global = 0.0
            account_id = 0
            move_id = 0
            for line in rec.line_ids:
                move_line_id = line.move_line_id.id
                for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                    account_move_id = move_line.move_id.id
                    for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                        account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                        account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                        if account_invoice_id:
                            for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                invoice_total = invoice.amount_total # Es el monto total de la factura
                                for invoice_line in invoice.invoice_line:
                                    if invoice_line.product_id.interest_product:
                                        interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                        interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                        interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                        interest_product_amount_abonated_global += interest_product_amount_abonated
                                        amount_unreconciled_line += line.amount_unreconciled
            amount_payment = amount_unreconciled_line - interest_product_amount_abonated_global
            rec.write({'liquidation_payment': interest_product_amount_abonated_global,'amount': amount_payment,'create_credit_note':True})
            # for l in rec.line_ids:
            #     if l.reconcile == False:
            #         l.write({'reconcile':True})

        return True


    def obtain_values_advanced_write(self, cr, uid, ids, context=None):
        resp = self.verify_check(cr, uid, ids, context=context)
        if resp == False:
            move_line_obj =  self.pool.get('account.move.line')
            account_move_obj = self.pool.get('account.move')
            account_invoice_obj = self.pool.get('account.invoice')
            line_account_number = 0.0
            invoice_lines = []
            for r in self.browse(cr, uid, ids, context=context):
                for l in r.line_ids:
                    if l.reconcile == True:
                        line_account_number = line_account_number + 1

            if line_account_number > 1:

                for rec in self.browse(cr, uid, ids, context=context):
                    interest_product_amount_abonated_global = 0.0
                    amount_unreconciled_line = 0.0
                    account_id = 0
                    move_id = 0
                    create_write = False
                    for line in rec.line_ids:
                        if line.reconcile == True:
                            move_line_id = line.move_line_id.id
                            for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                                account_move_id = move_line.move_id.id
                                for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                    account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                    account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                    if account_invoice_id:
                                        for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                            invoice_total = invoice.amount_total # Es el monto total de la factura
                                            for invoice_line in invoice.invoice_line:
                                                if invoice_line.product_id.interest_product:
                                                    interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                    interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                    interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                    interest_product_amount_abonated_global += interest_product_amount_abonated
                                                    amount_unreconciled_line += line.amount_unreconciled
                                                    create_write = True
                    if create_write == True:                
                        amount_payment = amount_unreconciled_line - interest_product_amount_abonated_global
                        writeoff = -1 * interest_product_amount_abonated_global
                        rec.write({'advanced_payment': interest_product_amount_abonated_global,'amount': amount_payment,'create_credit_note':True})
                    elif create_write == False:
                        self.obtain_values_normal(cr, uid, ids, context=context)
                    # rec._get_writeoff_amount(cr, uid, ids, name, args, context=context)
                    # 

            elif line_account_number == 1:
                for rec in self.browse(cr, uid, ids, context=context):
                        # ctx = context.copy()
                        # ctx.update({'date': voucher.date})
                        for line in rec.line_ids:
                            if line.reconcile == True:
                                move_line_id = line.move_line_id.id
                                for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                                    account_move_id = move_line.move_id.id
                                    for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                        account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                        account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                        if account_invoice_id:
                                            for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                                invoice_total = invoice.amount_total # Es el monto total de la factura
                                                for invoice_line in invoice.invoice_line:
                                                    if invoice_line.product_id.interest_product:
                                                        interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                        interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                        interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                        amount_unreconciled_line = line.amount_unreconciled
                                                        amount_payment = amount_unreconciled_line - interest_product_amount_abonated
                                                        writeoff = -1 * interest_product_amount_abonated
                                                        rec.write({'advanced_payment': interest_product_amount_abonated ,'amount': amount_payment, 'create_credit_note':True})
                                                        # rec.write({'advanced_payment': interest_product_amount_abonated ,'amount': amount_payment, 'writeoff_amount': self._compute_writeoff_amount()})
                                                        # rec._get_writeoff_amount(cr, uid, ids, name, args, context=context)
        else :
            for r in self.browse(cr, uid, ids, context=context):
                i=0
                for line in r.line_ids:
                    if i == 0:
                        line.write({'reconcile':True})
                        i=i+1
                    else:
                        self.obtain_values_advanced_write(cr, uid, ids, context=context)

        return True

# amount_unreconciled_line = 0.0
# amount_unreconciled_line += line.amount_unreconciled
# amount_payment = amount_unreconciled_line - interest_product_amount_abonated_global


    def obtain_values_advanced(self, cr, uid, ids, context=None):

        move_line_obj =  self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        account_invoice_obj = self.pool.get('account.invoice')
        line_account_number = 0.0
        invoice_lines = []
        account_invoice_created_id = 0
        amount_unreconciled_line = 0.0

        for r in self.browse(cr, uid, ids, context=context):
            for l in r.line_ids:
                if l.reconcile == True:
                    line_account_number = line_account_number + 1

        if line_account_number > 1:

            for rec in self.browse(cr, uid, ids, context=context):
                interest_product_amount_abonated_global = 0.0
                account_id = 0
                move_id = 0
                for line in rec.line_ids:
                    if line.reconcile == True:
                        move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                        invoice_total = invoice.amount_total # Es el monto total de la factura
                                        for invoice_line in invoice.invoice_line:
                                            if invoice_line.product_id.interest_product:
                                                interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                interest_product_amount_abonated_global += interest_product_amount_abonated
                                                account_id = invoice_line.product_id.property_account_reclasif.id
                                                name = "Nota de Credito por Pago Adelantado cargado al producto " + invoice_line.product_id.name
                                                # origin = invoice_line.
                                                if invoice_line.product_id.property_account_income:
                                                    account_id = invoice_line.product_id.property_account_income.id
                                                else:
                                                    account_id = invoice_line.product_id.categ_id.property_account_income_categ.id
                                                price_unit = invoice_line.price_unit
                                                quantity = invoice_line.quantity
                                                product_id = invoice_line.product_id.id
                                                amount_unreconciled_line += line.amount_unreconciled

                                                # uos_id = invoice_line.
                amount_payment = amount_unreconciled_line - interest_product_amount_abonated_global
                inv_line = (0,0,{
                #'name': activity['product_id']['name_template'],
                'name': name, #Descripcion
                # 'origin': activity['maintenance_order_id']['product_id']['name_template'],
                'account_id': account_id,
                'price_unit': interest_product_amount_abonated_global,
                'quantity': 1,
                # 'uos_id': activity['product_id'].uos_id.id,
                'product_id': product_id ,
                # 'invoice_line_tax_id': [(6, 0, [x.id for x in activity['product_id'].supplier_taxes_id])],
                # 'note': 'Notasss',
                'account_analytic_id': False,
                })
                invoice_lines.append(inv_line)
                vals = {
                        'name'              : 'Nota de Credito para '+str(rec.partner_id.name),
                        'origin'            : 'Pago Adelantado de Clientes '+str(rec.partner_id.name)+' '+str(rec.reference),
                        'type'              : 'out_refund',
                        'journal_id'        : '13',
                        'reference'         : rec.reference,
                        'account_id'        : rec.partner_id.property_account_receivable.id,
                        'partner_id'        : rec.partner_id.id,
                        'address_invoice_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                        'address_contact_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                        'invoice_line'      : [x for x in invoice_lines],                      #account.invoice.line
                        #'currency_id'       : data[1],                                     #res.currency
                        'comment'           : 'Sin Comentarios',
                        #'payment_term'      : pay_term,                                    #account.payment.term
                        'fiscal_position'   : rec.partner_id.property_account_position.id,
                        'date_invoice'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'state'             : 'draft',
                        'voucher_boolean_note': True,
                        'voucher_generated_id': rec.id,
                        'voucher_amount'    : amount_payment,
                }
                account_invoice_created_id = account_invoice_obj.create(cr, uid, vals, context=context)

        elif line_account_number == 1:
            for rec in self.browse(cr, uid, ids, context=context):
                    # ctx = context.copy()
                    # ctx.update({'date': voucher.date})
                    for line in rec.line_ids:
                        if line.reconcile == True:
                            move_line_id = line.move_line_id.id
                            for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                                account_move_id = move_line.move_id.id
                                for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                    account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                    account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                    if account_invoice_id:
                                        for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                            invoice_total = invoice.amount_total # Es el monto total de la factura
                                            for invoice_line in invoice.invoice_line:
                                                if invoice_line.product_id.interest_product:
                                                    interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                    interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                    interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                    account_id = invoice_line.product_id.property_account_reclasif.id
                                                    name = "Nota de Credito por Pago Adelantado cargado al producto " + invoice_line.product_id.name
                                                    # origin = invoice_line.
                                                    if invoice_line.product_id.property_account_income:
                                                        account_id = invoice_line.product_id.property_account_income.id
                                                    else:
                                                        account_id = invoice_line.product_id.categ_id.property_account_income_categ.id
                                                    price_unit = invoice_line.price_unit
                                                    quantity = invoice_line.quantity
                                                    product_id = invoice_line.product_id.id
                                                    amount_unreconciled_line = line.amount_unreconciled
                                                    amount_payment = amount_unreconciled_line - interest_product_amount_abonated
                                                    inv_line = (0,0,{
                                                                    #'name': activity['product_id']['name_template'],
                                                                    'name': name, #Descripcion
                                                                    # 'origin': activity['maintenance_order_id']['product_id']['name_template'],
                                                                    'account_id': account_id,
                                                                    'price_unit': interest_product_amount_abonated,
                                                                    'quantity': 1,
                                                                    # 'uos_id': activity['product_id'].uos_id.id,
                                                                    'product_id': product_id,
                                                                    # 'invoice_line_tax_id': [(6, 0, [x.id for x in activity['product_id'].supplier_taxes_id])],
                                                                    # 'note': 'Notasss',
                                                                    'account_analytic_id': False,
                                                    })
                                                    invoice_lines.append(inv_line)
                                                    vals = {
                                                            'name'              : 'Nota de Credito para '+str(rec.partner_id.name),
                                                            'origin'            : 'Pago Adelantado de Clientes '+str(rec.partner_id.name)+' '+str(rec.reference),
                                                            'type'              : 'out_refund',
                                                            'journal_id'        : '13',
                                                            'reference'         : rec.reference,
                                                            'account_id'        : rec.partner_id.property_account_receivable.id,
                                                            'partner_id'        : rec.partner_id.id,
                                                            'address_invoice_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                                                            'address_contact_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                                                            'invoice_line'      : [x for x in invoice_lines],                      #account.invoice.line
                                                            #'currency_id'       : data[1],                                     #res.currency
                                                            'comment'           : 'Sin Comentarios',
                                                            #'payment_term'      : pay_term,                                    #account.payment.term
                                                            'fiscal_position'   : rec.partner_id.property_account_position.id,
                                                            'date_invoice'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                            'state'             : 'draft',
                                                            'voucher_boolean_note': True,
                                                            'voucher_generated_id': rec.id,
                                                            'voucher_amount': amount_payment,
                                                    }
                                                    account_invoice_created_id = account_invoice_obj.create(cr, uid, vals, context=context)
        else :
            for r in self.browse(cr, uid, ids, context=context):
                i=0
                for line in r.line_ids:
                    if i == 0:
                        line.write({'reconcile':True})
                        i=i+1
            for rec in self.browse(cr, uid, ids, context=context):
                    # ctx = context.copy()
                    # ctx.update({'date': voucher.date})
                    for line in rec.line_ids:
                        if line.reconcile == True:
                            move_line_id = line.move_line_id.id
                            for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                                account_move_id = move_line.move_id.id
                                for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                    account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                    account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                    if account_invoice_id:
                                        for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                            invoice_total = invoice.amount_total # Es el monto total de la factura
                                            for invoice_line in invoice.invoice_line:
                                                if invoice_line.product_id.interest_product:
                                                    interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                    interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                    interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                    account_id = invoice_line.product_id.property_account_reclasif.id
                                                    name = "Nota de Credito por Pago Adelantado cargado al producto " + invoice_line.product_id.name
                                                    # origin = invoice_line.
                                                    if invoice_line.product_id.property_account_income:
                                                        account_id = invoice_line.product_id.property_account_income.id
                                                    else:
                                                        account_id = invoice_line.product_id.categ_id.property_account_income_categ.id
                                                    price_unit = invoice_line.price_unit
                                                    quantity = invoice_line.quantity
                                                    product_id = invoice_line.product_id.id
                                                    amount_unreconciled_line = line.amount_unreconciled
                                                    amount_payment = amount_unreconciled_line - interest_product_amount_abonated
                                                    inv_line = (0,0,{
                                                                    #'name': activity['product_id']['name_template'],
                                                                    'name': name, #Descripcion
                                                                    # 'origin': activity['maintenance_order_id']['product_id']['name_template'],
                                                                    'account_id': account_id,
                                                                    'price_unit': interest_product_amount_abonated,
                                                                    'quantity': 1,
                                                                    # 'uos_id': activity['product_id'].uos_id.id,
                                                                    'product_id': product_id,
                                                                    # 'invoice_line_tax_id': [(6, 0, [x.id for x in activity['product_id'].supplier_taxes_id])],
                                                                    # 'note': 'Notasss',
                                                                    'account_analytic_id': False,
                                                    })
                                                    invoice_lines.append(inv_line)
                                                    vals = {
                                                            'name'              : 'Nota de Credito para '+str(rec.partner_id.name),
                                                            'origin'            : 'Pago Adelantado de Clientes '+str(rec.partner_id.name)+' '+str(rec.reference),
                                                            'type'              : 'out_refund',
                                                            'journal_id'        : '13',
                                                            'reference'         : rec.reference,
                                                            'account_id'        : rec.partner_id.property_account_receivable.id,
                                                            'partner_id'        : rec.partner_id.id,
                                                            'address_invoice_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                                                            'address_contact_id': self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['default'])['default'] or False,
                                                            'invoice_line'      : [x for x in invoice_lines],                      #account.invoice.line
                                                            #'currency_id'       : data[1],                                     #res.currency
                                                            'comment'           : 'Sin Comentarios',
                                                            #'payment_term'      : pay_term,                                    #account.payment.term
                                                            'fiscal_position'   : rec.partner_id.property_account_position.id,
                                                            'date_invoice'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                            'state'             : 'draft',
                                                            'voucher_boolean_note': True,
                                                            'voucher_generated_id': rec.id,
                                                            'voucher_amount': amount_payment,
                                                    }
                                                    account_invoice_created_id = account_invoice_obj.create(cr, uid, vals, context=context)   
        
        # self.action_move_line_create(cr, uid, ids, context=context)
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Notas de Credito para Pago Adelantado'),
        #     'res_model': 'account.invoice',
        #     'res_id': account_invoice_created_id,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'view_id': False,
        #     'target': 'current',
        #     'nodestroy': True,
        # }
        return account_invoice_created_id






    def obtain_values_interest(self, cr, uid, ids, context=None):
        resp = self.verify_check(cr, uid, ids, context=context)
        if resp == False:
            amount_global = 0.0
            days_global = 0
            month_payment_global = 0.0
            customer_fee_global = 0.0
            month_ant = 0.0
            move_line_obj =  self.pool.get('account.move.line')
            account_move_obj = self.pool.get('account.move')
            account_invoice_obj = self.pool.get('account.invoice')
            for rec in self.browse(cr, uid, ids, context=context):
                fecha = rec.date
                for rec_line in rec.line_ids:
                    if rec_line.reconcile == True:
                        date_venc = rec_line.move_line_id.date_maturity

                        date_system = fecha

                        date_format = datetime.strptime(date_system, '%Y-%m-%d')

                        date_venc_format = datetime.strptime(date_venc, '%Y-%m-%d')

                        days = (date_format - date_venc_format).days
                        if days < 0:
                            days = 0
                        elif days > days_global:
                            days_global = days

                        month_payment = rec_line.amount_unreconciled
                        month_payment_global = month_payment_global + month_payment
                        #((20940.03*0.05)/30)*46
                        #customer_fee = (rec.percent*12/365)*days*month_payment
                        customer_fee = ((month_payment*rec.percent)/30)*days
                        customer_fee_global = customer_fee_global + customer_fee

                        amount = customer_fee + month_payment
                        amount_global =  amount_global + amount

                        # move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [rec_line.move_line_id.id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                        month_ant = invoice.residual
                        rec_line.write({'amount':rec_line.amount_unreconciled})

                    ########### LAS SIGUIENTES LINEAS SE ELIMINAN PARA PODER GENERAR UN MEJOR REPORTE ##########
                    #else:
                    #    rec_line.unlink()


                if rec.default_interest == True:
                    rec.write({'days':days_global,'month_payment': month_payment_global, 'customer_fee': customer_fee_global, 'amount': amount_global,'month_ant':month_ant})
                else:
                    rec.write({'days':days_global,'month_payment': month_payment_global, 'customer_fee': customer_fee_global,'month_ant':month_ant})
            
                    # else :
                    #     raise osv.except_osv(
                    #        _('Error !'),
                    #        _('You are not selected line for full reconcile !!!'))
        else :
            for r in self.browse(cr, uid, ids, context=context):
                date = r.date
                date_s = datetime.strptime(date, '%Y-%m-%d')
                i = 0
                
                for line in r.line_ids:
                    date_line = datetime.strptime(line.move_line_id.date_maturity, '%Y-%m-%d')
                    if date_line < date_s:
                        line.write({'reconcile':True})
                        i += 1
                if i == 0:
                    j=0
                    for line in r.line_ids:
                        if j == 0:
                            line.write({'reconcile':True})
                            j+=1
                
                self.obtain_values_interest(cr, uid, ids, context=context)


            # raise osv.except_osv(
            #     _('Error !'),
            #     _('No as seleccionado una linea para el pago!!!'))

        return True


    def on_change_payment_option(self, cr, uid, ids, default_interest, liquidation, partner_id, context=None):
    # def on_change_payment_option(self, cr, uid, ids, default_interest, liquidation, partner_id, journal_id, amount, currency_id, type, date, context=None):
    # def on_change_payment_option(self, cr, uid, ids, default_interest, default_advanced, liquidation, context=None):
        # if default_advanced == True:
        #     print "############################### ONCHANGE QUE EJECUTA LA ACTUALIZACION"
        #     product_obj = self.pool.get('product.product')
        #     product_id = product_obj.search(cr, uid, [('interest_product','=',True)], limit=1)

        #     if product_id:
        #         for product in product_obj.browse(cr, uid, product_id, context=context):
        #             account_id = product.property_account_reclasif.id
        #             print "######################### EL PRODUCTO ES", product.name, "LA CUENTA ES ",product.property_account_reclasif.name
        #     else:
        #         raise osv.except_osv(
        #                        _('Error !'),
        #                        _('No tienes una cuenta en el producto Intereses de Venta para poder Ingresar el monto por pago Adelantado !!!'))

        #     return {'value' :
        #         {
        #         'payment_option': 'with_writeoff',
        #         'writeoff_acc_id': account_id,
        #         'comment': 'Descuento por Pago Adelantado',
        #         'create_credit_note': False,
        #          }
        #          }

        if liquidation == True:
            product_obj = self.pool.get('product.product')
            product_id = product_obj.search(cr, uid, [('interest_product','=',True)], limit=1)

            if product_id:
                for product in product_obj.browse(cr, uid, product_id, context=context):
                    account_id = product.property_account_reclasif.id
            else:
                raise osv.except_osv(
                               _('Error !'),
                               _('No tienes una cuenta en el producto Intereses de Venta para poder Ingresar el monto por pago Adelantado !!!'))

            return {'value' :
                {
                'payment_option': 'with_writeoff',
                'writeoff_acc_id': account_id,
                'comment': 'Descuento por Liquidation de la Deuda (Pagos Adelantados)',
                'create_credit_note': False,
                 }
                 }

        # if default_interest == False and default_advanced == False and liquidation == False:
        if default_interest == False and liquidation == False:
            if not partner_id:
                return {'value' :
                    {
                     'payment_option': 'without_writeoff',
                     'create_credit_note': False,
                     'amount': 0.0,
                     'month_payment': 0.0,
                     'liquidation_payment': 0.0,
                     }
                     }
            else:
                partner_obj = self.pool.get('res.partner')
                for partner in partner_obj.browse(cr, uid, [partner_id], context=context):
                    partner_name = partner.name
                # self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, type, date, context=context)     
                return {'value' :
                    {
                     'payment_option': 'without_writeoff',
                     'create_credit_note': False,
                     # 'partner_id': partner_id,
                     'amount': 0.0,
                     'month_payment': 0.0,
                     'partner_id': False,
                     'liquidation_payment': 0.0,
                     }
                     }
        # if default_interest == False and default_advanced == False:
        #     print "############################### ONCHANGE QUE EJECUTA LA ACTUALIZACION"
        #     return {'value' :
        #         {
        #         'payment_option': 'without_writeoff',
        #          }
        #         }

        # if default_interest == True and default_advanced == True and liquidation == True:
        if default_interest == True and liquidation == True:
            raise osv.except_osv(
                           _('Error !'),
                           _('No se pueden marcar las 2 casillas Pago Adelantado y Cargo Moratorio!!!'))

        product_obj = self.pool.get('product.product')
        product_id = product_obj.search(cr, uid, [('interes_moratorio','=',True)], limit=1)

        if product_id:
            for product in product_obj.browse(cr, uid, product_id, context=context):
                account_id = product.property_account_income.id

        else:
            raise osv.except_osv(
                           _('Error !'),
                           _('No as creado un producto por Nombre Interes Moratorio y que tenga activada la casilla Interes Moratorio !!!'))

        return {'value' :
                {
                'payment_option': 'with_writeoff',
                'writeoff_acc_id': account_id,
                'comment': 'Cargo por intereses Moratorio',
                'create_credit_note': False,
                 }
                 }

    # def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
    #     result =  super(account_voucher, self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=context)
    #     if context is None:
    #         context = {}
    #     ctx = context.copy()
    #     ctx.update({'date': date})
    #     #read the voucher rate with the right date in the context
    #     currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
    #     voucher_rate = self.pool.get('res.currency').read(cr, uid, currency_id, ['rate'], context=ctx)['rate']
    #     ctx.update({
    #         'voucher_special_currency': payment_rate_currency_id,
    #         'voucher_special_currency_rate': rate * voucher_rate})
    #     res = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
    #     vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
    #     for key in vals.keys():
    #         res[key].update(vals[key])
    #     # vals['percent'] = 1.0
    #     for rec in self.browse(cr, uid, ids, context=context):
    #         rec.write({'percent':1})
    #     print "######################################################### ONCHANGE AMOUNT"
    #     print "######################################################### ONCHANGE AMOUNT"
    #     print "######################################################### ONCHANGE AMOUNT"
    #     return {'value': result.get('value',{})}




    # --------------------------- SUPER A ONCHANGE PARA RETORNAR SI TIENE NOTAS DE CREDITO POR CONFIRMAR ----------------------------------_#

    # def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):

    #     warning = {}
    #     title = False
    #     message = False
    #     partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
    #     title =  _("El cliente %s") % partner.name
    #     message = " Tiene Notas de Credito por Validar "
    #     # warning = {
    #     #         'title': title,
    #     #         'message': message,
    #     # }
    #     warning = {
    #             'title': title,
    #             'message': message,
    #     }
        
    #     result =  super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)

    #     for prueba in self.browse(cr, uid, ids, context=context):
    #         if not prueba.line_dr_ids:
    #             return {'value':{}}
    #     return {'value': result.get('value',{}), 'warning':warning}



    _defaults = {
        'percent': 0.03,
        # 'journal_invoice_id': _get_journal,

        'default_interest': True,
    }

    def button_dummy(self, cr, uid, ids, context=None):
        return True


    def proforma_voucher(self, cr, uid, ids, context=None):
        result =  super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)

        return result

    ################# RECLASIFICACION DE LOS PAGOS #########################
    def action_move_line_create(self, cr, uid, ids, context=None):
        result =  super(account_voucher, self).action_move_line_create(cr, uid, ids, context=context)
        move_line_obj =  self.pool.get('account.move.line')
        account_move_obj = self.pool.get('account.move')
        account_invoice_obj = self.pool.get('account.invoice')
        line_account_number = 0.0
        create_debit_credit = False
        account_str = ""
        #### CALCULANDO LA PRIMA ####
        pay_2 = 0
        prima_percent = 0.0
        prima_amount = 0.0

        for r in self.browse(cr, uid, ids, context=context):
            # ctx = context.copy()
            # ctx.update({'date': voucher.date})
            for l in r.line_ids:
                if l.reconcile == True:
                    line_account_number = line_account_number + 1

        if line_account_number > 1:

            for rec in self.browse(cr, uid, ids, context=context):
                # ctx = context.copy()
                # ctx.update({'date': voucher.date})
                interest_product_amount_abonated_global = 0.0
                account_id = 0
                move_id = 0
                globar_interest_amount_payment = 0.0

                for line in rec.line_ids:
                    if line.reconcile == True:
                        move_line_id = line.move_line_id.id
                        for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                            account_move_id = move_line.move_id.id
                            for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                if account_invoice_id:
                                    for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):

                                        ##### PRIMA #####
                                        if invoice.payment_term:
                                            i = 0
                                            number_pays=0
                                            for term in invoice.payment_term.line_ids:
                                                number_pays+=1
                                                if i == 0:
                                                    prima_percent = term.value_amount
                                                    prima_amount = invoice.amount_total* prima_percent
                                                    # print "##################### MONTO TOTAL DE LA PRIMA", prima_amount
                                                i+=1
                                            number_pays=number_pays-1
                                            # print "######################### EL TOTAL DE PAGOS ES", number_pays
                                        invoice_total = invoice.amount_total # Es el monto total de la factura
                                        # if invoice.payment_ids:
                                        #     for pay in invoice.payment_ids:
                                        #         pay_2 +=1
                                        for invoice_line in invoice.invoice_line:
                                            # print "############ FACTURA", invoice.name, "###  ", invoice.number
                                            if invoice_line.product_id.interest_product:
                                                interest_amount_payment = invoice_line.price_subtotal / number_pays
                                                # print "################ EL MONTO DE INTERES COBRADO POR PAGO ES", interest_amount_payment
                                                if line.amount_unreconciled != prima_amount:
                                                    globar_interest_amount_payment += interest_amount_payment

                                                # print "##################3 AL FINAL POR TODOS LOS PAGOS COBRAMOS EL INTERES", globar_interest_amount_payment

                                                account_str = invoice_line.product_id.name
                                                create_debit_credit = True
                                                ##interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                ##interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                ##interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                ##interest_product_amount_abonated_global += interest_product_amount_abonated

                                                account_id = invoice_line.product_id.property_account_reclasif.id
                                                # qty = invoice_line.product_uom_qty
                                                # uom_id = invoice_line.product_uom
                                                # Create the account move record
                                                # move_id = account_move_obj.create(cr, uid, self.account_move_get(cr, uid, rec.id, context=context), context=context)
                                                for move_id in rec.move_ids:
                                                    company_currency = self._get_company_currency(cr, uid, rec.id, context)
                                                    current_currency = self._get_current_currency(cr, uid, rec.id, context)
                                                    move_id = move_id.move_id.id
                                                    # if reconcile_id:
                                                    #     reconcile_id = move_id.reconcile_id.id
                if globar_interest_amount_payment > 0:
                    vals_debit = {
                            'name': account_str,
                            'account_id': account_id,
                            'move_id': move_id,
                            'partner_id': rec.partner_id.id,
                            # 'reconcile_id': reconcile_id,
                            # 'quantity': qty,
                            # 'product_uom_id': 
                            'debit': globar_interest_amount_payment,
                            'credit': 0.0,
                    }

                    vals_credit = {
                            'name': account_str,
                            'account_id': account_id,
                            'move_id': move_id,
                            'partner_id': rec.partner_id.id,
                            # 'quantity': qty,
                            # 'product_uom_id': 
                            'debit': 0.0,
                            'credit': globar_interest_amount_payment,
                    }
                    move_line__debit_id = move_line_obj.create(cr, uid, vals_debit, context=context)
                    move_line__credit_id = move_line_obj.create(cr, uid, vals_credit, context=context)

        elif line_account_number == 1:
            for rec in self.browse(cr, uid, ids, context=context):
                    # ctx = context.copy()
                    # ctx.update({'date': voucher.date})
                    for line in rec.line_ids:
                        if line.reconcile == True:
                            move_line_id = line.move_line_id.id
                            for move_line in move_line_obj.browse(cr, uid, [move_line_id], context=context):
                                account_move_id = move_line.move_id.id
                                for account_move in account_move_obj.browse(cr, uid, [account_move_id], context=context):
                                    account_name = account_move.name # Nombre de la cuenta para buscar la factura correspondiente que origino el movimiento
                                    account_invoice_id = account_invoice_obj.search(cr, uid, [('number','=',account_name)], limit=1)
                                    if account_invoice_id:
                                        for invoice in account_invoice_obj.browse(cr, uid, account_invoice_id, context=context):
                                            ##### PRIMA #####
                                            if invoice.payment_term:
                                                i = 0
                                                number_pays = 0
                                                for term in invoice.payment_term.line_ids:
                                                    number_pays+=1
                                                    if i == 0:
                                                        prima_percent = term.value_amount
                                                        prima_amount = invoice.amount_total* prima_percent
                                                        # print "##################### MONTO TOTAL DE LA PRIMA", prima_amount
                                                    i+=1
                                                number_pays=number_pays-1
                                                # print "###################### EL TOTAL DE PAGOS ES"    , number_pays
                                            if invoice.payment_ids:
                                                # print "############ FACTURA", invoice.name, "###  ", invoice.number
                                                for pay in invoice.payment_ids:
                                                    pay_2 +=1
                                            if pay_2 > 1:
                                                invoice_total = invoice.amount_total # Es el monto total de la factura
                                                for invoice_line in invoice.invoice_line:
                                                    if invoice_line.product_id.interest_product:
                                                        interest_amount_payment = invoice_line.price_subtotal / number_pays
                                                        # print "################# SE LES COBRA POR CADA PAGO EL PORCENTAJE INTERES", interest_amount_payment

                                                        ##interest_product_amount = invoice_line.price_subtotal # Es el total de intereses que estamos cobrando en la factura en monto $
                                                        ##interest_product_percent = invoice_total/interest_product_amount # Esta formula nos permite saber cual es el % porcentaje por cada pago del cliente que pertenece al abono del intereses por venta
                                                        ##interest_product_amount_abonated = line.amount_unreconciled/interest_product_percent # Esta formula separa el monto que se abona al producto intereses por venta
                                                        
                                                        # qty = invoice_line.product_uom_qty
                                                        # uom_id = invoice_line.product_uom
                                                        # Create the account move record
                                                        # move_id = account_move_obj.create(cr, uid, self.account_move_get(cr, uid, rec.id, context=context), context=context)
                                                        for move_id in rec.move_ids:
                                                            company_currency = self._get_company_currency(cr, uid, rec.id, context)
                                                            current_currency = self._get_current_currency(cr, uid, rec.id, context)
                                                            account_move_id = move_id.move_id.id
                                                            # if reconcile_id:
                                                            #     reconcile_id = move_id.reconcile_id.id

                                                        vals_debit = {
                                                                'name': "Intereses por Financiamiento",
                                                                'account_id': invoice_line.product_id.property_account_reclasif.id,
                                                                'move_id': account_move_id,
                                                                'partner_id': rec.partner_id.id,
                                                                # 'reconcile_id': reconcile_id,
                                                                # 'quantity': qty,
                                                                # 'product_uom_id': 
                                                                'debit': interest_amount_payment,
                                                                'credit': 0.0,
                                                        }

                                                        vals_credit = {
                                                                'name': "Intereses por Financiamiento",
                                                                'account_id': invoice_line.product_id.property_account_reclasif.id,
                                                                'move_id': account_move_id,
                                                                'partner_id': rec.partner_id.id,
                                                                # 'quantity': qty,
                                                                # 'product_uom_id': 
                                                                'debit': 0.0,
                                                                'credit': interest_amount_payment,
                                                        }
                                                        move_line__debit_id = move_line_obj.create(cr, uid, vals_debit, context=context)
                                                        move_line__credit_id = move_line_obj.create(cr, uid, vals_credit, context=context)

        return True


account_voucher()


class account_voucher_line(osv.osv):
    _inherit ='account.voucher.line'
    _columns = {
        'interes_reclasificacion': fields.boolean('Interes de Reclasificacion'),
    }
    
    # def onchange_reconcile(self, cr, uid, ids, reconcile, amount, amount_unreconciled, context=None):
    #     result =  super(account_voucher_line, self).onchange_reconcile(cr, uid, ids, reconcile, amount, amount_unreconciled, context=context)
        # acc_obj = self.pool.get('account.voucher')

        # for rec_line in self.browse(cr, uid, ids, context=context):
        #     print "###########################################################3 IDS", ids
        #     print "###########################################################3 ONCHANGE RECONCILE"
        #     print "###########################################################3 ONCHANGE RECONCILE"
        #     voucher_id = rec_line.voucher_id.id
        #     date_venc = rec_line.move_line_id.date_maturity
        #     print "################################# DATE VENC", date_venc
        # for rec in acc_obj.browse(cr, uid, [voucher_id], context=context):
        #     print "################################################# ACCOUNT VOUCHER", rec.partner_id.name
        #     ### OBTENIENDO Y FORMATEANDO LA FECHA DEL SISTEMA
        #     date_system = time.strftime( DEFAULT_SERVER_DATETIME_FORMAT)
        #     print "###################################################### DATE SYSTEM", date_system
        #     date_format = datetime.strptime(date_system, '%Y-%m-%d %H:%M:%S')
        #     print "###################################################### DATE FORMAT", date_format
        #     ### OBTENIENDO Y VALIDANDO LA FECHA DE VENCIMIENTO DE LA LINEA
        #     date_venc_format = datetime.strptime(date_venc, '%Y-%m-%d')
        #     print "##################################################### FECHA DEL VOUCHER LINE", (date_format - date_venc_format).days
        #     ### DIFERENCIA EN TIMEDELTA DE LA RESTA
        #     # result_delta_days =  date_venc  - date_format
        #     # print "################################################## EL RESULTADO DE LOS DIAS ES:", result_delta_days.days

        #     days = (date_format - date_venc_format).days
        #     if days < 0:
        #         days = 0

        #     month_payment = amount_unreconciled
        #     print "##################################################### RESULTADO DE MONTH PAYMENT", month_payment

        #     customer_fee = (rec.percent*12/365)*days*month_payment
        #     print "################################################### RESULTADO DE CUSTOMER FEE", customer_fee

        #     amount = customer_fee + month_payment
        #     print "##################################################### MONTO TOTAL RESULTADO", amount

        #     ######## ESCRIBIENDO EL RESULTADO DE LOS CALCULOS
        #     if rec.default_interest == True:
        #         rec.write({'days':days,'month_payment': month_payment, 'customer_fee': customer_fee, 'amount': amount})
        #     else:
        #         rec.write({'days':days,'month_payment': month_payment, 'customer_fee': customer_fee})
        # return result

account_voucher_line()

class account_arrear(osv.osv):
    _name = "account.arrear"
    _rec_name = "account_id"
    _columns = {
        'account_id':fields.many2one('account.account','Cuenta de Desajuste', required=True),
        'active': fields.boolean('Activo', required=True),
    }
    _defaults = {
        'active': True,
    }

account_arrear()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
