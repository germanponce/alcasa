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
import dateutil
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from openerp import netsvc


class sale_order_simulation_(osv.osv):

    """ Sale Order Simulation """

    _name = 'sale.order.simulation_'
    _description = 'Sale Order Simulation_'


    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            res[rec.id] = {
                'advance'        : 0.0,
                'monthly_amount' : 0.0,
                'financiado'     : 0.0,
                'intereses'      : 0.0,
                'subtotal'       : 0.0,
                'tax_amount'     : 0.0,
                'total'          : 0.0,
                'gran_total'     : 0.0,
                'total_financiado': 0.0,
            }
            x_adv = x_finan = x_intereses = x_total = x_subtotal = x_tax_amount = x_month = 0.0
            for line in rec.order_line:
                x_subtotal   += line.subtotal
                x_tax_amount += line.tax_amount
                x_total      += line.total

            x_adv = x_total * rec.advance_percent / 100.0
            x_finan = x_total - x_adv
            if rec.tipo_interes == 'flat':
                x_intereses = x_finan * (rec.annual_interest_rate / 100.0 / 12.0) * rec.terms
                x_month = (x_finan  + x_intereses) / rec.terms 
            else:
                x_month = (float(rec.annual_interest_rate / 100.0 /12.0) * x_finan) / (1.0 - ((1.0 + float(rec.annual_interest_rate / 100 / 12)) ** float(-1.0 * rec.terms)))
                x_intereses = (x_month - (x_finan / rec.terms)) * rec.terms
            res[rec.id] =  {
                'advance'        : x_adv,
                'monthly_amount' : x_month,
                'financiado'     : x_finan,
                'intereses'      : x_intereses,
                'subtotal'       : x_subtotal,
                'tax_amount'     : x_tax_amount,
                'total'          : x_total,
                'gran_total'     : x_adv + x_finan + x_intereses,
                'total_financiado': x_finan + x_intereses
                }
        return res


    _columns = {
        'name'           : fields.char('Folio', size=64, readonly=True),
        'partner_id'     : fields.many2one('res.partner', 'Cliente', required=True),
        'sale_order_id'  : fields.many2one('sale.order', 'Pedido de Venta', required=False),
        'pricelist_id'   : fields.many2one('product.pricelist', 'Lista de Precios', required=True),
        'date'           : fields.date('Fecha', required=True),
        'order_line'     : fields.one2many('sale.order.simulation.line_', 'order_id', 'Líneas de Venta'),
        'detail_line'    : fields.one2many('sale.order.simulation.detail_', 'order_id', 'Tabla de Amortización'),
        'annual_interest_rate': fields.float('Tasa Interés Anual (%)', required=True, digits_compute= dp.get_precision('Account')),
        'advance_percent': fields.float('Prima (%)', required=True, digits_compute= dp.get_precision('Account')),
        'advance'        : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Prima',  type='float', store=False, multi=True),
        'terms'          : fields.integer('Plazo (Meses)', required=True),
        'monthly_amount' : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Pago Mensual',  type='float', store=False, multi=True),
        'intereses'      : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Intereses',  type='float', store=False, multi=True),
        'financiado'     : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Financiado',  type='float', store=False, multi=True),
        'total_financiado': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Finan. + Inter',  type='float', store=False, multi=True),
        'subtotal'       : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Subtotal',  type='float', store=False, multi=True),
        'tax_amount'     : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Impuestos', type='float', store=False, multi=True),
        'total'          : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='De Contado',     type='float', store=False, multi=True),
        'gran_total'          : fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Gran Total',     type='float', store=False, multi=True),
        'salesman'       : fields.many2one('res.users', 'Vendedor', required=True),
        'tipo_interes'   : fields.selection([('flat','Cálculo Flat'), ('nivelada','Cuota Nivelada')], 'Tipo de Interés', required=True),
        }

    _defaults = {
        'date'                 : lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        'terms'                : 12,
        'annual_interest_rate' : 40.0,
        'advance_percent'      : 30.0,
        'salesman'             : lambda obj, cr, uid, context: uid,
        'tipo_interes'         : lambda *a: 'flat',
        }


    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = {} if not partner_id else {'value': { 'pricelist_id' : self.pool.get('res.partner').browse(cr, uid, [partner_id])[0].property_product_pricelist.id,} } 
        return res 

    def action_calculate(self, cr, uid, ids, context=None):
        return True

    def action_create_sale_order(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids):
            if rec.sale_order_id and rec.sale_order_id.id and rec.sale_order_id.state != 'cancel':
                raise osv.except_osv(_('Error!'),
                                     _('Ya existe un Pedido de Venta asociado a esta simulación de Venta. !\n'
                                       'Por favor revise el Pedido de Venta %s ') % (rec.sale_order_id.name))
            
            order_lines = []
            for line in rec.order_line:
                xline = (0 ,0,{
                        'product_id'      : line.product_id.id,
                        'product_uom_qty' : line.product_uom_qty,
                        'product_uom'     : line.product_uom.id,
                        'product_uos_qty' : line.product_uom_qty,
                        'product_uos'     : line.product_uom.id,
                        'price_unit'      : line.price_unit,
                        'name'            : line.product_id.name,
                        'type'            : 'make_to_stock',
                        'tax_id'          : [(6, 0, [x.id for x in line.product_id.taxes_id])],
                        })
                order_lines.append(xline)
            
            prod_obj = self.pool.get('product.product')
            prod_id = prod_obj.search(cr, uid, [('interest_product', '=', 1), ('active', '=', 1)])
            if prod_id:
                prod = prod_obj.browse(cr, uid, prod_id)[0]
            else:
                raise osv.except_osv(_('Error!'),
                                     _('No existe ningún producto marcado como Interes en Venta'))


            tax_factor = 0.00
            for taxes in prod.taxes_id:
                tax_factor = (tax_factor + taxes.amount) if taxes.amount <> 0.0 else tax_factor

            xline = (0 ,0,{
                    'product_id'      : prod.id,
                    'product_uom_qty' : 1.0,
                    'product_uom'     : prod.uom_id.id,
                    'product_uos_qty' : 1.0,
                    'product_uos'     : prod.uom_id.id,
                    'price_unit'      : rec.intereses / (1.0 + tax_factor),
                    'name'            : prod.name,
                    'type'            : 'make_to_stock',
                    'tax_id'          : [(6, 0, [x.id for x in prod.taxes_id])],
                    })
            order_lines.append(xline)

            terms_obj = self.pool.get('account.payment.term')
            res_id = terms_obj.search(cr, uid, [('terms' , '=', rec.terms),
                                                ('annual_interest_rate', '=', rec.annual_interest_rate),
                                                ('advance_percent', '=', rec.advance_percent),
                                                ('tipo_interes', '=', rec.tipo_interes)])
            term_id = res_id[0] if (res_id and res_id[0]) else terms_obj.create_payment_term(cr, uid, rec.advance_percent, rec.terms, rec.annual_interest_rate, rec.tipo_interes)

            sale_order = {'partner_id'          : rec.partner_id.id,
                          'partner_invoice_id'  : rec.partner_id.id,
                          'partner_shipping_id' : rec.partner_id.id,
                          'date_order'          : rec.date,
                          'client_order_ref'    : rec.name,
                          'user_id'             : rec.salesman.id,
                          'origin'              : rec.name,
                          'payment_term'        : term_id,
                          'order_line'          : [x for x in order_lines],
                          'pricelist_id'        : rec.pricelist_id.id,
                          'order_policy'        : 'manual',
                          'advance'        : rec.advance,
                          'terms'          : rec.terms,
                          'monthly_amount' : rec.monthly_amount,
                          'intereses'      : rec.intereses,
                          'financiado'     : rec.financiado,
                          'total_financiado': rec.total_financiado,
                          'subtotal'       : rec.subtotal,
                          'tax_amount'     : rec.tax_amount,
                          'total'          : rec.total,

                          }

            sale_order_id = self.pool.get('sale.order').create(cr,uid, sale_order)
            self.write(cr, uid, ids, { 'sale_order_id' : sale_order_id })


            return {
                'domain': "[('id','in', ["+','.join(map(str,[sale_order_id]))+"])]",
                'name': _('Pedido de Venta'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'view_id': False,
                'type': 'ir.actions.act_window'
                }



    def create(self, cr, uid, vals, context=None):
        print "Si entra aqui..."
        seq_obj = self.pool.get('ir.sequence')
        seq_id = seq_obj.search(cr, uid, [('name', '=', 'SIMULA')])
        if seq_id:
            seq_number = seq_obj.get_id(cr, uid, seq_id)
            vals['name'] = seq_number
        res = super(sale_order_simulation_, self).create(cr, uid, vals, context=context)
        self.calculate_amortization(cr, uid, [res])
        return res

    def write(self, cr, uid, ids, vals, context=None):
        super(sale_order_simulation_, self).write(cr, uid, ids, vals, context=context)
        self.calculate_amortization(cr, uid, ids)
        return True

    def calculate_amortization(self, cr, uid, ids, context=None):
        cr.execute("delete from sale_order_simulation_detail_ where order_id in %s",(tuple(ids),))
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


    def action_print_simulation(self, cr, uid, ids, context=None):            
        value = {
            'type'        : 'ir.actions.report.xml',
            'report_name' : 'report.sale_order_simulation_',
            'datas'       : 
            {
                'model'      : 'sale.order.simulation_',
                'ids'        : ids,
                'report_type': 'pdf',
                },
            'nodestroy'   : True
            } 
        
        return value



class sale_order_simulation_line_(osv.osv):

    """ Sale Order Simulation Line"""

    _name = 'sale.order.simulation.line_'
    _description = 'Sale Order Simulation Line _'
    _rec_name = 'product_id'
    _columns = {
        'order_id'       : fields.many2one('sale.order.simulation_', 'Order Reference', required=True),
        'sequence'       : fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'product_id'     : fields.many2one('product.product', 'Producto', domain=[('sale_ok', '=', True)], required=True),
        'product_uom_qty': fields.float('Cantidad', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom'    : fields.many2one('product.uom', 'Unidad de Medida', required=True),
        'price_unit'     : fields.float('Precio Unit.', required=True, digits_compute= dp.get_precision('Product Price')),
        'subtotal'       : fields.float('Subtotal', required=True, digits_compute= dp.get_precision('Product Price')),
        'tax_amount'     : fields.float('Impuestos', required=True, digits_compute= dp.get_precision('Product Price')),
        'total'          : fields.float('Total', required=True, digits_compute= dp.get_precision('Product Price')),
        'xsubtotal'      : fields.float('Subtotal', digits_compute= dp.get_precision('Product Price')),
        'xtax_amount'    : fields.float('Impuestos', digits_compute= dp.get_precision('Product Price')),
        'xtotal'         : fields.float('Total', digits_compute= dp.get_precision('Product Price')),
        'partner_id'     : fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', string='Cliente'),
        'pricelist_id'   : fields.many2one('product.pricelist', 'Lista de Precios'),
        }

    _defaults ={
        'xsubtotal'       : 0.0,
        'xtax_amount'     : 0.0,
        'xtotal'          : 0.0,
        'product_uom_qty' : 1.0,
        } 


    def on_change_product_id(self, cr, uid, ids, product_id, product_uom_qty, product_uom, partner_id, pricelist_id, context=None):
        result = {}
        if not product_id:
            return {}
        for product in self.pool.get('product.product').browse(cr, uid, [product_id]):
            result.update({'product_uom' : product.uom_id.id})
            # get unit price
            date = datetime.now().strftime('%Y-%m-%d')

            if not pricelist_id:
                raise osv.except_osv(_('Error!'),
                                     _('Debe seleccionar primero un cliente en el formulario !\n'
                                       'Por favor seleccione un cliente antes de seleccionar algún producto.'))
                
            else:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
                                                                     product_id, product_uom_qty or 1.0, partner_id, {
                        'uom': product_uom or False,
                        'date': date,
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


class sale_order_simulation_detail_(osv.osv):

    """ Sale Order Simulation Line"""

    _name = 'sale.order.simulation.detail_'
    _description = 'Sale Order Simulation Payments Detail _'

    _columns = {
        'order_id'       : fields.many2one('sale.order.simulation_', 'Order Reference', required=True),
        'name'           : fields.text('Description'),
        'date'           : fields.date('Fecha'),        
        'monthly_amount' : fields.float('Pago Mensual', required=True, digits_compute= dp.get_precision('Account')),
        'initial_balance': fields.float('Saldo Inicial', required=True, digits_compute= dp.get_precision('Account')),
        'ending_balance' : fields.float('Saldo Final', required=True, digits_compute= dp.get_precision('Account')),
        'sequence'       : fields.integer('Sequence'),
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
