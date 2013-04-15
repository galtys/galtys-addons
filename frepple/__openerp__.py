# -*- encoding: utf-8 -*-
#
# Copyright (C) 2010-2012 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# file : $URL: http://svn.code.sf.net/p/frepple/code/trunk/contrib/openerp/frepple/__terp__.py $
# revision : $LastChangedRevision: 1713 $  $LastChangedBy: jdetaeye $
# date : $LastChangedDate: 2012-07-18 11:46:01 +0200 (Wed, 18 Jul 2012) $

{
    "name" : "Advanced Planning and Scheduling Module",
    "version" : "1.0",
    "author" : "frePPLe",
    "website" : "http://www.frepple.com",
    "category" : "Generic Modules/Production",
    "depends" : ["mrp"],
    "description": """
    This module performs constrained planning scheduling with frePPLe.
    """,
    "init_xml": [],
    "update_xml": [
      'frepple_data.xml',
      'frepple_view.xml',
      ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
