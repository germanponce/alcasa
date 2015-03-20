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
from openerp import netsvc
from openerp import pooler
import time
from datetime import datetime, date

# Agregamos manejar una secuencia por cada tienda para controlar viajes 
class sale_order(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"
    
    _columns = {
        'advance'        : fields.float('Tasa Interés Anual (%)', method=True, digits_compute= dp.get_precision('Sale Price')),
        'terms'          : fields.integer('Plazo (Meses)', required=False),
        'monthly_amount' : fields.float('Pago Mensual', method=True, digits_compute= dp.get_precision('Sale Price')),
        'intereses'      : fields.float('Intereses', method=True, digits_compute= dp.get_precision('Sale Price')),
        'financiado'     : fields.float('Financiado', method=True, digits_compute= dp.get_precision('Sale Price')),
        'total_financiado': fields.float('Finan. + Inter', method=True, digits_compute= dp.get_precision('Sale Price')),
        'subtotal'       : fields.float('Subtotal', method=True, digits_compute= dp.get_precision('Sale Price')),
        'tax_amount'     : fields.float('Impuestos', method=True, digits_compute= dp.get_precision('Sale Price')),
        'total'          : fields.float('De Contado', method=True, digits_compute= dp.get_precision('Sale Price')),
        }

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None):
        res = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None)
        invoice = self.pool.get('account.invoice')
        for order in self.browse(cr, uid, ids, context=context):

            invoice_vals_02={}
            invoice_vals_02['advance'] = order.advance
            invoice_vals_02['terms'] = order.terms
            invoice_vals_02['monthly_amount'] = order.monthly_amount
            invoice_vals_02['intereses'] = order.intereses
            invoice_vals_02['financiado'] = order.financiado
            invoice_vals_02['total_financiado'] = order.total_financiado
            invoice_vals_02['subtotal'] = order.subtotal
#            invoice_vals_02['tax_amount'] = order.amount_tax
            invoice_vals_02['tax_amount'] = order.tax_amount
            invoice_vals_02['total'] = order.total
            invoice_vals_02['total_factura'] = order.subtotal + order.tax_amount

            invoice_id = invoice.search(cr, uid, [('origin','=',order.name)], limit=1)

            for factura in invoice.browse(cr, uid, [invoice_id[0]], context=context):
                factura.write(invoice_vals_02)         
        return res
        
sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: