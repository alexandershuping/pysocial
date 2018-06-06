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
import psycopg2
from psycopg2 import sql
import json

from social_ui import ui

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

class database_cursor:
	'''
	  ' Context manager class for psycopg2 cursor objects.
		' Instead of calling db.cursor() and then cursor.close(), just use
		' 
		'    with database_cursor(db) as cursor:
		'      do_things_with(cursor)
		'     
		'    do_other_things() # Cursor object is closed before this line
	'''
	def __init__(self, db):
		self.db = db
	
	def __enter__(self):
		self.cur = self.db.cursor()
		return self.cur
	
	def __exit__(self, xtype, xvalue, xtraceback):
		self.cur.close()



class db_initialize_error(BaseException):
	'''
	  ' Raised when the database can't be initialized properly
	'''



class db_connect:

	def __init__(self, ui, cfg, tables):
		''' Open database connection 
		  ' 
			' Parameters:
			'   ui = UI object for user-interface
			'   cfg = configuration object
			'   tables = expected schema dict loaded from social-tables.json
		'''
		self.ui = ui
		self.schema = tables
		if 'table_prefix' in cfg:
			self.table_prefix = cfg['table_prefix']
		else:
			self.table_prefix = ""

		self.ui.log('Connecting to database ' + str(cfg['db_name']) + ' as ' + str(cfg['db_user']) + '@' + str(cfg['db_host']) + ':' + str(cfg['db_port']))

		self.db = psycopg2.connect(dbname=cfg['db_name'], user=cfg['db_user'], password=cfg['db_password'], host=cfg['db_host'], port=cfg['db_port'])
		if 'table_prefix' in cfg:
			chk = self.table_check(schema=tables, table_prefix=cfg['table_prefix'])
		else:
			chk = self.table_check(schema=tables)
		if chk == 1:
			if self.ui.prompt_yn('The database looks empty. Initialize tables?'):
				self.setup_tables(force=False)
			else:
				self.ui.log_severe('Database was empty and user rejected initialization request!')
				raise db_initialize_error('Database was empty and user rejected re-initialization request!')
		elif chk == 2:
			if self.ui.prompt_yn('Some tables are missing. Re-initialize?'):
				if self.ui.prompt_yn('Delete the existing tables?'):
					self.setup_tables(force=True)
				else:
					self.setup_tables(force=False)
			else:
				self.ui.log_severe('Database was incomplete and user rejected re-initialization request!')
				raise db_initialize_error('Database was incomplete and user rejected re-initialization request!')
		elif chk == 3:
			if self.ui.prompt_yn('Database table name conflict or corruption. Delete and re-initialize?'):
				self.setup_tables(force=True)
			else:
				self.ui.log_severe('Database was corrupt and user rejected re-initialization request!')
				raise db_initialize_error('Database was corrupt and user rejected re-initialization request!')
	


	def table_check(self, schema=None, table_prefix=None):
		'''
		  ' Verify the table structure in the database
			' 
			' Parameters:
			'   schema = dict from social-tables.json, detailing the expected
			'            table schema for the database.
			' 
			'   table_prefix = if present, prepend this to table names as
			'                  specified in the schema.
			' 
			' Returns:
			'   0 if everything is normal
			'   1 if the database is empty
			'   2 if some tables are present but others are absent
			'   3 if tables do not follow the expected schema
		'''
		if not schema:
			schema = self.schema

		if not table_prefix:
			table_prefix = self.table_prefix

		all_tables_present = True
		database_empty = True
		schema_ok = True

		with database_cursor(self.db) as cur:
			cur.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public';")
			res_raw = cur.fetchall()

		res_fixed = []
		for result in res_raw:
			res_fixed.append(result[0])

		for table in schema:
			tname = table_prefix + table['name']
			if tname in res_fixed:
				database_empty = False
				with database_cursor(self.db) as cur:
					cur.execute("SELECT column_name, data_type from INFORMATION_SCHEMA.COLUMNS where table_name = '" + tname+ "';")
					res = cur.fetchall()
				
				if len(res) != len(table['schema']):
					self.ui.log_severe('Schema problem in table check! (in table ' + tname + ': missing column(s))')
					schema_ok = False # missing column(s)

				for column in res:
					match = False
					for col_descriptor in table['schema']:
						if col_descriptor['name'] == column[0]:
							if col_descriptor['type'].lower() == column[1].lower():
								match = True
								break
							else:
								self.ui.log_severe('Schema problem in table check! (in table ' + tname + ': column ' + col_descriptor['name'] + ' should be type ' + col_descriptor['type'] + ', but actual type is ' + column[1] + ')')
								schema_ok = False # Type mismatch

					if not match:
						self.ui.log_severe('Schema problem in table check! (in table ' + tname + ': unexpected column named ' + column[0] + ' of type ' + column[1] + ' is present in table)')
						schema_ok = False # Unexpected column

			else:
				self.ui.log_warning('Missing table in table check! (table name ' + tname + ')')
				all_tables_present = False # missing table

		if not schema_ok:
			return 3
		elif database_empty:
			return 1
		elif not all_tables_present:
			return 2
		else:
			return 0
	
	def setup_tables(self, force=False):
		'''
		  ' Sets up the proper tables in the postgresql database
			' 
			' Parameters:
			'   force = whether to delete all tables and re-initialize. This
			'           option is DANGEROUS, and should not be used unless
			'           necessary
		'''

		if force: # delete all present tables
			with database_cursor(self.db) as cur:
				cur.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public';")
				table_list_unfixed = cur.fetchall()

				for table in table_list_unfixed:
					tname = table[0]
					cmd = 'DROP TABLE ' + tname + ';'
					self.ui.log_warning('Removing table ' + tname)
					cur.execute(cmd)

				self.db.commit()

		with database_cursor(self.db) as cur:
			cur.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public';")
			table_list_unfixed = cur.fetchall()

			table_list = []

			for table in table_list_unfixed:
				table_list.append(table[0])
				self.ui.log_debug('Found table ' + str(table[0]))

			for table in self.schema:
				tname = self.table_prefix + table['name']
				if tname in table_list:
					continue # ignore tables which already exist
				else:
					cmd = 'CREATE TABLE ' + tname + ' ('
					for index, column in enumerate(table['schema']):
						if index != 0:
							cmd = cmd + ', '
						cmd = cmd + column['name'] + ' ' + column['type']
						if 'primary' in column: # columns with primary:true are PRIMARY KEY columns
							if column['primary']:
								cmd = cmd + ' PRIMARY KEY'
					
					cmd = cmd + ');'
					self.ui.log('Creating table ' + tname + ' with command ' + cmd)
					cur.execute(cmd) # create table
			self.db.commit()
