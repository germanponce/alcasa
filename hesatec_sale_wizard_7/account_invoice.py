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
import time
from datetime import datetime, date
from openerp.addons.decimal_precision import decimal_precision as dp

# Add special tax calculation for Mexico
class account_invoice(osv.osv):
    _inherit ='account.invoice'


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
        'total_factura'  : fields.float('Iva+Costo', method=True, digits_compute= dp.get_precision('Sale Price')),
    }
    
    _defaults = {
    }

account_invoice()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
