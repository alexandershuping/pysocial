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
import random
import sys
from psycopg2 import sql


from social_db import db_connect, database_cursor, db_initialize_error
from social_ui import ui, none_ui, basic_console_ui

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

class configurer:
	'''
	  ' Manages a configuration file, allowing program elements to
		' retrieve and change config values.
	'''

	def __init__(self, config_file_path='social-config.json'):
		'''
		  ' Loads configuration information from a JSON file
			'
			' Parameters:
			'   config_file_path = path to configuration file. If not
			'     provided, the program defaults to 'social-config.json'
			' 
			' Returns:
			'   0 = success
			'   1 = could not find / load config file
			'   2 = error in JSON decoding\
			'   3 = permission error
		'''
		self.default_config_path = config_file_path

		with open(config_file_path) as config_file:
			self.config = json.load(config_file)
	

	def modify_config_key(self, key_to_modify, new_value, strict=True):
		'''
		  ' Modifies a key within the configuration structure.
			' 
			' If 'strict' is not manually set to False, this function will
			' refuse to add new keys to the database.
			' 
			' Parameters:
			'   key_to_modify = config file key which will be updated
			'   
			'   new_value = new value which key_to_modify will take
			' 
			'   strict = if true, this function will refuse to add a new key
			'     i.e. it will *only* modify existing keys. Default: True
			'
			' Returns:
			'	  0 = successfully updated existing key
			'   1 = key_to_modify is not an existing key and strict=True
			'  -1 = successfully added a new key (strict=False)
		'''
		added_new = False
		if not key_to_modify in self.config.keys():
			if strict:
				return 1
			else:
				added_new = True

		self.config[key_to_modify] = new_value
		self.update_file(self.default_config_path)
		
		if added_new:
			return -1
		else:
			return 0
	

	def retrieve(self, key_to_retrieve):
		'''
		  ' Retrieves a key from the config structure.
			' 
			' Parameters:
			'   key_to_retrieve = configuration key to retrieve
			' 
			' Returns: the value associated with the key, or None if the key
			'   is not present.
		'''
		if key_to_retrieve in self.config.keys():
			return self.config[key_to_retrieve]
		else:
			return None

	def update_file(self, config_file_path='social-config.json'):
		'''
		  ' Saves configuration information to a JSON file
			' 
			' Parameters:
			'   config_file_path = path to save configuration to. Defaults
			'     to 'social-config.json'
			' 
			' Returns:
			'   0 = success
			'   3 = permission error
		'''
		try:
			with open(config_file_path, 'w') as config_file:
				json.dump(self.config, config_file)
		except PermissionError:
			return 3


class name_conflict_error(BaseException):
	pass


class database_io:
	
	def __init__(self, configurer_object, ui=None):
		self.config = configurer_object
		self.file_id = None
		self.file_name = None
		self.database = None
		if ui:
			self.ui = ui
		else:
			self.ui = none_ui()
		
	def hook_ui(self, ui_to_hook):
		if ui_to_hook:
			self.ui = ui_to_hook
			return 0
		else:
			return 1
	
	def is_connected(self):
		if self.database:
			return True
		else:
			return False
	
	def begin(self):
		self.ui.write('Connecting to database...')
		self.ui.log('Connecting to database ' + str(self.config.retrieve('db_name')) + ' at ' + str(self.config.retrieve('db_host')) + ':' + str(self.config.retrieve('db_port')) + ' as user ' + str(self.config.retrieve('db_user')))
		self.ui.log('Loading schema from social-tables.json...')
		try:
			with open('social-tables.json') as tables:
				self.schema = json.load(tables)
		except FileNotFoundError:
			self.ui.log_error('Could not find social-tables.json! Aborting connection!')
			return 1
		except json.decoder.JSONDecodeError:
			self.ui.log_error('Could not parse social-tables.json! Aborting connection!')
			return 2
		except PermissionError:
			self.ui.log_error('Could not open social-tables.json due to permission error! Aborting connection!')
			return 3
		
		self.ui.log('Schema load successful. Connecting...')
		try:
			self.database = db_connect(self.ui, self.config.config, self.schema)
		except db_initialize_error:
			self.ui.log_error('Failed to connect to database.')
			return 4
		self.ui.write('Connected.')
		return 0
	
	def __set_file(self, file_name, file_id):
		self.file_name = file_name
		self.file_id = file_id
	

	def create_file(self, file_name, file_id=None):
		if not file_id:
			file_id = random.randint(-1*sys.maxsize, sys.maxsize)
			self.ui.log_debug('Generated id ' + str(file_id))

		cmd = sql.SQL('INSERT INTO {} (name, id) VALUES (%s,%s);').format(sql.Identifier(self.database.tablify('files')))
		with database_cursor(self.database) as cur:
			cur.execute(cmd, (str(file_name), file_id))
			self.database.commit()

		return file_id

	def open_file_by_name(self, file_name, create=True):
		with database_cursor(self.database) as cur:
			self.ui.log('Searching for file named "' + str(file_name) + '"')
			cmd = sql.SQL('SELECT name, id FROM {} WHERE name = %s;').format(sql.Identifier(self.database.tablify('files')))
			cur.execute(cmd, (str(file_name),))
			res = cur.fetchall()
			if res:
				if len(res) == 1:
					self.__set_file(res[0][0], res[0][1])
					self.ui.log('File found with id ' + str(res[0][1]))
					return 0
				else: # len(res) > 1
					warning_str = 'Name conflict: files with ids'
					for r in res:
						warning_str = warning_str + ' ' + str(r[1])
					
					warning_str = warning_str + ' have the same name "' + file_name + '"'
					self.ui.log_warning(warning_str)
					return 2
			else:
				self.ui.log_warning('File not found with name "' + str(file_name) + '"')
				if create:
					file_id = self.create_file(file_name)
					self.ui.log_warning('Created file with id ' + str(file_id))
					self.__set_file(file_name, file_id)
				return 1
	
	def open_file_by_id(self, file_id):
		with database_cursor(self.database) as cur:
			self.ui.log('Searching for file with id ' + str(file_id))
			cmd = sql.SQL('SELECT name, id FROM {} WHERE id = %s;').format(sql.Identifier(self.database.tablify('files')))
			cur.execute(cmd, (str(file_id),))
			res = cur.fetchall()
			if res:
				if len(res) == 1:
					self.__set_file(res[0][0], res[0][1])
					self.ui.log('File found with name "' + str(res[0][0]) + '"')
					return 0
				else:
					self.ui.log_warning('File not found with id ' + str(file_id))
					return 1
			else:
				self.ui.log_warning('File not found with id ' + str(file_id))
				return 1
				
	
	def current_file(self):
		if self.file_name and self.file_id:
			return self.file_name
		else:
			return None
	
	def add_node(self, node_name):
		if not self.current_file():
			self.ui.log_warning('Attempted to add node, but no file is open')
			return 1

		node_id = random.randint(-1*sys.maxsize, sys.maxsize)
		with database_cursor(self.database) as cur:
			self.ui.log('Adding node named "' + node_name + '" as id ' + str(node_id) + ' with parent file id ' + str(self.file_id))
			cmd = sql.SQL('INSERT INTO {}(name, id, parent_file_id) VALUES (%s,%s,%s);').format(sql.Identifier(self.database.tablify('nodes')))
			cur.execute(cmd, (str(node_name), node_id, self.file_id))
			self.database.commit()
	
	def lookup_node_by_name(self, node_name, node_discrim=None):
		nodes = []
		with database_cursor(self.database) as cur:
			appendage = ''
			if self.current_file():
				appendage = ' AND parent_file_id=%s'
			cmd = sql.SQL('SELECT name, id FROM {} WHERE name=%s' + appendage + ';').format(sql.Identifier(self.database.tablify('nodes')))
			if self.current_file():
				cur.execute(cmd, (str(node_name), str(self.file_id)))
			else:
				cur.execute(cmd, (str(node_name),))

			nodes = cur.fetchall()

		if not nodes:
			nodes = []

		if len(nodes) == 1:
			return nodes[0]
		elif len(nodes) == 0:
			self.ui.log_warning('No matches found for node name "' + str(node_name) + '"')
			return None
		else:
			if not node_discrim:
				self.ui.log_warning('Multiple matches for node name " ' + str(node_name) + '", but no discrim provided.')
				raise name_conflict_error
			else:
				self.ui.log_debug('Attempting to resolve name conflict by name discriminator.')
				found = None       # Check all possibilities for discrim
				for node in nodes: # conflicts, just in case
					if abs(node[1]) % 100000 == node_discrim:
						if found: # Discrim conflict! My paranoia is justified!
							self.ui.log_warning('Multiple nodes have the same name "' + str(node_name) + '" and the same discrim ' + str(node_discrim) + '!')
							raise name_conflict_error
						else:
							found = node
				
				if found:
					self.ui.log_debug('Conflict successfully resolved by name discriminator.')
					return found
				else:
					self.ui.log_warning('Discriminator did not match any nodes.')
					return None
					

	def add_connection_by_id(self, origin_id, destination_id):
		if not self.current_file():
			self.log_error('Cannot add connections when no file is open.')

		with database_cursor(self.database) as cur:
			connection_id = random.randint(-1*sys.maxsize, sys.maxsize)
			self.ui.log('Connecting ' + str(origin_id) + ' to ' + str(destination_id) + ' with connection id ' + str(connection_id))
			cmd = sql.SQL('INSERT INTO {} (first_id, second_id, connection_id, parent_file_id) VALUES (%s,%s,%s,%s);').format(sql.Identifier(self.database.tablify('connections')))

			cur.execute(cmd, (origin_id,destination_id,connection_id,self.file_id))
			self.database.commit()

		return 0


	
	def add_connection_by_name(self, origin_name, destination_name, origin_discrim=None, destination_discrim=None):
		if not self.current_file():
			self.log_error('Cannot add connections when no file is open.')

		if origin_discrim:
			self.ui.log('Looking up "' + str(origin_name) + '":' + str(origin_discrim) + ' by name and discrim')
		else:
			self.ui.log('Looking up "' + str(origin_name) + '" by name')

		origin = self.lookup_node_by_name(origin_name, origin_discrim)

		if destination_discrim:
			self.ui.log('Looking up "' + str(destination_name) + '":' + str(destination_discrim) + ' by name and discrim')
		else:
			self.ui.log('Looking up "' + str(destination_name) + '" by name')

		destination = self.lookup_node_by_name(destination_name, destination_discrim)

		if not (origin and destination):
			self.ui.log_error('Could not identify nodes to connect.')
			return 1

		with database_cursor(self.database) as cur:
			cmd = sql.SQL('SELECT connection_id FROM {} WHERE (first_id=%s AND second_id=%s) OR (first_id=%s AND second_id=%s);').format(sql.Identifier(self.database.tablify('connections')))
			cur.execute(cmd, (origin[1],destination[1],destination[1],origin[1]))

			res = cur.fetchall()
			if res:
				self.ui.log_warning('Connection between "' + str(origin_name) + '" and "' + str(destination_name) + '" already exists.')
				return 2

		self.add_connection_by_id(origin[1], destination[1])
		return 0


	
	def list_nodes(self):
		file_filter = None
		if self.current_file():
			file_filter = self.file_id
		else:
			self.ui.log('Listing all nodes')
		with database_cursor(self.database) as cur:
			cmd = ''
			appendage = ''
			if file_filter:
				appendage = ' WHERE parent_file_id=%s'
			cmd = sql.SQL('SELECT name, id FROM {}' + appendage + ';').format(sql.Identifier(self.database.tablify('nodes')))

			if file_filter:
				cur.execute(cmd, (self.file_id,))
			else:
				cur.execute(cmd)

			return cur.fetchall()


	def list_connections(self):
		file_filter = None
		if self.current_file():
			file_filter = self.file_id
		else:
			self.ui.log('Listing all connections')
		with database_cursor(self.database) as cur:
			cmd = ''
			appendage = ''
			if file_filter:
				appendage = ' WHERE parent_file_id=%s'
			cmd = sql.SQL('SELECT first_id, second_id, connection_id FROM {}' + appendage + ';').format(sql.Identifier(self.database.tablify('connections')))

			if file_filter:
				cur.execute(cmd, (self.file_id,))
			else:
				cur.execute(cmd)

			return cur.fetchall()
	

	def list_files(self):
		cmd = sql.SQL('SELECT name, id FROM {};').format(sql.Identifier(self.database.tablify('files')))
		with database_cursor(self.database) as cur:
			cur.execute(cmd)
			return cur.fetchall()


