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

import json


class polymorphism_error(BaseException):
	'''
	  ' Raised when somebody tries to use a base class
	'''


class ui:
	'''
	  ' Base class for polymorphism. DO NOT initialize it - if you need a
		' UI that does nothing, you want none_ui, not this. If you need a
		' console UI, you want basic_console_ui, not this. This will angrily
		' throw exceptions at you if you try to do anything with it.
	'''
	def __init__(self):
		pass
	
	def begin(self):
		raise polymorphism_error('Cannot call a method from an abstract class!')
	
	def loop(self):
		raise polymorphism_error('Cannot call a method from an abstract class!')
	
	def write(self, message):
		raise polymorphism_error('Cannot call a method from an abstract class!')
	
	def log(self, message, level=5):
		raise polymorphism_error('Cannot call a method from an abstract class!')

	def log_debug(self, message):
		raise polymorphism_error('Cannot call a method from an abstract class!')

	def log_warning(self, message):
		raise polymorphism_error('Cannot call a method from an abstract class!')

	def log_error(self, message):
		raise polymorphism_error('Cannot call a method from an abstract class!')

	def log_severe(self, message):
		raise polymorphism_error('Cannot call a method from an abstract class!')

	def prompt_yn(self, prompt_text, default_resp=False):
		raise polymorphism_error('Cannot call a method from an abstract class!')


class none_ui(ui):
	'''
	  ' Convenience class to make logging functions easier. All logging
		' requests do nothing, and prompt_yn always returns the default.
	'''
	def __init__(self):
		pass
	
	def begin(self):
		pass
	
	def loop(self):
		pass
	
	def write(self, message):
		pass
	
	def log(self, message, level=5):
		pass

	def log_debug(self, message):
		pass
	
	def log_warning(self, message):
		pass
	
	def log_error(self, message):
		pass
	
	def log_severe(self, message):
		pass
	
	def log_severe(self, message):
		pass
	
	def prompt_yn(self, prompt_text, default_resp=False):
		return default_resp


class basic_console_ui(ui):

	def __init__(self, config, db_io, rend):
		with open('social-help.json') as hmenu:
			self.help_dict = json.load(hmenu)
			self.config = config
			self.db = db_io
			self.rend = rend

		self.command_lut = {
			'exit':self.cmd_exit,
			'x':self.cmd_exit,
			'help':self.cmd_help,
			'?':self.cmd_help,
			'h':self.cmd_help,
			'add':self.cmd_add,
			'a':self.cmd_add,
			'connect':self.cmd_connect,
			'cc':self.cmd_connect,
			'open':self.cmd_open,
			'o':self.cmd_open,
			'listnodes':self.cmd_list_nodes,
			'ln':self.cmd_list_nodes,
			'listconnections':self.cmd_list_connections,
			'lc':self.cmd_list_connections,
			'listfiles':self.cmd_list_files,
			'lf':self.cmd_list_files,
			'render':self.cmd_render,
			'r':self.cmd_render
			# TODO: add new commands here. The command name goes before the :,
			# and the name of the function to call goes after it.
		}
		self.keep_going = True

	def begin(self):
		self.log('Hooking and starting database connection.')
		self.db.hook_ui(self)
		rcode = self.db.begin()
		if rcode > 0:
			self.log_severe('FAILED TO CONNECT TO DATABASE! PROGRAM CANNOT CONTINUE!')
			return 1

		self.rend.hook_ui(self)

		print('\n\n\nPysocial Copyright (C) 2018 Alexander Shuping')
		print('This program comes with ABSOLUTELY NO WARRANTY; for details type `help warranty`.')
		print('This is free software, and you are welcome to redistribute it')
		print('under certain conditions; type `help copying` for details.\n')
		return 0
	

	def loop(self):
		while self.keep_going:
			prompt_string = '[pysocial] '
			cur_file = self.db.current_file()
			if cur_file:
				prompt_string = prompt_string + cur_file + ' '
			cmd = input(prompt_string + '>')
			carryover = self.parse(cmd)
			while carryover and self.keep_going:
				carryover = self.parse(carryover)
	
	def parse(self, text):
		preparsed_command = self.preparse(text)
		if preparsed_command == None:
			return None

		if preparsed_command['core'] == None:
			return preparsed_command['carryover']

		if preparsed_command['core'] in self.command_lut.keys():
			self.command_lut[preparsed_command['core']](preparsed_command['args'])
		else:
			self.unknown_command(preparsed_command['core'])
		return preparsed_command['carryover']


	def preparse(self, text):
		if not text:
			return None

		text = text.strip()

		if text == '':
			return None

		command = self.split_command(text)
		
		if len(command) > 0:
			core = None
			args = []
			
			for dex, piece in enumerate(command):
				if piece == ';':
					if dex < len(command) - 1:
						if not core:
							return None
						else:
							return {'core':core,'args':args,'carryover':command[len(command)-1]}
					else:
						return {'core':core,'args':args,'carryover':None}
				elif core == None:
					core = piece
				else:
					args.append(piece)
			return {'core':core,'args':args,'carryover':None}

		return None
	

	def split_command(self, cmd):
		# TODO: change this to iterate over the string, and keep track of
		# escape characters, etc.
		parts = []
		while True:
			cmd = cmd.strip()
			space_loc = cmd.find(' ')
			semic_loc = cmd.find(';')
			if space_loc == -1 and semic_loc == -1:
				parts.append(cmd)
				return parts
			else:
				if (space_loc < semic_loc and space_loc != -1) or semic_loc == -1:
					parts.append(cmd[:space_loc].strip())
					cmd = cmd[space_loc+1:]
				else:
					parts.append(cmd[:semic_loc].strip())
					parts.append(';')
					parts.append(cmd[semic_loc+1:])
					return parts
	

	def cmd_exit(self, args):
		self.write('Goodbye.\n\n')
		self.keep_going = False
	

	def cmd_help(self, args):
		self.write('================================')
		i = 0
		base = self.help_dict
		working_command = 'help'
		while i < len(args):
			if args[i] in base['sub']:
				working_command = working_command + ' ' + args[i]
				base = base['sub'][args[i]]
				i = i + 1
			else:
				self.write('Unknown help topic: ' + args[i])
				self.write('Top-level help:\n\n' + self.help_dict['text'] + '\n')
				return

		if i != 0:
			self.write(self.help_dict['text'] + '\n')

		self.write(base['text'] + '\n')

		if len(base['sub']) > 0:
			topics_string = 'Available sub-topics: '
			for subcommand in base['sub'].keys():
				topics_string = topics_string + subcommand + ' '

			self.write(topics_string + '\nType `' + working_command + ' <topic>` for more information.\n')
	

	def cmd_open(self, args):
		if len(args) == 1:
			self.db.open_file_by_name(args[0])
		elif len(args) == 2 and args[0] == '-i':
			self.db.open_file_by_id(args[1])
		else:
			self.cmd_help(['open'])


	def cmd_add(self, args):
		if len(args) == 0:
			self.cmd_help(['add'])
		elif not self.db.current_file():
			self.log_warning('Cannot add node with no open file.')
			return
		else:
			for node_name in args:
				if ':' in node_name:
					self.log_error('Reserved character ":" cannot be used in names. Node "' + str(node_name) + '" could not be added.')
				else:
					self.db.add_node(str(node_name))
	
	
	def cmd_connect(self, args):
		parsed_args = []
		if len(args) == 2:
			for name in args:
				if ':' in name:
					semi_pos = name.find(':')
					parsed_args.append({'name':str(name[:semi_pos]),'discrim':int(name[semi_pos+1:])})
				else:
					parsed_args.append({'name':str(name),'discrim':None})
			
			from social import name_conflict_error
			try:
				self.db.add_connection_by_name(parsed_args[0]['name'], parsed_args[1]['name'], parsed_args[0]['discrim'], parsed_args[1]['discrim'])
			except name_conflict_error:
				self.write('It looks like some of your nodes have the same name. See `help discrim` to learn how to fix this.')
		elif len(args) == 3 and args[0] == '-i':
			self.db.add_connection_by_id(args[1],args[2])
		else:
			self.cmd_help(['connect'])
	

	def cmd_list_nodes(self, args):
		nodes = self.db.list_nodes()
		if self.db.current_file():
			self.write('Listing nodes in current file...')
		else:
			self.write('Listing all nodes in all files...')

		for node in nodes:
			self.write('  "' + str(node[0]) + '" with id ' + str(node[1]) + ' (discrim ' + str(abs(node[1]) % 100000) + ')')
	
	
	def cmd_list_connections(self, args):
		cxns = self.db.list_connections()
		if self.db.current_file():
			self.write('Listing connections in current file...')
		else:
			self.write('Listing all connections in all files...')

		for cxn in cxns:
			self.write('  ' + str(cxn[0]) + ' to ' + str(cxn[1]) + ' with id ' + str(cxn[2]))
	

	def cmd_list_files(self, args):
		files = self.db.list_files()
		self.write('Current files:')
		for file_obj in files:
			self.write('  "' + str(file_obj[0]) + '" with id ' + str(file_obj[1]))

	
	def cmd_render(self, args):
		output_path = 'render_output.png'
		if len(args) == 0:
			pass
		elif len(args) == 1:
			output_path = str(args[0])
		else:
			self.cmd_help(['render'])
		
		self.write('Rendering graph to ' + str(output_path))
		ret = self.rend.render(output_path)

		if ret == 0:
			self.write('Success.')
		elif ret == 1:
			self.log_severe('DATABASE ERROR WHILE RENDERING.')
		elif ret == 2:
			self.log_error('No file open in database.')
		else:
			self.log_error('Unknown error while rendering.')
	

	def unknown_command(self, command_text):
		self.log_warning('Unknown command: "' + str(command_text) + '"!')
	

	def write(self, message):
		print(str(message))

	def log(self, message, level=5):
		print('[' + str(level) + ']: ' + str(message))
	
	def log_debug(self, message):
		self.log(message, level=7)
	
	def log_warning(self, message):
		self.log(message, level=3)
	
	def log_error(self, message):
		self.log(message, level=2)

	def log_severe(self, message):
		self.log(message, level=1)
	
	def prompt_yn(self, prompt_text, default_resp=False):
		acceptable_ys = ['y','yes','t','true' ,'1']
		acceptable_ns = ['n','no' ,'f','false','0']
		resp = input(str(prompt_text) + ' [Y/N] >')

		if resp.lower() in acceptable_ys:
			return True
		elif resp.lower() in acceptable_ns:
			return False
		else:
			return default_resp
