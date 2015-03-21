# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 HESATEC - http://www.hesatecnica.com
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@hesatecnica.com)
############################################################################
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
    'name': 'Menu Item para Account Move Line',
    'version': '1',
    "author" : "HESATEC",
    "category" : "HESATEC",
    'description': """
       Este modulo Crea un menu en Contabilidad para poder verificar los account_move_line en una Vista
    """,
    "website" : "http://www.hesatecnica.com/",
    "license" : "AGPL-3",
    "depends" : ["account","sale","purchase","account_voucher","account_accountant"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'account_move_line_menu.xml',
                    ],
    "installable" : True,
    "active" : False,
}
