'''

Copyright 2018 Alexander Shuping

This file is part of Pysocial.

Pysocial is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pysocial is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pysocial.  If not, see <http://www.gnu.org/licenses/>.

'''

import networkx as nx
import pygraphviz as pgv
import json


from social_db import db_connect, database_cursor
from social_ui import ui, basic_console_ui

'''
  ' Config structure
	' {
	'   db_name = name of database to connect to
	'   db_user = username for database connection
	'   db_password = password for above
	'   db_host = host to connect to for postgresql database
	'   db_port = port for above
	'   
	'   table_prefix = text to prepend to tables (for shared databases)
	' }
'''

def test_fun():
	with open('config.json') as config:
		c = json.load(config)
	
	with open('social-tables.json') as tables:
		t = json.load(tables)

	u = basic_console_ui()

	return [u,c,t]
