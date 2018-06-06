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



class basic_console_ui(ui):

	def __init__(self):
		with open('social-help.json') as hmenu:
			self.help_dict = json.load(hmenu)

		self.command_lut = {
			'exit':self.cmd_exit,
			'help':self.cmd_help
			# TODO: add new commands here. The command name goes before the :,
			# and the name of the function to call goes after it.
		}
		self.keep_going = True

	def begin(self):
		# TODO: configuration loading and database object creation is only
		# here for testing purposes. Move it out of the UI class.
		from social_db import db_connect
		self.write('Attempting to load configuration...')
		self.log('Loading config.json...')
		
		try:
			with open('config.json') as config:
				self.config = json.load(config)
		except FileNotFoundError:
			self.log_severe('Could not find config.json! Aborting startup!')
			return 1
		except json.decoder.JSONDecodeError:
			self.log_severe('Could not parse config.json! Aborting startup!')
			return 1
		else:
			self.write('Success!')

		self.write('Attempting to connect to database...')

		self.log('Loading table schema from social-tables.json...')
		try:
			with open('social-tables.json') as tables:
				self.schema = json.load(tables)
		except FileNotFoundError:
			self.log_severe('Could not find social-tables.json! Aborting startup!')
			return 1
		except json.decoder.JSONDecodeError:
			self.log_severe('Could not parse social-tables.json! Aborting startup!')
			return 1
		self.database = db_connect(self, self.config, self.schema)

		print('\n\n\nPysocial Copyright (C) 2018 Alexander Shuping')
		print('This program comes with ABSOLUTELY NO WARRANTY; for details type `help warranty`.')
		print('This is free software, and you are welcome to redistribute it')
		print('under certain conditions; type `help copying` for details.\n')
		return 0
	

	def loop(self):
		while self.keep_going:
			cmd = input('[pysocial] > ')
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
