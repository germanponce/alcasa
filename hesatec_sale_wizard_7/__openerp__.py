# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 HESATEC (<http://www.hesatecnica.com>).
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

{   
    "name" : "Hesatec - Sale Wizard",
    "version" : "1.0",
    "category" : "Sale",
    'complexity': "Easy",
    "author" : "HESATEC",
    "website": "http://www.hesatecnica.com",
    "depends" : ["sale"],
    "description": """
Modulo que permite abrir un wizard para realziar una simulacion
de venta a plazos.
Genera el plazo de pago en caso de que no exista.
""",
    "demo_xml" : [],
    "init_xml" : [],
    "update_xml" : [
        'product_view.xml',
        'ht_sale_wizard_view.xml',
        ],
    "active": False,
    'application': False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

