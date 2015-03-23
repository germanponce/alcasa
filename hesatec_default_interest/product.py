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
from datetime import datetime, date


#----------------------------------------------------------
# Products
#----------------------------------------------------------

class product_template(osv.osv):
    _inherit = "product.template"
    _columns = {
        'property_account_reclasif': fields.many2one('account.account', "Reclasificación de Interés", help=" Cuenta usada para reclasificar el interés cuando es efectivamente pagado."),
    }

product_template()


class product_template(osv.osv):
    _inherit ='product.template'
    _name = 'product.template'

    _columns = {

        'interes_moratorio'  : fields.boolean('Interes Moratorio', help="Activa esta casilla para definir un producto como Interes Moratorio para el Desajuste de los Pagos de Clientes"),        
        'readjustment'  : fields.boolean('Readecuacion', help="Activa esta casilla para definir un producto como Readecuacion de los Pagos de Clientes"),        
    }
    

    def _check_only_one_interes_moratorio(self, cr, uid, ids, context=None):
        if self.browse(cr, uid, ids)[0].interes_moratorio:
            prod_obj = self.pool.get('product.template')
            print ids
            recs = prod_obj.search(cr, uid, [('interes_moratorio', '=', 1), ('active', '=', 1), ('id', '!=', ids[0])])
            print recs
            if len(recs) :
                return False
        return True

    def _check_only_one_readjustment(self, cr, uid, ids, context=None):
        if self.browse(cr, uid, ids)[0].readjustment:
            prod_obj = self.pool.get('product.template')
            print ids
            recs = prod_obj.search(cr, uid, [('readjustment', '=', 1), ('active', '=', 1), ('id', '!=', ids[0])])
            print recs
            if len(recs) :
                return False
        return True

            

    _constraints = [
        (_check_only_one_interes_moratorio,
            'Solo puede tener un producto para el manejo automatico de Intereses Moratorios',
            ['interes_moratorio']),(_check_only_one_readjustment,
            'Solo puede tener un producto para el manejo de las Readecuaciones',
            ['readjustment'])
        ]


product_template()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
