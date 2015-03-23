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
from openerp import netsvc
from openerp import pooler
from openerp.addons.decimal_precision import decimal_precision as dp
import time
from datetime import datetime, date

class product_template(osv.osv):
    _inherit ='product.template'
    _name = 'product.template'

    _columns = {

        'interest_product'  : fields.boolean('Interes Ventas', help="Interes para las ventas a credito. Solo puede existir un producto con esta casilla activa"),        
    }
    

    def _check_only_one_interest_product(self, cr, uid, ids, context=None):
        if self.browse(cr, uid, ids)[0].interest_product:
            prod_obj = self.pool.get('product.template')
            print ids
            recs = prod_obj.search(cr, uid, [('interest_product', '=', 1), ('active', '=', 1), ('id', '!=', ids[0])])
            print recs
            if len(recs) :
                return False
        return True

            

    _constraints = [
        (_check_only_one_interest_product,
            'Solo puede tener un producto para el manejo automatico de Intereses',
            ['interest_product'])
        ]


product_template()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
