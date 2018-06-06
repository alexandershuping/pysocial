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

class polymorphism_error(BaseException):
	'''
	  ' Raised when somebody tries to use a base class
	'''


class ui:
	def __init__(self):
		pass
	
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
		pass
	
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
