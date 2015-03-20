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
import time
from datetime import datetime, date

class account_payment_term(osv.osv):
    _name = 'account.payment.term'
    _inherit = 'account.payment.term'
    _columns = {
        'advance_percent': fields.float('Prima/Anticipo (%)', digits_compute=dp.get_precision('Account')),
        'terms': fields.integer('Plazo (Meses)'),
        'annual_interest_rate': fields.float('Tasa Interés Anual (%)', digits_compute= dp.get_precision('Account')),
        'tipo_interes'   : fields.selection([('flat','Cálculo Flat'), ('nivelada','Cuota Nivelada')], 'Tipo de Interés'),
        'advance'        : fields.float('Tasa Interés Anual (%)', method=True, digits_compute= dp.get_precision('Sale Price')),
        'terms'          : fields.integer('Plazo (Meses)', required=True),
        'monthly_amount' : fields.float('Pago Mensual', method=True, digits_compute= dp.get_precision('Sale Price')),
        'intereses'      : fields.float('Intereses', method=True, digits_compute= dp.get_precision('Sale Price')),
        'financiado'     : fields.float('Financiado', method=True, digits_compute= dp.get_precision('Sale Price')),
        'total_financiado': fields.float('Finan. + Inter', method=True, digits_compute= dp.get_precision('Sale Price')),
        'subtotal'       : fields.float('Subtotal', method=True, digits_compute= dp.get_precision('Sale Price')),
        'tax_amount'     : fields.float('Impuestos', method=True, digits_compute= dp.get_precision('Sale Price')),
        'total'          : fields.float('De Contado', method=True, digits_compute= dp.get_precision('Sale Price')),
        }

    def create_payment_term(self, cr, uid, advance_percent, terms, annual_interest_rate, tipo_interes, context=None):
        x_total = 100.0
        x_advance = x_total * advance_percent / 100.0
        x_remaining = x_total - x_advance
        if tipo_interes == 'flat':
            x_interest = x_remaining * annual_interest_rate / 100.0 / 12 * terms
        else:
            x_month = (float(annual_interest_rate / 100.0 /12.0) * x_remaining) / (1.0 - ((1.0 + float(annual_interest_rate / 100 / 12)) ** float(-1.0 * terms)))
            x_interest = (x_month - (x_remaining / terms)) * terms

        x_total_financed = x_remaining + x_interest
        x_gran_total = x_advance + x_total_financed
        
        real_advance_percent = x_advance / x_gran_total
        real_monthly_percent = (1.0 - real_advance_percent) / terms
        
        term_lines = []
        
        for x in range(terms + 1):
            line = (0,0,{
                    'value'        : 'balance' if x == terms else 'procent', 
                    'value_amount' : real_monthly_percent if x > 0 else real_advance_percent,
                    'days'         : 1 + 30 * x,
                    'days2'        : 0,
                    })
            term_lines.append(line)
                    
        term = {
            'name'                 : 'Prima del %s, Plazo: %s meses, Tasa: %s, Tipo Interes: %s' % (advance_percent, terms, annual_interest_rate, tipo_interes) ,
            'advance_percent'      : advance_percent,
            'terms'                : terms,
            'annual_interest_rate' : annual_interest_rate,
            'tipo_interes'         : tipo_interes,
            'active'               : 1,
            'note'                 : 'Prima del %s, Plazo: %s meses, Tasa: %s, Tipo Interes: %s' % (advance_percent, terms, annual_interest_rate, tipo_interes) ,
            'line_ids'             : (x for x in term_lines),
            }

        res = self.create(cr, uid, term)
                
        return res




