import networkx as nx
import pygraphviz as pgv
import psycopg2
from psycopg2 import sql

'''
  ' Config structure
	' {
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
		self.cur = db.cursor()
		return self.cur
	
	def __exit__(self, xtype, xvalue, xtraceback):
		self.cur.close()





class db_initialize_error:
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
		self.ui.log('Connecting to database ' + str(cfg.db_name) + ' as ' + str(cfg.db_user) + '@' + str(cfg.db_host) + ':' + str(cfg.db_port))

		self.db = psycopg2.connect(dbname=cfg.db_name, user=cfg.db_user, password=cfg.db_password, host=cfg.db_host, port=cfg.db_port)
		chk = self.table_check()
		if chk == 1:
			if self.ui.prompt_yn('The database looks empty. Initialize tables?'):
				self.setup_tables(force=False)
			else:
				raise db_initialize_error
		elif chk == 2:
			if self.ui.prompt_yn('Some tables are missing. Re-initialize?'):
				if self.ui.prompt_yn('Delete the existing tables?'):
					self.setup_tables(force=True)
				else:
					self.setup_tables(force=False)
			else:
				raise db_initialize_error
		elif chk == 3:
			if self.ui.prompt_yn('Database table name conflict or corruption. Delete and re-initialize?'):
				self.setup_tables(force=True)
			else:
				raise db_initialize_error
	


	def table_check(self, schema):
		'''
		  ' Verify the table structure in the database
			' 
			' Parameters:
			'   schema = dict from social-tables.json, detailing the expected
			'            table schema for the database.
			' 
			' Returns:
			'   0 if everything is normal
			'   1 if the database is empty
			'   2 if some tables are present but others are absent
			'   3 if tables do not follow the expected schema
		'''
		all_tables_present = True
		database_empty = True
		schema_ok = True

		with databse_cursor(self.db) as cur:
			cur.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public';")
			res_raw = cur.fetchall()

		res_fixed = []
		for result in res_raw:
			res_fixed.append(result[0])

		for table in schema:
			if table['name'] in res_fixed:
				database_empty = False
				with database_cursor(self.db) as cur:
					cur.execute("SELECT column_name, data_type from INFORMATION_SCHEMA.COLUMNS where table_name = '" + table['name'] + "';")
					res = cur.fetchall()
				
				if len(res) != len(table['schema']):
					self.ui.log_servere('Schema problem in table check! (in table ' + table['name'] + ': missing column(s))')
					schema_ok = False # missing column(s)

				for column in res:
					match = False
					for col_descriptor in table['schema']:
						if col_descriptor['name'] == column[0]:
							if col_descriptor['type'] == column[1]:
								match = True
								break
							else:
								self.ui.log_severe('Schema problem in table check! (in table ' + table['name'] + ': column ' + col_descriptor['name'] + ' should be type ' + col_descriptor['type'] + ', but actual type is ' + column[1] + ')')
								schema_ok = False # Type mismatch

					if not match:
						self.ui.log_servere('Schema problem in table check! (in table ' + table['name'] + ': unexpected column named ' + column[0] + ' of type ' + column[1] + ' is present in table)')
						schema_ok = False # Unexpected column

			else:
				self.ui.log_warning('Missing table in table check! (table name ' + table['name']
				all_tables_present = False # TODO: left off here
